from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app import models

router = APIRouter(
    prefix="/userApi/v1/food",
    tags=["Foods"]
)

@router.get("/{foodId}")
async def get_food(foodId: int, db: Session = Depends(get_db)):
    db_food = db.query(models.Food).options(
        joinedload(models.Food.generic_ingredient).joinedload(models.GenericIngredient.food_family),
        joinedload(models.Food.specific_ingredient).joinedload(models.SpecificIngredient.food_family),
        # Recetas genéricas: pasos + ingredientes (con su familia)
        joinedload(models.Food.generic_recipe).joinedload(models.GenericRecipe.steps),
        joinedload(models.Food.generic_recipe).joinedload(models.GenericRecipe.ingredients)
            .joinedload(models.GenericIngredient.food_family),
        # Recetas específicas: pasos + ingredientes genéricos (con su familia)
        joinedload(models.Food.specific_recipe).joinedload(models.SpecificRecipe.steps),
        joinedload(models.Food.specific_recipe).joinedload(models.SpecificRecipe.ingredients)
            .joinedload(models.GenericIngredient.food_family),
        joinedload(models.Food.specific_recipe).joinedload(models.SpecificRecipe.specific_ingredients)
            .joinedload(models.SpecificIngredient.food_family),
    ).filter(models.Food.id == foodId).first()

    if not db_food:
        raise HTTPException(status_code=404, detail="Food not found")

    # Ingrediente genérico
    if db_food.generic_ingredient:
        ing = db_food.generic_ingredient
        return {
            "name": ing.self_name,
            "kcal": ing.kcal,
            "food_family": {
                "id": ing.food_family.id,
                "name": ing.food_family.self_name
            } if ing.food_family else None
        }

    # Ingrediente específico
    if db_food.specific_ingredient:
        ing = db_food.specific_ingredient
        return {
            "name": ing.self_name,
            "kcal": ing.kcal,
            "food_family": {
                "id": ing.food_family.id,
                "name": ing.food_family.self_name
            } if ing.food_family else None
        }

    # Receta genérica
    if db_food.generic_recipe:
        rec = db_food.generic_recipe
        return {
            "id": rec.id,
            "foodId": rec.food_id,
            "name": rec.self_name,
            "chefAdvice": rec.cheff_advice,
            "kcal": rec.kcal,
            "steps": [
                {
                    "stepNumber": s.step_number,
                    "instruction": s.instruction,
                    "estimatedTime": s.estimated_time
                } for s in rec.steps
            ],
            "ingredients": [
                {
                    "id": ing.id,
                    "name": ing.self_name,
                    "kcal": ing.kcal,
                    "food_family": {
                        "id": ing.food_family.id,
                        "name": ing.food_family.self_name
                    } if ing.food_family else None
                } for ing in rec.ingredients
            ]
        }

        # Receta específica
    if db_food.specific_recipe:
        rec = db_food.specific_recipe
        # Combinar ingredientes genéricos y específicos
        all_ingredients = []
        for ing in rec.ingredients:
            all_ingredients.append({
                "id": ing.id,
                "name": ing.self_name,
                "kcal": ing.kcal,
                "food_family": {
                    "id": ing.food_family.id,
                    "name": ing.food_family.self_name
                } if ing.food_family else None
            })
        for ing in rec.specific_ingredients:
            all_ingredients.append({
                "id": ing.id,
                "name": ing.self_name,
                "kcal": ing.kcal,
                "food_family": {
                    "id": ing.food_family.id,
                    "name": ing.food_family.self_name
                } if ing.food_family else None
            })

        return {
            "id": rec.id,
            "foodId": rec.food_id,
            "name": rec.self_name,
            "chefAdvice": rec.chef_advice,
            "kcal": rec.kcal,
            "steps": [
                {
                    "stepNumber": s.step_number,
                    "instruction": s.instruction,
                    "estimatedTime": s.estimated_time
                } for s in rec.steps
            ],
            "ingredients": all_ingredients
        }

    raise HTTPException(status_code=404, detail="Food exists but has no linked entity")


@router.delete("/{foodId}")
async def delete_food(foodId: int, db: Session = Depends(get_db)):
    db_food = db.query(models.Food).filter(models.Food.id == foodId).first()
    if not db_food:
        raise HTTPException(status_code=404, detail=f"Food with id {foodId} not found")

    db.delete(db_food)
    db.commit()
    return {"message": f"Successfully deleted food with id {foodId}."}