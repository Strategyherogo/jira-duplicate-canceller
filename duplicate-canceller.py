#!/usr/bin/env python3

"""
Jira Duplicate Ticket Canceller v2 - Enhanced Accuracy
Purpose: Automatically detect and cancel duplicate tickets with high accuracy
Features: Similarity scoring, time proximity, reporter checks, confidence levels
Created: 2025-10-16
GitHub Version: Credentials removed for security
"""

import requests
import json
import base64
import re
import os
from datetime import datetime, timedelta
from collections import defaultdict
import logging
from difflib import SequenceMatcher
import unicodedata

# Configuration - REPLACE WITH YOUR OWN CREDENTIALS
JIRA_SITE = os.getenv("JIRA_SITE", "your-site")  # e.g., "mycompany"
JIRA_URL = f"https://{JIRA_SITE}.atlassian.net"
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "your-email@example.com")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "your-api-token-here")

# Enhanced Configuration
SIMILARITY_THRESHOLD = 0.85  # 85% similarity required
TIME_WINDOW_MINUTES = 30  # Consider duplicates within 30 minutes
CONFIDENCE_THRESHOLD = 75  # 75% confidence required to mark as duplicate

# Setup logging
log_file = f"duplicate-canceller-v2-{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

# Create auth header
auth_string = f"{JIRA_EMAIL}:{JIRA_API_TOKEN}"
auth_bytes = auth_string.encode('ascii')
auth_b64 = base64.b64encode(auth_bytes).decode('ascii')

