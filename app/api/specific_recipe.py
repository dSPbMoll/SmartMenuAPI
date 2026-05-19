from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import insert, delete
from sqlalchemy.orm import Session
from app.database import get_db
from app import schemas
from google import genai
from google.genai import types
import json
import os
from dotenv import load_dotenv

from app import models

router = APIRouter(
    prefix="/userApi/v1/specific-recipe",
    tags=["Specific Recipes"]
)

# ================================ SPECIFIC RECIPES ================================ 

@router.post("/", status_code=201)
async def create_specific_recipe(
    recipe: schemas.SpecificRecipeCreate,
    db: Session = Depends(get_db)
):
    try:
        new_food = models.Food()
        db.add(new_food)
        db.flush()

        new_recipe = models.SpecificRecipe(
            account_id = recipe.account_id,
            food_id = new_food.id,
            self_name = recipe.name,
            chef_advice = recipe.cheff_advice,
            kcal=recipe.kcal if recipe.kcal is not None else 0
        )

        db.add(new_recipe)
        db.commit()
        db.refresh(new_recipe)

    except Exception as e:
        db.rollback()
        print(f"Error en create_specific_recipe: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Error while saving the recipe and food record: {str(e)}"
        )

    return {
        "id": new_recipe.id,
        "foodId": new_recipe.food_id,
        "accountId": new_recipe.account_id,
        "name": new_recipe.self_name,
        "chefAdvice": new_recipe.chef_advice,
        "kcal": new_recipe.kcal
    }

@router.get("/{specificRecipeId}")
async def get_specific_recipe(specificRecipeId: int, db: Session = Depends(get_db)):

    db_recipe = db.query(models.SpecificRecipe).filter(
        models.SpecificRecipe.id == specificRecipeId
    ).first()

    if not db_recipe:
        raise HTTPException(
            status_code=404,
            detail=f"Specific recipe with ID {specificRecipeId} not found"
        )

    steps = db.query(models.SpecificRecipeStep).filter(
        models.SpecificRecipeStep.specific_recipe_id == specificRecipeId
    ).order_by(models.SpecificRecipeStep.step_number.asc()).all()

    tags = db.query(models.RecipeTag).join(models.recipe_tag_in_specific).filter(
        models.recipe_tag_in_specific.c.specific_recipe_id == specificRecipeId
    ).all()

    generic_ingredients = db.query(models.GenericIngredient).join(models.generic_ingredient_in_specific_recipe).filter(
        models.generic_ingredient_in_specific_recipe.c.recipe_id == specificRecipeId
    ).all()

    specific_ingredients = db.query(models.SpecificIngredient).join(models.specific_ingredient_in_specific_recipe).filter(
        models.specific_ingredient_in_specific_recipe.c.recipe_id == specificRecipeId
    ).all()

    ingredients = generic_ingredients + specific_ingredients

    return {
        "id": db_recipe.id,
        "foodId": db_recipe.food_id,
        "name": db_recipe.self_name,
        "chefAdvice": db_recipe.chef_advice,
        "kcal": db_recipe.kcal,
        "steps": [
            {
                "stepNumber": s.step_number,
                "instruction": s.instruction,
                "estimatedTime": s.estimated_time
            } for s in steps
        ],
        "tags": [
            {
                "id": t.id,
                "name": t.self_name
            } for t in tags
        ],
        "ingredients": [
            {
                "id": i.id,
                "name": i.self_name,
                "foodId": i.food_id,
                "kcal": i.kcal,
                "foodFamily": {
                    "id": i.food_family.id,
                    "name": i.food_family.self_name
                } if i.food_family else None
            } for i in ingredients
        ]
    }


@router.get("/account/{accountId}")
async def get_specific_recipes_by_account(
    accountId: int,
    db: Session = Depends(get_db)
):
    recipes = db.query(models.SpecificRecipe).filter(
        models.SpecificRecipe.account_id == accountId
    ).all()

    return [
        {
            "id": r.id,
            "foodId": r.food_id,
            "name": r.self_name,
            "chefAdvice": r.chef_advice,
            "kcal": r.kcal,
        }
        for r in recipes
    ]

