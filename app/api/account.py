from fastapi import APIRouter, Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app import schemas
import re

from app import models

router = APIRouter(
    prefix="/userApi/v1/account",
    tags=["Accounts"]
)

# ================================= AUX TABLES ====================================

@router.get("/diet-types")
async def get_diet_types(db: Session = Depends(get_db)):

    db_diet_types = db.query(models.DietType).all()
    
    return [{
        "id": diet_type.id,
        "name": diet_type.self_name
    } for diet_type in db_diet_types]

@router.get("/goals")
async def get_goals(db: Session = Depends(get_db)):

    db_goals = db.query(models.Goal).all()
    
    return [{
        "id": goal.id,
        "name": goal.self_name
    } for goal in db_goals]

@router.get("/illnesses")
async def get_illnesses(db: Session = Depends(get_db)):

    db_illnesses = db.query(models.Illness).all()
    
    return [{
        "id": illness.id,
        "name": illness.self_name
    } for illness in db_illnesses]

# ================================= ACCOUNTS =================================

@router.post("/", status_code=201)
async def create_account(account: schemas.AccountCreate, db: Session = Depends(get_db)):

    account_exists = db.query(models.Account).filter(
        models.Account.email == account.email
    ).first()

    if account_exists:
        raise HTTPException(status_code=400, detail=f"The email {account.email} is already being used by an account")

    new_account = models.Account(
        username = account.username,
        email = account.email,
        password = account.password
    )
    
    db.add(new_account)

    try:
        db.commit()
        db.refresh(new_account)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error while creating the account: {str(e)}")
    
    return {
        "id": new_account.id,
        "username": new_account.username,
        "email": new_account.email,
        "password": new_account.password
    }

@router.get("/{accountId}")
async def get_account(accountId: int, db: Session = Depends(get_db)):
    
    db_account = db.query(models.Account).filter(models.Account.id == accountId).first()

    if db_account is None:
        raise HTTPException(
            status_code=404, 
            detail=f"Account with ID {accountId} not found"
        )

    return {
        "id": db_account.id,
        "username": db_account.username,
        "email": db_account.email,
        "password": db_account.password
    }

@router.delete("/{accountId}")
async def delete_account(accountId: int, db: Session = Depends(get_db)):
    
    db_account = db.query(models.Account).filter(models.Account.id == accountId).first()

    if db_account is None:
        raise HTTPException(
            status_code=404, 
            detail=f"Account with ID {accountId} not found"
        )

    db.delete(db_account)
    db.commit();

    return {
        "message": f"Account with ID {accountId} successfuly deleted" 
    }

@router.post("/login")
async def login(data: schemas.Login, db: Session = Depends(get_db)):
    
    db_user = db.query(models.Account).filter(
        data.email == models.Account.email,
        data.password == models.Account.password
    ).first()

    if db_user is None:
        return {"result": "NOT OK"}
    else:
        return {
            "result": "OK",
            "account": {
                "id": db_user.id,
                "username": db_user.username,
                "email": db_user.email
            } 
        }

# ================================= PROFILES =================================

@router.post("/{accountId}/profile", status_code=201)
async def create_profile(profile: schemas.ProfileCreate, accountId: int,  db: Session = Depends(get_db)):

    new_profile = models.Profile(
        self_name = profile.name,
        account_id = accountId
    )
    
    db.add(new_profile)

    try:
        db.commit()
        db.refresh(new_profile)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error while creating the profile: {str(e)}")
    
    return {
        "id": new_profile.id,
        "accountId": new_profile.account_id,
        "profileName": new_profile.self_name
    }

@router.get("/{accountId}/profile/{profileId}")
async def get_profile(accountId: int, profileId: int, db: Session = Depends(get_db)):
    
    db_profile = validate_profile_ownership(accountId, profileId, db)

    return {
        "id": db_profile.id,
        "accountId": db_profile.account_id,
        "name": db_profile.self_name
    }

@router.get("/{accountId}/profiles/")
async def get_profiles(accountId: int, db: Session = Depends(get_db)):
    
    db_profiles = db.query(models.Profile).filter(
        models.Profile.account_id == accountId
    ).all()

    return [
        {
            "id": profile.id,
            "accountId": profile.account_id,
            "name": profile.self_name
        } 
        for profile in db_profiles
    ]

@router.delete("/{accountId}/profile/{profileId}")
async def delete_profile(accountId: int, profileId: int, db: Session = Depends(get_db)):
    
    db_profile = validate_profile_ownership(accountId, profileId, db)

    db.delete(db_profile)
    db.commit()

    return {
        "message": f"Profile with ID {profileId} successfully deleted" 
    }


# =-------------- Profile Settings

@router.post("/{accountId}/profile/{profileId}/settings", status_code=201)
async def set_profile_settings(
    profileSettings: schemas.ProfileSettingsCreate,
    accountId: int,
    profileId:int,
    db: Session = Depends(get_db)):

    validate_profile_ownership(accountId, profileId, db)

    new_settings = models.ProfileSettings(
        profile_id = profileSettings.profile_id,
        diet_type_id = profileSettings.diet_type_id,
        goal_id = profileSettings.goal_id,
        birth_date = profileSettings.birth_date,
        weight = profileSettings.weight,
        height = profileSettings.height,
        waist_measure = profileSettings.waist_measure,
        hips_measure = profileSettings.hips_measure,
        sex = profileSettings.sex,
        activity_level = profileSettings.activity_level
    )

    db_settings = db.query(models.ProfileSettings).filter(
        models.ProfileSettings.profile_id == profileId
    ).first()

    if (db_settings):
        db.delete(db_settings)

    db.add(new_settings)

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error while setting the profile's settings: {str(e)}")
    
    return {
        "profile_id": new_settings.profile_id,
        "diet_type_id": new_settings.diet_type_id,
        "goal_id": new_settings.goal_id,
        "birth_date": new_settings.birth_date,
        "weight": new_settings.weight,
        "height": new_settings.height,
        "waist_measure": new_settings.waist_measure,
        "hips_measure": new_settings.hips_measure,
        "sex": new_settings.sex,
        "activity_level": new_settings.activity_level
    }

