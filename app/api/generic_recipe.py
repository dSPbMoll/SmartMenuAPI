from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import insert, delete
from sqlalchemy.orm import Session
from app.database import get_db
from app import schemas
from app import models

router = APIRouter(
    prefix="/userApi/v1/generic-recipe",
    tags=["Generic Recipes"]
)

# ================================ GENERIC RECIPES ================================ 

@router.post("/", status_code=201)
async def create_generic_recipe(
    recipe: schemas.GenericRecipeCreate, 
    db: Session = Depends(get_db)
):
    try:
        new_food = models.Food()
        db.add(new_food)

        db.flush() 

        new_recipe = models.GenericRecipe(
            self_name = recipe.name,
            food_id = new_food.id,
            cheff_advice = recipe.cheff_advice
        )
        
        db.add(new_recipe)

        db.commit()
        db.refresh(new_recipe)

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400, 
            detail=f"Error while saving the generic recipe and food record: {str(e)}"
        )
    
    return {
        "id": new_recipe.id,
        "foodId": new_recipe.food_id,
        "name": new_recipe.self_name,
        "cheffAdvice": new_recipe.cheff_advice,
    }

@router.get("/{genericRecipeId}")
async def get_generic_recipe(genericRecipeId: int, db: Session = Depends(get_db)):

    db_recipe = db.query(models.GenericRecipe).filter(
        models.GenericRecipe.id == genericRecipeId
    ).first()

    if not db_recipe:
        raise HTTPException(
            status_code=404, 
            detail=f"Recipe with ID {genericRecipeId} not found"
        )

    steps = db.query(models.GenericRecipeStep).filter(
        models.GenericRecipeStep.generic_recipe_id == genericRecipeId
    ).order_by(models.GenericRecipeStep.step_number.asc()).all()

    tags = db.query(models.RecipeTag).join(models.recipe_tag_in_generic).filter(
        models.recipe_tag_in_generic.c.generic_recipe_id == genericRecipeId
    ).all()

    ingredients = db.query(models.GenericIngredient).join(models.generic_ingredient_in_generic_recipe).filter(
        models.generic_ingredient_in_generic_recipe.c.recipe_id == genericRecipeId
    ).all()

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

@router.delete("/{genericRecipeId}")
async def delete_generic_recipe(genericRecipeId: int, db: Session = Depends(get_db)):

    recipe = db.query(models.GenericRecipe).filter(models.GenericRecipe.id == genericRecipeId).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Generic Recipe not found")

    # Delete recipe
    db.execute(
        delete(models.GenericRecipe).where(
            models.GenericRecipe.id == genericRecipeId
        )
    )

    db.commit()

    return {"message": f"Successfully deleted generic recipe with id {genericRecipeId}."}

# ================================ RECIPE TAGS ================================ 

@router.post("/{genericRecipeId}/tags")
async def set_tags_to_generic_recipe(genericRecipeId: int, tags: schemas.RecipeTagIdList, db: Session = Depends(get_db)):

    recipe = db.query(models.GenericRecipe).filter(
        models.GenericRecipe.id == genericRecipeId
    ).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Generic Recipe not found")

    db.execute(
        delete(models.recipe_tag_in_generic).where(
            models.recipe_tag_in_generic.c.generic_recipe_id == genericRecipeId
        )
    )

    if tags.ids:
        tag_associations = [
            {"generic_recipe_id": genericRecipeId, "recipe_tag_id": t_id}
            for t_id in set(tags.ids)
        ]
        db.execute(insert(models.recipe_tag_in_generic).values(tag_associations))

    db.commit()
    return {"message": f"Tags updated. Recipe {genericRecipeId} now has {len(tags.ids)} tags."}

# ================================ GENERIC INGREDIENTS ================================

@router.post("/{genericRecipeId}/ingredients")
async def set_ingredients_to_generic_recipe(
    genericRecipeId: int,
    ingredients: schemas.genericIngredientIdList,
    db: Session = Depends(get_db)
    ):

    recipe = db.query(models.GenericRecipe).filter(
        models.GenericRecipe.id == genericRecipeId
    ).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Generic Recipe not found")

    db.execute(
        delete(models.generic_ingredient_in_generic_recipe).where(
            models.generic_ingredient_in_generic_recipe.c.recipe_id == genericRecipeId
        )
    )

    if ingredients.ids:
        ingredient_associations = [
            {"recipe_id": genericRecipeId, "ingredient_id": i_id}
            for i_id in set(ingredients.ids)
        ]
        db.execute(insert(models.generic_ingredient_in_generic_recipe).values(ingredient_associations))

    db.commit()
    return {"message": f"Ingredients updated. Recipe {genericRecipeId} now has {len(ingredients.ids)} ingredients."}

# ================================ GENERIC RECIPE STEPS ================================

@router.post("/{genericRecipeId}/steps", status_code=201)
async def set_generic_recipe_steps(
    genericRecipeId: int,
    steps_in: schemas.GenericRecipeStepList, 
    db: Session = Depends(get_db)
):
    recipe = db.query(models.GenericRecipe).filter(
        models.GenericRecipe.id == genericRecipeId
    ).first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Generic Recipe not found")

    db.execute(
        delete(models.GenericRecipeStep).where(
            models.GenericRecipeStep.generic_recipe_id == genericRecipeId
        )
    )

    for step_data in steps_in.steps:
        full_data = step_data.model_dump()
        full_data["generic_recipe_id"] = genericRecipeId
        
        new_step = models.GenericRecipeStep(**full_data)
        db.add(new_step)

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")
    
    return {"message": f"Recipe steps updated for recipe with id {genericRecipeId}"}

@router.get("/{genericRecipeId}/steps")
async def get_all_generic_recipe_steps(genericRecipeId: int, db: Session = Depends(get_db)):

    recipe_exists = db.query(models.GenericRecipe).filter(
        models.GenericRecipe.id == genericRecipeId
    ).first()

    if not recipe_exists:
        raise HTTPException(
            status_code=404, 
            detail=f"Recipe with ID {genericRecipeId} does not exist"
        )

    steps = db.query(models.GenericRecipeStep).filter(
        models.GenericRecipeStep.generic_recipe_id == genericRecipeId
    ).order_by(models.GenericRecipeStep.step_number.asc()).all()
    
    # Steps can be a void list
    return steps
