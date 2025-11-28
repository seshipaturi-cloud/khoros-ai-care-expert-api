#!/usr/bin/env python3
"""
Test how FastAPI parses form arrays
"""

from fastapi import FastAPI, Form
from typing import List
import uvicorn

app = FastAPI()

@app.post("/test-form")
async def test_form(
    agent_ids: List[str] = Form(default=[])
):
    """Test form array parsing"""
    print(f"Received agent_ids: {agent_ids}")
    print(f"Type: {type(agent_ids)}")
    print(f"Length: {len(agent_ids)}")
    return {"agent_ids": agent_ids, "count": len(agent_ids)}

if __name__ == "__main__":
    print("Test with curl:")
    print('curl -X POST "http://localhost:8001/test-form" -F "agent_ids=id1" -F "agent_ids=id2"')
    print("")
    print("Or test with form-data:")
    print('curl -X POST "http://localhost:8001/test-form" -H "Content-Type: application/x-www-form-urlencoded" -d "agent_ids[]=id1&agent_ids[]=id2"')
    uvicorn.run(app, host="0.0.0.0", port=8001)