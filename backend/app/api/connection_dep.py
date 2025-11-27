from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, Path, Depends
from app.db import get_db
from app.models.models import User, UserOrg, Organization, Connection
from app.schemas import ConnectionCreate
from app.utility.security import hash_password, enc_netapp_password
from app.api.auth_dep import require_role


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
        username = conn_data.username,
        enc_password = enc_netapp_password(conn_data.password),
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
    
def verify_connection(conn_id: int, user_id: int, db: Session) -> Connection:
    # Combine the lookup and the membership check 
    # into a single query using a JOIN. This is faster and atomic.
    # "Select Connection WHERE id is X AND UserOrg exists for this user/org"

    connection =(
            db.query(Connection).join(UserOrg, UserOrg.org_id == Connection.org_id)
                .filter(Connection.id == conn_id)
                .filter(UserOrg.user_id == user_id)
                .first()
        )
    return connection


def get_auth_connection(
        conn_id: int = Path(..., description="The ID of the Connection"),
        current_user: User = Depends(require_role(["admin"])),
        db: Session = Depends(get_db)
) -> Connection:
    """
    Dependency that acts as a security gate.
    It resolves the Connection ID to an actual Connection object,
    BUT only if the user has rights to access it.
    """

    # 1 check the user if its a member of the org and the user 
    # is the owner is authorized to use the connection
    connection = verify_connection(conn_id=conn_id,
                                   user_id=current_user.id,
                                   db=db)
    
    # If no result, it either doesn't exist OR they don't have access.
    # We return 404 for both to prevent enumeration scanning.
    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")
    
    return connection
