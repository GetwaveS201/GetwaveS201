# Insurance Adjuster Follow-Up Automation System

## Overview

This system automates follow-ups with insurance adjusters while maintaining strict control, progressive pressure, and cash flow protection. It integrates with RestorationOS's existing communication logging and invoice tracking.

## System Architecture

```
Email Inbox (Gmail/Outlook)
    ↓
Email Qualification Filter
    ↓
Manual Approval Queue
    ↓
Follow-Up Scheduler (3-day business cycles)
    ↓
Progressive Escalation Engine
    ↓
Stop Condition Monitor
    ↓
Automated Email Sender
```

## Email Qualification Decision Tree

### Level 1: Domain Verification
```
IS sender domain one of:
  - Insurance carrier (@allstate.com, @statefarm.com, @progressive.com, etc.)
  - TPA (@crawco.com, @sedgwick.com, @gallagherbasset.com, etc.)
  - Adjuster firm (@eberl.com, @enservio.com, etc.)

YES → Proceed to Level 2
NO  → REJECT (Log as non-qualifying)
```

### Level 2: Content Analysis
```
DOES email body contain at least ONE keyword:
  - invoice
  - payment
  - billing
  - mitigation
  - estimate
  - scope
  - supplement
  - approval

YES → Proceed to Level 3
NO  → REJECT (Log as non-billable)
```

### Level 3: Message Type Filter
```
IS email:
  ✓ Direct to business (TO: field, not CC-only)
  ✓ From human (not auto-reply/OOO)
  ✓ External (not internal team)
  ✓ Not marketing/newsletter

YES to ALL → Proceed to Level 4
NO to ANY  → REJECT (Log as excluded type)
```

### Level 4: Manual Approval Gate
```
HAS user applied approval marker:
  - Gmail label: "Approved for Follow-Up"
  - Outlook category: "Adjuster Follow-Up"
  - Database flag: approved_for_followup = true
  - Spreadsheet checkbox: TRUE

YES → APPROVED (Enter follow-up queue)
NO  → PENDING (Wait in approval queue)
```

## Data Structure

### AdjusterFollowUpThread Collection (MongoDB)

```python
{
  "_id": ObjectId,
  "email_message_id": str,          # Gmail/Outlook message ID
  "thread_id": str,                  # Email thread ID
  "job_id": ObjectId,                # Link to restoration job
  "invoice_id": ObjectId,            # Link to invoice
  "claim_number": str,
  "adjuster_name": str,
  "adjuster_email": str,
  "carrier_name": str,
  "invoice_number": str,
  "invoice_amount": float,
  "invoice_due_date": datetime,
  "first_contact_date": datetime,
  "last_followup_date": datetime,
  "followup_count": int,
  "days_outstanding": int,
  "status": str,                     # active, paused, paid, escalated, disputed
  "approval_status": str,            # pending, approved, rejected
  "approved_by": ObjectId,           # User who approved
  "approved_at": datetime,
  "stop_reason": str,                # payment_received, coverage_issued, disputed, manual_pause
  "escalation_notes": [
    {
      "date": datetime,
      "followup_number": int,
      "days_since_first_contact": int,
      "days_past_due": int,
      "email_sent": bool,
      "email_sent_at": datetime
    }
  ],
  "created_at": datetime,
  "updated_at": datetime
}
```

### Follow-Up Status Values

| Status | Meaning | Action |
|--------|---------|--------|
| `pending_approval` | Qualified email awaiting manual approval | Show in approval queue |
| `active` | Approved and actively following up | Send scheduled follow-ups |
| `paused` | Manually paused by user | Skip all automation |
| `paid` | Payment received | STOP permanently |
| `coverage_issued` | Formal position received | STOP permanently |
| `disputed` | Adjuster contested scope | STOP permanently |
| `escalated_internal` | Moved to management | STOP automation, manual handling |

## Follow-Up Schedule Logic

### Business Day Calculator
```python
def next_business_day(start_date, days_to_add=3):
    """
    Skip weekends and US holidays:
    - New Year's Day
    - Memorial Day (last Monday in May)
    - Independence Day (July 4)
    - Labor Day (first Monday in September)
    - Thanksgiving (4th Thursday in November)
    - Christmas (December 25)
    """
    current = start_date
    days_added = 0

    while days_added < days_to_add:
        current += timedelta(days=1)
        if is_business_day(current):
            days_added += 1

    return current
```

### Follow-Up Cadence

| Follow-Up | Timing | Days Since First | Escalation Level |
|-----------|--------|-----------------|------------------|
| #1 | Day 3 (business days) | 3 | Gentle reminder |
| #2 | Day 6 | 6 | Professional nudge |
| #3 | Day 9 | 9 | Accountability focus |
| #4 | Day 12 | 12 | Escalation implied |
| #5 | Day 15 | 15 | Supervisory review hinted |
| #6+ | Every 3 business days | Continues | Maximum pressure maintained |

## Unified Escalation Message Template

