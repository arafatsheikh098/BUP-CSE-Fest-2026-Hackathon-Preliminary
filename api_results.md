# GridWise API Test Results

This file contains the validation results for all 10 public sample cases.

## SAMPLE-01 - Solar cleaning + distractor
**Status:** ✅ PASSED
- **Expected Cost:** 38365 BDT
- **Actual Cost:** 38365.0 BDT

### LLM Parsed Directives
```json
[
  {
    "note_index": 0,
    "applies": true,
    "directive_type": "solar_reduction",
    "structured_adjustment": {
      "hours": [
        12,
        13
      ],
      "factor": 0.25,
      "minimum_energy_kwh": null,
      "max_grid_kwh": null
    },
    "explanation": "Solar output is reduced to 25% during rooftop panel cleaning from 12:00 to 14:00."
  },
  {
    "note_index": 1,
    "applies": false,
    "directive_type": "no_op",
    "structured_adjustment": null,
    "explanation": "The note about the sports office registration deadline does not affect the 24-hour energy schedule."
  }
]
```

---

## SAMPLE-02 - Battery charging maintenance
**Status:** ✅ PASSED
- **Expected Cost:** 42885 BDT
- **Actual Cost:** 42885.0 BDT

### LLM Parsed Directives
```json
[
  {
    "note_index": 0,
    "applies": true,
    "directive_type": "no_charge_window",
    "structured_adjustment": {
      "hours": [
        2,
        3,
        4
      ],
      "factor": null,
      "minimum_energy_kwh": null,
      "max_grid_kwh": null
    },
    "explanation": "Battery charging is prohibited from 2\u202fAM (hour\u202f2) up to but not including 5\u202fAM (hour\u202f5) due to charger isolation for maintenance."
  }
]
```

---

## SAMPLE-03 - Emergency reserve as percentage
**Status:** ✅ PASSED
- **Expected Cost:** 35480 BDT
- **Actual Cost:** 35480.0 BDT

### LLM Parsed Directives
```json
[
  {
    "note_index": 0,
    "applies": true,
    "directive_type": "minimum_battery_reserve",
    "structured_adjustment": {
      "hours": [
        18,
        19,
        20
      ],
      "factor": null,
      "minimum_energy_kwh": 100.0,
      "max_grid_kwh": null
    },
    "explanation": "Maintain at least 50% (100\u202fkWh) of the 200\u202fkWh battery capacity from 6\u202fPM to 9\u202fPM for emergency operations."
  }
]
```

---

## SAMPLE-04 - No-discharge protection test
**Status:** ✅ PASSED
- **Expected Cost:** 40495 BDT
- **Actual Cost:** 40495.0 BDT

### LLM Parsed Directives
```json
[
  {
    "note_index": 0,
    "applies": true,
    "directive_type": "no_discharge_window",
    "structured_adjustment": {
      "hours": [
        18,
        19
      ],
      "factor": null,
      "minimum_energy_kwh": null,
      "max_grid_kwh": null
    },
    "explanation": "Battery discharge is prohibited during the protection testing window from 6\u202fPM to 8\u202fPM."
  }
]
```

---

## SAMPLE-05 - Temporary feeder grid cap
**Status:** ✅ PASSED
- **Expected Cost:** 33950 BDT
- **Actual Cost:** 33950.0 BDT

### LLM Parsed Directives
```json
[
  {
    "note_index": 0,
    "applies": true,
    "directive_type": "max_grid_window",
    "structured_adjustment": {
      "hours": [
        18,
        19,
        20
      ],
      "factor": null,
      "minimum_energy_kwh": null,
      "max_grid_kwh": 155.0
    },
    "explanation": "Grid import is limited to 155\u202fkWh per hour from 6\u202fPM to 9\u202fPM due to a temporary feeder constraint."
  }
]
```

---

## SAMPLE-06 - Multiple notes with distractor
**Status:** ✅ PASSED
- **Expected Cost:** 34090 BDT
- **Actual Cost:** 34090.0 BDT

### LLM Parsed Directives
```json
[
  {
    "note_index": 0,
    "applies": true,
    "directive_type": "solar_reduction",
    "structured_adjustment": {
      "hours": [
        10,
        11
      ],
      "factor": 0.5,
      "minimum_energy_kwh": null,
      "max_grid_kwh": null
    },
    "explanation": "Cloud cover reduces solar output to 50% of forecast from 10 AM to noon."
  },
  {
    "note_index": 1,
    "applies": true,
    "directive_type": "no_charge_window",
    "structured_adjustment": {
      "hours": [
        14,
        15
      ],
      "factor": null,
      "minimum_energy_kwh": null,
      "max_grid_kwh": null
    },
    "explanation": "Charging circuit unavailable from 2 PM until 4 PM."
  },
  {
    "note_index": 2,
    "applies": false,
    "directive_type": "no_op",
    "structured_adjustment": null,
    "explanation": "Library book-return hour extension does not affect the energy schedule."
  }
]
```

