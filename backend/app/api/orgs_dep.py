from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import Depends, HTTPException, status
from app.db import get_db
from app.models.models import Organization, UserOrg
from app.schemas import OrgCreate


def create_organization(db: Session, org_data: OrgCreate, user: int):
    """
    Creates an Organization and automatically adds the creator as a member.
    """
    # 1. Create the Organization Instance
    new_org = Organization(
            name=org_data.name
            # created_at is handled automatically by default=datetime.utcnow in your model
                    )
    
    try:
        db.add(new_org)
        db.flush() # This sends SQL to DB to generate the new_org.id, but doesn't commit yet

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Organization with this name already exists.")
    
    # 2. AUTOMATICALLY Link the Creator (Vital Step)
    # Since you have a UserOrg table, you shouldn't create an orphaned organization.
    # The person creating it should usually be the first member/admin.
    link_user_org = UserOrg(
        user_id = user,
        org_id = new_org.id
    )

    db.add(link_user_org)

    db.commit()
    db.refresh(new_org)

    return new_org