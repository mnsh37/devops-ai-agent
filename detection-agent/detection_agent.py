import os
import time
import requests
import json
import subprocess
from datetime import datetime, timedelta

# Import the Google GenAI library
from google import genai
from google.genai.errors import APIError

# --- CONFIGURATION ---
NODE_EXPORTER_URL = "http://localhost:9100/metrics"
LOKI_URL = "http://localhost:3100/loki/api/v1/query_range"
# CPU threshold (e.g., 75% for this POC running on a t3.small with 2 VCPUs)
CPU_THRESHOLD_PERCENT = 75 
# How long to wait between checks (seconds)
CHECK_INTERVAL_SECONDS = 10 
# The duration of logs to retrieve before the spike time (seconds)
LOG_WINDOW_SECONDS = 300 
# Time offset for Prometheus (Node Exporter) metric scraping (1 second)
METRIC_TIME_OFFSET_SECONDS = 1 
# Container name to target for remediation (our test app)
TARGET_CONTAINER_NAME = "cpu-test-app"
# Number of VCPUs on the EC2 instance (t3.small has 2)
NUM_VCPUS = 2 
REMEDIATION_HISTORY_FILE = "remediation_history.json"

# Initialize the Gemini client
try:
    client = genai.Client()
except Exception as e:
    print(f"Error initializing Gemini client: {e}")
    exit(1)

# --- CORE FUNCTIONS ---

def calculate_cpu_usage(metrics_data: str) -> float:
    """
    Calculates the total user/system CPU utilization percentage from Node Exporter data.
    This uses the 'delta' method, simulating Prometheus rate calculation over a short period.
    NOTE: For a true instantaneous rate, we would need two scraped points. 
    For this POC, we'll track 'mode=idle' time over the check interval.
    """
    
    # 1. Get current idle time (sum of all cores)
    idle_time_total = 0.0
    
    for line in metrics_data.split('\n'):
        if line.startswith('node_cpu_seconds_total') and 'mode="idle"' in line:
            # Format: node_cpu_seconds_total{cpu="0",mode="idle"} 4119.35
            try:
                # Extract the value after the last space
                value = float(line.split()[-1])
                idle_time_total += value
            except ValueError:
                continue

    # 2. Get the previous idle time (using a simple global variable for POC)
    if not hasattr(calculate_cpu_usage, 'prev_idle_time'):
        calculate_cpu_usage.prev_idle_time = idle_time_total
        calculate_cpu_usage.prev_total_time = sum(float(line.split()[-1]) for line in metrics_data.split('\n') if line.startswith('node_cpu_seconds_total') and 'mode=' in line)
        return 0.0 # Not enough data for initial calculation

    # 3. Calculate time difference
    # Total time is the sum of all mode times for all VCPUs
    current_total_time = sum(float(line.split()[-1]) for line in metrics_data.split('\n') if line.startswith('node_cpu_seconds_total') and 'mode=' in line)

    idle_delta = idle_time_total - calculate_cpu_usage.prev_idle_time
    total_delta = current_total_time - calculate_cpu_usage.prev_total_time
    
    # Safety check
    if total_delta == 0:
        return 0.0
        
    # Total CPU time used by non-idle modes
    used_cpu_delta = total_delta - idle_delta 
    
    # Total possible CPU time (Total VCPUs * time interval)
    # The 'total_delta' already represents the total possible time since it sums all modes.
    
    # CPU Usage = (Used Time / Total Possible Time) * 100
    # The total delta needs to be divided by the number of modes (8 modes per cpu * 2 cpus = 16)
    # A simpler, more robust metric is (1 - (Idle Delta / Total CPU Time))
    
    # Calculate percentage busy time relative to the total VCPU time (NUM_VCPUS * elapsed time)
    # total_delta is the sum of all mode times, so for 2 VCPUs, it's already 2x the wall clock time.
    
    # Ratio of busy time to total time available (per VCPU, then multiplied by 100)
    cpu_usage = (1 - (idle_delta / total_delta)) * NUM_VCPUS * 100 

    # 4. Update state for next check
    calculate_cpu_usage.prev_idle_time = idle_time_total
    calculate_cpu_usage.prev_total_time = current_total_time
    
    # Since we are using an approximation, limit to 100% per core.
    return min(cpu_usage, 100.0 * NUM_VCPUS)

