#!/usr/bin/env python3

"""
Jira Duplicate Canceller - Simple Health Monitor
Checks Jira directly for uncancelled duplicates
If duplicates exist for >20 minutes, sends Slack alert
Created: 2025-10-16
"""

import requests
import base64
from datetime import datetime, timedelta
import time
import os

# Configuration
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID", "C05FEF0UEDC")

JIRA_SITE = os.getenv("JIRA_SITE", "thealternative")
JIRA_URL = f"https://{JIRA_SITE}.atlassian.net"
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "egoncharov@thealternative.co")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")

CHECK_INTERVAL = 900  # 15 minutes
DUPLICATE_AGE_THRESHOLD = 20  # Alert if duplicates older than 20 minutes

# Create Jira auth header
auth_string = f"{JIRA_EMAIL}:{JIRA_API_TOKEN}"
auth_bytes = auth_string.encode('ascii')
auth_b64 = base64.b64encode(auth_bytes).decode('ascii')

jira_headers = {
    "Authorization": f"Basic {auth_b64}",
    "Accept": "application/json"
}

def send_slack_alert(title, message, severity="HIGH"):
    """Send alert to Slack"""
    emoji_map = {"CRITICAL": "🚨", "HIGH": "⚠️", "MEDIUM": "⚡", "LOW": "ℹ️"}
    emoji = emoji_map.get(severity, "⚠️")

    blocks = [
        {"type": "header", "text": {"type": "plain_text", "text": f"{emoji} {title}", "emoji": True}},
        {"type": "section", "text": {"type": "mrkdwn", "text": message}},
        {"type": "context", "elements": [{"type": "mrkdwn", "text": f"Duplicate Monitor | {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"}]}
    ]

    try:
        response = requests.post(
            'https://slack.com/api/chat.postMessage',
            headers={'Authorization': f'Bearer {SLACK_BOT_TOKEN}'},
            json={'channel': SLACK_CHANNEL_ID, 'blocks': blocks}
        )
        return response.json().get('ok', False)
    except Exception as e:
        print(f"❌ Slack error: {e}")
        return False

def check_for_old_duplicates():
    """Check Jira for duplicates that should have been cancelled"""
    print(f"\n{'='*60}")
    print(f"🔍 Checking for Uncancelled Duplicates")
    print(f"Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"{'='*60}")

    # Get recent issues from NVSTRS
    jql = f"project = NVSTRS AND created >= -1d AND status != Cancelled ORDER BY created DESC"
    url = f"{JIRA_URL}/rest/api/3/search/jql"
    params = {"jql": jql, "maxResults": 100, "fields": "summary,created,status,reporter"}

    try:
        response = requests.get(url, headers=jira_headers, params=params, timeout=30)

        if response.status_code != 200:
            print(f"❌ Jira API error: {response.status_code}")
            send_slack_alert(
                "Duplicate Monitor - Jira API Error",
                f"⚠️ Cannot access Jira API: {response.status_code}",
                severity="HIGH"
            )
            return False

        issues = response.json().get("issues", [])
        print(f"✅ Found {len(issues)} recent issues")

        # Group by summary + reporter to find potential duplicates
        groups = {}
        for issue in issues:
            fields = issue["fields"]
            key = f"{fields['summary']}|{fields.get('reporter', {}).get('displayName', 'Unknown')}"

            if key not in groups:
                groups[key] = []

            created = datetime.fromisoformat(fields["created"].replace('Z', '+00:00'))
            groups[key].append({
                "key": issue["key"],
                "created": created,
                "status": fields["status"]["name"]
            })

        # Find groups with multiple issues (potential duplicates)
        old_duplicates = []
        for key, group_issues in groups.items():
            if len(group_issues) > 1:
                # Check if any are old and not cancelled
                for issue_info in group_issues:
                    age_minutes = (datetime.now(issue_info["created"].tzinfo) - issue_info["created"]).total_seconds() / 60

                    if age_minutes > DUPLICATE_AGE_THRESHOLD and issue_info["status"] != "Cancelled":
                        old_duplicates.append({
                            "key": issue_info["key"],
                            "age": age_minutes,
                            "status": issue_info["status"]
                        })

        if old_duplicates:
            print(f"⚠️  Found {len(old_duplicates)} old uncancelled duplicates!")

            duplicate_list = '\n'.join([f"• [{d['key']}](https://thealternative.atlassian.net/browse/{d['key']}) - {d['age']:.0f} min old" for d in old_duplicates[:5]])

            send_slack_alert(
                "Duplicate Canceller - System May Be Down",
                f"🚨 Found {len(old_duplicates)} uncancelled duplicates older than {DUPLICATE_AGE_THRESHOLD} minutes!\n\n"
                f"{duplicate_list}\n\n"
                f"The duplicate canceller may not be running correctly.",
                severity="CRITICAL"
            )
            return False
        else:
            print("✅ No old duplicates found - system is healthy")
            return True

    except Exception as e:
        print(f"❌ Exception: {e}")
        send_slack_alert(
            "Duplicate Monitor - Check Failed",
            f"⚠️ Health check failed with error:\n```{str(e)}```",
            severity="HIGH"
        )
        return False

def main():
    """Main monitoring loop"""
    print("🚀 Simple Duplicate Monitor Started")
    print(f"Checking every {CHECK_INTERVAL / 60:.0f} minutes")
    print(f"Alert if duplicates older than {DUPLICATE_AGE_THRESHOLD} minutes")
    print("\nPress Ctrl+C to stop\n")

    # Send startup notification
    send_slack_alert(
        "Duplicate Monitor - Started",
        f"✅ Monitoring is now active (simple Jira-based check).\n\n"
        f"• Check interval: Every {CHECK_INTERVAL / 60:.0f} minutes\n"
        f"• Alert threshold: Duplicates older than {DUPLICATE_AGE_THRESHOLD} minutes",
        severity="LOW"
    )

    try:
        while True:
            check_for_old_duplicates()

            print(f"\n💤 Sleeping for {CHECK_INTERVAL / 60:.0f} minutes...")
            print(f"Next check at: {(datetime.utcnow() + timedelta(seconds=CHECK_INTERVAL)).strftime('%Y-%m-%d %H:%M:%S UTC')}\n")

            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        print("\n\n🛑 Monitor stopped")
        send_slack_alert(
            "Duplicate Monitor - Stopped",
            "⚠️ Monitoring has been stopped.",
            severity="MEDIUM"
        )

if __name__ == "__main__":
    main()
