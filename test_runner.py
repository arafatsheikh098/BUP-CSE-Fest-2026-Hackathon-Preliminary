import json
import math
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def run_tests():
    with open('BUP_CSE_FEST_2026_Preli_Public_Sample_Cases.json', 'r') as f:
        data = json.load(f)
        
        
    passed = 0
    total = len(data['cases'])
    
    with open('api_results.md', 'w') as out_f:
        out_f.write("# GridWise API Test Results\n\n")
        out_f.write("This file contains the validation results for all 10 public sample cases.\n\n")
        
        for case in data['cases']:
            print(f"Testing Case {case['id']} - {case['label']}")
            out_f.write(f"## {case['id']} - {case['label']}\n")
            
            # Call the endpoint
            response = client.post("/optimize-energy", json=case['input'])
            
            if response.status_code != 200:
                print(f"  ❌ FAILED: API returned {response.status_code}")
                out_f.write(f"**Status:** ❌ FAILED (API returned {response.status_code})\n\n")
                continue
                
            result = response.json()
            expected = case['expected_output']
            
            # Verify Cost
            expected_cost = expected['total_cost_bdt']
            actual_cost = result['total_cost_bdt']
            
            if math.isclose(expected_cost, actual_cost, abs_tol=0.01):
                print(f"  ✅ PASSED: Cost {actual_cost} matches expected {expected_cost}")
                out_f.write(f"**Status:** ✅ PASSED\n")
                out_f.write(f"- **Expected Cost:** {expected_cost} BDT\n")
                out_f.write(f"- **Actual Cost:** {actual_cost} BDT\n")
                passed += 1
            else:
                print(f"  ❌ FAILED: Cost {actual_cost} != expected {expected_cost}")
                out_f.write(f"**Status:** ❌ FAILED\n")
                out_f.write(f"- **Expected Cost:** {expected_cost} BDT\n")
                out_f.write(f"- **Actual Cost:** {actual_cost} BDT\n")
                
            out_f.write("\n### LLM Parsed Directives\n")
            out_f.write("```json\n")
            out_f.write(json.dumps([d for d in result['directive_interpretation']], indent=2))
            out_f.write("\n```\n\n")
            out_f.write("---\n\n")
            
        print(f"\nResult: {passed}/{total} cases passed.")
        out_f.write(f"## Final Result: {passed}/{total} cases passed.\n")


if __name__ == "__main__":
    run_tests()
