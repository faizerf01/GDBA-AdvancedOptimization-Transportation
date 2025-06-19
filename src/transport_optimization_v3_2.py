
"""
Optimization Script - Version 3.2
Includes:
- Minimum total flow: 15,000 units
- Unmet demand penalty: 2x average cost for each product
"""

import pandas as pd
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpStatus

# Load dataset
file_path = "warehouse_transport_data_v3_2.xlsx"
supply_df = pd.read_excel(file_path, sheet_name="Supply")
demand_df = pd.read_excel(file_path, sheet_name="Demand")
transport_df = pd.read_excel(file_path, sheet_name="TransportMatrix")
products_df = pd.read_excel(file_path, sheet_name="Products")

products = products_df['Product'].tolist()
warehouses = list(set(supply_df['Warehouse']).union(set(demand_df['Warehouse'])))
supply_dict = {(row['Product'], row['Warehouse']): row['SupplyQty'] for _, row in supply_df.iterrows()}
demand_dict = {(row['Product'], row['Warehouse']): row['DemandQty'] for _, row in demand_df.iterrows()}

# Calculate average cost per product for unmet demand penalty
avg_costs = transport_df.groupby('Product')['Cost'].mean().to_dict()
penalty_cost = {p: 2 * avg_costs[p] for p in products}

# Build model
model = LpProblem("Transport_Optimization_v3_2", LpMinimize)

# Variables
x = {
    (row['Product'], row['From'], row['To']): LpVariable(
        f"x_{row['Product']}_{row['From']}_{row['To']}", lowBound=0
    )
    for _, row in transport_df.iterrows()
}

# Unmet demand variables
unmet = {
    (product, dst): LpVariable(f"unmet_{product}_{dst}", lowBound=0)
    for (product, dst), demand in demand_dict.items()
}

# Objective: cost + time + unmet demand penalty
alpha, beta = 0.7, 0.3
model += (
    lpSum(
        x[(row['Product'], row['From'], row['To'])] *
        (alpha * row['Cost'] + beta * row['Time'])
        for _, row in transport_df.iterrows()
    ) +
    lpSum(unmet[pd] * penalty_cost[pd[0]] for pd in unmet)
)

# Supply constraints
for (product, wh), supply in supply_dict.items():
    model += lpSum(
        x[(product, wh, dst)]
        for dst in warehouses if (product, wh, dst) in x
    ) <= supply

# Demand constraints (with unmet demand allowed)
for (product, wh), demand in demand_dict.items():
    model += (
        lpSum(
            x[(product, src, wh)]
            for src in warehouses if (product, src, wh) in x
        ) + unmet[(product, wh)] == demand
    )

# Warehouse capacity constraints (CHI, MSP, SF)
for wh in ['CHI', 'MSP', 'SF']:
    model += lpSum(
        x[(product, src, wh)]
        for product in products
        for src in warehouses
        if (product, src, wh) in x
    ) <= 5000

# Global minimum flow constraint
model += lpSum(x.values()) >= 15000, "MinimumTotalFlow"

# Solve
print("Solving model v3.2...")
model.solve()
print(f"Model status: {LpStatus[model.status]}")

# Export results
results = []
for key, var in x.items():
    if var.varValue and var.varValue > 0:
        product, src, dst = key
        match = transport_df[
            (transport_df['Product'] == product) &
            (transport_df['From'] == src) &
            (transport_df['To'] == dst)
        ]
        if not match.empty:
            results.append({
                'Product': product,
                'From': src,
                'To': dst,
                'Quantity': var.varValue,
                'Cost': match['Cost'].values[0],
                'Time': match['Time'].values[0]
            })

# Unmet demand
unmet_summary = []
for key, var in unmet.items():
    if var.varValue and var.varValue > 0:
        unmet_summary.append({
            'Product': key[0],
            'Warehouse': key[1],
            'UnmetQty': var.varValue
        })

# Save outputs
pd.DataFrame(results).to_excel("optimized_transport_plan_v3_2.xlsx", index=False)
pd.DataFrame(unmet_summary).to_excel("unmet_demand_report_v3_2.xlsx", index=False)
print("Results saved.")
