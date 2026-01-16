# ⚡ Quick Start - Native Workflow Automation

## 🎯 3 Simple Steps to Run Your First Workflow

---

## Step 1: Start the Server

```bash
cd /home/user/GetwaveS201
./start-workflows.sh
```

**Wait for:** "Application startup complete"

---

## Step 2: Open the API Docs

Open your browser to:
```
http://localhost:8000/docs
```

You'll see the Swagger UI with all API endpoints.

---

## Step 3: Install and Run a Template

### Option A: Using the API (Swagger UI)

1. **Login first:**
   - Find `POST /api/auth/login`
   - Click "Try it out"
   - Use your RestorationOS credentials
   - Copy the `access_token`

2. **Authorize:**
   - Click the 🔒 "Authorize" button at top-right
   - Paste: `Bearer YOUR_ACCESS_TOKEN`
   - Click "Authorize"

3. **List Templates:**
   - Find `GET /api/workflows/templates/list`
   - Click "Try it out" → "Execute"
   - You'll see 4 templates:
     - `pro_followup`
     - `email_intelligence`
     - `adjuster_management`
     - `daily_summary`

4. **Install a Template:**
   - Find `POST /api/workflows/templates/{template_id}/install`
   - Click "Try it out"
   - Enter template_id: `pro_followup`
   - Request body:
     ```json
     {
       "template_id": "pro_followup",
       "customizations": {}
     }
     ```
   - Click "Execute"
   - Copy the `workflow_id` from response

5. **Run the Workflow:**
   - Find `POST /api/workflows/{workflow_id}/execute`
   - Click "Try it out"
   - Enter your `workflow_id`
   - Request body:
     ```json
     {
       "trigger_data": {}
     }
     ```
   - Click "Execute"

6. **Check Execution:**
   - Find `GET /api/workflows/{workflow_id}/executions`
   - Click "Try it out"
   - Enter your `workflow_id`
   - Click "Execute"
   - See your workflow execution!

---

### Option B: Using cURL (Command Line)

```bash
# 1. Login
TOKEN=$(curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"your@email.com","password":"yourpassword"}' \
  | jq -r '.access_token')

# 2. List Templates
curl http://localhost:8000/api/workflows/templates/list \
  -H "Authorization: Bearer $TOKEN"

# 3. Install PRO Follow-up Template
WORKFLOW_ID=$(curl -X POST http://localhost:8000/api/workflows/templates/pro_followup/install \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"template_id":"pro_followup","customizations":{}}' \
  | jq -r '.workflow_id')

# 4. Run the Workflow
curl -X POST http://localhost:8000/api/workflows/$WORKFLOW_ID/execute \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"trigger_data":{}}'

# 5. Check Executions
curl http://localhost:8000/api/workflows/$WORKFLOW_ID/executions \
  -H "Authorization: Bearer $TOKEN"
```

---

### Option C: Using Python

```python
import requests

# 1. Login
response = requests.post('http://localhost:8000/api/auth/login', json={
    'email': 'your@email.com',
    'password': 'yourpassword'
})
token = response.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# 2. List Templates
templates = requests.get('http://localhost:8000/api/workflows/templates/list',
                        headers=headers).json()
print("Available templates:", templates)

# 3. Install PRO Follow-up
workflow = requests.post(
    'http://localhost:8000/api/workflows/templates/pro_followup/install',
    headers=headers,
    json={'template_id': 'pro_followup', 'customizations': {}}
).json()
workflow_id = workflow['workflow_id']
print(f"Installed workflow: {workflow_id}")

# 4. Run the Workflow
execution = requests.post(
    f'http://localhost:8000/api/workflows/{workflow_id}/execute',
    headers=headers,
    json={'trigger_data': {}}
).json()
print(f"Execution started: {execution['execution_id']}")

# 5. Check Status
executions = requests.get(
    f'http://localhost:8000/api/workflows/{workflow_id}/executions',
    headers=headers
).json()
print("Executions:", executions)
```

---

## 🎨 With Frontend UI

