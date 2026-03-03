from pydantic import BaseModel, EmailStr, ConfigDict
from typing import List, Optional

class Profile(BaseModel):
    name: str
    account_id: int

class Account(BaseModel):
    username: str
    email: str
    password: str

    profiles: List[Profile]

class DietType(BaseModel):
    name: str

class Goal(BaseModel):
    name: str

class ProfileSettings():
    profileId: int
    dietTypeId: int
    goalId: int
    birthDate: str
    weight: float
    height: float
    waistMeasure: float
    hipsMeasure: float

class FoodFamily(BaseModel):
    name: str

class RecipeTag(BaseModel):
    name: str

class Food(BaseModel):
    id: int

class GenericIngredient(BaseModel):
    name: str
    foodFamilyId: int











class GenericRecipeStep(BaseModel):
    step_number: int
    instruction: str
    estimated_time: Optional[int] = None

class GenericRecipe(BaseModel):
    self_name: str
    cheff_advice: Optional[str] = None

    tagIDs: List[int]
    genericIngredientIDs: List[int]
    steps: List[GenericRecipeStep]

    # For FastAPI to convert models automaticly from DB
    model_config = ConfigDict(from_attributes=True)

