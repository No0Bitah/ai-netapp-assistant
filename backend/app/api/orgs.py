from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas import OrgCreate, OrgOut, OrgAddMember
from app.models.models import Organization, UserOrg, User
from app.api.auth_dep import require_role
from app.api.orgs_dep import create_organization


router = APIRouter(prefix="/organization", tags=["Organization"])

@router.post("/create", response_model=OrgOut)
def create_org(
    org_data: OrgCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    return create_organization(org_data=org_data, db=db, user=current_user.id)

@router.post("/{org_name}/member")
def add_member_org(
    org_name: str,
    new_member: OrgAddMember,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):
    # 1 - Validate the organization if it exist
    org = db.query(Organization).filter(Organization.name == org_name).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization Not Found!")
    # 2 - Validate the user if it exist
    user =  db.query(User).filter(User.email == new_member.user_email and User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=404, detail="User Not Found!")
    

    #3 - Check if the user is already a member of the org
    existing_member =  db.query(UserOrg).filter(
        UserOrg.user_id == user.id,
        UserOrg.org_id == org.id
          ).first()

    if existing_member:
        raise HTTPException(status_code=409, detail="User is already a member of this organization")

    link_new_member = UserOrg(
        user_id = user.id,
        org_id = org.id
    )

    # 4 - add the new member(commit to the db)
    db.add(link_new_member)
    db.commit()

    return {}

