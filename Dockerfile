FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /build

COPY . .

RUN pip install --upgrade pip setuptools wheel

RUN pip install --no-cache-dir \
    langchain==0.1.20 \
    langchain-core==0.1.52 \
    langgraph==0.1.19 \
    pydantic==2.7.1 \
    openai \
    anthropic \
    yfinance \
    pandas \
    numpy \
    ta \
    fastapi \
    uvicorn

RUN pip install --no-cache-dir .

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

RUN useradd --create-home appuser \
 && install -d -m 0755 -o appuser -g appuser /home/appuser/.tradingagents

USER appuser

WORKDIR /home/appuser/app

COPY --from=builder --chown=appuser:appuser /build .

ENTRYPOINT ["python", "run_bot.py"]
