import os
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

# ==========================================
# FORCE ENV
# ==========================================
BASE_URL = "https://token-plan-sgp.xiaomimimo.com/v1"
API_KEY = "ISI_API_KEY_LO"

# WAJIB SET SEMUA VARIAN ENV
os.environ["OPENAI_API_KEY"] = API_KEY
os.environ["OPENAI_BASE_URL"] = BASE_URL
os.environ["OPENAI_API_BASE"] = BASE_URL

print("[*] Setup Sistem LLM...")
print(f"[*] Base URL API : {BASE_URL}")

# ==========================================
# CONFIG
# ==========================================
config = DEFAULT_CONFIG.copy()

MODEL_NAME = "mimo-v2.5-pro"

config["deep_think_llm"] = MODEL_NAME
config["quick_think_llm"] = MODEL_NAME

# override llm config
config["llm"] = {
    "model": MODEL_NAME,
    "base_url": BASE_URL,
    "api_key": API_KEY,
    "temperature": 0.1
}

print(f"[*] Model Target : {MODEL_NAME}")
print("[*] Init TradingAgents...")

try:
    ta = TradingAgentsGraph(
        debug=True,
        config=config
    )

    print("[*] Running analysis BTC-USD...")

    _, decision = ta.propagate(
        "BTC-USD",
        "2026-05-31"
    )

    print(decision)

except Exception as e:
    import traceback
    print("\n[!] FULL ERROR:")
    traceback.print_exc()
