import asyncio
import os
from rini_client import RiniAPIClient, RiniApiException
from dotenv import load_dotenv

load_dotenv()

async def main():
    print("Rini API Client Example Usage")
    
    async with RiniAPIClient() as client:
        try:
            # 1. 사용자 생성 및 토큰 획득 (최초 실행 시 또는 토큰 없을 때)
            print("\n--- 1. Creating User and Getting Token ---")
            user_data = await client.create_user_and_set_token()
            print(f"User created: {user_data}")
            print(f"Token (first 10 chars): {client.token[:10] if client.token else 'N/A'}...")

            # 2. 현재 사용자 정보 조회
            print("\n--- 2. Getting Current User Info ---")
            me_info = await client.get_my_info()
            print(f"My info: {me_info}")
            current_user_id = me_info["id"]

            # 3. OpenAI API 키 등록 (실제 유효한 키로 대체해야 LLM 호출 가능)
            print("\n--- 3a. Registering OpenAI API Key ---")
            try:
                openai_key_value = os.getenv("OPENAI_API_KEY")
                print(openai_key_value, "!!!!!!!!!!!!")
                openai_key = await client.register_api_key("openai", openai_key_value, "Test OpenAI Key")
                print(f"OpenAI Key registered: {openai_key}")
            except RiniApiException as e:
                print(f"Error registering OpenAI key: {e.detail}")

            # Google API 키 등
            print("\n--- 3b. Registering Google API Key ---")
            try:
                google_key_value = os.getenv("GOOGLE_API_KEY")
                google_key = await client.register_api_key("google", google_key_value, "Test Google Key")
                print(f"Google Key registered: {google_key}")
            except RiniApiException as e:
                print(f"Error registering Google key: {e.detail}")


            # 4. 세션 생성
            print("\n--- 4. Creating Session ---")
            session = await client.create_session(alias="테스트 세션", system_prompt="너는 친절한 AI 비서야.")
            session_id = session["id"]
            print(f"Session created: {session}")

            # 5. 세션을 사용하여 텍스트 완성 요청 (예: OpenAI)
            print("\n--- 5. Text Completion with Session (OpenAI) ---")
            if client.token:
                try:
                    tc_response = await client.get_text_from_text(
                        text="안녕하세요! 오늘 기분 어때요?",
                        provider="openai",
                        model="gpt-4o",
                        session_id=session_id,
                        llm_params={"temperature": 0.7}
                    )
                    print(f"LLM Text Completion Response: {tc_response.get('response_text')}")
                    if tc_response.get("assistant_message"):
                        print(f"  Assistant Message ID: {tc_response['assistant_message']['id']}")
                except RiniApiException as e:
                    print(f"Text completion failed: {e.detail}")
            else:
                print("Skipping text completion: No auth token.")


            # 6. 메시지 목록으로 Stateless 챗 완성 요청 (예: Google)
            print("\n--- 6. Chat Completion (Stateless - Google) ---")
            if client.token:
                try:
                    messages_payload = [
                        {"role": "system", "content": "너는 유머러스한 AI야."},
                        {"role": "user", "content": "재미있는 농담 하나 해줘."}
                    ]
                    cc_response = await client.get_text_from_messages(
                        messages=messages_payload,
                        provider="google",
                        model="gemini-2.5-pro-preview-05-06",
                    )
                    print(f"LLM Chat Completion Response: {cc_response.get('response_text')}")
                except RiniApiException as e:
                    print(f"Chat completion failed: {e.detail}")
            else:
                print("Skipping chat completion: No auth token.")

            # 7. (선택) 이미지와 텍스트로 LLM 호출 (예: OpenAI gpt-4o 또는 Gemini flash 2.0)
            #    테스트를 위해 스크립트와 같은 경로에 'test_image.png' 같은 이미지 파일 필요
            IMAGE_TEST_PATH = "test_image.png"
            if os.path.exists(IMAGE_TEST_PATH) and client.token:
                print(f"\n--- 7. Image Completion ({IMAGE_TEST_PATH}) ---")
                try:
                    img_response = await client.get_text_from_image_and_text(
                        image_file_path=IMAGE_TEST_PATH,
                        prompt="이 이미지에 무엇이 보이나요? 자세히 설명해주세요.",
                        provider="google",
                        session_id=session_id # 세션에 이미지 요청/응답도 저장
                    )
                    print(f"LLM Image Completion Response: {img_response.get('response_text')}")
                except RiniApiException as e:
                    print(f"Image completion failed: {e.detail}")
                except FileNotFoundError:
                    print(f"Image file {IMAGE_TEST_PATH} not found for testing.")
            else:
                print(f"Skipping image completion test: {IMAGE_TEST_PATH} not found or no auth token.")


            # 8. 임베딩 생성 (OpenAI)
            print("\n--- 8. Embedding Creation (OpenAI) ---")
            if client.token:
                try:
                    embedding_res = await client.get_embedding(
                        text_input="This is a test sentence for OpenAI embedding.",
                        provider="openai",
                        model="text-embedding-3-small"
                    )
                    print(f"Embedding created (OpenAI): Model='{embedding_res.get('model')}', Tokens='{embedding_res.get('usage')}', Data length='{len(embedding_res.get('data', []))}'")
                    if embedding_res.get('data'):
                        print(f"  First embedding vector (first 5 dims): {embedding_res['data'][0]['embedding'][:5]}...")
                except RiniApiException as e:
                    print(f"Embedding creation failed: {e.detail}")
            else:
                print("Skipping embedding test: No auth token.")

            # 9. 세션 메시지 목록 조회
            print(f"\n--- 9. Listing Messages for Session {session_id} ---")
            if client.token and session_id:
                try:
                    session_msgs = await client.list_session_messages(session_id, limit=10)
                    print(f"Found {len(session_msgs)} messages in session {session_id}:")
                    for msg in session_msgs:
                        content_preview = msg.get('content', '')
                        if content_preview is None: content_preview = "" # content가 None일 수 있음
                        print(f"  ID: {msg['id']}, Role: {msg['role']}, Content: '{content_preview[:30]}...'")
                        if msg.get('file_reference'):
                            print(f"    File: {msg['original_filename']} ({msg['mime_type']}) at {msg['file_reference']}")
                except RiniApiException as e:
                    print(f"Failed to list session messages: {e.detail}")
            else:
                print("Skipping list session messages: No auth token or session_id.")

            # 10. 수동 메모리 추가
            #print(f"\n--- 10. Adding Memory Entry to Session {session_id} ---")
            #if client.token and session_id:
            #    try:
            #        memory_entry = await client.add_memory_to_session(
            #            session_id=session_id,
            #            memory_type="Fact",
            #            scope="Session",
            #            content="The user prefers to start conversations with 'Hello!'."
            #        )
            #        print(f"Memory entry added: {memory_entry}")
            #    except RiniApiException as e:
            #        print(f"Failed to add memory entry: {e.detail}")

            # 11. 비용 예상 조회
            print(f"\n--- 11. Getting Cost Estimation ---")
            if client.token:
                try:
                    cost_est = await client.get_cost_estimation(provider="openai")
                    print(f"Cost estimation: {cost_est}")
                except RiniApiException as e:
                    print(f"Failed to get cost estimation: {e.detail}")
        finally:
            print("\nRini API Client Example Usage Finished.")


if __name__ == "__main__":
    asyncio.run(main())