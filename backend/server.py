from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
import base64
import aiofiles
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from fastapi.responses import StreamingResponse
import json
import csv
from io import StringIO

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Config
JWT_SECRET = os.environ.get('JWT_SECRET', 'default-secret')
JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS256')
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get('ACCESS_TOKEN_EXPIRE_MINUTES', 1440))

# Create the main app
app = FastAPI(title="RestorationOS API")
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============ MODELS ============

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str = "user"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    email: str
    name: str
    role: str
    created_at: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# Job Models
class JobLineItem(BaseModel):
    description: str
    quantity: float = 1
    unit: str = "each"
    unit_price: float = 0
    item_type: str = "labor"  # labor, equipment, material
    is_taxable: bool = True

class JobCreate(BaseModel):
    title: str
    customer_name: str
    customer_phone: str
    customer_email: Optional[str] = None
    address: str
    scope: str
    priority: str = "medium"  # low, medium, high, urgent
    status: str = "pending"  # pending, scheduled, in_progress, completed, cancelled
    assigned_crew_id: Optional[str] = None
    scheduled_date: Optional[str] = None
    estimated_completion: Optional[str] = None
    notes: Optional[str] = None
    line_items: List[JobLineItem] = []

class JobUpdate(BaseModel):
    title: Optional[str] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    address: Optional[str] = None
    scope: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    assigned_crew_id: Optional[str] = None
    scheduled_date: Optional[str] = None
    estimated_completion: Optional[str] = None
    notes: Optional[str] = None
    line_items: Optional[List[JobLineItem]] = None

class JobResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    title: str
    customer_name: str
    customer_phone: str
    customer_email: Optional[str] = None
    address: str
    scope: str
    priority: str
    status: str
    assigned_crew_id: Optional[str] = None
    scheduled_date: Optional[str] = None
    estimated_completion: Optional[str] = None
    notes: Optional[str] = None
    line_items: List[JobLineItem] = []
    total_amount: float = 0
    created_at: str
    updated_at: str
    created_by: str

# Crew Models
class CrewMember(BaseModel):
    name: str
    role: str
    phone: str
    hourly_rate: float = 0

class CrewCreate(BaseModel):
    name: str
    members: List[CrewMember] = []
    specialty: str = "general"  # water, fire, mold, general
    status: str = "available"  # available, busy, off

class CrewUpdate(BaseModel):
    name: Optional[str] = None
    members: Optional[List[CrewMember]] = None
    specialty: Optional[str] = None
    status: Optional[str] = None

class CrewResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    name: str
    members: List[CrewMember] = []
    specialty: str
    status: str
    created_at: str
    updated_at: str

# Invoice Models
class InvoiceCreate(BaseModel):
    job_id: str
    due_date: str
    notes: Optional[str] = None
    tax_rate: float = 8.25

class InvoiceResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    invoice_number: str
    job_id: str
    customer_name: str
    customer_email: Optional[str] = None
    address: str
    line_items: List[Dict[str, Any]] = []
    subtotal: float
    tax_amount: float
    total: float
    status: str  # draft, sent, paid, overdue
    due_date: str
    notes: Optional[str] = None
    created_at: str

# Work Order Models
class WorkOrderTask(BaseModel):
    description: str
    is_completed: bool = False
    assigned_to: Optional[str] = None

class WorkOrderCreate(BaseModel):
    job_id: str
    tasks: List[WorkOrderTask] = []
    materials_needed: List[str] = []
    notes: Optional[str] = None

class WorkOrderResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    job_id: str
    job_title: str
    tasks: List[Dict[str, Any]] = []
    materials_needed: List[str] = []
    completion_percentage: float
    status: str
    notes: Optional[str] = None
    created_at: str
    updated_at: str

# Expense Models
class ExpenseCreate(BaseModel):
    description: str
    amount: float
    category: str  # labor, equipment, materials, overhead, subcontractor, other
    job_id: Optional[str] = None
    vendor: Optional[str] = None
    date: str
    is_taxable: bool = False
    receipt_data: Optional[str] = None

class ExpenseResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    description: str
    amount: float
    category: str
    job_id: Optional[str] = None
    vendor: Optional[str] = None
    date: str
    is_taxable: bool
    status: str  # pending, approved, exported
    created_at: str

