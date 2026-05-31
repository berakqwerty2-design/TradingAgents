FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY . .

RUN pip install --upgrade pip

RUN pip uninstall -y langgraph langchain langchain-core

RUN pip install \
    langgraph==0.0.40 \
    langchain==0.1.16 \
    langchain-core==0.1.42 \
    langchain-community==0.0.32 \
    langchain-openai==0.1.3 \
    openai==1.23.6 \
    pandas \
    numpy \
    yfinance \
    ta \
    feedparser \
    beautifulsoup4 \
    lxml \
    requests

RUN pip install .

RUN useradd -m appuser
USER appuser

WORKDIR /home/appuser/app

COPY --chown=appuser:appuser . .

CMD ["python", "run_bot.py"]