### Email Structure
```
Subject: Claim Billing Status Required – Invoice #{{invoice_number}}

Hello {{adjuster_name}},

We are following up regarding the invoice referenced below.

Services were completed and invoiced {{days_since_first_contact}} days ago, and this account remains open with no payment or formal coverage position issued. Multiple follow-ups have been sent without response, and we need clear direction to close this file.

{{#if days_past_due}}
This invoice is now {{days_past_due}} days past due.
{{/if}}

If additional documentation is required, please advise immediately. If the file requires reassignment or supervisory review, please confirm so we can coordinate accordingly.

Absent a response, this matter will be escalated internally to ensure timely resolution. Our preference is to resolve this directly and close the claim professionally.

Please confirm status or next steps by end of business day.

Thank you,
{{user_name}}
{{company_name}}
{{user_phone}}

---
Reference Information:
Claim #: {{claim_number}}
Invoice #: {{invoice_number}}
Invoice Amount: ${{invoice_amount}}
Invoice Date: {{invoice_date}}
Service Address: {{service_address}}
Loss Type: {{loss_type}}
```

### Progressive Pressure Mechanics

**Same Message, Different Weight:**
- Follow-up #1: Reads as "just checking in"
- Follow-up #3: Reads as "need response"
- Follow-up #5: Reads as "escalation imminent"
- Follow-up #7: Reads as "final notice"

The key is that the **recipient's guilt** increases with each identical message, not the message itself.

## Stop Conditions (CRITICAL)

### Automatic Stop Triggers

1. **Payment Received**
   - Detection: Payment logged in invoice payments
   - Action: Set status to `paid`, stop all automation
   - Notification: Send final thank you email

2. **Coverage Position Issued**
   - Detection: Communication log with type "coverage_position"
   - Action: Set status to `coverage_issued`, stop automation
   - Notification: Internal alert for review

3. **Dispute Flagged**
   - Detection: Email reply contains keywords: "dispute", "disagree", "incorrect", "not covered"
   - Action: Set status to `disputed`, stop automation
   - Notification: Urgent alert to user

4. **Manual Pause**
   - Detection: User clicks "Pause Follow-Ups" button
   - Action: Set status to `paused`, skip automation
   - Resume: User must manually reactivate

5. **Max Follow-Ups Reached**
   - Detection: followup_count >= 10 (30 business days)
   - Action: Set status to `escalated_internal`, notify management
   - Manual Review: Required before resuming

### Safety Mechanisms

```python
def should_send_followup(thread):
    """
    Returns False if ANY condition is true:
    """
    # Stop conditions
    if thread.status in ['paid', 'coverage_issued', 'disputed', 'paused']:
        return False

    # Not yet approved
    if thread.approval_status != 'approved':
        return False

    # Too soon since last followup
    if (datetime.now() - thread.last_followup_date).days < 3:
        return False

    # Max attempts reached
    if thread.followup_count >= 10:
        thread.status = 'escalated_internal'
        return False

    # Weekend or holiday
    if not is_business_day(datetime.now()):
        return False

    # Invoice already paid in accounting system
    if invoice_is_paid(thread.invoice_id):
        thread.status = 'paid'
        return False

    return True
```

## Implementation Steps

### Phase 1: Backend Core (Week 1)

1. **Database Models**
   - Create `AdjusterFollowUpThread` collection
   - Add indexes on `status`, `approval_status`, `next_followup_date`
   - Migration script for existing invoices

2. **Email Integration**
   - Install SendGrid/Mailgun SDK
   - Configure SMTP settings
   - Create email templates
   - Test email delivery

3. **API Endpoints**
   - `POST /adjuster-followups/qualify` - Run qualification on email
   - `GET /adjuster-followups/pending-approval` - Get approval queue
   - `PUT /adjuster-followups/{id}/approve` - Approve thread
   - `PUT /adjuster-followups/{id}/pause` - Pause automation
   - `GET /adjuster-followups/active` - List active threads
   - `POST /adjuster-followups/send-followup` - Manual send
   - `POST /adjuster-followups/run-scheduler` - Automated daily run

4. **Business Logic**
   - Email qualification engine
   - Business day calculator
   - Stop condition checker
   - Escalation message generator

### Phase 2: Frontend UI (Week 2)

1. **Approval Queue Page**
   - List pending emails with preview
   - Approve/Reject buttons
   - Bulk actions
   - Filter by carrier/adjuster

2. **Active Follow-Ups Dashboard**
   - Table of all active threads
   - Days outstanding counter
   - Last followup date
   - Next scheduled followup
   - Manual pause/resume controls

3. **Follow-Up History View**
   - Timeline of all follow-ups sent
   - Email preview
   - Response tracking
   - Status changes log

### Phase 3: Email Platform Integration (Week 3)

#### Gmail Integration (via Gmail API)
```javascript
// n8n/Make workflow
Gmail Trigger: New Email
    ↓
Filter: Domain matches adjuster list
    ↓
Filter: Contains billing keywords
    ↓
HTTP Request: POST /api/adjuster-followups/qualify
    ↓
If qualified: Add label "Needs Approval"
```

