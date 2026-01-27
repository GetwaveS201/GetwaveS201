/**
 * n8n Workflow Parsing Fixes
 *
 * This file contains the corrected JavaScript code for n8n Code nodes
 * to properly parse AI responses and log structured content.
 *
 * ISSUE: The AI models return JSON with fields like {subject, body, tone}
 * but the parsing nodes were looking for {email_subject, email_body}
 */

// =============================================================================
// PARSE FOLLOW-UP RESPONSE (Node: "Parse Follow-up Response")
// =============================================================================
// Replace the existing code in this node with the following:

const parseFollowUpResponse = `
// Extract the AI response content
const response = $json.message?.content || $json.choices?.[0]?.message?.content || $json.text || '';

// Clean markdown code blocks if present
let cleaned = response.replace(/\`\`\`json\\n?/g, '').replace(/\`\`\`\\n?/g, '').trim();

// Get source data from previous node
const sourceData = $('Track Payer Behavior').first().json;

try {
  const parsed = JSON.parse(cleaned);

  return {
    json: {
      // Log entry fields for Google Sheets
      date: new Date().toISOString().split('T')[0],
      invoice_id: sourceData.invoice_id || '',
      payer_name: sourceData.payer_name || sourceData.customer_name || '',
      // Map AI response fields to expected sheet columns
      email_subject: parsed.subject || '',
      email_body: parsed.body || '',
      days_outstanding: sourceData.days_outstanding || '',
      balance_due: sourceData.balance_due || '',
      tone: parsed.tone || '',
      // Additional structured data for tracking
      log_id: 'log_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9),
      status: 'pending',
      parse_error: false
    }
  };
} catch (error) {
  // Fallback if JSON parsing fails
  return {
    json: {
      date: new Date().toISOString().split('T')[0],
      invoice_id: sourceData.invoice_id || '',
      payer_name: sourceData.payer_name || sourceData.customer_name || '',
      email_subject: 'Payment Reminder - Invoice ' + (sourceData.invoice_id || 'Unknown'),
      email_body: cleaned, // Use raw response as body
      days_outstanding: sourceData.days_outstanding || '',
      balance_due: sourceData.balance_due || '',
      tone: 'professional',
      log_id: 'log_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9),
      status: 'pending',
      parse_error: true,
      error_message: error.message
    }
  };
}
`;

// =============================================================================
// PARSE SILENCE-BREAKER RESPONSE (Node: "Parse Silence-Breaker Response")
// =============================================================================
// Replace the existing code in this node with the following:

const parseSilenceBreakerResponse = `
// Extract the AI response content
const response = $json.message?.content || $json.choices?.[0]?.message?.content || $json.text || '';

// Clean markdown code blocks if present
let cleaned = response.replace(/\`\`\`json\\n?/g, '').replace(/\`\`\`\\n?/g, '').trim();

// Get source data from Silence-Breaker Engine
const sourceData = $('Silence-Breaker Engine').first().json;

try {
  const parsed = JSON.parse(cleaned);

  return {
    json: {
      date: new Date().toISOString(),
      payer_name: sourceData.payer_name || sourceData.customer_name || '',
      days_since_contact: sourceData.days_since_contact || '',
      // Map AI response fields correctly
      email_subject: parsed.subject || 'Response Required - Outstanding Invoice',
      email_body: parsed.body || '',
      invoice_id: sourceData.invoice_id || '',
      balance_due: sourceData.balance_due || '',
      log_id: 'sb_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9),
      type: 'silence_breaker',
      parse_error: false
    }
  };
} catch (error) {
  return {
    json: {
      date: new Date().toISOString(),
      payer_name: sourceData.payer_name || sourceData.customer_name || '',
      days_since_contact: sourceData.days_since_contact || '',
      email_subject: 'Checking In',
      email_body: cleaned,
      invoice_id: sourceData.invoice_id || '',
      balance_due: sourceData.balance_due || '',
      log_id: 'sb_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9),
      type: 'silence_breaker',
      parse_error: true,
      error_message: error.message
    }
  };
}
`;

// =============================================================================
// PARSE AUTO-REPLY RESPONSE (Node: "Parse Auto-Reply Response")
// =============================================================================
// Replace the existing code in this node with the following:

