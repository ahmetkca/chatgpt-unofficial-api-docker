# 端口规划
# 9000 - nginx
# 9001 - websocketify
# 5901 - tigervnc

# based on ubuntu 18.04 LTS
FROM ubuntu:18.04 as base

# 各种环境变量
ENV LANG=en_US.UTF-8 \
    LC_ALL=en_US.UTF-8 \
    S6_BEHAVIOUR_IF_STAGE2_FAILS=2 \
    S6_CMD_ARG0=/sbin/entrypoint.sh \
    VNC_GEOMETRY=800x600 \
    VNC_PASSWD=MAX8char \
    USER_PASSWD='' \
    DEBIAN_FRONTEND=noninteractive

# 首先加用户，防止 uid/gid 不稳定
RUN groupadd user && useradd -m -g user user && \
    # 安装依赖和代码
    apt-get update && apt-get upgrade -y && \
    apt-get install -y \
        git \
        ca-certificates wget locales \
        nginx sudo \
        xorg openbox python-numpy rxvt-unicode && \
    wget -O - https://github.com/just-containers/s6-overlay/releases/download/v1.22.1.0/s6-overlay-amd64.tar.gz | tar -xzv && \
    # workaround for https://github.com/just-containers/s6-overlay/issues/158
    ln -s /init /init.entrypoint && \
    # tigervnc
    wget -O /tmp/tigervnc.tar.gz https://sourceforge.net/projects/tigervnc/files/stable/1.10.1/tigervnc-1.10.1.x86_64.tar.gz && \
    tar xzf /tmp/tigervnc.tar.gz -C /tmp && \
    chown root:root -R /tmp/tigervnc-1.10.1.x86_64 && \
    tar c -C /tmp/tigervnc-1.10.1.x86_64 usr | tar x -C / && \
    locale-gen en_US.UTF-8 && \
    # novnc
    mkdir -p /app/src && \
    git clone --depth=1 https://github.com/novnc/noVNC.git /app/src/novnc && \
    git clone --depth=1 https://github.com/novnc/websockify.git /app/src/websockify && \
    apt-get purge -y git wget && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -fr /tmp/* /app/src/novnc/.git /app/src/websockify/.git /var/lib/apt/lists

# copy files
COPY ./docker-root /

EXPOSE 9000/tcp 9001/tcp 5901/tcp


ENTRYPOINT ["/init.entrypoint"]
CMD ["start"]



FROM base as chromedriver

# chromedriver
RUN apt-get update -y && \
    apt-get upgrade -y && \
    apt-get install -y wget unzip curl && \
    apt-get install -y wget && \
    wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt-get install -y ./google-chrome-stable_current_amd64.deb && \
    wget https://chromedriver.storage.googleapis.com/108.0.5359.71/chromedriver_linux64.zip && \
    unzip chromedriver_linux64.zip && \
    mv chromedriver /usr/bin/chromedriver && \
    chown root:root /usr/bin/chromedriver && \
    chmod +x /usr/bin/chromedriver

RUN apt-get update -y \ 
    && apt-get install -y --no-install-recommends \
    make build-essential libssl-dev zlib1g-dev libbz2-dev \
    libreadline-dev libsqlite3-dev wget ca-certificates curl \ 
    llvm libncurses5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev \ 
    libffi-dev liblzma-dev mecab-ipadic-utf8 git

FROM chromedriver AS python

USER user

ENV PYTHON_VERSION 3.11.0

ENV HOME=/home/user

# Set-up necessary Env vars for PyEnv
ENV PYENV_ROOT ${HOME}/.pyenv
# ENV PATH="$PATH:$PYENV_ROOT/shims:$PYENV_ROOT/bin"
ENV PATH="${PYENV_ROOT}/shims:${PATH}"
ENV PATH="${PYENV_ROOT}/bin:${PATH}"

# Install pyenv
RUN set -ex \
    && curl https://pyenv.run | bash \
    && pyenv update \
    && pyenv install $PYTHON_VERSION \
    && echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc \
    && echo 'eval "$(pyenv init -)"' >> ~/.bashrc \
    && pyenv virtualenv $PYTHON_VERSION venv \
    && pyenv global venv \
    && pyenv rehash \
    && pip install --upgrade pip

WORKDIR ${HOME}/api

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY ./app .

EXPOSE 8080/tcp

USER root

WORKDIR /app

COPY vncmain.sh .

RUN chmod +x ./vncmain.sh
