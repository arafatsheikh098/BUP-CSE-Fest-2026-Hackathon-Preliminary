import pulp
from typing import List, Tuple
from schemas import (
    HourEntry, BatterySpecs, DirectiveInterpretationEntry, HourlyPlanEntry,
    SolarReductionAdjustment, MinBatteryReserveAdjustment,
    WindowOnlyAdjustment, MaxGridWindowAdjustment,
)

def optimize_schedule(
    hours_data: List[HourEntry],
    battery_specs: BatterySpecs,
    directives: List[DirectiveInterpretationEntry]
) -> Tuple[List[HourlyPlanEntry], float, float, float]:
    """
    Builds and solves the LP problem for 24-hour energy scheduling.
    Returns: (hourly_plan, total_grid_kwh, total_cost_bdt, peak_grid_kwh)
    """
    
    # 1. Apply deterministic effects to input data before modeling
    effective_solar = {h.hour: h.solar_kwh for h in hours_data}
    min_reserve = {h.hour: battery_specs.minimum_energy_kwh for h in hours_data}
    max_grid = {h.hour: None for h in hours_data}
    charge_blocked = {h.hour: False for h in hours_data}
    discharge_blocked = {h.hour: False for h in hours_data}
    
    for d in directives:
        if d.applies and d.structured_adjustment:
            adj = d.structured_adjustment
            hours = adj.hours or []
            
            if d.directive_type == "solar_reduction" and isinstance(adj, SolarReductionAdjustment):
                for h in hours:
                    if h in effective_solar:
                        effective_solar[h] *= adj.factor
                        
            elif d.directive_type == "minimum_battery_reserve" and isinstance(adj, MinBatteryReserveAdjustment):
                for h in hours:
                    if h in min_reserve:
                        min_reserve[h] = max(min_reserve[h], adj.minimum_energy_kwh)
                        
            elif d.directive_type == "max_grid_window" and isinstance(adj, MaxGridWindowAdjustment):
                for h in hours:
                    if h in max_grid:
                        # If multiple caps, take the strictest (minimum)
                        if max_grid[h] is None:
                            max_grid[h] = adj.max_grid_kwh
                        else:
                            max_grid[h] = min(max_grid[h], adj.max_grid_kwh)
                            
            elif d.directive_type == "no_charge_window":
                for h in hours:
                    if h in charge_blocked:
                        charge_blocked[h] = True
                        
            elif d.directive_type == "no_discharge_window":
                for h in hours:
                    if h in discharge_blocked:
                        discharge_blocked[h] = True

    # 2. Create LP Problem
    prob = pulp.LpProblem("Campus_Energy_Optimization", pulp.LpMinimize)
    
    # 3. Define Variables for each hour (0 to 23)
    H = range(24)
    grid_vars = pulp.LpVariable.dicts("grid", H, lowBound=0, cat='Continuous')
    solar_used_vars = pulp.LpVariable.dicts("solar_used", H, lowBound=0, cat='Continuous')
    charge_vars = pulp.LpVariable.dicts("charge", H, lowBound=0, cat='Continuous')
    discharge_vars = pulp.LpVariable.dicts("discharge", H, lowBound=0, cat='Continuous')
    energy_vars = pulp.LpVariable.dicts("energy", H, lowBound=0, cat='Continuous')
    z_vars = pulp.LpVariable.dicts("z", H, cat=pulp.LpBinary)
    
    # 4. Objective Function: minimize total cost
    prob += pulp.lpSum([grid_vars[i] * hours_data[i].tariff_bdt_per_kwh for i in H]), "Total_Cost"
    
    # 5. Constraints
    for i in H:
        # Solar usage limit
        prob += solar_used_vars[i] <= effective_solar[i], f"Solar_Cap_{i}"
        
        # Charge/Discharge limits with mutual exclusivity
        if charge_blocked[i]:
            prob += charge_vars[i] == 0.0, f"No_Charge_{i}"
        else:
            prob += charge_vars[i] <= battery_specs.max_charge_kwh_per_hour * z_vars[i], f"Max_Charge_{i}"
            
        if discharge_blocked[i]:
            prob += discharge_vars[i] == 0.0, f"No_Discharge_{i}"
        else:
            prob += discharge_vars[i] <= battery_specs.max_discharge_kwh_per_hour * (1 - z_vars[i]), f"Max_Discharge_{i}"
        
        # Grid limit
        if max_grid[i] is not None:
            prob += grid_vars[i] <= max_grid[i], f"Max_Grid_{i}"
            
        # Energy Balance
        # grid_kwh + solar_used_kwh + battery_discharge_kwh = demand_kwh + battery_charge_kwh
        prob += grid_vars[i] + solar_used_vars[i] + discharge_vars[i] == hours_data[i].demand_kwh + charge_vars[i], f"Energy_Balance_{i}"
        
        # Battery State Transition
        if i == 0:
            prob += energy_vars[i] == battery_specs.initial_energy_kwh + charge_vars[i] - discharge_vars[i], f"Battery_State_{i}"
        else:
            prob += energy_vars[i] == energy_vars[i-1] + charge_vars[i] - discharge_vars[i], f"Battery_State_{i}"
            
        # Battery Bounds
        prob += energy_vars[i] >= min_reserve[i], f"Min_Reserve_{i}"
        prob += energy_vars[i] <= battery_specs.capacity_kwh, f"Max_Capacity_{i}"
        
    # End-of-Day Battery Neutrality
    prob += energy_vars[23] == battery_specs.initial_energy_kwh, "End_of_Day_Neutrality"
    
    # 6. Solve (using system CBC via COIN_CMD or default solver if available)
    try:
        prob.solve(pulp.PULP_CBC_CMD(msg=False))
    except Exception:
        # Fallback to system CBC installed via brew
        prob.solve(pulp.COIN_CMD(path="/opt/homebrew/bin/cbc", msg=False))
        
    if prob.status != pulp.LpStatusOptimal:
        raise ValueError("Optimization problem infeasible or solver failed.")
    
    # 7. Extract Results
    hourly_plan = []
    TOLERANCE = 1e-4
    
    for i in H:
        g = round(float(grid_vars[i].varValue or 0.0), 4)
        su = round(float(solar_used_vars[i].varValue or 0.0), 4)
        c = round(float(charge_vars[i].varValue or 0.0), 4)
        d = round(float(discharge_vars[i].varValue or 0.0), 4)
        e = round(float(energy_vars[i].varValue or 0.0), 4)
            
        # Determine battery action
        action = "idle"
        bat_kwh = 0.0
        if c > TOLERANCE:
            action = "charge"
            bat_kwh = c
        elif d > TOLERANCE:
            action = "discharge"
            bat_kwh = d
            
        hourly_plan.append(
            HourlyPlanEntry(
                hour=i,
                grid_kwh=g,
                solar_used_kwh=su,
                battery_action=action,
                battery_kwh=bat_kwh,
                battery_energy_after_kwh=e
            )
        )
        
    # 8. Recalculate Top-Level Aggregates directly from hourly_plan
    total_grid = round(sum(item.grid_kwh for item in hourly_plan), 4)
    total_cost = round(sum(item.grid_kwh * hours_data[item.hour].tariff_bdt_per_kwh for item in hourly_plan), 4)
    peak_grid = round(max(item.grid_kwh for item in hourly_plan), 4)
        
    return hourly_plan, total_grid, total_cost, peak_grid