# Job Log Models
class JobLogCreate(BaseModel):
    job_id: str
    entry_type: str  # note, photo, progress, issue
    content: str
    photo_data: Optional[str] = None

class JobLogResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    job_id: str
    entry_type: str
    content: str
    photo_url: Optional[str] = None
    created_by: str
    created_at: str

# Transaction Models
class TransactionCreate(BaseModel):
    description: str
    amount: float
    transaction_type: str  # income, expense
    date: str
    reference: Optional[str] = None
    matched_invoice_id: Optional[str] = None
    matched_expense_id: Optional[str] = None

class TransactionResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    description: str
    amount: float
    transaction_type: str
    date: str
    reference: Optional[str] = None
    matched_invoice_id: Optional[str] = None
    matched_expense_id: Optional[str] = None
    is_matched: bool
    created_at: str

# AI Message Models
class AIMessageRequest(BaseModel):
    message_type: str  # scheduling, arrival, progress, payment, custom
    job_id: Optional[str] = None
    customer_name: str
    custom_context: Optional[str] = None

class AIMessageResponse(BaseModel):
    message: str
    message_type: str

# Report Models
class CashFlowForecast(BaseModel):
    period: str
    expected_income: float
    expected_expenses: float
    net_cash_flow: float

# ============ AUTH HELPERS ============

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ============ AUTH ROUTES ============

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    user_doc = {
        "id": user_id,
        "email": user_data.email,
        "password": hash_password(user_data.password),
        "name": user_data.name,
        "role": user_data.role,
        "created_at": now
    }
    await db.users.insert_one(user_doc)
    
    token = create_access_token({"sub": user_id})
    user_response = UserResponse(
        id=user_id,
        email=user_data.email,
        name=user_data.name,
        role=user_data.role,
        created_at=now
    )
    return TokenResponse(access_token=token, user=user_response)

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"sub": user["id"]})
    user_response = UserResponse(
        id=user["id"],
        email=user["email"],
        name=user["name"],
        role=user["role"],
        created_at=user["created_at"]
    )
    return TokenResponse(access_token=token, user=user_response)

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(**current_user)

# ============ JOBS ROUTES ============

@api_router.post("/jobs", response_model=JobResponse)
async def create_job(job_data: JobCreate, current_user: dict = Depends(get_current_user)):
    job_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    # Calculate total amount
    total = sum(item.quantity * item.unit_price for item in job_data.line_items)
    
    job_doc = {
        "id": job_id,
        **job_data.model_dump(),
        "line_items": [item.model_dump() for item in job_data.line_items],
        "total_amount": total,
        "created_at": now,
        "updated_at": now,
        "created_by": current_user["id"]
    }
    await db.jobs.insert_one(job_doc)
    return JobResponse(**job_doc)

@api_router.get("/jobs", response_model=List[JobResponse])
async def get_jobs(current_user: dict = Depends(get_current_user)):
    jobs = await db.jobs.find({}, {"_id": 0}).to_list(1000)
    return [JobResponse(**job) for job in jobs]

