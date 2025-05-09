# Rini API Client [[English](https://github.com/mori-mmmm/Rini-API-client/blob/main/README_en.md)]
Rini API와 상호작용하기 위한 비동기 Python 클라이언트 라이브러리입니다.  
이 클라이언트는 [Rini-API-server](https://github.com/mori-mmmm/Rini-API-server)와 함께 사용하도록 설계되었습니다.   
Rini-API-server는 기본적으로 로컬 환경의 8000번 포트에서 실행됩니다.
<br />
<br />
이 클라이언트를 사용하면 사용자 관리, API 키 관리, 세션 관리, 다양한 LLM과의 상호작용(텍스트, 채팅, 이미지), 임베딩 생성, MCP 연결 관리, 메모리 관리 및 비용 추정 등의 기능을 Python 애플리케이션에서 쉽게 활용할 수 있습니다.

## 주요 기능

*   🙍🏻‍♂️ **사용자 관리**: 신규 사용자 생성 및 토큰 기반 인증을 지원합니다.
*   🔑 **API 키 관리**: OpenAI, Google 등 다양한 LLM 공급자의 API 키를 안전하게 등록하고 관리합니다.
*   🧵 **세션 관리**: 대화 세션을 생성, 조회, 수정 및 삭제하여 LLM과의 연속적인 상호작용을 관리합니다.
*   💬 **메시지 관리**: 세션 내에서 사용자, 어시스턴트, 시스템 메시지를 추가하고 조회합니다.
*   🧠 **LLM 상호작용**:
    *   **텍스트 완성**: 주어진 텍스트 프롬프트에 대한 LLM 응답을 받습니다.
    *   **채팅 완성**: 메시지 목록을 기반으로 Stateless 또는 Stateful 채팅 응답을 생성합니다.
    *   **이미지-텍스트 상호작용**: 이미지와 텍스트 프롬프트를 함께 입력하여 Vision 모델의 응답을 받습니다.
*   🛢️ **임베딩 생성**: 텍스트 입력을 위한 임베딩 벡터를 생성합니다.
*   🔧 **MCP 연결**: MCP(Model Context Protocol) 서버와의 연결을 추가, 조회, 수정 및 삭제합니다.
*   💾 **메모리 관리(WIP)**: 세션별로 메모리 항목(예: 사실, 요약)을 추가, 조회, 수정 및 삭제하여 LLM의 컨텍스트 이해도를 높입니다.
*   💰 **비용 추정**: API 사용량에 따른 예상 비용을 조회합니다.

## 요구 사항

*   Python 3.7 이상
*   `httpx` (비동기 HTTP 요청)
*   `asyncio` (비동기 프로그래밍)
*   `python-dotenv` (데모 실행 시 환경 변수 로드용)
*   `mimetypes` (이미지 파일 MIME 타입 추측용)

필요한 라이브러리는 다음 명령어로 설치할 수 있습니다:
```bash
pip install httpx python-dotenv
```

## 사용법

### 1. 클라이언트 초기화

`RiniAPIClient`를 초기화합니다. API 서버의 기본 URL과 선택적으로 인증 토큰을 전달할 수 있습니다.

```python
from rini_client import RiniAPIClient

async def main():
    # Rini-API-server가 기본적으로 http://localhost:8000 에서 실행됩니다.
    # 토큰은 사용자 생성 후 얻거나, 기존 토큰을 사용합니다.
    async with RiniAPIClient(base_url="http://localhost:8000", token="YOUR_ACCESS_TOKEN") as client:
        # 클라이언트 사용
        pass
```

### 2. 환경 변수 설정 (권장)

API 키와 같은 민감한 정보는 환경 변수를 통해 관리하는 것이 좋습니다. 프로젝트 루트 디렉터리에 `.env` 파일을 생성하고 다음과 같이 작성합니다.

```env
OPENAI_API_KEY="sk-your_openai_api_key"
GOOGLE_API_KEY="your_google_api_key"
# RINI_API_TOKEN="your_rini_api_token" # 초기 토큰이 있다면 설정
```

`demo.py`에서는 `python-dotenv`를 사용하여 이 파일의 변수를 로드합니다.

### 3. 주요 기능 사용 예시

`demo.py` 파일은 클라이언트의 다양한 기능을 사용하는 방법을 보여줍니다.

#### 사용자 생성 및 토큰 설정

```python
# 사용자 생성 및 토큰 자동 설정
user_data = await client.create_user_and_set_token()
print(f"User created: {user_data}")
print(f"Token: {client.token}")

# 현재 사용자 정보 조회
me_info = await client.get_my_info()
print(f"My info: {me_info}")
```

#### API 키 등록

```python
import os
from dotenv import load_dotenv

load_dotenv()

openai_key_value = os.getenv("OPENAI_API_KEY")
if openai_key_value:
    openai_key = await client.register_api_key(
        provider="openai",
        api_key_value=openai_key_value,
        description="My OpenAI Key"
    )
    print(f"OpenAI Key registered: {openai_key}")
```

#### 세션 생성 및 LLM 호출

```python
# 세션 생성
session = await client.create_session(alias="My Test Session", system_prompt="You are a helpful assistant.")
session_id = session["id"]
print(f"Session created: {session}")

# 텍스트 완성 (세션 사용)
tc_response = await client.get_text_from_text(
    text="Hello, how are you today?",
    provider="openai",
    model="gpt-4o",
    session_id=session_id
)
print(f"LLM Response: {tc_response.get('response_text')}")
```

#### 이미지와 텍스트로 LLM 호출
```python
# test_image.png 파일이 스크립트와 같은 경로에 있다고 가정
if os.path.exists("test_image.png"):
    img_response = await client.get_text_from_image_and_text(
        image_file_path="test_image.png",
        prompt="What do you see in this image?",
        provider="google", # 또는 "openai" 등 Vision 모델 지원 공급자
        model="gemini-2.0-flash",
        session_id=session_id
    )
    print(f"LLM Image Response: {img_response.get('response_text')}")
```

## 데모 실행
프로젝트에는 `demo.py` 파일이 포함되어 있어 클라이언트의 주요 기능을 시연합니다.

1.  먼저 [Rini-API-server](https://github.com/mori-mmmm/Rini-API-server)를 로컬 환경(기본 `http://localhost:8000`)에서 실행합니다.
2.  필요한 Python 라이브러리를 설치합니다 (`pip install httpx python-dotenv`).
3.  프로젝트 루트에 `.env` 파일을 만들고 `OPENAI_API_KEY` 와 `GOOGLE_API_KEY`를 설정합니다. (LLM 테스트를 위함)
3.  다음 명령어로 데모를 실행합니다:

    ```bash
    python demo.py
    ```
`simple_chatbot_cli.py`를 실행할 경우 매우 간단한 코드만으로 설정된 모델과 대화를 나눌 수 있습니다.  
`simple_chatbot_web.py`로 로컬 환경(기본 `http://localhost:5000`)에서 웹 인터페이스를 통해 대화를 나눌 수도 있습니다.  

## 예외 처리
API 호출 중 오류가 발생하면 `RiniApiException`이 발생합니다. 이 예외에는 `status_code`와 `detail` 속성이 포함되어 오류 진단에 도움을 줍니다.

```python
from rini_client import RiniApiException

try:
    # API 호출
    pass
except RiniApiException as e:
    print(f"API Error {e.status_code}: {e.detail}")
```

## 주의사항
*   실제 API 키는 소스 코드에 직접 하드코딩하지 말고, `.env` 파일이나 다른 안전한 방법을 통해 관리하세요.
*   이미지 관련 기능을 사용할 때는 올바른 이미지 파일 경로를 제공해야 합니다.
*   `RiniAPIClient`는 비동기 컨텍스트 매니저(`async with`)와 함께 사용하는 것이 권장됩니다. 이를 통해 HTTP 클라이언트 세션이 적절하게 관리됩니다.

## 기여
버그를 발견하거나 개선 사항이 있다면 언제든지 이슈를 열거나 풀 리퀘스트를 보내주세요.

## 라이선스
MIT License
