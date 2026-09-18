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

Given operator notes about a 24-hour campus energy schedule, extract ALL relevant directives from EACH note. A single note may contain multiple directives.

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
- You MUST return a JSON object with a single key "note_interpretations", which is a list of objects.
- The list MUST contain exactly one entry per input operator note, in the exact same order.
- Each entry MUST have a "directives" key, which is a list of one or more directive objects.
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
  "note_interpretations": [
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
  ]
}

### FEW-SHOT EXAMPLES:

Example 1 (solar paraphrase + distractor):
Input Notes:
  Note 0: "PV production will drop to about 20% between 13:00 and 15:00."
  Note 1: "Dean will visit the campus library tomorrow morning."
Output:
{
  "note_interpretations": [
    {
      "directives": [
        {
          "directive_type": "solar_reduction",
          "hours": [13, 14],
          "factor": 0.2,
          "explanation": "Solar output drops to 20% of normal from 1 PM to 3 PM."
        }
      ]
    },
    {
      "directives": [
        {
          "directive_type": "no_op",
          "explanation": "Campus visit does not affect the energy schedule."
        }
      ]
    }
  ]
}

Example 2 (80% curtailment paraphrase + grid cap):
Input Notes:
  Note 0: "Expect an 80% curtailment in rooftop solar during the 1-3 PM maintenance window."
  Note 1: "Grid import cannot exceed 150 kWh from 7 PM to 10 PM."
Output:
{
  "note_interpretations": [
    {
      "directives": [
        {
          "directive_type": "solar_reduction",
          "hours": [13, 14],
          "factor": 0.2,
          "explanation": "80% curtailment leaves 20% usable solar for hours 13 and 14."
        }
      ]
    },
    {
      "directives": [
        {
          "directive_type": "max_grid_window",
          "hours": [19, 20, 21],
          "max_grid_kwh": 150.0,
          "explanation": "Grid capped at 150 kWh per hour from 7 PM to 10 PM."
        }
      ]
    }
  ]
}

Example 3 (one-fifth paraphrase):
Input Notes:
  Note 0: "Panel washing from one until three will leave roughly one-fifth of normal solar output."
Output:
{
  "note_interpretations": [
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
  ]
}

Example 4 (battery reserve + no-discharge):
Input Notes:
  Note 0: "Do not pull battery power between 18:00 and 21:00 tonight."
  Note 1: "Keep at least 50% of battery capacity in reserve from 6 PM until 9 PM."
Output:
{
  "note_interpretations": [
    {
      "directives": [
        {
          "directive_type": "no_discharge_window",
          "hours": [18, 19, 20],
          "explanation": "Battery discharging forbidden from 6 PM to 9 PM."
        }
      ]
    },
    {
      "directives": [
        {
          "directive_type": "minimum_battery_reserve",
          "hours": [18, 19, 20],
          "minimum_energy_kwh": "<50% of battery capacity>",
          "explanation": "Battery must maintain at least 50% of capacity from 6 PM to 9 PM."
        }
      ]
    }
  ]
}

Example 5 (no-charge window):
Input Notes:
  Note 0: "Battery charging equipment will be under maintenance from 2 AM to 5 AM."
