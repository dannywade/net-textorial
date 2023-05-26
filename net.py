import streamlit as st
import helpers
import show_commands
import pandas as pd


st.set_page_config(page_title="Net-Streamtorial",
                   layout="wide", page_icon="🔧",)

topcol1, topcol2 = st.columns(2)

with topcol1:
    device = st.text_input('Device Hostname')
    run = st.button("Run")

with topcol2:
    # command = st.selectbox('Show Command', options=show_commands.SHOW_COMMANDS) # Use with show_commands.py if wanting to limit options
    command = st.text_input('Show Command', 'show Inventory')

tab1, tab2, tab3 = st.tabs(["Raw Output", "Parsed Output", "Table"])

if run:
    raw_output, parsed_output = helpers.get_device_info(f"{device} {command}")

    with tab1:
        st.header("Raw Output")
        st.code(raw_output, language="cisco", line_numbers=False)

    with tab2:
        st.header("Parsed Output")
        st.code(parsed_output, language="json", line_numbers=False)

    with tab3:
        df = pd.read_json(parsed_output)
        st.header("Table")
        if parsed_output:
            st.dataframe(df, use_container_width=True, height=1000)
else:
    with tab1:
        st.header("Raw Output")
        st.code("", language="cisco", line_numbers=False)

    with tab2:
        st.header("Parsed Output")
        st.code("", language="json", line_numbers=False)

    with tab3:
        st.header("Table")
        st.dataframe(data=None, use_container_width=True)
