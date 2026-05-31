import os
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG

# ==========================================
# 1. PAKSA ENVIRONMENT VARIABLES DI SINI
# ==========================================
# Kita coba HAPUS akhiran /v1 untuk menghindari error 404 dari Openresty
custom_base_url = os.getenv("OPENAI_BASE_URL", "https://token-plan-sgp.xiaomimimo.com")
os.environ["OPENAI_BASE_URL"] = custom_base_url

# Pastikan API Key terbaca (kalau di Railway kosong, dia pakai 'dummy-key')
api_key = os.getenv("OPENAI_API_KEY", "dummy-key")
os.environ["OPENAI_API_KEY"] = api_key

print(f"[*] Setup Sistem LLM...")
print(f"[*] Base URL API : {os.environ['OPENAI_BASE_URL']}")
print(f"[*] Status Key   : {'Terisi' if api_key != 'dummy-key' else 'KOSONG/DUMMY'}")

# ==========================================
# 2. OVERRIDE KONFIGURASI MODEL
# ==========================================
config = DEFAULT_CONFIG.copy()

# Memasukkan nama model Xiaomi Mimo lo
model_name = "xiaomi mimo v.2.5-pro"
config["model"] = model_name

# (Opsional) Berjaga-jaga kalau TradingAgents pakai nested dictionary untuk LLM
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
    
    # Jalankan agent untuk BTC-USD
    _, decision = ta.propagate("BTC-USD", "2026-05-31") 

    print("\n================ HASIL KEPUTUSAN TRADING ================")
    print(decision)
    print("=========================================================")

except Exception as e:
    print("\n[!] TERJADI ERROR CRASH SAAT EKSEKUSI:")
    print(str(e))
    print("[!] Cek kembali penulisan nama model atau format URL-nya.")