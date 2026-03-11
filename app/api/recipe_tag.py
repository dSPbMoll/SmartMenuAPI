from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app import schemas
from app import models

router = APIRouter(
    prefix="/userApi/v1/recipe_tag",
    tags=["Recipe Tags"]
)

@router.post("/", status_code=201)
async def create_recipe_tag(tag: schemas.RecipeTagCreate, db: Session = Depends(get_db)):

    new_tag = models.RecipeTag(
        self_name = tag.name,
    )
    
    db.add(new_tag)
    db.commit()
    
    return {
        "id": new_tag.id,
        "self_name": new_tag.self_name,
    }

@router.get("/{recipeTagId}")
async def get_recipe_tag(recipeTagId: int, db: Session = Depends(get_db)):

    db_recipe_tag = db.query(models.RecipeTag).filter(
        models.RecipeTag.id == recipeTagId
    ).first()

    if db_recipe_tag is None:
        raise HTTPException(
            status_code=404, 
            detail=f"Recipe tag with ID {db_recipe_tag.id} not found"
        )

    return {
        "id": db_recipe_tag.id,
        "self_name": db_recipe_tag.self_name,
    }

@router.delete("/{recipeTagId}")
async def delete_recipe_tag(recipeTagId: int, db: Session = Depends(get_db)):

    db_recipe_tag = db.query(models.RecipeTag).filter(
        models.RecipeTag.id == recipeTagId
    ).first()

    if db_recipe_tag is None:
        raise HTTPException(
            status_code=404, 
            detail=f"Recipe tag with ID {db_recipe_tag.id} not found"
        )

    db.delete(db_recipe_tag)
    db.commit()

    return {
        "message": f"Recipe tag with id {recipeTagId} successfully deleted"
    }