@router.delete("/{specificRecipeId}")
async def delete_specific_recipe(specificRecipeId: int, db: Session = Depends(get_db)):

    recipe = db.query(models.SpecificRecipe).filter(models.SpecificRecipe.id == specificRecipeId).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Specific Recipe not found")

    db.execute(
        delete(models.SpecificRecipe).where(
            models.SpecificRecipe.id == specificRecipeId
        )
    )

    db.commit()

    return {"message": f"Successfully deleted specific recipe with id {specificRecipeId}."}

# ================================ RECIPE TAGS ================================ 

@router.post("/{specificRecipeId}/tags")
async def set_tags_to_specific_recipe(specificRecipeId: int, tags: schemas.IdList, db: Session = Depends(get_db)):

    recipe = db.query(models.SpecificRecipe).filter(
        models.SpecificRecipe.id == specificRecipeId
    ).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Specific recipe not found")

    db.execute(
        delete(models.recipe_tag_in_specific).where(
            models.recipe_tag_in_specific.c.specific_recipe_id == specificRecipeId
        )
    )

    if tags.ids:
        tag_associations = [
            {"specific_recipe_id": specificRecipeId, "recipe_tag_id": t_id}
            for t_id in set(tags.ids)
        ]
        db.execute(insert(models.recipe_tag_in_specific).values(tag_associations))

    db.commit()
    return {"message": f"Tags updated. Specific recipe with id {specificRecipeId} now has {len(tags.ids)} tags."}

# ================================ SPECIFIC INGREDIENTS ================================

@router.post("/{specificRecipeId}/ingredients")
async def set_ingredients_to_specific_recipe(
    specificRecipeId: int,
    genericIngredients: schemas.IdList,
    specificIngredients: schemas.IdList,
    db: Session = Depends(get_db)
    ):

    recipe = db.query(models.SpecificRecipe).filter(
        models.SpecificRecipe.id == specificRecipeId
    ).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Specific Recipe not found")

    db.execute(
        delete(models.generic_ingredient_in_specific_recipe).where(
            models.generic_ingredient_in_specific_recipe.c.recipe_id == specificRecipeId
        )
    )
    db.execute(
        delete(models.specific_ingredient_in_specific_recipe).where(
            models.specific_ingredient_in_specific_recipe.c.recipe_id == specificRecipeId
        )
    )

    if genericIngredients.ids:
        ingredient_associations = [
            {"recipe_id": specificRecipeId, "ingredient_id": i_id}
            for i_id in set(genericIngredients.ids)
        ]
        db.execute(insert(models.generic_ingredient_in_specific_recipe).values(ingredient_associations))

    if specificIngredients.ids:
        ingredient_associations = [
            {"recipe_id": specificRecipeId, "ingredient_id": i_id}
            for i_id in set(specificIngredients.ids)
        ]
        db.execute(insert(models.specific_ingredient_in_specific_recipe).values(ingredient_associations))

    db.commit()
    return {"message": f"Ingredients updated. Recipe {specificRecipeId} now has {len(genericIngredients.ids) + len(specificIngredients.ids)} ingredients."}

# ================================ SPECIFICC RECIPE STEPS ================================

@router.post("/{specificRecipeId}/steps", status_code=201)
async def set_specific_recipe_steps(
    specificRecipeId: int,
    steps_in: schemas.SpecificRecipeStepList,
    db: Session = Depends(get_db)
):
    recipe = db.query(models.SpecificRecipe).filter(
        models.SpecificRecipe.id == specificRecipeId
    ).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Specific recipe not found")

    db.execute(
        delete(models.SpecificRecipeStep).where(
            models.SpecificRecipeStep.specific_recipe_id == specificRecipeId
        )
    )

    for step_data in steps_in.steps:
        full_data = step_data.model_dump()
        full_data.pop("kcal", None)
        full_data["specific_recipe_id"] = specificRecipeId

        new_step = models.SpecificRecipeStep(**full_data)
        db.add(new_step)

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")

    return {"message": f"Specific recipe steps updated for specific recipe with id {specificRecipeId}"}

@router.get("/{specificRecipeId}/steps")
async def get_all_specific_recipe_steps(specificRecipeId: int, db: Session = Depends(get_db)):
    recipe_exists = db.query(models.SpecificRecipe).filter(
        models.SpecificRecipe.id == specificRecipeId
    ).first()

    if not recipe_exists:
        raise HTTPException(
            status_code=404,
            detail=f"Specifci recipe with ID {specificRecipeId} does not exist"
        )

    steps = db.query(models.SpecificRecipe).filter(
        models.SpecificRecipe.specific_recipe_id == specificRecipeId
    ).order_by(models.SpecificRecipe.step_number.asc()).all()

    return steps


