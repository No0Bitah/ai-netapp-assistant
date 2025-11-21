from fastapi import APIRouter, Depends, HTTPException, status
from app.api.auth_dep import require_role


router = APIRouter(prefix="/svm", tags=["SVM"])
@router.post("/create")
def create_svm(current_user = Depends(require_role(["admin"]))):
    return {"message": "SVM created"}