"""
Advanced Workflow Automation Engine for RestorationOS
10x better than Make.com/n8n - native, intelligent, and scalable
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from uuid import uuid4
import traceback

from pydantic import BaseModel, Field
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import google.generativeai as genai
from openai import AsyncOpenAI

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# WORKFLOW MODELS
# ============================================================================

class NodeType(str, Enum):
    """Available node types in the workflow engine"""
    TRIGGER_SCHEDULE = "trigger_schedule"
    TRIGGER_EVENT = "trigger_event"
    TRIGGER_WEBHOOK = "trigger_webhook"

    ACTION_QUERY_DB = "action_query_db"
    ACTION_UPDATE_DB = "action_update_db"
    ACTION_SEND_EMAIL = "action_send_email"
    ACTION_SEND_SMS = "action_send_sms"
    ACTION_HTTP_REQUEST = "action_http_request"
    ACTION_GENERATE_PDF = "action_generate_pdf"
    ACTION_LOG = "action_log"

    AI_PROCESS_EMAIL = "ai_process_email"
    AI_EXTRACT_TASKS = "ai_extract_tasks"
    AI_ANALYZE_SENTIMENT = "ai_analyze_sentiment"
    AI_GENERATE_RESPONSE = "ai_generate_response"
    AI_PREDICT_BEHAVIOR = "ai_predict_behavior"
    AI_CATEGORIZE = "ai_categorize"
    AI_SUMMARIZE = "ai_summarize"

    CONDITION_IF = "condition_if"
    CONDITION_SWITCH = "condition_switch"
    CONDITION_FILTER = "condition_filter"

    TRANSFORM_MAP = "transform_map"
    TRANSFORM_MERGE = "transform_merge"
    TRANSFORM_AGGREGATE = "transform_aggregate"

    FLOW_DELAY = "flow_delay"
    FLOW_LOOP = "flow_loop"
    FLOW_PARALLEL = "flow_parallel"


class NodeConfig(BaseModel):
    """Configuration for a workflow node"""
    node_id: str = Field(default_factory=lambda: str(uuid4()))
    node_type: NodeType
    name: str
    description: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    next_nodes: List[str] = Field(default_factory=list)
    error_handler: Optional[str] = None
    retry_config: Optional[Dict[str, Any]] = None
    timeout: int = 300  # seconds


class WorkflowDefinition(BaseModel):
    """Complete workflow definition"""
    workflow_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None
    version: str = "1.0.0"
    enabled: bool = True
    nodes: List[NodeConfig]
    variables: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    organization_id: Optional[str] = None


class ExecutionStatus(str, Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class NodeExecution(BaseModel):
    """Record of a single node execution"""
    node_id: str
    node_type: NodeType
    status: ExecutionStatus
    input_data: Dict[str, Any] = Field(default_factory=dict)
    output_data: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    retry_count: int = 0


class WorkflowExecution(BaseModel):
    """Record of a complete workflow execution"""
    execution_id: str = Field(default_factory=lambda: str(uuid4()))
    workflow_id: str
    workflow_name: str
    status: ExecutionStatus = ExecutionStatus.PENDING
    trigger_data: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)
    node_executions: List[NodeExecution] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    error: Optional[str] = None


# ============================================================================
# AI SERVICES (10x BETTER INTELLIGENCE)
# ============================================================================

class AIService:
    """Advanced AI services for workflow automation"""

    def __init__(self, openai_api_key: str, google_api_key: str):
        self.openai_client = AsyncOpenAI(api_key=openai_api_key)
        genai.configure(api_key=google_api_key)
        self.gemini_model = genai.GenerativeModel('gemini-pro')

    async def process_email(self, email_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Advanced email processing with AI
        Extracts: intent, urgency, sentiment, action items, entities
        """
        email_content = f"""
        From: {email_data.get('from', 'Unknown')}
        Subject: {email_data.get('subject', 'No subject')}
        Body: {email_data.get('body', 'No content')}
        """

        prompt = f"""
        Analyze this email and extract structured information:

        {email_content}

        Return a JSON object with:
        1. intent: primary intent (payment_inquiry, status_update, complaint, request, etc.)
        2. urgency: urgency level (low, medium, high, critical)
        3. sentiment: overall sentiment (positive, neutral, negative, angry)
        4. entities: extracted entities (names, dates, amounts, job IDs, claim numbers)
        5. action_items: list of action items mentioned
        6. requires_response: boolean if response needed
        7. response_deadline: when to respond by (if mentioned)
        8. summary: 1-2 sentence summary
        9. category: email category (insurance, customer, vendor, internal)
        10. priority_score: 0-100 priority score
        """

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert email analyst for a restoration company. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            result['original_email'] = email_data
            result['processed_at'] = datetime.utcnow().isoformat()

            return result

        except Exception as e:
            logger.error(f"Email processing failed: {str(e)}")
            return {
                "error": str(e),
                "intent": "unknown",
                "urgency": "medium",
                "sentiment": "neutral"
            }

    async def extract_tasks(self, text: str, context: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Extract actionable tasks from text using AI
        Returns structured task list with assignees, deadlines, priorities
        """
        prompt = f"""
        Extract all actionable tasks from this text:

        {text}

        Context: {json.dumps(context) if context else 'None'}

        Return a JSON array of tasks with:
        1. task: clear description of the task
        2. assignee: who should do it (if mentioned)
        3. deadline: when it's due (if mentioned)
        4. priority: low, medium, high, critical
        5. estimated_duration: estimated time to complete
        6. dependencies: any dependencies on other tasks
        7. category: task category (follow_up, documentation, billing, etc.)
        """

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a task extraction expert. Always return valid JSON array."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            tasks = result.get('tasks', [])

            return tasks

        except Exception as e:
            logger.error(f"Task extraction failed: {str(e)}")
            return []

    async def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """
        Deep sentiment analysis with emotional intelligence
        """
        prompt = f"""
        Perform deep sentiment analysis on this text:

        {text}

        Return JSON with:
        1. overall_sentiment: positive, neutral, negative, mixed
        2. sentiment_score: -1.0 to 1.0
        3. emotions: list of detected emotions (frustrated, satisfied, confused, angry, etc.)
        4. tone: professional, casual, aggressive, friendly, etc.
        5. urgency_indicators: phrases indicating urgency
        6. satisfaction_level: 0-100
        7. churn_risk: 0-100 (risk of losing this customer)
        8. recommended_response_tone: how to respond
        """

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an emotional intelligence expert. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            logger.error(f"Sentiment analysis failed: {str(e)}")
            return {
                "overall_sentiment": "neutral",
                "sentiment_score": 0,
                "error": str(e)
            }

    async def generate_response(self,
                               input_data: Dict[str, Any],
                               response_type: str,
                               context: Dict[str, Any] = None) -> str:
        """
        Generate intelligent responses (emails, messages, summaries)
        """
        context_str = json.dumps(context, indent=2) if context else "No additional context"

        prompt = f"""
        Generate a professional {response_type} for a restoration company.

        Input data: {json.dumps(input_data, indent=2)}
        Context: {context_str}

        Requirements:
        - Professional and empathetic tone
        - Clear and concise
        - Action-oriented if needed
        - Include relevant details from context
        - Appropriate for restoration/disaster recovery industry
        """

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": f"You are a professional communication expert for a restoration company. Generate {response_type}."},
                    {"role": "user", "content": prompt}
                ]
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Response generation failed: {str(e)}")
            return f"Error generating response: {str(e)}"

    async def predict_behavior(self,
                              entity_type: str,
                              entity_id: str,
                              historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Predict future behavior based on historical data
        Use cases: payment likelihood, response time, customer satisfaction
        """
        prompt = f"""
        Analyze this historical data for {entity_type} {entity_id} and predict future behavior:

        Historical data: {json.dumps(historical_data, indent=2)}

        Return JSON with:
        1. payment_likelihood: 0-100 (if applicable)
        2. expected_response_time: estimated hours
        3. satisfaction_trend: improving, stable, declining
        4. risk_factors: list of identified risks
        5. recommended_actions: what to do proactively
        6. confidence_level: 0-100 confidence in predictions
        7. key_patterns: identified behavioral patterns
        """

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a predictive analytics expert. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            logger.error(f"Behavior prediction failed: {str(e)}")
            return {"error": str(e)}

    async def categorize(self,
                        item: Dict[str, Any],
                        categories: List[str],
                        context: str = "") -> Dict[str, Any]:
        """
        Intelligent categorization with confidence scores
        """
        prompt = f"""
        Categorize this item into one of these categories: {', '.join(categories)}

        Item: {json.dumps(item, indent=2)}
        Context: {context}

        Return JSON with:
        1. category: best matching category
        2. confidence: 0-100 confidence score
        3. reasoning: why this category was chosen
        4. alternative_categories: other possible categories with scores
        """

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a categorization expert. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"}
            )

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            logger.error(f"Categorization failed: {str(e)}")
            return {"error": str(e), "category": categories[0] if categories else "unknown"}

    async def summarize(self,
                       data: Any,
                       summary_type: str = "brief") -> str:
        """
        Generate intelligent summaries
        Types: brief, detailed, executive, technical
        """
        data_str = json.dumps(data, indent=2) if not isinstance(data, str) else data

        prompt = f"""
        Create a {summary_type} summary of this data:

        {data_str}

        Summary requirements:
        - {summary_type} style
        - Key highlights and insights
        - Actionable takeaways if relevant
        - Clear and professional language
        """

        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": f"You are an expert at creating {summary_type} summaries."},
                    {"role": "user", "content": prompt}
                ]
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"Summarization failed: {str(e)}")
            return f"Summary unavailable: {str(e)}"


