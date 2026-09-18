import pulp
from typing import List, Tuple
from schemas import HourEntry, BatterySpecs, DirectiveInterpretationEntry, HourlyPlanEntry

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
            
            if d.directive_type == "solar_reduction" and adj.factor is not None:
                for h in hours:
                    if h in effective_solar:
                        effective_solar[h] *= adj.factor
                        
            elif d.directive_type == "minimum_battery_reserve" and adj.minimum_energy_kwh is not None:
                for h in hours:
                    if h in min_reserve:
                        min_reserve[h] = max(min_reserve[h], adj.minimum_energy_kwh)
                        
            elif d.directive_type == "max_grid_window" and adj.max_grid_kwh is not None:
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
    
    # 4. Objective Function: minimize total cost
    prob += pulp.lpSum([grid_vars[i] * hours_data[i].tariff_bdt_per_kwh for i in H]), "Total_Cost"
    
    # 5. Constraints
    for i in H:
        # Solar usage limit
        prob += solar_used_vars[i] <= effective_solar[i], f"Solar_Cap_{i}"
        
        # Charge/Discharge limits
        prob += charge_vars[i] <= (0 if charge_blocked[i] else battery_specs.max_charge_kwh_per_hour), f"Max_Charge_{i}"
        prob += discharge_vars[i] <= (0 if discharge_blocked[i] else battery_specs.max_discharge_kwh_per_hour), f"Max_Discharge_{i}"
        
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
    
    # 7. Extract Results
    hourly_plan = []
    total_grid = 0.0
    total_cost = 0.0
    peak_grid = 0.0
    
    for i in H:
        g = grid_vars[i].varValue or 0.0
        su = solar_used_vars[i].varValue or 0.0
        c = charge_vars[i].varValue or 0.0
        d = discharge_vars[i].varValue or 0.0
        e = energy_vars[i].varValue or 0.0
        
        total_grid += g
        total_cost += g * hours_data[i].tariff_bdt_per_kwh
        if g > peak_grid:
            peak_grid = g
            
        # Determine battery action
        action = "idle"
        bat_kwh = 0.0
        if c > 0.01:
            action = "charge"
            bat_kwh = c
        elif d > 0.01:
            action = "discharge"
            bat_kwh = d
            
        hourly_plan.append(
            HourlyPlanEntry(
                hour=i,
                grid_kwh=round(g, 3),
                solar_used_kwh=round(su, 3),
                battery_action=action,
                battery_kwh=round(bat_kwh, 3),
                battery_energy_after_kwh=round(e, 3)
            )
        )
        
    return hourly_plan, round(total_grid, 3), round(total_cost, 3), round(peak_grid, 3)
