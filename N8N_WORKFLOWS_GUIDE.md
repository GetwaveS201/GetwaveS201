# N8N Workflow Files - Import Guide

## 📦 Files Included

1. **n8n-pro-followup-workflow.json** - PRO Follow-up Automation (13 nodes)
2. **n8n-email-intelligence-workflow.json** - Email Intelligence & Auto-Response (16 nodes)

These are the same workflows from the native RestorationOS system, but formatted for N8N import.

---

## 🚀 How to Import into N8N

### Step 1: Open N8N
```bash
# If running locally:
n8n start

# Or use cloud version: https://app.n8n.io
```

### Step 2: Import Workflow
1. Click **Workflows** in left sidebar
2. Click **Import from File** or **+ Add Workflow** → **Import from File**
3. Select the JSON file (e.g., `n8n-pro-followup-workflow.json`)
4. Click **Import**

### Step 3: Configure Credentials

You'll need to set up these credentials in N8N:

#### **MongoDB Connection**
1. Go to **Credentials** → **Add Credential**
2. Select **MongoDB**
3. Enter your connection details:
   - **Connection String**: Your MongoDB URL
   - **Database**: `restorationos` (or your DB name)

#### **OpenAI API**
1. Go to **Credentials** → **Add Credential**
2. Select **OpenAI**
3. Enter your **API Key**

#### **SMTP (Email)**
1. Go to **Credentials** → **Add Credential**
2. Select **SMTP**
3. Enter your email server details:
   - **Host**: smtp.gmail.com (or your SMTP server)
   - **Port**: 587
   - **User**: your-email@gmail.com
   - **Password**: your-password or app-specific password

### Step 4: Update Email Addresses
In each workflow, update these email addresses to match your setup:
- `owner@restoration.com` → Your owner's email
- `manager@restoration.com` → Your manager's email
- `support@restoration.com` → Your support email
- `alerts@restoration.com` → Your alerts email

### Step 5: Test the Workflow
1. Click **Execute Workflow** button
2. Watch nodes execute in real-time
3. Check results in each node
4. Verify emails were sent (check spam folder!)

### Step 6: Activate the Workflow
1. Toggle the **Active** switch at top-right
2. Workflow will now run on schedule automatically

---

## 📋 Workflow Details

### 1. PRO Follow-up Automation

**Schedule:** Daily at 9:00 AM

**What it does:**
1. ✅ Queries overdue invoices from MongoDB
2. ✅ Gets customer payment history
3. 🤖 **AI predicts payment likelihood** (GPT-4)
4. ✅ Calculates priority score (multi-dimensional)
5. ✅ Filters high-priority cases
6. 🤖 **AI generates personalized follow-up email**
7. ✅ Determines communication channel (urgent vs normal)
8. ✅ Sends follow-up email to customer
9. 🚨 Sends urgent alert to owner (if critical)
10. ✅ Logs interaction to database
11. 🔄 **Schedules next follow-up adaptively**
12. ✅ Logs execution metrics

**Key Features:**
- 🤖 **AI Payment Behavior Prediction** - Not just reminders!
- 🎯 **Multi-dimensional Priority Scoring** - Amount + days + likelihood
- 🔄 **Adaptive Scheduling** - Next follow-up based on AI predictions
- 📊 **Priority-based Routing** - Critical → owner alert, normal → email
- 📝 **Complete Tracking** - All interactions logged

**Credentials Needed:**
- MongoDB (read/write to `invoices`, `communications`, `workflow_logs`)
- OpenAI API (for GPT-4 predictions and email generation)
- SMTP (to send emails)

**To Customize:**
- Change schedule: Edit "Check Emails Every 15 Minutes" node → cron expression
- Change priority thresholds: Edit "Filter Actions Needed" node → conditions
- Change email templates: Edit "AI: Generate Personalized Follow-up" node → prompt

---

### 2. Email Intelligence & Auto-Response

**Schedule:** Every 15 minutes

