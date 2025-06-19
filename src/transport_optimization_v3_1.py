
"""
Optimization Script - Version 3.1
Optimizes inter-warehouse transport for food products with a global minimum movement constraint (5,000 units)
"""

import pandas as pd
from pulp import LpProblem, LpMinimize, LpVariable, lpSum

# Load v3.1 dataset
file_path = "warehouse_transport_data_v3_1.xlsx"
supply_df = pd.read_excel(file_path, sheet_name="Supply")
demand_df = pd.read_excel(file_path, sheet_name="Demand")
transport_df = pd.read_excel(file_path, sheet_name="TransportMatrix")
products_df = pd.read_excel(file_path, sheet_name="Products")

products = products_df['Product'].tolist()
warehouses = list(set(supply_df['Warehouse']).union(set(demand_df['Warehouse'])))
supply_dict = {(row['Product'], row['Warehouse']): row['SupplyQty'] for _, row in supply_df.iterrows()}
demand_dict = {(row['Product'], row['Warehouse']): row['DemandQty'] for _, row in demand_df.iterrows()}

# Build model
model = LpProblem("Transport_Optimization_v3_1", LpMinimize)

x = {
    (row['Product'], row['From'], row['To']): LpVariable(
        f"x_{row['Product']}_{row['From']}_{row['To']}", lowBound=0
    )
    for _, row in transport_df.iterrows()
}

# Objective: Minimize weighted cost and time
alpha, beta = 0.7, 0.3
model += lpSum(
    x[(row['Product'], row['From'], row['To'])] *
    (alpha * row['Cost'] + beta * row['Time'])
    for _, row in transport_df.iterrows()
)

# Supply constraints
for (product, wh), supply in supply_dict.items():
    model += lpSum(
        x[(product, wh, dst)]
        for dst in warehouses
        if (product, wh, dst) in x
    ) <= supply

# Demand constraints
for (product, wh), demand in demand_dict.items():
    model += lpSum(
        x[(product, src, wh)]
        for src in warehouses
        if (product, src, wh) in x
    ) <= demand

# Space constraints on CHI, MSP, SF
for wh in ['CHI', 'MSP', 'SF']:
    model += lpSum(
        x[(product, src, wh)]
        for product in products
        for src in warehouses
        if (product, src, wh) in x
    ) <= 5000

# Enforce global minimum movement
model += lpSum(x.values()) >= 5000, "GlobalMinimumFlow"

# Solve
print("Solving transport model v3.1...")
model.solve()
print("Done.")

# Output results
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

results_df = pd.DataFrame(results)
results_df.to_excel("optimized_transport_plan_v3_1.xlsx", index=False)
print("Results saved to optimized_transport_plan_v3_1.xlsx")
