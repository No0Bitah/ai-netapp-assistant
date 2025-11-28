from fastapi import APIRouter, Depends, HTTPException
import httpx
import json

from sqlalchemy.orm import Session
from app.db import get_db
from app.models.models import Connection
from app.api.auth_dep import require_role
from app.api.connection_dep import get_auth_connection
from app.schemas import SVMCreateRequest, SvmConnect
from app.utility.netapp_client import get_netapp_client
from app.netapp.svm.svm_dep import SvmQueryParams

router = APIRouter(prefix="/svm", tags=["SVM"])



@router.get("{conn_id}/svms")
async def get_svms(
    conn_id: int,
    filters: SvmQueryParams = Depends(),
    safe_connection: Connection = Depends(get_auth_connection),
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["viewer", "admin"]))          
    ):
    

    async with get_netapp_client(safe_connection.id, db=db) as conn:
        try:
            query_params = filters.to_dict()
            query_params["fields"] = "*"  # Fetch all fields
            response = await conn.get("/api/svm/svms", params=query_params)
            if response.status_code != 200:
                try:
                    error_detail = response.json().get('error', {}).get('message', 'Unknown error') 
                except Exception:
                    error_detail = response.text or f"HTTP {response.status_code}"
                
                print("ONTAP Error Response:", response.json())
                raise HTTPException(
                    status_code=response.status_code, 
                    detail=f"ONTAP Error: {error_detail}"
                )

            data = response.json()

            print(json.dumps(data, indent=2))
            return data.get("records", [])
        
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error communicating with ONTAP API: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected error: {str(e)}"
            )



@router.post("/{conn_id}/svms")
async def create_svm(
    new_svm: SVMCreateRequest,
    safe_connection: Connection = Depends(get_auth_connection),
    current_user = Depends(require_role(["admin"]))
    ):
    async with get_auth_connection(safe_connection) as conn:
        payload = {
            "name": new_svm.svm_name,
            "snapshot_policy.name": new_svm.snapshot_policy
        }
        await create(
            ontap_host=safe_connection.base_url,
            username=safe_connection.username,
            password=safe_connection.enc_password,
            payload=payload
        )   

    return {"message": "SVM created"}