from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.api import schemas, models

router = APIRouter(
    prefix="/userApi/v1/recipe_tag",
    tags=["Recipe Tags"]
)

@router.post("/", status_code=201)
async def create_recipe_tag(
    tag: schemas.RecipeTag,
    db: Session = Depends(get_db)
):
    # Creamos el objeto SIN food_id (el trigger se encargará de él)
    new_tag = models.RecipeTag(
        self_name=tag.name,
    )
    
    db.add(new_tag)
    
    try:
        # Al hacer commit, se dispara el trigger BEFORE INSERT en la DB
        db.commit()
        # Refresh recupera los datos que el trigger insertó (el food_id)
        db.refresh(new_tag)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=400, 
            detail=f"Error al guardar el ingrediente: {str(e)}"
        )
    
    return {
        "id": new_tag.id,
        "self_name": new_tag.self_name,
    }

# Método: GET
# Ruta: /userApi/v1/genericRecipe/{genericRecipeId}
@router.get("/{recipeTagId}")
async def get_recipe_tag(recipeTagId: int, db: Session = Depends(get_db)):

    # 1. Buscamos la familia en la base de datos por su ID
    db_recipe_tag = db.query(models.RecipeTag).filter(models.RecipeTag.id == recipeTagId).first()

    # 2. Si no existe, lanzamos un error 404
    if db_recipe_tag is None:
        raise HTTPException(
            status_code=404, 
            detail=f"Generic Ingredient with ID {db_recipe_tag} not found"
        )

    return {
        "id": db_recipe_tag.id,
        "self_name": db_recipe_tag.self_name,
    }