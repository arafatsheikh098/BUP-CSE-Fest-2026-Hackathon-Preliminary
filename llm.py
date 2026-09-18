import os
import json
from typing import List, Dict, Any
from groq import Groq
from schemas import (
    DirectiveInterpretationEntry,
    SolarReductionAdjustment,
    MinBatteryReserveAdjustment,
    WindowOnlyAdjustment,
    MaxGridWindowAdjustment,
)
from dotenv import load_dotenv

load_dotenv()


# Try to get the API key from environment
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if GROQ_API_KEY:
    client = Groq(api_key=GROQ_API_KEY)
else:
    client = None

SYSTEM_PROMPT = """
You are an expert energy operations parser for BUP Smart Campus.
Your sole job is to translate 1 to 3 natural-language operator notes into structured machine directives.

### DIRECTIVE TYPES & REQUIRED ADJUSTMENTS:
1. "solar_reduction": Usable solar drops during specific hours.
   Adjustment: {"hours": [int, ...], "factor": float}
   CRITICAL: "factor" is the USABLE FRACTION REMAINING (0.0 to 1.0).
   - "drops to 20%" -> factor = 0.2
   - "80% reduction" / "cut by 80%" / "80% curtailment" -> factor = 0.2
   - "one-fifth output remains" / "one-fifth of normal" -> factor = 0.2
   - "75% of normal output" / "reduced to 75%" -> factor = 0.75
   - "25% of forecast" / "roughly 25%" -> factor = 0.25
   - "halved" / "50% drop" -> factor = 0.5

2. "minimum_battery_reserve": Keep battery energy at or above a threshold.
   Adjustment: {"hours": [int, ...], "minimum_energy_kwh": float}
   If the note says a PERCENTAGE of battery capacity, convert it:
   - "50% of battery capacity" with capacity 200 kWh = minimum_energy_kwh 100.0

3. "no_charge_window": Battery charging forbidden during specific hours.
   Adjustment: {"hours": [int, ...]}

4. "no_discharge_window": Battery discharging forbidden during specific hours.
   Adjustment: {"hours": [int, ...]}

5. "max_grid_window": Grid import capped during specific hours.
   Adjustment: {"hours": [int, ...], "max_grid_kwh": float}

6. "no_op": The note does not affect electrical scheduling.
   Examples: campus events, cafeteria changes, administrative deadlines, weather commentary without numeric constraints, visits, meetings, exams, sports.
   Adjustment: null (no hours, no parameters)

### STRICT RULES:
- Return exactly one directive per note, preserving note order: index 0, 1, ... N-1.
- Time intervals: Start hour is INCLUDED, end hour is EXCLUDED.
  - "1 PM to 3 PM" or "13:00 to 15:00" -> hours: [13, 14]
  - "noon until 2 PM" or "12 PM to 2 PM" -> hours: [12, 13]
  - "6 PM until 9 PM" -> hours: [18, 19, 20]
  - "at 2 PM" (single hour) -> hours: [14]
  - "midnight to 3 AM" -> hours: [0, 1, 2]
- Hours must be unique integers from 0 to 23, sorted in ascending order.
- Do NOT invent directives or change base campus demand, battery specs, or tariffs.
- Return ONLY valid JSON matching the schema below.

### RESPONSE SCHEMA:
{
  "directives": [
    {
      "directive_type": "<one of 6 types>",
      "hours": [int, ...] or omit for no_op,
      "factor": float (only for solar_reduction),
      "minimum_energy_kwh": float (only for minimum_battery_reserve),
      "max_grid_kwh": float (only for max_grid_window),
      "explanation": "Short reason"
    }
  ]
}

### FEW-SHOT EXAMPLES:

Example 1 (solar paraphrase + distractor):
Input Notes:
  Note 0: "PV production will drop to about 20% between 13:00 and 15:00."
  Note 1: "Dean will visit the campus library tomorrow morning."
Output:
{
  "directives": [
    {
      "directive_type": "solar_reduction",
      "hours": [13, 14],
      "factor": 0.2,
      "explanation": "Solar output drops to 20% of normal from 1 PM to 3 PM."
    },
    {
      "directive_type": "no_op",
      "explanation": "Campus visit does not affect the energy schedule."
    }
  ]
}

Example 2 (80% curtailment paraphrase + grid cap):
Input Notes:
  Note 0: "Expect an 80% curtailment in rooftop solar during the 1-3 PM maintenance window."
  Note 1: "Grid import cannot exceed 150 kWh from 7 PM to 10 PM."
Output:
{
  "directives": [
    {
      "directive_type": "solar_reduction",
      "hours": [13, 14],
      "factor": 0.2,
      "explanation": "80% curtailment leaves 20% usable solar for hours 13 and 14."
    },
    {
      "directive_type": "max_grid_window",
      "hours": [19, 20, 21],
      "max_grid_kwh": 150.0,
      "explanation": "Grid capped at 150 kWh per hour from 7 PM to 10 PM."
    }
  ]
}

Example 3 (one-fifth paraphrase):
Input Notes:
  Note 0: "Panel washing from one until three will leave roughly one-fifth of normal solar output."
Output:
{
  "directives": [
    {
      "directive_type": "solar_reduction",
      "hours": [13, 14],
      "factor": 0.2,
      "explanation": "Panel washing reduces solar to one-fifth (20%) from 1 PM to 3 PM."
    }
  ]
}

Example 4 (battery reserve + no-discharge):
Input Notes:
  Note 0: "Do not pull battery power between 18:00 and 21:00 tonight."
  Note 1: "Keep at least 50% of battery capacity in reserve from 6 PM until 9 PM."
Output:
{
  "directives": [
    {
      "directive_type": "no_discharge_window",
      "hours": [18, 19, 20],
      "explanation": "Battery discharging forbidden from 6 PM to 9 PM."
    },
    {
      "directive_type": "minimum_battery_reserve",
      "hours": [18, 19, 20],
      "minimum_energy_kwh": "<50% of battery capacity>",
      "explanation": "Battery must maintain at least 50% of capacity from 6 PM to 9 PM."
    }
  ]
}

Example 5 (no-charge window):
Input Notes:
  Note 0: "Battery charging equipment will be under maintenance from 2 AM to 5 AM."
Output:
{
  "directives": [
    {
      "directive_type": "no_charge_window",
      "hours": [2, 3, 4],
      "explanation": "Battery charging unavailable during maintenance from 2 AM to 5 AM."
    }
  ]
}
"""

