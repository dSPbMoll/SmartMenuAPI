from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Importamos los routers de los archivos que crearás después
# Suponiendo que tus archivos están en una carpeta llamada 'routers'
from app.api import generic_recipe, generic_ingredient, account, food_family, generic_recipe_step, recipe_tag

app = FastAPI(
    title="Smart Menu",
    description="Api for managing recipes, menus and users in SmartMenu app",
    version="1.0.0"
)

# 1. Configuración de CORS
# Mantenemos lo que ya tenías, que es vital para que el Frontend conecte
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# 2. Inclusión de Rutas (Modularización)
# Aquí es donde "limpiamos" el main.py
app.include_router(recipe_tag.router)
app.include_router(generic_recipe.router)
app.include_router(generic_recipe_step.router)
app.include_router(generic_ingredient.router)
app.include_router(account.router)
app.include_router(food_family.router)
# app.include_router(users.router)

# 3. Endpoint de salud (Opcional pero recomendado)
@app.get("/", tags=["Health Check"])
async def root():
    return {
        "status": "online",
        "message": "Wellcome to the SMartMenu API",
        "docs": "/docs"
    }