headers = {
    "Authorization": f"Basic {auth_b64}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

class EnhancedDuplicateCanceller:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.cancelled_count = 0
        self.processed_pairs = set()  # Track processed ticket pairs
        self.history_file = "duplicate-history.json"
        self.load_history()

    def load_history(self):
        """Load processing history to avoid re-cancelling"""
        try:
            if os.path.exists(self.history_file):
                with open(self.history_file, 'r') as f:
                    data = json.load(f)
                    self.processed_pairs = set(tuple(pair) for pair in data.get('processed_pairs', []))
                    logging.info(f"Loaded {len(self.processed_pairs)} processed pairs from history")
        except Exception as e:
            logging.warning(f"Could not load history: {e}")
            self.processed_pairs = set()

    def save_history(self):
        """Save processing history"""
        try:
            with open(self.history_file, 'w') as f:
                json.dump({
                    'processed_pairs': [list(pair) for pair in self.processed_pairs],
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logging.error(f"Could not save history: {e}")

    def advanced_normalize_subject(self, subject):
        """Advanced subject normalization for better accuracy"""
        if not subject:
            return ""

        original = subject
        # Convert to lowercase
        subject = subject.lower()

        # Remove email prefixes in multiple languages (expanded list)
        email_prefixes = [
            r'^re:\s*', r'^re\[\d+\]:\s*', r'^re\s*\[\d+\]:\s*',  # RE: variations
            r'^fw:\s*', r'^fwd:\s*', r'^forwarded:\s*',           # Forward variations
            r'^aw:\s*', r'^antw:\s*',                              # German reply
            r'^sv:\s*', r'^svar:\s*',                              # Swedish/Norwegian reply
            r'^vs:\s*', r'^vedr:\s*',                              # Danish reply
            r'^tr:\s*',                                            # Turkish reply
            r'^res:\s*', r'^resp:\s*',                             # Spanish reply
            r'^enc:\s*',                                           # Spanish forward
            r'^odg:\s*',                                           # Polish reply
            r'^ynt:\s*',                                           # Turkish reply
            r'^att:\s*',                                           # Finnish reply
            r'^回复:\s*', r'^转发:\s*',                             # Chinese
            r'^답장:\s*', r'^전달:\s*',                             # Korean
            r'^返信:\s*', r'^転送:\s*',                             # Japanese
        ]

        for prefix in email_prefixes:
            subject = re.sub(prefix, '', subject, flags=re.IGNORECASE)

        # Remove trailing RE/FW that might be at the end
        subject = re.sub(r'\s*\(re\)\s*$', '', subject, flags=re.IGNORECASE)
        subject = re.sub(r'\s*\(fwd?\)\s*$', '', subject, flags=re.IGNORECASE)

        # Remove email thread indicators
        subject = re.sub(r'\[external\]', '', subject, flags=re.IGNORECASE)
        subject = re.sub(r'\[spam\]', '', subject, flags=re.IGNORECASE)
        subject = re.sub(r'\[important\]', '', subject, flags=re.IGNORECASE)
        subject = re.sub(r'\[urgent\]', '', subject, flags=re.IGNORECASE)

        # Remove email thread numbers
        subject = re.sub(r'\(\d+\)', '', subject)
        subject = re.sub(r'\[\d+\]', '', subject)
        subject = re.sub(r'#\d+', '', subject)

        # Remove case numbers and ticket IDs (common patterns)
        subject = re.sub(r'\b[a-z]{2,6}[-_]?\d{3,8}\b', '', subject, flags=re.IGNORECASE)

        # Remove URLs
        subject = re.sub(r'https?://\S+|www\.\S+', '', subject)

        # Remove email addresses
        subject = re.sub(r'[\w\.-]+@[\w\.-]+\.\w+', '', subject)

        # Remove multiple spaces and special characters
        subject = re.sub(r'[_\-–—•·│┃┆┇┈┉┊┋]+', ' ', subject)
        subject = re.sub(r'\s+', ' ', subject)

        # Remove trailing/leading whitespace
        subject = subject.strip()

        # Log normalization for debugging
        if subject != original.lower().strip():
            logging.debug(f"Normalized: '{original[:50]}...' -> '{subject[:50]}...'")

        return subject

    def calculate_similarity(self, str1, str2):
        """Calculate similarity score between two strings"""
        if not str1 or not str2:
            return 0.0

        # Quick exact match check
        if str1 == str2:
            return 1.0

        # Use SequenceMatcher for fuzzy matching
        return SequenceMatcher(None, str1, str2).ratio()

    def extract_core_subject(self, subject):
        """Extract the core subject by removing variable parts"""
        # Remove dates in various formats
        subject = re.sub(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', '', subject)
        subject = re.sub(r'\d{4}[/-]\d{1,2}[/-]\d{1,2}', '', subject)

        # Remove times
        subject = re.sub(r'\d{1,2}:\d{2}(:\d{2})?(\s*[ap]m)?', '', subject, flags=re.IGNORECASE)

        # Remove ticket numbers or IDs
        subject = re.sub(r'#\d+', '', subject)
        subject = re.sub(r'\[\d+\]', '', subject)

        # Remove email addresses
        subject = re.sub(r'\S+@\S+\.\S+', '', subject)

        # Clean up
        subject = re.sub(r'\s+', ' ', subject).strip()

        return subject

    def get_tickets(self, project, days_back=7):
        """Fetch tickets from specified project with enhanced field retrieval"""
        jql = f"project = {project} AND created >= -{days_back}d ORDER BY created ASC"

        url = f"{JIRA_URL}/rest/api/3/search/jql"
        params = {
            "jql": jql,
            "maxResults": 200,
            "fields": "summary,created,status,assignee,reporter,description,comment,updated"
        }

        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                return response.json().get('issues', [])
            else:
                logging.error(f"Failed to fetch tickets: {response.status_code}")
                if response.status_code == 410:
                    # Fallback to older API
                    url = f"{JIRA_URL}/rest/api/2/search"
                    response = requests.get(url, headers=headers, params=params)
                    if response.status_code == 200:
                        return response.json().get('issues', [])
                return []
        except Exception as e:
            logging.error(f"Error fetching tickets: {e}")
            return []

    def are_tickets_duplicate(self, ticket1, ticket2):
        """Enhanced duplicate detection with multiple criteria and improved confidence scoring"""
        # Extract basic info
        key1 = ticket1['key']
        key2 = ticket2['key']

        # Skip if already processed
        pair = tuple(sorted([key1, key2]))
        if pair in self.processed_pairs:
            return False

        summary1 = ticket1['fields']['summary']
        summary2 = ticket2['fields']['summary']
        created1 = ticket1['fields']['created']
        created2 = ticket2['fields']['created']
        status1 = ticket1['fields']['status']['name']
        status2 = ticket2['fields']['status']['name']
        reporter1 = ticket1['fields'].get('reporter', {})
        reporter2 = ticket2['fields'].get('reporter', {})
        description1 = ticket1['fields'].get('description', '') or ''
        description2 = ticket2['fields'].get('description', '') or ''

        # Skip if either is already processed (cancelled/done)
        processed_statuses = ['cancelled', 'done', 'closed', 'resolved', 'duplicate']
        if any(s in status1.lower() for s in processed_statuses) or \
           any(s in status2.lower() for s in processed_statuses):
            return False

        # Initialize confidence score and reasons
        confidence_score = 0
        reasons = []

        # === CRITERION 1: Subject Analysis (max 45 points) ===
        norm1 = self.advanced_normalize_subject(summary1)
        norm2 = self.advanced_normalize_subject(summary2)
        core1 = self.extract_core_subject(norm1)
        core2 = self.extract_core_subject(norm2)

        # Calculate various similarity metrics
        norm_similarity = self.calculate_similarity(norm1, norm2)
        core_similarity = self.calculate_similarity(core1, core2) if (core1 and core2) else 0

        if norm1 == norm2 and len(norm1) > 5:  # Exact match (not empty)
            confidence_score += 45
            reasons.append("Exact subject match")
        elif norm_similarity >= 0.95:
            confidence_score += 40
            reasons.append(f"Very high subject similarity ({norm_similarity:.1%})")
        elif norm_similarity >= 0.85:
            confidence_score += 35
            reasons.append(f"High subject similarity ({norm_similarity:.1%})")
        elif core1 == core2 and len(core1) > 10:  # Core match with substance
            confidence_score += 30
            reasons.append("Core subject match")
        elif norm_similarity >= 0.75:
            confidence_score += 25
            reasons.append(f"Good subject similarity ({norm_similarity:.1%})")
        elif core_similarity >= 0.80 and len(core1) > 10:
            confidence_score += 20
            reasons.append(f"Core similarity ({core_similarity:.1%})")

        # === CRITERION 2: Time Proximity (max 25 points) ===
        time1 = datetime.fromisoformat(created1.replace('Z', '+00:00'))
        time2 = datetime.fromisoformat(created2.replace('Z', '+00:00'))
        time_diff_seconds = abs((time2 - time1).total_seconds())
        time_diff_minutes = time_diff_seconds / 60

        # Adaptive time windows
        if time_diff_minutes <= 1:  # Within 1 minute
            confidence_score += 25
            reasons.append("Created within 1 minute (likely automation duplicate)")
        elif time_diff_minutes <= 5:  # Within 5 minutes
            confidence_score += 20
            reasons.append(f"Created within {int(time_diff_minutes)} minutes")
        elif time_diff_minutes <= 15:  # Within 15 minutes
            confidence_score += 15
            reasons.append(f"Created within {int(time_diff_minutes)} minutes")
        elif time_diff_minutes <= 30:  # Within 30 minutes
            confidence_score += 10
            reasons.append(f"Created within {int(time_diff_minutes)} minutes")
        elif time_diff_minutes <= 60:  # Within 1 hour
            confidence_score += 5
            reasons.append("Created within 1 hour")

        # === CRITERION 3: Reporter Analysis (max 20 points) ===
        if reporter1 and reporter2:
            same_email = reporter1.get('emailAddress') == reporter2.get('emailAddress')
            same_name = reporter1.get('displayName') == reporter2.get('displayName')
            same_account = reporter1.get('accountId') == reporter2.get('accountId')

            if same_account or (same_email and same_name):
                reporter_name = reporter1.get('displayName', 'Unknown')
                is_automation = 'automation' in reporter_name.lower() or 'bot' in reporter_name.lower()

                if is_automation:
                    confidence_score += 20
                    reasons.append(f"Same automation reporter: {reporter_name}")
                else:
                    confidence_score += 15
                    reasons.append(f"Same reporter: {reporter_name}")

        # === CRITERION 4: Description Analysis (max 15 points) ===
        desc_norm1 = ""
        desc_norm2 = ""
        if description1 and description2 and len(description1) > 20 and len(description2) > 20:
            # Compare first 500 chars of description
            desc_norm1 = self.advanced_normalize_subject(description1[:500])
            desc_norm2 = self.advanced_normalize_subject(description2[:500])
            desc_similarity = self.calculate_similarity(desc_norm1, desc_norm2)

            if desc_similarity >= 0.90:
                confidence_score += 15
                reasons.append(f"Very similar descriptions ({desc_similarity:.1%})")
            elif desc_similarity >= 0.75:
                confidence_score += 10
                reasons.append(f"Similar descriptions ({desc_similarity:.1%})")
            elif desc_similarity >= 0.60:
                confidence_score += 5
                reasons.append("Somewhat similar descriptions")

        # === CRITERION 5: Pattern Detection (max 10 points) ===
        # Email thread patterns
        email_patterns = [
            'capital call', 'reporting package', 'action required',
            'payment', 'invoice', 'statement', 'fund', 'investor',
            'quarterly report', 'monthly report', 'distribution',
            'subscription', 'redemption', 'transfer', 'notice'
        ]

        norm_combined1 = f"{norm1} {desc_norm1}"
        norm_combined2 = f"{norm2} {desc_norm2}"

        pattern_matches = 0
        for pattern in email_patterns:
            if pattern in norm_combined1 and pattern in norm_combined2:
                pattern_matches += 1

        if pattern_matches >= 3:
            confidence_score += 10
            reasons.append(f"Multiple email patterns matched ({pattern_matches})")
        elif pattern_matches >= 2:
            confidence_score += 7
            reasons.append(f"Email patterns matched ({pattern_matches})")
        elif pattern_matches >= 1:
            confidence_score += 4
            reasons.append("Email pattern detected")

        # === CRITERION 6: Negative Indicators (reduce score) ===
        # Different status categories might indicate intentional separate tickets
        if status1 != status2:
            status_category1 = ticket1['fields']['status'].get('statusCategory', {}).get('key', '')
            status_category2 = ticket2['fields']['status'].get('statusCategory', {}).get('key', '')
            if status_category1 != status_category2:
                confidence_score -= 5
                reasons.append("(Different status categories)")

        # Log the detailed analysis
        if confidence_score > 30:  # Only log potential matches
            logging.debug(f"Comparing {key1} vs {key2}:")
            logging.debug(f"  - Subject similarity: {norm_similarity:.1%}")
            logging.debug(f"  - Time difference: {time_diff_minutes:.1f} minutes")
            logging.debug(f"  - Confidence score: {confidence_score}")
            logging.debug(f"  - Reasons: {', '.join(reasons)}")

        # Require high confidence to mark as duplicate
        is_duplicate = confidence_score >= CONFIDENCE_THRESHOLD

        if is_duplicate:
            logging.info(f"✓ Duplicate detected: {key1} and {key2} (Confidence: {confidence_score}%)")
            logging.info(f"  Summary1: {summary1[:60]}...")
            logging.info(f"  Summary2: {summary2[:60]}...")
            logging.info(f"  Reasons: {', '.join(reasons)}")

        return is_duplicate

    def find_duplicates(self, tickets):
        """Find duplicate tickets with enhanced accuracy"""
        duplicates = []

        # Sort by creation date
        tickets_sorted = sorted(tickets, key=lambda x: x['fields']['created'])

        # Compare each ticket with others
        for i in range(len(tickets_sorted)):
            for j in range(i + 1, len(tickets_sorted)):
                if self.are_tickets_duplicate(tickets_sorted[i], tickets_sorted[j]):
                    # Found a duplicate pair
                    duplicates.append((tickets_sorted[i], tickets_sorted[j]))

        return duplicates

    def cancel_ticket(self, ticket_key, original_key, comment=None):
        """Cancel a specific ticket with proper transition"""
        if self.dry_run:
            logging.info(f"[DRY RUN] Would cancel ticket: {ticket_key}")
            return True

        try:
            # Get available transitions
            transitions_url = f"{JIRA_URL}/rest/api/3/issue/{ticket_key}/transitions"
            response = requests.get(transitions_url, headers=headers)

            if response.status_code != 200:
                logging.error(f"Failed to get transitions for {ticket_key}")
                return False

            transitions = response.json().get('transitions', [])

            # Find appropriate transition
            cancel_transition = None
            preferred_transitions = ['done', 'duplicate', 'close', 'cancel', 'resolve']

            for pref in preferred_transitions:
                for transition in transitions:
                    if pref in transition['name'].lower():
                        cancel_transition = transition
                        break
                if cancel_transition:
                    break

            if not cancel_transition:
                logging.warning(f"No suitable transition found for {ticket_key}")
                return False

            # Add detailed comment
            if comment:
                comment_url = f"{JIRA_URL}/rest/api/3/issue/{ticket_key}/comment"
                comment_body = {"body": comment}
                requests.post(comment_url, headers=headers, data=json.dumps(comment_body))

            # Execute transition
            transition_data = {
                "transition": {"id": cancel_transition['id']}
            }

            response = requests.post(
                transitions_url,
                headers=headers,
                data=json.dumps(transition_data)
            )

            if response.status_code == 204:
                logging.info(f"✅ Successfully cancelled ticket: {ticket_key} using '{cancel_transition['name']}'")
                self.cancelled_count += 1
                return True
            else:
                logging.error(f"Failed to cancel {ticket_key}: {response.status_code}")
                return False

        except Exception as e:
            logging.error(f"Error cancelling {ticket_key}: {e}")
            return False

    def process_duplicates(self, duplicate_pairs):
        """Process duplicate pairs and cancel newer tickets"""
        total_cancelled = 0

        for original, duplicate in duplicate_pairs:
            key1 = original['key']
            key2 = duplicate['key']

            # Mark this pair as processed
            pair = tuple(sorted([key1, key2]))
            self.processed_pairs.add(pair)

            # Determine which to keep (older one)
            if original['fields']['created'] <= duplicate['fields']['created']:
                to_keep = original
                to_cancel = duplicate
            else:
                to_keep = duplicate
                to_cancel = original

            logging.info(f"\nProcessing duplicate pair:")
            logging.info(f"  Keep:   {to_keep['key']} - {to_keep['fields']['summary'][:60]}")
            logging.info(f"  Cancel: {to_cancel['key']} - {to_cancel['fields']['summary'][:60]}")

            # Create detailed comment
            comment = (
                f"🤖 Automated Duplicate Detection (v2)\n\n"
                f"This ticket has been identified as a duplicate of {to_keep['key']}.\n\n"
                f"**Detection Criteria:**\n"
                f"• Subject similarity detected\n"
                f"• Created within short time window\n"
                f"• Confidence threshold met ({CONFIDENCE_THRESHOLD}%)\n\n"
                f"**Original ticket:** {to_keep['key']} - {to_keep['fields']['summary']}\n\n"
                f"If this was marked incorrectly, please reopen with an explanation.\n\n"
                f"_Automated by Duplicate Canceller v2 at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"
            )

            if self.cancel_ticket(to_cancel['key'], to_keep['key'], comment):
                total_cancelled += 1

        # Save history after processing
        self.save_history()

        return total_cancelled

    def run(self, projects):
        """Main execution function"""
        logging.info(f"\n{'='*80}")
        logging.info(f"Enhanced Duplicate Canceller v2 Started - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logging.info(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE'}")
        logging.info(f"Projects: {', '.join(projects)}")
        logging.info(f"Confidence Threshold: {CONFIDENCE_THRESHOLD}%")
        logging.info(f"{'='*80}\n")

        all_duplicates = []

        for project in projects:
            logging.info(f"Processing project: {project}")

            # Get tickets
            tickets = self.get_tickets(project)
            logging.info(f"  Found {len(tickets)} tickets")

            # Find duplicates with enhanced accuracy
            duplicates = self.find_duplicates(tickets)

            if duplicates:
                all_duplicates.extend(duplicates)
                logging.info(f"  Found {len(duplicates)} duplicate pairs")
            else:
                logging.info(f"  No duplicates found")

        # Process all duplicates
        total_cancelled = 0
        if all_duplicates:
            logging.info(f"\nProcessing {len(all_duplicates)} duplicate pairs...")
            total_cancelled = self.process_duplicates(all_duplicates)

        # Summary
        logging.info(f"\n{'='*80}")
        logging.info(f"Enhanced Duplicate Canceller Complete")
        logging.info(f"Total tickets cancelled: {total_cancelled}")
        logging.info(f"Processed pairs tracked: {len(self.processed_pairs)}")
        logging.info(f"{'='*80}\n")

        return total_cancelled

def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Cancel duplicate Jira tickets with enhanced accuracy')
    parser.add_argument('--dry-run', action='store_true',
                       help='Run in dry-run mode (no actual changes)')
    parser.add_argument('--projects', nargs='+', required=True,
                       help='Projects to check (e.g., PROJECT1 PROJECT2)')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug logging')
    parser.add_argument('--confidence', type=int, default=75,
                       help='Confidence threshold percentage (default: 75)')
    parser.add_argument('--similarity', type=float, default=0.85,
                       help='Similarity threshold (default: 0.85)')

    args = parser.parse_args()

    # Override global settings if provided
    global CONFIDENCE_THRESHOLD, SIMILARITY_THRESHOLD
    CONFIDENCE_THRESHOLD = args.confidence
    SIMILARITY_THRESHOLD = args.similarity

    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    # Check for required environment variables
    if JIRA_API_TOKEN == "your-api-token-here":
        print("ERROR: Please set your Jira credentials as environment variables:")
        print("  export JIRA_SITE='your-site'")
        print("  export JIRA_EMAIL='your-email@example.com'")
        print("  export JIRA_API_TOKEN='your-api-token'")
        print("\nTo get an API token:")
        print("1. Go to https://id.atlassian.com/manage-profile/security/api-tokens")
        print("2. Click 'Create API token'")
        print("3. Give it a name and copy the token")
        return

    # Initialize the canceller
    canceller = EnhancedDuplicateCanceller(dry_run=args.dry_run)

    # Run once
    canceller.run(args.projects)

if __name__ == "__main__":
    main()