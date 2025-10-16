#!/usr/bin/env python3

"""
Jira Duplicate Canceller - Health Monitor
Monitors the DigitalOcean duplicate canceller and sends Slack alerts if it's down
Created: 2025-10-16
"""

import subprocess
import json
from datetime import datetime, timedelta
import time
import requests
import os

# Configuration
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID", "C05FEF0UEDC")  # #55_anthropic
DO_APP_ID = "65226ccd-2ec5-4729-951a-0003b03b3466"
CHECK_INTERVAL = 900  # 15 minutes

# Alert thresholds
ALERT_IF_NO_LOGS_FOR_MINUTES = 15
ALERT_IF_ERRORS = True

class DuplicateCancellerMonitor:
    def __init__(self):
        self.last_alert_time = None
        self.consecutive_failures = 0

    def get_recent_logs(self, lines=50):
        """Get recent logs from DigitalOcean app"""
        try:
            cmd = f"doctl apps logs {DO_APP_ID} --tail {lines}"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                return result.stdout
            else:
                print(f"❌ Error getting logs: {result.stderr}")
                return None
        except Exception as e:
            print(f"❌ Exception getting logs: {e}")
            return None

    def parse_last_check_time(self, logs):
        """Extract the timestamp of the last successful check"""
        if not logs:
            return None

        lines = logs.strip().split('\n')
        for line in reversed(lines):
            if "Check completed successfully" in line:
                # Extract timestamp from log line
                # Format: duplicate-checker 2025-10-16T18:15:56.141386911Z Thu Oct 16 18:15:56 UTC 2025: Check completed successfully
                try:
                    parts = line.split(' ')
                    # Find the ISO timestamp
                    for part in parts:
                        if 'T' in part and 'Z' in part:
                            timestamp_str = part.split('Z')[0]
                            return datetime.fromisoformat(timestamp_str)
                except Exception as e:
                    continue

        return None

    def check_for_errors(self, logs):
        """Check if there are any errors in recent logs"""
        if not logs:
            return []

        errors = []
        for line in logs.split('\n'):
            if 'ERROR' in line or 'CRITICAL' in line or 'Failed' in line:
                errors.append(line)

        return errors

    def send_slack_alert(self, title, message, severity="HIGH"):
        """Send alert to Slack"""
        emoji_map = {
            "CRITICAL": "🚨",
            "HIGH": "⚠️",
            "MEDIUM": "⚡",
            "LOW": "ℹ️"
        }

        emoji = emoji_map.get(severity, "⚠️")

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} {title}",
                    "emoji": True
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": message
                }
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"Duplicate Canceller Monitor | {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
                    }
                ]
            }
        ]

        try:
            response = requests.post(
                'https://slack.com/api/chat.postMessage',
                headers={'Authorization': f'Bearer {SLACK_BOT_TOKEN}'},
                json={
                    'channel': SLACK_CHANNEL_ID,
                    'blocks': blocks
                }
            )

            result = response.json()
            if result.get('ok'):
                print(f"✅ Slack alert sent: {title}")
                return True
            else:
                print(f"❌ Slack error: {result.get('error')}")
                return False
        except Exception as e:
            print(f"❌ Failed to send Slack alert: {e}")
            return False

    def check_health(self):
        """Check if duplicate canceller is healthy"""
        print(f"\n{'='*60}")
        print(f"🔍 Checking Duplicate Canceller Health")
        print(f"Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print(f"{'='*60}")

        # Get recent logs
        logs = self.get_recent_logs(100)

        if not logs:
            print("❌ Could not retrieve logs")
            self.consecutive_failures += 1

            if self.consecutive_failures >= 2:
                self.send_slack_alert(
                    "Duplicate Canceller - Cannot Retrieve Logs",
                    f"⚠️ Unable to retrieve logs from DigitalOcean.\n"
                    f"• Consecutive failures: {self.consecutive_failures}\n"
                    f"• App ID: `{DO_APP_ID}`\n\n"
                    f"Please check DigitalOcean console manually.",
                    severity="HIGH"
                )
            return False

        # Reset failure counter if we got logs
        self.consecutive_failures = 0

        # Check last successful run time
        last_check = self.parse_last_check_time(logs)

        if last_check:
            time_since_last_check = datetime.utcnow() - last_check
            minutes_since = time_since_last_check.total_seconds() / 60

            print(f"✅ Last successful check: {last_check.strftime('%Y-%m-%d %H:%M:%S UTC')}")
            print(f"⏱️  Time since last check: {minutes_since:.1f} minutes")

            # Alert if no check for > threshold
            if minutes_since > ALERT_IF_NO_LOGS_FOR_MINUTES:
                self.send_slack_alert(
                    "Duplicate Canceller - System Down",
                    f"🚨 Duplicate canceller has not run in {minutes_since:.0f} minutes!\n\n"
                    f"• Last successful check: {last_check.strftime('%Y-%m-%d %H:%M:%S UTC')}\n"
                    f"• Expected interval: 10 minutes\n"
                    f"• App ID: `{DO_APP_ID}`\n\n"
                    f"Action required: Check DigitalOcean app status.",
                    severity="CRITICAL"
                )
                return False
        else:
            print("⚠️  Could not find last check timestamp")
            self.send_slack_alert(
                "Duplicate Canceller - No Recent Activity",
                f"⚠️ Cannot find any successful check logs.\n\n"
                f"• App ID: `{DO_APP_ID}`\n"
                f"• This may indicate the app is not running.\n\n"
                f"Action required: Check DigitalOcean app status.",
                severity="HIGH"
            )
            return False

        # Check for errors
        if ALERT_IF_ERRORS:
            errors = self.check_for_errors(logs)
            if errors:
                error_summary = '\n'.join([f"• {e[:100]}" for e in errors[:5]])
                print(f"⚠️  Found {len(errors)} errors in logs")

                self.send_slack_alert(
                    "Duplicate Canceller - Errors Detected",
                    f"⚠️ Found {len(errors)} error(s) in recent logs:\n\n"
                    f"```\n{error_summary}\n```\n\n"
                    f"App ID: `{DO_APP_ID}`",
                    severity="MEDIUM"
                )

        print("✅ System is healthy")
        return True

def main():
    """Main monitoring loop"""
    monitor = DuplicateCancellerMonitor()

    print("🚀 Duplicate Canceller Health Monitor Started")
    print(f"Checking every {CHECK_INTERVAL / 60:.0f} minutes")
    print(f"Alert threshold: {ALERT_IF_NO_LOGS_FOR_MINUTES} minutes without activity")
    print(f"Slack channel: #55_anthropic")
    print("\nPress Ctrl+C to stop\n")

    # Send startup notification
    monitor.send_slack_alert(
        "Duplicate Canceller Monitor - Started",
        f"✅ Health monitoring is now active.\n\n"
        f"• Check interval: Every {CHECK_INTERVAL / 60:.0f} minutes\n"
        f"• Alert threshold: {ALERT_IF_NO_LOGS_FOR_MINUTES} minutes\n"
        f"• Monitoring app: `{DO_APP_ID}`",
        severity="LOW"
    )

    try:
        while True:
            monitor.check_health()

            print(f"\n💤 Sleeping for {CHECK_INTERVAL / 60:.0f} minutes...")
            print(f"Next check at: {(datetime.utcnow() + timedelta(seconds=CHECK_INTERVAL)).strftime('%Y-%m-%d %H:%M:%S UTC')}\n")

            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("\n\n🛑 Monitor stopped by user")
        monitor.send_slack_alert(
            "Duplicate Canceller Monitor - Stopped",
            "⚠️ Health monitoring has been stopped manually.",
            severity="MEDIUM"
        )

if __name__ == "__main__":
    main()
