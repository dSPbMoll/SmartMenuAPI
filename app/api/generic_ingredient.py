from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import delete
from sqlalchemy.orm import Session
from app.database import get_db
from app import schemas
from app import models

router = APIRouter(
    prefix="/userApi/v1/generic-ingredient",
    tags=["Generic Ingredients"]
)

@router.get("/")
async def get_all_generic_ingredients(db: Session = Depends(get_db)):
    
    db_ingredients = db.query(models.GenericIngredient).all()

    if db_ingredients is None:
        raise HTTPException(status_code=404, detail="Couldn't find any generic ingredient")

    return [{
        "id": ingredient.id,
        "name": ingredient.self_name,
        "food_family": ingredient.food_family,
        "kcal": ingredient.kcal
    } for ingredient in db_ingredients]

@router.post("/", status_code=201)
async def create_generic_ingredient(
    ingredient: schemas.GenericIngredientCreate,
    db: Session = Depends(get_db)
):
    try:
        new_food = models.Food()
        db.add(new_food)
        
        db.flush() 

        new_ingredient = models.GenericIngredient(
            self_name = ingredient.name,
            food_family_id = ingredient.food_family_id,
            food_id = new_food.id,
            kcal = new_food.kcal
        )
        
        db.add(new_ingredient)
        db.commit()
        db.refresh(new_ingredient)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400, 
            detail=f"Error while saving the generic ingredient: {str(e)}"
        )
    
    return {
        "id": new_ingredient.id,
        "name": new_ingredient.self_name,
        "kcal": new_ingredient.kcal,
        "foodFamilyId": new_ingredient.food_family_id,
        "foodId": new_ingredient.food_id
    }

@router.get("/{genericIngredientId}")
async def get_generic_ingredient(genericIngredientId: int, db: Session = Depends(get_db)):

    db_generic_ingredient = db.query(models.GenericIngredient).filter(
        models.GenericIngredient.id == genericIngredientId
    ).first()

    if db_generic_ingredient is None:
        raise HTTPException(
            status_code=404, 
            detail=f"Generic Ingredient with ID {genericIngredientId} not found"
        )

    return {
        "id": db_generic_ingredient.id,
        "name": db_generic_ingredient.self_name,
        "kcal": db_generic_ingredient.kcal,
        "foodFamilyId": db_generic_ingredient.food_family_id,
        "foodId": db_generic_ingredient.food_id
    }

@router.delete("/{genericIngredientId}")
async def delete_generic_ingredient(genericIngredientId: int, db: Session = Depends(get_db)):
    
    ingredient = db.query(models.GenericIngredient).filter(
        models.GenericRecipe.id == genericIngredientId
    ).first()
    if not ingredient:
        raise HTTPException(status_code=404, detail="Generic Ingredient not found")
    
    db.execute(
        delete(models.GenericIngredient).where(
            models.GenericIngredient.id == genericIngredientId
        )
    )

    db.commit()

    return {"message": f"Successfully deleted generic ingredient with id {genericIngredientId}."}

