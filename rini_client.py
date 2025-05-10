import httpx
import asyncio
import os
import mimetypes # 이미지 MIME 타입 추측용
from typing import Optional, List, Dict, Any, Union

# --- Rini API 클라이언트 예외 정의 ---
class RiniApiException(Exception):
    """Rini API 호출 시 발생하는 기본 예외"""
    def __init__(self, status_code: int, detail: Any):
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"Rini API Error {status_code}: {detail}")

# --- Rini API 클라이언트 클래스 ---
class RiniAPIClient:
    def __init__(self, base_url: str = "http://localhost:8000", token: Optional[str] = None, timeout: float = 600.0):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self._http_client: Optional[httpx.AsyncClient] = None
        self._timeout = timeout # 모든 요청에 대한 기본 타임아웃 설정

    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입 시 HTTP 클라이언트 초기화"""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(base_url=self.base_url, timeout=self._timeout)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료 시 HTTP 클라이언트 닫기"""
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

    def _get_headers(self) -> Dict[str, str]:
        """요청 헤더 생성 (인증 토큰 포함)"""
        headers = {"accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json_data: Optional[Any] = None, # Pydantic 모델도 전달 가능
        data: Optional[Dict] = None,     # multipart/form-data 용
        files: Optional[Dict] = None     # multipart/form-data 용
    ) -> Any:
        """내부 HTTP 요청 헬퍼 함수"""
        if not self._http_client:
            # 컨텍스트 매니저 밖에서 호출 시 임시 클라이언트 사용 (권장되지는 않음)
            async with httpx.AsyncClient(base_url=self.base_url, timeout=self._timeout) as client:
                return await self._perform_request(client, method, endpoint, params, json_data, data, files)
        return await self._perform_request(self._http_client, method, endpoint, params, json_data, data, files)

    async def _perform_request(
        self,
        client: httpx.AsyncClient,
        method: str,
        endpoint: str,
        params: Optional[Dict],
        json_data: Optional[Any],
        data: Optional[Dict],
        files: Optional[Dict]
    ) -> Any:
        headers = self._get_headers()
        url = f"{self.base_url}{endpoint}" # base_url은 httpx.AsyncClient에 이미 설정됨

        try:
            response = await client.request(
                method,
                endpoint, # Client 생성 시 base_url이 있으므로 endpoint만 전달
                headers=headers,
                params=params,
                json=json_data,
                data=data,
                files=files
            )
            response.raise_for_status() # 2xx 외 상태 코드면 HTTPStatusError 발생
            if response.status_code == 204:  # No Content
                return None
            return response.json()
        except httpx.HTTPStatusError as e:
            detail = str(e)
            try: # FastAPI 오류 응답은 보통 JSON 형식의 'detail' 필드를 가짐
                error_payload = e.response.json()
                detail = error_payload.get("detail", str(e))
            except Exception:
                pass # JSON 파싱 실패 시 그냥 원래 에러 메시지 사용
            raise RiniApiException(status_code=e.response.status_code, detail=detail) from e
        except httpx.RequestError as e:
            raise RiniApiException(status_code=503, detail=f"Request to Rini API failed: {e}") from e
        except Exception as e:
            raise RiniApiException(status_code=500, detail=f"An unexpected client-side error occurred: {e}") from e

    def set_token(self, token: str):
        """클라이언트 인스턴스에 인증 토큰을 설정합니다."""
        self.token = token
        print(f"RiniAPIClient: Token set.")

    # --- User Endpoints ---
    async def create_user_and_set_token(self) -> Dict:
        """새로운 단순 사용자를 생성하고, 발급된 토큰을 클라이언트에 자동 설정합니다."""
        print("Creating user and fetching token...")
        response_data = await self._request("POST", "/users/")
        if response_data and "access_token" in response_data:
            self.set_token(response_data["access_token"])
            print(f"User ID {response_data.get('id')} created, token set.")
        return response_data

    async def get_my_info(self) -> Dict:
        """현재 인증된 사용자의 정보를 조회합니다."""
        print("Fetching current user info...")
        return await self._request("GET", "/users/me")

    # --- API Key Management ---
    async def register_api_key(self, model_provider: str, api_key_value: str, description: Optional[str] = None) -> Dict:
        """새로운 LLM API 키를 등록합니다."""
        payload = {"model_provider": model_provider, "api_key_value": api_key_value}
        if description is not None: payload["description"] = description
        print(f"Registering API key for provider: {model_provider}...")
        return await self._request("POST", "/api-keys/", json_data=payload)

    async def list_api_keys(self, skip: int = 0, limit: int = 10) -> List[Dict]:
        print("Listing API keys...")
        return await self._request("GET", "/api-keys/", params={"skip": skip, "limit": limit})

    async def get_api_key(self, api_key_id: int) -> Dict:
        print(f"Getting API key detail for ID: {api_key_id}...")
        return await self._request("GET", f"/api-keys/{api_key_id}")

    async def update_api_key(self, api_key_id: int, description: Optional[str] = None, is_active: Optional[bool] = None) -> Dict:
        payload = {}
        if description is not None: payload["description"] = description
        if is_active is not None: payload["is_active"] = is_active # 서버 스키마에 is_active 추가 필요
        print(f"Updating API key ID: {api_key_id}...")
        return await self._request("PUT", f"/api-keys/{api_key_id}", json_data=payload)

    async def delete_api_key(self, api_key_id: int) -> None:
        print(f"Deleting API key ID: {api_key_id}...")
        await self._request("DELETE", f"/api-keys/{api_key_id}")
        print(f"API key ID: {api_key_id} deleted.")

    # --- Session Management ---
    async def create_session(self, alias: Optional[str] = None, system_prompt: Optional[str] = None, memory_mode: str = "auto") -> Dict:
        payload = {"memory_mode": memory_mode}
        if alias is not None: payload["alias"] = alias
        if system_prompt is not None: payload["system_prompt"] = system_prompt
        print(f"Creating session with alias: {alias}...")
        return await self._request("POST", "/sessions/", json_data=payload)

    async def list_sessions(self, skip: int = 0, limit: int = 10) -> List[Dict]:
        print("Listing sessions...")
        return await self._request("GET", "/sessions/", params={"skip": skip, "limit": limit})

    async def get_session(self, session_id: str) -> Dict:
        print(f"Getting session detail for ID: {session_id}...")
        return await self._request("GET", f"/sessions/{session_id}")

    async def update_session(self, session_id: str, alias: Optional[str] = None, system_prompt: Optional[str] = None, memory_mode: Optional[str] = None) -> Dict:
        payload = {}
        if alias is not None: payload["alias"] = alias
        if system_prompt is not None: payload["system_prompt"] = system_prompt
        if memory_mode is not None: payload["memory_mode"] = memory_mode
        print(f"Updating session ID: {session_id}...")
        return await self._request("PUT", f"/sessions/{session_id}", json_data=payload)

    async def delete_session(self, session_id: str) -> None:
        print(f"Deleting session ID: {session_id}...")
        await self._request("DELETE", f"/sessions/{session_id}")
        print(f"Session ID: {session_id} deleted.")

    # --- Message Management ---
    async def add_message_to_session(self, session_id: str, role: str, content: str) -> Dict:
        """세션에 새 사용자 또는 시스템 메시지를 추가합니다 (어시스턴트 메시지는 보통 LLM 호출 결과로 자동 추가됨)."""
        payload = {"role": role, "content": content} # 서버 schemas.MessageCreateBase의 필드명 사용
        print(f"Adding message to session {session_id}: [{role}] {content[:50]}...")
        return await self._request("POST", f"/sessions/{session_id}/messages/", json_data=payload)

    async def list_session_messages(self, session_id: str, skip: int = 0, limit: int = 100) -> List[Dict]:
        print(f"Listing messages for session {session_id}...")
        return await self._request("GET", f"/sessions/{session_id}/messages/", params={"skip": skip, "limit": limit})

    async def get_message_info(self, message_id: int) -> Dict:
        print(f"Getting message info for ID: {message_id}...")
        return await self._request("GET", f"/messages/{message_id}")

    async def get_message_parent_history(self, message_id: int) -> List[Dict]:
        print(f"Getting parent history for message ID: {message_id}...")
        return await self._request("GET", f"/messages/{message_id}/history")

    # --- LLM Interaction ---
    async def get_text_from_text(
        self, text: str, provider: str, model: str,
        session_id: Optional[str] = None, llm_params: Optional[Dict[str, Any]] = None
    ) -> Dict:
        """단일 텍스트 입력으로 LLM 응답을 받습니다."""
        payload = {"text": text, "provider": provider, "model": model}
        if session_id: payload["session_id"] = session_id
        if llm_params: payload["llm_params"] = llm_params
        print(f"Requesting text completion: provider={provider}, model={model}, session={session_id}")
        return await self._request("POST", "/llm/text-completion/", json_data=payload)

    async def get_text_from_messages( # Stateless chat completion
        self, messages: List[Dict], provider: str, model: str, llm_params: Optional[Dict[str, Any]] = None
    ) -> Dict:
        """메시지 목록으로 LLM 응답을 받습니다 (Stateless)."""
        payload = {"messages": messages, "provider": provider, "model": model}
        if llm_params: payload["llm_params"] = llm_params
        print(f"Requesting chat completion (stateless): provider={provider}, model={model}")
        return await self._request("POST", "/llm/chat-completions/", json_data=payload)

    async def get_text_from_image_and_text(
        self, image_file_path: str, provider: str,
        model: Optional[str] = None, prompt: Optional[str] = None, session_id: Optional[str] = None
    ) -> Dict:
        """이미지와 텍스트로 LLM Vision 모델 응답을 받습니다."""
        if not os.path.exists(image_file_path):
            raise FileNotFoundError(f"Image file not found: {image_file_path}")

        form_data = {"provider": provider} # provider는 필수로 Form 데이터에 포함
        if prompt: form_data["prompt"] = prompt
        if model: form_data["model"] = model
        if session_id: form_data["session_id"] = session_id

        file_name = os.path.basename(image_file_path)
        mime_type, _ = mimetypes.guess_type(image_file_path)
        mime_type = mime_type or 'application/octet-stream'

        print(f"Requesting image completion: provider={provider}, model={model or 'default'}, session={session_id}")
        with open(image_file_path, "rb") as f:
            files = {"image_file": (file_name, f, mime_type)}
            # httpx는 files와 data를 동시에 보낼 때 data의 값들이 문자열이어야 할 수 있음
            # form_data의 모든 값을 문자열로 변환 (FastAPI Form()은 자동 변환하지만, 클라이언트는 명시적일 수 있음)
            str_form_data = {k: str(v) if v is not None else None for k, v in form_data.items() if v is not None}

            return await self._request("POST", "/llm/image-completion/", data=str_form_data, files=files)

    async def get_embedding(
        self, text_input: Union[str, List[str]],
        provider: str = "openai", model: str = "text-embedding-3-large"
    ) -> Dict:
        """텍스트(들)에 대한 임베딩 벡터를 생성합니다."""
        payload = {"input": text_input, "provider": provider, "model": model}
        print(f"Requesting embedding: provider={provider}, model={model}")
        return await self._request("POST", "/llm/embeddings/", json_data=payload)

    # --- MCP Connection Endpoints ---
    async def add_mcp_connection(self, url: str, alias: Optional[str] = None, description: Optional[str] = None, is_active: bool = True) -> Dict:
        payload = {"mcp_server_url": url, "is_active": is_active}
        if alias: payload["alias"] = alias
        if description: payload["description"] = description
        print(f"Adding MCP connection: {url} (Alias: {alias})")
        return await self._request("POST", "/mcp-connections/", json_data=payload)

    async def list_mcp_connections(self, is_active: Optional[bool] = None, skip: int = 0, limit: int = 100) -> List[Dict]:
        params = {"skip": skip, "limit": limit}
        if is_active is not None: params["is_active"] = is_active
        print(f"Listing MCP connections (is_active={is_active})...")
        return await self._request("GET", "/mcp-connections/", params=params)

    async def get_mcp_connection_detail(self, connection_id: int) -> Dict:
        print(f"Getting MCP connection detail for ID: {connection_id}...")
        return await self._request("GET", f"/mcp-connections/{connection_id}")

    async def update_mcp_connection(self, connection_id: int, mcp_update_data: Dict) -> Dict:
        print(f"Updating MCP connection ID: {connection_id}...")
        return await self._request("PUT", f"/mcp-connections/{connection_id}", json_data=mcp_update_data)

    async def delete_mcp_connection(self, connection_id: int) -> None:
        print(f"Deleting MCP connection ID: {connection_id}...")
        await self._request("DELETE", f"/mcp-connections/{connection_id}")
        print(f"MCP connection ID: {connection_id} deleted.")


    # --- Memory Endpoints ---
    async def add_memory_entry(self, session_id: str, memory_type: str, scope: str, content: str, **kwargs) -> Dict:
        payload = {"memory_type": memory_type, "scope": scope, "content": content, **kwargs}
        # kwargs에는 source_message_ids, keywords, importance 등이 올 수 있음
        print(f"Adding memory to session {session_id}: [{memory_type}/{scope}] {content[:50]}...")
        return await self._request("POST", f"/sessions/{session_id}/memory", json_data=payload)

    async def list_memory_entries(
        self, session_id: Optional[str] = None, scope: Optional[str] = None,
        memory_type: Optional[str] = None, skip: int = 0, limit: int = 100
    ) -> List[Dict]:
        params = {"skip": skip, "limit": limit}
        if session_id: params["session_id"] = session_id
        if scope: params["scope"] = scope
        if memory_type: params["memory_type"] = memory_type
        print(f"Listing memory entries with filters: session={session_id}, scope={scope}, type={memory_type}")
        return await self._request("GET", "/memory/", params=params)

    async def get_memory_entry_detail(self, memory_id: int) -> Dict:
        print(f"Getting memory entry detail for ID: {memory_id}...")
        return await self._request("GET", f"/memory/{memory_id}")

    async def update_memory_entry(self, memory_id: int, memory_update_data: Dict) -> Dict:
        # memory_update_data는 schemas.MemoryEntryUpdate 와 유사한 딕셔너리
        print(f"Updating memory entry ID: {memory_id}...")
        return await self._request("PATCH", f"/memory/{memory_id}", json_data=memory_update_data)

    async def delete_memory_entry(self, memory_id: int) -> None:
        print(f"Deleting memory entry ID: {memory_id}...")
        await self._request("DELETE", f"/memory/{memory_id}")
        print(f"Memory entry ID: {memory_id} deleted.")

    # --- Cost Estimation Endpoint ---
    async def get_cost_estimation(
        self, start_date: Optional[str] = None, end_date: Optional[str] = None, # YYYY-MM-DD string
        session_id: Optional[str] = None, provider: Optional[str] = None, model: Optional[str] = None
    ) -> Dict:
        params = {}
        if start_date: params["start_date"] = start_date
        if end_date: params["end_date"] = end_date
        if session_id: params["session_id"] = session_id
        if provider: params["provider"] = provider
        if model: params["model"] = model
        print(f"Getting cost estimation with filters: {params}")
        return await self._request("GET", "/usage/cost-estimation/", params=params)
