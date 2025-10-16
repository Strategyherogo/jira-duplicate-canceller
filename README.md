# 🤖 Jira Duplicate Ticket Canceller

An intelligent automation tool that detects and cancels duplicate Jira tickets with **75% confidence scoring** to prevent false positives. Built for accuracy, safety, and ease of deployment.

![Python](https://img.shields.io/badge/python-3.7+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-production-brightgreen.svg)

## ✨ Key Features

- 🎯 **High Accuracy**: 75% confidence threshold prevents false positives
- 🌍 **Multi-Language**: Handles email prefixes in 15+ languages
- ⏱️ **Smart Time Windows**: Adaptive detection based on reporter type (1-30 minutes)
- 📊 **Confidence Scoring**: Multi-criteria analysis with weighted scoring (0-115 points)
- 📝 **History Tracking**: Prevents re-processing of same ticket pairs
- 🔍 **Fuzzy Matching**: Similarity detection instead of exact match only
- 📧 **Pattern Recognition**: Detects common email thread patterns
- 🛡️ **Safe Mode**: Dry-run option for testing without changes
- 📈 **Detailed Logging**: Track every decision with confidence scores

## 🚀 Quick Start

### Prerequisites

- Python 3.7 or higher
- Jira Cloud account with API access
- Jira API token ([Get one here](https://id.atlassian.com/manage-profile/security/api-tokens))

### Installation

1. **Clone the repository**:
```bash
git clone https://github.com/yourusername/jira-duplicate-canceller.git
cd jira-duplicate-canceller
```

2. **Create virtual environment**:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Configure credentials**:
```bash
cp .env.example .env
# Edit .env with your Jira credentials
```

### Configuration

Edit `.env` with your Jira details:
```env
JIRA_SITE=your-company-name
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-api-token-here
```

**How to get an API token:**
1. Visit https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Give it a name (e.g., "Duplicate Canceller")
4. Copy the generated token

## 📖 Usage

### Basic Usage

```bash
# Test with dry-run (no changes made - RECOMMENDED FIRST)
python duplicate-canceller.py --dry-run --projects PROJECT1

# Run live (will cancel duplicates)
python duplicate-canceller.py --projects PROJECT1 PROJECT2

# Multiple projects at once
python duplicate-canceller.py --projects NVSTRS SUPPORT BILLING
```

### Advanced Options

```bash
# Custom confidence threshold (80 = more strict, fewer detections)
python duplicate-canceller.py --projects PROJECT1 --confidence 80

# Lower threshold (70 = less strict, more detections)
python duplicate-canceller.py --projects PROJECT1 --confidence 70

# Enable debug logging
python duplicate-canceller.py --projects PROJECT1 --debug

# Adjust similarity threshold
python duplicate-canceller.py --projects PROJECT1 --similarity 0.90
```

### Automated Scheduling

#### Linux/Mac (Cron)

Run every 10 minutes:
```bash
crontab -e
# Add this line:
*/10 * * * * /path/to/venv/bin/python /path/to/duplicate-canceller.py --projects PROJECT1
```

#### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily, repeat every 10 minutes
4. Action: Start a program
   - Program: `C:\path\to\venv\Scripts\python.exe`
   - Arguments: `C:\path\to\duplicate-canceller.py --projects PROJECT1`

## 🧮 How It Works

### Confidence Scoring System

The tool analyzes ticket pairs using multiple weighted criteria:

| Criteria | Max Points | What It Checks |
|----------|------------|----------------|
| **Subject Analysis** | 45 pts | Exact match, similarity percentage, core subject |
| **Time Proximity** | 25 pts | Tickets created within minutes (1min-1hr) |
| **Reporter Verification** | 20 pts | Same reporter/automation account |
| **Description Analysis** | 15 pts | Content similarity (first 500 chars) |
| **Pattern Detection** | 10 pts | Email thread patterns (capital call, invoice, etc.) |
| **Status Penalty** | -5 pts | Different status categories |

**Total Possible**: 115 points
**Default Threshold**: 75 points (75% confidence)

### Detection Process

```
1. Fetch tickets from last 7 days
   ↓
2. Normalize subjects (remove prefixes, clean text)
   ↓
3. Compare each pair of tickets
   ↓
4. Calculate confidence score (0-115 points)
   ↓
5. If score ≥ 75: Mark as duplicate
   ↓
6. Cancel newer ticket with explanation
   ↓
7. Log decision and save to history
```

### Subject Normalization

Removes common email variations:
- Email prefixes: RE:, FW:, FWD: (15+ languages)
- Thread indicators: [External], [SPAM], (2)
- Ticket IDs: PROJ-123, case numbers
- Email addresses and URLs
- Special characters and extra whitespace

### Example Detection

```
Ticket A: "Re: Q2 2025 Capital Call Notice - NVSTRS-371"
Ticket B: "FWD: Q2 2025 Capital Call Notice [External] (2)"

Normalized A: "q2 2025 capital call notice"
Normalized B: "q2 2025 capital call notice"

Similarity: 95%
Time diff: 30 seconds
Reporter: Same (automations)
Pattern: "capital call" detected

Confidence: 45 (subject) + 25 (time) + 20 (reporter) + 4 (pattern) = 94%
Result: ✅ DUPLICATE (exceeds 75% threshold)
```

## 📊 Monitoring

### Log Files

- `duplicate-canceller-v2-YYYYMMDD.log` - Daily detailed logs
- `duplicate-history.json` - Processed ticket pairs history

### Understanding Output

**Good (No duplicates)**:
```
INFO - Found 30 tickets
INFO - No duplicates found
INFO - Total tickets cancelled: 0
```

**Duplicate Detected**:
```
INFO - ✓ Duplicate detected: PROJ-123 and PROJ-124 (Confidence: 85%)
INFO - Reasons: Exact subject match, Created within 1 minute, Same automation reporter
INFO - Total tickets cancelled: 1
```

**Error**:
```
ERROR - Failed to fetch tickets: 401
```
→ Check API token and permissions

## 🔧 Customization

### Adjust Detection Sensitivity

Edit these variables in `duplicate-canceller.py`:

```python
# Line 28-30
CONFIDENCE_THRESHOLD = 75  # Increase for stricter (fewer detections)
SIMILARITY_THRESHOLD = 0.85  # Text similarity required (0.0-1.0)
TIME_WINDOW_MINUTES = 30  # Maximum time window for duplicates
```

### Customize Email Patterns

Add industry-specific terms (line 328):
```python
email_patterns = [
    'capital call', 'reporting package', 'action required',
    'your-custom-term', 'another-pattern'
]
```

## 🛡️ Security Best Practices

1. **Never commit credentials** - Use `.env` file (already in `.gitignore`)
2. **Restrict API token** - Grant only required Jira permissions:
   - Browse projects
   - View issues
   - Add comments
   - Transition issues
3. **Start with dry-run** - Always test before going live
4. **Monitor regularly** - Review logs for unexpected behavior
5. **Rotate tokens** - Change API tokens periodically

## 🐛 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: requests` | Run `pip install -r requirements.txt` |
| `API 401 Unauthorized` | Check API token validity and email address |
| `No duplicates found` | Lower confidence threshold or check time window |
| `Too many false positives` | Increase confidence threshold to 80+ |
| `Permission denied` | Make script executable: `chmod +x duplicate-canceller.py` |

### Debug Mode

Enable detailed logging:
```bash
python duplicate-canceller.py --projects PROJECT1 --debug
```

This shows:
- Subject normalization steps
- Similarity calculations
- Confidence score breakdown
- Comparison details for all ticket pairs

## 📈 Performance

- **Speed**: Processes ~200 tickets in <5 seconds
- **API Efficiency**: Batch fetching, minimal API calls
- **Memory**: <10MB usage
- **Scalability**: Handles projects with 1000+ tickets

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📝 License

MIT License - See [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

- Built with Python and [Jira REST API](https://developer.atlassian.com/cloud/jira/platform/rest/v3/)
- Uses `difflib.SequenceMatcher` for similarity analysis
- Inspired by email deduplication challenges in investor operations

## 📧 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/jira-duplicate-canceller/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/jira-duplicate-canceller/discussions)
- **Documentation**: See [ACCURACY_IMPROVEMENTS.md](ACCURACY_IMPROVEMENTS.md) for technical details

## 🎯 Roadmap

- [ ] Web dashboard for monitoring
- [ ] Machine learning for pattern detection
- [ ] Custom field matching support
- [ ] Webhook integration for real-time detection
- [ ] Multi-language UI
- [ ] Slack/Teams notifications
- [ ] Docker image for easy deployment

---

**Made with ❤️ for Jira admins tired of duplicate tickets**

**Star ⭐ this repo if it helps you!**