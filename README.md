# DevOps AI Agent: Automated Anomaly Detection & Remediation

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)](https://www.python.org/)
[![AWS](https://img.shields.io/badge/AWS-EC2%20%7C%20VPC-orange?logo=amazonaws)](https://aws.amazon.com/)
[![AIOps](https://img.shields.io/badge/AIOps-Google%20Gemini-purple)](https://ai.google.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Streamlit](https://img.shields.io/badge/Dashboard-Streamlit-red?logo=streamlit)](https://streamlit.io)

<p align="center">
  <img src="https://via.placeholder.com/1000x400/2563EB/ffffff?text=DevOps+AI+Agent+%E2%9A%A1+Closed--Loop+AIOps" alt="DevOps AI Agent Banner"/>
</p>

## Project Overview

**DevOps AI Agent** is a fully autonomous, closed-loop AIOps system that reduces **Mean Time To Resolution (MTTR)** from hours to seconds.

Deployed on a lightweight AWS EC2 instance, it continuously monitors infrastructure, detects anomalies, performs AI-powered root cause analysis using **Google Gemini**, and safely auto-remediates issues — all while providing full visibility through a real-time dashboard and Slack alerts.

## Key Features

| Feature                         | Description                                                                      |
|---------------------------------|----------------------------------------------------------------------------------|
| Real-time Anomaly Detection     | Continuously monitors CPU/memory via Prometheus Node Exporter                    |
| LLM-Powered Root Cause Analysis | Uses Google Gemini to analyze Loki logs and return root cause + confidence score |
| Safe Auto-Remediation           | Automatically restarts containers/services only when confidence > 80%           |
| Post-Remediation Verification   | Confirms system stability after taking action                                    |
| Live Observability Dashboard    | Beautiful Streamlit UI with metrics, incident timeline, and action history       |
| Slack Notifications             | Instant alerts on detection, RCA results, and remediation outcomes               |

## System Architecture

```text
┌────────────────┐       ┌───────────────────┐       ┌─────────────────┐
│   Prometheus   │ ◄──► │  Node Exporter    │       │   Docker Apps   │
│     + Loki     │       └───────────────────┘       └─────────────────┘
└────────────────┘             ▲      ▲                        ▲
        ▲                      │      │                        │
        │                      │      │                        │
        │                ┌─────▼──────┴─────┐          ┌────────┴────────┐
        │                │    Promtail       │          │   Containers    │
        └────────────────┤   (Log Shipping)  ├──────────►   (your apps)   │
                         └───────────────────┘          └─────────────────┘
                                  ▲
                                  │
                        ┌─────────▼──────────┐
                        │   DevOps AI Agent    │
                        │ (detection_agent.py)│
                        └─────────┬──────────┘
                                  │
                  ┌───────────────▼────────────────┐
                  │    Google Gemini (RCA Engine)   │
                  └───────────────┬────────────────┘
                                  │
                  ┌───────────────▼────────────────┐
                  │     Auto-Remediation Actions    │
                  │  docker restart, systemctl...   │
                  └───────────────┬────────────────┘
                                  │
                 ┌────────────────┴────────────────┐
                 │         Streamlit Dashboard      │
                 │          (dashboard.py)          │
                 └────────────────┬────────────────┘
                                  │
                          ┌───────▼────────┐
                          │   Slack Alerts   │
                          └────────────────┘
