from fastapi import FastAPI, HTTPException, Depends, Header
from dotenv import load_dotenv
from supabase import create_client
from pydantic import BaseModel
from typing import Optional
import os
from jsonschema import validate, ValidationError

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
API_KEY = os.getenv("API_KEY")
supabase = create_client(url, key)

app = FastAPI()

def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/schema/{datasource_id}")
def get_schema(datasource_id: int, api_key: str = Depends(verify_api_key)):
    result = supabase.table("datasources").select("data_schema").eq("id", datasource_id).execute()
    if result.data:
        return {"data_schema": result.data[0]["data_schema"]}
    else:
        raise HTTPException(status_code=404, detail="Datasource not found")
    
class ValidationRequest(BaseModel):
    data: dict
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

    # Validate the data
    try:
        validate(instance=request.data, schema=data_schema)
        return {"valid": True, "message": "Data is valid according to the schema."}
    except ValidationError as e:
        return {"valid": False, "message": f"Data validation error: {e.message}"}   