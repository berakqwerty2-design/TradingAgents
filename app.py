import os
import json
import threading
import traceback
from datetime import datetime
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Store analysis results in memory
analysis_store = {}

def run_analysis(job_id: str, ticker: str, trade_date: str):
    """Run TradingAgents analysis in background thread."""
    try:
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        from tradingagents.default_config import DEFAULT_CONFIG

        analysis_store[job_id]["status"] = "running"
        analysis_store[job_id]["logs"] = []

        config = DEFAULT_CONFIG.copy()
        config["llm_provider"] = "openai"
        config["deep_think_llm"] = os.environ.get("MODEL_NAME", "mimo-v2.5-pro")
        config["quick_think_llm"] = os.environ.get("MODEL_NAME", "mimo-v2.5-pro")
        config["temperature"] = 0
        config["max_tokens"] = 4000
        for bad_key in ["use_responses_api", "model", "llm"]:
            config.pop(bad_key, None)

        ta = TradingAgentsGraph(debug=False, config=config)
        _, decision = ta.propagate(ticker, trade_date)

        analysis_store[job_id]["status"] = "done"
        analysis_store[job_id]["result"] = decision
        analysis_store[job_id]["finished_at"] = datetime.utcnow().isoformat()

    except Exception as e:
        analysis_store[job_id]["status"] = "error"
        analysis_store[job_id]["error"] = traceback.format_exc()


# ─────────────────────────────────────────
# REST API endpoints
# ─────────────────────────────────────────

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "TradingAgents"})


@app.route("/analyze", methods=["POST"])
def analyze():
    """Start an analysis job. Returns job_id immediately."""
    data = request.get_json() or {}
    ticker = data.get("ticker", "BTC-USD").upper()
    trade_date = data.get("date", datetime.utcnow().strftime("%Y-%m-%d"))

    job_id = f"{ticker}_{trade_date}_{datetime.utcnow().strftime('%H%M%S')}"
    analysis_store[job_id] = {
        "job_id": job_id,
        "ticker": ticker,
        "date": trade_date,
        "status": "pending",
        "result": None,
        "error": None,
        "started_at": datetime.utcnow().isoformat(),
        "finished_at": None,
    }

    thread = threading.Thread(target=run_analysis, args=(job_id, ticker, trade_date))
    thread.daemon = True
    thread.start()

    return jsonify({"job_id": job_id, "status": "pending"})


@app.route("/status/<job_id>", methods=["GET"])
def status(job_id):
    """Check status of an analysis job."""
    job = analysis_store.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job)


@app.route("/jobs", methods=["GET"])
def list_jobs():
    """List all jobs."""
    return jsonify(list(analysis_store.values()))


# ─────────────────────────────────────────
# OpenWebUI / OpenAI-compatible Chat endpoint
# ─────────────────────────────────────────

@app.route("/v1/models", methods=["GET"])
def models():
    return jsonify({
        "object": "list",
        "data": [{
            "id": "tradingagents",
            "object": "model",
            "created": 1700000000,
            "owned_by": "tradingagents",
        }]
    })


