from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.preferences import Preferences
from app.schemas.preferences import PreferencesCreate, PreferencesUpdate, PreferencesOut
from app.core.security import get_current_user
from app.services.auth_service import get_user_by_email

router = APIRouter()

@router.post("/", response_model=PreferencesOut)
def create_preferences(
    preferences: PreferencesCreate,
    current_user_email: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = get_user_by_email(db, current_user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    existing_prefs = db.query(Preferences).filter(Preferences.user_id == user.id).first()
    if existing_prefs:
        raise HTTPException(status_code=400, detail="Preferences already exist for this user")

    db_preferences = Preferences(
        user_id=user.id,
        auto_trade=preferences.auto_trade,
        threshold_limit=preferences.threshold_limit
    )
    db.add(db_preferences)
    db.commit()
    db.refresh(db_preferences)
    return db_preferences

@router.get("/", response_model=PreferencesOut)
def get_preferences(
    current_user_email: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = get_user_by_email(db, current_user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    preferences = db.query(Preferences).filter(Preferences.user_id == user.id).first()
    if not preferences:
        raise HTTPException(status_code=404, detail="Preferences not found")
    
    return preferences

@router.put("/", response_model=PreferencesOut)
def update_preferences(
    preferences: PreferencesUpdate,
    current_user_email: str = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    user = get_user_by_email(db, current_user_email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    db_preferences = db.query(Preferences).filter(Preferences.user_id == user.id).first()
    if not db_preferences:
        raise HTTPException(status_code=404, detail="Preferences not found")

    db_preferences.auto_trade = preferences.auto_trade
    db_preferences.threshold_limit = preferences.threshold_limit
    db.commit()
    db.refresh(db_preferences)
    return db_preferences