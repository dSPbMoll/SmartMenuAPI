from sqlalchemy import Column, Integer, String, Text, ForeignKey, Numeric, Date, DateTime, Boolean, Enum, Table
from sqlalchemy.orm import relationship
from app.database import Base

# ============================== USERS ==============================

class Account(Base):
    __tablename__ = "account"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False)
    email = Column(String(320), nullable=False, unique=True)
    password = Column(String(255), nullable=False)

class Profile(Base):
    __tablename__ = "profile"
    id = Column(Integer, primary_key=True, autoincrement=True)
    self_name = Column(String(50))
    account_id = Column(Integer, ForeignKey("account.id", ondelete="CASCADE"), nullable=False)

class DietType(Base):
    __tablename__ = "diet_type"
    id = Column(Integer, primary_key=True, autoincrement=True)
    self_name = Column(String(100), nullable=False)

class Goal(Base):
    __tablename__ = "goal"
    id = Column(Integer, primary_key=True, autoincrement=True)
    self_name = Column(String(100), nullable=False)

class Illness(Base):
    __tablename__ = "illness"
    id = Column(Integer, primary_key=True, autoincrement=True)
    self_name = Column(String(100), nullable=False)

class ProfileSettings(Base):
    __tablename__ = "profile_settings"
    profile_id = Column(Integer, primary_key=True, autoincrement=True)
    diet_type_id = Column(Integer, ForeignKey("diet_type.id"))
    goal_id = Column(Integer, ForeignKey("goal.id"))
    birth_date = Column(Date)
    weight = Column(Numeric(5, 2))
    height = Column(Numeric(5, 2))
    waist_measure = Column(Numeric(5, 2))
    hips_measure = Column(Numeric(5, 2))
    sex = Column(Enum("male", "female"),
        nullable=False,
        default="male")
    activity_level = Column(Enum("very low", "low", "mid", "high", "very high"),
        nullable=False,
        default="mid")

class IllnessInProfile(Base):
    __tablename__ = "illness_in_profile_settings"
    profile_id = Column(Integer, ForeignKey("profile_settings.profile_id"), primary_key=True)
    illness_id = Column(Integer, ForeignKey("illness.id"), primary_key=True)

class FoodFamilyBan(Base):
    __tablename__ = "food_family_ban"
    profile_id = Column(Integer, ForeignKey("profile.id"), primary_key=True)
    food_family_id = Column(Integer, ForeignKey("food_family.id"), primary_key=True)
    is_blacklisted = Column(Boolean)

class GenericIngredientBan(Base):
    __tablename__ = "generic_ingredient_ban"
    profile_id = Column(Integer, ForeignKey("profile.id"), primary_key=True)
    ingredient_id = Column(Integer, ForeignKey("generic_ingredient.id"), primary_key=True)
    is_blacklisted = Column(Boolean)

# ============================== MEALS ==============================

class Meal(Base):
    __tablename__ = "meal"
    id = Column(Integer, primary_key=True, autoincrement=True)
    acc_id = Column(Integer, ForeignKey("account.id"))
    eating_moment = Column(
        Enum("breakfast", "mid_morning_snack", "lunch", "afternoon_snack", "dinner"),
        nullable=False,
        default="lunch"
    )
    eaten = Column(Boolean)
    datetime = Column(DateTime)
    #Relations
    foods = relationship("Food", secondary="food_in_meal", backref="meals")
    profiles = relationship("Profile", secondary="profile_in_meal", backref="meals")

food_in_meal = Table(
    "food_in_meal", Base.metadata,
    Column("food_id", Integer, ForeignKey("food.id"), primary_key=True),
    Column("meal_id", Integer, ForeignKey("meal.id"), primary_key=True)
)

profile_in_meal = Table(
    "profile_in_meal", Base.metadata,
    Column("profile_id", Integer, ForeignKey("profile.id"), primary_key=True),
    Column("meal_id", Integer, ForeignKey("meal.id"), primary_key=True)
)

# ============================== RECIPES ==============================

recipe_tag_in_generic = Table(
    "recipe_tag_in_generic", Base.metadata,
    Column("generic_recipe_id", Integer, ForeignKey("generic_recipe.id"), primary_key=True),
    Column("recipe_tag_id", Integer, ForeignKey("recipe_tag.id"), primary_key=True)
)

