# RestorationOS - AI Operations Assistant
## Product Requirements Document

### Original Problem Statement
Build an AI operations assistant for a restoration contracting company to manage:
- Jobs, crews, invoicing, job costing
- Customer communication
- Accounting (QuickBooks-ready)
- Financial reports and forecasting
- Compliance review

### User Personas
1. **Office Manager** - Handles invoicing, accounting, customer communication
2. **Field Supervisor** - Manages crews, work orders, job logs
3. **Business Owner** - Views reports, monitors profitability, forecasts cash flow

### Core Requirements (Static)
- JWT-based authentication
- Job management with status tracking
- Crew management with member tracking
- Invoice generation with PDF export
- Work orders with task checklists
- Expense tracking
- Financial reports (P&L, Tax Summary, Cash Flow)
- AI-powered customer message generation
- AI compliance analysis
- AI cash flow forecasting
- QuickBooks-ready CSV exports

### What's Been Implemented (December 27, 2025)

#### Backend (FastAPI + MongoDB)
- [x] User authentication (register/login with JWT)
- [x] Jobs CRUD with line items, status, priority
- [x] Crews CRUD with members and hourly rates
- [x] Invoices with automatic calculation from jobs
- [x] Invoice PDF generation (ReportLab)
- [x] Work Orders with task management
- [x] Expenses tracking with categories
- [x] Transactions tracking
- [x] Dashboard statistics endpoint
- [x] Financial reports (P&L, Tax Summary, Cash Flow Forecast)
- [x] QuickBooks CSV export (invoices, expenses)
- [x] AI Message Generation (OpenAI GPT-4o)
- [x] AI Compliance Analysis
- [x] AI Cash Flow Forecasting

#### Frontend (React + Tailwind + Shadcn)
- [x] Login/Register pages
- [x] Dashboard with metrics cards
- [x] Jobs management page
- [x] Crews management page
- [x] Invoices page with PDF download
- [x] Work Orders page with task toggle
- [x] Accounting page (Expenses + Transactions tabs)
- [x] Reports page (P&L, Tax, Cash Flow)
- [x] AI Assistant page with 3 AI features
- [x] Responsive sidebar navigation

### Prioritized Backlog

#### P0 (Critical) - DONE
- ✅ Authentication
- ✅ Jobs CRUD
- ✅ Invoicing
- ✅ Work Orders
- ✅ Basic Reports

#### P1 (High Priority) - For Next Phase
- Job costing per job (link expenses to jobs)
- Photo upload for job logs
- Bank transaction matching
- Real-time crew scheduling calendar
- Email integration for invoices

#### P2 (Medium Priority)
- Mobile-optimized field worker view
- Customer portal for invoice payment
- Recurring expense templates
- Equipment inventory tracking
- Sub-contractor management

#### P3 (Nice to Have)
- Insurance claim integration
- Weather-based scheduling
- Route optimization for crews
- Multi-company support

### Next Tasks
1. Add photo upload capability to job logs
2. Implement job-expense linking for true job costing
3. Add calendar view for crew scheduling
4. Build bank transaction import from CSV
5. Add email sending for invoices