If you have the React frontend running:

1. **Start Frontend:**
   ```bash
   cd /home/user/GetwaveS201/frontend
   npm start
   ```

2. **Open Browser:**
   ```
   http://localhost:3000
   ```

3. **Navigate to Workflow Automation**
   - Find "Workflow Automation" in the menu
   - Or go directly to: `http://localhost:3000/workflows`

4. **Use the Visual Interface:**
   - 📋 **Workflows Tab**: See all your workflows
   - 📦 **Templates Tab**: Browse and install templates
   - 🔄 **Executions Tab**: Monitor real-time execution
   - 📊 **Analytics Tab**: View success rates and metrics

5. **Install Template (Visual):**
   - Click **Templates** tab
   - Click **Install Template** on "PRO Follow-up Automation"
   - Done!

6. **Run Workflow (Visual):**
   - Click **Workflows** tab
   - Find your workflow
   - Click **Run** button
   - See it execute in real-time!

---

## 🧪 Test with Sample Data

### Add Test Invoice:
```javascript
// Connect to MongoDB and run:
db.invoices.insertOne({
  invoice_id: "TEST-001",
  customer_name: "John Doe",
  customer_email: "john@example.com",
  invoice_number: "INV-TEST-001",
  total: 5000,
  status: "sent",
  due_date: new Date("2024-01-01"),
  paid: false,
  job_id: "JOB-001",
  customer_id: "CUST-001"
})
```

### Add Test Email:
```javascript
db.communications.insertOne({
  communication_id: "EMAIL-001",
  type: "email",
  direction: "inbound",
  from: "customer@example.com",
  subject: "When will my job be done?",
  body: "I'm wondering when you'll complete my restoration. It's been 3 days.",
  processed: false,
  timestamp: new Date()
})
```

Now run your workflows and see them process this data!

---

## 🔑 Required Environment Variables

Create `.env` file in `/home/user/GetwaveS201/backend/`:

```bash
# MongoDB
MONGO_URL=mongodb://localhost:27017
DB_NAME=restorationos

# JWT
JWT_SECRET=your-super-secret-key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# AI APIs (for AI features)
OPENAI_API_KEY=sk-your-openai-key
GOOGLE_API_KEY=your-google-gemini-key

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8000
```

**Note:** Workflows will run without AI keys, but AI nodes will be skipped.

---

## ✅ Verify It's Working

### Check Server Health:
```bash
curl http://localhost:8000/api/health
```

Should return: `{"status":"healthy","timestamp":"..."}`

### List Available Endpoints:
Open: http://localhost:8000/docs

You should see:
- ✅ `/api/workflows` - Workflow CRUD
- ✅ `/api/workflows/templates/list` - Templates
- ✅ `/api/workflows/{id}/execute` - Execute
- ✅ `/api/workflows/analytics/overview` - Analytics

---

## 🎉 You're Done!

Your native workflow automation system is now running!

**Next Steps:**
1. Install all 4 templates
2. Add test data to MongoDB
3. Run workflows and see the magic
4. Check execution logs
5. View analytics

**Need help?** See `WORKFLOW_AUTOMATION.md` for full documentation.

---

## 🐛 Troubleshooting

### Server won't start?
```bash
# Check if port 8000 is already in use
lsof -i :8000

# Kill existing process
kill -9 $(lsof -t -i:8000)

# Try again
./start-workflows.sh
```

### "MongoDB connection failed"?
```bash
# Check MongoDB is running
mongosh --eval "db.serverStatus()"

# Or install MongoDB:
# macOS: brew install mongodb-community
# Ubuntu: sudo apt install mongodb
# Start: mongod --dbpath /path/to/data
```

### "Authentication failed"?
```bash
# Create a test user first
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"test123","name":"Test User","role":"admin"}'
```

### AI features not working?
- Add `OPENAI_API_KEY` to `.env`
- Get key from: https://platform.openai.com/api-keys
- Workflows will still run, AI nodes will be skipped if no key

---

**That's it! Super simple.** 🚀
