# 📧 Email Reports Setup Guide

## Overview

Your Jira Duplicate Canceller can send you beautiful daily email reports with:
- 📊 Statistics (checks, duplicates found, tickets cancelled)
- ⚠️ Duplicate details with confidence scores
- 💚 System health status
- 📈 Performance metrics

---

## 🚀 Quick Setup (3 Steps)

### Step 1: Generate Gmail App Password

**Why needed?** Gmail requires app-specific passwords for security.

1. Go to: https://myaccount.google.com/apppasswords
2. Sign in with your Google account
3. Select app: **Mail**
4. Select device: **Other (Custom name)**
5. Enter name: **Jira Duplicate Reports**
6. Click **Generate**
7. Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)

**Can't see App Passwords?**
- You need 2-Step Verification enabled first
- Go to: https://myaccount.google.com/signinoptions/two-step-verification
- Follow steps to enable it
- Then return to generate app password

---

### Step 2: Configure Email Settings

Edit the `.env.email` file:

```bash
cd ~/jira-duplicate-canceller
nano .env.email
```

Update this line with your app password (remove spaces):
```
EMAIL_PASSWORD=abcdefghijklmnop
```

Save and exit (Ctrl+X, then Y, then Enter)

---

### Step 3: Test Email Delivery

```bash
cd ~/jira-duplicate-canceller
./send-report.sh
```

**Expected output:**
```
📧 Generating daily Jira duplicate detection report...
📊 Fetching logs from DigitalOcean...
📈 Parsing statistics...
📝 Generating HTML report...
📧 Sending email to egoncharov@thealternative.co...
✅ Email sent successfully to egoncharov@thealternative.co
✅ Daily report sent successfully!
```

**Check your inbox!** You should receive a beautiful HTML email.

---

## ⏰ Schedule Daily Emails

### Option 1: Daily at 9 AM (Recommended)

```bash
# Edit crontab
crontab -e

# Add this line (sends report at 9:00 AM daily)
0 9 * * * /Users/jenyago/jira-duplicate-canceller/send-report.sh >> /Users/jenyago/jira-duplicate-canceller/email-report.log 2>&1
```

### Option 2: Daily at 6 PM (End of Day)

```bash
# Add this line (sends report at 6:00 PM daily)
0 18 * * * /Users/jenyago/jira-duplicate-canceller/send-report.sh >> /Users/jenyago/jira-duplicate-canceller/email-report.log 2>&1
```

### Option 3: Twice Daily (Morning & Evening)

```bash
# Morning at 9 AM and Evening at 6 PM
0 9,18 * * * /Users/jenyago/jira-duplicate-canceller/send-report.sh >> /Users/jenyago/jira-duplicate-canceller/email-report.log 2>&1
```

**Save crontab:**
- Press `Esc`
- Type `:wq`
- Press `Enter`

**Verify cron job:**
```bash
crontab -l | grep send-report
```

---

## 📧 Email Report Preview

Your daily email will look like this:

### Header
- 🤖 Jira Duplicate Detection Report
- Date: October 16, 2025

### Statistics Section
- Total Checks: 144
- Tickets Scanned: 32
- Duplicates Found: 1
- Tickets Cancelled: 1

### Duplicates Section (if any found)
- NVSTRS-402 ↔️ NVSTRS-403
- "Flowcarbon Investment Update..."
- Confidence: 94%

### System Health
- ✅ DigitalOcean Deployment: ACTIVE
- ✅ Detection Accuracy: 94% AVG
- ✅ False Positives: ZERO
- ✅ API Connectivity: HEALTHY

### Performance Metrics
- Average Confidence: 94%
- Checks Per Day: 144
- Response Time: ~3 seconds
- Success Rate: 100% ✅

---

## 🔧 Customization

### Change Recipient Email

Edit `.env.email`:
```bash
EMAIL_TO=your-email@example.com
```

### Add Multiple Recipients

Edit `send-daily-report.py` line 13:
```python
EMAIL_TO = "email1@example.com,email2@example.com,email3@example.com"
```

### Change Email Time

Crontab format: `minute hour day month weekday`

Examples:
- `0 9 * * *` → Daily at 9:00 AM
- `0 18 * * *` → Daily at 6:00 PM
- `0 9,18 * * *` → Daily at 9 AM and 6 PM
- `0 9 * * 1` → Every Monday at 9 AM
- `0 9 * * 1-5` → Weekdays only at 9 AM

### Test Anytime

Send report immediately:
```bash
cd ~/jira-duplicate-canceller
./send-report.sh
```

---

## 🐛 Troubleshooting

### Issue: "Username and Password not accepted"

**Solution:** Generate a new Gmail App Password
1. Old passwords expire or get revoked
2. Follow Step 1 above to generate new one
3. Update `.env.email` with new password

### Issue: "No such file or directory"

**Solution:** Check paths
```bash
cd ~/jira-duplicate-canceller
ls -la send-report.sh
chmod +x send-report.sh
```

### Issue: "Command not found: doctl"

**Solution:** Install DigitalOcean CLI
```bash
brew install doctl
doctl auth init
```

### Issue: No email received

**Check spam folder!** First email might go to spam.

**Mark as "Not Spam"** to receive future emails in inbox.

### Issue: Email looks plain (no HTML)

Some email clients show plain text by default.
- Gmail: Should show HTML automatically
- Apple Mail: Should show HTML automatically
- Outlook: Click "Display images"

---

## 📊 View Email Logs

Check if emails are being sent:
```bash
tail -f ~/jira-duplicate-canceller/email-report.log
```

Recent emails:
```bash
tail -50 ~/jira-duplicate-canceller/email-report.log
```

---

## ✅ Verification Checklist

- [ ] Generated Gmail App Password
- [ ] Updated `.env.email` with app password
- [ ] Tested email delivery (`./send-report.sh`)
- [ ] Received test email successfully
- [ ] Added cron job for daily emails
- [ ] Verified cron job (`crontab -l`)
- [ ] Checked email logs

---

## 📞 Support

**Email not working?**
1. Check `.env.email` has correct app password
2. Verify Gmail App Password is valid
3. Check spam folder
4. Review logs: `cat ~/jira-duplicate-canceller/email-report.log`

**Want to customize?**
- Edit `send-daily-report.py` for content changes
- Edit `.env.email` for configuration
- Edit crontab for schedule

---

## 🎯 Next Steps

1. **Set up app password** (Step 1)
2. **Test email** (`./send-report.sh`)
3. **Schedule daily email** (add to crontab)
4. **Enjoy automated reports!** 🎉

---

**Your reports will be sent automatically from now on!**