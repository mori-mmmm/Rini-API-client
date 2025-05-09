import asyncio
import os
from flask import Flask, render_template_string, request, jsonify
from rini_client import RiniAPIClient, RiniApiException
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")

app = Flask(__name__)

current_session_id = None

async def get_rini_client():
    return RiniAPIClient(token=TOKEN)

@app.route('/')
async def index():
    global current_session_id
    async with await get_rini_client() as client:
        if not current_session_id:
            try:
                session = await client.create_session(alias="웹 챗봇 세션", system_prompt="너는 친절한 AI 비서야.")
                current_session_id = session["id"]
            except RiniApiException as e:
                print(f"세션 생성 오류: {e}")
                return "Rini API 세션 생성에 실패했습니다. API 키 또는 서비스 상태를 확인해주세요.", 500

    # 사용 가능한 provider와 model 목록
    providers = ["openai", "google", "anthropic"]
    models = {
        "openai": ["gpt-4.1", "gpt-4.1-mini", "gpt-4.1-nano", "gpt-4.5-preview", "gpt-4o", "gpt-4o-mini", "o3", "o4-mini"],
        "google": ["gemini-2.5-flash-preview-04-17", "gemini-2.5-pro-preview-03-25", "gemini-2.5-pro-preview-05-06"],
        "anthropic": ["claude-3-7-sonnet-20250219", "claude-3-5-haiku-20241022"]
    }

    return render_template_string(HTML_TEMPLATE, providers=providers, models=models)

