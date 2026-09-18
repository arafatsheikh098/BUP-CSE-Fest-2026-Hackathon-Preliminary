import json
import math
import sys
import time
from fastapi.testclient import TestClient
from main import app

sys.stdout.reconfigure(encoding='utf-8')

client = TestClient(app)

def run_tests():
    with open('BUP_CSE_FEST_2026_Preli_Public_Sample_Cases.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    passed = 0
    total = len(data['cases'])
    execution_times = []
    
    with open('api_results.md', 'w', encoding='utf-8') as out_f:
        out_f.write("# GridWise API Test Results\n\n")
        out_f.write("This file contains the validation results for all 10 public sample cases.\n\n")
        
        for case in data['cases']:
            print(f"Testing Case {case['id']} - {case['label']}")
            out_f.write(f"## {case['id']} - {case['label']}\n")
            
            # Call the endpoint and measure time
            start_time = time.time()
            response = client.post("/optimize-energy", json=case['input'])
            end_time = time.time()
            
            exec_time = end_time - start_time
            
            if response.status_code != 200:
                print(f"  ❌ FAILED: API returned {response.status_code} in {exec_time:.2f}s")
                out_f.write(f"**Status:** ❌ FAILED (API returned {response.status_code}) in {exec_time:.2f}s\n\n")
                execution_times.append({
                    "scenario_id": case['id'],
                    "execution_time_seconds": exec_time,
                    "status": "failed"
                })
                continue
                
            result = response.json()
            expected = case['expected_output']
            
            # Verify Cost
            expected_cost = expected['total_cost_bdt']
            actual_cost = result['total_cost_bdt']
            
            if math.isclose(expected_cost, actual_cost, abs_tol=0.01):
                print(f"  ✅ PASSED: Cost {actual_cost} matches expected {expected_cost} in {exec_time:.2f}s")
                out_f.write(f"**Status:** ✅ PASSED in {exec_time:.2f}s\n")
                out_f.write(f"- **Expected Cost:** {expected_cost} BDT\n")
                out_f.write(f"- **Actual Cost:** {actual_cost} BDT\n")
                passed += 1
                execution_times.append({
                    "scenario_id": case['id'],
                    "execution_time_seconds": exec_time,
                    "status": "success"
                })
            else:
                print(f"  ❌ FAILED: Cost {actual_cost} != expected {expected_cost} in {exec_time:.2f}s")
                out_f.write(f"**Status:** ❌ FAILED in {exec_time:.2f}s\n")
                out_f.write(f"- **Expected Cost:** {expected_cost} BDT\n")
                out_f.write(f"- **Actual Cost:** {actual_cost} BDT\n")
                execution_times.append({
                    "scenario_id": case['id'],
                    "execution_time_seconds": exec_time,
                    "status": "failed (cost mismatch)"
                })
                
            out_f.write("\n### LLM Parsed Directives\n")
            out_f.write("```json\n")
            out_f.write(json.dumps([d for d in result['directive_interpretation']], indent=2))
            out_f.write("\n```\n\n")
            out_f.write("---\n\n")
            
        print(f"\nResult: {passed}/{total} cases passed.")
        out_f.write(f"## Final Result: {passed}/{total} cases passed.\n")

    with open('test_runner_execution_times.json', 'w') as f:
        json.dump(execution_times, f, indent=2)
    print("Saved execution times to test_runner_execution_times.json")

if __name__ == "__main__":
    run_tests()
