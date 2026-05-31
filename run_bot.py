import os
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

# ==========================================
# 1. PAKSA ENVIRONMENT VARIABLES DI SINI
# ==========================================
# Coba pakai /v1 tanpa garis miring di ujungnya dulu
custom_base_url = "https://token-plan-sgp.xiaomimimo.com/v1"
os.environ["OPENAI_BASE_URL"] = custom_base_url

# Ganti pakai API Key Mimo lo yang asli
api_key = "API_KEY_MIMO_LO_DISINI" 
os.environ["OPENAI_API_KEY"] = api_key

print(f"[*] Setup Sistem LLM...")
print(f"[*] Base URL API : {os.environ['OPENAI_BASE_URL']}")

# ==========================================
# 2. OVERRIDE DENGAN MODEL ID YANG BENER
# ==========================================
config = DEFAULT_CONFIG.copy()

# Pake ID yang barusan lo koreksi
model_name = "mimo-v2.5-pro"
config["model"] = model_name

# Buat jaga-jaga kalau library-nya baca nested config
if "llm" in config:
    config["llm"]["model"] = model_name
    config["llm"]["base_url"] = custom_base_url

print(f"[*] Model Target : {model_name}")
print("[*] Menginisialisasi Trading Agents Graph...")

# ==========================================
# 3. EKSEKUSI TRADING BOT
# ==========================================
try:
    ta = TradingAgentsGraph(debug=True, config=config)
    print("[*] Bot berjalan! Memulai analisis untuk BTC-USD...")
    
    # Jalankan agent
    _, decision = ta.propagate("BTC-USD", "2026-05-31") 

    print("\n================ HASIL KEPUTUSAN TRADING ================")
    print(decision)
    print("=========================================================")

except Exception as e:
    print("\n[!] TERJADI ERROR CRASH SAAT EKSEKUSI:")
    print(str(e))