@app.route('/send_message', methods=['POST'])
async def send_message():
    global current_session_id
    if not current_session_id:
        return jsonify({"error": "세션이 초기화되지 않았습니다."}), 400

    data = request.get_json()
    user_message = data.get('message')
    provider = data.get('provider')
    model = data.get('model')

    if not user_message or not provider or not model:
        return jsonify({"error": "메시지, provider 또는 model이 누락되었습니다."}), 400

    async with await get_rini_client() as client:
        try:
            response = await client.get_text_from_text(
                text=user_message,
                provider=provider,
                model=model,
                session_id=current_session_id,
            )
            ai_response = response.get('response_text')
            return jsonify({"ai_response": ai_response})
        except RiniApiException as e:
            print(f"메시지 전송 오류: {e}")
            return jsonify({"error": f"Rini API 오류: {e}"}), 500
        except Exception as e:
            print(f"알 수 없는 오류: {e}")
            return jsonify({"error": "메시지 처리 중 알 수 없는 오류가 발생했습니다."}), 500

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Simple Chatbot</title>
    <style>
        body {
            font-family: sans-serif;
            background-color: #f0f0f0;
            color: #333;
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            min-height: 100vh;
        }
        .container {
            background-color: #fff;
            border-radius: 8px;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            width: 90%;
            max-width: 600px;
            margin-top: 20px;
            display: flex;
            flex-direction: column;
            height: calc(100vh - 160px); /* 헤더와 입력창 높이 제외 */
        }
        .chat-header {
            background-color: #e0e0e0;
            color: #333;
            padding: 15px;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            text-align: center;
            font-size: 1.2em;
        }
        .chat-window {
            flex-grow: 1;
            padding: 20px;
            overflow-y: auto;
            border-bottom: 1px solid #e0e0e0;
        }
        .message {
            margin-bottom: 15px;
            display: flex;
            flex-direction: column;
        }
        .user-message .message-bubble {
            background-color: #d1e7dd; /* 연한 녹색 */
            color: #0f5132; /* 어두운 녹색 */
            padding: 10px 15px;
            border-radius: 15px 15px 0 15px; /* 말풍선 모양 */
            max-width: 70%;
            align-self: flex-end;
            word-wrap: break-word;
        }
        .ai-response { /* AI 응답은 말풍선 없음 */
            padding: 10px 0;
            max-width: 100%;
            align-self: flex-start;
            word-wrap: break-word;
            white-space: pre-wrap; /* 줄바꿈 및 공백 유지 */
        }
        .input-area {
            display: flex;
            padding: 15px;
            border-top: 1px solid #e0e0e0;
            background-color: #f9f9f9;
        }
        #message-input {
            flex-grow: 1;
            padding: 10px;
            border: 1px solid #ccc;
            border-radius: 4px;
            margin-right: 10px;
        }
        #send-button {
            padding: 10px 15px;
            background-color: #555;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        #send-button:hover {
            background-color: #333;
        }
        .controls {
            display: flex;
            justify-content: space-between;
            padding: 10px 15px;
            background-color: #f9f9f9;
            border-bottom-left-radius: 8px;
            border-bottom-right-radius: 8px;
        }
        .controls select {
            padding: 8px;
            border: 1px solid #ccc;
            border-radius: 4px;
            background-color: white;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="chat-header">Rini Chatbot</div>
        <div class="controls">
            <div>
                <label for="provider-select">Provider: </label>
                <select id="provider-select">
                    {% for p in providers %}
                    <option value="{{ p }}">{{ p }}</option>
                    {% endfor %}
                </select>
            </div>
            <div>
                <label for="model-select">Model: </label>
                <select id="model-select">
                    {# 모델은 Provider 선택에 따라 동적으로 채워짐 #}
                </select>
            </div>
        </div>
        <div class="chat-window" id="chat-window">
            <!-- 채팅 메시지가 여기에 표시됩니다 -->
        </div>
        <div class="input-area">
            <input type="text" id="message-input" placeholder="메시지를 입력하세요...">
            <button id="send-button">전송</button>
        </div>
    </div>

    <script>
        const chatWindow = document.getElementById('chat-window');
        const messageInput = document.getElementById('message-input');
        const sendButton = document.getElementById('send-button');
        const providerSelect = document.getElementById('provider-select');
        const modelSelect = document.getElementById('model-select');

        const models = {{ models | tojson }};

        function updateModels() {
            const selectedProvider = providerSelect.value;
            const providerModels = models[selectedProvider] || [];
            modelSelect.innerHTML = ''; // 기존 옵션 삭제
            providerModels.forEach(model => {
                const option = document.createElement('option');
                option.value = model;
                option.textContent = model;
                modelSelect.appendChild(option);
            });
        }

        providerSelect.addEventListener('change', updateModels);
        // 페이지 로드 시 초기 모델 목록 설정
        updateModels();

        async function sendMessage() {
            const messageText = messageInput.value.trim();
            if (messageText === '') return;

            const selectedProvider = providerSelect.value;
            const selectedModel = modelSelect.value;

            // 사용자 메시지 표시
            const userMessageDiv = document.createElement('div');
            userMessageDiv.classList.add('message', 'user-message');
            const userBubble = document.createElement('div');
            userBubble.classList.add('message-bubble');
            userBubble.textContent = messageText;
            userMessageDiv.appendChild(userBubble);
            chatWindow.appendChild(userMessageDiv);

            messageInput.value = ''; // 입력창 비우기
            chatWindow.scrollTop = chatWindow.scrollHeight; // 스크롤 맨 아래로

            try {
                const response = await fetch('/send_message', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        message: messageText,
                        provider: selectedProvider,
                        model: selectedModel
                    }),
                });

                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'AI 응답을 가져오는데 실패했습니다.');
                }

                const data = await response.json();
                const aiResponseText = data.ai_response;

                // AI 응답 표시 (말풍선 없음)
                const aiResponseDiv = document.createElement('div');
                aiResponseDiv.classList.add('message', 'ai-response');
                aiResponseDiv.textContent = aiResponseText;
                chatWindow.appendChild(aiResponseDiv);

            } catch (error) {
                console.error('Error sending message:', error);
                const errorDiv = document.createElement('div');
                errorDiv.classList.add('message', 'ai-response'); // AI 응답 스타일 사용
                errorDiv.style.color = 'red';
                errorDiv.textContent = '오류: ' + error.message;
                chatWindow.appendChild(errorDiv);
            } finally {
                chatWindow.scrollTop = chatWindow.scrollHeight; // 스크롤 맨 아래로
            }
        }

        sendButton.addEventListener('click', sendMessage);
        messageInput.addEventListener('keypress', function(event) {
            if (event.key === 'Enter') {
                sendMessage();
            }
        });
    </script>
</body>
</html>
"""

if __name__ == '__main__':
    # Windows에서 asyncio 이벤트 루프 관련 경고를 피하기 위한 설정
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    app.run(debug=True)