recipe_tag_in_specific = Table(
    "recipe_tag_in_specific", Base.metadata,
    Column("specific_recipe_id", Integer, ForeignKey("specific_recipe.id"), primary_key=True),
    Column("recipe_tag_id", Integer, ForeignKey("recipe_tag.id"), primary_key=True)
)

generic_ingredient_in_generic_recipe = Table(
    "generic_ingredient_in_generic_recipe", Base.metadata,
    Column("recipe_id", Integer, ForeignKey("generic_recipe.id"), primary_key=True),
    Column("ingredient_id", Integer, ForeignKey("generic_ingredient.id"), primary_key=True)
)

generic_ingredient_in_specific_recipe = Table(
    "generic_ingredient_in_specific_recipe", Base.metadata,
    Column("recipe_id", Integer, ForeignKey("specific_recipe.id"), primary_key=True),
    Column("ingredient_id", Integer, ForeignKey("generic_ingredient.id"), primary_key=True)
)

specific_ingredient_in_specific_recipe = Table(
    "specific_ingredient_in_specific_recipe", Base.metadata,
    Column("recipe_id", Integer, ForeignKey("specific_recipe.id"), primary_key=True),
    Column("ingredient_id", Integer, ForeignKey("specific_ingredient.id"), primary_key=True)
)

class RecipeTag(Base):
    __tablename__ = "recipe_tag"
    id = Column(Integer, primary_key=True, autoincrement=True)
    self_name = Column(String(50), nullable=False, unique=True)

class GenericRecipe(Base):
    __tablename__ = "generic_recipe"
    id = Column(Integer, primary_key=True, autoincrement=True)
    food_id = Column(Integer, ForeignKey("food.id"), nullable=False)
    self_name = Column(String(150), nullable=False)
    cheff_advice = Column(Text)

    food_node = relationship("Food", back_populates="generic_recipe")

class SpecificRecipe(Base):
    __tablename__ = "specific_recipe"
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("account.id"), nullable=False)
    food_id = Column(Integer, ForeignKey("food.id"))
    self_name = Column(String(150), nullable=False)
    chef_advice = Column(Text)

    food_node = relationship("Food", back_populates="specific_recipe")

class GenericRecipeStep(Base):
    __tablename__ = "generic_recipe_step"
    generic_recipe_id = Column(Integer, ForeignKey("generic_recipe.id", ondelete="CASCADE"), primary_key=True)
    step_number = Column(Integer, primary_key=True)
    instruction = Column(Text, nullable=False)
    estimated_time = Column(Integer)  # In minutes

class SpecificRecipeStep(Base):
    __tablename__ = "specific_recipe_step"
    specific_recipe_id = Column(Integer, ForeignKey("specific_recipe.id", ondelete="CASCADE"), primary_key=True)
    step_number = Column(Integer, primary_key=True)
    instruction = Column(Text, nullable=False)
    estimated_time = Column(Integer)  # In minutes

# ============================== INGREDIENTS ==============================

class Food(Base):
    __tablename__ = "food"
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Define the relations towards the possible "childs"
    generic_ingredient = relationship("GenericIngredient", back_populates="food_node", uselist=False)
    specific_ingredient = relationship("SpecificIngredient", back_populates="food_node", uselist=False)
    generic_recipe = relationship("GenericRecipe", back_populates="food_node", uselist=False)
    specific_recipe = relationship("SpecificRecipe", back_populates="food_node", uselist=False)

class FoodFamily(Base):
    __tablename__ = "food_family"
    id = Column(Integer, primary_key=True, autoincrement=True)
    self_name = Column(String(100), nullable=False)

class GenericIngredient(Base):
    __tablename__ = "generic_ingredient"
    id = Column(Integer, primary_key=True, autoincrement=True)
    self_name = Column(String(100))
    food_family_id = Column(Integer, ForeignKey("food_family.id"), nullable=False)
    food_id = Column(Integer, ForeignKey("food.id"), nullable=False)

    food_family = relationship("FoodFamily")
    food_node = relationship("Food", back_populates="generic_ingredient")

class SpecificIngredient(Base):
    __tablename__ = "specific_ingredient"
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("account.id"), nullable=False)
    self_name = Column(String(100), nullable=False)
    food_family_id = Column(Integer, ForeignKey("food_family.id"))
    food_id = Column(Integer, ForeignKey("food.id"))

    food_family = relationship("FoodFamily")
    food_node = relationship("Food", back_populates="specific_ingredient")
