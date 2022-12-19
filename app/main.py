import json
from typing import List, Optional
import undetected_chromedriver as uc
import time
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException

logging.basicConfig(level=logging.INFO)

# input("Press enter to start")
# print("Sleeping for 60 seconds")
# time.sleep(60)
import os

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

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


driver = uc.Chrome(
    version_main=108,
    no_sandbox=True,
    disable_gpu=False,
    keep_alive=True,
    headless=False,
    suppress_welcome=True,
)
parent_window_handle = driver.current_window_handle
driver.implicitly_wait(15)

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


def close_all_windows_except_parent():
    for handle in driver.window_handles:
        if handle != parent_window_handle:
            driver.switch_to.window(handle)
            driver.close()


def create_new_window_and_switch_to_it() -> bool:
    driver.window_new()
    for handle in driver.window_handles:
        if handle != parent_window_handle:
            driver.switch_to.window(handle)
            return True
    return False


async def manual_login():
    close_all_windows_except_parent()
    assert create_new_window_and_switch_to_it() == True
    recaptcha = None
    wait_result = await wait()
    assert wait_result == False
    
    cookies_ = driver.get_cookies()

    # TODO: Check if cookies are valid.
    

async def login():
    close_all_windows_except_parent()
    assert create_new_window_and_switch_to_it() == True
    driver.delete_all_cookies()
    print(driver.current_window_handle)

    logging.info("Driver started")
    driver.get("https://chat.openai.com/auth/login")
    try:
        print("SESSION_ID: " + str(driver.session_id))
    except:
        logging.error("Session ID not found")

    logging.info("Waiting cloudflare, 15 seconds")
    time.sleep(15)
    loginBtn = None
    try:
        loginBtn = driver.find_element(By.CSS_SELECTOR, "button.btn:nth-child(1)")
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
    # driver.quit()
    return cookies_


from chatgpt import post_conversation, Conversation, get_access_token
from fastapi import FastAPI, Response, status

app = FastAPI()

cookies: Optional[List[dict[str, str]]] = None
access_token: Optional[str] = None


@app.get("/login")
async def read_login():
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


# import uvicorn

# if __name__ == "__main__":
#     config = uvicorn.Config("main:app", port=8080, log_level="info", reload=False)
#     server = uvicorn.Server(config)
#     server.run()
