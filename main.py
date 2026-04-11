import streamlit as st
import pandas as pd
import numpy as np

st.title("MRP algorithm")


if "input_df" not in st.session_state:
    st.session_state.input_df = pd.DataFrame([
        {"week": "Forecasted demand", "1":0, "2":5, "3":6, "4":6, "5":0, "6":6, "7":0, "8":6, "9":6, "10":6},
        {"week": "Production", "1":0, "2":5, "3":6, "4":6, "5":0, "6":6, "7":0, "8":6, "9":6, "10":6},
        {"week": "Projected on hand", "1":0, "2":5, "3":6, "4":6, "5":0, "6":6, "7":0, "8":6, "9":6, "10":6},
        {"week": "Lead time = 1, On hand = 2 ", "1":0, "2":0, "3":0, "4":0, "5":0, "6":0, "7":0, "8":0, "9":0, "10":0 },
    ])

if "output_df" not in st.session_state:
    st.session_state.output_df = pd.DataFrame(
        np.zeros((3, 3)), 
        columns=["Result A", "Result B", "Result C"]
    )


st.subheader("Enter the values in MPS(sample data is provided)")
edited_input = st.data_editor(st.session_state.input_df, key="input_editor")


if st.button("Count"):
    new_output = st.session_state.output_df.copy()
    
    #  Row 1, Column 1 of the second table = Row 2, Column 1 of the first table * 10

    
    try:
        val_to_multiply = edited_input.iloc[1, 0] # Row 2, Col 1
        new_output.iloc[0, 0] = val_to_multiply * 10
        
        # other connections
        new_output.iloc[1, 1] = edited_input.iloc[0, 2] * 5 # R2C2 = R1C3 * 5
        
        st.session_state.output_df = new_output
        st.success("sucess")
    except IndexError:
        st.error("error")

#result
st.subheader("MRS candle wax")
st.dataframe(st.session_state.output_df)

