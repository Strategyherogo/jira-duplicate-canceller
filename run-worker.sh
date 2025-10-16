#!/bin/bash
# DigitalOcean Worker - Runs duplicate canceller every 10 minutes

echo "🤖 Jira Duplicate Canceller Worker Starting..."
echo "Environment: DigitalOcean App Platform"
echo "Schedule: Every 10 minutes"
echo "Project: ${PROJECT_NAME:-NVSTRS}"
echo "=========================================="

# Install dependencies
pip install -r requirements.txt

# Run continuously
while true; do
    echo ""
    echo "$(date): Running duplicate check..."

    # Run the duplicate canceller
    python duplicate-canceller.py --projects ${PROJECT_NAME:-NVSTRS}

    EXIT_CODE=$?
    if [ $EXIT_CODE -eq 0 ]; then
        echo "$(date): Check completed successfully"
    else
        echo "$(date): Check failed with exit code $EXIT_CODE"
    fi

    # Sleep for 10 minutes (600 seconds)
    echo "$(date): Sleeping for 10 minutes..."
    sleep 600
done