const parseAutoReplyResponse = `
// Extract the AI response content
const response = $json.message?.content || $json.choices?.[0]?.message?.content || $json.text || '';

// Clean markdown code blocks if present
let cleaned = response.replace(/\`\`\`json\\n?/g, '').replace(/\`\`\`\\n?/g, '').trim();

// Get source data from email processing
const sourceData = $('Filter - Email Actions Needed').first().json;

try {
  const parsed = JSON.parse(cleaned);

  // Check if AI decided not to send a reply
  if (parsed.send_reply === false) {
    return {
      json: {
        date: new Date().toISOString(),
        email_from: sourceData.from || '',
        original_subject: sourceData.subject || '',
        reply_subject: null,
        reply_body: null,
        send_reply: false,
        reason: parsed.reason || 'No reply needed',
        log_id: 'ar_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9),
        type: 'auto_reply',
        parse_error: false
      }
    };
  }

  return {
    json: {
      date: new Date().toISOString(),
      email_from: sourceData.from || '',
      original_subject: sourceData.subject || '',
      // Map correctly - AI uses reply_subject/reply_body OR subject/body
      reply_subject: parsed.reply_subject || parsed.subject || ('RE: ' + sourceData.subject),
      reply_body: parsed.reply_body || parsed.body || '',
      send_reply: parsed.send_reply !== false,
      reason: parsed.reason || '',
      log_id: 'ar_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9),
      type: 'auto_reply',
      parse_error: false
    }
  };
} catch (error) {
  return {
    json: {
      date: new Date().toISOString(),
      email_from: sourceData.from || '',
      original_subject: sourceData.subject || '',
      reply_subject: 'RE: ' + (sourceData.subject || ''),
      reply_body: cleaned,
      send_reply: true,
      reason: 'Parse error - using raw response',
      log_id: 'ar_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9),
      type: 'auto_reply',
      parse_error: true,
      error_message: error.message
    }
  };
}
`;

// =============================================================================
// PARSE OWNER ALERT RESPONSE (Node: "Parse Owner Alert Response")
// =============================================================================
// The existing code is mostly correct, but here's an improved version:

const parseOwnerAlertResponse = `
// Extract the AI response content
const response = $json.message?.content || $json.choices?.[0]?.message?.content || $json.text || '';

// Clean markdown code blocks if present
let cleaned = response.replace(/\`\`\`json\\n?/g, '').replace(/\`\`\`\\n?/g, '').trim();

// Get source data
const sourceData = $('Track Payer Behavior').first().json;

try {
  const parsed = JSON.parse(cleaned);

  return {
    json: {
      date: new Date().toISOString(),
      invoice_id: sourceData.invoice_id || '',
      customer_name: sourceData.customer_name || '',
      days_outstanding: sourceData.days_outstanding || '',
      balance_due: sourceData.balance_due || '',
      subject: parsed.subject || 'URGENT: Invoice Requires Attention',
      body: parsed.body || 'Please review this invoice immediately.',
      alert_type: 'owner_alert',
      priority: 'urgent',
      log_id: 'oa_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9),
      parse_error: false
    }
  };
} catch (error) {
  return {
    json: {
      date: new Date().toISOString(),
      invoice_id: sourceData.invoice_id || '',
      customer_name: sourceData.customer_name || '',
      days_outstanding: sourceData.days_outstanding || '',
      balance_due: sourceData.balance_due || '',
      subject: 'URGENT: Invoice Requires Attention',
      body: cleaned,
      alert_type: 'owner_alert',
      priority: 'urgent',
      log_id: 'oa_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9),
      parse_error: true,
      error_message: error.message
    }
  };
}
`;

// =============================================================================
// PARSE TASKS RESPONSE (Node: "Parse Tasks Response")
// =============================================================================
// The existing code is mostly correct, enhanced version:

const parseTasksResponse = `
// Extract the AI response content
const response = $json.message?.content || $json.choices?.[0]?.message?.content || $json.text || '';

// Clean markdown code blocks if present
let cleaned = response.replace(/\`\`\`json\\n?/g, '').replace(/\`\`\`\\n?/g, '').trim();

// Get source email data
const sourceData = $('Process Emails + Intelligence').first().json;

try {
  const parsed = JSON.parse(cleaned);

  if (!parsed.tasks || !Array.isArray(parsed.tasks) || parsed.tasks.length === 0) {
    return [{
      json: {
        no_tasks: true,
        source_email: sourceData.from || '',
        processed_at: new Date().toISOString()
      }
    }];
  }

  return parsed.tasks.map(task => ({
    json: {
      date: new Date().toISOString(),
      task: task.task || '',
      priority: task.priority || 'medium',
      deadline: task.deadline || 'none',
      category: task.category || 'general',
      source_email: sourceData.from || '',
      source_subject: sourceData.subject || '',
      log_id: 'task_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9),
      status: 'pending',
      type: 'task',
      parse_error: false
    }
  }));
} catch (error) {
  return [{
    json: {
      no_tasks: true,
      parse_error: true,
      error_message: error.message,
      source_email: sourceData.from || '',
      processed_at: new Date().toISOString()
    }
  }];
}
`;

