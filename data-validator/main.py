from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from supabase import create_client
from pydantic import BaseModel
from typing import Optional
import os
from jsonschema import validate, ValidationError

load_dotenv()
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")
supabase = create_client(url, key) 

app = FastAPI()

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/schema/{datasource_id}")
def get_schema(datasource_id: int):
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
def validate_data(request: ValidationRequest):
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