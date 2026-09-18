# 🏆 BUP CSE Fest 2026 — GridWise Hackathon: Challenge Breakdown & 3h Battle Plan

---

## What This Challenge Actually Is (TL;DR)

You are building a **single HTTP API** that:

1. Receives a 24-hour campus energy scenario (demand, solar, tariff per hour) + battery specs + **1–3 operator notes in plain English**
2. Uses an **LLM to interpret** those notes into structured directives (e.g. "reduce solar", "don't charge battery", etc.)
3. **Validates** the LLM output with deterministic guardrails
4. **Solves a cost-minimization optimization** (Linear Programming) over 24 hours, respecting all directives
5. Returns a JSON response with both the interpretation AND the optimized schedule

```
[Judge sends JSON] → Your API → [LLM interprets notes] → [Guardrails validate] → [LP Solver optimizes] → [JSON response]
```

---

## The 6 Directive Types You Must Handle

These are the ONLY 6 things an operator note can mean:

| # | Directive | What It Does | `structured_adjustment` Shape |
|:-:|:----------|:-------------|:-----------------------------|
| 1 | `solar_reduction` | Reduce usable solar to `factor` fraction during `hours` | `{"hours": [...], "factor": 0.2}` |
| 2 | `minimum_battery_reserve` | Battery must stay ≥ X kWh during `hours` | `{"hours": [...], "minimum_energy_kwh": 100}` |
| 3 | `no_charge_window` | Battery cannot charge during `hours` | `{"hours": [...]}` |
| 4 | `no_discharge_window` | Battery cannot discharge during `hours` | `{"hours": [...]}` |
| 5 | `max_grid_window` | Grid import capped at X kWh during `hours` | `{"hours": [...], "max_grid_kwh": 155}` |
| 6 | `no_op` | Note is irrelevant (distractor) | `null` |

> [!IMPORTANT]
> **Time convention**: "1 PM to 3 PM" = hours `[13, 14]` (start inclusive, end exclusive)  
> **Factor semantics**: "80% reduction" = `factor: 0.2` (20% REMAINS)

---

## The Math You Must Solve (LP Problem)

### Objective
$$\min \sum_{h=0}^{23} \text{grid\_kwh}[h] \times \text{tariff}[h]$$

### Hard Constraints (Every Hour)
```
grid_kwh + solar_used + battery_discharge = demand + battery_charge     (energy balance)
0 ≤ solar_used ≤ effective_solar                                       (solar cap)
0 ≤ battery_charge ≤ max_charge_per_hour                               (charge rate)
0 ≤ battery_discharge ≤ max_discharge_per_hour                         (discharge rate)
minimum_energy ≤ battery_energy_after ≤ capacity                       (battery bounds)
battery_energy_after[h] = battery_energy_after[h-1] + charge - discharge
grid_kwh ≥ 0
```

### End-of-Day Rule
$$\text{battery\_energy\_after}[23] = \text{initial\_energy\_kwh}$$

### Directive Constraints
- `solar_reduction` → `effective_solar[h] = solar_kwh[h] * factor` for listed hours
- `minimum_battery_reserve` → `battery_energy_after[h] ≥ max(base_min, directive_min)` for listed hours
- `no_charge_window` → `battery_charge[h] = 0` for listed hours
- `no_discharge_window` → `battery_discharge[h] = 0` for listed hours
- `max_grid_window` → `grid_kwh[h] ≤ max_grid_kwh` for listed hours

> [!TIP]
> This is a standard **Linear Program (LP)**. Use **PuLP** or **SciPy linprog**. It will solve in milliseconds.

---

## Scoring Breakdown (100 Points)

| Category | Points | What Matters Most |
|:---------|:------:|:------------------|
| **LLM Directive Interpretation** | **25** | Correctly classify notes → directive types, extract hours & numbers |
| **Directive Application & Constraints** | **25** | Schedule ACTUALLY obeys the directives + energy balance |
| **Optimization Quality** | **10** | How close your cost is to the optimal (ratio formula) |
| **API Contract & Schema** | **10** | Exact JSON field names, types, status codes |
| **Performance & Reliability** | **10** | p95 < 5s, no crashes on bad input |
| **Deployment & Docker** | **10** | Reachable endpoint + working Docker image |
| **Documentation & Reproducibility** | **10** | README with setup instructions |

