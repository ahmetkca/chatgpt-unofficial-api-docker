import json
from typing import List, Optional, Tuple
import uuid
import undetected_chromedriver as uc
import time
import logging
from selenium.webdriver.common.by import By

# from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(level=logging.INFO)

# input("Press enter to start")
# print("Sleeping for 60 seconds")
# time.sleep(60)
import os

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")
CHATGPT_API_SERVER_URI=os.getenv("CHATGPT_API_SERVER", 'localhost:8080')

if not EMAIL or not PASSWORD:
    raise Exception("EMAIL or PASSWORD not set")


def find_element(driver: uc.Chrome, by: str = By.ID, value: "str | None" = None):
    try:
        return driver.find_element(by, value)
    except NoSuchElementException:
        logging.error(f"Element not found, by: {by}, value: {value}")
        return None


def sleep(seconds: int = 1):
    logging.info(f"Sleeping for {seconds} seconds")
    time.sleep(seconds)


# driver = uc.Chrome(
#     version_main=108,
#     no_sandbox=True,
#     disable_gpu=False,
#     keep_alive=True,
#     headless=False,
#     suppress_welcome=True,
# )
# parent_window_handle = driver.current_window_handle
# # driver.close()
# driver.implicitly_wait(15)

is_logged_in = False
is_wait = False

import asyncio


async def wait() -> bool:
    global is_wait
    is_wait = True
    while is_wait:
        logging.warn("Waiting for post request to reset is_wait")
        await asyncio.sleep(1)
    logging.info("is_wait set to False, ")
    is_wait = False
    return is_wait


# def close_all_windows_except_parent():
#     for handle in driver.window_handles:
#         if handle != parent_window_handle:
#             driver.switch_to.window(handle)
#             driver.close()


# def create_new_window_and_switch_to_it() -> Tuple[bool, str]:
#     driver.window_new()
#     for handle in driver.window_handles:
#         if handle != parent_window_handle:
#             driver.switch_to.window(handle)
#             return (True, handle)
#     return (False, None)


# async def manual_login():
#     # close_all_windows_except_parent()
#     assert create_new_window_and_switch_to_it() == True
#     recaptcha = None
#     wait_result = await wait()
#     assert wait_result == False

#     cookies_ = driver.get_cookies()

# TODO: Check if cookies are valid.

import websockets


async def login():
    cookies_ = None
    with uc.Chrome(
        version_main=108,
        no_sandbox=True,
        disable_gpu=False,
        keep_alive=True,
        headless=False,
        suppress_welcome=True,
    ) as driver:
        sleep(3)
        # close_all_windows_except_parent()
        # ret = create_new_window_and_switch_to_it()
        # assert ret[0] == True
        # current_window_handle = ret[1]

        driver.delete_all_cookies()
        logging.info("Driver started")
        driver.get("https://chat.openai.com/auth/login")
        print(driver.current_window_handle)

        assert len(driver.window_handles) == 1

        try:
            print("SESSION_ID: " + str(driver.session_id))
        except:
            logging.error("Session ID not found")

        logging.info("Waiting cloudflare, 15 seconds")
        time.sleep(15)
        loginBtn = None
        try:
            loginBtn = driver.find_element(
                By.XPATH, '//*[@id="__next"]/div/div/div[4]/button[1]'
            )
        except NoSuchElementException:
            loginBtn = None
        if loginBtn and loginBtn.is_displayed() and loginBtn.is_enabled():
            logging.info("Login button found")
            loginBtn.click()
            print(driver.current_url)
            time.sleep(10)
            print(driver.current_url)
        else:
            logging.error("Login button not found")
        logging.info("Waiting for login, 5 seconds")
        time.sleep(5)
        usernameInput = driver.find_element(By.ID, "username")
        if usernameInput:
            usernameInput.send_keys(EMAIL)
        else:
            logging.error("Username input not found")
        sleep(1)
        recaptcha = None
        wait_result = await wait()
        assert wait_result == False
        # input("reCAPTCHA found, Human verification required, press enter to continue...")
        try:
            recaptcha = driver.find_element(
                By.XPATH, "/html/body/main/section/div/div/div/form/div[1]/div/div[2]"
            )
            if recaptcha:
                logging.info("reCAPTCHA found")
        except:
            logging.info("No reCAPTCHA found")
            recaptcha = None

        continueBtn = None
        try:
            continueBtn = driver.find_element(
                By.XPATH, "/html/body/main/section/div/div/div/form/div[2]/button"
            )
        except:
            logging.error("Continue button not found")
            continueBtn = None
        if continueBtn:
            continueBtn.click()
        else:
            logging.error("Continue button not found")

        sleep(3)

        passwordInput = find_element(driver, By.ID, "password")
        if passwordInput:
            passwordInput.send_keys(PASSWORD)

        sleep(3)
        lastContinueBtn = find_element(
            driver, By.XPATH, "/html/body/main/section/div/div/div/form/div[2]/button"
        )
        if lastContinueBtn:
            sleep(1)
            lastContinueBtn.click()

        sleep(5)

        logging.info("#==============================#")

        logging.info("Cookies: ")
        logging.info(driver.get_cookies())

        logging.info(driver.current_url)

        print("SESSION_ID: " + str(driver.session_id))

        logging.info("#==============================#")

        cookies_ = driver.get_cookies()
    return cookies_

