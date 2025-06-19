
"""
Optimization Script - Version 3.5
Objective: Enforce maximum delivery time of 16 hours
Weights: Cost α = 0.5, Time β = 0.5
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

# Penalty cost per product (2x average cost)
avg_costs = transport_df.groupby('Product')['Cost'].mean().to_dict()
penalty_cost = {p: 2 * avg_costs[p] for p in products}

# Build model
model = LpProblem("Transport_Optimization_v3_5_TimeCap", LpMinimize)

# Variables only for routes with time <= 16
x = {}
for _, row in transport_df.iterrows():
    if row['Time'] <= 16:
        x[(row['Product'], row['From'], row['To'])] = LpVariable(
            f"x_{row['Product']}_{row['From']}_{row['To']}", lowBound=0
        )

unmet = {
    (product, dst): LpVariable(f"unmet_{product}_{dst}", lowBound=0)
    for (product, dst), demand in demand_dict.items()
}

# Objective: balance cost and time equally
alpha, beta = 0.5, 0.5
model += (
    lpSum(
        x[key] * (alpha * row['Cost'] + beta * row['Time'])
        for key in x
        for _, row in transport_df[
            (transport_df['Product'] == key[0]) &
            (transport_df['From'] == key[1]) &
            (transport_df['To'] == key[2])
        ].iterrows()
    ) +
    lpSum(unmet[pd] * penalty_cost[pd[0]] for pd in unmet)
)

# Constraints
for (product, wh), supply in supply_dict.items():
    model += lpSum(
        x[(product, wh, dst)]
        for dst in warehouses if (product, wh, dst) in x
    ) <= supply

for (product, wh), demand in demand_dict.items():
    model += (
        lpSum(
            x[(product, src, wh)]
            for src in warehouses if (product, src, wh) in x
        ) + unmet[(product, wh)] == demand
    )

for wh in ['CHI', 'MSP', 'SF']:
    model += lpSum(
        x[(product, src, wh)]
        for product in products
        for src in warehouses
        if (product, src, wh) in x
    ) <= 5000

model += lpSum(x.values()) >= 15000, "MinimumTotalFlow"

# Solve
print("Solving model v3.5 with time cap...")
model.solve()
print(f"Model status: {LpStatus[model.status]}")

# Output
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

unmet_summary = []
for key, var in unmet.items():
    if var.varValue and var.varValue > 0:
        unmet_summary.append({
            'Product': key[0],
            'Warehouse': key[1],
            'UnmetQty': var.varValue
        })

pd.DataFrame(results).to_excel("optimized_transport_plan_v3_5.xlsx", index=False)
pd.DataFrame(unmet_summary).to_excel("unmet_demand_report_v3_5.xlsx", index=False)
print("Results saved.")
