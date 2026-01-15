"""
Workflow Automation API Endpoints
10x better than Make.com - native, intelligent, integrated
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from workflow_engine import (
    WorkflowEngine,
    WorkflowDefinition,
    WorkflowExecution,
    AIService,
    WorkflowScheduler,
    NodeConfig,
    NodeType,
    ExecutionStatus
)
from workflow_templates import WorkflowTemplates

logger = logging.getLogger(__name__)

# ============================================================================
# API MODELS
# ============================================================================

class WorkflowCreateRequest(BaseModel):
    """Request to create a new workflow"""
    name: str
    description: Optional[str] = None
    nodes: List[Dict[str, Any]]
    variables: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    enabled: bool = True


class WorkflowUpdateRequest(BaseModel):
    """Request to update a workflow"""
    name: Optional[str] = None
    description: Optional[str] = None
    nodes: Optional[List[Dict[str, Any]]] = None
    variables: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    enabled: Optional[bool] = None


class WorkflowExecuteRequest(BaseModel):
    """Request to execute a workflow"""
    trigger_data: Dict[str, Any] = Field(default_factory=dict)


class TemplateInstallRequest(BaseModel):
    """Request to install a workflow template"""
    template_id: str
    customizations: Dict[str, Any] = Field(default_factory=dict)


class WorkflowResponse(BaseModel):
    """Workflow response"""
    workflow_id: str
    name: str
    description: Optional[str]
    version: str
    enabled: bool
    nodes_count: int
    tags: List[str]
    created_at: str
    updated_at: str
    created_by: str


class ExecutionResponse(BaseModel):
    """Execution response"""
    execution_id: str
    workflow_id: str
    workflow_name: str
    status: str
    started_at: str
    completed_at: Optional[str]
    duration_ms: Optional[int]
    error: Optional[str]
    node_executions_count: int


# ============================================================================
# WORKFLOW API ROUTER
# ============================================================================

def create_workflow_router(db, security, get_current_user) -> APIRouter:
    """Create workflow API router with all endpoints"""

    router = APIRouter(prefix="/workflows", tags=["Workflows"])

    # Initialize AI service (will need API keys from env)
    import os
    ai_service = AIService(
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        google_api_key=os.getenv("GOOGLE_API_KEY", "")
    )

    # Initialize workflow engine
    engine = WorkflowEngine(db=db, ai_service=ai_service)

    # Initialize scheduler (optional - can start separately)
    scheduler = WorkflowScheduler(db=db, engine=engine)

    # ========================================================================
    # WORKFLOW CRUD ENDPOINTS
    # ========================================================================

    @router.post("", response_model=WorkflowResponse)
    async def create_workflow(
        request: WorkflowCreateRequest,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ):
        """Create a new workflow"""
        try:
            user = await get_current_user(credentials)

            # Convert nodes to NodeConfig objects
            nodes = [NodeConfig(**node) for node in request.nodes]

            workflow = WorkflowDefinition(
                name=request.name,
                description=request.description,
                nodes=nodes,
                variables=request.variables,
                tags=request.tags,
                enabled=request.enabled,
                created_by=user['id']
            )

            # Save to database
            await db.workflows.insert_one(workflow.model_dump())

            logger.info(f"Workflow created: {workflow.workflow_id} by user {user['id']}")

            return WorkflowResponse(
                workflow_id=workflow.workflow_id,
                name=workflow.name,
                description=workflow.description,
                version=workflow.version,
                enabled=workflow.enabled,
                nodes_count=len(workflow.nodes),
                tags=workflow.tags,
                created_at=workflow.created_at.isoformat(),
                updated_at=workflow.updated_at.isoformat(),
                created_by=workflow.created_by
            )

        except Exception as e:
            logger.error(f"Failed to create workflow: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("", response_model=List[WorkflowResponse])
    async def list_workflows(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        tags: Optional[str] = None,
        enabled: Optional[bool] = None
    ):
        """List all workflows"""
        try:
            user = await get_current_user(credentials)

            query = {"created_by": user['id']}
            if tags:
                query["tags"] = {"$in": tags.split(",")}
            if enabled is not None:
                query["enabled"] = enabled

            workflows = await db.workflows.find(query).to_list(length=100)

            return [
                WorkflowResponse(
                    workflow_id=w["workflow_id"],
                    name=w["name"],
                    description=w.get("description"),
                    version=w.get("version", "1.0.0"),
                    enabled=w.get("enabled", True),
                    nodes_count=len(w.get("nodes", [])),
                    tags=w.get("tags", []),
                    created_at=w["created_at"].isoformat() if isinstance(w["created_at"], datetime) else w["created_at"],
                    updated_at=w["updated_at"].isoformat() if isinstance(w["updated_at"], datetime) else w["updated_at"],
                    created_by=w["created_by"]
                )
                for w in workflows
            ]

        except Exception as e:
            logger.error(f"Failed to list workflows: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/{workflow_id}")
    async def get_workflow(
        workflow_id: str,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ):
        """Get a specific workflow"""
        try:
            user = await get_current_user(credentials)

            workflow = await db.workflows.find_one({
                "workflow_id": workflow_id,
                "created_by": user['id']
            })

            if not workflow:
                raise HTTPException(status_code=404, detail="Workflow not found")

            return workflow

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get workflow: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.put("/{workflow_id}", response_model=WorkflowResponse)
    async def update_workflow(
        workflow_id: str,
        request: WorkflowUpdateRequest,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ):
        """Update a workflow"""
        try:
            user = await get_current_user(credentials)

            workflow = await db.workflows.find_one({
                "workflow_id": workflow_id,
                "created_by": user['id']
            })

            if not workflow:
                raise HTTPException(status_code=404, detail="Workflow not found")

            # Build update dict
            update_data = {"updated_at": datetime.utcnow()}

            if request.name:
                update_data["name"] = request.name
            if request.description is not None:
                update_data["description"] = request.description
            if request.nodes:
                update_data["nodes"] = [NodeConfig(**node).model_dump() for node in request.nodes]
            if request.variables is not None:
                update_data["variables"] = request.variables
            if request.tags is not None:
                update_data["tags"] = request.tags
            if request.enabled is not None:
                update_data["enabled"] = request.enabled

            # Update in database
            await db.workflows.update_one(
                {"workflow_id": workflow_id},
                {"$set": update_data}
            )

            # Get updated workflow
            updated_workflow = await db.workflows.find_one({"workflow_id": workflow_id})

            return WorkflowResponse(
                workflow_id=updated_workflow["workflow_id"],
                name=updated_workflow["name"],
                description=updated_workflow.get("description"),
                version=updated_workflow.get("version", "1.0.0"),
                enabled=updated_workflow.get("enabled", True),
                nodes_count=len(updated_workflow.get("nodes", [])),
                tags=updated_workflow.get("tags", []),
                created_at=updated_workflow["created_at"].isoformat() if isinstance(updated_workflow["created_at"], datetime) else updated_workflow["created_at"],
                updated_at=updated_workflow["updated_at"].isoformat() if isinstance(updated_workflow["updated_at"], datetime) else updated_workflow["updated_at"],
                created_by=updated_workflow["created_by"]
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to update workflow: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.delete("/{workflow_id}")
    async def delete_workflow(
        workflow_id: str,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ):
        """Delete a workflow"""
        try:
            user = await get_current_user(credentials)

            result = await db.workflows.delete_one({
                "workflow_id": workflow_id,
                "created_by": user['id']
            })

            if result.deleted_count == 0:
                raise HTTPException(status_code=404, detail="Workflow not found")

            return {"message": "Workflow deleted successfully"}

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to delete workflow: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    # ========================================================================
    # WORKFLOW EXECUTION ENDPOINTS
    # ========================================================================

    @router.post("/{workflow_id}/execute", response_model=ExecutionResponse)
    async def execute_workflow(
        workflow_id: str,
        request: WorkflowExecuteRequest,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ):
        """Execute a workflow"""
        try:
            user = await get_current_user(credentials)

            # Get workflow
            workflow_data = await db.workflows.find_one({
                "workflow_id": workflow_id,
                "created_by": user['id']
            })

            if not workflow_data:
                raise HTTPException(status_code=404, detail="Workflow not found")

            if not workflow_data.get("enabled", True):
                raise HTTPException(status_code=400, detail="Workflow is disabled")

            # Convert to WorkflowDefinition
            workflow = WorkflowDefinition(**workflow_data)

            # Execute
            logger.info(f"Executing workflow {workflow_id} triggered by user {user['id']}")
            execution = await engine.execute_workflow(workflow, request.trigger_data)

            return ExecutionResponse(
                execution_id=execution.execution_id,
                workflow_id=execution.workflow_id,
                workflow_name=execution.workflow_name,
                status=execution.status.value,
                started_at=execution.started_at.isoformat(),
                completed_at=execution.completed_at.isoformat() if execution.completed_at else None,
                duration_ms=execution.duration_ms,
                error=execution.error,
                node_executions_count=len(execution.node_executions)
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to execute workflow: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/{workflow_id}/executions", response_model=List[ExecutionResponse])
    async def list_executions(
        workflow_id: str,
        credentials: HTTPAuthorizationCredentials = Depends(security),
        limit: int = 50,
        status: Optional[str] = None
    ):
        """List workflow executions"""
        try:
            user = await get_current_user(credentials)

            # Verify workflow ownership
            workflow = await db.workflows.find_one({
                "workflow_id": workflow_id,
                "created_by": user['id']
            })

            if not workflow:
                raise HTTPException(status_code=404, detail="Workflow not found")

            query = {"workflow_id": workflow_id}
            if status:
                query["status"] = status

            executions = await db.workflow_executions.find(query).sort("started_at", -1).to_list(length=limit)

            return [
                ExecutionResponse(
                    execution_id=e["execution_id"],
                    workflow_id=e["workflow_id"],
                    workflow_name=e["workflow_name"],
                    status=e["status"],
                    started_at=e["started_at"].isoformat() if isinstance(e["started_at"], datetime) else e["started_at"],
                    completed_at=e["completed_at"].isoformat() if e.get("completed_at") and isinstance(e["completed_at"], datetime) else e.get("completed_at"),
                    duration_ms=e.get("duration_ms"),
                    error=e.get("error"),
                    node_executions_count=len(e.get("node_executions", []))
                )
                for e in executions
            ]

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to list executions: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/executions/{execution_id}")
    async def get_execution(
        execution_id: str,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ):
        """Get execution details"""
        try:
            user = await get_current_user(credentials)

            execution = await db.workflow_executions.find_one({"execution_id": execution_id})

            if not execution:
                raise HTTPException(status_code=404, detail="Execution not found")

            # Verify workflow ownership
            workflow = await db.workflows.find_one({
                "workflow_id": execution["workflow_id"],
                "created_by": user['id']
            })

            if not workflow:
                raise HTTPException(status_code=404, detail="Workflow not found")

            return execution

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get execution: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    # ========================================================================
    # TEMPLATE ENDPOINTS
    # ========================================================================

    @router.get("/templates/list")
    async def list_templates(
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ):
        """List all available workflow templates"""
        try:
            await get_current_user(credentials)
            return WorkflowTemplates.get_all_templates()

        except Exception as e:
            logger.error(f"Failed to list templates: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    @router.post("/templates/{template_id}/install", response_model=WorkflowResponse)
    async def install_template(
        template_id: str,
        request: TemplateInstallRequest,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ):
        """Install a workflow template"""
        try:
            user = await get_current_user(credentials)

            # Get template
            template_map = {
                "pro_followup": WorkflowTemplates.create_pro_followup_workflow,
                "email_intelligence": WorkflowTemplates.create_email_intelligence_workflow,
                "adjuster_management": WorkflowTemplates.create_adjuster_management_workflow,
                "daily_summary": WorkflowTemplates.create_daily_summary_workflow
            }

            if template_id not in template_map:
                raise HTTPException(status_code=404, detail="Template not found")

            # Create workflow from template
            workflow = template_map[template_id](user['id'])

            # Apply customizations
            if request.customizations:
                if "name" in request.customizations:
                    workflow.name = request.customizations["name"]
                if "variables" in request.customizations:
                    workflow.variables.update(request.customizations["variables"])
                if "tags" in request.customizations:
                    workflow.tags.extend(request.customizations["tags"])

            # Save to database
            await db.workflows.insert_one(workflow.model_dump())

            logger.info(f"Template {template_id} installed as workflow {workflow.workflow_id} by user {user['id']}")

            return WorkflowResponse(
                workflow_id=workflow.workflow_id,
                name=workflow.name,
                description=workflow.description,
                version=workflow.version,
                enabled=workflow.enabled,
                nodes_count=len(workflow.nodes),
                tags=workflow.tags,
                created_at=workflow.created_at.isoformat(),
                updated_at=workflow.updated_at.isoformat(),
                created_by=workflow.created_by
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to install template: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    # ========================================================================
    # ANALYTICS ENDPOINTS
    # ========================================================================

    @router.get("/analytics/overview")
    async def get_analytics_overview(
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ):
        """Get workflow analytics overview"""
        try:
            user = await get_current_user(credentials)

            # Get all user workflows
            workflows = await db.workflows.find({"created_by": user['id']}).to_list(length=100)
            workflow_ids = [w["workflow_id"] for w in workflows]

            # Get execution stats
            total_executions = await db.workflow_executions.count_documents({
                "workflow_id": {"$in": workflow_ids}
            })

            successful_executions = await db.workflow_executions.count_documents({
                "workflow_id": {"$in": workflow_ids},
                "status": "completed"
            })

            failed_executions = await db.workflow_executions.count_documents({
                "workflow_id": {"$in": workflow_ids},
                "status": "failed"
            })

            # Get recent executions
            recent_executions = await db.workflow_executions.find({
                "workflow_id": {"$in": workflow_ids}
            }).sort("started_at", -1).limit(10).to_list(length=10)

            return {
                "total_workflows": len(workflows),
                "enabled_workflows": len([w for w in workflows if w.get("enabled", True)]),
                "total_executions": total_executions,
                "successful_executions": successful_executions,
                "failed_executions": failed_executions,
                "success_rate": (successful_executions / total_executions * 100) if total_executions > 0 else 0,
                "recent_executions": [
                    {
                        "execution_id": e["execution_id"],
                        "workflow_name": e["workflow_name"],
                        "status": e["status"],
                        "started_at": e["started_at"].isoformat() if isinstance(e["started_at"], datetime) else e["started_at"],
                        "duration_ms": e.get("duration_ms")
                    }
                    for e in recent_executions
                ]
            }

        except Exception as e:
            logger.error(f"Failed to get analytics: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    # ========================================================================
    # NODE TYPES ENDPOINT (for UI builder)
    # ========================================================================

    @router.get("/node-types")
    async def get_node_types(
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ):
        """Get available node types for workflow builder"""
        try:
            await get_current_user(credentials)

            return {
                "triggers": [
                    {
                        "type": NodeType.TRIGGER_SCHEDULE.value,
                        "name": "Schedule Trigger",
                        "description": "Run workflow on a schedule (cron)",
                        "icon": "⏰",
                        "config_schema": {
                            "schedule": {
                                "type": "object",
                                "properties": {
                                    "interval": {"type": "string", "enum": ["hourly", "daily", "weekly", "monthly"]},
                                    "time": {"type": "string", "description": "Time in HH:MM format"}
                                }
                            }
                        }
                    },
                    {
                        "type": NodeType.TRIGGER_EVENT.value,
                        "name": "Event Trigger",
                        "description": "Trigger on database event",
                        "icon": "⚡",
                        "config_schema": {}
                    }
                ],
                "ai": [
                    {
                        "type": NodeType.AI_PROCESS_EMAIL.value,
                        "name": "Process Email with AI",
                        "description": "Extract intent, sentiment, urgency from emails",
                        "icon": "🤖",
                        "config_schema": {}
                    },
                    {
                        "type": NodeType.AI_EXTRACT_TASKS.value,
                        "name": "Extract Tasks",
                        "description": "Find actionable tasks in text",
                        "icon": "📋",
                        "config_schema": {}
                    },
                    {
                        "type": NodeType.AI_ANALYZE_SENTIMENT.value,
                        "name": "Analyze Sentiment",
                        "description": "Deep sentiment and emotion analysis",
                        "icon": "😊",
                        "config_schema": {}
                    },
                    {
                        "type": NodeType.AI_GENERATE_RESPONSE.value,
                        "name": "Generate Response",
                        "description": "AI-generated messages and content",
                        "icon": "✍️",
                        "config_schema": {
                            "response_type": {"type": "string", "description": "Type of response to generate"}
                        }
                    },
                    {
                        "type": NodeType.AI_PREDICT_BEHAVIOR.value,
                        "name": "Predict Behavior",
                        "description": "Predict future actions based on history",
                        "icon": "🔮",
                        "config_schema": {
                            "entity_type": {"type": "string", "description": "Type of entity to predict"}
                        }
                    }
                ],
                "actions": [
                    {
                        "type": NodeType.ACTION_QUERY_DB.value,
                        "name": "Query Database",
                        "description": "Read data from MongoDB",
                        "icon": "🔍",
                        "config_schema": {
                            "collection": {"type": "string"},
                            "query": {"type": "object"},
                            "limit": {"type": "number"}
                        }
                    },
                    {
                        "type": NodeType.ACTION_UPDATE_DB.value,
                        "name": "Update Database",
                        "description": "Write or update data",
                        "icon": "💾",
                        "config_schema": {
                            "collection": {"type": "string"},
                            "operation": {"type": "string", "enum": ["update_one", "update_many", "insert_one"]},
                            "query": {"type": "object"},
                            "update": {"type": "object"}
                        }
                    },
                    {
                        "type": NodeType.ACTION_SEND_EMAIL.value,
                        "name": "Send Email",
                        "description": "Send email to recipients",
                        "icon": "📧",
                        "config_schema": {
                            "to": {"type": "string"},
                            "subject": {"type": "string"},
                            "body": {"type": "string"}
                        }
                    }
                ],
                "conditions": [
                    {
                        "type": NodeType.CONDITION_IF.value,
                        "name": "If Condition",
                        "description": "Conditional branching",
                        "icon": "🔀",
                        "config_schema": {
                            "condition": {"type": "string", "description": "Condition expression"}
                        }
                    },
                    {
                        "type": NodeType.CONDITION_FILTER.value,
                        "name": "Filter Items",
                        "description": "Filter array items by condition",
                        "icon": "🔽",
                        "config_schema": {
                            "condition": {"type": "string"}
                        }
                    }
                ],
                "transforms": [
                    {
                        "type": NodeType.TRANSFORM_MAP.value,
                        "name": "Map/Transform",
                        "description": "Transform data structure",
                        "icon": "🔄",
                        "config_schema": {
                            "mapping": {"type": "object"}
                        }
                    },
                    {
                        "type": NodeType.TRANSFORM_MERGE.value,
                        "name": "Merge Data",
                        "description": "Combine multiple data sources",
                        "icon": "🔗",
                        "config_schema": {
                            "merge_keys": {"type": "array"}
                        }
                    }
                ],
                "flow": [
                    {
                        "type": NodeType.FLOW_DELAY.value,
                        "name": "Delay",
                        "description": "Wait for specified time",
                        "icon": "⏱️",
                        "config_schema": {
                            "delay_seconds": {"type": "number"}
                        }
                    },
                    {
                        "type": NodeType.FLOW_PARALLEL.value,
                        "name": "Parallel Execution",
                        "description": "Run multiple branches in parallel",
                        "icon": "⚡",
                        "config_schema": {}
                    }
                ]
            }

        except Exception as e:
            logger.error(f"Failed to get node types: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))

    return router
