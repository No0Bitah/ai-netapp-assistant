import httpx
from sqalchemy.orm import Session
from app.db import get_db
from app.models.models import Connection
from app.utility.security import decode_token

async def create(ontap_host: str, username: str, password: str, payload: dict):
    url = f"https://{ontap_host}/api/svm/svms"

    async with httpx.AsyncClient(verify=False) as client:  # verify=False for self-signed cert
        response = await client.post(
            url,
            json=payload,
            auth=(username, password),
            timeout=30
        )

    if response.status_code not in (200, 201, 202):
        raise Exception(f"ONTAP Error {response.status_code}: {response.text}")

    return response.json()

async def list(ontap_host: str, username: str, password: str):
    url = f"https://{ontap_host}/api/svm/svms"

    async with httpx.AsyncClient(verify=False) as client:  # verify=False for self-signed cert
        response = await client.get(
            url,
            auth=(username, password),
            timeout=30
        )

    if response.status_code != 200:
        raise Exception(f"ONTAP Error {response.status_code}: {response.text}")

    return response.json().get('records', [])