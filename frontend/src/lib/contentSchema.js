/**
 * Content Logging Schema
 * Defines the structure for all logged content types in the workflow
 */

// Content type constants
export const CONTENT_TYPES = {
  INVOICE_FOLLOWUP: 'invoice_followup',
  OWNER_ALERT: 'owner_alert',
  SILENCE_BREAKER: 'silence_breaker',
  AUTO_REPLY: 'auto_reply',
  TASK: 'task',
  ADJUSTER_DRAFT: 'adjuster_draft',
};

// Priority levels
export const PRIORITY_LEVELS = {
  LOW: 'low',
  MEDIUM: 'medium',
  HIGH: 'high',
  URGENT: 'urgent',
};

// Tone levels for escalation
export const TONE_LEVELS = {
  FRIENDLY: 'friendly',
  PROFESSIONAL: 'professional',
  FIRM: 'firm',
  URGENT: 'urgent',
  FINAL: 'final',
};

/**
 * Creates a structured log entry for invoice follow-up messages
 * @param {Object} data - The invoice and message data
 * @returns {Object} Structured log entry
 */
export function createFollowUpLog(data) {
  return {
    id: generateLogId(),
    type: CONTENT_TYPES.INVOICE_FOLLOWUP,
    timestamp: new Date().toISOString(),
    metadata: {
      invoice_id: data.invoice_id || null,
      invoice_number: data.invoice_number || null,
      customer_name: data.customer_name || null,
      payer_name: data.payer_name || null,
      days_outstanding: data.days_outstanding || 0,
      balance_due: parseFloat(data.balance_due) || 0,
    },
    content: {
      subject: data.subject || data.email_subject || '',
      body: data.body || data.email_body || '',
      tone: data.tone || determineTone(data.days_outstanding),
    },
    status: {
      sent: false,
      logged: true,
      error: null,
    },
  };
}

/**
 * Creates a structured log entry for owner alerts
 * @param {Object} data - The alert data
 * @returns {Object} Structured log entry
 */
export function createOwnerAlertLog(data) {
  return {
    id: generateLogId(),
    type: CONTENT_TYPES.OWNER_ALERT,
    timestamp: new Date().toISOString(),
    metadata: {
      invoice_id: data.invoice_id || null,
      customer_name: data.customer_name || null,
      priority: PRIORITY_LEVELS.URGENT,
      days_outstanding: data.days_outstanding || 0,
      balance_due: parseFloat(data.balance_due) || 0,
    },
    content: {
      subject: data.subject || 'URGENT: Invoice Requires Attention',
      body: data.body || '',
    },
    status: {
      sent: false,
      logged: true,
      error: null,
    },
  };
}

/**
 * Creates a structured log entry for silence-breaker emails
 * @param {Object} data - The silence-breaker data
 * @returns {Object} Structured log entry
 */
export function createSilenceBreakerLog(data) {
  return {
    id: generateLogId(),
    type: CONTENT_TYPES.SILENCE_BREAKER,
    timestamp: new Date().toISOString(),
    metadata: {
      payer_name: data.payer_name || null,
      days_since_contact: data.days_since_contact || 0,
      invoice_id: data.invoice_id || null,
    },
    content: {
      subject: data.subject || data.email_subject || 'Checking In',
      body: data.body || data.email_body || '',
    },
    status: {
      sent: false,
      logged: true,
      error: null,
    },
  };
}

/**
 * Creates a structured log entry for auto-replies
 * @param {Object} data - The auto-reply data
 * @returns {Object} Structured log entry
 */
export function createAutoReplyLog(data) {
  return {
    id: generateLogId(),
    type: CONTENT_TYPES.AUTO_REPLY,
    timestamp: new Date().toISOString(),
    metadata: {
      original_from: data.email_from || null,
      original_subject: data.original_subject || null,
    },
    content: {
      subject: data.reply_subject || data.subject || '',
      body: data.reply_body || data.body || '',
    },
    status: {
      sent: data.send_reply !== false,
      logged: true,
      error: null,
    },
  };
}

/**
 * Creates a structured log entry for extracted tasks
 * @param {Object} data - The task data
 * @returns {Object} Structured log entry
 */