@app.route("/v1/chat/completions", methods=["POST"])
def chat_completions():
    """
    OpenAI-compatible endpoint for OpenWebUI integration.
    Send: { "model": "tradingagents", "messages": [{"role":"user","content":"analyze BTC-USD"}] }
    """
    data = request.get_json() or {}
    messages = data.get("messages", [])
    stream = data.get("stream", False)

    # Extract ticker and date from last user message
    last_msg = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            last_msg = m.get("content", "")
            break

    # Parse ticker and date from message
    import re
    ticker_match = re.search(r'\b([A-Z]{1,5}(?:-USD)?)\b', last_msg.upper())
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', last_msg)

    ticker = ticker_match.group(1) if ticker_match else "BTC-USD"
    trade_date = date_match.group(1) if date_match else datetime.utcnow().strftime("%Y-%m-%d")

    # Run analysis synchronously for chat (blocking)
    result_text = ""
    try:
        from tradingagents.graph.trading_graph import TradingAgentsGraph
        from tradingagents.default_config import DEFAULT_CONFIG

        config = DEFAULT_CONFIG.copy()
        config["llm_provider"] = "openai"
        config["deep_think_llm"] = os.environ.get("MODEL_NAME", "mimo-v2.5-pro")
        config["quick_think_llm"] = os.environ.get("MODEL_NAME", "mimo-v2.5-pro")
        config["temperature"] = 0
        config["max_tokens"] = 4000
        for bad_key in ["use_responses_api", "model", "llm"]:
            config.pop(bad_key, None)

        ta = TradingAgentsGraph(debug=False, config=config)
        _, decision = ta.propagate(ticker, trade_date)
        result_text = decision or "Analysis complete but no decision returned."

    except Exception as e:
        result_text = f"❌ Error during analysis:\n```\n{traceback.format_exc()}\n```"

    response_payload = {
        "id": f"chatcmpl-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "object": "chat.completion",
        "created": int(datetime.utcnow().timestamp()),
        "model": "tradingagents",
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": result_text,
            },
            "finish_reason": "stop",
        }],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
    }

    if stream:
        def generate():
            chunk = {
                "id": response_payload["id"],
                "object": "chat.completion.chunk",
                "created": response_payload["created"],
                "model": "tradingagents",
                "choices": [{
                    "index": 0,
                    "delta": {"role": "assistant", "content": result_text},
                    "finish_reason": "stop",
                }]
            }
            yield f"data: {json.dumps(chunk)}\n\ndata: [DONE]\n\n"
        return Response(stream_with_context(generate()), content_type="text/event-stream")

    return jsonify(response_payload)


# ─────────────────────────────────────────
# Simple Web Dashboard
# ─────────────────────────────────────────

