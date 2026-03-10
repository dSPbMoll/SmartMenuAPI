from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from app.database import get_db
from app.api import schemas, models
from google import genai
from google.genai import types
import json
import os
from dotenv import load_dotenv

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

# ===================================== AI ========================================

load_dotenv()
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY"),
    http_options={'api_version': 'v1beta'} 
)

@router.post("/ai-detect")
async def detect_ingredients(file: UploadFile = File(...)):
    # 1. Leer los bytes de la imagen que envía el móvil
    image_bytes = await file.read()
    
    # 2. Preparar el contenido para Gemini (Texto + Imagen)
    prompt = [
        "Identifica todos los ingredientes de cocina presentes en esta imagen. "
        "Devuelve una lista simple de strings en formato JSON: {'ingredients': ['item1', 'item2']}",
        types.Part.from_bytes(data=image_bytes, mime_type=file.content_type)
    ]

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash", # <--- Prueba este nombre simplificado
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        return json.loads(response.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