export function createTaskLog(data) {
  return {
    id: generateLogId(),
    type: CONTENT_TYPES.TASK,
    timestamp: new Date().toISOString(),
    metadata: {
      source_email: data.source_email || null,
      category: data.category || 'general',
      priority: data.priority || PRIORITY_LEVELS.MEDIUM,
      deadline: data.deadline || null,
    },
    content: {
      task: data.task || '',
    },
    status: {
      completed: false,
      logged: true,
      error: null,
    },
  };
}

/**
 * Parses a business message (like an invoice reminder) into structured format
 * @param {string} messageText - Raw message text
 * @returns {Object} Parsed structured message
 */
export function parseBusinessMessage(messageText) {
  const lines = messageText.split('\n').map(l => l.trim()).filter(Boolean);

  const parsed = {
    id: generateLogId(),
    type: 'business_message',
    timestamp: new Date().toISOString(),
    greeting: '',
    body: [],
    invoice_details: null,
    closing: '',
    signature: {
      name: '',
      company: '',
      phone: '',
      email: '',
    },
  };

  let currentSection = 'greeting';
  const invoiceData = {};

  for (const line of lines) {
    // Check for invoice details
    const invoiceMatch = line.match(/Invoice\s*#:\s*(.+)/i);
    const dateMatch = line.match(/Invoice\s*Date:\s*(.+)/i);
    const amountMatch = line.match(/Amount\s*Due:\s*\$?([\d,]+\.?\d*)/i);
    const dueDateMatch = line.match(/Due\s*Date:\s*(.+)/i);

    if (invoiceMatch) {
      invoiceData.invoice_number = invoiceMatch[1].trim();
      currentSection = 'invoice';
    } else if (dateMatch) {
      invoiceData.invoice_date = dateMatch[1].trim();
    } else if (amountMatch) {
      invoiceData.amount_due = parseFloat(amountMatch[1].replace(/,/g, ''));
    } else if (dueDateMatch) {
      invoiceData.due_date = dueDateMatch[1].trim();
    } else if (line.match(/^(Hello|Hi|Dear|Good\s)/i)) {
      parsed.greeting = line;
      currentSection = 'body';
    } else if (line.match(/^(Thanks|Thank you|Regards|Best|Sincerely)/i)) {
      currentSection = 'closing';
      parsed.closing = line;
    } else if (line.match(/^\d{3}[-.\s]?\d{3}[-.\s]?\d{4}/)) {
      parsed.signature.phone = line;
    } else if (line.match(/@.*\.(com|net|org|io)/i)) {
      parsed.signature.email = line;
    } else if (currentSection === 'body' && !invoiceData.invoice_number) {
      parsed.body.push(line);
    } else if (currentSection === 'closing' && !parsed.signature.name) {
      parsed.signature.name = line;
    } else if (parsed.signature.name && !parsed.signature.company && !line.match(/^\d/)) {
      parsed.signature.company = line;
    }
  }

  if (Object.keys(invoiceData).length > 0) {
    parsed.invoice_details = invoiceData;
  }

  return parsed;
}

/**
 * Generates a unique log ID
 * @returns {string} Unique ID
 */
function generateLogId() {
  return `log_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Determines tone based on days outstanding
 * @param {number} days - Days outstanding
 * @returns {string} Tone level
 */
function determineTone(days) {
  if (days >= 90) return TONE_LEVELS.FINAL;
  if (days >= 61) return TONE_LEVELS.URGENT;
  if (days >= 46) return TONE_LEVELS.FIRM;
  if (days >= 30) return TONE_LEVELS.PROFESSIONAL;
  return TONE_LEVELS.FRIENDLY;
}

/**
 * Formats a log entry for display
 * @param {Object} logEntry - The log entry
 * @returns {Object} Formatted for display
 */
export function formatForDisplay(logEntry) {
  return {
    ...logEntry,
    formattedDate: new Date(logEntry.timestamp).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }),
    formattedAmount: logEntry.metadata?.balance_due
      ? new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' })
          .format(logEntry.metadata.balance_due)
      : null,
  };
}
