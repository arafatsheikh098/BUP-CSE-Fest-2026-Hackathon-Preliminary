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
      "factor": 0.25
    },
    "explanation": "Solar output reduced to 25% of forecast during panel washing from noon to 2\u202fPM."
  },
  {
    "note_index": 1,
    "applies": false,
    "directive_type": "no_op",
    "structured_adjustment": null,
    "explanation": "Registration deadline change does not affect energy scheduling."
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
      ]
    },
    "explanation": "Battery charging unavailable from 2 AM to 5 AM due to maintenance."
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
      "minimum_energy_kwh": 100.0
    },
    "explanation": "Battery must maintain at least 50% (100\u202fkWh) of its 200\u202fkWh capacity from 6\u202fPM to 9\u202fPM for emergency operations."
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
      ]
    },
    "explanation": "Battery discharging prohibited from 6\u202fPM to 8\u202fPM for protection testing."
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
      "max_grid_kwh": 155.0
    },
    "explanation": "Grid import capped at 155\u202fkWh per hour from 6\u202fPM to 9\u202fPM."
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
      "factor": 0.5
    },
    "explanation": "Solar output reduced to 50% from 10 AM to noon."
  },
  {
    "note_index": 1,
    "applies": true,
    "directive_type": "no_charge_window",
    "structured_adjustment": {
      "hours": [
        14,
        15
      ]
    },
    "explanation": "Charging unavailable from 2 PM to 4 PM."
  },
  {
    "note_index": 2,
    "applies": false,
    "directive_type": "no_op",
    "structured_adjustment": null,
    "explanation": "Library hour change does not affect energy scheduling."
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
      "minimum_energy_kwh": 90.0
    },
    "explanation": "Maintain at least 90\u202fkWh in the battery from 6\u202fPM to 10\u202fPM for emergency services."
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
      "max_grid_kwh": 180.0
    },
    "explanation": "Limit grid import to 180\u202fkWh per hour from 7\u202fPM to 9\u202fPM due to transformer capacity."
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
      ]
    },
    "explanation": "Battery charging disabled from 11 AM to 1 PM for maintenance."
  },
  {
    "note_index": 1,
    "applies": true,
    "directive_type": "no_discharge_window",
    "structured_adjustment": {
      "hours": [
        17,
        18
      ]
    },
    "explanation": "Battery discharging prohibited from 5 PM to 7 PM during testing."
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
      "factor": 0.2
    },
    "explanation": "Solar output reduced by 80%, leaving 20% usable from 11 AM to 2 PM."
  },
  {
    "note_index": 1,
    "applies": false,
    "directive_type": "no_op",
    "structured_adjustment": null,
    "explanation": "Student affairs club notices do not affect the energy schedule."
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
      "minimum_energy_kwh": 80.0
    },
    "explanation": "Battery must retain at least 80 kWh from 6\u202fPM to 10\u202fPM."
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
      "max_grid_kwh": 190.0
    },
    "explanation": "Grid import limited to 190\u202fkWh per hour from 7\u202fPM to 10\u202fPM."
  },
  {
    "note_index": 2,
    "applies": false,
    "directive_type": "no_op",
    "structured_adjustment": null,
    "explanation": "Seminar room booking does not affect energy schedule."
  }
]
```

---

## Final Result: 10/10 cases passed.
