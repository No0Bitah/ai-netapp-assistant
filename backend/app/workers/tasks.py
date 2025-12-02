from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import asyncio
import json
from datetime import datetime
from app.workers.celery_app import celery_app
from app.utility.netapp_client import get_netapp_client
from app.schemas import SVMCreateRequest
from app.db import get_db, SessionLocal
from app.models.models import Connection, Job
from app.api.connection_dep import get_auth_connection
from app.api.auth_dep import require_role
from app.netapp.svm.svm_dep import _async_create_svm



@celery_app.task(name="task_create_svm")
def task_create_svm(
                    job_id: int, 
                    svm_payload: dict,
                    conn_id: int,
                ):

    db = SessionLocal()
    job = db.query(Job).filter(Job.id == job_id).first()
    try:
        # Update Status: Started
        job.status = "running"
        job.started_at = datetime.utcnow()
        db.commit()
        
        create_response = asyncio.run(
                _async_create_svm(conn_id=conn_id, db=db, svm_payload=svm_payload)
            )
        print("SVM Creation Response:", create_response)
        print("payload used:", job.payload_json)
        resp_data =json.loads(json.dumps(create_response))
        # 5. Success!
        job.status = resp_data.get("status"," ") 
        if resp_data.get("message") != "SVM Created":
            current_payload = dict(job.payload_json or {})
            current_payload["error"] = resp_data.get("message", "Unknown error")
            job.payload_json = current_payload

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
        print("SVM Creation Task Failed:", e)
        current_payload = dict(job.payload_json or {})
        current_payload["error"] = [str(e)]
        job.payload_json = current_payload
        
    finally:
        db.commit()
        db.close() # Always close the session!
    