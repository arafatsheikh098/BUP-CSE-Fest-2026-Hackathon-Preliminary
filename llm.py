import os
import json
from typing import List, Dict, Any
from groq import Groq
from schemas import DirectiveInterpretationEntry, StructuredAdjustment
from dotenv import load_dotenv

load_dotenv()


# Try to get the API key from environment
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

if GROQ_API_KEY:
    client = Groq(api_key=GROQ_API_KEY)
else:
    client = None

SYSTEM_PROMPT = """
You are a campus energy operator-note interpreter for the GridWise challenge.

Given operator notes about a 24-hour campus energy schedule, classify EACH note into EXACTLY ONE of these directive types:

1. solar_reduction: Solar output reduced. Requires "hours" and "factor" (the REMAINING fraction. "80% reduction" = factor 0.2).
2. minimum_battery_reserve: Battery must stay above X kWh. Requires "hours" and "minimum_energy_kwh".
3. no_charge_window: No battery charging allowed. Requires "hours".
4. no_discharge_window: No battery discharging allowed. Requires "hours".
5. max_grid_window: Grid import capped. Requires "hours" and "max_grid_kwh".
6. no_op: Note is irrelevant to the energy schedule. Requires NO parameters.

RULES:
- You MUST return a JSON object with a single key "directives", which is a list of objects.
- The list MUST contain exactly one entry per input operator note, in the exact same order.
- Time windows: start inclusive, end EXCLUSIVE. "1 PM to 3 PM" = hours [13, 14]
- Hours are integers 0-23, sorted ascending, unique.
- "50% of battery capacity" with capacity 200 = minimum_energy_kwh 100
- For no_op, just set "directive_type": "no_op" and provide an "explanation". Do not include hours or other parameters.

Example JSON output structure:
{
  "directives": [
    {
      "directive_type": "solar_reduction",
      "hours": [12, 13],
      "factor": 0.25,
      "explanation": "Solar availability is reduced to 25% during the panel-cleaning window."
    },
    {
      "directive_type": "no_op",
      "explanation": "This note does not affect the 24-hour energy schedule."
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
            
            # Guardrail: clean factor
            factor = d.get("factor")
            if factor is not None:
                factor = max(0.0, min(1.0, float(factor)))
                
            # Guardrail: clean min energy
            min_e = d.get("minimum_energy_kwh")
            if min_e is not None:
                min_e = max(0.0, min(float(battery_specs["capacity_kwh"]), float(min_e)))
                
            # Guardrail: clean max grid
            max_grid = d.get("max_grid_kwh")
            if max_grid is not None:
                max_grid = max(0.0, float(max_grid))
                
            adjustment = StructuredAdjustment(
                hours=hours,
                factor=factor,
                minimum_energy_kwh=min_e,
                max_grid_kwh=max_grid
            )
            
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
