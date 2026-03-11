from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app import models

router = APIRouter(
    prefix="/userApi/v1/food",
    tags=["Foods"]
)

# ================================ FOODS ================================ 

@router.get("/{foodId}")
async def get_food(foodId: int, db: Session = Depends(get_db)):
    # Bring Food and "pre-charge" all its possible types
    db_food = db.query(models.Food).options(
        joinedload(models.Food.generic_ingredient),
        joinedload(models.Food.specific_ingredient),
        joinedload(models.Food.generic_recipe),
        joinedload(models.Food.specific_recipe)
    ).filter(models.Food.id == foodId).first()

    if not db_food:
        raise HTTPException(status_code=404, detail="Food not found")

    # Verify what is the true answer
    if db_food.generic_ingredient:
        return db_food.generic_ingredient
    
    if db_food.specific_ingredient:
        return db_food.specific_ingredient
    
    if db_food.generic_recipe:
        return db_food.generic_recipe
    
    if db_food.specific_recipe:
        return db_food.specific_recipe

    raise HTTPException(status_code=404, detail="Food exists but has no linked entity")

@router.delete("/{foodId}")
async def delete_food(foodId: int, db: Session = Depends(get_db)):

    db_food = db.query(models.Food).filter(
        models.Food.id == foodId
    ).first()
    if not db_food:
        raise HTTPException(status_code = 404, detail = f"Food with id {foodId} not found")

    db.delete(db_food)
    db.commit()

    return {"message": f"Successfully deleted food with id {foodId}."}
