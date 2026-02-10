from fastapi import FastAPI
from typing import List, Optional

app = FastAPI()

# Definimos el endpoint siguiendo tu estructura:
# Método: GET
# Ruta: /userApi/v1/genericRecipe/{genericRecipeId}
@app.get("/userApi/v1/genericRecipe/{genericRecipeId}")
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

# Para ejecutar esto, usa en la terminal:
# uvicorn nombre_de_tu_archivo:app --reload