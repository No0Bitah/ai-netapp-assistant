from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from app.db import get_db
from app.models.models import User, UserOrg, Organization, Connection
from app.schemas import ConnectionCreate
from app.utility.security import hash_password

def create(conn_data: ConnectionCreate, db: Session, user: int):
    
    # 1 - get the org Id using the org name
    org =  db.query(Organization).filter(Organization.name == conn_data.organization).first()
    if not org:
        raise HTTPException(status_code=404, detail="Organization Not Found!")
    
    # 2 - verify first if the user is a member of the org
    print(verify_member(db=db, user_id=user, org_id=org.id))
    if not verify_member(db=db, user_id=user, org_id=org.id):
        raise HTTPException(status_code=404, detail="User should be a member of the organization")

    # 3 - create the connection
    new_conn = Connection(
        org_id = org.id,
        name = conn_data.conn_name,
        base_url = conn_data.base_url,
        enc_password = hash_password(conn_data.password),
        scope = conn_data.scope,
        svm_name = conn_data.svm_name
    )

    try:
        db.add(new_conn)
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409)
    
    db.commit()
    return new_conn

def verify_member(db: Session, user_id: int, org_id: int) -> bool:
    # return a bool to verify if the current user is a member of the Organization
    return bool(db.query(UserOrg).filter(
        UserOrg.user_id == user_id,
        UserOrg.org_id == org_id
        ).first())
    
