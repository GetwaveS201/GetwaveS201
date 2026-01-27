import React from 'react';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Badge } from './ui/badge';
import { Separator } from './ui/separator';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import {
  BusinessMessageViewer,
  ContentLogEntry,
  ContentLogList,
  JsonLogViewer,
} from './ContentLogViewer';
import {
  createFollowUpLog,
  parseBusinessMessage,
  TONE_LEVELS,
} from '@/lib/contentSchema';

/**
 * Sample invoice reminder message (from user's example)
 */
const SAMPLE_MESSAGE_TEXT = `Hello,

This is a friendly reminder regarding the invoice below, which is now past due.

Invoice #: INV-1047
Invoice Date: January 3, 2026
Amount Due: $8,450.00
Due Date: January 17, 2026

Please let us know when payment is scheduled, or if there's anything needed from us to release payment.

If payment has already been sent, thank you.

Christian
Superior Restoration & Construction
808-555-0199
billing@superiorrestorationhi.com`;

/**
 * Sample structured log entry (what the n8n workflow should produce)
 */
const SAMPLE_FOLLOWUP_LOG = {
  id: 'log_1706400000000_abc123def',
  type: 'invoice_followup',
  timestamp: '2026-01-27T10:30:00.000Z',
  metadata: {
    invoice_id: 'INV-1047',
    invoice_number: 'INV-1047',
    customer_name: 'ABC Insurance Company',
    payer_name: 'ABC Insurance Company',
    days_outstanding: 10,
    balance_due: 8450.0,
  },
  content: {
    subject: 'Payment Reminder - Invoice INV-1047',
    body: `Hello,

This is a friendly reminder regarding the invoice below, which is now past due.

Invoice #: INV-1047
Invoice Date: January 3, 2026
Amount Due: $8,450.00
Due Date: January 17, 2026

Please let us know when payment is scheduled, or if there's anything needed from us to release payment.

If payment has already been sent, thank you.

Christian
Superior Restoration & Construction
808-555-0199
billing@superiorrestorationhi.com`,
    tone: 'friendly',
  },
  status: {
    sent: true,
    logged: true,
    error: null,
  },
};

/**
 * Multiple sample log entries for demonstrating the log list
 */
const SAMPLE_LOG_ENTRIES = [
  SAMPLE_FOLLOWUP_LOG,
  {
    id: 'log_1706400001000_xyz789',
    type: 'owner_alert',
    timestamp: '2026-01-27T09:15:00.000Z',
    metadata: {
      invoice_id: 'INV-1032',
      customer_name: 'State Farm Insurance',
      priority: 'urgent',
      days_outstanding: 75,
      balance_due: 12500.0,
    },
    content: {
      subject: 'URGENT: Invoice INV-1032 - 75 Days Outstanding',
      body: `Critical attention required.

Invoice INV-1032 for State Farm Insurance is now 75 days past due with a balance of $12,500.00.

This invoice is approaching the 90-day threshold for collections referral.

Recommended Action: Direct owner call to claims supervisor.`,
    },
    status: {
      sent: true,
      logged: true,
      error: null,
    },
  },
  {
    id: 'log_1706400002000_task456',
    type: 'task',
    timestamp: '2026-01-27T08:45:00.000Z',
    metadata: {
      source_email: 'adjuster@allstate.com',
      category: 'documentation',
      priority: 'high',
      deadline: '2026-01-28',
    },
    content: {
      task: 'Send completion photos and final invoice to Allstate adjuster for claim #CLM-2026-0892',
    },
    status: {
      completed: false,
      logged: true,
      error: null,
    },
  },
];

/**
 * ContentLogDemo - Demonstrates the content logging and display system
 */