def interpret_notes(notes: List[str], battery_specs: Dict[str, Any]) -> List[DirectiveInterpretationEntry]:
    """
    Calls Groq API to interpret notes, then passes them through deterministic guardrails.
    """
    if not client:
        raise Exception("GROQ_API_KEY is not set.")

    user_prompt = f"Battery Capacity: {battery_specs['capacity_kwh']} kWh\n\nNotes to interpret:\n"
    for i, note in enumerate(notes):
        user_prompt += f"Note {i}: {note}\n"

    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            model="openai/gpt-oss-120b", # Highly capable model that supports JSON mode
            response_format={"type": "json_object"},
            temperature=0.0,
            max_tokens=1024
        )
        
        content = response.choices[0].message.content
        llm_output = json.loads(content)
        extracted_directives = llm_output.get("directives", [])
    except Exception as e:
        print(f"Error calling LLM or parsing JSON: {e}")
        extracted_directives = []

    # Deterministic Guardrails & Fallback
    interpretations = []
    for i, note in enumerate(notes):
        # Fallback to no_op if LLM missed this note
        if i >= len(extracted_directives):
            interpretations.append(
                DirectiveInterpretationEntry(
                    note_index=i,
                    applies=False,
                    directive_type="no_op",
                    structured_adjustment=None,
                    explanation="Fallback due to LLM parsing error."
                )
            )
            continue
        
        d = extracted_directives[i]
        dtype = d.get("directive_type", "no_op")
        
        # Valid types
        valid_types = ["solar_reduction", "minimum_battery_reserve", "no_charge_window", "no_discharge_window", "max_grid_window", "no_op"]
        if dtype not in valid_types:
            dtype = "no_op"
            
        if dtype == "no_op":
            interpretations.append(
                DirectiveInterpretationEntry(
                    note_index=i,
                    applies=False,
                    directive_type="no_op",
                    structured_adjustment=None,
                    explanation=d.get("explanation", "Irrelevant note.")
                )
            )
        else:
            # Guardrail: clean hours
            raw_hours = d.get("hours", [])
            hours = sorted(list(set([h for h in raw_hours if isinstance(h, int) and 0 <= h <= 23])))
            
            if not hours:
                # A directive requiring hours cannot apply without valid hours
                interpretations.append(
                    DirectiveInterpretationEntry(
                        note_index=i,
                        applies=False,
                        directive_type="no_op",
                        structured_adjustment=None,
                        explanation="Guardrail: Directive contained no valid hours."
                    )
                )
                continue
            
            # Build the correct per-type adjustment object
            adjustment = None
            
            if dtype == "solar_reduction":
                factor = d.get("factor")
                if factor is not None:
                    factor = max(0.0, min(1.0, float(factor)))
                else:
                    factor = 1.0  # No reduction if factor missing
                adjustment = SolarReductionAdjustment(hours=hours, factor=factor)
                
            elif dtype == "minimum_battery_reserve":
                min_e = d.get("minimum_energy_kwh")
                if min_e is not None:
                    min_e = max(0.0, min(float(battery_specs["capacity_kwh"]), float(min_e)))
                else:
                    min_e = 0.0
                adjustment = MinBatteryReserveAdjustment(hours=hours, minimum_energy_kwh=min_e)
                
            elif dtype in ("no_charge_window", "no_discharge_window"):
                adjustment = WindowOnlyAdjustment(hours=hours)
                
            elif dtype == "max_grid_window":
                max_grid = d.get("max_grid_kwh")
                if max_grid is not None:
                    max_grid = max(0.0, float(max_grid))
                else:
                    max_grid = 0.0
                adjustment = MaxGridWindowAdjustment(hours=hours, max_grid_kwh=max_grid)
            
            interpretations.append(
                DirectiveInterpretationEntry(
                    note_index=i,
                    applies=True,
                    directive_type=dtype,
                    structured_adjustment=adjustment,
                    explanation=d.get("explanation", "Applied directive.")
                )
            )
            
    return interpretations
