from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import schemas
from app import models

router = APIRouter(
    prefix="/userApi/v1/food-family",
    tags=["Food Families"]
)

@router.post("/", status_code=201)
async def create_food_family(food_family: schemas.FoodFamily, db: Session = Depends(get_db)):

    new_family = models.FoodFamily(
        self_name=food_family.name
    )
    
    db.add(new_family)

    try:
        db.commit()
        db.refresh(new_family)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error al guardar la receta: {str(e)}")
    
    return {
        "id": new_family.id,
        "name": new_family.self_name
    }

@router.get("/{foodFamilyId}")
async def get_food_family(foodFamilyId: int, db: Session = Depends(get_db)):
    
    db_food_family = db.query(models.FoodFamily).filter(models.FoodFamily.id == foodFamilyId).first()

    if db_food_family is None:
        raise HTTPException(
            status_code=404, 
            detail=f"Food Family with ID {foodFamilyId} not found"
        )

    return {
        "id": db_food_family.id,
        "name": db_food_family.self_name,
    }

@router.delete("/{foodFamilyId}")
async def delete_food_family(foodFamilyId: int, db: Session = Depends(get_db)):
    
    db_food_family = db.query(models.FoodFamily).filter(
        models.FoodFamily.id == foodFamilyId
    ).first()

    if db_food_family is None:
        raise HTTPException(
            status_code=404, 
            detail=f"Food Family with ID {foodFamilyId} not found"
        )

    db.delete(db_food_family)
    db.commit()

    return {
        "message": f"Food family with id {foodFamilyId} successfully deleted"
    }