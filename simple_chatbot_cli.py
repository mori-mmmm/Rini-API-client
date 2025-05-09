import asyncio
import os
from rini_client import RiniAPIClient, RiniApiException
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")

async def main():
   async with RiniAPIClient(token=TOKEN) as client:
        session = await client.create_session(alias="테스트 세션", system_prompt="너는 친절한 AI 비서야.")
        session_id = session["id"]

        while True:
            query = input(">>> ")
            response = await client.get_text_from_text(
                text=query,
                provider="openai",
                model="gpt-4.1-nano",
                session_id=session_id,
            )
            #print(response)
            print(f"Response: {response.get('response_text')}")
            #if response.get("assistant_message"):
            #    print(f"  Assistant Message ID: {response['assistant_message']}")

if __name__ == "__main__":
    asyncio.run(main())