#!/bin/bash
# DigitalOcean Worker - Runs health monitor

echo "🔍 Jira Duplicate Canceller Health Monitor Starting..."
echo "Environment: DigitalOcean App Platform"
echo "Monitoring App: Duplicate Canceller"
echo "Check Interval: 15 minutes"
echo "=========================================="

# Install dependencies
pip install -r requirements.txt

# Run the monitor
python monitor-duplicate-canceller.py
