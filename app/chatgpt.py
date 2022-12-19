import json
from typing import List
import httpx
import logging

import tls_client

logging.basicConfig(level=logging.INFO)

# from uuid import uuid4


def prepare_cookies(cookies: List[dict]):
    cookies_dict = {}
    for cookie in cookies:
        cookies_dict[cookie["name"]] = cookie["value"]

    return cookies_dict


def prepare_headers(access_token: str) -> dict[str, str]:
    headers = {
        "authority": "chat.openai.com",
        "accept": "text/event-stream",
        "accept-language": "en-US,en;q=0.9",
        "authorization": f"Bearer {access_token}",
        "content-type": "application/json",
        "origin": "https://chat.openai.com",
        "referer": "https://chat.openai.com/chat",
        "sec-ch-ua": '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Linux"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
        "x-openai-assistant-app-id": "",
    }
    return headers


from pydantic import BaseModel


class ConversationMessagesContent(BaseModel):
    content_type: str
    parts: List[str]


class ConversationMessages(BaseModel):
    id: str
    role: str
    content: ConversationMessagesContent


class Conversation(BaseModel):
    action: str
    conversation_id: str | None
    messages: List[ConversationMessages]
    parent_message_id: str
    model: str


# def prepare_json_data(
#     message: str, parent_message_id: str | None, conversation_id: str | None
# ):
#     if parent_message_id is None:
#         parent_message_id = str(uuid4())

#     json_data = {
#         "action": "next",
#         "messages": [
#             {
#                 "id": str(uuid4()),
#                 "role": "user",
#                 "content": {
#                     "content_type": "text",
#                     "parts": [
#                         message,
#                     ],
#                 },
#             },
#         ],
#         "parent_message_id": parent_message_id,
#         "model": "text-davinci-002-render",
#     }

#     if conversation_id is not None:
#         json_data["conversation_id"] = conversation_id

#     return json_data

tls_client = tls_client.Session(client_identifier="chrome_108")

limits = httpx.Limits(
    max_keepalive_connections=1, max_connections=1, keepalive_expiry=None
)
client = httpx.AsyncClient(limits=limits)


async def get_access_token(cookies: List[dict]) -> str | None:
    if len(cookies) == 0 or cookies is None:
        return {"status": "error", "message": "Cookies is empty"}

    headers = {
        "authority": "chat.openai.com",
        "accept": "*/*",
        "accept-language": "en-US,en;q=0.9",
        "cache-control": "no-cache",
        "pragma": "no-cache",
        "referer": "https://chat.openai.com/chat",
        "sec-ch-ua": '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Linux"',
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    }
    _cookies = prepare_cookies(cookies)
    # async with httpx.AsyncClient() as client:
    # response = await client.get(
    #     "https://chat.openai.com/api/auth/session",
    #     headers=headers,
    #     cookies=_cookies,
    # )
    response = tls_client.get(
        "https://chat.openai.com/api/auth/session",
        headers=headers,
        cookies=_cookies,
    )

    if response.status_code == 200:
        return response.json()["accessToken"]

    return None


async def post_conversation(
    conversation: Conversation, cookies: List[dict], access_token: str
):
    if len(conversation.parent_message_id) == 0:
        return {"status": "error", "message": "parent_message_id is empty"}

    if len(conversation.messages) == 0:
        return {"status": "error", "message": "messages is empty"}

    if len(conversation.messages[0].content.parts) == 0:
        return {"status": "error", "message": "message is empty"}

    if len(conversation.messages[0].id) == 0:
        return {"status": "error", "message": "message id is empty"}

    if access_token is None or len(access_token) == 0:
        return {"status": "error", "message": "access token is empty"}

    logging.info(f"conversation: {conversation}")
    logging.info(f"cookies: {cookies}")
    logging.info(f"access token: {access_token}")

    response_data = []
    json_payload = conversation.dict(exclude_none=True)
    # async with httpx.AsyncClient() as client:
    # async with client.stream(
    #     "POST",
    #     "https://chat.openai.com/backend-api/conversation",
    #     headers=prepare_headers(access_token),
    #     cookies=prepare_cookies(cookies),
    #     json=json_payload,
    # ) as response:
    #     logging.info(f"response_status_code: {response.status_code}")
    #     logging.info(f"response_headers: {response.headers}")
    #     logging.info(f"response_cookies: {response.cookies}")
    #     logging.info(f"response_is_closed: {response.is_closed}")
    #     logging.info(f"response_is_error: {response.is_error}")
    #     logging.info(f"response_is_redirect: {response.is_redirect}")
    #     logging.info(f"response_is_stream_consumed: {response.is_stream_consumed}")
    #     logging.info(f"response_request: {response.request}")
    #     logging.info(f"response_reason_phrase: {response.reason_phrase}")
    #     logging.info(f"response_url: {response.url}")
    #     logging.info(f"response_history: {response.history}")
    #     logging.info(f"response_next: {response.next_request}")
    #     logging.info(f"response_extensions: {response.extensions}")

    #     logging.info(f"response_http_version: {response.http_version}")
    #     logging.info(f"response_encoding: {response.encoding}")
    #     logging.info(f"response_links: {response.links}")

    #     async for line in response.aiter_lines():
    #         if line:
    #             logging.info(
    #                 f"response_num_bytes_downloaded: {response.num_bytes_downloaded}"
    #             )
    #             # logging.info(f"line: {line}")
    #             response_data.append(line)
    #     logging.info(f"response_elapsed: {response.elapsed}")

    res = tls_client.post(
        "https://chat.openai.com/backend-api/conversation",
        json=json_payload,
        headers=prepare_headers(access_token),
        cookies=prepare_cookies(cookies),
    )
    logging.info(f"response_status_code: {res.status_code}")
    # for line in res.iter_lines():
    #     if line:
    #         _line = line.decode(res.encoding)
    #         logging.info(f"line: {_line}")
    #         response_data.append(_line)

    # logging.info(f"response_data: {response_data}")
    # logging.info(f"response_elapsed: {res.elapsed}")
    # logging.info(f"response_cookies: {res.cookies}")
    # logging.info(f"response_headers: {res.headers}")
    # logging.info(f"response_history: {res.history}")
    # logging.info(f"response_is_redirect: {res.is_redirect}")
    # logging.info(f"response_is_permanent_redirect: {res.is_permanent_redirect}")
    # logging.info(f"response_links: {res.links}")
    # logging.info(f"response_next: {res.next}")
    # logging.info(f"response_reason: {res.reason}")
    # logging.info(f"response_request: {res.request}")
    # logging.info(f"response_url: {res.url}")
    logging.info(dir(res))  # 'cookies', 'headers', 'json', 'status_code', 'text', 'url
    try:
        logging.info(f"response_text: {res.text}")
    except:
        ...
    try:
        logging.info(f"response_content: {res.content}")
    except:
        ...
    try:
        logging.info(f"response_json: {res.json}")
    except:
        ...
    logging.info(f"response_status_code: {res.status_code}")
    logging.info(f"response_cookies: {res.cookies}")
    logging.info(f"response_headers: {res.headers}")
    logging.info(f"response_url: {res.url}")
    return res
    if res.status_code == 200:
        resp_body: str = res.text
        resp_body = resp_body.split("data:")[-2]
        resp_body = resp_body.strip()
        return json.loads(resp_body)
    logging.warn("New access token and cookies are required")
    return None
    # return res.text
    # return response_data
