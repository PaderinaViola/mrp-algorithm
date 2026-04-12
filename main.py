import streamlit as st
import pandas as pd
import numpy as np
import math

st.set_page_config(page_title="MRP Calculator", layout="wide")
st.title("3-Level MRP Calculator")

#params
st.subheader("Parameters for the scented candle in glass jar")
cols = st.columns(4)

labels = ["End Product", "Glass jars (L1)", "Candle fills (L1)", "Wax (L2)"]
for i, (col, label) in enumerate(zip(cols, labels)):
    col.markdown(f"**{label}**")

prod_lead_time = cols[0].number_input("Lead Time", value=1, min_value=0, key="plt")

jar_lot      = cols[1].number_input("Lot Size",    value=60,  min_value=1, key="tlot")
jar_lt       = cols[1].number_input("Lead Time",   value=2,   min_value=0, key="tlt")
jar_onhand   = cols[1].number_input("On Hand",     value=20,  min_value=0, key="toh")
jar_sr_w1    = cols[1].number_input("Scheduled Receipts", value=0, min_value=0, key="tsr")

fill_lot        = cols[2].number_input("Lot Size",       value=100, min_value=1, key="llot")
fill_lt         = cols[2].number_input("Lead Time",      value=2,   min_value=0, key="llt")
fill_onhand     = cols[2].number_input("On Hand",        value=15,  min_value=0, key="loh")
fill_sr_w1      = cols[2].number_input("Scheduled Receipts", value=0, min_value=0, key="lsr")

wax_lot    = cols[3].number_input("Lot Size",            value=150, min_value=1, key="plot")
wax_lt     = cols[3].number_input("Lead Time",           value=1,  min_value=0, key="plt2")
wax_onhand = cols[3].number_input("On Hand",             value=40, min_value=0, key="poh")
wax_sr_w1  = cols[3].number_input("Scheduled Receipts", value=0, min_value=0, key="psr")

#Mrp
def calculate_mrp(gross_req, sched_receipts, on_hand, lead_time, lot_size):
    n = len(gross_req)
    pab = np.zeros(n, dtype=int)
    net_req = np.zeros(n, dtype=int)
    plan_receipts = np.zeros(n, dtype=int)
    plan_releases = np.zeros(n, dtype=int)
    inventory = on_hand

    for i in range(n):
        nr = gross_req[i] - inventory - sched_receipts[i]
        if nr > 0:
            net_req[i] = nr
            plan_receipts[i] = math.ceil(nr / lot_size) * lot_size
        inventory = inventory + sched_receipts[i] + plan_receipts[i] - gross_req[i]
        pab[i] = inventory
        if plan_receipts[i] > 0:
            rel = i - lead_time
            if rel >= 0:
                plan_releases[rel] = plan_receipts[i]
            else:
                st.warning(f"Past due order! Needed {abs(rel)} week(s) before period {i+1}.")

    df = pd.DataFrame({
        "Gross requirements":          gross_req,
        "Scheduled receipts":          sched_receipts,
        "Projected ending inventory":  pab,
        "Net requirements":            net_req,
        "Planned order releases":      plan_releases,
        "Planned order receipts":      plan_receipts,

    }, index=pd.RangeIndex(1, n+1)).T.replace(0, "") #flip the table from horizontal to vertical

    return df, plan_releases

#MPS
st.divider()
st.subheader("Master Production Schedule (MPS)")


default_mps = pd.DataFrame(
    [[0,0,0,0,60,0,80,0,0,0], [0,0,0,0,60,0,70,0,0,0]],
    columns=[str(i) for i in range(1, 11)],
    index=["Forecasted demand", "Production"]
)
mps = st.data_editor(default_mps, use_container_width=True)

#button func
st.divider()
if not st.button("Calculate MRP Tables", type="primary", use_container_width=True):
    st.stop()

production = mps.loc["Production"].astype(int).values

#end product planned order releases
end_por = np.zeros(10, dtype=int)
for i, qty in enumerate(production):
    if qty > 0 and (i - prod_lead_time) >= 0:
        end_por[i - prod_lead_time] += qty

#level 1
cols2 = st.columns(2)

cols2[0].subheader("Level 1: Glass jars")
cols2[0].caption(f"Lot size = {jar_lot} | Lead time = {jar_lt} | On hand = {jar_onhand}")
jar_sr = np.zeros(10, dtype=int)
jar_sr[0] = jar_sr_w1
jar_df, jar_releases = calculate_mrp(end_por, np.zeros(10, dtype=int), jar_onhand, jar_lt, jar_lot)
cols2[0].dataframe(jar_df, use_container_width=True)

cols2[1].subheader("Level 1: Candle fills")
cols2[1].caption(f"Lot size = {fill_lot} | Lead time = {fill_lt} | On hand = {fill_onhand} ")
fill_sr = np.zeros(10, dtype=int)
fill_sr[0] = fill_sr_w1
fill_df, fill_releases = calculate_mrp(end_por, np.zeros(10, dtype=int), fill_onhand, fill_lt, fill_lot)
cols2[1].dataframe(fill_df, use_container_width=True)

#level 2
st.divider()
st.subheader("Level 2: Wax")
st.caption(f"Lot size = {wax_lot} | Lead time = {wax_lt} | On hand = {wax_onhand}")
wax_sr = np.zeros(10, dtype=int)
wax_sr[0] = wax_sr_w1
wax_df, _ = calculate_mrp(fill_releases, wax_sr, wax_onhand, wax_lt, wax_lot)
st.dataframe(wax_df, use_container_width=True)