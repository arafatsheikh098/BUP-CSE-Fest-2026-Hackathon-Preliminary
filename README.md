# BUP CSE Fest 2026 - GridWise Hackathon Preliminary Solution

This repository contains our complete solution for the **Smart Campus Energy Optimization Challenge (GridWise)**. It provides a robust, fast, and mathematically optimal API that translates human operator notes into strict constraints and generates a cost-minimized 24-hour energy schedule.

## 🚀 Architecture

Our solution is designed around a 3-stage pipeline to ensure maximum accuracy and reliability:

1. **LLM Interpretation Engine (Groq API)**: We utilize the Groq API (specifically the `openai/gpt-oss-120b` model) in structured JSON mode to parse plain English operator notes. Groq was specifically chosen over standard Gemini/OpenAI free tiers to **avoid HTTP 429 Too Many Requests rate limits** during automated judging.
2. **Deterministic Guardrails**: The raw LLM output is passed through strict Python guardrails. This step enforces time-window formatting (e.g., converting "1 PM to 3 PM" to `[13, 14]`), validates factor percentages (e.g., "80% reduction" = `0.2` remaining), and gracefully degrades malformed responses to safe `no_op` directives.
3. **Linear Programming Optimizer (PuLP)**: We formulated the energy balance and directives as a strict mathematical Linear Program. Solved via the CBC engine, this guarantees that energy constraints are NEVER violated, battery neutrality is strictly enforced, and the overall BDT cost is mathematically minimized to the absolute lowest possible value.

## 🏆 Performance

Our API achieves a **perfect 10/10 passing score** against the provided Public Sample Cases, matching the expected `total_cost_bdt` exactly to the decimal.

## 🛠️ Tech Stack

- **Framework**: Python 3.11 + FastAPI (for high-performance async JSON serving)
- **Validation**: Pydantic (ensures 100% adherence to the hackathon's input/output schema)
- **Optimizer**: PuLP + COIN-OR CBC Solver (pure Linear Programming)
- **AI/LLM**: Groq Python SDK

## ⚙️ How to Run Locally

### Option 1: Docker (Recommended)
This is the safest way to run the API, as the Dockerfile automatically installs the required system binaries for the CBC mathematical solver.

```bash
# 1. Build the image
docker build -t gridwise-api .

# 2. Run the container (Make sure to pass your Groq API Key)
docker run -d -p 8000:8000 -e GROQ_API_KEY="your_groq_api_key_here" gridwise-api
```

### Option 2: Python Virtual Environment
Requires Python 3.11+ and the `coinor-cbc` binary installed on your system (e.g., `brew install cbc` on macOS or `apt-get install coinor-cbc` on Linux).

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set your API key
export GROQ_API_KEY="your_groq_api_key_here"

# Run the server
uvicorn main:app --host 0.0.0.0 --port 8000
```

## 🧪 Running the Tests

Once the server is running on `localhost:8000`, you can execute the test suite which validates the endpoint against the 10 provided sample cases:

```bash
python test_runner.py
```

## ⚠️ Known Limitations

While highly optimized, this solution has a few practical constraints:
1. **External Network Latency**: Because we rely on the Groq API for semantic extraction, total request latency is heavily bottlenecked by the network round-trip time to Groq's servers (typically ~1-2 seconds). The internal mathematical optimization itself takes `< 50ms`.
2. **API Key Dependency**: The application will instantly fail if the `GROQ_API_KEY` environment variable is not provided or if the key runs out of credits.
3. **LLM Hallucination Ceiling**: While our deterministic guardrails catch formatting errors and out-of-bounds numbers, the system is fundamentally dependent on the LLM correctly classifying the *intent* of the note. If the LLM entirely misclassifies a complex note (e.g., mistaking a `no_charge_window` for a `solar_reduction`), the guardrails cannot mathematically save it. However, the system prompt is highly tuned to mitigate this.
