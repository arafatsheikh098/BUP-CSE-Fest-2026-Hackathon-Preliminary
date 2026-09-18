from fastapi import FastAPI, HTTPException
from schemas import OptimizeEnergyRequest, OptimizeEnergyResponse
from llm import interpret_notes
from optimizer import optimize_schedule
import traceback

app = FastAPI(title="GridWise API", version="1.0.0")

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/optimize-energy", response_model=OptimizeEnergyResponse)
def optimize_energy(request: OptimizeEnergyRequest):
    try:
        # 1. LLM Interpretation & Guardrails
        interpretations = interpret_notes(
            notes=request.operator_notes,
            battery_specs=request.battery.model_dump()
        )
        
        # 2. Optimization
        try:
            hourly_plan, total_grid, total_cost, peak_grid = optimize_schedule(
                hours_data=request.hours,
                battery_specs=request.battery,
                directives=interpretations
            )
        except ValueError as ve:
            if "infeasible" in str(ve).lower():
                # Fallback: safe failure by ignoring impossible directives
                hourly_plan, total_grid, total_cost, peak_grid = optimize_schedule(
                    hours_data=request.hours,
                    battery_specs=request.battery,
                    directives=[]
                )
            else:
                raise ve
                
        # 3. Formulate Summary
        # Simple dynamic summary based on cost and directives
        active_directives = [d.directive_type for d in interpretations if d.applies]
        summary = "Base schedule applied."
        if active_directives:
            summary = f"Schedule optimized respecting: {', '.join(active_directives)}."
        
        # 4. Construct Response
        return OptimizeEnergyResponse(
            scenario_id=request.scenario_id,
            directive_interpretation=interpretations,
            hourly_plan=hourly_plan,
            total_grid_kwh=total_grid,
            total_cost_bdt=total_cost,
            peak_grid_kwh=peak_grid,
            plan_summary=summary
        )
        
    except Exception as e:
        # Return 500 but don't leak stack traces in production
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal processing error.")

if __name__ == "__main__":
    import os
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
