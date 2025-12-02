
import time
from flask import Flask, jsonify
import logging

app = Flask(__name__)

# Configure logging to go to standard out/err (which Docker and Promtail monitor)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- CONFIGURATION ---
SPIKE_ITERATIONS = 500000000  # Adjust this number to control spike duration/intensity
CONTAINER_NAME = "cpu-test-app"

@app.route('/health')
def health_check():
    """A standard low-CPU endpoint."""
    logging.info(f"[{CONTAINER_NAME}] Health check successful.")
    return jsonify(status="ok", message="Service is healthy")

@app.route('/spike')
def cpu_spike():
    """Triggers an intentional CPU spike and logs an ERROR message."""
    
    # 1. Log the ERROR message *before* the spike
    logging.error(f"[{CONTAINER_NAME}] **CRITICAL ERROR: Beginning CPU-intensive calculation.** Iterations: {SPIKE_ITERATIONS}")
    
    start_time = time.time()
    
    # 2. The CPU-intensive operation (a simple loop for calculation)
    result = 0
    for i in range(SPIKE_ITERATIONS):
        # Perform a mathematical operation to consume CPU cycles
        result += i * i % 1234567 
        
    end_time = time.time()
    duration = end_time - start_time
    
    # 3. Log the INFO message *after* the spike
    logging.info(f"[{CONTAINER_NAME}] CPU calculation finished. Duration: {duration:.2f}s")
    
    return jsonify(
        status="completed", 
        message=f"CPU spike triggered and finished in {duration:.2f} seconds. Result: {result % 100}"
    )

if __name__ == '__main__':
    # Run using the Flask development server (fine for this controlled test)
    app.run(host='0.0.0.0', port=5000)
