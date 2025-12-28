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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============ ENUMS & CONSTANTS ============

JOB_PHASES = ["intake", "emergency_services", "drying_remediation", "repairs_rebuild", "closeout"]
JOB_STATUSES = ["pending", "scheduled", "in_progress", "on_hold", "completed", "cancelled"]
LOSS_TYPES = ["water", "fire", "mold", "storm", "sewage", "biohazard", "vandalism", "other"]
INSURANCE_STATUSES = ["pending", "submitted", "approved", "partial_approved", "denied", "paid", "closed"]
FOLLOWUP_SCHEDULE = [3, 7, 14, 21, 30, 45, 60, 90]  # Days after invoice

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

# Job Models - Enhanced
class InsuranceClaim(BaseModel):
    carrier: str = ""
    adjuster_name: str = ""
    adjuster_phone: str = ""
    adjuster_email: str = ""
    claim_number: str = ""
    policy_number: str = ""
    deductible: float = 0
    status: str = "pending"  # pending, submitted, approved, partial_approved, denied, paid, closed
    date_of_loss: Optional[str] = None
    date_submitted: Optional[str] = None
    date_approved: Optional[str] = None
    approved_amount: float = 0
    depreciation_withheld: float = 0
    notes: str = ""

class JobLineItem(BaseModel):
    description: str
    quantity: float = 1
    unit: str = "each"
    unit_price: float = 0
    item_type: str = "labor"  # labor, equipment, material, subcontractor
    is_taxable: bool = True
    phase: str = "general"

class PaymentRecord(BaseModel):
    date: str
    amount: float
    payment_type: str = "insurance"  # insurance, customer, deductible, depreciation_recovery
    reference: str = ""
    notes: str = ""

class JobCreate(BaseModel):
    # Customer Info
    customer_name: str
    customer_phone: str
    customer_email: Optional[str] = None
    property_address: str
    billing_address: Optional[str] = None
    
    # Job Details
    title: str
    loss_type: str = "water"  # water, fire, mold, storm, etc.
    loss_date: Optional[str] = None
    scope: str
    priority: str = "medium"
    status: str = "pending"
    current_phase: str = "intake"
    
    # Assignment
    assigned_crew_id: Optional[str] = None
    project_manager: Optional[str] = None
    
    # Scheduling
    scheduled_date: Optional[str] = None
    estimated_completion: Optional[str] = None
    
    # Insurance
    insurance_claim: Optional[InsuranceClaim] = None
    
    # Financial
    estimated_amount: float = 0
    budget_amount: float = 0
    
    notes: Optional[str] = None
    line_items: List[JobLineItem] = []

class JobUpdate(BaseModel):
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    property_address: Optional[str] = None
    billing_address: Optional[str] = None
    title: Optional[str] = None
    loss_type: Optional[str] = None
    loss_date: Optional[str] = None
    scope: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    current_phase: Optional[str] = None
    assigned_crew_id: Optional[str] = None
    project_manager: Optional[str] = None
    scheduled_date: Optional[str] = None
    estimated_completion: Optional[str] = None
    insurance_claim: Optional[InsuranceClaim] = None
    estimated_amount: Optional[float] = None
    budget_amount: Optional[float] = None
    notes: Optional[str] = None
    line_items: Optional[List[JobLineItem]] = None

# Crew Models
class CrewMember(BaseModel):
    id: str = ""
    name: str
    role: str
    phone: str = ""
    hourly_rate: float = 0
    is_active: bool = True

class CrewCreate(BaseModel):
    name: str
    members: List[CrewMember] = []
    specialty: str = "general"
    status: str = "available"
    home_base: str = ""

class CrewUpdate(BaseModel):
    name: Optional[str] = None
    members: Optional[List[CrewMember]] = None
    specialty: Optional[str] = None
    status: Optional[str] = None
    home_base: Optional[str] = None

# Work Order Models - Enhanced
class WorkOrderTask(BaseModel):
    id: str = ""
    description: str
    is_completed: bool = False
    assigned_to: Optional[str] = None
    completed_at: Optional[str] = None
    completed_by: Optional[str] = None

class WorkOrderCheckpoint(BaseModel):
    description: str
    is_verified: bool = False
    verified_at: Optional[str] = None
    verified_by: Optional[str] = None

class WorkOrderCreate(BaseModel):
    job_id: str
    phase: str = "general"
    tasks: List[WorkOrderTask] = []
    materials_needed: List[str] = []
    equipment_needed: List[str] = []
    checkpoints: List[WorkOrderCheckpoint] = []
    notes: Optional[str] = None

# Daily Job Log Models
class LaborEntry(BaseModel):
    crew_member_name: str
    hours: float
    hourly_rate: float = 0
    task_description: str = ""

class EquipmentEntry(BaseModel):
    equipment_name: str
    quantity: int = 1
    daily_rate: float = 0
    notes: str = ""

class MaterialEntry(BaseModel):
    material_name: str
    quantity: float
    unit: str = "each"
    unit_cost: float = 0

class DailyLogCreate(BaseModel):
    job_id: str
    date: str
    phase: str = "general"
    labor_entries: List[LaborEntry] = []
    equipment_entries: List[EquipmentEntry] = []
    material_entries: List[MaterialEntry] = []
    weather_conditions: str = ""
    work_performed: str = ""
    issues_encountered: str = ""
    photos: List[str] = []
    notes: str = ""

# Invoice Models - Enhanced
class InvoiceCreate(BaseModel):
    job_id: str
    due_date: str
    invoice_type: str = "progress"  # progress, final, supplement
    phase: Optional[str] = None
    notes: Optional[str] = None
    tax_rate: float = 8.25
    include_line_items: bool = True
    custom_line_items: List[JobLineItem] = []

# Expense Models
class ExpenseCreate(BaseModel):
    description: str
    amount: float
    category: str
    job_id: Optional[str] = None
    vendor: Optional[str] = None
    date: str
    is_taxable: bool = False
    phase: Optional[str] = None
    receipt_data: Optional[str] = None

# Communication Log
class CommunicationLogCreate(BaseModel):
    job_id: str
    contact_type: str  # customer, adjuster, carrier, subcontractor, internal
    contact_name: str
    method: str  # phone, email, text, in_person
    direction: str  # inbound, outbound
    subject: str
    content: str
    follow_up_required: bool = False
    follow_up_date: Optional[str] = None

# Photo Upload
class PhotoUpload(BaseModel):
    photo_data: str
    caption: Optional[str] = ""

# AI Message Request
class AIMessageRequest(BaseModel):
    message_type: str
    job_id: Optional[str] = None
    customer_name: str
    custom_context: Optional[str] = None

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
    user_response = UserResponse(id=user_id, email=user_data.email, name=user_data.name, role=user_data.role, created_at=now)
    return TokenResponse(access_token=token, user=user_response)

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"sub": user["id"]})
    user_response = UserResponse(id=user["id"], email=user["email"], name=user["name"], role=user["role"], created_at=user["created_at"])
    return TokenResponse(access_token=token, user=user_response)

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(**current_user)

# ============ JOBS ROUTES ============

@api_router.post("/jobs")
async def create_job(job_data: JobCreate, current_user: dict = Depends(get_current_user)):
    job_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    total = sum(item.quantity * item.unit_price for item in job_data.line_items)
    
    job_doc = {
        "id": job_id,
        **job_data.model_dump(),
        "line_items": [item.model_dump() for item in job_data.line_items],
        "insurance_claim": job_data.insurance_claim.model_dump() if job_data.insurance_claim else None,
        "total_amount": total,
        "payments": [],
        "phase_history": [{"phase": job_data.current_phase, "started_at": now, "ended_at": None}],
        "created_at": now,
        "updated_at": now,
        "created_by": current_user["id"]
    }
    await db.jobs.insert_one(job_doc)
    
    job_doc.pop("_id", None)
    return job_doc

