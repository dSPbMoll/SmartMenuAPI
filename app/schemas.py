from pydantic import BaseModel, EmailStr, ConfigDict
from typing import List, Optional
from enum import Enum
from datetime import datetime

# ============================== USERS ==============================

class AccountCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class Account(AccountCreate):
    id: int

class ProfileCreate(BaseModel):
    name: str

class Profile(ProfileCreate):
    id: int

    account: Account
    model_config = ConfigDict(from_attributes=True)

class DietType(BaseModel):
    name: str

class Goal(BaseModel):
    name: str

class ProfileSettings(BaseModel):
    profile_id: int
    diet_type_id: int
    goalId: int
    birth_date: str
    weight: float
    height: float
    waist_measure: float
    hips_measure: float

# ============================== MEALS ==============================

class EatingMoment(str, Enum):
    breakfast = "breakfast"
    mid_morning_snack = "mid_morning_snack"
    lunch = "lunch"
    afternoon_snack = "afternoon_snack"
    dinner = "dinner"

class MealCreate(BaseModel):
    account_id: int
    eating_moment: EatingMoment
    eaten: bool
    datetime: datetime

class Meal(MealCreate):
    id: int

    account: Account
    model_config = ConfigDict(from_attributes=True)


# ============================== RECIPES ==============================
# ---------------- RECIPE TAGS

class RecipeTagCreate(BaseModel):
    name: str

class RecipeTag(RecipeTagCreate):
    id: int

class RecipeTagIdList(BaseModel):
    ids: List[int]

# -------------- RECIPES

class GenericRecipeCreate(BaseModel):
    name: str
    cheff_advice: Optional[str] = None

class GenericRecipe(GenericRecipeCreate):
    id: int
    food_id: int

class SpecificRecipeCreate(BaseModel):
    name: str
    cheff_advice: Optional[str] = None
    account_id: int

class SpecificRecipe(BaseModel):
    id: int
    food_id: int

# ---------------- RECIPE STEPS

class GenericRecipeStepCreate(BaseModel):
    generic_recipe_id: int
    step_number: int
    instruction: str
    estimated_time: Optional[int] = None

class GenericRecipeStep(GenericRecipeStepCreate):
    generic_recipe: GenericRecipe

class GenericRecipeStepList(BaseModel):
    steps: List[GenericRecipeStep] 

class SpecificRecipeStepCreate(BaseModel):
    specific_recipe_id: int
    step_number: int
    instruction: str
    estimated_time: Optional[int] = None

class SpecificRecipeStep(SpecificRecipeStepCreate):
    specific_recipe: SpecificRecipe

class SpecificRecipeStepList(BaseModel):
    steps: List[SpecificRecipeStep] 

# ============================== INGREDIENTS ==============================

class genericIngredientIdList(BaseModel):
    ids: List[int]

class specificIngredientIdList(BaseModel):
    ids: List[int]

class ingredientNameListAI(BaseModel):
    ingredient_list: List[str]

# ------ Food

class FoodIdList(BaseModel):
    ids: List[int]

class Food(BaseModel):
    id: int

class FoodFamily(BaseModel):
    name: str

# ------ Generic

class GenericIngredientCreate(BaseModel):
    name: str
    food_family_id: int

class GenericIngredient(GenericIngredientCreate):
    id: int
    food_id: int

    # Relations
    food_family: Optional[FoodFamily] = None
    model_config = ConfigDict(from_attributes=True)



# ------ Specific

class SpecificIngredientCreate(BaseModel):
    name: str
    food_family_id: int
    account_id: int

class SpecificIngredient(SpecificIngredientCreate):
    id: int
    food_id: int

    # Relations
    food_family: Optional[FoodFamily] = None
    model_config = ConfigDict(from_attributes=True)