**What it does:**
1. ✅ Queries unread emails from MongoDB
2. 🤖 **AI processes email** (intent, urgency, sentiment, entities)
3. 🤖 **Deep sentiment analysis** (emotions, churn risk, satisfaction)
4. 🤖 **Extracts actionable tasks** automatically
5. ⚠️ **Detects critical issues** (high churn risk or angry sentiment)
6. 🚨 Sends urgent alert to manager (if critical)
7. 📝 Routes to priority queue (if critical)
8. ✅ Creates work orders from extracted tasks
9. ✅ Checks if can auto-respond (simple + positive queries only)
10. 🤖 **Generates smart auto-reply** (context-aware)
11. ✅ Sends auto-response to customer
12. ✅ Logs all interactions

**Key Features:**
- 🤖 **Multi-dimensional Email Analysis** - Intent, sentiment, urgency, entities
- 😊 **Emotional Intelligence** - Detects emotions, frustration, satisfaction
- 🚨 **Churn Risk Detection** - Predicts at-risk customers (0-100 score)
- 📋 **Automatic Task Extraction** - Creates work orders from email content
- 🤖 **Context-aware Auto-responses** - Not templates, actual AI understanding
- ⚡ **Smart Routing** - Critical → manager, simple → auto-respond

**Credentials Needed:**
- MongoDB (read/write to `communications`, `work_orders`)
- OpenAI API (for email analysis, sentiment, task extraction, response generation)
- SMTP (to send auto-responses and alerts)

**To Customize:**
- Change check frequency: Edit "Check Emails Every 15 Minutes" → cron expression
- Change churn threshold: Edit "Detect Critical Issues" → conditions (default 70%)
- Change auto-respond criteria: Edit "Can Auto-Respond?" → conditions

---

## 🔧 Configuration Tips

### MongoDB Collections Required

Make sure these collections exist in your MongoDB:

```javascript
// For PRO Follow-up:
db.invoices
db.communications
db.workflow_logs

// For Email Intelligence:
db.communications
db.work_orders
```

### MongoDB Document Schema

**invoices:**
```json
{
  "invoice_id": "string",
  "customer_id": "string",
  "customer_name": "string",
  "customer_email": "string",
  "invoice_number": "string",
  "total": 5000.00,
  "status": "sent",
  "due_date": "2024-01-01",
  "paid": false,
  "job_id": "string"
}
```

**communications:**
```json
{
  "communication_id": "string",
  "type": "email",
  "direction": "inbound" | "outbound",
  "from": "email@example.com",
  "subject": "string",
  "body": "string",
  "processed": false,
  "timestamp": "ISO date"
}
```

### Environment Variables

If using N8N self-hosted, set these environment variables:

```bash
# MongoDB
MONGODB_URI=mongodb://localhost:27017/restorationos

# OpenAI
OPENAI_API_KEY=sk-...

# SMTP (Gmail example)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password
```

---

## 🎯 Testing Workflows

### Test PRO Follow-up:
1. Add a test invoice to MongoDB:
```javascript
db.invoices.insertOne({
  invoice_id: "TEST-001",
  customer_name: "Test Customer",
  customer_email: "test@example.com",
  invoice_number: "INV-TEST-001",
  total: 5000,
  status: "sent",
  due_date: new Date("2024-01-01"),
  paid: false,
  job_id: "JOB-TEST-001"
})
```

2. Click **Execute Workflow** in N8N
3. Watch AI predictions and email generation
4. Check your email for the follow-up

### Test Email Intelligence:
1. Add a test email to MongoDB:
```javascript
db.communications.insertOne({
  communication_id: "EMAIL-TEST-001",
  type: "email",
  direction: "inbound",
  from: "customer@example.com",
  subject: "When will my job be done?",
  body: "Hi, I'm wondering when you'll complete the water damage repair. It's been 3 days.",
  processed: false,
  timestamp: new Date()
})
```

2. Click **Execute Workflow** in N8N
3. Watch AI analyze sentiment and extract tasks
4. Check if auto-response was sent

---

## 🆚 N8N vs Native RestorationOS System

| Feature | N8N Version | Native RestorationOS | Winner |
|---------|-------------|----------------------|---------|
| **Setup** | Manual import + config | Built-in, zero setup | ✅ Native |
| **Speed** | ~2-5s per node | <100ms per node | ✅ Native |
| **Cost** | N8N license + API fees | $0 | ✅ Native |
| **Customization** | Visual editor | Full code access | ✅ Native |
| **Monitoring** | N8N dashboard | Custom analytics | 🤝 Tie |
| **AI Power** | Same (GPT-4) | Same (GPT-4) | 🤝 Tie |
| **Portability** | Export/import JSON | Database only | ✅ N8N |
| **Visual** | Drag-and-drop | Code-based | ✅ N8N |