@api_router.get("/jobs")
async def get_jobs(status: Optional[str] = None, phase: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {}
    if status:
        query["status"] = status
    if phase:
        query["current_phase"] = phase
    
    jobs = await db.jobs.find(query, {"_id": 0}).to_list(1000)
    return jobs

@api_router.get("/jobs/{job_id}")
async def get_job(job_id: str, current_user: dict = Depends(get_current_user)):
    job = await db.jobs.find_one({"id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@api_router.put("/jobs/{job_id}")
async def update_job(job_id: str, job_data: JobUpdate, current_user: dict = Depends(get_current_user)):
    job = await db.jobs.find_one({"id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    update_data = {k: v for k, v in job_data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Handle phase change
    if "current_phase" in update_data and update_data["current_phase"] != job.get("current_phase"):
        now = datetime.now(timezone.utc).isoformat()
        phase_history = job.get("phase_history", [])
        if phase_history:
            phase_history[-1]["ended_at"] = now
        phase_history.append({"phase": update_data["current_phase"], "started_at": now, "ended_at": None})
        update_data["phase_history"] = phase_history
    
    if "line_items" in update_data:
        update_data["line_items"] = [item.model_dump() if hasattr(item, 'model_dump') else item for item in update_data["line_items"]]
        update_data["total_amount"] = sum(item["quantity"] * item["unit_price"] for item in update_data["line_items"])
    
    if "insurance_claim" in update_data and update_data["insurance_claim"]:
        update_data["insurance_claim"] = update_data["insurance_claim"].model_dump() if hasattr(update_data["insurance_claim"], 'model_dump') else update_data["insurance_claim"]
    
    await db.jobs.update_one({"id": job_id}, {"$set": update_data})
    updated_job = await db.jobs.find_one({"id": job_id}, {"_id": 0})
    return updated_job

@api_router.delete("/jobs/{job_id}")
async def delete_job(job_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.jobs.delete_one({"id": job_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"message": "Job deleted"}

@api_router.post("/jobs/{job_id}/line-items")
async def add_job_line_item(job_id: str, item: JobLineItem, current_user: dict = Depends(get_current_user)):
    job = await db.jobs.find_one({"id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    line_items = job.get("line_items", [])
    line_items.append(item.model_dump())
    total = sum(i["quantity"] * i["unit_price"] for i in line_items)
    
    await db.jobs.update_one({"id": job_id}, {"$set": {"line_items": line_items, "total_amount": total, "updated_at": datetime.now(timezone.utc).isoformat()}})
    return {"message": "Line item added", "total_amount": total}

@api_router.delete("/jobs/{job_id}/line-items/{item_index}")
async def delete_job_line_item(job_id: str, item_index: int, current_user: dict = Depends(get_current_user)):
    job = await db.jobs.find_one({"id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    line_items = job.get("line_items", [])
    if 0 <= item_index < len(line_items):
        line_items.pop(item_index)
    
    total = sum(i["quantity"] * i["unit_price"] for i in line_items)
    await db.jobs.update_one({"id": job_id}, {"$set": {"line_items": line_items, "total_amount": total, "updated_at": datetime.now(timezone.utc).isoformat()}})
    return {"message": "Line item deleted", "total_amount": total}

@api_router.post("/jobs/{job_id}/payments")
async def add_payment(job_id: str, payment: PaymentRecord, current_user: dict = Depends(get_current_user)):
    job = await db.jobs.find_one({"id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    payments = job.get("payments", [])
    payments.append(payment.model_dump())
    
    await db.jobs.update_one({"id": job_id}, {"$set": {"payments": payments, "updated_at": datetime.now(timezone.utc).isoformat()}})
    return {"message": "Payment recorded"}

@api_router.get("/jobs/{job_id}/details")
async def get_job_details(job_id: str, current_user: dict = Depends(get_current_user)):
    job = await db.jobs.find_one({"id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    crew = None
    if job.get("assigned_crew_id"):
        crew = await db.crews.find_one({"id": job["assigned_crew_id"]}, {"_id": 0})
    
    invoices = await db.invoices.find({"job_id": job_id}, {"_id": 0}).to_list(100)
    work_orders = await db.work_orders.find({"job_id": job_id}, {"_id": 0}).to_list(100)
    expenses = await db.expenses.find({"job_id": job_id}, {"_id": 0}).to_list(1000)
    daily_logs = await db.daily_logs.find({"job_id": job_id}, {"_id": 0}).sort("date", -1).to_list(100)
    logs = await db.job_logs.find({"job_id": job_id}, {"_id": 0}).to_list(1000)
    photos = await db.job_photos.find({"job_id": job_id}, {"_id": 0}).to_list(100)
    communications = await db.communications.find({"job_id": job_id}, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    # Calculate job costing
    total_labor_cost = sum(
        sum(entry.get("hours", 0) * entry.get("hourly_rate", 0) for entry in log.get("labor_entries", []))
        for log in daily_logs
    )
    total_equipment_cost = sum(
        sum(entry.get("quantity", 1) * entry.get("daily_rate", 0) for entry in log.get("equipment_entries", []))
        for log in daily_logs
    )
    total_material_cost = sum(
        sum(entry.get("quantity", 0) * entry.get("unit_cost", 0) for entry in log.get("material_entries", []))
        for log in daily_logs
    )
    total_expenses = sum(exp.get("amount", 0) for exp in expenses)
    
    total_cost = total_labor_cost + total_equipment_cost + total_material_cost + total_expenses
    total_invoiced = sum(inv.get("total", 0) for inv in invoices)
    total_paid = sum(p.get("amount", 0) for p in job.get("payments", []))
    
    # Phase costs
    phase_costs = {}
    for log in daily_logs:
        phase = log.get("phase", "general")
        if phase not in phase_costs:
            phase_costs[phase] = {"labor": 0, "equipment": 0, "materials": 0}
        phase_costs[phase]["labor"] += sum(e.get("hours", 0) * e.get("hourly_rate", 0) for e in log.get("labor_entries", []))
        phase_costs[phase]["equipment"] += sum(e.get("quantity", 1) * e.get("daily_rate", 0) for e in log.get("equipment_entries", []))
        phase_costs[phase]["materials"] += sum(e.get("quantity", 0) * e.get("unit_cost", 0) for e in log.get("material_entries", []))
    
    budget = job.get("budget_amount", 0)
    is_over_budget = total_cost > budget if budget > 0 else False
    
    return {
        "job": job,
        "crew": crew,
        "invoices": invoices,
        "work_orders": work_orders,
        "expenses": expenses,
        "daily_logs": daily_logs,
        "logs": sorted(logs, key=lambda x: x.get("created_at", ""), reverse=True),
        "photos": photos,
        "communications": communications,
        "costing": {
            "labor_cost": total_labor_cost,
            "equipment_cost": total_equipment_cost,
            "material_cost": total_material_cost,
            "other_expenses": total_expenses,
            "total_cost": total_cost,
            "total_invoiced": total_invoiced,
            "total_paid": total_paid,
            "outstanding": total_invoiced - total_paid,
            "gross_margin": total_invoiced - total_cost,
            "margin_percentage": round((total_invoiced - total_cost) / total_invoiced * 100, 2) if total_invoiced > 0 else 0,
            "budget": budget,
            "is_over_budget": is_over_budget,
            "budget_variance": total_cost - budget if budget > 0 else 0,
            "phase_costs": phase_costs
        }
    }

# ============ CREWS ROUTES ============

@api_router.post("/crews")
async def create_crew(crew_data: CrewCreate, current_user: dict = Depends(get_current_user)):
    crew_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    members = []
    for m in crew_data.members:
        member = m.model_dump()
        if not member.get("id"):
            member["id"] = str(uuid.uuid4())
        members.append(member)
    
    crew_doc = {
        "id": crew_id,
        "name": crew_data.name,
        "members": members,
        "specialty": crew_data.specialty,
        "status": crew_data.status,
        "home_base": crew_data.home_base,
        "created_at": now,
        "updated_at": now
    }
    await db.crews.insert_one(crew_doc)
    crew_doc.pop("_id", None)
    return crew_doc

@api_router.get("/crews")
async def get_crews(status: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {}
    if status:
        query["status"] = status
    crews = await db.crews.find(query, {"_id": 0}).to_list(100)
    return crews

@api_router.get("/crews/{crew_id}")
async def get_crew(crew_id: str, current_user: dict = Depends(get_current_user)):
    crew = await db.crews.find_one({"id": crew_id}, {"_id": 0})
    if not crew:
        raise HTTPException(status_code=404, detail="Crew not found")
    return crew

@api_router.put("/crews/{crew_id}")
async def update_crew(crew_id: str, crew_data: CrewUpdate, current_user: dict = Depends(get_current_user)):
    update_data = {k: v for k, v in crew_data.model_dump().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    if "members" in update_data:
        members = []
        for m in update_data["members"]:
            member = m.model_dump() if hasattr(m, 'model_dump') else m
            if not member.get("id"):
                member["id"] = str(uuid.uuid4())
            members.append(member)
        update_data["members"] = members
    
    await db.crews.update_one({"id": crew_id}, {"$set": update_data})
    crew = await db.crews.find_one({"id": crew_id}, {"_id": 0})
    return crew

@api_router.delete("/crews/{crew_id}")
async def delete_crew(crew_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.crews.delete_one({"id": crew_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Crew not found")
    return {"message": "Crew deleted"}

# ============ WORK ORDERS ROUTES ============

@api_router.post("/work-orders")
async def create_work_order(wo_data: WorkOrderCreate, current_user: dict = Depends(get_current_user)):
    job = await db.jobs.find_one({"id": wo_data.job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    wo_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    tasks = []
    for task in wo_data.tasks:
        t = task.model_dump() if hasattr(task, 'model_dump') else task
        if not t.get("id"):
            t["id"] = str(uuid.uuid4())
        tasks.append(t)
    
    checkpoints = [c.model_dump() if hasattr(c, 'model_dump') else c for c in wo_data.checkpoints]
    
    wo_doc = {
        "id": wo_id,
        "job_id": wo_data.job_id,
        "job_title": job["title"],
        "phase": wo_data.phase,
        "tasks": tasks,
        "materials_needed": wo_data.materials_needed,
        "equipment_needed": wo_data.equipment_needed,
        "checkpoints": checkpoints,
        "completion_percentage": 0,
        "status": "pending",
        "notes": wo_data.notes,
        "created_at": now,
        "updated_at": now,
        "created_by": current_user["id"]
    }
    await db.work_orders.insert_one(wo_doc)
    wo_doc.pop("_id", None)
    return wo_doc

@api_router.get("/work-orders")
async def get_work_orders(job_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {}
    if job_id:
        query["job_id"] = job_id
    work_orders = await db.work_orders.find(query, {"_id": 0}).to_list(1000)
    return work_orders

@api_router.get("/work-orders/{wo_id}")
async def get_work_order(wo_id: str, current_user: dict = Depends(get_current_user)):
    wo = await db.work_orders.find_one({"id": wo_id}, {"_id": 0})
    if not wo:
        raise HTTPException(status_code=404, detail="Work order not found")
    return wo

@api_router.put("/work-orders/{wo_id}/tasks")
async def update_work_order_tasks(wo_id: str, tasks: List[Dict], current_user: dict = Depends(get_current_user)):
    now = datetime.now(timezone.utc).isoformat()
    
    for task in tasks:
        if task.get("is_completed") and not task.get("completed_at"):
            task["completed_at"] = now
            task["completed_by"] = current_user["name"]
    
    completed = sum(1 for t in tasks if t.get("is_completed", False))
    percentage = (completed / len(tasks) * 100) if tasks else 0
    status = "completed" if percentage == 100 else "in_progress" if percentage > 0 else "pending"
    
    await db.work_orders.update_one(
        {"id": wo_id},
        {"$set": {"tasks": tasks, "completion_percentage": percentage, "status": status, "updated_at": now}}
    )
    return {"message": "Tasks updated", "completion_percentage": percentage, "status": status}

@api_router.put("/work-orders/{wo_id}/checkpoints")
async def update_work_order_checkpoints(wo_id: str, checkpoints: List[Dict], current_user: dict = Depends(get_current_user)):
    now = datetime.now(timezone.utc).isoformat()
    
    for cp in checkpoints:
        if cp.get("is_verified") and not cp.get("verified_at"):
            cp["verified_at"] = now
            cp["verified_by"] = current_user["name"]
    
    await db.work_orders.update_one({"id": wo_id}, {"$set": {"checkpoints": checkpoints, "updated_at": now}})
    return {"message": "Checkpoints updated"}

# ============ DAILY LOGS ROUTES ============

@api_router.post("/daily-logs")
async def create_daily_log(log_data: DailyLogCreate, current_user: dict = Depends(get_current_user)):
    log_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    log_doc = {
        "id": log_id,
        **log_data.model_dump(),
        "labor_entries": [e.model_dump() for e in log_data.labor_entries],
        "equipment_entries": [e.model_dump() for e in log_data.equipment_entries],
        "material_entries": [e.model_dump() for e in log_data.material_entries],
        "created_by": current_user["name"],
        "created_at": now
    }
    await db.daily_logs.insert_one(log_doc)
    log_doc.pop("_id", None)
    return log_doc

@api_router.get("/daily-logs")
async def get_daily_logs(job_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {}
    if job_id:
        query["job_id"] = job_id
    logs = await db.daily_logs.find(query, {"_id": 0}).sort("date", -1).to_list(1000)
    return logs

@api_router.get("/daily-logs/{log_id}")
async def get_daily_log(log_id: str, current_user: dict = Depends(get_current_user)):
    log = await db.daily_logs.find_one({"id": log_id}, {"_id": 0})
    if not log:
        raise HTTPException(status_code=404, detail="Daily log not found")
    return log

@api_router.put("/daily-logs/{log_id}")
async def update_daily_log(log_id: str, log_data: DailyLogCreate, current_user: dict = Depends(get_current_user)):
    update_data = log_data.model_dump()
    update_data["labor_entries"] = [e.model_dump() if hasattr(e, 'model_dump') else e for e in log_data.labor_entries]
    update_data["equipment_entries"] = [e.model_dump() if hasattr(e, 'model_dump') else e for e in log_data.equipment_entries]
    update_data["material_entries"] = [e.model_dump() if hasattr(e, 'model_dump') else e for e in log_data.material_entries]
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.daily_logs.update_one({"id": log_id}, {"$set": update_data})
    log = await db.daily_logs.find_one({"id": log_id}, {"_id": 0})
    return log

# ============ INVOICES ROUTES ============

@api_router.post("/invoices")
async def create_invoice(invoice_data: InvoiceCreate, current_user: dict = Depends(get_current_user)):
    job = await db.jobs.find_one({"id": invoice_data.job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    invoice_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    invoice_number = f"INV-{now.strftime('%Y%m%d')}-{invoice_id[:8].upper()}"
    
    # Use custom line items or job line items
    if invoice_data.custom_line_items:
        line_items = [item.model_dump() for item in invoice_data.custom_line_items]
    elif invoice_data.include_line_items:
        line_items = job.get("line_items", [])
        if invoice_data.phase:
            line_items = [item for item in line_items if item.get("phase") == invoice_data.phase or item.get("phase") == "general"]
    else:
        line_items = []
    
    subtotal = sum(item["quantity"] * item["unit_price"] for item in line_items)
    taxable_subtotal = sum(item["quantity"] * item["unit_price"] for item in line_items if item.get("is_taxable", True))
    tax_amount = round(taxable_subtotal * (invoice_data.tax_rate / 100), 2)
    total = round(subtotal + tax_amount, 2)
    
    invoice_doc = {
        "id": invoice_id,
        "invoice_number": invoice_number,
        "invoice_type": invoice_data.invoice_type,
        "job_id": invoice_data.job_id,
        "customer_name": job["customer_name"],
        "customer_email": job.get("customer_email"),
        "property_address": job.get("property_address"),
        "billing_address": job.get("billing_address") or job.get("property_address"),
        "line_items": line_items,
        "phase": invoice_data.phase,
        "subtotal": subtotal,
        "tax_rate": invoice_data.tax_rate,
        "tax_amount": tax_amount,
        "total": total,
        "status": "draft",
        "due_date": invoice_data.due_date,
        "notes": invoice_data.notes,
        "insurance_claim": job.get("insurance_claim"),
        "created_at": now.isoformat(),
        "created_by": current_user["id"],
        "followup_schedule": [],
        "last_followup": None
    }
    
    # Generate follow-up schedule
    due_date = datetime.strptime(invoice_data.due_date, "%Y-%m-%d")
    for days in FOLLOWUP_SCHEDULE:
        followup_date = due_date + timedelta(days=days)
        invoice_doc["followup_schedule"].append({
            "day": days,
            "date": followup_date.strftime("%Y-%m-%d"),
            "completed": False,
            "notes": ""
        })
    
    await db.invoices.insert_one(invoice_doc)
    invoice_doc.pop("_id", None)
    return invoice_doc

@api_router.get("/invoices")
async def get_invoices(job_id: Optional[str] = None, status: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {}
    if job_id:
        query["job_id"] = job_id
    if status:
        query["status"] = status
    invoices = await db.invoices.find(query, {"_id": 0}).to_list(1000)
    return invoices

@api_router.get("/invoices/{invoice_id}")
async def get_invoice(invoice_id: str, current_user: dict = Depends(get_current_user)):
    invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    return invoice

@api_router.put("/invoices/{invoice_id}/status")
async def update_invoice_status(invoice_id: str, status: str, current_user: dict = Depends(get_current_user)):
    await db.invoices.update_one({"id": invoice_id}, {"$set": {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}})
    return {"message": "Status updated"}

@api_router.put("/invoices/{invoice_id}/followup")
async def update_invoice_followup(invoice_id: str, day: int, notes: str = "", current_user: dict = Depends(get_current_user)):
    invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    schedule = invoice.get("followup_schedule", [])
    for item in schedule:
        if item["day"] == day:
            item["completed"] = True
            item["notes"] = notes
            item["completed_at"] = datetime.now(timezone.utc).isoformat()
            item["completed_by"] = current_user["name"]
            break
    
    await db.invoices.update_one(
        {"id": invoice_id}, 
        {"$set": {"followup_schedule": schedule, "last_followup": datetime.now(timezone.utc).isoformat()}}
    )
    return {"message": "Follow-up recorded"}

@api_router.get("/invoices/{invoice_id}/pdf")
async def get_invoice_pdf(invoice_id: str, current_user: dict = Depends(get_current_user)):
    invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    elements.append(Paragraph(f"<b>INVOICE {invoice['invoice_number']}</b>", styles['Title']))
    elements.append(Paragraph(f"Type: {invoice.get('invoice_type', 'standard').title()}", styles['Normal']))
    elements.append(Spacer(1, 0.25*inch))
    elements.append(Paragraph(f"Customer: {invoice['customer_name']}", styles['Normal']))
    elements.append(Paragraph(f"Property: {invoice.get('property_address', '')}", styles['Normal']))
    if invoice.get('billing_address') and invoice.get('billing_address') != invoice.get('property_address'):
        elements.append(Paragraph(f"Bill To: {invoice['billing_address']}", styles['Normal']))
    elements.append(Paragraph(f"Due Date: {invoice['due_date']}", styles['Normal']))
    
    if invoice.get('insurance_claim'):
        claim = invoice['insurance_claim']
        if claim.get('carrier'):
            elements.append(Spacer(1, 0.25*inch))
            elements.append(Paragraph(f"<b>Insurance Information</b>", styles['Normal']))
            elements.append(Paragraph(f"Carrier: {claim.get('carrier', '')}", styles['Normal']))
            elements.append(Paragraph(f"Claim #: {claim.get('claim_number', '')}", styles['Normal']))
    
    elements.append(Spacer(1, 0.5*inch))
    
    table_data = [["Description", "Qty", "Unit", "Price", "Total"]]
    for item in invoice.get("line_items", []):
        total = item["quantity"] * item["unit_price"]
        table_data.append([item["description"], str(item["quantity"]), item["unit"], f"${item['unit_price']:.2f}", f"${total:.2f}"])
    
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
    
    elements.append(Paragraph(f"<b>Subtotal:</b> ${invoice['subtotal']:.2f}", styles['Normal']))
    elements.append(Paragraph(f"<b>Tax ({invoice.get('tax_rate', 0)}%):</b> ${invoice['tax_amount']:.2f}", styles['Normal']))
    elements.append(Paragraph(f"<b>Total:</b> ${invoice['total']:.2f}", styles['Heading2']))
    
    doc.build(elements)
    buffer.seek(0)
    
    return StreamingResponse(buffer, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={invoice['invoice_number']}.pdf"})

# ============ EXPENSES ROUTES ============

@api_router.post("/expenses")
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
    del expense_doc["receipt_data"]
    await db.expenses.insert_one(expense_doc)
    expense_doc.pop("_id", None)
    return expense_doc

@api_router.get("/expenses")
async def get_expenses(job_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {}
    if job_id:
        query["job_id"] = job_id
    expenses = await db.expenses.find(query, {"_id": 0}).to_list(1000)
    return expenses

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

@api_router.post("/jobs/{job_id}/expenses")
async def add_job_expense(job_id: str, expense_data: ExpenseCreate, current_user: dict = Depends(get_current_user)):
    expense_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    expense_doc = {
        "id": expense_id,
        **expense_data.model_dump(),
        "job_id": job_id,
        "status": "pending",
        "created_at": now,
        "created_by": current_user["id"]
    }
    if "receipt_data" in expense_doc:
        del expense_doc["receipt_data"]
    
    await db.expenses.insert_one(expense_doc)
    expense_doc.pop("_id", None)
    return expense_doc

# ============ COMMUNICATION LOG ROUTES ============

@api_router.post("/communications")
async def create_communication(comm_data: CommunicationLogCreate, current_user: dict = Depends(get_current_user)):
    comm_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    comm_doc = {
        "id": comm_id,
        **comm_data.model_dump(),
        "created_by": current_user["name"],
        "created_at": now
    }
    await db.communications.insert_one(comm_doc)
    comm_doc.pop("_id", None)
    return comm_doc

@api_router.get("/communications")
async def get_communications(job_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    query = {}
    if job_id:
        query["job_id"] = job_id
    comms = await db.communications.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
    return comms

# ============ PHOTOS & LOGS ROUTES ============

@api_router.post("/jobs/{job_id}/photos")
async def upload_job_photo(job_id: str, photo: PhotoUpload, current_user: dict = Depends(get_current_user)):
    photo_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    photo_doc = {
        "id": photo_id,
        "job_id": job_id,
        "data": photo.photo_data,
        "caption": photo.caption,
        "created_by": current_user["name"],
        "created_at": now
    }
    await db.job_photos.insert_one(photo_doc)
    return {"id": photo_id, "message": "Photo uploaded"}

@api_router.get("/jobs/{job_id}/photos")
async def get_job_photos(job_id: str, current_user: dict = Depends(get_current_user)):
    photos = await db.job_photos.find({"job_id": job_id}, {"_id": 0}).to_list(100)
    return photos

@api_router.delete("/photos/{photo_id}")
async def delete_photo(photo_id: str, current_user: dict = Depends(get_current_user)):
    await db.job_photos.delete_one({"id": photo_id})
    return {"message": "Photo deleted"}

class JobLogCreate(BaseModel):
    job_id: str
    entry_type: str
    content: str
    photo_data: Optional[str] = None

@api_router.post("/job-logs")
async def create_job_log(log_data: JobLogCreate, current_user: dict = Depends(get_current_user)):
    log_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    photo_url = None
    if log_data.photo_data:
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
    log_doc.pop("_id", None)
    return log_doc

@api_router.get("/job-logs/{job_id}")
async def get_job_logs(job_id: str, current_user: dict = Depends(get_current_user)):
    logs = await db.job_logs.find({"job_id": job_id}, {"_id": 0}).to_list(1000)
    return logs

# ============ REPORTS ROUTES ============

@api_router.get("/reports/dashboard")
async def get_dashboard_stats(current_user: dict = Depends(get_current_user)):
    jobs = await db.jobs.find({}, {"_id": 0}).to_list(1000)
    invoices = await db.invoices.find({}, {"_id": 0}).to_list(1000)
    expenses = await db.expenses.find({}, {"_id": 0}).to_list(1000)
    crews = await db.crews.find({}, {"_id": 0}).to_list(100)
    daily_logs = await db.daily_logs.find({}, {"_id": 0}).to_list(1000)
    
    now = datetime.now(timezone.utc)
    today = now.date()
    week_ago = today - timedelta(days=7)
    two_weeks_ago = today - timedelta(days=14)
    month_ago = today - timedelta(days=30)
    two_months_ago = today - timedelta(days=60)
    
    # Current period totals
    total_revenue = sum(inv["total"] for inv in invoices if inv.get("status") == "paid")
    total_expenses = sum(exp["amount"] for exp in expenses)
    outstanding_invoices = sum(inv["total"] for inv in invoices if inv.get("status") in ["sent", "draft", "overdue"])
    
    # Calculate weekly revenue (this week vs last week)
    this_week_revenue = sum(
        inv["total"] for inv in invoices 
        if inv.get("status") == "paid" and inv.get("created_at", "")[:10] >= str(week_ago)
    )
    last_week_revenue = sum(
        inv["total"] for inv in invoices 
        if inv.get("status") == "paid" and str(two_weeks_ago) <= inv.get("created_at", "")[:10] < str(week_ago)
    )
    revenue_change = ((this_week_revenue - last_week_revenue) / last_week_revenue * 100) if last_week_revenue > 0 else (100 if this_week_revenue > 0 else 0)
    
    # Calculate monthly revenue trend
    this_month_revenue = sum(
        inv["total"] for inv in invoices 
        if inv.get("status") == "paid" and inv.get("created_at", "")[:10] >= str(month_ago)
    )
    last_month_revenue = sum(
        inv["total"] for inv in invoices 
        if inv.get("status") == "paid" and str(two_months_ago) <= inv.get("created_at", "")[:10] < str(month_ago)
    )
    monthly_revenue_change = ((this_month_revenue - last_month_revenue) / last_month_revenue * 100) if last_month_revenue > 0 else (100 if this_month_revenue > 0 else 0)
    
    # Jobs this week vs last week
    jobs_this_week = len([j for j in jobs if j.get("created_at", "")[:10] >= str(week_ago)])
    jobs_last_week = len([j for j in jobs if str(two_weeks_ago) <= j.get("created_at", "")[:10] < str(week_ago)])
    jobs_change = ((jobs_this_week - jobs_last_week) / jobs_last_week * 100) if jobs_last_week > 0 else (100 if jobs_this_week > 0 else 0)
    
    # Active jobs trend
    active_jobs = [j for j in jobs if j.get("status") in ["scheduled", "in_progress"]]
    completed_this_week = len([j for j in jobs if j.get("status") == "completed" and j.get("updated_at", "")[:10] >= str(week_ago)])
    
    # Crew utilization
    busy_crews = len([c for c in crews if c.get("status") == "busy"])
    crew_utilization = (busy_crews / len(crews) * 100) if crews else 0
    
    # Average job value
    completed_jobs = [j for j in jobs if j.get("status") == "completed" and j.get("total_amount", 0) > 0]
    avg_job_value = sum(j.get("total_amount", 0) for j in completed_jobs) / len(completed_jobs) if completed_jobs else 0
    
    # Days to completion average
    completed_with_dates = [j for j in jobs if j.get("status") == "completed" and j.get("created_at") and j.get("updated_at")]
    avg_days_to_complete = 0
    if completed_with_dates:
        total_days = 0
        for j in completed_with_dates:
            try:
                created = datetime.fromisoformat(j["created_at"].replace("Z", "+00:00"))
                updated = datetime.fromisoformat(j["updated_at"].replace("Z", "+00:00"))
                total_days += (updated - created).days
            except:
                pass
        avg_days_to_complete = total_days / len(completed_with_dates) if completed_with_dates else 0
    
    # Labor hours this week
    labor_hours_this_week = sum(
        sum(e.get("hours", 0) for e in log.get("labor_entries", []))
        for log in daily_logs if log.get("date", "") >= str(week_ago)
    )
    labor_hours_last_week = sum(
        sum(e.get("hours", 0) for e in log.get("labor_entries", []))
        for log in daily_logs if str(two_weeks_ago) <= log.get("date", "") < str(week_ago)
    )
    labor_hours_change = ((labor_hours_this_week - labor_hours_last_week) / labor_hours_last_week * 100) if labor_hours_last_week > 0 else (100 if labor_hours_this_week > 0 else 0)
    
    # Jobs by status and phase
    jobs_by_status = {}
    jobs_by_phase = {}
    for job in jobs:
        status = job.get("status", "pending")
        phase = job.get("current_phase", "intake")
        jobs_by_status[status] = jobs_by_status.get(status, 0) + 1
        jobs_by_phase[phase] = jobs_by_phase.get(phase, 0) + 1
    
    # Overdue invoices
    overdue_invoices = []
    for inv in invoices:
        if inv.get("status") not in ["paid", "cancelled"]:
            try:
                due_date = datetime.strptime(inv["due_date"], "%Y-%m-%d").date()
                if due_date < today:
                    days_overdue = (today - due_date).days
                    overdue_invoices.append({
                        "invoice_number": inv["invoice_number"],
                        "customer_name": inv["customer_name"],
                        "total": inv["total"],
                        "due_date": inv["due_date"],
                        "days_overdue": days_overdue
                    })
            except:
                pass
    
    # Jobs over budget
    jobs_over_budget = []
    for job in jobs:
        if job.get("budget_amount", 0) > 0:
            job_expenses = await db.expenses.find({"job_id": job["id"]}, {"_id": 0}).to_list(1000)
            total_cost = sum(e["amount"] for e in job_expenses)
            if total_cost > job["budget_amount"]:
                jobs_over_budget.append({
                    "id": job["id"],
                    "title": job["title"],
                    "budget": job["budget_amount"],
                    "actual": total_cost,
                    "variance": total_cost - job["budget_amount"]
                })
    
    # Loss type breakdown
    loss_type_counts = {}
    for job in jobs:
        lt = job.get("loss_type", "other")
        loss_type_counts[lt] = loss_type_counts.get(lt, 0) + 1
    
    # Insurance stats
    jobs_with_insurance = len([j for j in jobs if j.get("insurance_claim", {}).get("claim_number")])
    total_approved = sum(j.get("insurance_claim", {}).get("approved_amount", 0) for j in jobs if j.get("insurance_claim"))
    total_depreciation = sum(j.get("insurance_claim", {}).get("depreciation_withheld", 0) for j in jobs if j.get("insurance_claim"))
    
    return {
        "total_jobs": len(jobs),
        "active_jobs": len(active_jobs),
        "jobs_this_week": jobs_this_week,
        "jobs_change_percent": round(jobs_change, 1),
        "completed_this_week": completed_this_week,
        "total_crews": len(crews),
        "available_crews": len([c for c in crews if c.get("status") == "available"]),
        "busy_crews": busy_crews,
        "crew_utilization": round(crew_utilization, 1),
        "total_revenue": total_revenue,
        "this_week_revenue": this_week_revenue,
        "revenue_change_percent": round(revenue_change, 1),
        "monthly_revenue_change_percent": round(monthly_revenue_change, 1),
        "total_expenses": total_expenses,
        "gross_profit": total_revenue - total_expenses,
        "profit_margin": round((total_revenue - total_expenses) / total_revenue * 100, 1) if total_revenue > 0 else 0,
        "outstanding_invoices": outstanding_invoices,
        "avg_job_value": round(avg_job_value, 2),
        "avg_days_to_complete": round(avg_days_to_complete, 1),
        "labor_hours_this_week": labor_hours_this_week,
        "labor_hours_change_percent": round(labor_hours_change, 1),
        "jobs_by_status": jobs_by_status,
        "jobs_by_phase": jobs_by_phase,
        "loss_type_counts": loss_type_counts,
        "pending_invoices": len([inv for inv in invoices if inv.get("status") == "sent"]),
        "overdue_invoices": sorted(overdue_invoices, key=lambda x: x["days_overdue"], reverse=True)[:5],
        "overdue_invoices_count": len(overdue_invoices),
        "overdue_invoices_total": sum(inv["total"] for inv in overdue_invoices),
        "jobs_over_budget": jobs_over_budget[:5],
        "jobs_over_budget_count": len(jobs_over_budget),
        "jobs_with_insurance": jobs_with_insurance,
        "insurance_approved_total": total_approved,
        "depreciation_withheld_total": total_depreciation,
        "recent_jobs": jobs[-5:][::-1] if jobs else []
    }

@api_router.get("/reports/collections")
async def get_collections_report(current_user: dict = Depends(get_current_user)):
    """Get collection follow-up report"""
    invoices = await db.invoices.find({"status": {"$nin": ["paid", "cancelled"]}}, {"_id": 0}).to_list(1000)
    
    today = datetime.now(timezone.utc).date()
    followups_due = []
    aging_buckets = {"current": 0, "1-30": 0, "31-60": 0, "61-90": 0, "90+": 0}
    
    for inv in invoices:
        due_date = datetime.strptime(inv["due_date"], "%Y-%m-%d").date()
        days_outstanding = (today - due_date).days
        
        # Aging buckets
        if days_outstanding <= 0:
            aging_buckets["current"] += inv["total"]
        elif days_outstanding <= 30:
            aging_buckets["1-30"] += inv["total"]
        elif days_outstanding <= 60:
            aging_buckets["31-60"] += inv["total"]
        elif days_outstanding <= 90:
            aging_buckets["61-90"] += inv["total"]
        else:
            aging_buckets["90+"] += inv["total"]
        
        # Check follow-up schedule
        for followup in inv.get("followup_schedule", []):
            if not followup.get("completed"):
                followup_date = datetime.strptime(followup["date"], "%Y-%m-%d").date()
                if followup_date <= today:
                    followups_due.append({
                        "invoice_id": inv["id"],
                        "invoice_number": inv["invoice_number"],
                        "customer_name": inv["customer_name"],
                        "total": inv["total"],
                        "due_date": inv["due_date"],
                        "followup_day": followup["day"],
                        "followup_date": followup["date"],
                        "days_overdue": days_outstanding
                    })
                break
    
    return {
        "aging_buckets": aging_buckets,
        "total_outstanding": sum(aging_buckets.values()),
        "followups_due": sorted(followups_due, key=lambda x: x["days_overdue"], reverse=True),
        "followups_due_count": len(followups_due)
    }

@api_router.get("/reports/job-costing/{job_id}")
async def get_job_costing(job_id: str, current_user: dict = Depends(get_current_user)):
    job = await db.jobs.find_one({"id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    expenses = await db.expenses.find({"job_id": job_id}, {"_id": 0}).to_list(1000)
    invoices = await db.invoices.find({"job_id": job_id}, {"_id": 0}).to_list(10)
    daily_logs = await db.daily_logs.find({"job_id": job_id}, {"_id": 0}).to_list(100)
    
    # Calculate from daily logs
    labor_cost = sum(
        sum(e.get("hours", 0) * e.get("hourly_rate", 0) for e in log.get("labor_entries", []))
        for log in daily_logs
    )
    equipment_cost = sum(
        sum(e.get("quantity", 1) * e.get("daily_rate", 0) for e in log.get("equipment_entries", []))
        for log in daily_logs
    )
    material_cost = sum(
        sum(e.get("quantity", 0) * e.get("unit_cost", 0) for e in log.get("material_entries", []))
        for log in daily_logs
    )
    other_expenses = sum(exp["amount"] for exp in expenses)
    
    total_cost = labor_cost + equipment_cost + material_cost + other_expenses
    revenue = sum(inv["total"] for inv in invoices if inv.get("status") == "paid")
    total_invoiced = sum(inv["total"] for inv in invoices)
    gross_margin = revenue - total_cost
    
    # Phase breakdown
    phase_costs = {}
    for log in daily_logs:
        phase = log.get("phase", "general")
        if phase not in phase_costs:
            phase_costs[phase] = {"labor": 0, "equipment": 0, "materials": 0, "total": 0}
        phase_labor = sum(e.get("hours", 0) * e.get("hourly_rate", 0) for e in log.get("labor_entries", []))
        phase_equip = sum(e.get("quantity", 1) * e.get("daily_rate", 0) for e in log.get("equipment_entries", []))
        phase_mat = sum(e.get("quantity", 0) * e.get("unit_cost", 0) for e in log.get("material_entries", []))
        phase_costs[phase]["labor"] += phase_labor
        phase_costs[phase]["equipment"] += phase_equip
        phase_costs[phase]["materials"] += phase_mat
        phase_costs[phase]["total"] += phase_labor + phase_equip + phase_mat
    
    budget = job.get("budget_amount", 0)
    
    return {
        "job_id": job_id,
        "job_title": job["title"],
        "budget": budget,
        "revenue": revenue,
        "total_invoiced": total_invoiced,
        "costs": {
            "labor": labor_cost,
            "equipment": equipment_cost,
            "materials": material_cost,
            "other": other_expenses,
            "total": total_cost
        },
        "gross_margin": gross_margin,
        "margin_percentage": round((gross_margin / revenue * 100) if revenue > 0 else 0, 2),
        "is_profitable": gross_margin > 0,
        "is_over_budget": total_cost > budget if budget > 0 else False,
        "budget_variance": total_cost - budget if budget > 0 else 0,
        "phase_costs": phase_costs
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
    
    expected_income = sum(inv["total"] for inv in invoices)
    avg_monthly_expenses = sum(exp["amount"] for exp in expenses) / 3 if expenses else 0
    
    forecasts = [
        {"period": "30 days", "expected_income": expected_income * 0.5, "expected_expenses": avg_monthly_expenses, "net_cash_flow": (expected_income * 0.5) - avg_monthly_expenses},
        {"period": "60 days", "expected_income": expected_income * 0.8, "expected_expenses": avg_monthly_expenses * 2, "net_cash_flow": (expected_income * 0.8) - (avg_monthly_expenses * 2)},
        {"period": "90 days", "expected_income": expected_income, "expected_expenses": avg_monthly_expenses * 3, "net_cash_flow": expected_income - (avg_monthly_expenses * 3)}
    ]
    
    return {"forecasts": forecasts, "outstanding_invoices_total": expected_income}

# ============ EXPORT ROUTES ============

@api_router.get("/export/quickbooks")
async def export_quickbooks(data_type: str, current_user: dict = Depends(get_current_user)):
    output = StringIO()
    writer = csv.writer(output)
    
    if data_type == "invoices":
        invoices = await db.invoices.find({}, {"_id": 0}).to_list(1000)
        writer.writerow(["Invoice Number", "Customer", "Property Address", "Date", "Due Date", "Subtotal", "Tax", "Total", "Status", "Claim Number"])
        for inv in invoices:
            claim_num = inv.get("insurance_claim", {}).get("claim_number", "") if inv.get("insurance_claim") else ""
            writer.writerow([
                inv["invoice_number"], inv["customer_name"], inv.get("property_address", ""),
                inv["created_at"][:10], inv["due_date"], inv["subtotal"], inv["tax_amount"],
                inv["total"], inv["status"], claim_num
            ])
    elif data_type == "expenses":
        expenses = await db.expenses.find({}, {"_id": 0}).to_list(1000)
        writer.writerow(["Date", "Vendor", "Description", "Category", "Job ID", "Amount", "Taxable", "Status"])
        for exp in expenses:
            writer.writerow([
                exp["date"], exp.get("vendor", ""), exp["description"], exp["category"],
                exp.get("job_id", ""), exp["amount"], "Yes" if exp.get("is_taxable") else "No", exp.get("status", "pending")
            ])
    elif data_type == "job_costs":
        jobs = await db.jobs.find({}, {"_id": 0}).to_list(1000)
        writer.writerow(["Job ID", "Title", "Customer", "Status", "Phase", "Budget", "Total Amount", "Created"])
        for job in jobs:
            writer.writerow([
                job["id"], job["title"], job["customer_name"], job["status"],
                job.get("current_phase", ""), job.get("budget_amount", 0), job.get("total_amount", 0), job["created_at"][:10]
            ])
    else:
        raise HTTPException(status_code=400, detail="Invalid data type")
    
    output.seek(0)
    return StreamingResponse(iter([output.getvalue()]), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={data_type}_export.csv"})

# ============ AI ROUTES ============

@api_router.post("/ai/generate-message")
async def generate_ai_message(request: AIMessageRequest, current_user: dict = Depends(get_current_user)):
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="AI service not configured")
    
    job_context = ""
    if request.job_id:
        job = await db.jobs.find_one({"id": request.job_id}, {"_id": 0})
        if job:
            job_context = f"Job: {job['title']} at {job.get('property_address', '')}. Status: {job['status']}. Phase: {job.get('current_phase', '')}. Loss type: {job.get('loss_type', '')}. Scope: {job['scope']}"
            if job.get("insurance_claim"):
                claim = job["insurance_claim"]
                job_context += f". Insurance: {claim.get('carrier', '')} Claim #{claim.get('claim_number', '')}"
    
    message_prompts = {
        "scheduling": f"Generate a short, professional text message to {request.customer_name} about scheduling their restoration job. {job_context}",
        "arrival": f"Generate a short, professional text message to {request.customer_name} notifying them that the crew is arriving soon. {job_context}",
        "delay": f"Generate a professional, empathetic text message to {request.customer_name} explaining a delay in their restoration work. {job_context}",
        "progress": f"Generate a short, professional text message to {request.customer_name} with a progress update on their restoration work. {job_context}",
        "payment": f"Generate a professional but friendly text message to {request.customer_name} as a payment reminder. {job_context}",
        "insurance_update": f"Generate a professional message to {request.customer_name} providing an update on their insurance claim status. {job_context}",
        "completion": f"Generate a professional message to {request.customer_name} notifying them their restoration work is complete. {job_context}",
        "custom": f"Generate a professional message for {request.customer_name}. Context: {request.custom_context or job_context}"
    }
    
    prompt = message_prompts.get(request.message_type, message_prompts["custom"])
    
    chat = LlmChat(
        api_key=api_key,
        session_id=f"msg-{uuid.uuid4()}",
        system_message="You are a professional assistant for a restoration contracting company. Generate short, friendly, and professional text messages for customer communication. Use restoration industry terminology appropriately. Keep messages under 160 characters when possible."
    ).with_model("openai", "gpt-4o")
    
    user_message = UserMessage(text=prompt)
    response = await chat.send_message(user_message)
    
    return {"message": response, "message_type": request.message_type}


# ============ ACCOUNTING ASSISTANT ============

class TransactionCategorizationRequest(BaseModel):
    transactions: List[Dict[str, Any]]

@api_router.post("/ai/accounting/categorize")
async def ai_categorize_transactions(request: TransactionCategorizationRequest, current_user: dict = Depends(get_current_user)):
    """AI-powered transaction categorization"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="AI service not configured")
    
    chat = LlmChat(
        api_key=api_key,
        session_id=f"accounting-{uuid.uuid4()}",
        system_message="""You are an accounting assistant for a restoration contracting company. 
        Your job is to categorize transactions into these categories: labor, equipment, materials, overhead, subcontractor, insurance_payment, customer_payment, fuel, office_supplies, utilities, other.
        Provide clear explanations for each categorization. Flag any unusual, duplicate, or missing transactions.
        Return JSON format with categorizations and explanations."""
    ).with_model("openai", "gpt-4o")
    
    transactions_text = "\n".join([
        f"- ${t.get('amount', 0)}: {t.get('description', 'No description')} from {t.get('vendor', 'Unknown')} on {t.get('date', 'Unknown date')}"
        for t in request.transactions
    ])
    
    prompt = f"""Categorize these transactions for a restoration company and explain your reasoning:

{transactions_text}

Return a JSON object with:
1. categorizations: array of {{description, suggested_category, explanation, confidence, flags}}
2. alerts: array of potential issues found
3. summary: brief overall assessment"""
    
    response = await chat.send_message(UserMessage(text=prompt))
    
    return {"analysis": response, "transaction_count": len(request.transactions)}


@api_router.post("/ai/accounting/analyze")
async def ai_accounting_analysis(current_user: dict = Depends(get_current_user)):
    """Analyze accounting data for issues and recommendations"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="AI service not configured")
    
    expenses = await db.expenses.find({}, {"_id": 0}).to_list(500)
    invoices = await db.invoices.find({}, {"_id": 0}).to_list(500)
    
    # Check for issues
    uncategorized = [e for e in expenses if not e.get("category") or e.get("category") == "other"]
    pending_expenses = [e for e in expenses if e.get("status") == "pending"]
    
    # Find potential duplicates
    duplicates = []
    seen = {}
    for e in expenses:
        key = f"{e.get('date')}_{e.get('amount')}_{e.get('vendor', '')}"
        if key in seen:
            duplicates.append({"expense": e["description"], "amount": e["amount"], "date": e["date"]})
        seen[key] = True
    
    # Expense summary by category
    by_category = {}
    for e in expenses:
        cat = e.get("category", "other")
        by_category[cat] = by_category.get(cat, 0) + e.get("amount", 0)
    
    chat = LlmChat(
        api_key=api_key,
        session_id=f"acct-analysis-{uuid.uuid4()}",
        system_message="""You are an accounting assistant for a restoration contracting company. 
        Analyze the financial data and provide actionable insights. Focus on:
        1. Data quality issues
        2. Potential errors or duplicates
        3. Month-end close readiness
        4. Recommended corrective actions
        Keep response concise and actionable."""
    ).with_model("openai", "gpt-4o")
    
    prompt = f"""Analyze this accounting data:

Expenses by Category:
{json.dumps(by_category, indent=2)}

Issues Found:
- Uncategorized expenses: {len(uncategorized)}
- Pending approval: {len(pending_expenses)}
- Potential duplicates: {len(duplicates)}

Total invoices: {len(invoices)}
Paid invoices: {len([i for i in invoices if i.get('status') == 'paid'])}

Provide:
1. Data quality assessment
2. Specific issues to fix
3. Recommendations before month-end close
4. Ready-to-post entries if any corrections needed"""
    
    response = await chat.send_message(UserMessage(text=prompt))
    
    return {
        "analysis": response,
        "metrics": {
            "total_expenses": len(expenses),
            "uncategorized_count": len(uncategorized),
            "pending_approval_count": len(pending_expenses),
            "potential_duplicates": duplicates[:10],
            "expenses_by_category": by_category
        }
    }


# ============ PAYMENTS ASSISTANT ============

@api_router.post("/ai/payments/analyze")
async def ai_payments_analysis(current_user: dict = Depends(get_current_user)):
    """Analyze payment patterns and suggest follow-up strategies"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="AI service not configured")
    
    invoices = await db.invoices.find({}, {"_id": 0}).to_list(1000)
    jobs = await db.jobs.find({}, {"_id": 0}).to_list(1000)
    
    today = datetime.now(timezone.utc).date()
    
    # Analyze by customer
    customer_data = {}
    for inv in invoices:
        customer = inv.get("customer_name", "Unknown")
        if customer not in customer_data:
            customer_data[customer] = {"total_invoiced": 0, "total_paid": 0, "overdue": 0, "invoices": []}
        customer_data[customer]["total_invoiced"] += inv.get("total", 0)
        if inv.get("status") == "paid":
            customer_data[customer]["total_paid"] += inv.get("total", 0)
        
        if inv.get("status") not in ["paid", "cancelled"]:
            try:
                due_date = datetime.strptime(inv["due_date"], "%Y-%m-%d").date()
                days_overdue = (today - due_date).days
                if days_overdue > 0:
                    customer_data[customer]["overdue"] += inv.get("total", 0)
                customer_data[customer]["invoices"].append({
                    "number": inv["invoice_number"],
                    "total": inv["total"],
                    "due_date": inv["due_date"],
                    "days_overdue": days_overdue,
                    "has_insurance": bool(inv.get("insurance_claim", {}).get("claim_number"))
                })
            except:
                pass
    
    # Get customers needing follow-up
    followup_needed = []
    for customer, data in customer_data.items():
        unpaid_invoices = [i for i in data["invoices"] if i["days_overdue"] >= 0]
        if unpaid_invoices:
            followup_needed.append({
                "customer": customer,
                "outstanding": sum(i["total"] for i in unpaid_invoices),
                "oldest_days": max(i["days_overdue"] for i in unpaid_invoices),
                "invoice_count": len(unpaid_invoices),
                "has_insurance": any(i["has_insurance"] for i in unpaid_invoices)
            })
    
    followup_needed.sort(key=lambda x: x["oldest_days"], reverse=True)
    
    chat = LlmChat(
        api_key=api_key,
        session_id=f"payments-{uuid.uuid4()}",
        system_message="""You are a payments collection specialist for a restoration contracting company.
        Analyze payment patterns and provide specific follow-up strategies. Consider:
        - Insurance vs direct-pay customers
        - Payment history
        - Days overdue
        - Escalation timing
        Provide actionable, specific recommendations."""
    ).with_model("openai", "gpt-4o")
    
    prompt = f"""Analyze these outstanding accounts and recommend follow-up strategies:

Customers Needing Follow-up (top 10):
{json.dumps(followup_needed[:10], indent=2)}

Total Outstanding: ${sum(f['outstanding'] for f in followup_needed):,.2f}
Insurance Jobs: {len([f for f in followup_needed if f['has_insurance']])}
Direct Pay: {len([f for f in followup_needed if not f['has_insurance']])}

Provide:
1. Priority ranking with reasons
2. Specific follow-up strategy for each top customer
3. Recommended timing for escalation
4. Draft message templates for different scenarios"""
    
    response = await chat.send_message(UserMessage(text=prompt))
    
    return {
        "analysis": response,
        "followup_list": followup_needed[:20],
        "summary": {
            "total_outstanding": sum(f["outstanding"] for f in followup_needed),
            "customers_needing_followup": len(followup_needed),
            "over_30_days": len([f for f in followup_needed if f["oldest_days"] > 30]),
            "over_60_days": len([f for f in followup_needed if f["oldest_days"] > 60]),
            "over_90_days": len([f for f in followup_needed if f["oldest_days"] > 90])
        }
    }


@api_router.post("/ai/payments/draft-message")
async def ai_draft_payment_message(customer_name: str, amount: float, days_overdue: int, has_insurance: bool = False, escalation_level: int = 1, current_user: dict = Depends(get_current_user)):
    """Generate payment reminder message"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="AI service not configured")
    
    escalation_context = {
        1: "friendly first reminder",
        2: "second notice, slightly more formal",
        3: "urgent final notice before escalation",
        4: "final demand before collections"
    }
    
    chat = LlmChat(
        api_key=api_key,
        session_id=f"payment-msg-{uuid.uuid4()}",
        system_message="You are a professional accounts receivable specialist for a restoration company. Write clear, professional payment reminder messages that maintain good customer relationships while being firm about payment."
    ).with_model("openai", "gpt-4o")
    
    prompt = f"""Write a payment reminder for:
Customer: {customer_name}
Amount Due: ${amount:,.2f}
Days Overdue: {days_overdue}
Insurance Claim: {'Yes' if has_insurance else 'No - Direct Pay'}
Escalation Level: {escalation_level} ({escalation_context.get(escalation_level, 'standard')})

Generate both an email and SMS version. Keep SMS under 160 characters."""
    
    response = await chat.send_message(UserMessage(text=prompt))
    
    return {"messages": response, "customer": customer_name, "amount": amount, "escalation_level": escalation_level}


# ============ RECONCILIATION ASSISTANT ============

@api_router.post("/ai/reconciliation/analyze")
async def ai_reconciliation_analysis(current_user: dict = Depends(get_current_user)):
    """AI-powered bank reconciliation assistant"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="AI service not configured")
    
    invoices = await db.invoices.find({"status": "paid"}, {"_id": 0}).to_list(500)
    expenses = await db.expenses.find({}, {"_id": 0}).to_list(500)
    jobs = await db.jobs.find({}, {"_id": 0}).to_list(500)
    
    # Get payments from jobs
    all_payments = []
    for job in jobs:
        for payment in job.get("payments", []):
            all_payments.append({
                "type": "payment_received",
                "amount": payment.get("amount", 0),
                "date": payment.get("date"),
                "reference": payment.get("reference"),
                "job_id": job["id"],
                "customer": job["customer_name"]
            })
    
    # Summary of expected vs recorded
    total_invoiced_paid = sum(inv.get("total", 0) for inv in invoices)
    total_payments_recorded = sum(p["amount"] for p in all_payments)
    total_expenses = sum(e.get("amount", 0) for e in expenses)
    
    # Find unmatched items
    unmatched_invoices = []
    for inv in invoices:
        matching_payments = [p for p in all_payments if abs(p["amount"] - inv["total"]) < 0.01]
        if not matching_payments:
            unmatched_invoices.append({
                "invoice_number": inv["invoice_number"],
                "amount": inv["total"],
                "customer": inv["customer_name"]
            })
    
    chat = LlmChat(
        api_key=api_key,
        session_id=f"recon-{uuid.uuid4()}",
        system_message="""You are a reconciliation specialist for a restoration company.
        Analyze financial records and identify discrepancies. Focus on:
        1. Matching deposits to invoices
        2. Identifying missing or duplicate entries
        3. Explaining discrepancies
        4. Providing specific corrective actions
        Be precise with amounts and references."""
    ).with_model("openai", "gpt-4o")
    
    prompt = f"""Analyze this reconciliation data:

Summary:
- Total Invoices Marked Paid: ${total_invoiced_paid:,.2f}
- Total Payments Recorded: ${total_payments_recorded:,.2f}
- Variance: ${total_invoiced_paid - total_payments_recorded:,.2f}
- Total Expenses: ${total_expenses:,.2f}

Unmatched Paid Invoices (no matching payment record): {len(unmatched_invoices)}
{json.dumps(unmatched_invoices[:10], indent=2)}

Provide:
1. Reconciliation summary
2. List of exceptions needing attention
3. Suggested corrections
4. Steps to resolve each discrepancy"""
    
    response = await chat.send_message(UserMessage(text=prompt))
    
    return {
        "analysis": response,
        "summary": {
            "total_invoiced_paid": total_invoiced_paid,
            "total_payments_recorded": total_payments_recorded,
            "variance": total_invoiced_paid - total_payments_recorded,
            "unmatched_invoices": len(unmatched_invoices),
            "total_expenses": total_expenses
        },
        "exceptions": unmatched_invoices[:20]
    }


# ============ CUSTOMER FOLLOW-UP ASSISTANT ============

@api_router.post("/ai/customer/prioritize")
async def ai_customer_prioritization(current_user: dict = Depends(get_current_user)):
    """Prioritize customers for follow-up"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="AI service not configured")
    
    jobs = await db.jobs.find({}, {"_id": 0}).to_list(500)
    invoices = await db.invoices.find({}, {"_id": 0}).to_list(500)
    communications = await db.communications.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)
    
    today = datetime.now(timezone.utc).date()
    
    # Build customer profiles
    customers = {}
    for job in jobs:
        name = job.get("customer_name")
        if name not in customers:
            customers[name] = {
                "name": name,
                "phone": job.get("customer_phone"),
                "email": job.get("customer_email"),
                "jobs": [],
                "total_value": 0,
                "last_communication": None,
                "outstanding_balance": 0,
                "needs_followup": []
            }
        customers[name]["jobs"].append({
            "title": job["title"],
            "status": job["status"],
            "phase": job.get("current_phase"),
            "value": job.get("total_amount", 0)
        })
        customers[name]["total_value"] += job.get("total_amount", 0)
    
    # Add invoice data
    for inv in invoices:
        name = inv.get("customer_name")
        if name in customers and inv.get("status") not in ["paid", "cancelled"]:
            customers[name]["outstanding_balance"] += inv.get("total", 0)
            try:
                due_date = datetime.strptime(inv["due_date"], "%Y-%m-%d").date()
                if due_date < today:
                    customers[name]["needs_followup"].append(f"Overdue invoice {inv['invoice_number']}")
            except:
                pass
    
    # Add communication data
    for comm in communications:
        job = next((j for j in jobs if j["id"] == comm.get("job_id")), None)
        if job:
            name = job.get("customer_name")
            if name in customers and not customers[name]["last_communication"]:
                customers[name]["last_communication"] = comm.get("created_at", "")[:10]
    
    # Score and sort customers
    customer_list = list(customers.values())
    for c in customer_list:
        score = 0
        if c["outstanding_balance"] > 0:
            score += 50
        if c["needs_followup"]:
            score += 30
        if any(j["status"] == "in_progress" for j in c["jobs"]):
            score += 20
        c["priority_score"] = score
    
    customer_list.sort(key=lambda x: x["priority_score"], reverse=True)
    
    chat = LlmChat(
        api_key=api_key,
        session_id=f"customer-{uuid.uuid4()}",
        system_message="""You are a customer success manager for a restoration company.
        Analyze customer data and prioritize follow-ups. Consider:
        - Outstanding payments
        - Job status and phase
        - Time since last contact
        - Customer value
        Provide specific, actionable follow-up recommendations."""
    ).with_model("openai", "gpt-4o")
    
    top_customers = customer_list[:15]
    prompt = f"""Prioritize these customers for follow-up:

{json.dumps(top_customers, indent=2, default=str)}

Provide:
1. Ranked priority list with reasons
2. Specific follow-up action for each customer
3. Suggested message or talking points
4. Best contact method (call, email, text)"""
    
    response = await chat.send_message(UserMessage(text=prompt))
    
    return {
        "analysis": response,
        "priority_list": top_customers,
        "summary": {
            "total_customers": len(customers),
            "needing_followup": len([c for c in customer_list if c["needs_followup"]]),
            "with_outstanding_balance": len([c for c in customer_list if c["outstanding_balance"] > 0])
        }
    }


# ============ FINANCIAL INSIGHTS ASSISTANT ============

@api_router.post("/ai/finance/insights")
async def ai_financial_insights(current_user: dict = Depends(get_current_user)):
    """AI-powered financial analysis and KPIs"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="AI service not configured")
    
    jobs = await db.jobs.find({}, {"_id": 0}).to_list(1000)
    invoices = await db.invoices.find({}, {"_id": 0}).to_list(1000)
    expenses = await db.expenses.find({}, {"_id": 0}).to_list(1000)
    daily_logs = await db.daily_logs.find({}, {"_id": 0}).to_list(1000)
    
    today = datetime.now(timezone.utc).date()
    month_ago = today - timedelta(days=30)
    
    # Calculate KPIs
    total_revenue = sum(inv.get("total", 0) for inv in invoices if inv.get("status") == "paid")
    total_expenses = sum(e.get("amount", 0) for e in expenses)
    gross_profit = total_revenue - total_expenses
    profit_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    # Labor costs from daily logs
    total_labor_cost = sum(
        sum(e.get("hours", 0) * e.get("hourly_rate", 0) for e in log.get("labor_entries", []))
        for log in daily_logs
    )
    
    # Cash position
    outstanding_ar = sum(inv.get("total", 0) for inv in invoices if inv.get("status") in ["sent", "draft"])
    
    # Aging analysis
    aging = {"current": 0, "30_days": 0, "60_days": 0, "90_days": 0}
    for inv in invoices:
        if inv.get("status") not in ["paid", "cancelled"]:
            try:
                due_date = datetime.strptime(inv["due_date"], "%Y-%m-%d").date()
                days = (today - due_date).days
                if days <= 0:
                    aging["current"] += inv["total"]
                elif days <= 30:
                    aging["30_days"] += inv["total"]
                elif days <= 60:
                    aging["60_days"] += inv["total"]
                else:
                    aging["90_days"] += inv["total"]
            except:
                pass
    
    # Job metrics
    completed_jobs = [j for j in jobs if j.get("status") == "completed"]
    avg_job_value = sum(j.get("total_amount", 0) for j in completed_jobs) / len(completed_jobs) if completed_jobs else 0
    
    kpis = {
        "total_revenue": total_revenue,
        "total_expenses": total_expenses,
        "gross_profit": gross_profit,
        "profit_margin": round(profit_margin, 1),
        "total_labor_cost": total_labor_cost,
        "outstanding_ar": outstanding_ar,
        "aging": aging,
        "total_jobs": len(jobs),
        "completed_jobs": len(completed_jobs),
        "active_jobs": len([j for j in jobs if j.get("status") in ["scheduled", "in_progress"]]),
        "avg_job_value": round(avg_job_value, 2),
        "labor_as_percent_revenue": round((total_labor_cost / total_revenue * 100) if total_revenue > 0 else 0, 1)
    }
    
    chat = LlmChat(
        api_key=api_key,
        session_id=f"finance-{uuid.uuid4()}",
        system_message="""You are a financial analyst for a restoration contracting company.
        Analyze KPIs and financial data to provide actionable insights. Focus on:
        1. Profitability trends
        2. Cash flow health
        3. Risk indicators
        4. Improvement opportunities
        Use industry benchmarks for restoration companies when relevant.
        Be specific with numbers and recommendations."""
    ).with_model("openai", "gpt-4o")
    
    prompt = f"""Analyze these financial KPIs for a restoration company:

{json.dumps(kpis, indent=2)}

Provide:
1. KPI Assessment - How do these metrics compare to industry benchmarks?
2. Cash Flow Analysis - Current position and 30/60/90 day outlook
3. Risk Indicators - What financial risks need attention?
4. Improvement Opportunities - Specific actions to improve margins
5. Forecast - Brief outlook based on current trends"""
    
    response = await chat.send_message(UserMessage(text=prompt))
    
    return {
        "analysis": response,
        "kpis": kpis
    }


# ============ PROJECT & COST CONTROL ASSISTANT ============

@api_router.post("/ai/projects/analyze")
async def ai_project_analysis(job_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """AI-powered project cost analysis"""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="AI service not configured")
    
    if job_id:
        jobs = [await db.jobs.find_one({"id": job_id}, {"_id": 0})]
        if not jobs[0]:
            raise HTTPException(status_code=404, detail="Job not found")
    else:
        jobs = await db.jobs.find({"status": {"$in": ["scheduled", "in_progress"]}}, {"_id": 0}).to_list(100)
    
    project_data = []
    for job in jobs:
        if not job:
            continue
            
        expenses = await db.expenses.find({"job_id": job["id"]}, {"_id": 0}).to_list(500)
        daily_logs = await db.daily_logs.find({"job_id": job["id"]}, {"_id": 0}).to_list(500)
        invoices = await db.invoices.find({"job_id": job["id"]}, {"_id": 0}).to_list(50)
        
        # Calculate costs
        labor_cost = sum(
            sum(e.get("hours", 0) * e.get("hourly_rate", 0) for e in log.get("labor_entries", []))
            for log in daily_logs
        )
        equipment_cost = sum(
            sum(e.get("quantity", 1) * e.get("daily_rate", 0) for e in log.get("equipment_entries", []))
            for log in daily_logs
        )
        material_cost = sum(
            sum(e.get("quantity", 0) * e.get("unit_cost", 0) for e in log.get("material_entries", []))
            for log in daily_logs
        )
        other_expenses = sum(e.get("amount", 0) for e in expenses)
        total_cost = labor_cost + equipment_cost + material_cost + other_expenses
        
        budget = job.get("budget_amount", 0)
        estimated = job.get("estimated_amount", 0)
        invoiced = sum(inv.get("total", 0) for inv in invoices)
        
        project_data.append({
            "job_id": job["id"],
            "title": job["title"],
            "customer": job["customer_name"],
            "status": job["status"],
            "phase": job.get("current_phase"),
            "budget": budget,
            "estimated": estimated,
            "actual_cost": total_cost,
            "invoiced": invoiced,
            "costs": {
                "labor": labor_cost,
                "equipment": equipment_cost,
                "materials": material_cost,
                "other": other_expenses
            },
            "variance": total_cost - budget if budget > 0 else 0,
            "variance_percent": round((total_cost - budget) / budget * 100, 1) if budget > 0 else 0,
            "is_over_budget": total_cost > budget if budget > 0 else False
        })
    
    chat = LlmChat(
        api_key=api_key,
        session_id=f"project-{uuid.uuid4()}",
        system_message="""You are a project cost controller for a restoration contracting company.
        Analyze project costs and budgets. Focus on:
        1. Cost overruns and their causes
        2. Budget vs actual comparisons
        3. Early warning indicators
        4. Cost optimization opportunities
        Provide specific, actionable recommendations for each project."""
    ).with_model("openai", "gpt-4o")
    
    prompt = f"""Analyze these project costs:

{json.dumps(project_data, indent=2)}

Provide:
1. Project-by-project cost assessment
2. Budget vs Actual comparison with explanations
3. Projects at risk of overrun
4. Cost optimization recommendations
5. Bid review insights for future estimates"""
    
    response = await chat.send_message(UserMessage(text=prompt))
    
    return {
        "analysis": response,
        "projects": project_data,
        "summary": {
            "total_projects": len(project_data),
            "over_budget": len([p for p in project_data if p["is_over_budget"]]),
            "total_budget": sum(p["budget"] for p in project_data),
            "total_actual": sum(p["actual_cost"] for p in project_data),
            "total_variance": sum(p["variance"] for p in project_data)
        }
    }


@api_router.post("/ai/analyze-compliance")
async def analyze_compliance(current_user: dict = Depends(get_current_user)):
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    
    api_key = os.environ.get('EMERGENT_LLM_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="AI service not configured")
    
    invoices = await db.invoices.find({}, {"_id": 0}).to_list(100)
    expenses = await db.expenses.find({}, {"_id": 0}).to_list(100)
    jobs = await db.jobs.find({}, {"_id": 0}).to_list(100)
    
    # Check for issues
    issues = []
    
    # Overdue invoices
    today = datetime.now(timezone.utc).date()
    overdue = [inv for inv in invoices if inv.get("status") not in ["paid", "cancelled"] and datetime.strptime(inv["due_date"], "%Y-%m-%d").date() < today]
    if overdue:
        issues.append(f"{len(overdue)} overdue invoices totaling ${sum(inv['total'] for inv in overdue):,.2f}")
    
    # Jobs without insurance info
    jobs_missing_insurance = [j for j in jobs if j.get("loss_type") != "other" and not j.get("insurance_claim", {}).get("claim_number")]
    if jobs_missing_insurance:
        issues.append(f"{len(jobs_missing_insurance)} jobs may be missing insurance claim information")
    
    # Duplicate expenses
    expense_hashes = {}
    duplicates = []
    for exp in expenses:
        key = f"{exp['date']}_{exp['amount']}_{exp.get('vendor', '')}"
        if key in expense_hashes:
            duplicates.append(exp["description"])
        expense_hashes[key] = True
    
    chat = LlmChat(
        api_key=api_key,
        session_id=f"compliance-{uuid.uuid4()}",
        system_message="You are a financial compliance analyst for a restoration company. Analyze the provided data and identify potential issues, risks, or compliance concerns. Focus on cash flow, collections, and documentation completeness."
    ).with_model("openai", "gpt-4o")
    
    prompt = f"""Analyze this restoration company's operations for compliance issues:
    - Total jobs: {len(jobs)}
    - Active jobs: {len([j for j in jobs if j.get('status') in ['scheduled', 'in_progress']])}
    - Total invoices: {len(invoices)}
    - Overdue invoices: {len(overdue)}
    - Potential duplicate expenses: {len(duplicates)}
    - Known issues: {'; '.join(issues) if issues else 'None identified'}
    
    Provide a brief compliance report with concerns and recommendations."""
    
    user_message = UserMessage(text=prompt)
    response = await chat.send_message(user_message)
    
    return {
        "analysis": response,
        "potential_duplicates": duplicates,
        "overdue_invoices_count": len(overdue),
        "issues_found": issues,
        "action_items": [f"Review {len(duplicates)} potential duplicate expenses" if duplicates else None, f"Follow up on {len(overdue)} overdue invoices" if overdue else None, f"Add insurance info for {len(jobs_missing_insurance)} jobs" if jobs_missing_insurance else None]
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
    pipeline_value = sum(j.get("estimated_amount", 0) for j in jobs if j.get("status") in ["pending", "scheduled"])
    
    chat = LlmChat(
        api_key=api_key,
        session_id=f"forecast-{uuid.uuid4()}",
        system_message="You are a financial analyst for a restoration company. Provide realistic cash flow forecasts and business insights based on the data provided. Consider typical restoration industry payment cycles."
    ).with_model("openai", "gpt-4o")
    
    prompt = f"""Based on this restoration company data, provide a cash flow analysis:
    - Outstanding invoices: ${outstanding:,.2f}
    - Recent paid revenue: ${recent_revenue:,.2f}
    - Total expenses: ${total_expenses:,.2f}
    - Active jobs in progress: {active_jobs}
    - Pipeline value (pending jobs): ${pipeline_value:,.2f}
    
    Provide insights on cash flow health and recommendations for the next 90 days."""
    
    user_message = UserMessage(text=prompt)
    response = await chat.send_message(user_message)
    
    return {
        "ai_analysis": response,
        "metrics": {"outstanding_invoices": outstanding, "recent_revenue": recent_revenue, "total_expenses": total_expenses, "active_jobs": active_jobs, "pipeline_value": pipeline_value}
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
