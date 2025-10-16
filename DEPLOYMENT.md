# 🚀 Deployment Guide - Jira Duplicate Canceller

## ✅ GitHub Repository Published!

**Repository**: https://github.com/Strategyherogo/jira-duplicate-canceller

Your code is now public and ready for deployment!

---

## 📍 Deployment Options

### Option 1: Local Cron (Already Running) ⭐ RECOMMENDED FOR SINGLE ORG

**Status**: ✅ Already deployed on your machine
**Cost**: Free
**Maintenance**: Low
**Best for**: Single organization, single Jira instance

#### Current Setup
```bash
# Running every 10 minutes on your Mac
# Location: /Users/jenyago/Library/CloudStorage/Dropbox-TheAlternative/Evgeny Goncharov/0. Apps Factory/jira-cleanup-scripts
```

#### Advantages
- ✅ No cloud costs
- ✅ Complete control
- ✅ Already configured
- ✅ Fast (no network latency)

#### Disadvantages
- ❌ Requires computer to be on
- ❌ Not accessible from other machines
- ❌ Single point of failure

---

### Option 2: AWS Lambda (Serverless) ⭐ RECOMMENDED FOR CLOUD

**Cost**: ~$0-1/month (Free tier covers it)
**Complexity**: Medium
**Best for**: Production deployments, multiple organizations

#### Setup Steps

1. **Prepare Lambda Package**
```bash
cd ~/jira-duplicate-canceller
mkdir lambda-package
pip install -r requirements.txt -t lambda-package/
cp duplicate-canceller.py lambda-package/
cd lambda-package && zip -r ../lambda-function.zip .
```

2. **Create Lambda Function** (AWS Console or CLI)
```bash
aws lambda create-function \
  --function-name jira-duplicate-canceller \
  --runtime python3.9 \
  --role arn:aws:iam::YOUR-ACCOUNT:role/lambda-role \
  --handler duplicate-canceller.lambda_handler \
  --zip-file fileb://lambda-function.zip \
  --timeout 300 \
  --memory-size 256
```

3. **Set Environment Variables**
```bash
aws lambda update-function-configuration \
  --function-name jira-duplicate-canceller \
  --environment Variables="{
    JIRA_SITE=your-site,
    JIRA_EMAIL=your-email@example.com,
    JIRA_API_TOKEN=your-token
  }"
```

4. **Create EventBridge Schedule**
```bash
# Run every 10 minutes
aws events put-rule \
  --name jira-duplicate-check \
  --schedule-expression "rate(10 minutes)"

aws events put-targets \
  --rule jira-duplicate-check \
  --targets "Id"="1","Arn"="arn:aws:lambda:REGION:ACCOUNT:function:jira-duplicate-canceller"
```

#### Advantages
- ✅ Fully managed
- ✅ Scales automatically
- ✅ Very cheap ($0-1/month)
- ✅ No server maintenance
- ✅ High availability

#### Disadvantages
- ❌ AWS account required
- ❌ Setup complexity
- ❌ Cold start delays

**Estimated Cost**: ~$0.20/month (well within free tier)

---

### Option 3: Docker + Cloud Run (Google Cloud)

**Cost**: ~$0-5/month
**Complexity**: Medium
**Best for**: Multi-cloud deployments

#### Setup Steps

1. **Create Dockerfile**
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY duplicate-canceller.py .

CMD ["python", "duplicate-canceller.py", "--projects", "NVSTRS"]
```

2. **Build and Push**
```bash
cd ~/jira-duplicate-canceller
docker build -t gcr.io/YOUR-PROJECT/jira-canceller .
docker push gcr.io/YOUR-PROJECT/jira-canceller
```

3. **Deploy to Cloud Run**
```bash
gcloud run deploy jira-canceller \
  --image gcr.io/YOUR-PROJECT/jira-canceller \
  --platform managed \
  --region us-central1 \
  --set-env-vars JIRA_SITE=your-site,JIRA_EMAIL=your-email,JIRA_API_TOKEN=your-token
```

4. **Schedule with Cloud Scheduler**
```bash
gcloud scheduler jobs create http jira-check \
  --schedule="*/10 * * * *" \
  --uri="https://YOUR-SERVICE-URL" \
  --http-method=POST
```

#### Advantages
- ✅ Container-based (portable)
- ✅ Auto-scaling
- ✅ Pay-per-use
- ✅ Easy CI/CD

#### Disadvantages
- ❌ GCP account needed
- ❌ Docker knowledge required

**Estimated Cost**: ~$2/month

---

### Option 4: Azure Functions

**Cost**: ~$0-2/month
**Complexity**: Medium
**Best for**: Organizations already on Azure

#### Quick Setup
```bash
# Install Azure Functions Core Tools
brew install azure-functions-core-tools

# Create function app
cd ~/jira-duplicate-canceller
func init --worker-runtime python
func new --name JiraDuplicateCheck --template "Timer trigger"

# Deploy
func azure functionapp publish YOUR-FUNCTION-APP
```

#### Advantages
- ✅ Integrated with Microsoft ecosystem
- ✅ Good monitoring tools
- ✅ Generous free tier

#### Disadvantages
- ❌ Azure account required
- ❌ Learning curve

**Estimated Cost**: ~$1/month

---

### Option 5: DigitalOcean App Platform

**Cost**: ~$5/month (cheapest tier)
**Complexity**: Low
**Best for**: Simple cloud deployment

#### Setup Steps

1. **Create app.yaml**
```yaml
name: jira-duplicate-canceller
services:
  - name: worker
    github:
      repo: Strategyherogo/jira-duplicate-canceller
      branch: main
    run_command: python duplicate-canceller.py --projects NVSTRS
    envs:
      - key: JIRA_SITE
        value: your-site
      - key: JIRA_EMAIL
        value: your-email
      - key: JIRA_API_TOKEN
        value: your-token
        type: SECRET
