# Automation Platform Integration Guide
## Email Automation for Adjuster Follow-Ups

This guide shows how to integrate Gmail/Outlook with RestorationOS's adjuster follow-up system using n8n, Make (Integromat), or Zapier.

---

## Table of Contents

1. [Gmail Integration with n8n](#gmail-integration-with-n8n)
2. [Outlook Integration with n8n](#outlook-integration-with-n8n)
3. [Make (Integromat) Integration](#make-integromat-integration)
4. [Zapier Integration](#zapier-integration)
5. [Cron Job Setup](#cron-job-setup)
6. [Testing & Validation](#testing--validation)

---

## Gmail Integration with n8n

### Overview
This workflow automatically qualifies incoming Gmail emails and adds them to the approval queue.

### Workflow Steps

```
Gmail Trigger (New Email)
    ↓
Filter: Check sender domain
    ↓
Filter: Check for billing keywords
    ↓
HTTP Request: Qualify email
    ↓
If qualified → HTTP Request: Create follow-up thread
    ↓
Gmail: Apply label "Needs Approval"
```

### n8n Workflow JSON

```json
{
  "name": "Gmail Adjuster Follow-Up Qualification",
  "nodes": [
    {
      "name": "Gmail Trigger",
      "type": "n8n-nodes-base.gmailTrigger",
      "position": [250, 300],
      "parameters": {
        "triggerOn": "messageReceived",
        "filters": {
          "includeSpamTrash": false
        }
      },
      "credentials": {
        "gmailOAuth2": {
          "id": "1",
          "name": "Gmail account"
        }
      }
    },
    {
      "name": "Extract Email Data",
      "type": "n8n-nodes-base.set",
      "position": [450, 300],
      "parameters": {
        "values": {
          "string": [
            {
              "name": "sender_email",
              "value": "={{$json.payload.headers.find(h => h.name === 'From').value.match(/<(.+)>/)?.[1] || $json.payload.headers.find(h => h.name === 'From').value}}"
            },
            {
              "name": "sender_domain",
              "value": "={{$node['Extract Email Data'].json.sender_email.split('@')[1].toLowerCase()}}"
            },
            {
              "name": "subject",
              "value": "={{$json.payload.headers.find(h => h.name === 'Subject').value}}"
            },
            {
              "name": "message_id",
              "value": "={{$json.payload.headers.find(h => h.name === 'Message-ID').value}}"
            },
            {
              "name": "thread_id",
              "value": "={{$json.threadId}}"
            },
            {
              "name": "body",
              "value": "={{$json.snippet}}"
            }
          ]
        }
      }
    },
    {
      "name": "Qualify Email",
      "type": "n8n-nodes-base.httpRequest",
      "position": [650, 300],
      "parameters": {
        "method": "POST",
        "url": "https://your-api.restorationos.com/api/adjuster-followups/qualify",
        "authentication": "genericCredentialType",
        "genericAuthType": "httpHeaderAuth",
        "sendBody": true,
        "bodyParameters": {
          "parameters": [
            {
              "name": "sender_email",
              "value": "={{$json.sender_email}}"
            },
            {
              "name": "sender_domain",
              "value": "={{$json.sender_domain}}"
            },
            {
              "name": "email_subject",
              "value": "={{$json.subject}}"
            },
            {
              "name": "email_body",
              "value": "={{$json.body}}"
            },
            {
              "name": "recipients_to",
              "value": "=['your-email@company.com']"
            },
            {
              "name": "recipients_cc",
              "value": "=[]"
            },
            {
              "name": "message_id",
              "value": "={{$json.message_id}}"
            },
            {
              "name": "thread_id",
              "value": "={{$json.thread_id}}"
            },
            {
              "name": "is_auto_reply",
              "value": "=false"
            }
          ]
        }
      },
      "credentials": {
        "httpHeaderAuth": {
          "id": "2",
          "name": "RestorationOS API"
        }
      }
    },
    {
      "name": "Check if Qualified",
      "type": "n8n-nodes-base.if",
      "position": [850, 300],
      "parameters": {
        "conditions": {
          "boolean": [
            {
              "value1": "={{$json.qualified}}",
              "value2": true
            }
          ]
        }
      }
    },
    {
      "name": "Apply Label - Needs Approval",
      "type": "n8n-nodes-base.gmail",
      "position": [1050, 250],
      "parameters": {
        "operation": "addLabels",
        "messageId": "={{$node['Gmail Trigger'].json.id}}",
        "labelIds": ["Label_ApprovalNeeded"]
      },
      "credentials": {
        "gmailOAuth2": {
          "id": "1",
          "name": "Gmail account"
        }
      }
    },
    {
      "name": "Log Rejected Email",
      "type": "n8n-nodes-base.set",
      "position": [1050, 400],
      "parameters": {
        "values": {
          "string": [
            {
              "name": "reason",
              "value": "={{$node['Qualify Email'].json.reason}}"
            }
          ]
        }
      }
    }
  ],
  "connections": {
    "Gmail Trigger": {
      "main": [[{ "node": "Extract Email Data", "type": "main", "index": 0 }]]
    },
    "Extract Email Data": {
      "main": [[{ "node": "Qualify Email", "type": "main", "index": 0 }]]
    },
    "Qualify Email": {
      "main": [[{ "node": "Check if Qualified", "type": "main", "index": 0 }]]
    },
    "Check if Qualified": {
      "main": [
        [{ "node": "Apply Label - Needs Approval", "type": "main", "index": 0 }],
        [{ "node": "Log Rejected Email", "type": "main", "index": 0 }]
      ]
    }
  }
}
```

### Setup Instructions

1. **Install n8n** (if not already):
   ```bash
   npm install n8n -g
   n8n start
   ```

2. **Create Gmail OAuth2 Credentials**:
   - Go to n8n Credentials
   - Add new credential: Gmail OAuth2 API
   - Follow Google OAuth flow to authenticate

3. **Create API Authentication**:
   - Credential type: Header Auth
   - Header name: `Authorization`
   - Header value: `Bearer YOUR_JWT_TOKEN`

4. **Create "Needs Approval" Label in Gmail**:
   - Open Gmail
   - Create new label: "Adjuster Follow-Up - Needs Approval"
   - Note the label ID

5. **Import Workflow**:
   - Copy the JSON above
   - In n8n, click "Import from File" or paste JSON
   - Update URLs and credentials

6. **Activate Workflow**:
   - Click "Active" toggle
   - Test with a sample email

---

## Outlook Integration with n8n

### Workflow Steps

```
Outlook Trigger (New Email)
    ↓
Extract sender and content
    ↓
HTTP Request: Qualify email
    ↓
If qualified → Apply Outlook category
```

### n8n Workflow for Outlook

```json
{
  "name": "Outlook Adjuster Follow-Up Qualification",
  "nodes": [
    {
      "name": "Outlook Trigger",
      "type": "n8n-nodes-base.microsoftOutlookTrigger",
      "position": [250, 300],
      "parameters": {
        "resource": "message",
        "operation": "messageReceived"
      },
      "credentials": {
        "microsoftOutlookOAuth2Api": {
          "id": "3",
          "name": "Outlook account"
        }
      }
    },
    {
      "name": "Extract Email Data",
      "type": "n8n-nodes-base.set",
      "position": [450, 300],
      "parameters": {
        "values": {
          "string": [
            {
              "name": "sender_email",
              "value": "={{$json.from.emailAddress.address}}"
            },
            {
              "name": "sender_domain",
              "value": "={{$json.from.emailAddress.address.split('@')[1].toLowerCase()}}"
            },
            {
              "name": "subject",
              "value": "={{$json.subject}}"
            },
            {
              "name": "body",
              "value": "={{$json.bodyPreview}}"
            },
            {
              "name": "message_id",
              "value": "={{$json.id}}"
            },
            {
              "name": "thread_id",
              "value": "={{$json.conversationId}}"
            }
          ]
        }
      }
    },
    {
      "name": "Qualify Email",
      "type": "n8n-nodes-base.httpRequest",
      "position": [650, 300],
      "parameters": {
        "method": "POST",
        "url": "https://your-api.restorationos.com/api/adjuster-followups/qualify",
        "authentication": "genericCredentialType",
        "genericAuthType": "httpHeaderAuth",
        "sendBody": true,
        "bodyParameters": {
          "parameters": [
            {
              "name": "sender_email",
              "value": "={{$json.sender_email}}"
            },
            {
              "name": "sender_domain",
              "value": "={{$json.sender_domain}}"
            },
            {
              "name": "email_subject",
              "value": "={{$json.subject}}"
            },
            {
              "name": "email_body",
              "value": "={{$json.body}}"
            },
            {
              "name": "message_id",
              "value": "={{$json.message_id}}"
            },
            {
              "name": "thread_id",
              "value": "={{$json.thread_id}}"
            }
          ]
        }
      }
    },
    {
      "name": "Check if Qualified",
      "type": "n8n-nodes-base.if",
      "position": [850, 300],
      "parameters": {
        "conditions": {
          "boolean": [
            {
              "value1": "={{$json.qualified}}",
              "value2": true
            }
          ]
        }
      }
    },
    {
      "name": "Apply Category",
      "type": "n8n-nodes-base.microsoftOutlook",
      "position": [1050, 250],
      "parameters": {
        "resource": "message",
        "operation": "update",
        "messageId": "={{$node['Outlook Trigger'].json.id}}",
        "updateFields": {
          "categories": ["Adjuster Follow-Up"]
        }
      }
    }
  ]
}
```

---

## Make (Integromat) Integration

### Scenario Structure

**Modules:**
1. Gmail/Outlook: Watch Emails
2. Router: Split based on sender domain
3. Filter: Check for billing keywords
4. HTTP: Call qualification API
5. Condition: Check if qualified
6. Gmail/Outlook: Apply label/category

### Make Scenario Setup

```
[Gmail] Watch Emails
    ↓
[Router] Branch 1: Insurance Carriers
         Branch 2: TPAs
         Branch 3: Adjuster Firms
    ↓
[Filter] Contains billing keywords
    ↓
[HTTP] POST to /api/adjuster-followups/qualify
    ↓
[Filter] qualified = true
    ↓
[Gmail] Add Label "Needs Approval"
```

### HTTP Module Configuration

**URL:** `https://your-api.restorationos.com/api/adjuster-followups/qualify`

**Method:** POST

**Headers:**
- Authorization: `Bearer YOUR_JWT_TOKEN`
- Content-Type: `application/json`

**Body:**
```json
{
  "sender_email": "{{from.address}}",
  "sender_domain": "{{split(from.address; "@")[2]}}",
  "email_subject": "{{subject}}",
  "email_body": "{{text}}",
  "recipients_to": ["{{to[].address}}"],
  "recipients_cc": ["{{cc[].address}}"],
  "message_id": "{{id}}",
  "thread_id": "{{threadId}}",
  "is_auto_reply": false
}
```

### Filter Module Configuration

**Condition:** `{{qualified}}` equals `true`

---

## Zapier Integration

### Zap Structure

```
Trigger: Gmail - New Email Matching Search
    ↓
Filter: Only continue if sender domain matches list
    ↓
Code: Extract domain and check keywords
    ↓
Webhooks: POST to qualification API
    ↓
Filter: Only continue if qualified = true
    ↓
Gmail: Add Label to Email
```

### Zapier Setup Steps

1. **Trigger: Gmail - New Email Matching Search**
   - Search String: Leave blank or use: `from:(*@allstate.com OR *@statefarm.com OR *@progressive.com)`

2. **Filter by Zapier**
   - Continue only if:
   - (From Email) Contains `@allstate.com`
   - OR (From Email) Contains `@statefarm.com`
   - (Add all qualified domains...)

3. **Code by Zapier** (Python)
   ```python
   import re

   def extract_domain(email):
       return email.split('@')[-1].lower()

   def contains_keywords(text):
       keywords = ['invoice', 'payment', 'billing', 'mitigation', 'estimate', 'scope', 'supplement', 'approval']
       text_lower = text.lower()
       return any(keyword in text_lower for keyword in keywords)

   sender = input_data.get('from')
   subject = input_data.get('subject', '')
   body = input_data.get('body', '')

   domain = extract_domain(sender)
   has_keywords = contains_keywords(subject + ' ' + body)

   return {
       'sender_domain': domain,
       'has_keywords': has_keywords
   }
   ```

4. **Webhooks by Zapier: POST**
   - URL: `https://your-api.restorationos.com/api/adjuster-followups/qualify`
   - Payload Type: JSON
   - Headers:
     - Authorization: `Bearer YOUR_JWT_TOKEN`
   - Data:
     ```json
     {
       "sender_email": "{{from}}",
       "sender_domain": "{{sender_domain}}",
       "email_subject": "{{subject}}",
       "email_body": "{{body}}",
       "recipients_to": ["{{to}}"],
       "message_id": "{{id}}",
       "thread_id": "{{thread_id}}"
     }
     ```

5. **Filter by Zapier**
   - Continue only if:
   - (Qualified from Webhooks) Equals `true`

6. **Gmail: Add Label to Email**
   - Label: "Adjuster Follow-Up - Needs Approval"
   - Message ID: `{{id}}`

---

## Cron Job Setup

### Automated Daily Follow-Up Scheduler

The scheduler runs automatically every business day at 8 AM to process all approved threads.

### Linux Cron Job

```bash
# Edit crontab
crontab -e

# Add this line to run daily at 8 AM (Monday-Friday)
0 8 * * 1-5 curl -X POST https://your-api.restorationos.com/api/adjuster-followups/run-scheduler -H "Authorization: Bearer YOUR_SERVICE_ACCOUNT_JWT" >> /var/log/adjuster-scheduler.log 2>&1
```

### n8n Scheduler Workflow

```json
{
  "name": "Daily Adjuster Follow-Up Scheduler",
  "nodes": [
    {
      "name": "Schedule Trigger",
      "type": "n8n-nodes-base.cron",
      "position": [250, 300],
      "parameters": {
        "triggerTimes": {
          "item": [
            {
              "hour": 8,
              "minute": 0,
              "dayOfWeek": [1, 2, 3, 4, 5]
            }
          ]
        }
      }
    },
    {
      "name": "Run Scheduler",
      "type": "n8n-nodes-base.httpRequest",
      "position": [450, 300],
      "parameters": {
        "method": "POST",
        "url": "https://your-api.restorationos.com/api/adjuster-followups/run-scheduler",
        "authentication": "genericCredentialType",
        "genericAuthType": "httpHeaderAuth"
      },
      "credentials": {
        "httpHeaderAuth": {
          "id": "2",
          "name": "RestorationOS API"
        }
      }
    },
    {
      "name": "Log Results",
      "type": "n8n-nodes-base.set",
      "position": [650, 300],
      "parameters": {
        "values": {
          "string": [
            {
              "name": "processed_at",
              "value": "={{$json.processed_at}}"
            },
            {
              "name": "total_sent",
              "value": "={{$json.results.filter(r => r.status === 'sent').length}}"
            },
            {
              "name": "total_skipped",
              "value": "={{$json.results.filter(r => r.status === 'skipped').length}}"
            }
          ]
        }
      }
    }
  ]
}
```

### Make Scenario (Daily Scheduler)

1. **Schedule Module**: Every day at 8:00 AM (weekdays only)
2. **HTTP Module**: POST to `/api/adjuster-followups/run-scheduler`
3. **Email Module**: Send summary report to team

### Zapier Schedule

1. **Trigger: Schedule by Zapier**
   - Frequency: Daily
   - Time of Day: 8:00 AM
   - Days: Weekdays only

2. **Webhooks: POST**
   - URL: `https://your-api.restorationos.com/api/adjuster-followups/run-scheduler`

3. **Email by Zapier** (Optional)
   - Send daily summary to management

---

## Testing & Validation

### Test Email Qualification

```bash
curl -X POST https://your-api.restorationos.com/api/adjuster-followups/qualify \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "sender_email": "john.adjuster@allstate.com",
    "sender_domain": "allstate.com",
    "email_subject": "RE: Invoice #12345 - Payment Status",
    "email_body": "We need additional documentation for this claim.",
    "recipients_to": ["billing@yourcompany.com"],
    "recipients_cc": [],
    "message_id": "test-message-123",
    "thread_id": "test-thread-abc",
    "is_auto_reply": false
  }'
```

**Expected Response:**
```json
{
  "qualified": true,
  "reason": "Email qualified for follow-up - requires manual approval",
  "domain_match": true,
  "keyword_match": true,
  "message_type_valid": true,
  "requires_approval": true
}
```

### Test Scheduler

```bash
curl -X POST https://your-api.restorationos.com/api/adjuster-followups/run-scheduler \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Expected Response:**
```json
{
  "processed_at": "2026-01-15T08:00:00.000Z",
  "total_threads": 5,
  "results": [
    {
      "thread_id": "uuid-123",
      "status": "sent",
      "followup_number": 2
    },
    {
      "thread_id": "uuid-456",
      "status": "skipped",
      "reason": "Only 1 days since last follow-up (minimum 3 required)"
    }
  ]
}
```

### Validation Checklist

- [ ] Email qualification correctly identifies carrier/TPA domains
- [ ] Billing keywords are detected in subject and body
- [ ] Auto-replies are filtered out
- [ ] CC-only emails are excluded
- [ ] Qualified emails appear in approval queue
- [ ] Gmail label/Outlook category is applied
- [ ] Daily scheduler runs at correct time
- [ ] Business day calculation skips weekends
- [ ] Stop conditions prevent over-automation
- [ ] Max follow-ups (10) trigger internal escalation

---

## Environment Variables

Add these to your `.env` file:

```env
# API URL
API_BASE_URL=https://your-api.restorationos.com

# Email Service
SMTP_FROM_EMAIL=billing@yourcompany.com
COMPANY_NAME=Your Restoration Company
COMPANY_PHONE=555-123-4567

# Optional: SendGrid
SENDGRID_API_KEY=your_sendgrid_key

# Optional: Mailgun
MAILGUN_API_KEY=your_mailgun_key
MAILGUN_DOMAIN=mg.yourcompany.com
```

---

## Troubleshooting

### Email not qualifying

1. Check sender domain against qualified list
2. Verify email contains billing keywords
3. Ensure email is direct (TO: field, not CC-only)
4. Check for auto-reply headers

### Scheduler not sending

1. Verify cron job is running (`crontab -l`)
2. Check business day logic (may be weekend/holiday)
3. Ensure threads are approved (`approval_status = "approved"`)
4. Verify 3-day interval since last follow-up

### Email delivery failing

1. Check SMTP credentials
2. Verify SendGrid/Mailgun API keys
3. Review email service logs
4. Test with manual send endpoint

---

## Next Steps

1. Set up email automation platform (n8n/Make/Zapier)
2. Configure email credentials (Gmail/Outlook OAuth)
3. Import workflow template
4. Test with sample emails
5. Set up daily scheduler cron job
6. Monitor approval queue
7. Train team on approval process

---

**Last Updated:** 2026-01-15
**Version:** 1.0
