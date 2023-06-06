import streamlit as st
import pandas as pd
from dotenv import load_dotenv
import os
from helpers import NetworkDevice

st.set_page_config(page_title="Net-Streamtorial",
                   layout="wide", page_icon="🔧")

# Load the environmental variables
load_dotenv()

# Check for environment variables. If not present, use Streamlit to get the inputs.
user = os.getenv("NET_TEXT_USER")
pw = os.getenv("NET_TEXT_PASS")


if not user and pw:
        with st.expander("Credentials", expanded=True):
            user = st.text_input("Username")
            pw = st.text_input("Password", type="password")

creds = {"username": user, "password": pw}

platforms = {
    "Arista EOS": "arista_eos",
    "Cisco ASA": "cisco_asa",
    "Cisco IOS": "cisco_ios",
    "Cisco NX-OS": "cisco_nxos",
    "Cisco IOS XE": "cisco_xe",
    "Cisco IOS XR": "cisco_xr",
    "Juniper Junos": "juniper_junos",
    "Autodetect": "autodetect"
}

topcol1, topcol2, topcol3 = st.columns(3)

with topcol1:
    device = st.text_input('Device Hostname')
    run = st.button("Run")

with topcol2:
    command = st.text_input('Show Command', 'show Inventory')

with topcol3:
    platform = st.selectbox('Platform', options=list(platforms.keys()), index=len(platforms) - 1)  # default to "Autodetect"

tab1, tab2, tab3 = st.tabs(["Raw Output", "Parsed Output", "Table"])

if run:

    # Create the network device object and establish the connection
    with st.spinner('Connecting to device...'):
        # Get the actual platform string from the dictionary
        platform_type = platforms[platform]

        # Create the network device object and establish the connection
        network_device = NetworkDevice(device, creds, platform_type)
        network_device.device_connection()

    # Execute the command and get the output
    with st.spinner('Executing command...'):
        raw_output, parsed_output = network_device.get_device_info(f"{device} {command}")

    with tab1:
        st.header("Raw Output")
        if raw_output is None:
            st.warning("No data to display.")
        else:
            st.code(raw_output, language="cisco", line_numbers=False)

    with tab2:
        st.header("Parsed Output")
        if parsed_output is None:
            st.warning("No data to display.")
        else:    
            st.code(parsed_output, language="json", line_numbers=False)

    with tab3:
        st.header("Table")
        try:
            df = pd.read_json(parsed_output)
            st.dataframe(df, use_container_width=True, height=1000)
        except ValueError:
            st.warning("No data to display")
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
