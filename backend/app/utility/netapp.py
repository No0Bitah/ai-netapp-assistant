import httpx

async def create_svm(ontap_host: str, username: str, password: str, payload: dict):
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

