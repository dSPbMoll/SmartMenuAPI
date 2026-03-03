from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.api import schemas, models

router = APIRouter(
    prefix="/userApi/v1/food-family",
    tags=["Food Families"]
)

@router.post("/", status_code=201)
async def create_food_family(food_family: schemas.FoodFamily, db: Session = Depends(get_db)):

    new_family = models.FoodFamily(
        self_name=food_family.name
    )
    
    # Añadimos a la sesión para que SQLAlchemy genere el ID
    db.add(new_family)

    # Confirmamos todos los cambios en la base de datos
    try:
        db.commit()
        db.refresh(new_family)
    except Exception as e:
        db.rollback() # Si algo falla, deshacemos todo para no dejar datos huérfanos
        raise HTTPException(status_code=400, detail=f"Error al guardar la receta: {str(e)}")
    
    return {
        "id": new_family.id,
        "name": new_family.self_name
    }

# Método: GET
# Ruta: /userApi/v1/food-family/{foodFamilyId}
@router.get("/{foodFamilyId}")
async def get_food_family(foodFamilyId: int, db: Session = Depends(get_db)):
    
    # 1. Buscamos la familia en la base de datos por su ID
    db_food_family = db.query(models.FoodFamily).filter(models.FoodFamily.id == foodFamilyId).first()

    # 2. Si no existe, lanzamos un error 404
    if db_food_family is None:
        raise HTTPException(
            status_code=404, 
            detail=f"Food Family with ID {foodFamilyId} not found"
        )

    return {
        "id": db_food_family.id,
        "name": db_food_family.self_name,
    }