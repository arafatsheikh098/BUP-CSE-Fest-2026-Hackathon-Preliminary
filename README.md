# BUP CSE Fest 2026 - GridWise Hackathon Preliminary Solution

This repository contains the complete solution for the **Smart Campus Energy Optimization Challenge (GridWise)** at BUP CSE Fest 2026. It provides a robust, fast, and mathematically optimal HTTP API that translates unstructured operator notes into strict scheduling directives and computes an optimal 24-hour energy dispatch schedule.

---

## 🚀 Architecture Overview

Our solution implements the 3-stage pipeline mandated by the challenge:

1. **LLM Interpretation Engine (Groq API)**:
   - **Model**: `openai/gpt-oss-120b` via Groq Python SDK.
   - Operates in strict JSON mode with zero temperature (`temperature=0.0`) to extract operator note intents into structured directives (`solar_reduction`, `minimum_battery_reserve`, `no_charge_window`, `no_discharge_window`, `max_grid_window`, or `no_op`).
   - Includes automatic exponential backoff and retry mechanisms to handle API rate limits gracefully.

2. **Deterministic Guardrails**:
   - Validates and sanitizes raw model output against the problem specification:
     - Enforces ascending, unique integer hours ($0 \le h \le 23$) with half-open intervals ($[\text{start}, \text{end})$).
     - Caps reduction factors strictly between $[0.0, 1.0]$.
     - Constrains minimum energy reserve within $[0.0, \text{capacity\_kwh}]$.
     - Constrains grid import limits to non-negative floats.
     - Gracefully degrades malformed, unsupported, or missing outputs to safe `no_op` (`applies = false`, `structured_adjustment = null`).

3. **Linear Programming Optimizer (PuLP + CBC)**:
   - Formulates the 24-hour campus energy scheduling problem as a Mixed-Integer Linear Program (MILP).
   - Incorporates binary decision variables ($z_h \in \{0, 1\}$) to guarantee strict mutual exclusivity between battery charging and discharging.
   - Satisfies hourly energy balance, battery capacity limits, solar usage limits, grid import caps, and end-of-day battery energy neutrality.
   - Minimizes total grid electricity cost in BDT.
   - Solved with the COIN-OR CBC solver via PuLP.

---

## 🏆 Performance

- **Public Sample Cases**: **10/10 Passed** with exact decimal cost match.
- **Latency**: Mean per-request response time $\approx 1.5 - 2.5\text{s}$, well within the $p95 \le 5\text{s}$ threshold.
- **Complexity**: Solves LP instances in $< 50\text{ms}$.

---

## 🛠️ Tech Stack & Dependencies

- **Runtime**: Python 3.11+
- **API Framework**: FastAPI (`fastapi==0.111.0`, `uvicorn==0.30.1`)
- **Schema Validation**: Pydantic v2 (`pydantic==2.7.4`)
- **Mathematical Solver**: PuLP (`pulp==2.8.0`) + COIN-OR CBC
- **LLM Provider**: Groq SDK (`groq==0.11.0`)
- **HTTP Client**: HTTPX (`httpx==0.27.2`)
- **Environment Management**: Python-dotenv (`python-dotenv==1.0.1`)

---

## ⚙️ Configuration & Environment Variables

Create a `.env` file in the root directory (do not commit this file):

```ini
GROQ_API_KEY=your_groq_api_key_here
PORT=8000
```

| Variable | Required | Description |
| :--- | :---: | :--- |
| `GROQ_API_KEY` | **Yes** | API key for Groq Cloud. |
| `PORT` | No | Port to bind the server to (defaults to `8000`, dynamically set by Render). |

---

## 💻 Local Quickstart

### Method 1: Local Python Environment (Recommended for Development)

```bash
# 1. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
export GROQ_API_KEY="your_groq_api_key_here"

# 4. Start the server
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Method 2: Docker Compose (Live Hot-Reloading)

```bash
# Start container with volume mounting and auto-reload on file edits
docker compose up

# Stop container
docker compose down
```

---

## 🧪 Running Tests & Verification

### 1. Health Check
```bash
curl -s http://localhost:8000/health
# Expected: {"status":"ok"}
```

### 2. API Optimization Endpoint Example
```bash
curl -X POST http://localhost:8000/optimize-energy \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_id": "TEST-01",
    "operator_notes": ["Grid import capped at 100 kWh from 6 PM to 10 PM."],
    "battery": {
      "capacity_kwh": 500.0,
      "initial_energy_kwh": 200.0,
      "minimum_energy_kwh": 50.0,
      "max_charge_kwh_per_hour": 100.0,
      "max_discharge_kwh_per_hour": 100.0
    },
    "hours": [
      { "hour": 0, "demand_kwh": 145.0, "solar_kwh": 0.0, "tariff_bdt_per_kwh": 5.0 }
    ]
  }'
# Note: Provide all 24 hours in a real request.
```

### 3. Public Sample Validation Suite (10 Cases)
```bash
python test_runner.py
# Validates all 10 sample cases, records execution times, and generates api_results.md
```

### 4. Complex Corner Cases (13 Cases)
```bash
python test_corner_cases.py
# Tests challenging corner cases, rate limits, edge boundaries, and distractors
```

---

## 🌐 Production Deployment (Render)

This service is pre-configured for deployment on **Render** using native Python (`requirements.txt`).

1. In the [Render Dashboard](https://dashboard.render.com/):
   - Click **New +** $\to$ **Web Service**.
   - Connect this GitHub repository.
   - **Environment / Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
2. **Environment Variables**:
   - `GROQ_API_KEY`: *(your Groq API key)*
   - `PYTHON_VERSION`: `3.11.10`
3. **Health Check Path**: `/health`
4. Click **Create Web Service**.

> Render automatically injects the `$PORT` variable into the runtime environment.

---

## 🐳 Docker Fallback Image (Competition Item #4)

A production-ready Docker image is provided as a verified fallback execution path for organizers. 

**Compliance Checklist**:
- ✅ **Pullable Registry Reference**: `arafatsheikh098/gridwise-api:latest`
- ✅ **Exposed Port**: Exposes port `8000` as documented.
- ✅ **Host Binding**: Binds strictly to `0.0.0.0`.
- ✅ **Secrets**: Does **NOT** contain any baked-in secrets. You must inject `GROQ_API_KEY` at runtime.

### Pull & Run from Registry:
```bash
# 1. Pull the image
docker pull arafatsheikh098/gridwise-api:latest

# 2. Run the container
docker run -d -p 8000:8000 -e GROQ_API_KEY="your_groq_api_key_here" arafatsheikh098/gridwise-api:latest

# 3. Verify health
curl -s http://localhost:8000/health
```

### Build & Push (for Maintainers):
```bash
docker build -t arafatsheikh098/gridwise-api:latest .
docker push arafatsheikh098/gridwise-api:latest
```

---

## ⚠️ Known Limitations

1. **External API Dependency**: Semantic interpretation depends on the Groq API availability and network round-trip latency. Internal mathematical optimization is sub-second ($< 50\text{ms}$).
2. **API Quota**: Free-tier Groq API keys may experience rate limiting under high concurrency; the client includes exponential backoff retry logic to handle rate limit bursts.