// =============================================================================
// PARSE SUMMARY RESPONSE (Node: "Parse Summary Response")
// =============================================================================

const parseSummaryResponse = `
// Extract the AI response content
const response = $json.message?.content || $json.choices?.[0]?.message?.content || $json.text || '';

// Clean markdown code blocks if present
let cleaned = response.replace(/\`\`\`json\\n?/g, '').replace(/\`\`\`\\n?/g, '').trim();

try {
  const parsed = JSON.parse(cleaned);

  return {
    json: {
      date: new Date().toISOString(),
      summary_text: parsed.summary_text || 'Daily summary generated.',
      stats: parsed.stats || {},
      urgent_items: parsed.urgent_items || [],
      log_id: 'summary_' + Date.now(),
      type: 'daily_summary',
      parse_error: false
    }
  };
} catch (error) {
  return {
    json: {
      date: new Date().toISOString(),
      summary_text: cleaned, // Use raw response as summary
      stats: {},
      urgent_items: [],
      log_id: 'summary_' + Date.now(),
      type: 'daily_summary',
      parse_error: true,
      error_message: error.message
    }
  };
}
`;

// =============================================================================
// EXPORT: Sample JSON log structure for reference
// =============================================================================

const sampleLogStructures = {
  invoice_followup: {
    date: "2026-01-27",
    invoice_id: "INV-1047",
    payer_name: "ABC Insurance Company",
    email_subject: "Payment Reminder - Invoice INV-1047",
    email_body: "Hello,\n\nThis is a friendly reminder regarding the invoice below...",
    days_outstanding: 10,
    balance_due: 8450.00,
    tone: "friendly",
    log_id: "log_1706400000000_abc123",
    status: "pending",
    parse_error: false
  },

  owner_alert: {
    date: "2026-01-27T10:30:00.000Z",
    invoice_id: "INV-1032",
    customer_name: "State Farm Insurance",
    days_outstanding: 75,
    balance_due: 12500.00,
    subject: "URGENT: Invoice INV-1032 - 75 Days Outstanding",
    body: "Critical attention required...",
    alert_type: "owner_alert",
    priority: "urgent",
    log_id: "oa_1706400000000_xyz789",
    parse_error: false
  },

  silence_breaker: {
    date: "2026-01-27T09:00:00.000Z",
    payer_name: "Allstate Insurance",
    days_since_contact: 21,
    email_subject: "Response Required - Invoice INV-1089",
    email_body: "We've attempted to reach you multiple times...",
    invoice_id: "INV-1089",
    balance_due: 5200.00,
    log_id: "sb_1706400000000_def456",
    type: "silence_breaker",
    parse_error: false
  },

  task: {
    date: "2026-01-27T08:45:00.000Z",
    task: "Send completion photos to Allstate adjuster for claim #CLM-2026-0892",
    priority: "high",
    deadline: "2026-01-28",
    category: "documentation",
    source_email: "adjuster@allstate.com",
    source_subject: "RE: Claim Documentation Needed",
    log_id: "task_1706400000000_ghi789",
    status: "pending",
    type: "task",
    parse_error: false
  },

  auto_reply: {
    date: "2026-01-27T10:15:00.000Z",
    email_from: "claims@statefarm.com",
    original_subject: "Invoice Query - INV-1055",
    reply_subject: "RE: Invoice Query - INV-1055",
    reply_body: "Mahalo for reaching out. We've received your inquiry and are reviewing...",
    send_reply: true,
    reason: "Invoice inquiry requires acknowledgment",
    log_id: "ar_1706400000000_jkl012",
    type: "auto_reply",
    parse_error: false
  }
};

console.log("n8n Parsing Fixes loaded. Copy the code blocks above into your n8n workflow nodes.");
console.log("\nSample log structures:", JSON.stringify(sampleLogStructures, null, 2));