def get_incident_logs(spike_time: datetime) -> tuple[str, str]:
    """
    Queries Loki for logs in the time window leading up to the spike.
    It checks both container logs and system logs for the incident time.
    Returns: (container_logs_str, system_logs_str)
    """
    
    # Loki uses nanoseconds since epoch for time range
    end_time_ns = int(spike_time.timestamp() * 1e9)
    start_time_ns = int((spike_time - timedelta(seconds=LOG_WINDOW_SECONDS)).timestamp() * 1e9)
    
    print(f"[{datetime.now().isoformat()}] Fetching logs from Loki: {spike_time - timedelta(seconds=LOG_WINDOW_SECONDS)} to {spike_time}")

    def query_loki(job_label: str) -> str:
        """Helper to execute the Loki query."""
        loki_query = f'{{job="{job_label}"}}'
        params = {
            'query': loki_query,
            'limit': 5000, # Limit the number of lines
            'start': start_time_ns,
            'end': end_time_ns,
            'direction': 'forward'
        }
        
        try:
            response = requests.get(LOKI_URL, params=params)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            data = response.json()
            
            log_output = []
            if data['data']['resultType'] == 'streams':
                for stream in data['data']['result']:
                    for timestamp, line in stream['values']:
                        # Convert timestamp from nanoseconds to microseconds, then seconds
                        dt = datetime.fromtimestamp(int(timestamp) / 1e9) 
                        log_output.append(f"[{dt.isoformat()}] {line.strip()}")
            
            return "\n".join(log_output)
            
        except requests.exceptions.RequestException as e:
            print(f"Error querying Loki for job '{job_label}': {e}")
            return f"Error: Could not retrieve logs from Loki for job {job_label}."
    
    container_logs = query_loki("containerlogs")
    system_logs = query_loki("varlogs")
    
    return container_logs, system_logs


def analyze_logs_with_llm(logs: str) -> str:
    """Sends the retrieved logs to the Gemini API for root cause analysis."""
    
    llm_prompt = f"""
    Analyze these application and system logs to identify the possible cause of high CPU usage. 
    The CPU spike started around the time these logs were collected. 
    Look for patterns like repeating queries, memory errors, or excessive logging.
    
    Provide your response in two parts:
    1. **REASON**: A clear, concise reason for the spike. Say 'UNCLEAR' if you cannot determine the cause.
    2. **CONFIDENCE**: A confidence score from 0 to 100 based on the evidence in the logs.
    
    Example output format:
    REASON: An infinite loop was triggered by request ID 12345.
    CONFIDENCE: 90
    
    --- START OF LOGS ---
    {logs}
    --- END OF LOGS ---
    """
    
    print(f"[{datetime.now().isoformat()}] Sending logs to Gemini for analysis...")
    
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=llm_prompt,
            # Adjust temperature for less creative, more factual analysis
            config={"temperature": 0.1} 
        )
        return response.text
    except APIError as e:
        print(f"Gemini API Error: {e}")
        return "LLM_ERROR: Could not complete analysis due to API issue."
        
        
# detection_agent.py (Add a new function)
def log_remediation_history(incident_data: dict):
    """Appends the incident and remediation details to a JSON file."""
    try:
        if not os.path.exists(REMEDIATION_HISTORY_FILE):
            history = []
        else:
            with open(REMEDIATION_HISTORY_FILE, 'r') as f:
                history = json.load(f)
        
        history.append(incident_data)
        
        with open(REMEDIATION_HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=4, default=str) # Use default=str for datetime objects
        
        print(f"[{datetime.now().isoformat()}] History logged successfully.")
    except Exception as e:
        print(f"[{datetime.now().isoformat()}] ERROR logging history: {e}")
        
        
