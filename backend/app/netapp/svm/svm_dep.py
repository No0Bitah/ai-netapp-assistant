from fastapi import Query, Depends, HTTPException
from sqlalchemy.orm import Session
from app.utility.netapp_client import get_netapp_client
import asyncio
import time


async def _poll_netapp_job(conn_id: int, db: Session, job_link: str):
    async with get_netapp_client(conn_id, db) as client:
        while True:
            job_resp = await client.get(job_link)
            if job_resp.status_code != 200:
                return {"status_code":job_resp.status_code, 
                    "message":job_resp.json().get('error',{}).get('message',''),
                    "status":"failed"
                      }
            job_data = job_resp.json()
            state = job_data.get("state") # e.g., "running", "success", "failure"
            
            print(f"NetApp Job State: {state}")
            
            if state == "success" or state == "running":
                return {"status_code":job_resp.status_code, 
                    "message":"SVM Created",
                    "status":job_data.get("state")
                      }
            elif state == "failure":
                return {"status_code":job_resp.status_code, 
                    "message":job_data.get("message", "Unknown NetApp Error"),
                    "status":job_data.get("state")
                      }

            # 2. Wait before polling again to avoid spamming the API
            await asyncio.sleep(10) # Poll every 10 seconds


async def _async_create_svm(conn_id: int, db: Session, svm_payload: dict):

    async with get_netapp_client(conn_id, db) as client:
        print("Sending SVM creation payload to NetApp:", svm_payload)
        check = await client.get(f"/api/svm/svms/?name={svm_payload.get("name")}")
        
        if check.json().get("num_records") != 0:
            return {"status_code":400, 
                    "message":"Invalid SVM name. The name is already in use by another SVM, IPspace or cluster.",
                    "status":"failed"
                      }

        response = await client.post("/api/svm/svms", json=svm_payload)
        if response.status_code in [200, 201, 202]:
            print("SVM creation request accepted by NetApp. Polling for job completion...")
            time.sleep(5) # Give NetApp a moment to register the job
            response_json = response.json()
            # NetApp usually returns a job object with a link
            job_link = response_json.get("job", {}).get("_links", {}).get("self", {}).get("href")
            if job_link:
                print(f"SVM creation queued on NetApp. Polling Job: {job_link}")
                # Poll until finished
                svm_data = await _poll_netapp_job(conn_id, db, job_link)

                return svm_data
        
        if response.status_code >= 400:
            # raise Exception(f"NetApp Error {response.status_code}: {response.text}")
            return {"status_code":response.status_code, 
                    "message":response.json().get('error',{}).get('message',''),
                    "status":"failed"
                      }