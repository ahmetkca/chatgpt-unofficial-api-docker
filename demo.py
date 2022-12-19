import json
import logging
import time
from typing import Optional
import httpx
from uuid import uuid4
from rich.console import Console
from rich.markdown import Markdown

logging.basicConfig(level=logging.INFO)
console = Console()


def prepare_payload(
    message,
    conversation_id: Optional[str] = None,
    parent_message_id: Optional[str] = None,
):
    payload = {
        "action": "next",
        "messages": [
            {
                "content": {
                    "content_type": "text",
                    "parts": [message],
                },
                "id": str(uuid4()),
                "role": "user",
            }
        ],
        "model": "text-davinci-002-render",
    }
    if conversation_id:
        payload["conversation_id"] = conversation_id

    if parent_message_id:
        payload["parent_message_id"] = parent_message_id
    else:
        payload["parent_message_id"] = str(uuid4())

    return payload


def send_message(message, conversation_id=None, parent_message_id=None):
    console.print("[bold green underline]You[/bold green underline]:", emoji=":smiley:")
    console.print(
        message,
        emoji=":point_right:",
        style="bold blue",
        soft_wrap=True,
        justify="left",
    )

    response = None
    with console.status(
        "[bold green]Waiting for response...",
        spinner="dots",
        spinner_style="bold green",
    ) as _status:
        response = httpx.post(
            "http://localhost:8080/backend-api/conversation",
            json=prepare_payload(message, conversation_id, parent_message_id),
            timeout=None,
        )
    logging.info(response)
    if response is None:
        raise Exception("Response is None")

    if response.status_code != 200:
        raise Exception("Response status code is not 200")

    response_body = response.json()["data"]
    markdown = Markdown(response_body["message"]["content"]["parts"][0])
    console.print(
        "[deep_sky_blue1 underline]ChatGPT Assistant[/deep_sky_blue1 underline]:",
        emoji=":robot_face:",
    )
    console.print(markdown)
    console.print("\n")
    # print(json.dumps(response_body, indent=2, sort_keys=True))
    if response_body["conversation_id"]:
        conversation_id = response_body["conversation_id"]
    if response_body["message"]["id"]:
        parent_message_id = response_body["message"]["id"]
    return conversation_id, parent_message_id


if __name__ == "__main__":
    conversation_id = None
    parent_message_id = None
    conversation_id, parent_message_id = send_message(
        "Hello, Assistant!", conversation_id, parent_message_id
    )

    time.sleep(1)
    conversation_id, parent_message_id = send_message(
        "What is the difference between functional and procedural programming languages?",
        conversation_id,
        parent_message_id,
    )

    time.sleep(1)
    conversation_id, parent_message_id = send_message(
        "Write a program to print the first 10 natural numbers.",
        conversation_id,
        parent_message_id,
    )
