import streamlit as st
import pandas as pd
import numpy as np
import math

st.set_page_config(page_title="MRP Calculator", layout="wide")
st.title("3-Level MRP Calculator")

# --- PARAMETERS ---
st.subheader("Parameters for the scented candle in glass jar")
cols = st.columns(4)

labels = ["End Product", "Glass jars (L1)", "Candle fills (L1)", "Wax (L2)"]
for col, label in zip(cols, labels):
    col.markdown(f"**{label}**")

prod_lead_time = cols[0].number_input("Lead Time", value=1, min_value=0, key="plt")
mps_onhand_start = cols[0].number_input("On Hand (start)", value=10, min_value=0, key="mps_oh")

jar_lot    = cols[1].number_input("Lot Size",   value=60,  min_value=1, key="tlot")
jar_lt     = cols[1].number_input("Lead Time",  value=2,   min_value=0, key="tlt")
jar_onhand = cols[1].number_input("On Hand",    value=20,  min_value=0, key="toh")

fill_lot    = cols[2].number_input("Lot Size",   value=100, min_value=1, key="llot")
fill_lt     = cols[2].number_input("Lead Time",  value=2,   min_value=0, key="llt")
fill_onhand = cols[2].number_input("On Hand",    value=15,  min_value=0, key="loh")

wax_lot    = cols[3].number_input("Lot Size",   value=150, min_value=1, key="plot")
wax_lt     = cols[3].number_input("Lead Time",  value=1,   min_value=0, key="plt2")
wax_onhand = cols[3].number_input("On Hand",    value=40,  min_value=0, key="poh")

# --- SCHEDULED RECEIPTS ---
st.divider()
st.subheader("Scheduled Receipts")
st.caption("Enter the week number (1–10) and quantity for any scheduled receipts. Leave quantity at 0 to skip.")

sr_cols = st.columns(4)
sr_labels = ["Glass jars", "Candle fills", "Wax"]
sr_keys   = [("jar",  10), ("fill", 10), ("wax",  10)]

def sr_input(col, name, key):
    col.markdown(f"**{name}**")
    week = col.number_input("Week",     value=1, min_value=1, max_value=10, key=f"{key}_week")
    qty  = col.number_input("Quantity", value=0, min_value=0,               key=f"{key}_qty")
    arr  = np.zeros(10, dtype=int)
    arr[int(week) - 1] = int(qty)
    return arr

jar_sr  = sr_input(sr_cols[0], "Glass jars",   "jar")
fill_sr = sr_input(sr_cols[1], "Candle fills", "fill")
wax_sr  = sr_input(sr_cols[2], "Wax",          "wax")

# --- MRP FUNCTION ---
def calculate_mrp(gross_req, sched_receipts, on_hand, lead_time, lot_size):
    n = len(gross_req)
    pab           = np.zeros(n, dtype=int)
    net_req       = np.zeros(n, dtype=int)
    plan_receipts = np.zeros(n, dtype=int)
    plan_releases = np.zeros(n, dtype=int)
    inventory = on_hand

    for i in range(n):
        nr = gross_req[i] - inventory - sched_receipts[i]
        if nr > 0:
            net_req[i] = nr
            receipt = math.ceil(nr / lot_size) * lot_size
            rel = i - lead_time
            if rel >= 0:
                plan_receipts[i] = receipt
                plan_releases[rel] += receipt
            else:
                st.warning(f"Past due order! Needed {abs(rel)} week(s) before period {i+1}.")
        inventory = inventory + sched_receipts[i] + plan_receipts[i] - gross_req[i]
        pab[i] = inventory

    df = pd.DataFrame({
        "Gross requirements":         gross_req,
        "Scheduled receipts":         sched_receipts,
        "Projected ending inventory": pab,
        "Net requirements":           net_req,
        "Planned order releases":     plan_releases,
        "Planned order receipts":     plan_receipts,
    }, index=pd.RangeIndex(1, n + 1)).T

    # Replace zeros with empty string, but keep negatives visible
    df = df.apply(lambda row: row.where(row != 0, "") if row.name != "Projected ending inventory" else row, axis=1)

    return df, plan_releases

# --- MPS ---
st.divider()
st.subheader("Master Production Schedule (MPS)")

default_mps = pd.DataFrame(
    [[0,0,0,0,60,0,80,0,0,0],
     [0,0,0,0,60,0,70,0,0,0]],
    columns=[str(i) for i in range(1, 11)],
    index=["Forecasted demand", "Production"]
)
mps = st.data_editor(default_mps, use_container_width=True)

# --- CALCULATE ---
st.divider()
if not st.button("Calculate MRP Tables", type="primary", use_container_width=True):
    st.stop()

production = mps.loc["Production"].astype(int).values

# Fix 3: MPS on-hand row
st.subheader("MPS — On Hand Inventory")
mps_onhand = np.maximum(0, mps_onhand_start - np.cumsum(production))
mps_oh_df = pd.DataFrame(
    [mps.loc["Forecasted demand"].values, production, mps_onhand],
    columns=[str(i) for i in range(1, 11)],
    index=["Forecasted demand", "Production", "On hand"]
)
st.dataframe(mps_oh_df, use_container_width=True)

# End product planned order releases
end_por = np.zeros(10, dtype=int)
for i, qty in enumerate(production):
    if qty > 0 and (i - prod_lead_time) >= 0:
        end_por[i - prod_lead_time] += qty

# --- LEVEL 1 ---
st.divider()
cols2 = st.columns(2)

cols2[0].subheader("Level 1: Glass jars")
cols2[0].caption(f"Lot {jar_lot} | Lead Time {jar_lt} | On Hand {jar_onhand}")
jar_df, jar_releases = calculate_mrp(end_por, jar_sr, jar_onhand, jar_lt, jar_lot)
cols2[0].dataframe(jar_df, use_container_width=True)

cols2[1].subheader("Level 1: Candle fills")
cols2[1].caption(f"Lot {fill_lot} | Lead Time {fill_lt} | On Hand {fill_onhand}")
fill_df, fill_releases = calculate_mrp(end_por, fill_sr, fill_onhand, fill_lt, fill_lot)
cols2[1].dataframe(fill_df, use_container_width=True)

# --- LEVEL 2 ---
st.divider()
st.subheader("Level 2: Wax")
st.caption(f"Lot {wax_lot} | Lead Time {wax_lt} | On Hand {wax_onhand}")
wax_df, _ = calculate_mrp(fill_releases, wax_sr, wax_onhand, wax_lt, wax_lot)
st.dataframe(wax_df, use_container_width=True)