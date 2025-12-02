# DevOps AI Agent: Automated Anomaly Detection & Remediation

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)](https://www.python.org/)
[![AWS](https://img.shields.io/badge/AWS-EC2%20%7C%20VPC-orange?logo=amazonaws)](https://aws.amazon.com/)
[![AIOps](https://img.shields.io/badge/AIOps-Google%20Gemini-purple)](https://ai.google.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-red?logo=streamlit)](https://streamlit.io)

## Project Overview

**DevOps AI Agent** is a fully autonomous, closed-loop AIOps system that reduces **Mean Time To Resolution (MTTR)** from hours to seconds.

Deployed on a lightweight AWS EC2 instance, it continuously monitors infrastructure, detects anomalies (specifically CPU spikes), performs AI-powered root cause analysis using **Google Gemini**, and safely auto-remediates issues — all while providing full visibility through a real-time dashboard and Slack alerts.

## Key Features

| Feature | Description |
|---|---|
| **Real-time Anomaly Detection** | Continuously monitors CPU/memory via Prometheus Node Exporter. |
| **LLM-Powered Root Cause Analysis** | Uses Google Gemini to analyze Loki logs and return root cause + confidence score. |
| **Safe Auto-Remediation** | Automatically restarts containers/services only when confidence > 80%. |
| **Post-Remediation Verification** | Confirms system stability after taking action. |
| **Live Observability Dashboard** | Beautiful Streamlit UI with metrics, incident timeline, and action history. |
| **Slack Notifications** | Instant alerts on detection, RCA results, and remediation outcomes. |

## System Architecture

```text
┌────────────────┐       ┌──────────────────┐       ┌─────────────────┐
│   Prometheus   │ ◄──►  │  Node Exporter   │       │   Docker Apps   │
│     + Loki     │       └──────────────────┘       └─────────────────┘
└────────────────┘             ▲      ▲                        ▲
        ▲                      │      │                        │
        │                      │      │                        │
        │                ┌─────▼──────┴─────┐          ┌────────┴────────┐
        │                │    Promtail      │          │   Containers    │
        └────────────────┤   (Log Shipping) ├──────────►   (your apps)   │
                         └──────────────────┘          └─────────────────┘
                                  ▲
                                  │
                        ┌─────────▼──────────┐
                        │   DevOps AI Agent  │
                        │ (detection-agent/) │
                        └─────────┬──────────┘
                                  │
                  ┌───────────────▼────────────────┐
                  │    Google Gemini (RCA Engine)  │
                  └───────────────┬────────────────┘
                                  │
                  ┌───────────────▼────────────────┐
                  │     Auto-Remediation Actions   │
                  │  docker restart, systemctl...  │
                  └───────────────┬────────────────┘
                                  │
                 ┌────────────────┴────────────────┐
                 │         Streamlit Dashboard     │
                 │      (agent_dashboard.py)       │
                 └────────────────┬────────────────┘
                                  │
                          ┌───────▼────────┐
                          │   Slack Alerts │
                          └────────────────┘
```

## Prerequisites

Before running the agent, ensure you have the following infrastructure components running:

- **Python 3.8+**
- **Docker** (for managing containers)
- **Prometheus Node Exporter** (running on port 9100)
- **Loki** (running on port 3100)
- **Promtail** (for shipping logs to Loki)

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd devops-ai-agent
    ```

2.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

The agent requires specific environment variables to function correctly. You can set these in your shell or a `.env` file.

| Variable | Description | Required |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | Your Google Gemini API key for LLM analysis. | **Yes** |
| `SLACK_WEBHOOK_URL` | Webhook URL for sending Slack notifications. | No (Recommended) |

### Agent Configuration
Key parameters can be adjusted directly in `detection-agent/detection_agent.py`:
- `CPU_THRESHOLD_PERCENT`: CPU usage percentage to trigger an alert (default: 75).
- `CHECK_INTERVAL_SECONDS`: Frequency of checks (default: 10s).
- `TARGET_CONTAINER_NAME`: Name of the container to target for remediation (default: `cpu-test-app`).

## Usage

1.  **Start the Target Application (Optional)**:
    If you want to test the agent, build and run the included CPU spike simulation app:
    ```bash
    cd cpu-spike-app
    docker build -t cpu-test-app .
    docker run -d --name cpu-test-app -p 5000:5000 cpu-test-app
    ```

2.  **Run the Detection Agent**:
    ```bash
    export GEMINI_API_KEY="your_api_key_here"
    export SLACK_WEBHOOK_URL="your_slack_webhook_here"
    python detection-agent/detection_agent.py
    ```

3.  **Run the Dashboard**:
    ```bash
    streamlit run detection-agent/agent_dashboard.py
    ```

## Proof of Concept Demo

[![Watch the video: AI detects CPU spike → Gemini RCA → Auto-restart in under 45 seconds](https://img.youtube.com/vi/4CwItTCkkTw/maxresdefault.jpg)](https://youtu.be/4CwItTCkkTw)

*Click above to watch the full autonomous remediation flow in action*


## Project Structure

- `detection-agent/`: Contains the main agent logic (`detection_agent.py`) and dashboard code (`agent_dashboard.py`).
- `cpu-spike-app/`: A test application used to simulate high CPU load for testing the agent.
- `requirements.txt`: Python dependencies.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
