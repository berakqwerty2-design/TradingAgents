import os
import traceback
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

# Baca dari environment Railway, jangan hardcode
BASE_URL = os.environ.get("OPENAI_BASE_URL") or os.environ.get("OPENAI_API_BASE", "https://token-plan-sgp.xiaomimimo.com/v1")
API_KEY = os.environ.get("OPENAI_API_KEY", "")

# Pastikan keduanya ter-set
os.environ["OPENAI_API_KEY"] = API_KEY
os.environ["OPENAI_BASE_URL"] = BASE_URL
os.environ["OPENAI_API_BASE"] = BASE_URL

print("[*] Setup Sistem LLM...")
print(f"[*] Base URL API : {BASE_URL}")
print(f"[*] API Key     : {API_KEY[:8]}...")

config = DEFAULT_CONFIG.copy()
config["llm_provider"] = "openai"
config["deep_think_llm"] = "mimo-v2.5-pro"
config["quick_think_llm"] = "mimo-v2.5-pro"
config["temperature"] = 0
config["max_tokens"] = 4000

for bad_key in ["use_responses_api", "model", "llm"]:
    config.pop(bad_key, None)

print("[*] Init TradingAgents...")

try:
    ta = TradingAgentsGraph(debug=True, config=config)
    print("[*] Running analysis BTC-USD...")
    print("[*] Trade Date : 2026-05-31")
    _, decision = ta.propagate("BTC-USD", "2026-05-31")
    print("\n================ RESULT ================")
    print(decision)
    print("========================================")
except Exception as e:
    print("\n[!] FULL ERROR:")
    traceback.print_exc()
