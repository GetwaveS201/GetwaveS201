# How to Download & Import n8n Workflows

## 📥 Files to Download

You need to download these 2 n8n workflow files:

1. **`n8n-adjuster-followup-workflow.json`** - Email qualification & approval queue
2. **`n8n-daily-scheduler-workflow.json`** - Daily automated follow-up sender

---

## 🔽 How to Download Files

### Option 1: From GitHub (If pushed to repository)

1. Go to your GitHub repository
2. Navigate to `/docs/` folder
3. Click on `n8n-adjuster-followup-workflow.json`
4. Click the "Raw" button (top right)
5. Right-click → "Save As..." → Save to your computer
6. Repeat for `n8n-daily-scheduler-workflow.json`

### Option 2: From Local Files

The files are located at:
```
/home/user/GetwaveS201/docs/n8n-adjuster-followup-workflow.json
/home/user/GetwaveS201/docs/n8n-daily-scheduler-workflow.json
```

**To copy them:**
```bash
# From the project directory
cp docs/n8n-adjuster-followup-workflow.json ~/Downloads/
cp docs/n8n-daily-scheduler-workflow.json ~/Downloads/
```

### Option 3: Using Git

```bash
cd /home/user/GetwaveS201
git pull origin claude/insurance-claims-automation-b72Xf

# Files are in docs/ folder
ls -la docs/n8n-*.json
```

---

## 📤 How to Import into n8n

### Step 1: Install n8n (if not already installed)

```bash
npm install n8n -g
```

### Step 2: Start n8n

```bash
n8n start
```

This will open n8n in your browser at `http://localhost:5678`

### Step 3: Import Workflow #1 (Email Qualification)

1. **Open n8n** in your browser
2. Click **"Workflows"** in the left sidebar
3. Click **"Add workflow"** button (top right)
4. Click the **"..."** menu (top right corner)
5. Select **"Import from File"**
6. Choose **`n8n-adjuster-followup-workflow.json`**
7. Click **"Import"**

✅ Workflow imported!

### Step 4: Import Workflow #2 (Daily Scheduler)

1. Click **"Add workflow"** again
2. Click the **"..."** menu
3. Select **"Import from File"**
4. Choose **`n8n-daily-scheduler-workflow.json`**
5. Click **"Import"**

✅ Both workflows imported!

---

## ⚙️ Configure Workflows

### Configure Workflow #1: Email Qualification

**1. Set up Gmail Credentials:**
- Click on "Gmail Trigger - New Email" node
- Click "Create New Credential"
- Follow OAuth2 flow to connect your Gmail account
- Save credentials

**2. Update API URL:**
- Click on "Call Qualification API" node
- Replace `https://YOUR_API_URL` with your actual backend URL
  - Example: `http://localhost:8000` (local)
  - Example: `https://api.yourcompany.com` (production)

**3. Create API Authentication:**
- Click "Credentials" in left sidebar
- Click "Add Credential"
- Choose "Header Auth"
- Set:
  - **Name:** `RestorationOS API Token`
  - **Header Name:** `Authorization`
  - **Header Value:** `Bearer YOUR_JWT_TOKEN`
- Save

**4. Create Gmail Label:**
- Open Gmail
- Create new label: "Adjuster Follow-Up - Needs Approval"
- In n8n, click "Apply Gmail Label" node
- Update `Label_AdjusterFollowUp` to your label ID
  - Or use label name if n8n supports it

**5. Test the Workflow:**
- Click "Execute Workflow" button
- Or send a test email to trigger it
- Check execution log for results

**6. Activate Workflow:**
- Toggle "Active" switch (top right)
- Workflow now runs automatically on new emails!

---

### Configure Workflow #2: Daily Scheduler

**1. Update API URL:**
- Click on "Run Scheduler API" node
- Replace `https://YOUR_API_URL` with your backend URL

**2. Set Schedule (if needed):**
- Click "Schedule - Daily 8 AM (Weekdays)" node
- Cron expression: `0 8 * * 1-5`
  - `0` = minute 0
  - `8` = hour 8 AM
  - `*` = every day of month
  - `*` = every month
  - `1-5` = Monday-Friday
- Modify if you want different time/days

**3. Configure Email Report (Optional):**
- Click "Send Email Report" node
- Set up SMTP credentials:
  - Host: `smtp.gmail.com` (or your email provider)
  - Port: `587` (TLS) or `465` (SSL)
  - Username: your email
  - Password: app password
- Update sender/recipient emails

**4. Test the Workflow:**
- Click "Execute Workflow" button
- Check API response
- Verify email report sent (if configured)

**5. Activate Workflow:**
- Toggle "Active" switch
- Workflow now runs daily at 8 AM (weekdays)!

---

## 🔐 Setting Up Credentials

### Gmail OAuth2

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project (or use existing)
3. Enable Gmail API
4. Create OAuth2 credentials
5. Add authorized redirect URI: `http://localhost:5678/rest/oauth2-credential/callback`
6. Copy Client ID and Client Secret
7. In n8n, paste credentials and complete OAuth flow

