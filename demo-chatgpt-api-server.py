import time
from typing import Optional
import httpx
import asyncio

# curl "http://localhost:8080/api/ask" -X POST --header 'Authorization: secretapikey' -d '{"content": "Hello, Assistant!"}'
async def chatgpt_api_ask(content: str , conversation_id: Optional[str], parent_message_id: Optional[str]):
    payload = {
        "content": content
    }
    if conversation_id:
        payload["conversation_id"] = conversation_id
    if parent_message_id:
        payload["parent_id"] = parent_message_id
    async with httpx.AsyncClient(timeout=None) as client:
        response = await client.post('http://localhost:8080/api/ask', 
                    headers={'Authorization': 'secretapikey'},
                    json=payload)
        responseJson = response.json()
        return responseJson["content"], responseJson["response_id"], responseJson["conversation_id"]

async def main():
    time.sleep(1)
    content, parent_id, conversation_id = "Let's play tic-tac-toe. Draw 3 by 3 grid. The game will start once I message you 'start the game'. I'll go first and I am 'X'. I'll message you in the following format: for example 1,1 which means put X at the top left corner or 3,3 which means put X bottom right corner. We can not put 'X' or 'O' if there is already occupied by another 'X' or 'O'. I win if I get 3 straight 'X's in a row, column or diagonally.", None, None
    print(f"User message: \n{content}")
    chatgptResponse, parent_id, conversation_id = await chatgpt_api_ask(content, conversation_id, parent_id)
    print(f"ChatGPT response: \n{chatgptResponse}\n")

    time.sleep(2)
    
    content = "start the game"
    print(f"User message: \n{content}")
    chatgptResponse, parent_id, conversation_id =  await chatgpt_api_ask(
            content, 
            conversation_id, 
            parent_id)
    print(f"ChatGPT response: \n{chatgptResponse}\n")

    time.sleep(2)

    content = "2,2"
    print(f"User message: \n{content}")
    chatgptResponse, parent_id, conversation_id =  await chatgpt_api_ask(
            content, 
            conversation_id, 
            parent_id)
    print(f"ChatGPT response: \n{chatgptResponse}\n")



if __name__ == "__main__":
    with asyncio.Runner() as runner:
        runner.run(main())