@router.get("/{accountId}/profile/{profileId}/settings", status_code=201)
async def get_profile_settings(accountId: int, profileId:int, db: Session = Depends(get_db)):

    validate_profile_ownership(accountId, profileId, db)

    db_settings = db.query(models.ProfileSettings).filter(
        models.ProfileSettings.profile_id == profileId
    ).first()

    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Error while setting the profile's settings: {str(e)}")
    
    return {
        "profile_id": db_settings.profile_id,
        "diet_type_id": db_settings.diet_type_id,
        "goal_id": db_settings.goal_id,
        "birth_date": db_settings.birth_date,
        "weight": db_settings.weight,
        "height": db_settings.height,
        "waist_measure": db_settings.waist_measure,
        "hips_measure": db_settings.hips_measure
    }

@router.post("/{accountId}/profile/{profileId}/illnesses", status_code=201)
async def set_profile_illnesses(
    accountId: int, 
    profileId: int, 
    illnessIds: schemas.IdList,
    db: Session = Depends(get_db)):
    validate_profile_ownership(accountId, profileId, db)

    existing_illnesses = db.query(models.Illness.id).filter(
        models.Illness.id.in_(illnessIds.ids)
    ).all()
    
    existing_illness_set = {i[0] for i in existing_illnesses}

    failed_illness_ids = [id for id in illnessIds.ids if id not in existing_illness_set]

    try:
        db.query(models.IllnessInProfile).filter(
            models.IllnessInProfile.profile_id == profileId
        ).delete(synchronize_session=False)

        new_illnesses = []
        for ill_id in existing_illness_set:
            new_illnesses.append(
                models.IllnessInProfile(
                    profile_id=profileId, 
                    illness_id=ill_id
                )
            )
        
        db.add_all(new_illnesses)
        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Error al actualizar las enfermedades: {str(e)}"
        )

    return {
        "status": "Success" if not failed_illness_ids else "Partial Success",
        "message": "Enfermedades actualizadas correctamente",
        "failed_illness_ids": failed_illness_ids
    }

@router.get("/{accountId}/profile/{profileId}/illnesses")
async def get_profile_illnesses(
    accountId: int, 
    profileId: int, 
    db: Session = Depends(get_db)):
    # 1. Validar propiedad del perfil
    validate_profile_ownership(accountId, profileId, db)

    # 2. Consultar las enfermedades uniendo con la tabla asociativa
    db_illnesses = db.query(models.Illness).join(
        models.IllnessInProfile, 
        models.Illness.id == models.IllnessInProfile.illness_id
    ).filter(
        models.IllnessInProfile.profile_id == profileId
    ).all()

    # 3. Retornar la respuesta con el formato solicitado
    return {
        "accountId": accountId,
        "profileId": profileId,
        "illnesses": [
            {
                "id": illness.id,
                "name": illness.self_name
            } for illness in db_illnesses
        ]
    }

@router.post("/{accountId}/profile/{profileId}/bans", status_code=201)
async def set_bans(
    accountId: int, 
    profileId: int, 
    foodFamilyIds: schemas.IdList,
    genericIngredientIds: schemas.IdList,
    db: Session = Depends(get_db)):

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
            new_bans.append(models.FoodFamilyBan(profile_id=profileId, food_family_id=ff_id))
        
        for gi_id in existing_gi_set:
            new_bans.append(models.GenericIngredientBan(profile_id=profileId, ingredient_id=gi_id))
        
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
    db: Session = Depends(get_db)):

    validate_profile_ownership(accountId, profileId, db)

    db_ff_bans = db.query(models.FoodFamily).join(
        models.FoodFamilyBan, 
        models.FoodFamily.id == models.FoodFamilyBan.food_family_id
    ).filter(
        models.FoodFamilyBan.profile_id == profileId
    ).all()

    db_gi_bans = db.query(models.GenericIngredient).join(
        models.GenericIngredientBan, 
        models.GenericIngredient.id == models.GenericIngredientBan.ingredient_id
    ).filter(
        models.GenericIngredientBan.profile_id == profileId
    ).all()

    return {
        "accountId": accountId,
        "profileId": profileId,
        "bannedFoodFamilies": [family.self_name for family in db_ff_bans],
        "bannedGenericIngredients": [generic_ingredient.self_name for generic_ingredient in db_gi_bans]
    }


# ================================= AUX FUNCTIONS =================================

def validate_profile_ownership(accountId: int, profileId: int, db: Session):

    db_account = db.query(models.Account).filter(
        models.Account.id == accountId
    ).first()
    
    if not db_account:
        raise HTTPException(
            status_code=404, 
            detail=f"Account with ID {accountId} not found"
        )
    
    db_profile = db.query(models.Profile).filter(
        models.Profile.id == profileId,
        models.Profile.account_id == accountId
    ).first()

    if not db_profile:
        raise HTTPException(
            status_code=404, 
            detail=f"Profile with ID {profileId} belonging to account {accountId} not found"
        )
    
    return db_profile
