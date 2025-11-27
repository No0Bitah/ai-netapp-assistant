import httpx, base64
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from contextlib import asynccontextmanager
from app.db import get_db
from app.models.models import Connection
from app.utility.security import decode_token, decrypt_netapp_password


@asynccontextmanager
async def get_netapp_client(conn_id: int, db: Session):
    """
    Context manager that provides a pre-configured, authenticated NetApp client.
    Usage:
        async with get_netapp_client(conn_id, db) as client:
            resp = await client.get(...)
    """
    # 1. Fetch Connection Details from DB
    conn = db.query(Connection).filter(Connection.id == conn_id).first()
    
    if not conn:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Connection configuration not found"
        )

    # 2. Decrypt the Password
    # We decrypt it only for this instant, in memory.
    try:
        plain_password = decrypt_netapp_password(conn.enc_password)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not decrypt connection credentials."
        )

    # 3. Configure the HTTP Client
    # We use 'async with' here so httpx automatically closes the connection
    # when the block ends, preventing memory leaks.
    async with httpx.AsyncClient(
        base_url=conn.base_url,         # Ensure it's a string
        auth=(conn.username, plain_password), # Automatic Basic Auth header
        verify=conn.verify_tls,               # Enforce SSL verification setting
        timeout=20.0,                         # Default timeout (NetApp can be slow)
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    ) as client:
        # 4. Yield the client to the route handler
        yield client


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