#### Outlook Integration (via Microsoft Graph API)
```javascript
Outlook Trigger: New Email
    ↓
Filter: Sender domain in adjuster list
    ↓
Filter: Body contains keywords
    ↓
HTTP Request: POST /api/adjuster-followups/qualify
    ↓
If qualified: Apply category "Adjuster Follow-Up"
```

### Phase 4: Automation Scheduler (Week 4)

#### Daily Cron Job
```bash
# Run every business day at 8 AM
0 8 * * 1-5 curl -X POST https://api.restorationos.com/adjuster-followups/run-scheduler
```

#### Scheduler Logic
```python
async def run_daily_scheduler():
    """
    Runs every morning to send scheduled follow-ups
    """
    today = datetime.now()

    # Get all active threads due for followup
    threads = await db.adjuster_followups.find({
        "status": "active",
        "approval_status": "approved",
        "next_followup_date": {"$lte": today}
    }).to_list(length=None)

    results = []
    for thread in threads:
        # Safety check
        if not should_send_followup(thread):
            continue

        # Generate and send email
        email_sent = await send_escalation_email(thread)

        if email_sent:
            # Update thread
            await update_followup_thread(
                thread_id=thread['_id'],
                followup_count=thread['followup_count'] + 1,
                last_followup_date=today,
                next_followup_date=next_business_day(today, 3)
            )
            results.append({"thread_id": thread['_id'], "status": "sent"})
        else:
            results.append({"thread_id": thread['_id'], "status": "failed"})

    return results
```

## Insurance Carrier & TPA Domain List

### Major Insurance Carriers
```
allstate.com
statefarm.com
progressive.com
geico.com
libertymutual.com
travelers.com
nationwide.com
usaa.com
farmers.com
americanfamily.com
safeco.com
aig.com
chubb.com
zurichna.com
thehartford.com
```

### TPAs (Third-Party Administrators)
```
crawco.com
sedgwick.com
gallagherbasset.com
corvel.com
tristargroup.com
york-intl.com
esis.com
broadspire.com
```

### Adjuster Firms
```
eberl.com
enservio.com
verisk.com
haag.com
```

## Testing Protocol

### Before Production Launch

1. **Email Qualification Tests**
   - Test with 20 real emails (10 qualifying, 10 non-qualifying)
   - Verify 100% accuracy on domain matching
   - Verify keyword detection works on all message formats (HTML, plain text)

2. **Follow-Up Schedule Tests**
   - Create test thread with first contact date 10 days ago
   - Verify business day calculation skips weekends
   - Verify holidays are excluded

3. **Stop Condition Tests**
   - Mark test invoice as paid → verify automation stops
   - Add "disputed" keyword in mock reply → verify automation stops
   - Manually pause thread → verify no emails sent

4. **Safety Mechanism Tests**
   - Attempt to send followup on weekend → should skip
   - Attempt to send before 3 business days → should skip
   - Thread with 10+ followups → should escalate internally

5. **Email Delivery Tests**
   - Send test escalation email to team members
   - Verify formatting is professional
   - Verify all variables populate correctly
   - Test on mobile and desktop email clients

## Risk Mitigation

### Blind Automation Prevention
- **Approval gate**: No email sends without explicit approval
- **Manual override**: Pause button available on all threads
- **Max attempts**: Hard limit at 10 follow-ups (escalate to management)

### Relationship Protection
- **Tone calibration**: Same professional message throughout
- **No threats**: No legal language or aggressive wording
- **Dispute detection**: Automatic stop if adjuster pushes back

### Cash Flow Optimization
- **3-day cycles**: Fast enough to maintain pressure, slow enough to allow response time
- **Progressive pressure**: Implicit escalation without burning bridges
- **Accountability focus**: Message emphasizes need for clear direction, not just payment

## Metrics & Reporting

### Track These KPIs
- Average days to payment (before vs after automation)
- Follow-up count at payment (which cycle adjuster responds)
- Automation stop reasons (paid, disputed, paused, etc.)
- Email open rates (if tracking pixels enabled)
- Response rate by carrier

### Dashboard Views
- Active threads by carrier
- Overdue invoices by days outstanding
- Follow-up effectiveness (payment rate by followup #)
- Automation health (emails sent, errors, stops)

## Maintenance & Optimization

### Weekly
- Review pending approval queue
- Check for stuck threads (status not updating)
- Review disputed claims for patterns

### Monthly
- Analyze which carriers respond fastest
- Identify carriers requiring different approach
- Update adjuster domain list as needed
- Review escalation message effectiveness

### Quarterly
- A/B test message variations
- Review max followup limit (raise/lower from 10)
- Assess business day schedule (add/remove holidays)
- Train team on system usage

---

**Last Updated:** 2026-01-15
**System Version:** 1.0
**Status:** Implementation Ready
