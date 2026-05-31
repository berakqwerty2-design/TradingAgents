from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

# Salin konfigurasi bawaan
config = DEFAULT_CONFIG.copy()

# Lo bisa tambahkan konfigurasi API key atau LLM provider di sini jika perlu
# config["llm_provider"] = "openai" 

ta = TradingAgentsGraph(debug=True, config=config)

# Langsung tembak Ticker (misal "SPY" atau "BTC-USD") dan tanggalnya
# Bot akan langsung bekerja tanpa meminta input terminal
_, decision = ta.propagate("BTC-USD", "2026-05-31") 

print("================ HASIL KEPUTUSAN TRADING ================")
print(decision)