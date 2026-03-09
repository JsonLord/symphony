from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import schemas, domain

router = APIRouter()

@router.post("/profiles", response_model=schemas.ProfileResponse)
def create_profile(profile: schemas.ProfileCreate, db: Session = Depends(get_db)):
    db_profile = domain.SettingsProfile(
        profile_name=profile.profile_name,
        hf_space_id=profile.hf_space_id,
        parameters=profile.parameters
    )
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    return {"profile_id": db_profile.id}
