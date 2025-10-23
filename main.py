from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
import json

app = FastAPI()

def load_health_data():
    with open("data/health_data.json", "r", encoding="utf-8") as f:
        return json.load(f)

# 1. Mock API 구현
# 건강검진 데이터를 제공하는 간단한 JSON 파일 또는 Mock Server를 생성하세요.
# **API 엔드포인트**: `GET /api/health/{patientId}`

@app.get("/api/health/{patientId}")
def get_health_data(patientId: str):
    data = load_health_data()
    if patientId in data:
        return {
            "status": "success",
            "data": data[patientId]
        }
    else:
        raise HTTPException(status_code=404, detail="Patient not found")
