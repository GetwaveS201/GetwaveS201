import React from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from './ui/card';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { cn } from '@/lib/utils';

/**
 * Tone color mapping for visual indicators
 */
const TONE_COLORS = {
  friendly: 'bg-green-100 text-green-800 border-green-200',
  professional: 'bg-blue-100 text-blue-800 border-blue-200',
  firm: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  urgent: 'bg-orange-100 text-orange-800 border-orange-200',
  final: 'bg-red-100 text-red-800 border-red-200',
};

/**
 * Priority color mapping
 */
const PRIORITY_COLORS = {
  low: 'bg-slate-100 text-slate-700',
  medium: 'bg-blue-100 text-blue-700',
  high: 'bg-orange-100 text-orange-700',
  urgent: 'bg-red-100 text-red-700',
};

/**
 * Content type labels
 */
const TYPE_LABELS = {
  invoice_followup: 'Invoice Follow-up',
  owner_alert: 'Owner Alert',
  silence_breaker: 'Silence Breaker',
  auto_reply: 'Auto Reply',
  task: 'Task',
  adjuster_draft: 'Adjuster Draft',
  business_message: 'Business Message',
};

/**
 * Formats currency values
 */
function formatCurrency(amount) {
  if (amount === null || amount === undefined) return null;
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(amount);
}

/**
 * Formats dates for display
 */
function formatDate(dateString) {
  if (!dateString) return null;
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  });
}

/**
 * Formats timestamp for display
 */
