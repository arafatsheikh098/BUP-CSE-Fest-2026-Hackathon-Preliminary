import json
import math
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def run_tests():
    with open('BUP_CSE_FEST_2026_Complex_Dummy_Inputs.json', 'r') as f:
        data = json.load(f)
        
    print("=== RUNNING CORNER CASES ===")
    
    for case in data:
        print(f"\nTesting Case {case['scenario_id']}")
        
        # Call the endpoint
        response = client.post("/optimize-energy", json=case)
        
        if response.status_code != 200:
            print(f"  ❌ FAILED: API returned {response.status_code}")
            print(f"  {response.text}")
            continue
            
        result = response.json()
        
        print("  ✅ API Processed Successfully (Status 200)")
        print(f"  Total Cost: {result['total_cost_bdt']} BDT")
        print(f"  Peak Grid: {result['peak_grid_kwh']} kWh")
        print(f"  Directives Extracted by LLM:")
        for d in result['directive_interpretation']:
            print(f"    - Note {d['note_index']} ({d['directive_type']}): applies={d['applies']}, args={d['structured_adjustment']}")
            
if __name__ == "__main__":
    run_tests()
