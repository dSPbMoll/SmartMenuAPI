from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    generic_recipe, generic_ingredient, account, food_family,
    recipe_tag, specific_ingredient, specific_recipe, food, meal, ban
)

app = FastAPI(
    title="Smart Menu",
    description="Api for managing recipes, menus and users in SmartMenu app",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


app.include_router(account.router)

app.include_router(food_family.router)
app.include_router(food.router)

app.include_router(recipe_tag.router)
app.include_router(generic_recipe.router)
app.include_router(generic_ingredient.router)
app.include_router(specific_recipe.router)
app.include_router(specific_ingredient.router)

app.include_router(meal.router)

app.include_router(ban.router)

@app.get("/", tags=["Health Check"])
async def root():
    return {
        "status": "Online",
        "message": "Wellcome to the SmartMenu API",
        "docs": "/docs"
    }