function formatTimestamp(timestamp) {
  if (!timestamp) return null;
  const date = new Date(timestamp);
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Invoice Details Card - displays structured invoice information
 */
function InvoiceDetailsCard({ invoice }) {
  if (!invoice) return null;

  return (
    <div className="bg-slate-50 rounded-lg p-4 border border-slate-200 my-4">
      <h4 className="text-sm font-semibold text-slate-600 mb-3 uppercase tracking-wide">
        Invoice Details
      </h4>
      <div className="grid grid-cols-2 gap-3">
        {invoice.invoice_number && (
          <div>
            <span className="text-xs text-slate-500">Invoice #</span>
            <p className="font-mono font-semibold text-slate-900">{invoice.invoice_number}</p>
          </div>
        )}
        {invoice.invoice_date && (
          <div>
            <span className="text-xs text-slate-500">Invoice Date</span>
            <p className="text-slate-900">{invoice.invoice_date}</p>
          </div>
        )}
        {invoice.amount_due !== undefined && (
          <div>
            <span className="text-xs text-slate-500">Amount Due</span>
            <p className="font-semibold text-lg text-slate-900">
              {formatCurrency(invoice.amount_due)}
            </p>
          </div>
        )}
        {invoice.due_date && (
          <div>
            <span className="text-xs text-slate-500">Due Date</span>
            <p className="text-slate-900">{invoice.due_date}</p>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Signature Block - displays sender information
 */
function SignatureBlock({ signature }) {
  if (!signature || (!signature.name && !signature.company)) return null;

  return (
    <div className="mt-6 pt-4 border-t border-slate-200">
      {signature.name && <p className="font-medium text-slate-900">{signature.name}</p>}
      {signature.company && <p className="text-slate-600">{signature.company}</p>}
      {signature.phone && (
        <p className="text-slate-600 font-mono text-sm">{signature.phone}</p>
      )}
      {signature.email && (
        <p className="text-blue-600 text-sm">{signature.email}</p>
      )}
    </div>
  );
}

/**
 * Business Message Viewer - renders structured business messages like invoice reminders
 */
export function BusinessMessageViewer({ message }) {
  if (!message) return null;

  return (
    <Card className="w-full max-w-2xl mx-auto shadow-lg">
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <Badge variant="outline" className="text-xs">
            {TYPE_LABELS[message.type] || 'Message'}
          </Badge>
          {message.timestamp && (
            <span className="text-xs text-slate-500">
              {formatTimestamp(message.timestamp)}
            </span>
          )}
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Greeting */}
        {message.greeting && (
          <p className="text-slate-700">{message.greeting}</p>
        )}

        {/* Body paragraphs */}
        {message.body && message.body.length > 0 && (
          <div className="space-y-2">
            {message.body.map((paragraph, index) => (
              <p key={index} className="text-slate-700">{paragraph}</p>
            ))}
          </div>
        )}

        {/* Invoice Details */}
        {message.invoice_details && (
          <InvoiceDetailsCard invoice={message.invoice_details} />
        )}

        {/* Closing */}
        {message.closing && (
          <p className="text-slate-700">{message.closing}</p>
        )}

        {/* Signature */}
        <SignatureBlock signature={message.signature} />
      </CardContent>
    </Card>
  );
}

/**
 * Content Log Entry Viewer - displays a single log entry
 */
export function ContentLogEntry({ entry }) {
  if (!entry) return null;

  const toneClass = entry.content?.tone ? TONE_COLORS[entry.content.tone] : '';

  return (
    <Card className="w-full max-w-2xl mx-auto shadow-md mb-4">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between flex-wrap gap-2">
          <div className="flex items-center gap-2">
            <Badge variant="outline">
              {TYPE_LABELS[entry.type] || entry.type}
            </Badge>
            {entry.content?.tone && (
              <Badge className={cn('capitalize', toneClass)}>
                {entry.content.tone}
              </Badge>
            )}
          </div>
          <span className="text-xs text-slate-500">
            {formatTimestamp(entry.timestamp)}
          </span>
        </div>
        {entry.content?.subject && (
          <CardTitle className="text-lg mt-2">{entry.content.subject}</CardTitle>
        )}
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Metadata section */}
        {entry.metadata && (
          <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
            <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
              Details
            </h4>
            <div className="grid grid-cols-2 gap-2 text-sm">
              {entry.metadata.invoice_id && (
                <div>
                  <span className="text-slate-500">Invoice ID:</span>
                  <span className="ml-2 font-mono">{entry.metadata.invoice_id}</span>
                </div>
              )}
              {entry.metadata.customer_name && (
                <div>
                  <span className="text-slate-500">Customer:</span>
                  <span className="ml-2">{entry.metadata.customer_name}</span>
                </div>
              )}
              {entry.metadata.payer_name && (
                <div>
                  <span className="text-slate-500">Payer:</span>
                  <span className="ml-2">{entry.metadata.payer_name}</span>
                </div>
              )}
              {entry.metadata.days_outstanding !== undefined && (
                <div>
                  <span className="text-slate-500">Days Outstanding:</span>
                  <span className="ml-2 font-semibold">{entry.metadata.days_outstanding}</span>
                </div>
              )}
              {entry.metadata.balance_due !== undefined && (
                <div>
                  <span className="text-slate-500">Balance Due:</span>
                  <span className="ml-2 font-semibold text-red-600">
                    {formatCurrency(entry.metadata.balance_due)}
                  </span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Email body */}
        {entry.content?.body && (
          <div className="prose prose-sm max-w-none">
            <div className="whitespace-pre-wrap text-slate-700">
              {entry.content.body}
            </div>
          </div>
        )}

        {/* Task content */}
        {entry.content?.task && (
          <div className="flex items-start gap-3 p-3 bg-amber-50 rounded-lg border border-amber-200">
            <div className="flex-1">
              <p className="font-medium text-slate-900">{entry.content.task}</p>
              {entry.metadata?.deadline && (
                <p className="text-sm text-slate-600 mt-1">
                  Deadline: {entry.metadata.deadline}
                </p>
              )}
            </div>
            {entry.metadata?.priority && (
              <Badge className={PRIORITY_COLORS[entry.metadata.priority]}>
                {entry.metadata.priority}
              </Badge>
            )}
          </div>
        )}
      </CardContent>

      <CardFooter className="pt-0">
        <div className="flex items-center gap-2 text-xs text-slate-500">
          <span className="font-mono">{entry.id}</span>
          {entry.status?.sent && (
            <Badge variant="outline" className="bg-green-50 text-green-700 text-xs">
              Sent
            </Badge>
          )}
          {entry.status?.error && (
            <Badge variant="destructive" className="text-xs">
              Error
            </Badge>
          )}
        </div>
      </CardFooter>
    </Card>
  );
}

/**
 * Content Log List - displays multiple log entries
 */
export function ContentLogList({ entries = [], emptyMessage = 'No content logs available' }) {
  if (!entries || entries.length === 0) {
    return (
      <div className="text-center py-12 text-slate-500">
        <p>{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {entries.map((entry, index) => (
        <ContentLogEntry key={entry.id || index} entry={entry} />
      ))}
    </div>
  );
}

/**
 * JSON Log Viewer - displays raw JSON with syntax highlighting
 */
export function JsonLogViewer({ data, title = 'JSON Log' }) {
  if (!data) return null;

  const jsonString = JSON.stringify(data, null, 2);

  return (
    <Card className="w-full max-w-2xl mx-auto">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-slate-600">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <pre className="bg-slate-900 text-slate-100 p-4 rounded-lg overflow-x-auto text-sm font-mono">
          <code>{jsonString}</code>
        </pre>
      </CardContent>
    </Card>
  );
}

export default {
  BusinessMessageViewer,
  ContentLogEntry,
  ContentLogList,
  JsonLogViewer,
};
