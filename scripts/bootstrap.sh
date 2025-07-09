# Installs Docker (for container testing/remediation)
# Installs Prometheus Node Exporter on EC2
# Installs and configures Prometheus
# Added logging and error handling to make debugging easier 
# This script sets up the environment for the DevOps AI Agent
# It installs Docker, Prometheus, and Prometheus Node Exporter on an EC2 instance
# It also logs the setup process to a file for later review

#!/bin/bash

# Exit on any error
set -e

# Log file for setup
LOG_FILE="/var/log/setup_environment.log"
echo "Starting setup at $(date)" | tee -a $LOG_FILE

# Update package list
echo "Updating package list..." | tee -a $LOG_FILE
apt-get update -y >> $LOG_FILE 2>&1

# Install Docker
echo "Installing Docker..." | tee -a $LOG_FILE
apt-get install -y docker.io >> $LOG_FILE 2>&1
systemctl start docker >> $LOG_FILE 2>&1
systemctl enable docker >> $LOG_FILE 2>&1

# Install Prometheus
echo "Installing Prometheus..." | tee -a $LOG_FILE
apt-get install -y prometheus >> $LOG_FILE 2>&1
systemctl start prometheus >> $LOG_FILE 2>&1
systemctl enable prometheus >> $LOG_FILE 2>&1

# Install Prometheus Node Exporter
echo "Installing Node Exporter..." | tee -a $LOG_FILE
apt-get install -y prometheus-node-exporter >> $LOG_FILE 2>&1
systemctl start prometheus-node-exporter >> $LOG_FILE 2>&1
systemctl enable prometheus-node-exporter >> $LOG_FILE 2>&1

# Verify installations
echo "Verifying installations..." | tee -a $LOG_FILE
docker --version >> $LOG_FILE 2>&1
prometheus --version >> $LOG_FILE 2>&1
prometheus-node-exporter --version >> $LOG_FILE 2>&1

echo "Setup completed successfully at $(date)" | tee -a $LOG_FILE