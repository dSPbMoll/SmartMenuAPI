from fastapi import APIRouter, Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import schemas
from .account import validate_profile_ownership
from app import models

router = APIRouter(
    prefix="/userApi/v1/ban",
    tags=["Bans"]
)
'''
# ================================= FOOD FAMILY BAN =================================

@router.post("/{accountId}/profile/{profileId}/bans", status_code=201)
async def set_bans(
    accountId: int, 
    profileId: int, 
    foodFamilyIds: schemas.IdList,
    genericIngredientIds: schemas.IdList,
    db: Session = Depends(get_db)
):
    validate_profile_ownership(accountId, profileId, db)

    existing_families = db.query(models.FoodFamily.id).filter(
        models.FoodFamily.id.in_(foodFamilyIds.ids)
    ).all()
    existing_ff_set = {f[0] for f in existing_families}

    existing_ingredients = db.query(models.GenericIngredient.id).filter(
        models.GenericIngredient.id.in_(genericIngredientIds.ids)
    ).all()
    existing_gi_set = {i[0] for i in existing_ingredients}

    failed_family_ids = [id for id in foodFamilyIds.ids if id not in existing_ff_set]
    failed_ingredient_ids = [id for id in genericIngredientIds.ids if id not in existing_gi_set]

    try:
        db.query(models.FoodFamilyBan).filter(
            models.FoodFamilyBan.profile_id == profileId
        ).delete(synchronize_session=False)

        db.query(models.GenericIngredientBan).filter(
            models.GenericIngredientBan.profile_id == profileId
        ).delete(synchronize_session=False)

        new_bans = []
        for ff_id in existing_ff_set:
            new_bans.append(models.FoodFamilyBan(profile_id=profileId, food_family_id=ff_id, account_id=accountId))
        
        for gi_id in existing_gi_set:
            new_bans.append(models.GenericIngredientBan(profile_id=profileId, generic_ingredient_id=gi_id, account_id=accountId))
        
        db.add_all(new_bans)
        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return {
        "status": "Success" if not (failed_family_ids or failed_ingredient_ids) else "Partial Success",
        "failed_family_ids": failed_family_ids,
        "failed_ingredient_ids": failed_ingredient_ids
    }

@router.get("/{accountId}/profile/{profileId}/bans")
async def get_bans(
    accountId: int, 
    profileId: int, 
    db: Session = Depends(get_db)
):
    validate_profile_ownership(accountId, profileId, db)

    db_ff_bans = db.query(models.FoodFamily).join(
        models.FoodFamilyBan, 
        models.FoodFamily.id == models.FoodFamilyBan.food_family_id
    ).filter(
        models.FoodFamilyBan.profile_id == profileId
    ).all()

    db_gi_bans = db.query(models.GenericIngredient).join(
        models.GenericIngredientBan, 
        models.GenericIngredient.id == models.GenericIngredientBan.generic_ingredient_id
    ).filter(
        models.GenericIngredientBan.profile_id == profileId
    ).all()

    return {
        "accountId": accountId,
        "profileId": profileId,
        "bannedFoodFamilies": [family.self_name for family in db_ff_bans],
        "bannedGenericIngredients": [generic_ingredient.self_name for generic_ingredient in db_gi_bans]
    }
'''
