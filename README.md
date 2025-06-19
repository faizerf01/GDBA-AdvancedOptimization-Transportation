#  Transportation Optimization Project – Consolidated ReadMe

## Business Goal
Design a scalable optimization model for inter-warehouse logistics that:
- Reduces transportation costs by at least 40%
- Improves average delivery time by at least 30%
- Ensures full demand fulfillment
- Incorporates product-specific constraints such as refrigeration and warehouse capacity

---

## Dataset Overview
- 17 US-based warehouse locations across West, Southwest, East, and Midwest
- 10 food products including Salad Dressing, Mayonnaise, Margarine, Sauces, and Liquid Eggs
- Refrigerated items: Mayonnaise, Margarine, Liquid Eggs, Butter Blends

**Dataset Tabs:**
- `Warehouses`: List of codes
- `Products`: Product list and refrigeration flag
- `Supply`: Per product, up to 6 supply locations
- `Demand`: Per product, 10 demand locations
- `TransportMatrix`: Valid supply-demand paths with cost, time, refrigeration

---

##  Optimization Model (Linear Programming)

### Objective Function

Weighted sum minimization:
```
Z = Σ x[p,i,j] * (α * cost[p,i,j] + β * time[p,i,j]) + Σ unmet[p,j] * penalty[p]
```
- `x[p,i,j]`: Product units from supply `i` to demand `j`
- `unmet[p,j]`: Unfulfilled demand
- `penalty[p]`: 2 × average cost per product
- α and β define cost-time trade-off, tested from (0.3, 0.7) to (0.7, 0.3)

### Constraints
1. **Supply**: Shipments ≤ available stock
2. **Demand**: Shipments + unmet = demand
3. **Capacity**: CHI, MSP, SF ≤ 5,000 inbound units
4. **Flow Minimum**: Total movement ≥ 15,000 units
5. **Time Cap (v3.5 only)**: Max delivery time ≤ 16 hrs
6. **Non-negativity**: x, unmet ≥ 0

---

##  Optimization Versions Summary

| Version | Strategy        | α (Cost) | β (Time) | Avg. Cost | Avg. Time | Units Moved | Demand Met | Notes |
|---------|------------------|----------|----------|-----------|-----------|-------------|-------------|-------|
| v3.1    | Cost-heavy        | 0.7      | 0.3      | $174.75   | N/A       | Few         | ❌          | Sparse |
| v3.2    | Cost-weighted     | 0.7      | 0.3      | $169.69   | 19.78     | 80,000+     | ✅          | Strong savings |
| v3.3    | Speed-prioritized | 0.3      | 0.7      | $171.15   | 18.69     | 80,189      | ✅          | Better time |
| v3.4    | Balanced weights  | 0.5      | 0.5      | $169.97   | 19.41     | 80,189      | ✅          | Cost-effective |
| v3.5    | Time-capped       | 0.5      | 0.5      | $250.26   | 11.67     | 71,838      | ❌          | Great time, high cost |
| v3.6    | Soft time penalty | 0.4      | 0.6      | TBD       | TBD       | TBD         | TBD         | Balanced |

---

## Refrigerated Transport Logic
- Refrigerated transport costs 20–25% more
- Delivery time slightly faster
- Logic applies cost/time adjustments for applicable products

---

##  Execution Instructions

### Requirements:
```bash
pip install pandas pulp openpyxl xlsxwriter
```

### Run:
```bash
python transport_optimization_v3_X.py
```

Replace `v3_X` with the appropriate version (e.g., `v3_6`).

---

##  Use Cases & Next Steps
- Simulate different cost-time scenarios
- Optimize for SLA-driven cold-chain logistics
- Inform warehouse placement and prepositioning
