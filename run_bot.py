import os
import traceback
from datetime import datetime

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

# =====================================================
# ENVIRONMENT
# =====================================================

BASE_URL = os.getenv(
    "OPENAI_API_BASE",
    "https://token-plan-sgp.xiaomimimo.com/v1"
)

API_KEY = os.getenv("OPENAI_API_KEY")

MODEL_NAME = "mimo-v2.5-pro"

# FORCE ENV
os.environ["OPENAI_API_BASE"] = BASE_URL
os.environ["OPENAI_BASE_URL"] = BASE_URL
os.environ["OPENAI_API_KEY"] = API_KEY

print("[*] Setup Sistem LLM...")
print(f"[*] Base URL API : {BASE_URL}")
print(f"[*] Model Target : {MODEL_NAME}")

# =====================================================
# CONFIG
# =====================================================

config = DEFAULT_CONFIG.copy()

# OVERRIDE MODEL
config["deep_think_llm"] = MODEL_NAME
config["quick_think_llm"] = MODEL_NAME

config["llm"] = {
    "model": MODEL_NAME,
    "base_url": BASE_URL,
    "api_key": API_KEY,
    "temperature": 0.1
}

print("[*] Init TradingAgents...")

# =====================================================
# RUN
# =====================================================

try:
    ta = TradingAgentsGraph(
        debug=True,
        config=config
    )

    ticker = "BTC-USD"

    # pakai tanggal hari ini
    trade_date = datetime.today().strftime("%Y-%m-%d")

    print(f"[*] Running analysis {ticker}...")
    print(f"[*] Trade Date : {trade_date}")

    _, decision = ta.propagate(
        ticker,
        trade_date
    )

    print("\n================ HASIL ANALISIS ================")
    print(decision)
    print("================================================")

except Exception as e:
    print("\n[!] FULL ERROR TRACE:")
    traceback.print_exc()
