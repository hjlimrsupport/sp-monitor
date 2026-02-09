# Robust Gemini API Integration Skill

이 스킬은 여러 개의 Google Gemini API 키를 활용하여 쿼터 제한을 극복하고, 모델 폴백(Fallback) 로직을 통해 분석 성공률을 극대화하는 표준 방식입니다.

## 🛠️ 핵심 로직: Key Rotation & Multi-Model
1. **API 키 분산**: `API.txt` 또는 환경 변수에서 여러 개의 키를 로드하여 순차적 또는 랜덤하게 사용합니다.
2. **모델 자동 감지**: `gemini-2.0-flash` -> `gemini-1.5-flash` -> `gemini-1.5-pro` 순으로 가용한 모델을 자동 탐색합니다.
3. **재시도 메커니즘**: 특정 키가 쿼터 초과(429 Error) 시 즉시 다음 키로 전환하여 재시도합니다.

## 📄 표준 구현 템플릿 (Python)

```python
import os
import google.generativeai as genai
import random
from dotenv import load_dotenv

class RobustGeminiClient:
    def __init__(self):
        load_dotenv() # .env 파일 로드
        # GEMINI_API_KEYS=key1,key2,key3 형식을 지원합니다.
        raw_keys = os.getenv("GEMINI_API_KEYS", "")
        self.keys = [k.strip() for k in raw_keys.split(",") if k.strip()]
        self.models = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]

    def generate_content(self, prompt):
        if not self.keys:
            return "No API keys found in .env"
            
        shuffled_keys = self.keys[:]
        random.shuffle(shuffled_keys)
        
        for key in shuffled_keys:
            genai.configure(api_key=key)
            for model_name in self.models:
                try:
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(prompt)
                    return response.text
                except Exception as e:
                    if "429" in str(e): # Resource Exhausted
                        continue
                    print(f"Error with {model_name}: {e}")
        return "All keys/models failed."
```

## 🚀 활용 가이드
- **번역 프로젝트**: 대량의 텍스트 번역 시 키 5~10개를 등록하여 멈춤 없이 진행.
- **웹 분석**: 수백 개의 URL 본문을 요약할 때 각기 다른 키를 할당하여 속도 향상.
- **안티그래비티 지시어**: "Robust Gemini 스킬을 적용해서 현재 크롤러에 요약 기능을 추가해줘"라고 명령하세요.
