#!/bin/bash
# DigitalOcean Worker - Runs simple Jira-based health monitor

echo "🔍 Jira Duplicate Monitor Starting..."
echo "Environment: DigitalOcean App Platform"
echo "Method: Direct Jira check"
echo "Check Interval: 15 minutes"
echo "=========================================="

# Install dependencies
pip install -r requirements.txt

# Run the simple monitor (checks Jira directly)
python simple-monitor.py