from chatgpt import ConversationMessages, ConversationMessagesContent, post_conversation, Conversation, get_access_token
from fastapi import BackgroundTasks, FastAPI, Response, status

app = FastAPI()

cookies: Optional[List[dict[str, str]]] = None
access_token: Optional[str] = None

wsapp = None


# import logging
# wsLogger = logging.getLogger('websockets')
# wsLogger.setLevel(logging.DEBUG)
# wsLogger.addHandler(logging.StreamHandler())

import websocket

connectionId = None

def handleConnectionId(ws, data):
    logging.info("handleConnectionId")
    logging.info(data)
    global connectionId
    if connectionId:
        ws.send(json.dumps({
            "id": connectionId,
            "message": "Connection id",
            "data": "",
        }))
        return
    if data.get("id"):
        connectionId = data["id"]
        ws.send(json.dumps({
            "id": connectionId,
            "message": "Connection id",
            "data": "",
        }))
        return
    logging.error("Connection id not found")


def handlePing(ws , data):
    if data.get("id"):
        ws.send(json.dumps({
            "id": data["id"],
            "message": "pong",
            "data": "",
        }))
        return
    logging.error("Connection id not found")


def handleChatGptRequest(ws, data):
    if not cookies:
        logging.error("Cookies not found")
        return
    if not access_token:
        logging.error("Access token not found")
        return
    if not data.get("id"):
        logging.error("Connection id not found")
        return
    if not data.get("data"):
        logging.error("Message not found")
        return
    
    chatgptRequestPayload = json.loads(data["data"])
    # {
    #     "message_id": "ca7bdb17-1de2-4d8e-94fc-c5b3455f8ec4",
    #     "conversation_id": "",
    #     "parent_id": "225bb0f1-89d4-488a-8657-980d8b7598c2",
    #     "content": "Hello world"
    # }
    logging.warning(json.dumps(chatgptRequestPayload, indent=4))
    def synchronize_async_func(func_to_await):
        async_resp = []
        async def run_and_capture_result():
            r = await func_to_await
            async_resp.append(r)
        loop = asyncio.new_event_loop()
        coroutine = run_and_capture_result()
        loop.run_until_complete(coroutine)
        loop.close()
        return async_resp[0]

    def post_conversation_sync(conversation: Conversation):
        return synchronize_async_func(post_conversation(conversation, cookies, access_token))
    
    if not chatgptRequestPayload.get("conversation_id"):
        chatgptRequestPayload["conversation_id"] = None
    if not chatgptRequestPayload.get("message_id"):
        chatgptRequestPayload["message_id"] = str(uuid.uuid4())
    if not chatgptRequestPayload.get("parent_id"):
        chatgptRequestPayload["parent_id"] = str(uuid.uuid4())
    convPayload = Conversation(
        model="text-davinci-002-render",
        action="next",
        parent_message_id=chatgptRequestPayload.get("parent_id"),
        conversation_id=chatgptRequestPayload.get("conversation_id"),
        messages=[ConversationMessages(
            role='user',
            content=ConversationMessagesContent(
                content_type='text',
                parts=[chatgptRequestPayload.get('content')],
            ),
            id=chatgptRequestPayload['message_id'],
        )]
    )
    chatgptResponse = post_conversation_sync(conversation=convPayload)
    if not chatgptResponse:
        logging.error("chatgptResponse is empty")
        return
    if chatgptResponse.status_code != 200:
        logging.error(f"chatgptResponse status code is {chatgptResponse.status_code}")
        return
    resp_body: str = chatgptResponse.text
    resp_body = resp_body.split("data:")[-2]
    resp_body = resp_body.strip()
    chatgptResponseJson = json.loads(resp_body)
    logging.info(json.dumps(chatgptResponseJson, indent=4))
    websocketPayload = {
        "response_id": chatgptResponseJson["message"]["id"],
        "conversation_id": chatgptResponseJson["conversation_id"],
        "content": chatgptResponseJson["message"]["content"]["parts"][0],
    }
    ws.send(json.dumps({
        "id": data["id"],
        "message": "ChatGptResponse",
        "data": json.dumps(websocketPayload),
    }))
    ...
    # const responseData = JSON.stringify({
    # response_id: lastElement.message.id,
    # conversation_id: lastElement.conversation_id,
    # content: lastElement.message.content.parts[0],
    # });
    # sendWebSocketMessage(
    # ws,
    # data.id,
    # "ChatGptResponse",
    # responseData
    # );
    

