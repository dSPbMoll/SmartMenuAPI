from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.api import schemas, models

router = APIRouter(
    prefix="/userApi/v1/generic-ingredient",
    tags=["Generic Ingredients"]
)

@router.post("/", status_code=201)
async def create_generic_ingredient(
    ingredient: schemas.GenericIngredient, # Usamos el schema sin foodId
    db: Session = Depends(get_db)
):
    # Creamos el objeto SIN food_id (el trigger se encargará de él)
    new_ingredient = models.GenericIngredient(
        self_name=ingredient.name,
        food_family_id=ingredient.foodFamilyId
    )
    
    db.add(new_ingredient)
    
    try:
        # Al hacer commit, se dispara el trigger BEFORE INSERT en la DB
        db.commit()
        # Refresh recupera los datos que el trigger insertó (el food_id)
        db.refresh(new_ingredient)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400, 
            detail=f"Error al guardar el ingrediente: {str(e)}"
        )
    
    return {
        "id": new_ingredient.id,
        "name": new_ingredient.self_name,
        "foodId": new_ingredient.food_id
    }

# Método: GET
# Ruta: /userApi/v1/genericRecipe/{genericRecipeId}
@router.get("/{genericIngredientId}")
async def get_generic_ingredient(genericIngredientId: int, db: Session = Depends(get_db)):

    # 1. Buscamos la familia en la base de datos por su ID
    db_generic_ingredient = db.query(models.GenericIngredient).filter(models.GenericIngredient.id == genericIngredientId).first()

    # 2. Si no existe, lanzamos un error 404
    if db_generic_ingredient is None:
        raise HTTPException(
            status_code=404, 
            detail=f"Generic Ingredient with ID {genericIngredientId} not found"
        )

    return {
        "id": db_generic_ingredient.id,
        "name": db_generic_ingredient.self_name,
        "food_family_id": db_generic_ingredient.food_family_id,
        "food_id": db_generic_ingredient.food_id
    }