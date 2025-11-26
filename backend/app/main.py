from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from app.api import auth, orgs, connection
from app.netapp import svm
from dotenv import load_dotenv
load_dotenv()


app = FastAPI(title="AI NetApp Assistant API")


origins = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}

app.include_router(auth.router)
app.include_router(orgs.router)
app.include_router(connection.router)
app.include_router(svm.router)