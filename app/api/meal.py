from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import insert, delete, or_, and_, not_
from sqlalchemy.orm import Session
from app.database import get_db
from app import schemas
from app import models
from app.api.account import validate_profile_ownership

router = APIRouter(
    prefix="/userApi/v1/meal",
    tags=["Meals"]
)

# ================================ MEALS ================================ 

@router.post("/", status_code=201)
async def create_meal(meal: schemas.MealCreate, db: Session = Depends(get_db)):
    # Clean duplicates
    unique_food_ids = list(set(meal.foodIds))
    unique_profile_ids = list(set(meal.profilIds))

    # Profile verifying
    valid_profiles_count = db.query(models.Profile).filter(
        models.Profile.id.in_(unique_profile_ids),
        models.Profile.account_id == meal.account_id
    ).count()

    if valid_profiles_count != len(unique_profile_ids):
        raise HTTPException(status_code=403, detail="Uno o más perfiles no pertenecen a esta cuenta.")

    # Food validations
    valid_foods = db.query(models.Food.id).outerjoin(
        models.SpecificIngredient, models.Food.id == models.SpecificIngredient.food_id
    ).outerjoin(
        models.SpecificRecipe, models.Food.id == models.SpecificRecipe.food_id
    ).filter(
        models.Food.id.in_(unique_food_ids),
        or_(
            # Specific ingredient that belongs to the user
            models.SpecificIngredient.account_id == meal.account_id,
            # Specific recipe that belongs to the user
            models.SpecificRecipe.account_id == meal.account_id,
            # Is generic
            and_(
                models.SpecificIngredient.account_id.is_(None),
                models.SpecificRecipe.account_id.is_(None)
            )
        )
    ).all()

    valid_food_ids = [f.id for f in valid_foods]

    if len(valid_food_ids) != len(unique_food_ids):
        invalid_ids = set(unique_food_ids) - set(valid_food_ids)
        raise HTTPException(
            status_code=403, 
            detail=f"No tienes permiso sobre los food_ids: {list(invalid_ids)}"
        )

    new_meal = models.Meal(
        acc_id=meal.account_id,
        eating_moment=meal.eating_moment,
        eaten=meal.eaten,
        datetime=meal.datetime
    )

    db_foods = db.query(models.Food).filter(models.Food.id.in_(valid_food_ids)).all()
    db_profiles = db.query(models.Profile).filter(models.Profile.id.in_(unique_profile_ids)).all()

    new_meal.foods = db_foods
    new_meal.profiles = db_profiles
    
    try:
        db.add(new_meal)
        db.commit()
        db.refresh(new_meal)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error al guardar: {str(e)}")

    return new_meal

@router.get("/{mealId}")
async def get_meal(mealId: int, db: Session = Depends(get_db)):

    db_meal = db.query(models.Meal).filter(
        models.Meal.id == mealId
    ).first()

    if not db_meal:
        raise HTTPException(
            status_code=404, 
            detail=f"Meal with ID {mealId} not found"
        )

    account = db.query(models.Account).filter(
        models.Account.id == db_meal.acc_id
    ).first()

    foods = db.query(models.Food).join(models.food_in_meal).filter(
        models.food_in_meal.c.meal_id == mealId
    ).all()

    '''
    THIS IS MEANT FOR THE FAMILIES PLAN THAT IS NOT IMPLEMENTED

    profiles = db.query(models.Profile).join(models.profile_in_meal).filter(
        models.profile_in_meal.c.meal_id == mealId
    ).all()
    '''

    return {
        "id": db_meal.id,
        "eatingMoment": db_meal.eating_moment,
        "eaten": db_meal.eaten,
        "datetime": db_meal.datetime,
        "account": {
            "id": account.id,
            "username": account.username,
            "email": account.email
        },
        "foodIds": [
            {
                "id": f.id
            } for f in foods
        ]
    }

@router.delete("/{mealId}")
async def delete_meal(mealId: int, db: Session = Depends(get_db)):

    db_meal = db.query(models.Meal).filter(
        models.Meal.id == mealId
    ).first()
    if not db_meal:
        raise HTTPException(status_code=404, detail="Meal not found")

    db.delete(db_meal)
    db.commit()

    return {"message": f"Successfully deleted meal with id {mealId}."}

@router.get("/account/{accountId}")
async def get_meals_from_account(accountId: int, db: Session = Depends(get_db)):
    
    db_meals = db.query(models.Meal).filter(
        models.Meal.acc_id == accountId
    ).all()

    return {
        "accountId": accountId,
        "meals": [{
            "id": m.id,
            "eatingMoment": m.eating_moment,
            "eaten": m.eaten,
            "datetime": m.datetime,
            "foods": [
                {
                    "foodId": f.id,
                    "name": (
                        f.generic_recipe.self_name if getattr(f, 'generic_recipe', None) else
                        f.specific_recipe.self_name if getattr(f, 'specific_recipe', None) else
                        f.generic_ingredient.self_name if getattr(f, 'generic_ingredient', None) else
                        f.specific_ingredient.self_name if getattr(f, 'specific_ingredient', None) else
                        "Unknown Food"
                    )
                } for f in m.foods
            ]
        } for m in db_meals]
    }

# ================================ FOODS ================================ 

@router.post("/{mealId}/foods")
async def set_foods_to_meal(mealId: int, foodIds: schemas.IdList, db: Session = Depends(get_db)):

    db_meal = db.query(models.Meal).filter(
        models.Meal.id == mealId
    ).first()
    if not db_meal:
        raise HTTPException(status_code=404, detail = f"Meal with id {mealId} not found")

    db.execute(
        delete(models.food_in_meal).where(
            models.food_in_meal.c.meal_id == mealId
        )
    )

    if foodIds.ids:
        food_associations = [
            {"food_id": f_id, "meal": mealId}
            for f_id in set(foodIds.ids)
        ]
        db.execute(insert(models.food_in_meal).values(food_associations))

    db.commit()
    return {"message": f"Foods updated. Meal {mealId} now has {len(foodIds.ids)} foods."}