def send_slack_notification(incident_summary: str, details: str):
    """Sends a formatted notification to the configured Slack webhook."""
    SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
    if not SLACK_WEBHOOK_URL:
        print(f"[{datetime.now().isoformat()}] WARNING: SLACK_WEBHOOK_URL not set. Skipping notification.")
        return

    # Using the 'blocks' format for a cleaner message
    payload = {
        "text": f"?? DevOps AI Agent Incident: {incident_summary}",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"?? Automated Incident Report: CPU Spike ??"
                }
            },
            {
                "type": "section",
                "fields": [
                    { "type": "mrkdwn", "text": f"*Time:* {datetime.now().isoformat()}" },
                    { "type": "mrkdwn", "text": f"*Summary:* {incident_summary}" }
                ]
            },
            {
                "type": "divider"
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Detailed Analysis & Action Taken:*"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"```{details}```"
                }
            }
        ]
    }
    
    try:
        response = requests.post(
            SLACK_WEBHOOK_URL, 
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )
        response.raise_for_status()
        print(f"[{datetime.now().isoformat()}] ? Slack notification sent successfully.")
    except requests.exceptions.RequestException as e:
        print(f"[{datetime.now().isoformat()}] ERROR sending Slack notification: {e}")
        
    

def remediate(tool_target: str, action: str, root_cause: str, remediation_confidence: int, llm_response_text: str):
    """
    Executes the remediation action (e.g., docker restart or systemctl restart),
    verifies stability, and sends a Slack notification.
    """
    print(f"[{datetime.now().isoformat()}] --- REMEDIATION ACTION: {action} on {tool_target} ---")

    # Build command
    if action == "docker restart":
        command = ["docker", "restart", tool_target]
    elif action == "systemctl restart":
        command = ["sudo", "systemctl", "restart", tool_target]
    else:
        print(f"[{datetime.now().isoformat()}] ERROR: Unknown remediation action: {action}")
        return

    try:
        # Execute the command
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"[{datetime.now().isoformat()}] Remediation successful. Output:\n{result.stdout.strip()}")

        # 4. Verify System Stability Post-Remediation
        post_remediation_cpu = verify_stability()  # Returns current CPU% after waiting

        # 5. Prepare and Send Notification
        incident_summary = (
            f"Container '{tool_target}' restarted due to CPU spike. "
            f"RCA Confidence: {remediation_confidence}%."
        )

        details_text = (
            f"Root Cause: {root_cause}\n"
            f"Action: {action}\n"
            f"Status: SUCCESS\n"
            f"Post-Remediation CPU: {post_remediation_cpu:.2f}%\n"
            f"LLM Response:\n{llm_response_text}"
        )

        send_slack_notification(incident_summary, details_text)
        
        # NEW: Log the complete history of the event
        incident_data = {
            "timestamp": datetime.now(),
            "status": "SUCCESS",
            "cpu_peak": post_remediation_cpu, # Use the lowest value post-remediation
            "root_cause": root_cause,
            "confidence": remediation_confidence,
            "action": action,
            "target": tool_target,
            "summary": incident_summary
        }
        log_remediation_history(incident_data)
        

    except subprocess.CalledProcessError as e:
        print(f"[{datetime.now().isoformat()}] REMEDIATION FAILED. Error:\n{e.stderr.strip()}")

    except FileNotFoundError:
        print(f"[{datetime.now().isoformat()}] ERROR: Command not found. Is Docker/systemctl installed?")
        
        
def verify_stability() -> float:
    """Waits and checks CPU usage again after remediation."""
    print(f"[{datetime.now().isoformat()}] Waiting {CHECK_INTERVAL_SECONDS * 2} seconds for stability check...")
    time.sleep(CHECK_INTERVAL_SECONDS * 2)

    try:
        response = requests.get(NODE_EXPORTER_URL)
        metrics_data = response.text
        current_cpu = calculate_cpu_usage(metrics_data)

        # Stability threshold = 50% of the detection threshold
        stability_threshold = CPU_THRESHOLD_PERCENT * NUM_VCPUS * 0.5

        if current_cpu < stability_threshold:
            print(f"[{datetime.now().isoformat()}] STABILITY VERIFIED: CPU usage is now {current_cpu:.2f}%, below threshold.")
        else:
            print(f"[{datetime.now().isoformat()}] STABILITY ISSUE: CPU is still high at {current_cpu:.2f}%. Manual review may be needed.")

        return current_cpu  # Important: we return the CPU value so remediation summary is correct

    except Exception as e:
        print(f"[{datetime.now().isoformat()}] Error during stability check: {e}")
        return 0.0



# --- MAIN LOOP ---

