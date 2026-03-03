from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.api import schemas, models

router = APIRouter(
    prefix="/userApi/v1/generic-recipe-step",
    tags=["Generic Recipe Steps"]
)

@router.post("/", status_code=201)
async def create_generic_recipe_step(
    step: schemas.GenericRecipeStep,
    db: Session = Depends(get_db)
):
    # Creamos el objeto SIN food_id (el trigger se encargará de él)
    new_step = models.GenericRecipeStep(
        generic_recipe_id = step.genericRecipeId,
        step_number = step.stepNumber,
        instruction = step.instruction,
        estimated_time = step.estimatedTime
    )
    
    db.add(new_step)
    
    # Confirmamos todos los cambios en la base de datos
    try:
        db.commit()
        db.refresh(new_step)
    except Exception as e:
        db.rollback() # Si algo falla, deshacemos todo para no dejar datos huérfanos
        raise HTTPException(status_code=400, detail=f"Error al guardar la receta: {str(e)}")
    
    return {
        "generic_recipe_id": new_step.generic_recipe_id,
        "step_number": new_step.step_number,
        "instruction": new_step.instruction,
        "estimated_time": new_step.estimated_time
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