def handleWebSocket(chatgpt_api_server_uri):
    global wsapp
    uri = ""
    if chatgpt_api_server_uri:
        uri = chatgpt_api_server_uri
    if CHATGPT_API_SERVER_URI:
        uri = CHATGPT_API_SERVER_URI
    wsuri = f"ws://{uri}/client/register"
    logging.info(f"Connecting to {wsuri}")
    def on_message(wsapp, message):
        
        data = json.loads(message)
        logging.info(f"Message received: {json.dumps(message, indent=4)}")
        match data["message"]:
            case "Connection id":
                handleConnectionId(wsapp, data)
            case "ping":
                handlePing(wsapp, data)
            case "ChatGptRequest":
                handleChatGptRequest(wsapp, data)
            case _:
                logging.error("Unknown message")
                logging.error(data)

    def on_error(wsapp, error):
        logging.error(error)
    def on_close(wsapp):
        logging.info("### WebSocket closed ###")
    def on_open(wsapp):
        logging.info("### WebSocket opened ###")
    try:
        wsapp = websocket.WebSocketApp(wsuri, on_message=on_message, on_open=on_open, on_error=on_error, on_close=on_close)
        wsapp.run_forever()
    except Exception as e:
        logging.error(e)
        logging.error("### WebSocket error ###")
    finally:
        logging.info("### WebSocket finally ###")
        if wsapp:
            wsapp.close()


# def handleWebSocket(chatgpt_api_server_uri):
#     ws = websocket.WebSocket()
#     uri = ""
#     if chatgpt_api_server_uri:
#         uri = chatgpt_api_server_uri
#     if CHATGPT_API_SERVER_URI is None:
#         uri = CHATGPT_API_SERVER_URI
#     wsuri = f"ws://{uri}/client/register"
#     logging.info(f"Connecting to {wsuri}")
#     try:
#         ws.connect(wsuri)
#         logging.info("Connected to websocket")
#         data = ws.recv()
#         data = json.loads(data)
#         print(json.dumps(data, indent=4))
#     except Exception as e:
#         logging.error(e)
#         logging.error("Failed to connect to websocket")
#     finally:
#         ws.close()
#     logging.info("Websocket closed")

# async def handleWebSocket(chatgpt_api_server_uri):
#     try:
#         uri = ""
#         if chatgpt_api_server_uri:
#             uri = chatgpt_api_server_uri
#         if CHATGPT_API_SERVER_URI is None:
#             uri = CHATGPT_API_SERVER_URI
#         wsuri = f"ws://{uri}/client/register"
#         logging.info(f"Connecting to {wsuri}")
#         async with websockets.connect(wsuri) as ws:
#             logging.info("Connected to websocket")
#             while True:
#                 data = await ws.recv()
#                 data = json.loads(data)
#                 print("Received: \n\n")
#                 print(json.dumps(data, indent=4))
#                 print("\n\n")
#     except Exception as e:
#         logging.error(e)