def run_detection_loop():
    """Main function to continuously monitor and act."""
    print(f"[{datetime.now().isoformat()}] Starting CPU Spike Detection Agent. Monitoring...")
    print(f"[{datetime.now().isoformat()}] Threshold: {CPU_THRESHOLD_PERCENT}% of total VCPU capacity ({NUM_VCPUS} VCPUs)")

    while True:
        spike_detected = False
        spike_time = datetime.now()

        try:
            # 1. Scrape Node Exporter Metrics
            response = requests.get(NODE_EXPORTER_URL)
            metrics_data = response.text
            current_cpu_percent = calculate_cpu_usage(metrics_data)

            print(f"[{spike_time.isoformat()}] Current Total CPU Usage: {current_cpu_percent:.2f}%")

            # 2. Spike Detection Logic
            if current_cpu_percent > CPU_THRESHOLD_PERCENT:
                spike_detected = True
                print(f"[{spike_time.isoformat()}] !!! HIGH CPU SPIKE DETECTED: {current_cpu_percent:.2f}% !!!")

                # ? NEW: Add ingestion delay before retrieving logs
                LOG_INGESTION_DELAY_SECONDS = 5
                print(f"[{spike_time.isoformat()}] Waiting {LOG_INGESTION_DELAY_SECONDS}s for Promtail/Loki ingestion...")
                time.sleep(LOG_INGESTION_DELAY_SECONDS)

                # Update spike time AFTER delay
                spike_time = datetime.now()

                # 3. Retrieve Logs
                container_logs, system_logs = get_incident_logs(spike_time)
                
                # NEW: Combine logs for LLM - much better for detection                
                logs_for_llm = (
                    "--- SYSTEM LOGS ---\n" + system_logs +
                    "\n--- CONTAINER LOGS ---\n" + container_logs
                )

                # ? NEW: Default remediation assumption (test container)
                remediation_target = TARGET_CONTAINER_NAME
                remediation_action = "docker restart"
                print(f"[{spike_time.isoformat()}] Identified Cause Source (Heuristic): CONTAINER ({remediation_target})")

                # ? NEW: Additional subtle heuristic
                if len(container_logs) < 100:
                    print(f"[{spike_time.isoformat()}] WARNING: Container logs are minimal. Analyzing full logs.")
                    # We still allow the LLM to decide root cause

                # 4. LLM Analysis
                llm_response_text = analyze_logs_with_llm(logs_for_llm)

                # 5. Parse LLM Response
                remediation_confidence = 0
                root_cause = "Not determined"

                for line in llm_response_text.split("\n"):
                    if line.startswith("REASON:"):
                        root_cause = line.split("REASON:")[1].strip()
                    elif line.startswith("CONFIDENCE:"):
                        try:
                            remediation_confidence = int(line.split("CONFIDENCE:")[1].strip())
                        except ValueError:
                            pass

                print(f"[{spike_time.isoformat()}] LLM Analysis Result:")
                print(f"  Root Cause: {root_cause}")
                print(f"  Confidence: {remediation_confidence}%")

                # 6. Auto Remediation Logic
                if remediation_action and remediation_confidence >= 80:
                    remediate(remediation_target, remediation_action, root_cause, remediation_confidence, llm_response_text)
                elif remediation_action and remediation_confidence < 80:
                    print(f"[{spike_time.isoformat()}] SKIPPING REMEDIATION: LLM confidence ({remediation_confidence}%) too low.")
                else:
                    print(f"[{spike_time.isoformat()}] SKIPPING REMEDIATION: No remediation action selected.")

            else:
                print(f"[{spike_time.isoformat()}] CPU usage nominal. Continuing...")

        except requests.exceptions.RequestException as e:
            print(f"[{spike_time.isoformat()}] ERROR: Could not scrape Node Exporter: {e}")
        except Exception as e:
            print(f"[{spike_time.isoformat()}] UNEXPECTED ERROR: {e}")

        # 7. Wait interval
        if not spike_detected:
            time.sleep(CHECK_INTERVAL_SECONDS)
        else:
            time.sleep(CHECK_INTERVAL_SECONDS * 3)


if __name__ == "__main__":
    if not os.getenv("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY environment variable not set.")
    else:
        run_detection_loop()

