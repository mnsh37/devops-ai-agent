# DevOps AI Agent

## Overview

**DevOps AI Agent** is an intelligent, automated incident response tool designed to monitor system health, detect anomalies (specifically CPU spikes), analyze root causes using Large Language Models (LLM), and perform auto-remediation.

By integrating **Prometheus Node Exporter** for metrics, **Loki** for logs, and **Google Gemini** for analysis, this agent acts as a first responder to system performance issues, reducing downtime and manual intervention.

## Features

- **Real-time Monitoring**: Continuously tracks CPU usage via Node Exporter metrics.
- **Anomaly Detection**: Automatically detects CPU spikes based on configurable thresholds.
- **Intelligent Analysis**: Fetches system and container logs from Loki and uses **Google Gemini** to determine the root cause of the spike with a confidence score.
- **Auto-Remediation**: Automatically restarts the problematic Docker container if the analysis confidence is high.
- **Slack Notifications**: Sends detailed incident reports, including root cause analysis and actions taken, to a Slack channel.
- **Audit Logging**: Maintains a local history of remediation actions for review.

## Architecture

1.  **Monitor**: The agent polls Node Exporter metrics to calculate CPU usage.
2.  **Detect**: If CPU usage exceeds the defined threshold (default: 75%), a spike is flagged.
3.  **Analyze**: The agent queries Loki for logs (system and container) from the time window leading up to the spike. These logs are sent to Google Gemini to identify the root cause.
4.  **Remediate**: If the LLM identifies a cause with high confidence (>= 80%), the agent executes a remediation command (e.g., `docker restart <container>`) and verifies system stability.
5.  **Notify**: An alert is sent to Slack with the incident details.

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

The agent will start monitoring CPU usage and print logs to the console.

## Project Structure

- `detection-agent/`: Contains the main agent logic (`detection_agent.py`) and dashboard code.
- `cpu-spike-app/`: A test application used to simulate high CPU load for testing the agent.
- `requirements.txt`: Python dependencies.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