### API Authentication (JWT Token)

**Get your JWT token:**
```bash
# Login to get token
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your@email.com",
    "password": "yourpassword"
  }'

# Response includes:
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Add to n8n:**
- Use the `access_token` value
- Format: `Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...`

---

## 🧪 Testing Guide

### Test Email Qualification Workflow

**1. Send Test Email:**
- From adjuster email (e.g., test@allstate.com)
- Subject: "RE: Invoice #12345"
- Body: "We need payment documentation"
- To: your business email

**2. Check n8n:**
- Go to "Executions" in n8n
- Should see new execution
- Click to view details
- Should see "qualified: true"

**3. Check Gmail:**
- Email should have label "Adjuster Follow-Up - Needs Approval"

**4. Check Backend:**
- Go to RestorationOS frontend
- Navigate to "Adjuster Follow-Ups"
- Should see email in "Pending Approval" tab

### Test Daily Scheduler Workflow

**1. Manual Test:**
- In n8n, open scheduler workflow
- Click "Execute Workflow"
- Wait for completion
- Check execution results

**2. Check API Response:**
- Should see:
  ```json
  {
    "processed_at": "2026-01-15T08:00:00Z",
    "total_threads": 0,
    "results": []
  }
  ```

**3. Check Email Report:**
- If configured, check your inbox
- Should receive summary email

---

## 🎯 Workflow Diagram

### Email Qualification Flow

```
New Email Arrives (Gmail)
    ↓
Extract Email Data (sender, subject, body)
    ↓
Check Domain Qualified? (insurance/TPA/adjuster)
    ↓ YES
Check Billing Keywords? (invoice, payment, etc.)
    ↓ YES
Call Qualification API
    ↓
Qualified = TRUE?
    ↓ YES
Apply Gmail Label "Needs Approval"
    ↓
Log Success
```

### Daily Scheduler Flow

```
Schedule Trigger (8 AM, Mon-Fri)
    ↓
Call Scheduler API
    ↓
Parse Results (count sent/skipped/failed)
    ↓
Any Emails Sent?
    ↓ YES
Send Summary Email Report to Management
```

---

## 🔧 Customization Options

### Change Email Domains

Edit the regex in "Check Domain Qualified" node:
```
(allstate|statefarm|YOUR_CARRIER)\\.com
```

Add your carriers/TPAs to the list.

### Change Billing Keywords

Edit the regex in "Check Billing Keywords" node:
```
(invoice|payment|YOUR_KEYWORD)
```

### Change Schedule Time

Edit cron expression in scheduler:
- `0 9 * * 1-5` = 9 AM weekdays
- `0 8 * * *` = 8 AM every day
- `0 8,14 * * 1-5` = 8 AM and 2 PM weekdays

### Add More Actions

You can add nodes to:
- Send Slack notifications
- Update Google Sheets
- Log to database
- Send SMS alerts
- Create tickets in project management tools

---

## 🆘 Troubleshooting

### "Invalid credentials" error
- Re-authenticate Gmail OAuth2
- Check API token is valid and not expired
- Verify Bearer token format: `Bearer YOUR_TOKEN`

### "Workflow not triggering"
- Make sure workflow is "Active" (toggle on)
- Check Gmail trigger is properly configured
- Verify email matches domain whitelist
- Check n8n is running (`n8n start`)

### "API call failed"
- Verify backend server is running
- Check API URL is correct (no trailing slash)
- Test API endpoint with curl first
- Check firewall/network connectivity

### "Label not found"
- Create label in Gmail first
- Use correct label ID or name
- Check Gmail credentials have permission

---

## 📊 Monitoring

### View Workflow Executions

1. Click "Executions" in n8n sidebar
2. See all workflow runs
3. Click any execution to see details
4. Green = success, Red = error

### Enable Error Notifications

1. Click workflow settings (gear icon)
2. Go to "Error Workflow"
3. Create error notification workflow
4. Gets triggered on any workflow error

---

## 🎉 You're Done!

Once both workflows are imported and configured:

✅ **Email Qualification** runs automatically on every new email
✅ **Daily Scheduler** sends follow-ups every weekday at 8 AM
✅ **Manual approval** required before any automation starts
✅ **Complete safety** with all stop conditions in place

**Next Steps:**
1. Send test email to verify qualification
2. Approve a test thread in RestorationOS UI
3. Wait for first automated follow-up (or test manually)
4. Monitor results in dashboard

---

## 📞 Need Help?

- **n8n Documentation:** https://docs.n8n.io/
- **n8n Community Forum:** https://community.n8n.io/
- **Gmail API Setup:** https://developers.google.com/gmail/api
- **RestorationOS Docs:** `/docs/ADJUSTER_FOLLOWUP_SYSTEM.md`

---

**Files Location:**
- Email Workflow: `/docs/n8n-adjuster-followup-workflow.json`
- Scheduler Workflow: `/docs/n8n-daily-scheduler-workflow.json`
- This Guide: `/docs/N8N_IMPORT_GUIDE.md`