> [!WARNING]
> **50 out of 100 points** come from LLM interpretation (25) + directive application (25). These are your bread and butter. Get these right first.

---

## Sample Case Patterns (From the 10 Public Cases)

| Case | Directives | Key Test |
|:-----|:-----------|:---------|
| SAMPLE-01 | `solar_reduction` + `no_op` | Basic solar + distractor |
| SAMPLE-02 | `no_charge_window` | Single hard constraint |
| SAMPLE-03 | `minimum_battery_reserve` | "50% of capacity" → 100 kWh (math conversion) |
| SAMPLE-04 | `no_discharge_window` | Discharge blocked in expensive hours |
| SAMPLE-05 | `max_grid_window` | Grid cap during peak |
| SAMPLE-06 | `solar_reduction` + `no_charge_window` + `no_op` | 3 notes, mixed |
| SAMPLE-07 | `minimum_battery_reserve` + `max_grid_window` | Two hard constraints |
| SAMPLE-08 | `no_charge_window` + `no_discharge_window` | Separate charge/discharge blocks |
| SAMPLE-09 | `solar_reduction` + `no_op` | "80% reduction" = factor 0.2 |
| SAMPLE-10 | `minimum_battery_reserve` + `max_grid_window` + `no_op` | 3 notes, evening combo |

---

## Tech Stack Recommendation

| Component | Choice | Why |
|:----------|:-------|:----|
| **Language** | Python 3.10+ | Fastest to prototype; rich ecosystem |
| **Framework** | **FastAPI** | Auto JSON validation, async support, fast |
| **LLM** | **Gemini Flash** or **GPT-4o-mini** via API | Fast, cheap, accurate for structured extraction |
| **Optimizer** | **PuLP** (with CBC solver) | Pure LP, pip installable, no external deps |
| **Container** | **Dockerfile** based on `python:3.11-slim` | Lightweight, reproducible |
| **Deployment** | **Railway** / **Render** / **Fly.io** | Free tier, quick deploy, public URL |

---

## ⏱️ 3-Hour Battle Plan

### Phase 1: API Skeleton (0:00 – 0:20) — 20 min

- [ ] `pip install fastapi uvicorn pulp httpx` (+ your LLM SDK)
- [ ] Create `main.py` with FastAPI
- [ ] `GET /health` → returns `{"status": "ok"}`
- [ ] `POST /optimize-energy` → accepts JSON, returns hardcoded stub response
- [ ] Verify with `curl` locally
- [ ] **Pydantic models** for request/response schemas (copy field names EXACTLY from spec)

### Phase 2: LLM Interpreter (0:20 – 1:00) — 40 min

- [ ] Write a **system prompt** that tells the LLM:
  - Here are the 6 directive types with their exact JSON shapes
  - Extract `directive_type`, `hours`, numeric values
  - Mark irrelevant notes as `no_op`
  - "1 PM to 3 PM" = `[13, 14]`
  - "80% reduction" = `factor: 0.2` (remaining fraction)
- [ ] Call LLM with the operator notes + battery context
- [ ] Parse the LLM's JSON response into `directive_interpretation` entries
- [ ] Handle LLM parse failures gracefully (fallback to `no_op` if malformed)

> [!TIP]
> **Prompt Engineering is the 25-point key.** Give the LLM explicit few-shot examples from the spec. Ask it to return ONLY valid JSON. Use `json_mode` / structured output if your provider supports it.

### Phase 3: Deterministic Guardrails (1:00 – 1:20) — 20 min

- [ ] Validate `directive_type` is one of the 6 allowed values
- [ ] Validate `hours` are unique ints 0–23, sorted ascending
- [ ] Validate `factor` is 0–1 for `solar_reduction`
- [ ] Validate `minimum_energy_kwh` ≤ battery capacity, ≥ 0
- [ ] Validate `max_grid_kwh` ≥ 0
- [ ] Ensure `no_op` has `applies=false`, `structured_adjustment=null`
- [ ] Ensure all others have `applies=true`
- [ ] Reject/fix any LLM hallucinations

