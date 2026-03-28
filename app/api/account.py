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

# ================================= PROFILES =================================

@router.post("/{accountId}/profile", status_code=201)
async def create_profile(profile: schemas.ProfileCreate, db: Session = Depends(get_db)):

    new_profile = models.Profile(
        self_name = profile.name,
        account_id = profile.account_id
    )
    
    db.add(new_profile)

    try:
        db.commit()
        db.refresh(new_profile)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error while creating the profile: {str(e)}")
    
    return {
        "id": new_profile.id,
        "accountId": new_profile.account_id,
        "profileName": new_profile.name
    }

@router.get("/{accountId}/profile/{profileId}")
async def get_profile(accountId: int, profileId: int, db: Session = Depends(get_db)):
    
    db_account = db.query(models.Account).filter(
        models.Account.id == accountId
    ).first()

    if db_account is None:
        raise HTTPException(
            status_code=404, 
            detail=f"Account with ID {accountId} not found"
        )
    
    db_profile = db.query(models.Profile).filter(
        models.Profile.id == profileId
    ).first()

    if db_profile is None:
        raise HTTPException(
            status_code=404, 
            detail=f"Profile with ID {profileId} not found"
        )

    return {
        "id": db_profile.id,
        "accountId": db_profile.account_id,
        "name": db_profile.name
    }

@router.delete("/{accountId}/profile/{profileId}")
async def delete_profile(accountId: int, profileId: int, db: Session = Depends(get_db)):
    
    db_account = db.query(models.Account).filter(
        models.Account.id == accountId
    ).first()

    if db_account is None:
        raise HTTPException(
            status_code=404, 
            detail=f"Account with ID {accountId} not found"
        )
    
    db_profile = db.query(models.Profile).filter(
        models.Profile.id == profileId
    ).first()

    if db_profile is None:
        raise HTTPException(
            status_code=404, 
            detail=f"Profile with ID {profileId} not found"
        )

    db.delete(db_profile)
    db.commit();

    return {
        "message": f"Profile with ID {profileId} successfuly deleted" 
    }
