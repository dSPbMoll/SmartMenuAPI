from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.api import schemas, models

router = APIRouter(
    prefix="/userApi/v1/generic-recipe",
    tags=["Generic Recipes"]
)

@router.post("/", status_code=201)
async def create_generic_recipe(recipe: schemas.GenericRecipe, db: Session = Depends(get_db)):
    # 1. Creamos el objeto principal de la receta (Tabla: generic_recipe)
    # No pasamos el 'id' porque es AUTO_INCREMENT en MySQL
    new_recipe = models.GenericRecipe(
        self_name=recipe.self_name,
        cheff_advice=recipe.cheff_advice
    )
    
    # Añadimos a la sesión para que SQLAlchemy genere el ID
    db.add(new_recipe)
    db.flush()  # flush() "envía" la receta a la DB para obtener su ID sin cerrar la transacción

    # 2. Guardamos los pasos (Tabla: generic_recipe_step)
    for step in recipe.steps:
        nuevo_paso = models.GenericRecipeStep(
            generic_recipe_id=new_recipe.id, # Usamos el ID recién generado
            step_number=step.step_number,
            instruction=step.instruction,
            estimated_time=step.estimated_time
        )
        db.add(nuevo_paso)

    # 3. Guardamos las relaciones Muchos a Muchos (Tags e Ingredientes)
    # Nota: Aquí usamos las tablas intermedias que definimos en models.py
    for tag_id in recipe.tagIDs:
        statement = models.recipe_tag_in_generic.insert().values(
            generic_recipe_id=new_recipe.id, 
            recipe_tag_id=tag_id
        )
        db.execute(statement)

    for ing_id in recipe.genericIngredientIDs:
        statement = models.generic_ingredient_in_generic_recipe.insert().values(
            recipe_id=new_recipe.id, 
            ingredient_id=ing_id
        )
        db.execute(statement)

    # 4. Confirmamos todos los cambios en la base de datos
    try:
        db.commit()
        db.refresh(new_recipe)
    except Exception as e:
        db.rollback() # Si algo falla, deshacemos todo para no dejar datos huérfanos
        raise HTTPException(status_code=400, detail=f"Error al guardar la receta: {str(e)}")
    
    return {
        "id": new_recipe.id,
        "foodId": new_recipe.food_id, # El que generó el Trigger
        "self_name": new_recipe.self_name,
        "cheff_advice": new_recipe.cheff_advice,
        
        # Extraemos los IDs de la lista de ingredientes (si tienes la relación)
        "generic_ingredient_ids": [ing.id for ing in new_recipe.ingredients] if hasattr(new_recipe, 'ingredients') else recipe.genericIngredientIDs,
        
        # Formateamos los pasos como una lista de objetos
        "generic_recipe_steps": [
            {
                "step_number": s.step_number,
                "instruction": s.instruction,
                "estimated_time": s.estimated_time
            } for s in new_recipe.steps
        ] if hasattr(new_recipe, 'steps') else [],
        
        "tagIDs": recipe.tagIDs
    }

    '''
    return {
        "id": new_recipe.id,
        "self_name": new_recipe.self_name,
        "cheff_advice": new_recipe.cheff_advice,
        "generic_ingredient_ids": {

        }, "generic_recipe_steps": {

        },"tagIDs": {

        }
    }

    
    class GenericRecipe(BaseModel):
    self_name: str
    cheff_advice: Optional[str] = None

    tagIDs: List[int]
    genericIngredientIDs: List[int]
    steps: List[GenericRecipeStep]

    # For FastAPI to convert models automaticly from DB
    model_config = ConfigDict(from_attributes=True)




    class GenericRecipe(Base):
    __tablename__ = "generic_recipe"
    id = Column(Integer, primary_key=True, autoincrement=True)
    food_id = Column(Integer, ForeignKey("food.id"), nullable=False)
    self_name = Column(String(150), nullable=False)
    cheff_advice = Column(Text)
    '''

# Método: GET
# Ruta: /userApi/v1/genericRecipe/{genericRecipeId}
@router.get("/userApi/v1/genericRecipe/{genericRecipeId}")
async def get_generic_recipe(genericRecipeId: int):
    """
    Simula la obtención de una receta genérica de la BD.
    Devuelve un JSON hardcodeado basado en tus especificaciones.
    """
    
    # Este es el JSON "hardcodeado" (los datos fijos)
    receta_ejemplo = {
        "name": "Paella de la Abuela",
        "tagIDs": [1, 5, 12],
        "genericIngredientIDs": [101, 102, 105, 110],
        "steps": [
            {
                "number": 1,
                "instruction": "Sofreír el conejo y el pollo hasta que estén dorados.",
                "minutes": 15
            },
            {
                "number": 2,
                "instruction": "Añadir el tomate rallado y el azafrán.",
                "minutes": 5
            }
        ],
        "cheffAdvice": "No remuevas el arroz una vez que lo eches al caldo si quieres un buen socarrat."
    }

    # FastAPI convierte automáticamente este diccionario a JSON
    return receta_ejemplo