Output:
{
  "note_interpretations": [
    {
      "directives": [
        {
          "directive_type": "no_charge_window",
          "hours": [2, 3, 4],
          "explanation": "Battery charging unavailable during maintenance from 2 AM to 5 AM."
        }
      ]
    }
  ]
}
"""

def apply_deterministic_guardrails(
    llm_output: Dict[str, Any], 
    battery_capacity: float, 
    base_minimum_energy: float
) -> Dict[str, Any]:
    """
    Validates LLM output against strict GridWise preliminary rules.
    """
    d_type = llm_output.get("directive_type")
    
    # Valid types
    valid_types = ["solar_reduction", "minimum_battery_reserve", "no_charge_window", "no_discharge_window", "max_grid_window", "no_op"]
    if d_type not in valid_types:
        d_type = "no_op"
        llm_output["directive_type"] = "no_op"
        
    adj = llm_output.get("structured_adjustment") or {}
    
    # 1. Enforce `applies` Semantics
    if d_type == "no_op":
        llm_output["applies"] = False
        llm_output["structured_adjustment"] = None
        return llm_output
    
    llm_output["applies"] = True
    
    # 2. Sanitize Hours (Must be unique integers 0-23 in ascending order)
    raw_hours = adj.get("hours", [])
    valid_hours = sorted(list(set([h for h in raw_hours if isinstance(h, int) and 0 <= h <= 23])))
    adj["hours"] = valid_hours

    # 3. Sanitize Directive-Specific Values
    if d_type == "solar_reduction":
        # Factor must be between 0.0 and 1.0
        raw_factor = adj.get("factor", 1.0)
        try:
            adj["factor"] = max(0.0, min(1.0, float(raw_factor)))
        except (ValueError, TypeError):
            adj["factor"] = 1.0
            
    elif d_type == "minimum_battery_reserve":
        # Reserve cannot exceed capacity or be less than the base minimum
        raw_reserve = adj.get("minimum_energy_kwh", 0.0)
        try:
            adj["minimum_energy_kwh"] = max(base_minimum_energy, min(battery_capacity, float(raw_reserve)))
        except (ValueError, TypeError):
            adj["minimum_energy_kwh"] = base_minimum_energy
            
    elif d_type == "max_grid_window":
        # Grid cap must be non-negative
        raw_grid = adj.get("max_grid_kwh", 0.0)
        try:
            adj["max_grid_kwh"] = max(0.0, float(raw_grid))
        except (ValueError, TypeError):
            adj["max_grid_kwh"] = 0.0

    llm_output["structured_adjustment"] = adj
    return llm_output


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
        import time
        max_retries = 4
        for attempt in range(max_retries):
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
                break
            except Exception as e:
                if "429" in str(e) and attempt < max_retries - 1:
                    sleep_time = 5.0  # Wait 5 seconds to allow token bucket to refill safely
                    print(f"Rate limit hit, sleeping for {sleep_time} seconds before retry (Attempt {attempt+1}/{max_retries})...")
                    time.sleep(sleep_time)
                else:
                    raise e
                    
        content = response.choices[0].message.content
        llm_output = json.loads(content)
        note_interpretations = llm_output.get("note_interpretations", [])
    except Exception as e:
        print(f"Error calling LLM or parsing JSON: {e}")
        note_interpretations = []

    # Deterministic Guardrails & Fallback
    interpretations = []
    for i, note in enumerate(notes):
        # Fallback to no_op if LLM missed this note
        if i >= len(note_interpretations):
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
        
        note_obj = note_interpretations[i]
        
        extracted_directives = []
        if isinstance(note_obj, dict):
            extracted_directives = note_obj.get("directives", [])
            if not extracted_directives and "directive_type" in note_obj:
                extracted_directives = [note_obj]
        elif isinstance(note_obj, list):
            extracted_directives = note_obj
            
        if not extracted_directives:
            extracted_directives = [{"directive_type": "no_op", "explanation": "No directives extracted or invalid structure."}]
            
        for d in extracted_directives:
            # Build the shape expected by apply_deterministic_guardrails
            llm_dict_for_guardrails = {
                "directive_type": d.get("directive_type", "no_op"),
                "structured_adjustment": {
                    "hours": d.get("hours"),
                    "factor": d.get("factor"),
                    "minimum_energy_kwh": d.get("minimum_energy_kwh"),
                    "max_grid_kwh": d.get("max_grid_kwh")
                },
                "explanation": d.get("explanation", "")
            }
            
            # Apply the EXACT required guardrails logic
            sanitized = apply_deterministic_guardrails(
                llm_dict_for_guardrails, 
                float(battery_specs["capacity_kwh"]), 
                float(battery_specs["minimum_energy_kwh"])
            )
            
            dtype = sanitized["directive_type"]
            applies = sanitized["applies"]
            adj_dict = sanitized.get("structured_adjustment")
            explanation = sanitized.get("explanation", "")
            
            if not applies or adj_dict is None:
                interpretations.append(
                    DirectiveInterpretationEntry(
                        note_index=i,
                        applies=False,
                        directive_type="no_op",
                        structured_adjustment=None,
                        explanation=explanation
                    )
                )
            else:
                hours = adj_dict.get("hours", [])
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
                    
                # Build the correct per-type adjustment Pydantic object
                adjustment = None
                
                if dtype == "solar_reduction":
                    adjustment = SolarReductionAdjustment(hours=hours, factor=adj_dict["factor"])
                elif dtype == "minimum_battery_reserve":
                    adjustment = MinBatteryReserveAdjustment(hours=hours, minimum_energy_kwh=adj_dict["minimum_energy_kwh"])
                elif dtype in ("no_charge_window", "no_discharge_window"):
                    adjustment = WindowOnlyAdjustment(hours=hours)
                elif dtype == "max_grid_window":
                    adjustment = MaxGridWindowAdjustment(hours=hours, max_grid_kwh=adj_dict["max_grid_kwh"])
                    
                interpretations.append(
                    DirectiveInterpretationEntry(
                        note_index=i,
                        applies=True,
                        directive_type=dtype,
                        structured_adjustment=adjustment,
                        explanation=explanation
                    )
                )
            
    return interpretations
