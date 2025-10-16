#!/bin/bash
# Wrapper script to send daily Jira duplicate report via email

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load environment variables
if [ -f .env.email ]; then
    export $(cat .env.email | grep -v '^#' | xargs)
fi

# Run the email report script
python3 send-daily-report.py