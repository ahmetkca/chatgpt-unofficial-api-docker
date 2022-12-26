#!/bin/bash
# Set them to empty is NOT SECURE but avoid them display in random logs.
export VNC_PASSWD=''
export USER_PASSWD=''


(cd /home/user/api && /home/user/.pyenv/shims/uvicorn main:app --host 0.0.0.0 --port 8080 --reload)