# uvicorn main:app --reload
from fastapi import FastAPI, HTTPException
import json
import requests

app = FastAPI()

# 0. json 데이터 로드
def load_health_data():
    with open("data/health_data.json", encoding="utf-8") as f:
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


# 2. Ollama LLM 연동
MODEL_NAME = "llama3.1:8b" # ollama pull llama3.1:8b
OLLAMA_API_URL = "http://localhost:11434/api/generate"

def ask_ollama(prompt: str):
    response = requests.post(
        OLLAMA_API_URL,
        json={
            "model": MODEL_NAME,
            "system": "질문을 반복하지 말고, 바로 3문장으로 간략하게 답변하세요.",
            "prompt": prompt
        },
        stream=True
    )

    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="LLM request failed")

    full_text = ""
    for line in response.iter_lines():
        if not line:
            continue
        try:
            json_line = json.loads(line.decode("utf-8"))
            if "response" in json_line:
                full_text += json_line["response"]
        except json.JSONDecodeError:
            continue

    return full_text.strip() or "LLM 응답을 가져오지 못했습니다."


# 3. 질의응답 시스템
# 사용자 질문 → API 데이터 조회 → LLM 프롬프트 생성 → 응답
@app.post("/qna")
def ask_health_question(patientId: str, question: str):
    data = load_health_data()

    if patientId not in data:
        raise HTTPException(status_code=404, detail="Patient not found")

    health_info = json.dumps(data[patientId], ensure_ascii=False, indent=3)

    # 🔹 LLM에게 보낼 프롬프트 생성
    prompt = f"""
            당신은 의료 데이터 분석 전문가입니다.
            다음은 환자의 건강검진 데이터입니다:

            {health_info}
            
            데이터 구조:
            - overviewList: 사용자의 건강검진 데이터
            - referenceList: 각 데이터 단위 및 정상 범위/질환 의심 여부

            사용자의 질문: "{question}"

            응답 규칙:
            1. 반드시 한국어로만 답변하고, 수치는 데이터 값 그대로 사용하세요.
            2. 검진 날짜를 언급하세요.
            3. 질문하는 것에만 답변하세요.
            4. 수치의 정상 범위/주의/질환의심 여부를 구분해서 알려주세요.
            5. 간단한 조언을 추가하세요.
            
            
            예시:
            - 질문 1: "최근 건강검진 결과는 어때요?"
            - 답변 1: "8월 15일 건강검진 결과입니다. BMI 23.5로 정상, 혈당 95mg/dL로 정상 범위에 있습니다. 다만 혈압이 125/82로 약간 높은 편이니 염분 섭취를 줄이시길 권합니다."
            
            - 질문 2: "콜레스테롤 수치가 어때요?"
            - 답변 2: "총 콜레스테롤 190mg/dL로 정상 범위(200 미만)입니다. HDL 60mg/dL도 우수한 수준이네요. 현재 상태를 유지하시면 됩니다."
            """

    answer = ask_ollama(prompt)

    return answer