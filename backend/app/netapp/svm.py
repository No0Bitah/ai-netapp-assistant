from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.models import Connection
from app.api.auth_dep import require_role
from app.api.connection_dep import get_auth_connection
from app.schemas import SVMCreateRequest, SvmConnect
from backend.app.utility.netapp_client import create, list


router = APIRouter(prefix="/svm", tags=["SVM"])



@router.get("{conn_id}/svms")
def get_svms(
    svm_data:SvmConnect,
    safe_connection: Connection = Depends(get_auth_connection),
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["viewer", "admin"]))          
              ):
    try:
        svms = list(
            ontap_host=svm_data.base_url,
            username=svm_data.base_url,  # Replace with actual username
            password=svm_data.base_url  # Replace with actual password
        )
        return {"svms": svms}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    



@router.post("/{conn_id}/create/svms")
def create_svm(current_user = Depends(require_role(["admin"]))):
    return {"message": "SVM created"}