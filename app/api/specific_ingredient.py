from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.api import schemas, models

router = APIRouter(
    prefix="/userApi/v1/specific-ingredient",
    tags=["Specific Ingredients"]
)

@router.post("/", status_code=201)
async def create_specific_ingredient(
    ingredient: schemas.SpecificIngredientCreate,
    db: Session = Depends(get_db)
):
    new_ingredient = models.SpecificIngredient(
        self_name = ingredient.name,
        food_family_id = ingredient.food_family_id,
        account_id = ingredient.account_id
    )
    
    db.add(new_ingredient)
    
    try:
        db.commit()
        db.refresh(new_ingredient)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400, 
            detail=f"Error al guardar el ingrediente: {str(e)}"
        )
    
    return {
        "id": new_ingredient.id,
        "accountId": new_ingredient.account_id,
        "name": new_ingredient.self_name,
        "foodId": new_ingredient.food_id
    }

@router.get("/{specificIngredientId}")
async def get_specific_ingredient(specificIngredientId: int, db: Session = Depends(get_db)):

    db_specific_ingredient = db.query(models.SpecificIngredient).filter(
        models.SpecificIngredient.id == specificIngredientId
    ).first()

    if db_specific_ingredient is None:
        raise HTTPException(
            status_code=404, 
            detail=f"Specific Ingredient with ID {specificIngredientId} not found"
        )

    return {
        "id": db_specific_ingredient.id,
        "name": db_specific_ingredient.self_name,
        "food_family_id": db_specific_ingredient.food_family_id,
        "food_id": db_specific_ingredient.food_id
    }

@router.delete("/{specificIngredientId}")
async def delete_specific_ingredient(specificIngredientId: int, db: Session = Depends(get_db)):

    db_specific_ingredient = db.query(models.SpecificIngredient).filter(
        models.SpecificIngredient.id == specificIngredientId
    ).first()

    if db_specific_ingredient is None:
        raise HTTPException(
            status_code=404, 
            detail=f"Specific ingredient with ID {specificIngredientId} not found"
        )

    db.delete(db_specific_ingredient)

    db.commit()