# ================================ AI ================================

load_dotenv()
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
    http_options={'api_version': 'v1beta'}
)


@router.post("/ai")
async def generate_specific_recipe_through_ai(
    payload: schemas.ingredientNameListAI,
    db: Session = Depends(get_db)
):
    ingredients_str = ", ".join(payload.ingredient_list)
    strict = payload.strict_mode if payload.strict_mode is not None else True

    filter = payload.filter if payload.filter else ''
    if filter:
        if filter == 'Rápidas':
            filter_instruction = 'La receta debe ser rápida de preparar (menos de 30 minutos).'
        elif filter == 'Elaboradas':
            filter_instruction = 'La receta puede ser elaborada, sin límite de tiempo.'
        elif filter == 'Postres':
            filter_instruction = 'La receta debe ser un postre o dulce.'
        else:
            filter_instruction = ''
    else:
        filter_instruction = ''

    restrictions = payload.restrictions if payload.restrictions else []
    if restrictions:
        restrictions_str = ", ".join(restrictions)
        restrictions_instruction = (
            f"⚠️ RESTRICCIONES DEL USUARIO: {restrictions_str}. "
            "Estas restricciones pueden ser alimentos concretos, familias de alimentos (ej. Lácteos) o condiciones médicas (ej. diabetes, celiaquía). "
            "NO uses ningún alimento mencionado ni derivados que los contengan. "
            "Si hay una condición médica, adapta la receta para que sea totalmente segura."
        )
    else:
        restrictions_instruction = ''



    if strict:
        prompt = f"""
        Eres un chef experto. Basándote SOLO en estos ingredientes (no debes usarlos todos necesariamente):
        {ingredients_str}, genera una receta creativa {' ' + filter_instruction if filter_instruction else ''}{' ' + restrictions_instruction if restrictions_instruction else ''}.
        Incluye SIEMPRE en el JSON la lista completa de ingredientes utilizados (solo los de la lista).
        Responde ÚNICAMENTE en formato JSON con la siguiente estructura:
        {{
            "self_name": "Nombre de la receta",
            "chef_advice": "Un consejo breve del chef",
            "kcal": "Numero entero con las kcal totales de la receta",
            "steps": [
                {{"step_number": 1, "instruction": "descripción", "estimated_time": 5}}
            ],
            "ingredients": ["ingrediente1", "ingrediente2", ...]
        }}
        No añadas texto extra fuera del JSON.
        """
    else:
        prompt = f"""
        Eres un chef experto. Utilizando como base o inspiración estos ingredientes (no debes usarlos todos necesariamente):
        {ingredients_str}, genera una receta creativa, sabrosa y completa {' ' + filter_instruction if filter_instruction else ''}{' ' + restrictions_instruction if restrictions_instruction else ''}.
        Puedes añadir libremente otros ingredientes, condimentos, líquidos y guarniciones
        que consideres necesarios para que la receta sea un plato realista y apetecible.
        Incluye SIEMPRE en el JSON la lista completa de ingredientes utilizados (tanto los proporcionados como los añadidos por ti).
        Responde ÚNICAMENTE en formato JSON con la siguiente estructura:
        {{
            "self_name": "Nombre de la receta",
            "chef_advice": "Un consejo breve del chef",
            "kcal": "Numero entero con las kcal totales de la receta",
            "steps": [
                {{"step_number": 1, "instruction": "descripción", "estimated_time": 5}},
                ...
            ],
            "ingredients": ["ingrediente1", "ingrediente2", ...]
        }}
        No añadas texto extra fuera del JSON.
        """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        recipe = json.loads(response.text)

        # Fallback: si la IA no incluyó el campo "ingredients", añadir al menos los originales
        if "ingredients" not in recipe:
            recipe["ingredients"] = payload.ingredient_list

        return recipe

    except Exception as e:
        print(f"DEBUG FINAL: {e}")
        error_str = str(e)
        if "503" in error_str or "UNAVAILABLE" in error_str:
            raise HTTPException(
                status_code=503,
                detail="El servicio de IA está temporalmente sobrecargado. Inténtalo de nuevo en unos segundos."
            )
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")