from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import insert, delete
from sqlalchemy.orm import Session
from app.database import get_db
from app.api import schemas, models
from google import genai
from google.genai import types
import json
import os
from dotenv import load_dotenv

router = APIRouter(
    prefix="/userApi/v1/specific-recipe",
    tags=["Specific Recipes"]
)

# ================================ SPECIFIC RECIPES ================================ 

@router.post("/", status_code=201)
async def create_specific_recipe(recipe: schemas.SpecificRecipeCreate, db: Session = Depends(get_db)):
    new_recipe = models.SpecificRecipe(
        account_id = recipe.account_id,
        self_name = recipe.name,
        cheff_advice = recipe.cheff_advice
    )
    
    db.add(new_recipe)
    db.flush()

    try:
        db.commit()
        db.refresh(new_recipe)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error while saving the recipe: {str(e)}")
    
    return {
        "id": new_recipe.id,
        "foodId": new_recipe.food_id,
        "accountId": new_recipe.account_id,
        "name": new_recipe.self_name,
        "cheffAdvice": new_recipe.cheff_advice
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
        "cheffAdvice": db_recipe.cheff_advice,
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
                "foodFamily": {
                    "id": i.food_family.id,
                    "name": i.food_family.self_name
                } if i.food_family else None # Just in case an ingredient has no family
            } for i in ingredients
        ]
    }

@router.delete("/{specificRecipeId}")
async def delete_specific_recipe(specificRecipeId: int, db: Session = Depends(get_db)):

    recipe = db.query(models.SpecificRecipe).filter(models.SpecificRecipe.id == specificRecipeId).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Specific Recipe not found")

    # Delete recipe
    db.execute(
        delete(models.SpecificRecipe).where(
            models.SpecificRecipe.id == specificRecipeId
        )
    )

    db.commit()

    return {"message": f"Successfully deleted specific recipe with id {specificRecipeId}."}

# ================================ RECIPE TAGS ================================ 

@router.post("/{specificRecipeId}/tags")
async def set_tags_to_specific_recipe(specificRecipeId: int, tags: schemas.RecipeTagIdList, db: Session = Depends(get_db)):

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
    genericIngredients: schemas.genericIngredientIdList,
    specificIngredients: schemas.specificIngredientIdList,
    db: Session = Depends(get_db)
    ):

    recipe = db.query(models.SpecificRecipe).filter(
        models.SpecificRecipe.id == specificRecipeId
    ).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Specific Recipe not found")

    # Delete existing ingredient relations
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

    # Add new ingredients to recipe's associatives
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
    
    # Steps can be a void list
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
    '''
    for m in client.models.list():
        print(f"Modelo disponible: {m.name}")
    '''

    # 1. Preparamos la lista de ingredientes para el prompt
    ingredients_str = ", ".join(payload.ingredient_list)
    
    # 2. Creamos el Prompt (Instrucciones precisas)
    prompt = f"""
    Eres un chef experto. Basándote SOLO en estos ingredientes (no debes usarlos todos necesariamente):
    {ingredients_str}, genera una receta creativa. 
    Responde ÚNICAMENTE en formato JSON con la siguiente estructura:
    {{
        "self_name": "Nombre de la receta",
        "chef_advice": "Un consejo breve del chef",
        "steps": [
            {{"step_number": 1, "instruction": "descripción", "estimated_time": 5}},
            ...
        ]
    }}
    No añadas texto extra fuera del JSON.
    """

    try:
        # Cambiamos el modelo a la versión flash estándar (sin el "native-audio")
        response = client.models.generate_content(
            model="gemini-2.5-flash", # <--- Prueba este nombre simplificado
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        return json.loads(response.text)

    except Exception as e:
        print(f"DEBUG FINAL: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