@app.get("/login")
async def read_login(chatgpt_api_server_uri: str, background_tasks: BackgroundTasks):
    logging.info("Login request received")
    global cookies
    global access_token
    logging.info("Getting cookies...")
    cookies = await login()
    if cookies is None:
        return {"status": "error"}
    logging.info("Getting access token...")
    sleep(2)
    access_token = await get_access_token(cookies)
    logging.info("Cookies: ")
    for cookie in cookies:
        logging.info(cookie)
    logging.info("Access token: ")
    logging.info(access_token)
    logging.info("Connecting to websocket...")
    background_tasks.add_task(handleWebSocket, chatgpt_api_server_uri)
    return {
        "status": "success",
        "cookies": cookies,
        "access_token": access_token
    }

# testing purposes only
@app.post("/register")
async def register(background_tasks: BackgroundTasks):
    background_tasks.add_task(handleWebSocket)
    return {"status": "success"}



@app.post("/reset-auth-session")
async def reset_auth_session():
    global cookies
    global access_token
    cookies = None
    access_token = None
    return {"status": "success"}


@app.get("/cookies")
async def get_cookies():
    if cookies is None or len(cookies) == 0:
        return {"status": "error", "cookies": []}

    return {"cookies": cookies}


@app.get("/access-token")
async def _access_token():
    if access_token is None or len(access_token) == 0:
        return {"status": "error", "access_token": ""}

    return {"access_token": access_token}


@app.get("/refresh-access-token")
async def refresh_access_token():
    global access_token
    global cookies
    if cookies:
        logging.info("Refreshing access token...")
        res = await get_access_token(cookies)
        if res is None:
            return {"status": "error", "error": "Access token not found"}
        access_token = res
        return {"status": "success", "access_token": access_token}

    return {"status": "error", "error": "Cookies not found"}


@app.get("/test")
async def test(response: Response):
    response.status_code = status.HTTP_403_FORBIDDEN
    return {"status": "error", "error": "Forbidden"}


@app.post("/reset-wait")
async def reset_wait():
    try:
        global is_wait
        logging.info("Resetting is_wait")
        await asyncio.sleep(1)
        is_wait = False
        return {"status": "success"}
    except:
        return {"status": "error"}


@app.post("/backend-api/conversation")
async def conversation(conversation: Conversation):
    global cookies
    global access_token
    _response = {"status": "success", "error": [], "data": {}}
    if cookies is None:
        _response["status"] = "error"
        _response["error"].append("Cookies not found")
    if access_token is None:
        _response["status"] = "error"
        _response["error"].append("Access token not found")

    # if _response["status"] == "error":
    #     return _response

    # response["data"] = await post_conversation(conversation, cookies, access_token)
    res = await post_conversation(conversation, cookies, access_token)
    logging.info(res.status_code)
    if res is None:
        logging.info("Response is None")
        # response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        _response["status"] = "error"
        _response["error"].append("Internal server error")

    if res.status_code == 401:
        logging.info("Unauthorized")
        _response["status"] = "error"
        # response.status_code = status.HTTP_401_UNAUTHORIZED
        _response["error"].append("Unauthorized")

    if res.status_code == 403:
        logging.info("Forbidden")
        _response["status"] = "error"
        # response.status_code = status.HTTP_403_FORBIDDEN
        _response["error"].append("Forbidden")

    if res.status_code == 404:
        logging.info("Not found")
        _response["status"] = "error"
        # response.status_code = status.HTTP_404_NOT_FOUND
        _response["error"].append("Not found")

    if res.status_code == 200:
        logging.info("Success")
        _response["status"] = "success"
        resp_body: str = res.text
        resp_body = resp_body.split("data:")[-2]
        resp_body = resp_body.strip()
        _response["data"] = json.loads(resp_body)

    return _response


@app.on_event("shutdown")
def shutdown_event():
    if wsapp:
        logging.info("Closing websocket connection")
        wsapp.close()
        logging.info("Websocket connection closed")
    logging.info("Shutting down...")

# import uvicorn

# if __name__ == "__main__":
#     config = uvicorn.Config("main:app", port=8080, log_level="info", reload=False)
#     server = uvicorn.Server(config)
#     server.run()
