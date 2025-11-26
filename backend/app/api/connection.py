from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas import ConnectionCreate
from app.models.models import User, Connection
from app.api.auth_dep import require_role
from app.api.connection_dep import create




router = APIRouter(prefix="/connection", tags=["Connection"])

@router.post("/create")
def create_conn(
    conn_data: ConnectionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"]))
):

    return create(conn_data=conn_data, db=db, user=current_user.id)

