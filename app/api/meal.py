from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import insert, delete
from sqlalchemy.orm import Session
from app.database import get_db
from app.api import schemas, models

router = APIRouter(
    prefix="/userApi/v1/meal",
    tags=["Meals"]
)

# ================================ MEALS ================================ 

@router.post("/", status_code=201)
async def create_meal(meal: schemas.MealCreate, db: Session = Depends(get_db)):
    new_meal = models.Meal(
        acc_id = meal.account_id,
        eating_moment = meal.eating_moment,
        eaten = meal.eaten,
        datetime = meal.datetime
    )
    
    db.add(new_meal)
    db.flush()

    try:
        db.commit()
        db.refresh(new_meal)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error while saving the meal: {str(e)}")
    
    return {
        "id": new_meal.id,
        "accountId": new_meal.acc_id,
        "eatingMoment": new_meal.eating_moment,
        "eaten": new_meal.eaten,
        "datetime": new_meal.datetime
    }

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

# ================================ FOODS ================================ 

@router.post("/{mealId}/foods")
async def set_foods_to_meal(mealId: int, foodIds: schemas.FoodIdList, db: Session = Depends(get_db)):

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

