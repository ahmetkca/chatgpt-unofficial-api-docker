FROM oott123/novnc:latest AS base


FROM base AS chromedriver

RUN apt-get update -y && \
    apt-get upgrade -y && \
    apt-get install -y wget unzip curl
RUN apt-get install -y wget
RUN wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
RUN apt-get install -y ./google-chrome-stable_current_amd64.deb
RUN wget https://chromedriver.storage.googleapis.com/108.0.5359.71/chromedriver_linux64.zip
RUN unzip chromedriver_linux64.zip
RUN mv chromedriver /usr/bin/chromedriver
RUN chown root:root /usr/bin/chromedriver
RUN chmod +x /usr/bin/chromedriver

FROM chromedriver AS chatgpt

RUN apt-get update \ 
    && apt-get install -y --no-install-recommends \
    make build-essential libssl-dev zlib1g-dev libbz2-dev \
    libreadline-dev libsqlite3-dev wget ca-certificates curl \ 
    llvm libncurses5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev \ 
    libffi-dev liblzma-dev mecab-ipadic-utf8 git

RUN groupadd -r python-user && useradd -r -m -g python-user python-user

USER python-user

ENV PYTHON_VERSION 3.10.0

# Set-up necessary Env vars for PyEnv
ENV PYENV_ROOT /home/python-user/.pyenv
ENV PATH $PYENV_ROOT/shims:$PYENV_ROOT/bin:$PATH



# Install pyenv
RUN set -ex \
    && curl https://pyenv.run | bash \
    && pyenv update \
    && pyenv install $PYTHON_VERSION \
    && pyenv global $PYTHON_VERSION \
    && pyenv rehash

RUN pip install --upgrade pip

COPY --chown=user:user ./requirements.txt /home/python-user/app/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /home/python-user/app/requirements.txt

COPY --chown=user:user ./app /home/python-user/app

# RUN apt-get install -y git build-essential

FROM chatgpt AS laststage

USER root

EXPOSE 8080
# RUN usermod -a -G user python-user
# RUN usermod -a -G python-user user

# RUN mkdir -p -m 777 /home/python-user/app

# RUN touch /home/python-user/app/main.py
# RUN touch /home/python-user/app/screenshot0.png
# RUN touch /home/python-user/app/screenshot1.png
# RUN touch /home/python-user/app/screenshot2.png
# RUN touch /home/python-user/app/page_source.html
# RUN touch /home/python-user/app/cookies.txt

# RUN chown -R user:user /home/python-user/app

# RUN chmod 777 /home/python-user/app

# COPY --chown=user:user main.py /home/python-user/app/main.py

COPY vncmain.sh /app/vncmain.sh

RUN chmod +x /app/vncmain.sh