**Recommendation:**
- Use **N8N** if you want visual workflow editing and easy export/import
- Use **Native RestorationOS** if you want 10x faster execution and $0 cost

---

## 🐛 Troubleshooting

### "MongoDB connection failed"
- Check your MongoDB connection string
- Verify database name is correct
- Test connection in MongoDB Compass

### "OpenAI API error"
- Verify your API key is valid
- Check you have credits/billing enabled
- Try using GPT-3.5 instead of GPT-4 (cheaper)

### "Email not sending"
- Check SMTP credentials
- Enable "Less secure apps" or use app-specific password
- Check spam folder
- Verify port (587 for TLS, 465 for SSL)

### "Workflow runs but does nothing"
- Check if you have test data in MongoDB
- Verify filters aren't too strict (e.g., priority_score >= 70)
- Check node execution logs for errors

### "AI predictions are weird"
- Verify input data format matches expected schema
- Check OpenAI API response in node output
- Try simplifying the prompt

---

## 💡 Optimization Tips

### Reduce API Costs
1. **Use GPT-3.5 instead of GPT-4** (10x cheaper)
   - Change: `"model": "gpt-4"` → `"model": "gpt-3.5-turbo"`
2. **Cache AI results** - Add a check if email already analyzed
3. **Batch processing** - Process multiple emails at once
4. **Reduce check frequency** - Change from 15min to 30min or hourly

### Improve Performance
1. **Add MongoDB indexes**:
   ```javascript
   db.invoices.createIndex({ "paid": 1, "due_date": 1 })
   db.communications.createIndex({ "processed": 1, "type": 1 })
   ```
2. **Limit query results** - Don't fetch more than 50-100 at once
3. **Use webhook triggers** instead of schedule (if possible)

### Scale Up
1. **Multiple workflows** - Create separate workflows per customer segment
2. **Parallel execution** - Enable parallel processing in N8N settings
3. **Queue system** - Use N8N's built-in queue mode for reliability

---

## 📈 Success Metrics to Track

In N8N, you can track:

1. **Execution Stats**
   - Total executions
   - Success rate
   - Average execution time
   - Failed executions

2. **Business Metrics** (add these to workflow)
   - Emails sent per day
   - High-priority cases detected
   - Auto-response rate
   - Tasks created automatically
   - Churn risk alerts sent

3. **AI Metrics**
   - Average payment likelihood score
   - Average churn risk score
   - Sentiment distribution (positive/neutral/negative)
   - Auto-response accuracy (track feedback)

---

## 🎉 Next Steps

1. **Import both workflows** into N8N
2. **Configure credentials** (MongoDB, OpenAI, SMTP)
3. **Update email addresses** to your actual addresses
4. **Add test data** to MongoDB
5. **Run test executions** to verify everything works
6. **Activate workflows** to run on schedule
7. **Monitor results** in N8N dashboard
8. **Iterate and improve** based on results

---

## 📚 Additional Resources

- **N8N Documentation**: https://docs.n8n.io
- **OpenAI API Docs**: https://platform.openai.com/docs
- **MongoDB Docs**: https://www.mongodb.com/docs
- **RestorationOS Native System**: See `WORKFLOW_AUTOMATION.md`

---

## 🤝 Support

If you have issues with these N8N workflows:

1. Check the troubleshooting section above
2. Review N8N execution logs
3. Test each node individually
4. Verify your credentials are correct
5. Check MongoDB has the required data

For RestorationOS-specific questions, see the native workflow documentation.

---

**Note:** These N8N workflows replicate the functionality of the native RestorationOS workflow system, but run ~10-50x slower due to external API calls. For production use at scale, consider using the native RestorationOS system which has:
- Direct database access (no API latency)
- Async/queue-based execution
- $0 per-operation cost
- Built-in monitoring
- 10x faster performance

But N8N is great for:
- Visual workflow editing
- Quick prototyping
- Non-technical users
- Multi-platform integration
- Easy export/import

Choose the right tool for your needs! 🚀