```

2. **Deploy**
```bash
doctl apps create --spec app.yaml
```

#### Advantages
- ✅ Very simple setup
- ✅ Good documentation
- ✅ Predictable pricing

#### Disadvantages
- ❌ More expensive than serverless
- ❌ Always running (not event-driven)

**Estimated Cost**: $5/month

---

### Option 6: Heroku (Simple but Pricier)

**Cost**: ~$7/month (Eco Dynos)
**Complexity**: Low
**Best for**: Quick prototypes

#### Setup
```bash
cd ~/jira-duplicate-canceller

# Create Procfile
echo "worker: python duplicate-canceller.py --projects NVSTRS" > Procfile

# Deploy
heroku create jira-duplicate-canceller
heroku config:set JIRA_SITE=your-site JIRA_EMAIL=your-email JIRA_API_TOKEN=your-token
git push heroku main

# Add scheduler
heroku addons:create scheduler:standard
# Then configure via dashboard to run every 10 minutes
```

#### Advantages
- ✅ Extremely simple
- ✅ Great developer experience
- ✅ Built-in scheduler

#### Disadvantages
- ❌ More expensive
- ❌ Overkill for this use case

**Estimated Cost**: $7/month

---

### Option 7: GitHub Actions (Free for public repos!)

**Cost**: FREE ✨
**Complexity**: Low
**Best for**: Public repos, testing

#### Setup

Create `.github/workflows/duplicate-check.yml`:
```yaml
name: Jira Duplicate Check

on:
  schedule:
    - cron: '*/10 * * * *'  # Every 10 minutes
  workflow_dispatch:  # Manual trigger

jobs:
  check-duplicates:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run duplicate checker
        env:
          JIRA_SITE: ${{ secrets.JIRA_SITE }}
          JIRA_EMAIL: ${{ secrets.JIRA_EMAIL }}
          JIRA_API_TOKEN: ${{ secrets.JIRA_API_TOKEN }}
        run: python duplicate-canceller.py --projects NVSTRS
```

Then add secrets in GitHub repo settings:
- JIRA_SITE
- JIRA_EMAIL
- JIRA_API_TOKEN

#### Advantages
- ✅ Completely FREE
- ✅ No infrastructure
- ✅ Built into GitHub
- ✅ Easy to monitor

#### Disadvantages
- ❌ Limited to public repos (or paid GitHub)
- ❌ Less reliable than dedicated infrastructure
- ❌ 6-hour delay possible during high load

**Estimated Cost**: FREE (for public repos)

---

## 📊 Comparison Table

| Option | Cost/Month | Complexity | Reliability | Best For |
|--------|------------|------------|-------------|----------|
| **Local Cron** | $0 | Low | Medium | Single org, already running |
| **AWS Lambda** | $0-1 | Medium | High | Production, scale |
| **GCP Cloud Run** | $0-5 | Medium | High | Multi-cloud |
| **Azure Functions** | $0-2 | Medium | High | Microsoft shops |
| **DigitalOcean** | $5 | Low | High | Simple cloud |
| **Heroku** | $7 | Low | High | Quick deploy |
| **GitHub Actions** | $0 | Low | Medium | Public repos |

---

## 🎯 Recommendations

### For Your Current Setup (The Alternative)
**Keep local cron** - It's already working perfectly!
- ✅ Free
- ✅ Fast
- ✅ Complete control
- ✅ No vendor lock-in

### For Other Organizations/Clients
**Option 1: GitHub Actions** (if repo is public)
- Free and simple
- No infrastructure needed
- Good enough for most use cases

**Option 2: AWS Lambda** (if need production-grade)
- Cheap (~$0.20/month)
- Highly reliable
- Industry standard
- Scales automatically

### For SaaS Product
If you want to offer this as a service:
- **AWS Lambda** for compute
- **DynamoDB** for history storage
- **API Gateway** for webhook endpoint
- **Cognito** for user auth

**Estimated Cost**: $5-20/month for 100 organizations

---

## 🔒 Security Considerations

### Environment Variables
Always use environment variables or secrets management:

**AWS**: Secrets Manager or Parameter Store
**GCP**: Secret Manager
**Azure**: Key Vault
**Heroku/DO**: Built-in config vars
**GitHub**: Repository secrets

### API Token Permissions
Restrict Jira API token to minimum required:
- ✅ Browse projects
- ✅ View issues
- ✅ Add comments
- ✅ Transition issues
- ❌ Delete projects
- ❌ Administer Jira
- ❌ Manage users

---

## 📈 Monitoring & Alerting

### Add Monitoring
For cloud deployments, add:

1. **Health checks** - Ensure service is running
2. **Error alerts** - Get notified on failures
3. **Usage metrics** - Track API calls
4. **Cost alerts** - Monitor spending

### Example AWS CloudWatch Alarm
```bash
aws cloudwatch put-metric-alarm \
  --alarm-name jira-canceller-errors \
  --alarm-description "Alert on Lambda errors" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 5 \
  --comparison-operator GreaterThanThreshold
```

---

## ✅ Final Recommendation

**For you right now**:
✨ **Keep using local cron** - It's working perfectly!

**For sharing with others**:
✨ **Use GitHub Actions** - Free, simple, works out of the box

**For production/commercial**:
✨ **Deploy on AWS Lambda** - Reliable, scalable, cheap

---

## 🆘 Need Help Deploying?

I can help you set up any of these options. Just let me know which one you prefer!