FROM python:3.12-slim

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

RUN pip install \
    langgraph==0.2.56 \
    langchain-core==0.3.21 \
    langchain-community \
    langchain-openai \
    openai \
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
