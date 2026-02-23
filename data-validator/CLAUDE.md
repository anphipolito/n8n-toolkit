# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python FastAPI service that validates data before ingestion into Google Spreadsheets. Used as a validation layer in n8n workflows. Schemas are stored in a Supabase `datasources` table (`data_schema` JSONB column).

## Development Commands

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn main:app --reload

# Server runs at http://localhost:8000
# API docs at http://localhost:8000/docs
```

## API Endpoints

- `GET /health` - Health check
- `GET /schema/{datasource_id}` - Fetch schema for a datasource from Supabase
- `POST /validate` - Validate data against a datasource's JSON schema

## Environment Variables

Required in `.env`:
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_KEY` - Supabase service role key

## External Dependencies

- **Supabase**: Stores datasource metadata including JSON schemas in `datasources` table
- **n8n**: Calls this API to validate data before spreadsheet ingestion