@app.route("/", methods=["GET"])
def dashboard():
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TradingAgents Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Syne:wght@400;700;800&display=swap" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<style>
  :root {
    --bg: #0a0a0f;
    --surface: #111118;
    --border: #1e1e2e;
    --accent: #00ff88;
    --accent2: #ff6b35;
    --text: #e2e2e8;
    --muted: #555570;
    --buy: #00ff88;
    --sell: #ff4466;
    --hold: #ffcc00;
  }
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Space Mono', monospace;
    min-height: 100vh;
  }
  .noise {
    position: fixed; inset: 0; pointer-events: none; z-index: 0;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)' opacity='0.03'/%3E%3C/svg%3E");
    opacity: 0.4;
  }
  .container { max-width: 1100px; margin: 0 auto; padding: 2rem; position: relative; z-index: 1; }
  header {
    display: flex; align-items: center; justify-content: space-between;
    padding: 1.5rem 0; border-bottom: 1px solid var(--border); margin-bottom: 2rem;
  }
  .logo { font-family: 'Syne', sans-serif; font-size: 1.5rem; font-weight: 800; letter-spacing: -0.02em; }
  .logo span { color: var(--accent); }
  .status-dot {
    width: 8px; height: 8px; border-radius: 50%; background: var(--accent);
    box-shadow: 0 0 8px var(--accent); animation: pulse 2s infinite;
    display: inline-block; margin-right: 0.5rem;
  }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:0.4} }

  .input-panel {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 12px; padding: 1.5rem; margin-bottom: 2rem;
  }
  .input-row { display: flex; gap: 1rem; flex-wrap: wrap; align-items: flex-end; }
  .field { display: flex; flex-direction: column; gap: 0.4rem; flex: 1; min-width: 140px; }
  label { font-size: 0.7rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.1em; }
  input {
    background: var(--bg); border: 1px solid var(--border); color: var(--text);
    padding: 0.6rem 0.8rem; border-radius: 6px; font-family: 'Space Mono', monospace;
    font-size: 0.9rem; outline: none; transition: border-color 0.2s;
  }
  input:focus { border-color: var(--accent); }
  .btn {
    background: var(--accent); color: #000; border: none; padding: 0.65rem 1.5rem;
    border-radius: 6px; font-family: 'Space Mono', monospace; font-weight: 700;
    font-size: 0.85rem; cursor: pointer; transition: all 0.2s; white-space: nowrap;
    text-transform: uppercase; letter-spacing: 0.05em;
  }
  .btn:hover { background: #00cc6e; transform: translateY(-1px); }
  .btn:disabled { opacity: 0.4; cursor: not-allowed; transform: none; }

  .jobs-grid { display: grid; gap: 1rem; margin-bottom: 2rem; }
  .job-card {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 10px; padding: 1.2rem; cursor: pointer;
    transition: border-color 0.2s;
  }
  .job-card:hover { border-color: var(--accent); }
  .job-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }
  .job-ticker { font-family: 'Syne', sans-serif; font-weight: 700; font-size: 1.1rem; }
  .badge {
    font-size: 0.65rem; padding: 0.2rem 0.5rem; border-radius: 4px;
    text-transform: uppercase; font-weight: 700; letter-spacing: 0.08em;
  }
  .badge-pending { background: #2a2a10; color: var(--hold); }
  .badge-running { background: #102a1a; color: var(--buy); animation: pulse 1s infinite; }
  .badge-done { background: #0a2a1a; color: var(--buy); }
  .badge-error { background: #2a0a10; color: var(--sell); }
  .job-meta { font-size: 0.75rem; color: var(--muted); }

  .result-panel {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 12px; padding: 1.5rem; display: none;
  }
  .result-panel.visible { display: block; }
  .result-panel h3 { font-family: 'Syne', sans-serif; font-size: 1rem; margin-bottom: 1rem; color: var(--accent); }
  .result-body { line-height: 1.7; font-size: 0.85rem; }
  .result-body h1,.result-body h2,.result-body h3 { font-family: 'Syne', sans-serif; margin: 1rem 0 0.5rem; }
  .result-body table { width: 100%; border-collapse: collapse; margin: 0.8rem 0; }
  .result-body th,.result-body td { border: 1px solid var(--border); padding: 0.4rem 0.6rem; text-align: left; font-size: 0.8rem; }
  .result-body th { background: var(--bg); color: var(--accent); }
  .result-body code { background: var(--bg); padding: 0.1rem 0.3rem; border-radius: 3px; font-size: 0.8rem; }
  .result-body hr { border: none; border-top: 1px solid var(--border); margin: 1rem 0; }

  .openwebui-info {
    background: var(--surface); border: 1px solid var(--border);
    border-left: 3px solid var(--accent2);
    border-radius: 10px; padding: 1.2rem; margin-bottom: 2rem;
  }
  .openwebui-info h4 { font-family: 'Syne', sans-serif; color: var(--accent2); margin-bottom: 0.5rem; }
  .openwebui-info code { color: var(--accent); font-size: 0.8rem; }
  .empty { text-align: center; color: var(--muted); padding: 2rem; font-size: 0.85rem; }

  .spinner {
    display: inline-block; width: 12px; height: 12px;
    border: 2px solid var(--border); border-top-color: var(--accent);
    border-radius: 50%; animation: spin 0.8s linear infinite; margin-right: 0.5rem;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
</style>
</head>
<body>
<div class="noise"></div>
<div class="container">
  <header>
    <div class="logo">Trading<span>Agents</span></div>
    <div style="font-size:0.75rem;color:var(--muted)">
      <span class="status-dot"></span>LIVE
    </div>
  </header>

  <div class="openwebui-info">
    <h4>🔌 OpenWebUI Integration</h4>
    <p style="font-size:0.8rem;color:var(--muted);margin-bottom:0.5rem">
      Tambahkan sebagai custom model di OpenWebUI → Settings → Connections → Add OpenAI API
    </p>
    <code id="base-url"></code>
    <script>document.getElementById('base-url').textContent = window.location.origin + '/v1'</script>
    <span style="color:var(--muted);font-size:0.75rem"> · Model ID: <code>tradingagents</code> · API Key: <code>any</code></span>
  </div>

  <div class="input-panel">
    <div class="input-row">
      <div class="field">
        <label>Ticker</label>
        <input id="ticker" value="BTC-USD" placeholder="BTC-USD, AAPL...">
      </div>
      <div class="field">
        <label>Date</label>
        <input id="date" type="date">
      </div>
      <button class="btn" id="run-btn" onclick="startAnalysis()">▶ Run Analysis</button>
    </div>
  </div>

  <div id="jobs-list" class="jobs-grid">
    <div class="empty">No analysis jobs yet. Run one above ↑</div>
  </div>

  <div class="result-panel" id="result-panel">
    <h3 id="result-title">Result</h3>
    <div class="result-body" id="result-body"></div>
  </div>
</div>

<script>
// Set today as default date
document.getElementById('date').value = new Date().toISOString().split('T')[0];

let jobs = [];
let pollTimers = {};

async function startAnalysis() {
  const ticker = document.getElementById('ticker').value.trim().toUpperCase();
  const date = document.getElementById('date').value;
  if (!ticker || !date) return alert('Fill in ticker and date');

  const btn = document.getElementById('run-btn');
  btn.disabled = true;
  btn.innerHTML = '<span class="spinner"></span>Starting...';

  try {
    const res = await fetch('/analyze', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({ticker, date})
    });
    const job = await res.json();
    jobs.unshift(job);
    renderJobs();
    pollJob(job.job_id);
  } catch(e) {
    alert('Failed to start: ' + e.message);
  }

  btn.disabled = false;
  btn.innerHTML = '▶ Run Analysis';
}

function pollJob(jobId) {
  if (pollTimers[jobId]) return;
  pollTimers[jobId] = setInterval(async () => {
    try {
      const res = await fetch('/status/' + jobId);
      const job = await res.json();
      const idx = jobs.findIndex(j => j.job_id === jobId);
      if (idx !== -1) jobs[idx] = job;
      renderJobs();
      if (job.status === 'done' || job.status === 'error') {
        clearInterval(pollTimers[jobId]);
        delete pollTimers[jobId];
        if (job.status === 'done') showResult(job);
      }
    } catch(e) {}
  }, 3000);
}

function renderJobs() {
  const el = document.getElementById('jobs-list');
  if (!jobs.length) {
    el.innerHTML = '<div class="empty">No analysis jobs yet. Run one above ↑</div>';
    return;
  }
  el.innerHTML = jobs.map(j => `
    <div class="job-card" onclick="showResult(${JSON.stringify(j).replace(/"/g, '&quot;')})">
      <div class="job-header">
        <span class="job-ticker">${j.ticker}</span>
        <span class="badge badge-${j.status}">
          ${j.status === 'running' ? '<span class="spinner"></span>' : ''}${j.status}
        </span>
      </div>
      <div class="job-meta">${j.date} · ${j.started_at ? j.started_at.replace('T',' ').slice(0,19) + ' UTC' : ''}</div>
    </div>
  `).join('');
}

function showResult(job) {
  const panel = document.getElementById('result-panel');
  const title = document.getElementById('result-title');
  const body = document.getElementById('result-body');

  panel.classList.add('visible');
  title.textContent = `${job.ticker} · ${job.date} · ${job.status.toUpperCase()}`;

  if (job.status === 'done' && job.result) {
    body.innerHTML = marked.parse(job.result);
  } else if (job.status === 'error') {
    body.innerHTML = '<pre style="color:var(--sell);font-size:0.75rem;overflow:auto">' + (job.error || 'Unknown error') + '</pre>';
  } else if (job.status === 'running') {
    body.innerHTML = '<div style="color:var(--muted)"><span class="spinner"></span>Analysis in progress... (~5-15 min)</div>';
  } else {
    body.innerHTML = '<div style="color:var(--muted)">Pending...</div>';
  }

  panel.scrollIntoView({behavior:'smooth'});
}
</script>
</body>
</html>"""


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
