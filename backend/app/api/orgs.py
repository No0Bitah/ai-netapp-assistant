from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas import OrgCreate, OrgOut
from app.models.models import Organization, UserOrg
from app.api.auth_dep import get_current_user
from app.api.orgs_dep import create_organization


router = APIRouter(prefix="/organization", tags=["Organization"])

@router.post("/create", response_model=OrgOut)
def create_org(
    org_data: OrgCreate,
    db: Session = Depends(get_db),
    current_user =  Depends(get_current_user)
):
    return create_organization(org_data=org_data, db=db, user=current_user.id)