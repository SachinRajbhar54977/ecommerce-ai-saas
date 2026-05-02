from fastapi import APIRouter, UploadFile, File, Header, HTTPException
from pathlib import Path
import shutil

import pandas as pd
from io import BytesIO
from utils.schema_validator import validate_schema, get_canonical_filename

from backend.auth import decode_token

router = APIRouter(prefix="/upload", tags=["Upload"])

BASE_UPLOAD_DIR = Path("backend/uploads")
BASE_UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/csv")
def upload_csv(
    file: UploadFile = File(...),
    authorization: str = Header(None)
):
    # -----------------------------
    # AUTH CHECK
    # -----------------------------
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing token")

    token = authorization.split(" ")[1]
    user_email = decode_token(token)

    if not user_email:
        raise HTTPException(status_code=401, detail="Invalid token")

    # -----------------------------
    # FILE VALIDATION
    # -----------------------------
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV allowed")

    # -----------------------------
    # USER-SPECIFIC FOLDER
    # -----------------------------
    user_folder = BASE_UPLOAD_DIR / user_email
    user_folder.mkdir(parents=True, exist_ok=True)

    file_path = user_folder / file.filename

    # -----------------------------
    # SAVE FILE
    # -----------------------------
    # -----------------------------
    # READ FILE FOR VALIDATION
    # -----------------------------
    file_bytes = file.file.read()

    try:
        df = pd.read_csv(BytesIO(file_bytes))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid CSV file")

    # -----------------------------
    # VALIDATE SCHEMA
    # -----------------------------
    from utils.schema_validator import get_canonical_filename

    is_valid, dataset_type, message = validate_schema(df)

    if not is_valid:
        raise HTTPException(status_code=400, detail=message)

    canonical_filename = get_canonical_filename(dataset_type)
    file_path = user_folder / canonical_filename

    # -----------------------------
    # SAVE FILE (ONLY IF VALID)
    # -----------------------------
    with file_path.open("wb") as buffer:
        buffer.write(file_bytes)

    return {
        "message": "File uploaded successfully",
        "user": user_email,
        "dataset_type": dataset_type,
        "original_filename": file.filename,
        "saved_as": canonical_filename,
        "path": str(file_path)
    }

@router.get("/files")
def list_user_files(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing token")

    token = authorization.split(" ")[1]
    user_email = decode_token(token)

    if not user_email:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_folder = BASE_UPLOAD_DIR / user_email

    if not user_folder.exists():
        return {"files": []}

    files = [file.name for file in user_folder.glob("*.csv")]

    return {
        "user": user_email,
        "files": files
    }


@router.get("/status")
def upload_status(authorization: str = Header(None)):
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing token")

    token = authorization.split(" ")[1]
    user_email = decode_token(token)

    if not user_email:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_folder = BASE_UPLOAD_DIR / user_email

    required_files = [
        "customers.csv",
        "orders.csv",
        "monthly_revenue.csv",
        "product_summary.csv"
    ]

    status = {}

    for file in required_files:
        status[file] = (user_folder / file).exists() if user_folder.exists() else False

    forecasting_ready = status.get("orders.csv", False)

    dashboard_ready = all(status.values())

    return {
        "user": user_email,
        "files": status,
        "forecasting_ready": forecasting_ready,
        "dashboard_ready": dashboard_ready
    }