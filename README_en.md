# Rini API Client
This is an asynchronous Python client library for interacting with the Rini API.  
This client is designed to be used with the [Rini-API-server](https://github.com/mori-mmmm/Rini-API-server).  
The Rini-API-server runs by default on port 8000 in a local environment.  
<br />
<br />
Using this client, you can easily leverage features such as user management, API key management, session management, interaction with various LLMs (text, chat, image), embedding generation, MCP connection management, memory management, and cost estimation in your Python applications.

## Key Features

* 🙍🏻‍♂️ **User Management**: Supports new user creation and token-based authentication.
* 🔑 **API Key Management**: Securely register and manage API keys for various LLM providers like OpenAI, Google, etc.
* 🧵 **Session Management**: Create, retrieve, modify, and delete conversation sessions to manage continuous interactions with LLMs.
* 💬 **Message Management**: Add and retrieve user, assistant, and system messages within a session.
* 🧠 **LLM Interaction**:
    * **Text Completion**: Receive LLM responses for given text prompts.
    * **Chat Completion**: Generate stateless or stateful chat responses based on a list of messages.
    * **Image-Text Interaction**: Receive responses from Vision models by inputting images along with text prompts.
* 🛢️ **Embedding Generation**: Generate embedding vectors for text inputs.
* 🔧 **MCP Connection**: Add, retrieve, modify, and delete connections to MCP (Model Context Protocol) servers.
* 💾 **Memory Management (WIP)**: Add, retrieve, modify, and delete memory entries (e.g., facts, summaries) on a per-session basis to enhance LLM's contextual understanding.
* 💰 **Cost Estimation**: Retrieve estimated costs based on API usage.

## Requirements

* Python 3.7 or higher
* `httpx` (for asynchronous HTTP requests)
* `asyncio` (for asynchronous programming)
* `python-dotenv` (for loading environment variables when running demos)
* `mimetypes` (for guessing MIME types of image files)

Required libraries can be installed with the following command:
```bash
pip install httpx python-dotenv
```

## Usage

### 1. Client Initialization

Initialize `RiniAPIClient`. You can pass the base URL of the API server and optionally an authentication token.

```python
from rini_client import RiniAPIClient

async def main():
    # Rini-API-server runs at http://localhost:8000 by default.
    # The token is obtained after user creation or uses an existing token.
    async with RiniAPIClient(base_url="http://localhost:8000", token="YOUR_ACCESS_TOKEN") as client:
        # Use the client
        pass
```

### 2. Environment Variable Setup (Recommended)

It is recommended to manage sensitive information like API keys through environment variables. Create a `.env` file in your project root directory and write as follows:

```env
OPENAI_API_KEY="sk-your_openai_api_key"
GOOGLE_API_KEY="your_google_api_key"
# RINI_API_TOKEN="your_rini_api_token" # Set if you have an initial token
```

In `demo.py`, `python-dotenv` is used to load variables from this file.

### 3. Example Usage of Key Features

The `demo.py` file demonstrates how to use various features of the client.

#### User Creation and Token Setup

```python
# Create user and set token automatically
user_data = await client.create_user_and_set_token()
print(f"User created: {user_data}")
print(f"Token: {client.token}")

# Retrieve current user information
me_info = await client.get_my_info()
print(f"My info: {me_info}")
```

#### API Key Registration

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

#### Session Creation and LLM Call

```python
# Create a session
session = await client.create_session(alias="My Test Session", system_prompt="You are a helpful assistant.")
session_id = session["id"]
print(f"Session created: {session}")

# Text completion (using session)
tc_response = await client.get_text_from_text(
    text="Hello, how are you today?",
    provider="openai",
    model="gpt-4o",
    session_id=session_id
)
print(f"LLM Response: {tc_response.get('response_text')}")
```

#### LLM Call with Image and Text
```python
# Assuming test_image.png is in the same directory as the script
if os.path.exists("test_image.png"):
    img_response = await client.get_text_from_image_and_text(
        image_file_path="test_image.png",
        prompt="What do you see in this image?",
        provider="google", # Or "openai", etc., Vision model supporting provider
        model="gemini-1.5-flash-latest", # User 'gemini-2.0-flash' in original, updated to common model name
        session_id=session_id
    )
    print(f"LLM Image Response: {img_response.get('response_text')}")
```

## Running the Demo
The project includes a `demo.py` file to demonstrate the client's main features.

1.  First, run the [Rini-API-server](https://github.com/mori-mmmm/Rini-API-server) in your local environment (default `http://localhost:8000`).
2.  Install the required Python libraries (`pip install httpx python-dotenv`).
3.  Create a `.env` file in the project root and set your `OPENAI_API_KEY` and `GOOGLE_API_KEY`. (For LLM testing)
4.  Run the demo with the following command:

    ```bash
    python demo.py
    ```
Running `simple_chatbot_cli.py` allows you to have a conversation with the configured model using only very simple code.
Running `simple_chatbot_web.py` allows you to have a conversation via a web interface in your local environment (default `http://localhost:5000`).

## Exception Handling
If an error occurs during an API call, a `RiniApiException` will be raised. This exception includes `status_code` and `detail` attributes to help diagnose the error.

```python
from rini_client import RiniApiException

try:
    # API call
    pass
except RiniApiException as e:
    print(f"API Error {e.status_code}: {e.detail}")
```

## Important Notes
* Do not hardcode actual API keys directly into your source code; manage them via a `.env` file or other secure methods.
* Ensure you provide the correct image file path when using image-related functions.
* It is recommended to use `RiniAPIClient` with an asynchronous context manager (`async with`) to ensure proper management of the HTTP client session.

## Contributing
If you find a bug or have suggestions for improvement, please feel free to open an issue or send a pull request.

## License
MIT License
```
