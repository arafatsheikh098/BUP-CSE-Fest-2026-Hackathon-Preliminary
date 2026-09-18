import json
import time
import math
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def run_tests():
    with open('BUP_CSE_FEST_2026_Complex_Dummy_Inputs.json', 'r') as f:
        data = json.load(f)
        
    print("=== RUNNING CORNER CASES ===")
    
    execution_times = []
    
    for case in data:
        scenario_id = case['scenario_id']
        print(f"\nTesting Case {scenario_id}")
        
        # Call the endpoint and measure time
        start_time = time.time()
        response = client.post("/optimize-energy", json=case)
        end_time = time.time()
        
        exec_time = end_time - start_time
        
        if response.status_code != 200:
            print(f"  ❌ FAILED: API returned {response.status_code} in {exec_time:.2f}s")
            print(f"  {response.text}")
            execution_times.append({
                "scenario_id": scenario_id,
                "execution_time_seconds": exec_time,
                "status": "failed"
            })
            continue
            
        result = response.json()
        
        print(f"  ✅ API Processed Successfully (Status 200) in {exec_time:.2f}s")
        print(f"  Total Cost: {result['total_cost_bdt']} BDT")
        print(f"  Peak Grid: {result['peak_grid_kwh']} kWh")
        print(f"  Directives Extracted by LLM:")
        for d in result['directive_interpretation']:
            print(f"    - Note {d['note_index']} ({d['directive_type']}): applies={d['applies']}, args={d['structured_adjustment']}")
            
        execution_times.append({
            "scenario_id": scenario_id,
            "execution_time_seconds": exec_time,
            "status": "success"
        })
        
    with open('execution_times.json', 'w') as f:
        json.dump(execution_times, f, indent=2)
    print("\nSaved execution times to execution_times.json")
            
if __name__ == "__main__":
    run_tests()