---

## SAMPLE-07 - Reserve plus transformer cap
**Status:** ✅ PASSED
- **Expected Cost:** 38550 BDT
- **Actual Cost:** 38550.0 BDT

### LLM Parsed Directives
```json
[
  {
    "note_index": 0,
    "applies": true,
    "directive_type": "minimum_battery_reserve",
    "structured_adjustment": {
      "hours": [
        18,
        19,
        20,
        21
      ],
      "factor": null,
      "minimum_energy_kwh": 90.0,
      "max_grid_kwh": null
    },
    "explanation": "Maintain at least 90\u202fkWh in the battery between 6\u202fPM and 10\u202fPM."
  },
  {
    "note_index": 1,
    "applies": true,
    "directive_type": "max_grid_window",
    "structured_adjustment": {
      "hours": [
        19,
        20
      ],
      "factor": null,
      "minimum_energy_kwh": null,
      "max_grid_kwh": 180.0
    },
    "explanation": "Limit grid import to 180\u202fkWh from 7\u202fPM to 9\u202fPM."
  }
]
```

---

## SAMPLE-08 - Separate charge/discharge outages
**Status:** ✅ PASSED
- **Expected Cost:** 37665 BDT
- **Actual Cost:** 37665.0 BDT

### LLM Parsed Directives
```json
[
  {
    "note_index": 0,
    "applies": true,
    "directive_type": "no_charge_window",
    "structured_adjustment": {
      "hours": [
        11,
        12
      ],
      "factor": null,
      "minimum_energy_kwh": null,
      "max_grid_kwh": null
    },
    "explanation": "Charging is disabled while technicians inspect the charger."
  },
  {
    "note_index": 1,
    "applies": true,
    "directive_type": "no_discharge_window",
    "structured_adjustment": {
      "hours": [
        17,
        18
      ],
      "factor": null,
      "minimum_energy_kwh": null,
      "max_grid_kwh": null
    },
    "explanation": "Discharging is prohibited during relay testing."
  }
]
```

---

## SAMPLE-09 - Reduction wording normalization
**Status:** ✅ PASSED
- **Expected Cost:** 34873 BDT
- **Actual Cost:** 34873.0 BDT

### LLM Parsed Directives
```json
[
  {
    "note_index": 0,
    "applies": true,
    "directive_type": "solar_reduction",
    "structured_adjustment": {
      "hours": [
        11,
        12,
        13
      ],
      "factor": 0.2,
      "minimum_energy_kwh": null,
      "max_grid_kwh": null
    },
    "explanation": "Rooftop solar output is reduced by 80% during inverter work from 11\u202fAM to 2\u202fPM."
  },
  {
    "note_index": 1,
    "applies": false,
    "directive_type": "no_op",
    "structured_adjustment": null,
    "explanation": "The note about club notices does not affect the 24\u2011hour energy schedule."
  }
]
```

---

## SAMPLE-10 - Multi-constraint evening operation
**Status:** ✅ PASSED
- **Expected Cost:** 41620 BDT
- **Actual Cost:** 41620.0 BDT

### LLM Parsed Directives
```json
[
  {
    "note_index": 0,
    "applies": true,
    "directive_type": "minimum_battery_reserve",
    "structured_adjustment": {
      "hours": [
        18,
        19,
        20,
        21
      ],
      "factor": null,
      "minimum_energy_kwh": 80.0,
      "max_grid_kwh": null
    },
    "explanation": "Applied directive."
  },
  {
    "note_index": 1,
    "applies": true,
    "directive_type": "max_grid_window",
    "structured_adjustment": {
      "hours": [
        19,
        20,
        21
      ],
      "factor": null,
      "minimum_energy_kwh": null,
      "max_grid_kwh": 190.0
    },
    "explanation": "Applied directive."
  },
  {
    "note_index": 2,
    "applies": false,
    "directive_type": "no_op",
    "structured_adjustment": null,
    "explanation": "The note does not affect the 24-hour energy schedule."
  }
]
```

---

## Final Result: 10/10 cases passed.
