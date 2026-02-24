from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import APIKeyHeader
from dotenv import load_dotenv
from supabase import create_client
from pydantic import BaseModel
from typing import Optional, List
import os
from jsonschema import validate, ValidationError

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
API_KEY = os.getenv("API_KEY")
supabase = create_client(url, key)

app = FastAPI()

api_key_header = APIKeyHeader(name="X-API-Key")

def verify_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return api_key

@app.get("/health")
def health():
    return {
        "status": "ok",
        "api_key_loaded": API_KEY is not None and len(API_KEY) > 0
    }

@app.get("/schema/{datasource_id}")
def get_schema(datasource_id: int, api_key: str = Depends(verify_api_key)):
    result = supabase.table("datasources").select("data_schema").eq("id", datasource_id).execute()
    if result.data:
        return {"data_schema": result.data[0]["data_schema"]}
    else:
        raise HTTPException(status_code=404, detail="Datasource not found")
    
class ValidationRequest(BaseModel):
    data: List[dict]
    datasource_id: Optional[int] = None
    schema: Optional[dict] = None

@app.post("/validate")
def validate_data(request: ValidationRequest, api_key: str = Depends(verify_api_key)):
    # Validate: must provide exactly one of datasource_id or schema
    if request.datasource_id and request.schema:
        raise HTTPException(status_code=400, detail="Provide only one of 'datasource_id' or 'schema', not both")

    if not request.datasource_id and not request.schema:
        raise HTTPException(status_code=400, detail="Provide either 'datasource_id' or 'schema'")

    # Get schema from Supabase or use custom schema
    if request.datasource_id:
        result = supabase.table("datasources").select("data_schema").eq("id", request.datasource_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Datasource not found")
        data_schema = result.data[0]["data_schema"]
    else:
        data_schema = request.schema

    # Validate each item in the array
    valid_items = []
    errors = []

    for index, item in enumerate(request.data):
        try:
            validate(instance=item, schema=data_schema)
            valid_items.append(item)
        except ValidationError as e:
            errors.append({"index": index, "item": item, "error": e.message})

    # If all valid, return just the data
    if len(errors) == 0:
        return valid_items

    # If there are errors, return detailed response
    return {
        "valid_items": valid_items,
        "errors": errors,
        "total": len(request.data),
        "valid_count": len(valid_items),
        "error_count": len(errors)
    }   