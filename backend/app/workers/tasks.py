from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import asyncio
from datetime import datetime
from app.workers.celery_app import celery_app
from app.utility.netapp_client import get_netapp_client
from app.schemas import SVMCreateRequest
from app.db import get_db, SessionLocal
from app.models.models import Connection, Job
from app.api.connection_dep import get_auth_connection
from app.api.auth_dep import require_role



async def _async_create_svm(conn_id: int, db: Session, svm_payload: dict):
    print("Inside async SVM creation function")
    print("SVM Payload:", svm_payload)
    async with get_netapp_client(conn_id, db) as client:
            
            # 2. Perform the API call
            # print("Creating SVM with payload:", svm_payload)
            response = await client.post("/api/svm/svms", json=svm_payload)
            response.raise_for_status()
            
            return response.json()


@celery_app.task(name="task_create_svm")
def task_create_svm(
                    job_id: int, 
                    svm_payload: dict,
                    conn_id: int,
                ):
    print("Starting Celery task for SVM creation...")
    db = SessionLocal()
    job = db.query(Job).filter(Job.id == job_id).first()
    print("Job fetched from DB:", job)
    try:
        # Update Status: Started
        job.status = "running"
        job.started_at = datetime.utcnow()
        db.commit()
        print("Starting SVM creation task...")
        create_response = asyncio.run(
             _async_create_svm(conn_id=conn_id, db=db, svm_payload=svm_payload)
        )
            
        # 5. Success!
        job.status = "success"
        job.finished_at = datetime.utcnow()
        # Optionally save the result in the payload or a new field
        # job.result = response.json() 
        
    except Exception as e:
        # 6. Handle Failure
        db.rollback()
        job.status = "failed"
        job.finished_at = datetime.utcnow()
        # It's good practice to store the error message
        # Since your Job model has 'payload_json', we can append the error there
        current_payload = dict(job.payload_json or {})
        current_payload["error"] = str(e)
        job.payload_json = current_payload
        
    finally:
        db.commit()
        db.close() # Always close the session!