export function ContentLogDemo() {
  // Parse the sample message text into structured format
  const parsedMessage = parseBusinessMessage(SAMPLE_MESSAGE_TEXT);

  return (
    <div className="min-h-screen bg-slate-100 py-8 px-4">
      <div className="max-w-4xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center">
          <h1 className="text-3xl font-bold text-slate-900">
            Content Logging & Display System
          </h1>
          <p className="text-slate-600 mt-2">
            Structured logging for invoices, messages, and workflow content
          </p>
        </div>

        <Separator />

        {/* Tabs for different views */}
        <Tabs defaultValue="rendered" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="rendered">Rendered View</TabsTrigger>
            <TabsTrigger value="structured">Structured Log</TabsTrigger>
            <TabsTrigger value="json">JSON Format</TabsTrigger>
            <TabsTrigger value="list">Log List</TabsTrigger>
          </TabsList>

          {/* Rendered Message View */}
          <TabsContent value="rendered" className="mt-6">
            <div className="space-y-4">
              <h2 className="text-xl font-semibold text-slate-800">
                Rendered Business Message
              </h2>
              <p className="text-slate-600 text-sm">
                This is how the invoice reminder appears when rendered on the front end.
              </p>
              <BusinessMessageViewer message={parsedMessage} />
            </div>
          </TabsContent>

          {/* Structured Log Entry View */}
          <TabsContent value="structured" className="mt-6">
            <div className="space-y-4">
              <h2 className="text-xl font-semibold text-slate-800">
                Structured Log Entry
              </h2>
              <p className="text-slate-600 text-sm">
                This is the structured log format used by the n8n workflow for tracking.
              </p>
              <ContentLogEntry entry={SAMPLE_FOLLOWUP_LOG} />
            </div>
          </TabsContent>

          {/* JSON Format View */}
          <TabsContent value="json" className="mt-6">
            <div className="space-y-6">
              <div>
                <h2 className="text-xl font-semibold text-slate-800 mb-2">
                  JSON Log Format
                </h2>
                <p className="text-slate-600 text-sm mb-4">
                  This is the JSON structure that should be logged to Google Sheets or your database.
                </p>
                <JsonLogViewer data={SAMPLE_FOLLOWUP_LOG} title="Invoice Follow-up Log Entry" />
              </div>

              <Separator />

              <div>
                <h3 className="text-lg font-semibold text-slate-800 mb-2">
                  Parsed Message Structure
                </h3>
                <p className="text-slate-600 text-sm mb-4">
                  Raw message text parsed into structured format for display.
                </p>
                <JsonLogViewer data={parsedMessage} title="Parsed Business Message" />
              </div>
            </div>
          </TabsContent>

          {/* Log List View */}
          <TabsContent value="list" className="mt-6">
            <div className="space-y-4">
              <h2 className="text-xl font-semibold text-slate-800">
                Activity Log
              </h2>
              <p className="text-slate-600 text-sm">
                Multiple log entries displayed in a list format for tracking workflow activity.
              </p>
              <ContentLogList entries={SAMPLE_LOG_ENTRIES} />
            </div>
          </TabsContent>
        </Tabs>

        <Separator />

        {/* Schema Reference */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Logging Schema Reference</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <h4 className="font-semibold text-slate-800 mb-2">Content Types</h4>
                <div className="space-y-1">
                  <Badge variant="outline">invoice_followup</Badge>
                  <Badge variant="outline">owner_alert</Badge>
                  <Badge variant="outline">silence_breaker</Badge>
                  <Badge variant="outline">auto_reply</Badge>
                  <Badge variant="outline">task</Badge>
                  <Badge variant="outline">adjuster_draft</Badge>
                </div>
              </div>
              <div>
                <h4 className="font-semibold text-slate-800 mb-2">Tone Levels</h4>
                <div className="space-y-1">
                  <Badge className="bg-green-100 text-green-800">friendly</Badge>
                  <Badge className="bg-blue-100 text-blue-800">professional</Badge>
                  <Badge className="bg-yellow-100 text-yellow-800">firm</Badge>
                  <Badge className="bg-orange-100 text-orange-800">urgent</Badge>
                  <Badge className="bg-red-100 text-red-800">final</Badge>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default ContentLogDemo;
