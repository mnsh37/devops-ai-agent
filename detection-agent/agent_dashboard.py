import streamlit as st
import requests
import json
import time
import os
import pandas as pd

# --- CONFIGURATION ---
NODE_EXPORTER_URL = "http://localhost:9100/metrics"
REMEDIATION_HISTORY_FILE = "remediation_history.json"
TARGET_CONTAINER_NAME = "cpu-test-app"
REFRESH_RATE_SECONDS = 1  # Faster refresh for smoother chart
NUM_CORES = 2 # Set to matches your t3.small (2 vCPUs)

# Page Config (Clean, No Icons)
st.set_page_config(
    page_title="DevOps AI Agent",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- LIGHTWEIGHT STATE MANAGEMENT ---
if 'cpu_data' not in st.session_state:
    st.session_state.cpu_data = [0.0] * 60 # Store last 60 points

# --- HELPER FUNCTIONS ---

def get_cpu_percentage():
    """
    Fetches CPU usage and scales it to 0-200% (matching the Agent's logic).
    """
    try:
        response = requests.get(NODE_EXPORTER_URL, timeout=0.5)
        if response.status_code == 200:
            lines = response.text.split('\n')
            idle_secs = 0.0
            total_secs = 0.0
            
            # Fast parsing
            for line in lines:
                if line.startswith('node_cpu_seconds_total'):
                    parts = line.split()
                    val = float(parts[-1])
                    if 'mode="idle"' in line:
                        idle_secs += val
                    total_secs += val
            
            # State management for rate calculation
            if 'prev_idle' not in st.session_state:
                st.session_state.prev_idle = idle_secs
                st.session_state.prev_total = total_secs
                return 0.0
            
            delta_idle = idle_secs - st.session_state.prev_idle
            delta_total = total_secs - st.session_state.prev_total
            
            st.session_state.prev_idle = idle_secs
            st.session_state.prev_total = total_secs
            
            if delta_total == 0: return 0.0
            
            # FORMULA FIX: Multiply by NUM_CORES to match Agent's 0-200% scale
            # (1 - idle_ratio) gives average load (0-1). 
            # Multiply by 100 for %. Multiply by Cores for Aggregate.
            cpu_util = (1 - (delta_idle / delta_total)) * 100 * NUM_CORES
            
            return round(cpu_util, 2)
            
    except Exception:
        return 0.0
    return 0.0

def load_history():
    """Loads history with UTF-8 encoding."""
    if os.path.exists(REMEDIATION_HISTORY_FILE):
        try:
            with open(REMEDIATION_HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

# --- MAIN UI LAYOUT ---

# 1. Header Area
st.title("DevOps AI Agent")
st.markdown("### Live Observability System")
st.divider()

# 2. Live Metrics Row
col1, col2, col3, col4 = st.columns(4)

# Fetch Data
current_cpu = get_cpu_percentage()
history = load_history()
incident_count = len(history)
last_incident_time = history[-1]['timestamp'] if history else "No Incidents"

# Update Chart Data
st.session_state.cpu_data.append(current_cpu)
st.session_state.cpu_data.pop(0) 

# Display Metrics
with col1:
    st.metric(label="Live CPU Usage", value=f"{current_cpu}%", delta=f"{current_cpu - st.session_state.cpu_data[-2]:.2f}%" if len(st.session_state.cpu_data) > 1 else None)

with col2:
    st.metric(label="Total Incidents", value=incident_count)

with col3:
    st.metric(label="Last Incident", value=str(last_incident_time).split('.')[0]) 

with col4:
    # Status Indicator (Thresholds scaled for 200% max)
    if current_cpu > 150:
        st.error("Status: CRITICAL")
    elif current_cpu > 75:
        st.warning("Status: HIGH LOAD")
    else:
        st.success("Status: HEALTHY")

# 3. Live Chart
st.subheader("CPU Trend (Real-time)")
chart_data = pd.DataFrame(st.session_state.cpu_data, columns=["CPU Usage %"])
# Chart Color Logic: Red if over 75%
color = "#FF4B4B" if current_cpu > 75 else "#00CC96"
st.area_chart(chart_data, color=color, height=200)

# 4. Incident History
st.subheader("Incident History & RCA")

if not history:
    st.info("No incidents recorded yet. System is stable.")
else:
    for incident in reversed(history[-5:]):
        with st.expander(f"{incident.get('timestamp')} - {incident.get('status')}", expanded=True):
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(f"**Root Cause:** {incident.get('root_cause')}")
                st.markdown(f"**Summary:** {incident.get('summary')}")
            with c2:
                st.metric("Confidence", f"{incident.get('confidence')}%")
                st.caption(f"Action: {incident.get('action')}")

# Auto-Refresh
time.sleep(REFRESH_RATE_SECONDS)
st.rerun()