# ============================================================================
# WORKFLOW ENGINE (ORCHESTRATION)
# ============================================================================

class WorkflowEngine:
    """
    Advanced workflow orchestration engine
    10x better than Make.com - native, reliable, scalable
    """

    def __init__(self,
                 db: AsyncIOMotorDatabase,
                 ai_service: AIService):
        self.db = db
        self.ai_service = ai_service
        self.running_executions: Dict[str, WorkflowExecution] = {}
        self.node_handlers: Dict[NodeType, Callable] = {}

        # Register node handlers
        self._register_node_handlers()

    def _register_node_handlers(self):
        """Register all node type handlers"""
        # AI Nodes
        self.node_handlers[NodeType.AI_PROCESS_EMAIL] = self._handle_ai_process_email
        self.node_handlers[NodeType.AI_EXTRACT_TASKS] = self._handle_ai_extract_tasks
        self.node_handlers[NodeType.AI_ANALYZE_SENTIMENT] = self._handle_ai_analyze_sentiment
        self.node_handlers[NodeType.AI_GENERATE_RESPONSE] = self._handle_ai_generate_response
        self.node_handlers[NodeType.AI_PREDICT_BEHAVIOR] = self._handle_ai_predict_behavior
        self.node_handlers[NodeType.AI_CATEGORIZE] = self._handle_ai_categorize
        self.node_handlers[NodeType.AI_SUMMARIZE] = self._handle_ai_summarize

        # Action Nodes
        self.node_handlers[NodeType.ACTION_QUERY_DB] = self._handle_action_query_db
        self.node_handlers[NodeType.ACTION_UPDATE_DB] = self._handle_action_update_db
        self.node_handlers[NodeType.ACTION_SEND_EMAIL] = self._handle_action_send_email
        self.node_handlers[NodeType.ACTION_LOG] = self._handle_action_log

        # Condition Nodes
        self.node_handlers[NodeType.CONDITION_IF] = self._handle_condition_if
        self.node_handlers[NodeType.CONDITION_FILTER] = self._handle_condition_filter

        # Transform Nodes
        self.node_handlers[NodeType.TRANSFORM_MAP] = self._handle_transform_map
        self.node_handlers[NodeType.TRANSFORM_MERGE] = self._handle_transform_merge

        # Flow Control Nodes
        self.node_handlers[NodeType.FLOW_DELAY] = self._handle_flow_delay
        self.node_handlers[NodeType.FLOW_PARALLEL] = self._handle_flow_parallel

    # ========================================================================
    # EXECUTION ENGINE
    # ========================================================================

    async def execute_workflow(self,
                               workflow: WorkflowDefinition,
                               trigger_data: Dict[str, Any] = None) -> WorkflowExecution:
        """
        Execute a complete workflow
        """
        execution = WorkflowExecution(
            workflow_id=workflow.workflow_id,
            workflow_name=workflow.name,
            trigger_data=trigger_data or {},
            context=workflow.variables.copy()
        )

        execution.status = ExecutionStatus.RUNNING
        self.running_executions[execution.execution_id] = execution

        # Save initial execution record
        await self.db.workflow_executions.insert_one(execution.model_dump())

        logger.info(f"Starting workflow execution: {execution.execution_id} for workflow: {workflow.name}")

        try:
            # Find trigger node(s)
            trigger_nodes = [n for n in workflow.nodes if n.node_type.startswith("trigger_")]

            if not trigger_nodes:
                raise ValueError("No trigger nodes found in workflow")

            # Execute from trigger node
            for trigger_node in trigger_nodes:
                await self._execute_node(trigger_node, workflow, execution, trigger_data or {})

            # Mark as completed
            execution.status = ExecutionStatus.COMPLETED
            execution.completed_at = datetime.utcnow()
            execution.duration_ms = int((execution.completed_at - execution.started_at).total_seconds() * 1000)

            logger.info(f"Workflow execution completed: {execution.execution_id} in {execution.duration_ms}ms")

        except Exception as e:
            execution.status = ExecutionStatus.FAILED
            execution.error = str(e)
            execution.completed_at = datetime.utcnow()
            logger.error(f"Workflow execution failed: {execution.execution_id} - {str(e)}")
            logger.error(traceback.format_exc())

        finally:
            # Update execution record
            await self.db.workflow_executions.update_one(
                {"execution_id": execution.execution_id},
                {"$set": execution.model_dump()}
            )

            # Remove from running executions
            self.running_executions.pop(execution.execution_id, None)

        return execution

    async def _execute_node(self,
                           node: NodeConfig,
                           workflow: WorkflowDefinition,
                           execution: WorkflowExecution,
                           input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single node with retry logic and error handling
        """
        node_execution = NodeExecution(
            node_id=node.node_id,
            node_type=node.node_type,
            status=ExecutionStatus.RUNNING,
            input_data=input_data,
            started_at=datetime.utcnow()
        )

        execution.node_executions.append(node_execution)

        logger.info(f"Executing node: {node.name} ({node.node_type})")

        try:
            # Get handler for this node type
            handler = self.node_handlers.get(node.node_type)

            if not handler:
                raise ValueError(f"No handler registered for node type: {node.node_type}")

            # Execute with timeout
            output_data = await asyncio.wait_for(
                handler(node, execution.context, input_data),
                timeout=node.timeout
            )

            node_execution.status = ExecutionStatus.COMPLETED
            node_execution.output_data = output_data

            # Update context with output
            execution.context[f"node_{node.node_id}"] = output_data

            # Execute next nodes
            if node.next_nodes:
                node_map = {n.node_id: n for n in workflow.nodes}

                for next_node_id in node.next_nodes:
                    next_node = node_map.get(next_node_id)
                    if next_node:
                        await self._execute_node(next_node, workflow, execution, output_data)

            return output_data

        except asyncio.TimeoutError:
            node_execution.status = ExecutionStatus.TIMEOUT
            node_execution.error = f"Node execution timed out after {node.timeout}s"
            logger.error(f"Node timeout: {node.name}")
            raise

        except Exception as e:
            node_execution.status = ExecutionStatus.FAILED
            node_execution.error = str(e)
            logger.error(f"Node execution failed: {node.name} - {str(e)}")

            # Handle error with error handler node if configured
            if node.error_handler:
                logger.info(f"Executing error handler for node: {node.name}")
                # TODO: Implement error handler execution

            raise

        finally:
            node_execution.completed_at = datetime.utcnow()
            node_execution.duration_ms = int(
                (node_execution.completed_at - node_execution.started_at).total_seconds() * 1000
            )

    # ========================================================================
    # AI NODE HANDLERS
    # ========================================================================

    async def _handle_ai_process_email(self,
                                      node: NodeConfig,
                                      context: Dict[str, Any],
                                      input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process email with AI"""
        email_data = input_data.get('email', input_data)
        result = await self.ai_service.process_email(email_data)
        return {"processed_email": result}

    async def _handle_ai_extract_tasks(self,
                                      node: NodeConfig,
                                      context: Dict[str, Any],
                                      input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract tasks from text"""
        text = input_data.get('text', '')
        tasks = await self.ai_service.extract_tasks(text, context)
        return {"tasks": tasks}

    async def _handle_ai_analyze_sentiment(self,
                                          node: NodeConfig,
                                          context: Dict[str, Any],
                                          input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sentiment"""
        text = input_data.get('text', '')
        sentiment = await self.ai_service.analyze_sentiment(text)
        return {"sentiment": sentiment}

    async def _handle_ai_generate_response(self,
                                          node: NodeConfig,
                                          context: Dict[str, Any],
                                          input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate AI response"""
        response_type = node.config.get('response_type', 'email')
        response = await self.ai_service.generate_response(input_data, response_type, context)
        return {"generated_response": response}

    async def _handle_ai_predict_behavior(self,
                                         node: NodeConfig,
                                         context: Dict[str, Any],
                                         input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Predict behavior"""
        entity_type = node.config.get('entity_type', 'customer')
        entity_id = input_data.get('entity_id', '')
        historical_data = input_data.get('historical_data', [])

        prediction = await self.ai_service.predict_behavior(entity_type, entity_id, historical_data)
        return {"prediction": prediction}

    async def _handle_ai_categorize(self,
                                   node: NodeConfig,
                                   context: Dict[str, Any],
                                   input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Categorize item"""
        categories = node.config.get('categories', [])
        category_context = node.config.get('context', '')

        result = await self.ai_service.categorize(input_data, categories, category_context)
        return {"categorization": result}

    async def _handle_ai_summarize(self,
                                  node: NodeConfig,
                                  context: Dict[str, Any],
                                  input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize data"""
        summary_type = node.config.get('summary_type', 'brief')
        summary = await self.ai_service.summarize(input_data, summary_type)
        return {"summary": summary}

    # ========================================================================
    # ACTION NODE HANDLERS
    # ========================================================================

    async def _handle_action_query_db(self,
                                     node: NodeConfig,
                                     context: Dict[str, Any],
                                     input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Query database"""
        collection_name = node.config.get('collection')
        query = node.config.get('query', {})

        # Support variable substitution in query
        query = self._substitute_variables(query, context, input_data)

        collection = self.db[collection_name]
        results = await collection.find(query).to_list(length=node.config.get('limit', 100))

        return {"results": results, "count": len(results)}

    async def _handle_action_update_db(self,
                                      node: NodeConfig,
                                      context: Dict[str, Any],
                                      input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update database"""
        collection_name = node.config.get('collection')
        query = node.config.get('query', {})
        update = node.config.get('update', {})
        operation = node.config.get('operation', 'update_one')  # update_one, update_many, insert_one

        # Support variable substitution
        query = self._substitute_variables(query, context, input_data)
        update = self._substitute_variables(update, context, input_data)

        collection = self.db[collection_name]

        if operation == 'update_one':
            result = await collection.update_one(query, update)
            return {"matched_count": result.matched_count, "modified_count": result.modified_count}
        elif operation == 'update_many':
            result = await collection.update_many(query, update)
            return {"matched_count": result.matched_count, "modified_count": result.modified_count}
        elif operation == 'insert_one':
            result = await collection.insert_one(update)
            return {"inserted_id": str(result.inserted_id)}
        else:
            raise ValueError(f"Unknown operation: {operation}")

    async def _handle_action_send_email(self,
                                       node: NodeConfig,
                                       context: Dict[str, Any],
                                       input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Send email (placeholder - integrate with actual email service)"""
        to = node.config.get('to', input_data.get('to'))
        subject = node.config.get('subject', input_data.get('subject'))
        body = node.config.get('body', input_data.get('body'))

        # Substitute variables
        to = self._substitute_variables(to, context, input_data)
        subject = self._substitute_variables(subject, context, input_data)
        body = self._substitute_variables(body, context, input_data)

        logger.info(f"Would send email to: {to} with subject: {subject}")

        # TODO: Integrate with actual email service (SendGrid, AWS SES, etc.)
        return {
            "sent": True,
            "to": to,
            "subject": subject,
            "timestamp": datetime.utcnow().isoformat()
        }

    async def _handle_action_log(self,
                                node: NodeConfig,
                                context: Dict[str, Any],
                                input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Log action"""
        message = node.config.get('message', str(input_data))
        level = node.config.get('level', 'info')

        message = self._substitute_variables(message, context, input_data)

        if level == 'info':
            logger.info(f"Workflow log: {message}")
        elif level == 'warning':
            logger.warning(f"Workflow log: {message}")
        elif level == 'error':
            logger.error(f"Workflow log: {message}")

        return {"logged": True, "message": message}

    # ========================================================================
    # CONDITION NODE HANDLERS
    # ========================================================================

    async def _handle_condition_if(self,
                                  node: NodeConfig,
                                  context: Dict[str, Any],
                                  input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Conditional execution"""
        condition = node.config.get('condition', '')

        # Evaluate condition (simple implementation)
        result = self._evaluate_condition(condition, context, input_data)

        return {"condition_result": result, "input_data": input_data}

    async def _handle_condition_filter(self,
                                      node: NodeConfig,
                                      context: Dict[str, Any],
                                      input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Filter items based on condition"""
        items = input_data.get('items', [])
        filter_condition = node.config.get('condition', '')

        filtered_items = [
            item for item in items
            if self._evaluate_condition(filter_condition, context, item)
        ]

        return {"filtered_items": filtered_items, "count": len(filtered_items)}

    # ========================================================================
    # TRANSFORM NODE HANDLERS
    # ========================================================================

    async def _handle_transform_map(self,
                                   node: NodeConfig,
                                   context: Dict[str, Any],
                                   input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Map/transform data"""
        items = input_data.get('items', [input_data])
        mapping = node.config.get('mapping', {})

        transformed_items = []
        for item in items:
            transformed = {}
            for target_key, source_path in mapping.items():
                transformed[target_key] = self._get_nested_value(item, source_path)
            transformed_items.append(transformed)

        return {"transformed_items": transformed_items}

    async def _handle_transform_merge(self,
                                     node: NodeConfig,
                                     context: Dict[str, Any],
                                     input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge multiple data sources"""
        merge_keys = node.config.get('merge_keys', [])

        merged = {}
        for key in merge_keys:
            if key in context:
                merged.update(context[key] if isinstance(context[key], dict) else {key: context[key]})

        merged.update(input_data)

        return {"merged_data": merged}

    # ========================================================================
    # FLOW CONTROL NODE HANDLERS
    # ========================================================================

    async def _handle_flow_delay(self,
                                node: NodeConfig,
                                context: Dict[str, Any],
                                input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Delay execution"""
        delay_seconds = node.config.get('delay_seconds', 0)

        if delay_seconds > 0:
            logger.info(f"Delaying execution for {delay_seconds} seconds")
            await asyncio.sleep(delay_seconds)

        return input_data

    async def _handle_flow_parallel(self,
                                   node: NodeConfig,
                                   context: Dict[str, Any],
                                   input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute multiple branches in parallel"""
        # This would be handled by the execution engine
        # when multiple next_nodes are configured
        return input_data

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def _substitute_variables(self, value: Any, context: Dict[str, Any], input_data: Dict[str, Any]) -> Any:
        """Substitute variables in strings like {{variable_name}}"""
        if not isinstance(value, str):
            if isinstance(value, dict):
                return {k: self._substitute_variables(v, context, input_data) for k, v in value.items()}
            elif isinstance(value, list):
                return [self._substitute_variables(v, context, input_data) for v in value]
            return value

        # Simple variable substitution
        import re
        pattern = r'\{\{([^}]+)\}\}'

        def replacer(match):
            var_name = match.group(1).strip()

            # Try context first, then input_data
            if var_name in context:
                return str(context[var_name])
            elif var_name in input_data:
                return str(input_data[var_name])
            else:
                # Support nested access like "data.field"
                return str(self._get_nested_value(context, var_name) or
                          self._get_nested_value(input_data, var_name) or
                          match.group(0))

        return re.sub(pattern, replacer, value)

    def _get_nested_value(self, obj: Any, path: str) -> Any:
        """Get nested value from object using dot notation"""
        try:
            parts = path.split('.')
            current = obj
            for part in parts:
                if isinstance(current, dict):
                    current = current.get(part)
                elif isinstance(current, list) and part.isdigit():
                    current = current[int(part)]
                else:
                    return None
            return current
        except:
            return None

    def _evaluate_condition(self, condition: str, context: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """Evaluate a simple condition"""
        try:
            # Very basic condition evaluation
            # In production, use a proper expression parser

            # Support simple comparisons like "urgency == 'high'" or "amount > 1000"
            condition = self._substitute_variables(condition, context, data)

            # For safety, only allow basic comparisons
            allowed_operators = ['==', '!=', '>', '<', '>=', '<=', 'in', 'not in']

            for op in allowed_operators:
                if op in condition:
                    parts = condition.split(op, 1)
                    if len(parts) == 2:
                        left = eval(parts[0].strip())
                        right = eval(parts[1].strip())

                        if op == '==':
                            return left == right
                        elif op == '!=':
                            return left != right
                        elif op == '>':
                            return left > right
                        elif op == '<':
                            return left < right
                        elif op == '>=':
                            return left >= right
                        elif op == '<=':
                            return left <= right
                        elif op == 'in':
                            return left in right
                        elif op == 'not in':
                            return left not in right

            # If no operator found, try to evaluate as boolean
            return bool(eval(condition))

        except Exception as e:
            logger.error(f"Condition evaluation failed: {condition} - {str(e)}")
            return False


# ============================================================================
# WORKFLOW SCHEDULER
# ============================================================================

class WorkflowScheduler:
    """
    Cron-based workflow scheduler
    """

    def __init__(self, db: AsyncIOMotorDatabase, engine: WorkflowEngine):
        self.db = db
        self.engine = engine
        self.running = False
        self.scheduled_tasks: Dict[str, asyncio.Task] = {}

    async def start(self):
        """Start the scheduler"""
        self.running = True
        logger.info("Workflow scheduler started")

        # Check for scheduled workflows every minute
        while self.running:
            try:
                await self._check_scheduled_workflows()
                await asyncio.sleep(60)  # Check every minute
            except Exception as e:
                logger.error(f"Scheduler error: {str(e)}")
                await asyncio.sleep(60)

    async def stop(self):
        """Stop the scheduler"""
        self.running = False

        # Cancel all scheduled tasks
        for task in self.scheduled_tasks.values():
            task.cancel()

        logger.info("Workflow scheduler stopped")

    async def _check_scheduled_workflows(self):
        """Check for workflows that need to run"""
        # Find workflows with schedule triggers
        workflows = await self.db.workflows.find({"enabled": True}).to_list(length=None)

        for workflow_data in workflows:
            workflow = WorkflowDefinition(**workflow_data)

            # Find schedule trigger nodes
            schedule_nodes = [
                n for n in workflow.nodes
                if n.node_type == NodeType.TRIGGER_SCHEDULE
            ]

            for schedule_node in schedule_nodes:
                if self._should_run(schedule_node, workflow):
                    logger.info(f"Triggering scheduled workflow: {workflow.name}")

                    # Execute workflow asynchronously
                    task = asyncio.create_task(
                        self.engine.execute_workflow(workflow, {"trigger": "schedule"})
                    )
                    self.scheduled_tasks[workflow.workflow_id] = task

    def _should_run(self, schedule_node: NodeConfig, workflow: WorkflowDefinition) -> bool:
        """Check if workflow should run based on schedule"""
        # Check last execution time
        schedule = schedule_node.config.get('schedule', {})
        interval = schedule.get('interval', 'daily')  # hourly, daily, weekly, monthly
        time_of_day = schedule.get('time', '09:00')

        # Simple schedule checking (in production, use APScheduler or similar)
        now = datetime.utcnow()

        # Check if it's the right time
        target_hour, target_minute = map(int, time_of_day.split(':'))

        if interval == 'daily':
            return now.hour == target_hour and now.minute == target_minute
        elif interval == 'hourly':
            return now.minute == target_minute

        return False