@api_router.get("/jobs/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, current_user: dict = Depends(get_current_user)):
    job = await db.jobs.find_one({"id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse(**job)

@api_router.put("/jobs/{job_id}", response_model=JobResponse)
async def update_job(job_id: str, job_data: JobUpdate, current_user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in job_data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    if "line_items" in update_data:
        update_data["line_items"] = [item.model_dump() if hasattr(item, 'model_dump') else item for item in update_data["line_items"]]
        update_data["total_amount"] = sum(item["quantity"] * item["unit_price"] for item in update_data["line_items"])
    
    await db.jobs.update_one({"id": job_id}, {"$set": update_data})
    job = await db.jobs.find_one({"id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse(**job)

@api_router.delete("/jobs/{job_id}")
async def delete_job(job_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.jobs.delete_one({"id": job_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"message": "Job deleted"}

# ============ CREWS ROUTES ============

@api_router.post("/crews", response_model=CrewResponse)
async def create_crew(crew_data: CrewCreate, current_user: dict = Depends(get_current_user)):
    crew_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    crew_doc = {
        "id": crew_id,
        **crew_data.model_dump(),
        "members": [m.model_dump() for m in crew_data.members],
        "created_at": now,
        "updated_at": now
    }
    await db.crews.insert_one(crew_doc)
    return CrewResponse(**crew_doc)

@api_router.get("/crews", response_model=List[CrewResponse])
async def get_crews(current_user: dict = Depends(get_current_user)):
    crews = await db.crews.find({}, {"_id": 0}).to_list(100)
    return [CrewResponse(**crew) for crew in crews]

@api_router.get("/crews/{crew_id}", response_model=CrewResponse)
async def get_crew(crew_id: str, current_user: dict = Depends(get_current_user)):
    crew = await db.crews.find_one({"id": crew_id}, {"_id": 0})
    if not crew:
        raise HTTPException(status_code=404, detail="Crew not found")
    return CrewResponse(**crew)

@api_router.put("/crews/{crew_id}", response_model=CrewResponse)
async def update_crew(crew_id: str, crew_data: CrewUpdate, current_user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in crew_data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    if "members" in update_data:
        update_data["members"] = [m.model_dump() if hasattr(m, 'model_dump') else m for m in update_data["members"]]
    
    await db.crews.update_one({"id": crew_id}, {"$set": update_data})
    crew = await db.crews.find_one({"id": crew_id}, {"_id": 0})
    if not crew:
        raise HTTPException(status_code=404, detail="Crew not found")
    return CrewResponse(**crew)

@api_router.delete("/crews/{crew_id}")
async def delete_crew(crew_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.crews.delete_one({"id": crew_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Crew not found")
    return {"message": "Crew deleted"}

# ============ INVOICES ROUTES ============

@api_router.post("/invoices", response_model=InvoiceResponse)
async def create_invoice(invoice_data: InvoiceCreate, current_user: dict = Depends(get_current_user)):
    job = await db.jobs.find_one({"id": invoice_data.job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    invoice_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    invoice_number = f"INV-{now.strftime('%Y%m%d')}-{invoice_id[:8].upper()}"
    
    # Calculate totals
    subtotal = sum(item["quantity"] * item["unit_price"] for item in job.get("line_items", []))
    taxable_subtotal = sum(
        item["quantity"] * item["unit_price"] 
        for item in job.get("line_items", []) 
        if item.get("is_taxable", True)
    )
    tax_amount = round(taxable_subtotal * (invoice_data.tax_rate / 100), 2)
    total = round(subtotal + tax_amount, 2)
    
    invoice_doc = {
        "id": invoice_id,
        "invoice_number": invoice_number,
        "job_id": invoice_data.job_id,
        "customer_name": job["customer_name"],
        "customer_email": job.get("customer_email"),
        "address": job["address"],
        "line_items": job.get("line_items", []),
        "subtotal": subtotal,
        "tax_rate": invoice_data.tax_rate,
        "tax_amount": tax_amount,
        "total": total,
        "status": "draft",
        "due_date": invoice_data.due_date,
        "notes": invoice_data.notes,
        "created_at": now.isoformat(),
        "created_by": current_user["id"]
    }
    await db.invoices.insert_one(invoice_doc)
    return InvoiceResponse(**invoice_doc)

@api_router.get("/invoices", response_model=List[InvoiceResponse])
async def get_invoices(current_user: dict = Depends(get_current_user)):
    invoices = await db.invoices.find({}, {"_id": 0}).to_list(1000)
    return [InvoiceResponse(**inv) for inv in invoices]

@api_router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(invoice_id: str, current_user: dict = Depends(get_current_user)):
    invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return InvoiceResponse(**invoice)

@api_router.put("/invoices/{invoice_id}/status")
async def update_invoice_status(invoice_id: str, status: str, current_user: dict = Depends(get_current_user)):
    await db.invoices.update_one({"id": invoice_id}, {"$set": {"status": status}})
    return {"message": "Status updated"}

@api_router.get("/invoices/{invoice_id}/pdf")
async def get_invoice_pdf(invoice_id: str, current_user: dict = Depends(get_current_user)):
    invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    # Header
    elements.append(Paragraph(f"<b>INVOICE {invoice['invoice_number']}</b>", styles['Title']))
    elements.append(Spacer(1, 0.25*inch))
    elements.append(Paragraph(f"Customer: {invoice['customer_name']}", styles['Normal']))
    elements.append(Paragraph(f"Address: {invoice['address']}", styles['Normal']))
    elements.append(Paragraph(f"Due Date: {invoice['due_date']}", styles['Normal']))
    elements.append(Spacer(1, 0.5*inch))
    
    # Line items table
    table_data = [["Description", "Qty", "Unit", "Price", "Total"]]
    for item in invoice.get("line_items", []):
        total = item["quantity"] * item["unit_price"]
        table_data.append([
            item["description"],
            str(item["quantity"]),
            item["unit"],
            f"${item['unit_price']:.2f}",
            f"${total:.2f}"
        ])
    
    table = Table(table_data, colWidths=[3*inch, 0.75*inch, 0.75*inch, 1*inch, 1*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F172A')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#E2E8F0')),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 0.5*inch))
    
    # Totals
    elements.append(Paragraph(f"<b>Subtotal:</b> ${invoice['subtotal']:.2f}", styles['Normal']))
    elements.append(Paragraph(f"<b>Tax:</b> ${invoice['tax_amount']:.2f}", styles['Normal']))
    elements.append(Paragraph(f"<b>Total:</b> ${invoice['total']:.2f}", styles['Heading2']))
    
    doc.build(elements)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={invoice['invoice_number']}.pdf"}
    )

# ============ WORK ORDERS ROUTES ============

@api_router.post("/work-orders", response_model=WorkOrderResponse)
async def create_work_order(wo_data: WorkOrderCreate, current_user: dict = Depends(get_current_user)):
    job = await db.jobs.find_one({"id": wo_data.job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    wo_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    tasks = [task.model_dump() for task in wo_data.tasks] if wo_data.tasks else []
    
    wo_doc = {
        "id": wo_id,
        "job_id": wo_data.job_id,
        "job_title": job["title"],
        "tasks": tasks,
        "materials_needed": wo_data.materials_needed,
        "completion_percentage": 0,
        "status": "pending",
        "notes": wo_data.notes,
        "created_at": now,
        "updated_at": now,
        "created_by": current_user["id"]
    }
    await db.work_orders.insert_one(wo_doc)
    return WorkOrderResponse(**wo_doc)

@api_router.get("/work-orders", response_model=List[WorkOrderResponse])
async def get_work_orders(current_user: dict = Depends(get_current_user)):
    work_orders = await db.work_orders.find({}, {"_id": 0}).to_list(1000)
    return [WorkOrderResponse(**wo) for wo in work_orders]

@api_router.get("/work-orders/{wo_id}", response_model=WorkOrderResponse)
async def get_work_order(wo_id: str, current_user: dict = Depends(get_current_user)):
    wo = await db.work_orders.find_one({"id": wo_id}, {"_id": 0})
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    return WorkOrderResponse(**wo)

@api_router.put("/work-orders/{wo_id}/tasks")
async def update_work_order_tasks(wo_id: str, tasks: List[Dict], current_user: dict = Depends(get_current_user)):
    completed = sum(1 for t in tasks if t.get("is_completed", False))
    percentage = (completed / len(tasks) * 100) if tasks else 0
    status = "completed" if percentage == 100 else "in_progress" if percentage > 0 else "pending"
    
    await db.work_orders.update_one(
        {"id": wo_id},
        {"$set": {
            "tasks": tasks,
            "completion_percentage": percentage,
            "status": status,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    return {"message": "Tasks updated", "completion_percentage": percentage}

# ============ EXPENSES ROUTES ============

@api_router.post("/expenses", response_model=ExpenseResponse)
async def create_expense(expense_data: ExpenseCreate, current_user: dict = Depends(get_current_user)):
    expense_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    expense_doc = {
        "id": expense_id,
        **expense_data.model_dump(),
        "status": "pending",
        "created_at": now,
        "created_by": current_user["id"]
    }
    del expense_doc["receipt_data"]  # Don't store base64 in main doc
    await db.expenses.insert_one(expense_doc)
    return ExpenseResponse(**expense_doc)

@api_router.get("/expenses", response_model=List[ExpenseResponse])
async def get_expenses(current_user: dict = Depends(get_current_user)):
    expenses = await db.expenses.find({}, {"_id": 0}).to_list(1000)
    return [ExpenseResponse(**exp) for exp in expenses]

@api_router.put("/expenses/{expense_id}/status")
async def update_expense_status(expense_id: str, status: str, current_user: dict = Depends(get_current_user)):
    await db.expenses.update_one({"id": expense_id}, {"$set": {"status": status}})
    return {"message": "Status updated"}

@api_router.delete("/expenses/{expense_id}")
async def delete_expense(expense_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.expenses.delete_one({"id": expense_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Expense not found")
    return {"message": "Expense deleted"}

# ============ JOB LOGS ROUTES ============

@api_router.post("/job-logs", response_model=JobLogResponse)
async def create_job_log(log_data: JobLogCreate, current_user: dict = Depends(get_current_user)):
    log_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    photo_url = None
    if log_data.photo_data:
        # Store photo data (in production, upload to S3/cloud storage)
        photo_url = f"/api/photos/{log_id}"
        await db.photos.insert_one({"id": log_id, "data": log_data.photo_data})
    
    log_doc = {
        "id": log_id,
        "job_id": log_data.job_id,
        "entry_type": log_data.entry_type,
        "content": log_data.content,
        "photo_url": photo_url,
        "created_by": current_user["name"],
        "created_at": now
    }
    await db.job_logs.insert_one(log_doc)
    return JobLogResponse(**log_doc)

@api_router.get("/job-logs/{job_id}", response_model=List[JobLogResponse])
async def get_job_logs(job_id: str, current_user: dict = Depends(get_current_user)):
    logs = await db.job_logs.find({"job_id": job_id}, {"_id": 0}).to_list(1000)
    return [JobLogResponse(**log) for log in logs]

# ============ TRANSACTIONS ROUTES ============

@api_router.post("/transactions", response_model=TransactionResponse)
async def create_transaction(tx_data: TransactionCreate, current_user: dict = Depends(get_current_user)):
    tx_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    tx_doc = {
        "id": tx_id,
        **tx_data.model_dump(),
        "is_matched": bool(tx_data.matched_invoice_id or tx_data.matched_expense_id),
        "created_at": now
    }
    await db.transactions.insert_one(tx_doc)
    return TransactionResponse(**tx_doc)

@api_router.get("/transactions", response_model=List[TransactionResponse])
async def get_transactions(current_user: dict = Depends(get_current_user)):
    transactions = await db.transactions.find({}, {"_id": 0}).to_list(1000)
    return [TransactionResponse(**tx) for tx in transactions]

@api_router.put("/transactions/{tx_id}/match")
async def match_transaction(tx_id: str, invoice_id: Optional[str] = None, expense_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    update = {
        "matched_invoice_id": invoice_id,
        "matched_expense_id": expense_id,
        "is_matched": bool(invoice_id or expense_id)
    }
    await db.transactions.update_one({"id": tx_id}, {"$set": update})
    return {"message": "Transaction matched"}

# ============ REPORTS ROUTES ============

@api_router.get("/reports/dashboard")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    jobs = await db.jobs.find({}, {"_id": 0}).to_list(1000)
    invoices = await db.invoices.find({}, {"_id": 0}).to_list(1000)
    expenses = await db.expenses.find({}, {"_id": 0}).to_list(1000)
    crews = await db.crews.find({}, {"_id": 0}).to_list(100)
    
    total_revenue = sum(inv["total"] for inv in invoices if inv.get("status") == "paid")
    total_expenses = sum(exp["amount"] for exp in expenses)
    outstanding_invoices = sum(inv["total"] for inv in invoices if inv.get("status") in ["sent", "draft"])
    
    jobs_by_status = {}
    for job in jobs:
        status = job.get("status", "pending")
        jobs_by_status[status] = jobs_by_status.get(status, 0) + 1
    
    return {
        "total_jobs": len(jobs),
        "active_jobs": len([j for j in jobs if j.get("status") in ["scheduled", "in_progress"]]),
        "total_crews": len(crews),
        "available_crews": len([c for c in crews if c.get("status") == "available"]),
        "total_revenue": total_revenue,
        "total_expenses": total_expenses,
        "gross_profit": total_revenue - total_expenses,
        "outstanding_invoices": outstanding_invoices,
        "jobs_by_status": jobs_by_status,
        "pending_invoices": len([inv for inv in invoices if inv.get("status") == "sent"]),
        "recent_jobs": jobs[-5:][::-1] if jobs else []
    }

@api_router.get("/reports/job-costing/{job_id}")
async def get_job_costing(job_id: str, current_user: dict = Depends(get_current_user)):
    job = await db.jobs.find_one({"id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    expenses = await db.expenses.find({"job_id": job_id}, {"_id": 0}).to_list(1000)
    invoices = await db.invoices.find({"job_id": job_id}, {"_id": 0}).to_list(10)
    
    labor_cost = sum(exp["amount"] for exp in expenses if exp.get("category") == "labor")
    equipment_cost = sum(exp["amount"] for exp in expenses if exp.get("category") == "equipment")
    material_cost = sum(exp["amount"] for exp in expenses if exp.get("category") == "materials")
    overhead = sum(exp["amount"] for exp in expenses if exp.get("category") == "overhead")
    total_cost = labor_cost + equipment_cost + material_cost + overhead
    
    revenue = sum(inv["total"] for inv in invoices if inv.get("status") == "paid")
    gross_margin = revenue - total_cost
    margin_percentage = (gross_margin / revenue * 100) if revenue > 0 else 0
    
    return {
        "job_id": job_id,
        "job_title": job["title"],
        "revenue": revenue,
        "costs": {
            "labor": labor_cost,
            "equipment": equipment_cost,
            "materials": material_cost,
            "overhead": overhead,
            "total": total_cost
        },
        "gross_margin": gross_margin,
        "margin_percentage": round(margin_percentage, 2),
        "is_profitable": gross_margin > 0
    }

@api_router.get("/reports/profit-loss")
async def get_profit_loss(current_user: dict = Depends(get_current_user)):
    invoices = await db.invoices.find({"status": "paid"}, {"_id": 0}).to_list(1000)
    expenses = await db.expenses.find({}, {"_id": 0}).to_list(1000)
    
    total_revenue = sum(inv["total"] for inv in invoices)
    
    expenses_by_category = {}
    for exp in expenses:
        cat = exp.get("category", "other")
        expenses_by_category[cat] = expenses_by_category.get(cat, 0) + exp["amount"]
    
    total_expenses = sum(expenses_by_category.values())
    net_profit = total_revenue - total_expenses
    
    return {
        "total_revenue": total_revenue,
        "expenses_by_category": expenses_by_category,
        "total_expenses": total_expenses,
        "net_profit": net_profit,
        "profit_margin": round((net_profit / total_revenue * 100) if total_revenue > 0 else 0, 2)
    }

@api_router.get("/reports/tax-summary")
async def get_tax_summary(current_user: dict = Depends(get_current_user)):
    invoices = await db.invoices.find({}, {"_id": 0}).to_list(1000)
    expenses = await db.expenses.find({}, {"_id": 0}).to_list(1000)
    
    total_sales_tax_collected = sum(inv.get("tax_amount", 0) for inv in invoices if inv.get("status") == "paid")
    taxable_expenses = sum(exp["amount"] for exp in expenses if exp.get("is_taxable", False))
    non_taxable_expenses = sum(exp["amount"] for exp in expenses if not exp.get("is_taxable", False))
    
    return {
        "sales_tax_collected": total_sales_tax_collected,
        "taxable_revenue": sum(inv["subtotal"] for inv in invoices if inv.get("status") == "paid"),
        "taxable_expenses": taxable_expenses,
        "non_taxable_expenses": non_taxable_expenses,
        "estimated_tax_liability": total_sales_tax_collected
    }

@api_router.get("/reports/cash-flow-forecast")
async def get_cash_flow_forecast(current_user: dict = Depends(get_current_user)):
    invoices = await db.invoices.find({"status": {"$in": ["sent", "draft"]}}, {"_id": 0}).to_list(1000)
    expenses = await db.expenses.find({}, {"_id": 0}).to_list(1000)
    
    now = datetime.now(timezone.utc)
    
    # Calculate expected income from outstanding invoices
    expected_income_30 = sum(inv["total"] for inv in invoices)
    avg_monthly_expenses = sum(exp["amount"] for exp in expenses) / 3 if expenses else 0
    
    forecasts = [
        {
            "period": "30 days",
            "expected_income": expected_income_30 * 0.5,
            "expected_expenses": avg_monthly_expenses,
            "net_cash_flow": (expected_income_30 * 0.5) - avg_monthly_expenses
        },
        {
            "period": "60 days",
            "expected_income": expected_income_30 * 0.8,
            "expected_expenses": avg_monthly_expenses * 2,
            "net_cash_flow": (expected_income_30 * 0.8) - (avg_monthly_expenses * 2)
        },
        {
            "period": "90 days",
            "expected_income": expected_income_30,
            "expected_expenses": avg_monthly_expenses * 3,
            "net_cash_flow": expected_income_30 - (avg_monthly_expenses * 3)
        }
    ]
    
    return {"forecasts": forecasts, "outstanding_invoices_total": expected_income_30}

# ============ EXPORT ROUTES ============

@api_router.get("/export/quickbooks")
async def export_quickbooks(data_type: str, current_user: dict = Depends(get_current_user)):
    output = StringIO()
    writer = csv.writer(output)
    
    if data_type == "invoices":
        invoices = await db.invoices.find({}, {"_id": 0}).to_list(1000)
        writer.writerow(["Invoice Number", "Customer", "Date", "Due Date", "Amount", "Status"])
        for inv in invoices:
            writer.writerow([
                inv["invoice_number"],
                inv["customer_name"],
                inv["created_at"][:10],
                inv["due_date"],
                inv["total"],
                inv["status"]
            ])
    elif data_type == "expenses":
        expenses = await db.expenses.find({}, {"_id": 0}).to_list(1000)
        writer.writerow(["Date", "Vendor", "Description", "Category", "Amount", "Taxable"])
        for exp in expenses:
            writer.writerow([
                exp["date"],
                exp.get("vendor", ""),
                exp["description"],
                exp["category"],
                exp["amount"],
                "Yes" if exp.get("is_taxable") else "No"
            ])
    else:
        raise HTTPException(status_code=400, detail="Invalid data type")
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={data_type}_export.csv"}
    )

# ============ AI ROUTES ============

@api_router.post("/ai/generate-message", response_model=AIMessageResponse)
async def generate_ai_message(request: AIMessageRequest, current_user: dict = Depends(get_current_user)):
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="AI service not configured")
    
    job_context = ""
    if request.job_id:
        job = await db.jobs.find_one({"id": request.job_id}, {"_id": 0})
        if job:
            job_context = f"Job: {job['title']} at {job['address']}. Status: {job['status']}. Scope: {job['scope']}"
    
    message_prompts = {
        "scheduling": f"Generate a short, professional text message to {request.customer_name} about scheduling their restoration job. {job_context}",
        "arrival": f"Generate a short, professional text message to {request.customer_name} notifying them that the crew is arriving soon. {job_context}",
        "progress": f"Generate a short, professional text message to {request.customer_name} with a progress update on their restoration work. {job_context}",
        "payment": f"Generate a short, professional but friendly text message to {request.customer_name} as a payment reminder. {job_context}",
        "custom": f"Generate a professional message for {request.customer_name}. Context: {request.custom_context or job_context}"
    }
    
    prompt = message_prompts.get(request.message_type, message_prompts["custom"])
    
    chat = LlmChat(
        api_key=api_key,
        session_id=f"msg-{uuid.uuid4()}",
        system_message="You are a professional assistant for a restoration contracting company. Generate short, friendly, and professional text messages for customer communication. Keep messages under 160 characters when possible."
    ).with_model("openai", "gpt-4o")
    
    user_message = UserMessage(text=prompt)
    response = await chat.send_message(user_message)
    
    return AIMessageResponse(message=response, message_type=request.message_type)

@api_router.post("/ai/analyze-compliance")
async def analyze_compliance(current_user: dict = Depends(get_current_user)):
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="AI service not configured")
    
    # Gather recent data for analysis
    invoices = await db.invoices.find({}, {"_id": 0}).to_list(100)
    expenses = await db.expenses.find({}, {"_id": 0}).to_list(100)
    transactions = await db.transactions.find({}, {"_id": 0}).to_list(100)
    
    # Prepare summary for AI
    data_summary = {
        "invoice_count": len(invoices),
        "expense_count": len(expenses),
        "unmatched_transactions": len([t for t in transactions if not t.get("is_matched")]),
        "overdue_invoices": len([i for i in invoices if i.get("status") == "overdue"]),
        "pending_expenses": len([e for e in expenses if e.get("status") == "pending"]),
        "duplicate_check": "checking for duplicate expenses..."
    }
    
    # Check for potential duplicates
    expense_hashes = {}
    duplicates = []
    for exp in expenses:
        key = f"{exp['date']}_{exp['amount']}_{exp['vendor'] if exp.get('vendor') else ''}"
        if key in expense_hashes:
            duplicates.append(exp["description"])
        expense_hashes[key] = True
    
    chat = LlmChat(
        api_key=api_key,
        session_id=f"compliance-{uuid.uuid4()}",
        system_message="You are a financial compliance analyst for a restoration company. Analyze the provided data and identify potential issues, risks, or compliance concerns. Be concise and actionable."
    ).with_model("openai", "gpt-4o")
    
    prompt = f"""Analyze this restoration company's financial data for compliance issues:
    - Total invoices: {data_summary['invoice_count']}
    - Total expenses: {data_summary['expense_count']}
    - Unmatched bank transactions: {data_summary['unmatched_transactions']}
    - Overdue invoices: {data_summary['overdue_invoices']}
    - Pending expenses needing approval: {data_summary['pending_expenses']}
    - Potential duplicate expenses: {len(duplicates)} found
    
    Provide a brief compliance report with any concerns and recommendations."""
    
    user_message = UserMessage(text=prompt)
    response = await chat.send_message(user_message)
    
    return {
        "analysis": response,
        "potential_duplicates": duplicates,
        "unmatched_transactions": data_summary["unmatched_transactions"],
        "action_items": [
            f"Review {len(duplicates)} potential duplicate expenses" if duplicates else None,
            f"Match {data_summary['unmatched_transactions']} bank transactions" if data_summary['unmatched_transactions'] > 0 else None,
            f"Follow up on {data_summary['overdue_invoices']} overdue invoices" if data_summary['overdue_invoices'] > 0 else None
        ]
    }

@api_router.post("/ai/forecast-cashflow")
async def ai_forecast_cashflow(current_user: dict = Depends(get_current_user)):
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="AI service not configured")
    
    invoices = await db.invoices.find({}, {"_id": 0}).to_list(1000)
    expenses = await db.expenses.find({}, {"_id": 0}).to_list(1000)
    jobs = await db.jobs.find({}, {"_id": 0}).to_list(1000)
    
    outstanding = sum(inv["total"] for inv in invoices if inv.get("status") in ["sent", "draft"])
    recent_revenue = sum(inv["total"] for inv in invoices if inv.get("status") == "paid")
    total_expenses = sum(exp["amount"] for exp in expenses)
    active_jobs = len([j for j in jobs if j.get("status") in ["scheduled", "in_progress"]])
    
    chat = LlmChat(
        api_key=api_key,
        session_id=f"forecast-{uuid.uuid4()}",
        system_message="You are a financial analyst for a restoration company. Provide realistic cash flow forecasts and business insights based on the data provided."
    ).with_model("openai", "gpt-4o")
    
    prompt = f"""Based on this restoration company data, provide a cash flow analysis:
    - Outstanding invoices: ${outstanding:,.2f}
    - Recent paid revenue: ${recent_revenue:,.2f}
    - Total expenses: ${total_expenses:,.2f}
    - Active jobs in progress: {active_jobs}
    
    Provide insights on cash flow health and recommendations for the next 90 days."""
    
    user_message = UserMessage(text=prompt)
    response = await chat.send_message(user_message)
    
    return {
        "ai_analysis": response,
        "metrics": {
            "outstanding_invoices": outstanding,
            "recent_revenue": recent_revenue,
            "total_expenses": total_expenses,
            "active_jobs": active_jobs
        }
    }

# ============ HEALTH CHECK ============

@api_router.get("/")
async def root():
    return {"message": "RestorationOS API is running"}

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()}

# Include router and add middleware
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