### Phase 4: LP Optimizer (1:20 – 2:00) — 40 min

- [ ] Build PuLP model with 24-hour variables:
  - `grid_kwh[h]`, `solar_used[h]`, `charge[h]`, `discharge[h]`, `battery_energy[h]`
- [ ] Add constraints for each hour (energy balance, solar cap, battery bounds, rate limits)
- [ ] Add end-of-day neutrality: `battery_energy[23] == initial_energy`
- [ ] Apply directives as additional constraints
- [ ] Objective: minimize `sum(grid[h] * tariff[h])`
- [ ] Solve and extract results into `hourly_plan` format
- [ ] Compute `total_grid_kwh`, `total_cost_bdt`, `peak_grid_kwh` from the plan
- [ ] **Test against ALL 10 sample cases** — compare costs

### Phase 5: Docker + Deploy + Docs (2:00 – 2:30) — 30 min

- [ ] Write `Dockerfile`:
  ```dockerfile
  FROM python:3.11-slim
  WORKDIR /app
  COPY requirements.txt .
  RUN pip install -r requirements.txt
  COPY . .
  CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
  ```
- [ ] Build & test locally: `docker build -t gridwise . && docker run -p 8000:8000 gridwise`
- [ ] Push to **Docker Hub** or **GHCR**
- [ ] Deploy to **Railway/Render/Fly.io** — get public URL
- [ ] Test both endpoints from outside
- [ ] Write `README.md` with:
  - Setup instructions, env var names, model/provider, run command
  - curl examples for `/health` and `/optimize-energy`
  - Architecture explanation (LLM → guardrails → PuLP LP → response)

### Phase 6: Testing & Polish (2:30 – 3:00) — 30 min

- [ ] Run ALL 10 sample cases through your deployed endpoint
- [ ] Verify `total_cost_bdt` matches expected (within 0.01 tolerance)
- [ ] Test with malformed JSON → should return 400, not crash
- [ ] Test with empty/weird operator notes → should handle gracefully
- [ ] Check p95 latency < 5 seconds
- [ ] Make GitHub repo public (after deadline)
- [ ] Final `curl` check from phone/different network

---

## Critical Gotchas to Avoid

| Mistake | Consequence |
|:--------|:-----------|
| ❌ "80% reduction" → `factor: 0.8` | Should be `0.2` (what REMAINS). Costs you 5+ points. |
| ❌ "1 PM to 3 PM" → `[13, 14, 15]` | End is exclusive. Should be `[13, 14]`. |
| ❌ Forgetting end-of-day battery neutrality | Every case fails validation. 25+ points lost. |
| ❌ Using LLM only for `plan_summary` | Disqualified entirely. LLM must interpret notes. |
| ❌ `no_op` with `applies: true` | Must be `applies: false` + `structured_adjustment: null`. |
| ❌ Baking API keys into Docker image | Penalty. Use environment variables. |
| ❌ Crash on malformed input | Lose reliability points. Return 400/500 gracefully. |

---

## LLM System Prompt Template (Copy-Paste Ready)

```
You are a campus energy operator-note interpreter for the GridWise challenge.

Given operator notes about a 24-hour campus energy schedule, classify each note 
into EXACTLY ONE of these directive types:

1. solar_reduction — Solar output reduced. Return {"hours": [...], "factor": <0-1>}
   - "factor" is the REMAINING fraction. "80% reduction" = factor 0.2
2. minimum_battery_reserve — Battery must stay above X kWh. Return {"hours": [...], "minimum_energy_kwh": <number>}
3. no_charge_window — No battery charging allowed. Return {"hours": [...]}
4. no_discharge_window — No battery discharging allowed. Return {"hours": [...]}  
5. max_grid_window — Grid import capped. Return {"hours": [...], "max_grid_kwh": <number>}
6. no_op — Note is irrelevant to the energy schedule. Return null.

RULES:
- Time windows: start inclusive, end EXCLUSIVE. "1 PM to 3 PM" = hours [13, 14]
- Hours are integers 0-23, sorted ascending, unique
- "50% of battery capacity" with capacity 200 = minimum_energy_kwh 100
- Return ONLY valid JSON array. One entry per note.

Battery context will be provided for percentage calculations.
```
