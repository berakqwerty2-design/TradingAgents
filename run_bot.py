import os
import traceback

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

# =========================================================
# XIAOMI MIMO CONFIG
# =========================================================

BASE_URL = "https://token-plan-sgp.xiaomimimo.com/v1"
API_KEY = "ISI_API_KEY_LO"

os.environ["OPENAI_API_KEY"] = API_KEY
os.environ["OPENAI_BASE_URL"] = BASE_URL
os.environ["OPENAI_API_BASE"] = BASE_URL

print("[*] Setup Sistem LLM...")
print(f"[*] Base URL API : {BASE_URL}")

# =========================================================
# CONFIG
# =========================================================

config = DEFAULT_CONFIG.copy()

config["model"] = "mimo-v2.5-pro"

config["temperature"] = 0
config["max_tokens"] = 4000

if "llm" in config:

    config["llm"]["model"] = "mimo-v2.5-pro"

    config["llm"]["base_url"] = BASE_URL

    config["llm"]["api_key"] = API_KEY

    config["llm"]["temperature"] = 0

    config["llm"]["max_tokens"] = 4000

print("[*] Init TradingAgents...")

# =========================================================
# RUN BOT
# =========================================================

try:

    ta = TradingAgentsGraph(
        debug=True,
        config=config
    )

    print("[*] Running analysis BTC-USD...")
    print("[*] Trade Date : 2026-05-31")

    _, decision = ta.propagate(
        "BTC-USD",
        "2026-05-31"
    )

    print("\n================ RESULT ================")
    print(decision)
    print("========================================")

except Exception as e:

    print("\n[!] FULL ERROR:")
    traceback.print_exc()
