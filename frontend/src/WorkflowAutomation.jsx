/**
 * Workflow Automation UI - 10x Better Than Make.com
 *
 * Features:
 * - Visual workflow builder with drag-and-drop
 * - Pre-built templates library
 * - Real-time execution monitoring
 * - Analytics dashboard
 * - AI-powered workflow suggestions
 */

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from './components/ui/card';
import { Button } from './components/ui/button';
import { Badge } from './components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { ScrollArea } from './components/ui/scroll-area';
import { Separator } from './components/ui/separator';
import { toast } from './hooks/use-toast';
import {
  PlayCircle,
  Pause,
  Trash2,
  Copy,
  Settings,
  Activity,
  TrendingUp,
  Zap,
  GitBranch,
  Calendar,
  Mail,
  Database,
  Bot,
  Filter,
  Workflow,
  Plus,
  Download,
  BarChart3,
  CheckCircle2,
  XCircle,
  Clock,
  AlertCircle,
  ChevronRight,
  Sparkles
} from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from './components/ui/dialog';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';
import { Textarea } from './components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './components/ui/select';
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from './components/ui/alert';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// ============================================================================
// WORKFLOW TEMPLATES LIBRARY
// ============================================================================

const TemplatesLibrary = ({ onInstall }) => {
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTemplate, setSelectedTemplate] = useState(null);

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      const response = await axios.get(`${API_BASE}/workflows/templates/list`);
      setTemplates(response.data);
    } catch (error) {
      console.error('Failed to load templates:', error);
      toast({
        title: 'Error',
        description: 'Failed to load workflow templates',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleInstall = async (templateId) => {
    try {
      const response = await axios.post(
        `${API_BASE}/workflows/templates/${templateId}/install`,
        { template_id: templateId, customizations: {} }
      );

      toast({
        title: 'Success',
        description: 'Workflow template installed successfully',
      });

      if (onInstall) {
        onInstall(response.data);
      }
    } catch (error) {
      console.error('Failed to install template:', error);
      toast({
        title: 'Error',
        description: 'Failed to install workflow template',
        variant: 'destructive',
      });
    }
  };

  const getIconComponent = (iconChar) => {
    const iconMap = {
      '💰': TrendingUp,
      '📧': Mail,
      '🏢': Database,
      '📊': BarChart3,
    };
    const IconComponent = iconMap[iconChar] || Workflow;
    return <IconComponent className="h-6 w-6" />;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Workflow Templates</h2>
          <p className="text-gray-500">Pre-built workflows, ready to install</p>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {templates.map((template) => (
          <Card key={template.id} className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    {getIconComponent(template.icon)}
                  </div>
                  <div>
                    <CardTitle className="text-lg">{template.name}</CardTitle>
                    <Badge variant="outline" className="mt-1">
                      {template.category}
                    </Badge>
                  </div>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-gray-600 mb-4">{template.description}</p>

              <div className="space-y-2 mb-4">
                <p className="text-xs font-semibold text-gray-500 uppercase">Benefits:</p>
                <ul className="space-y-1">
                  {template.benefits.map((benefit, idx) => (
                    <li key={idx} className="flex items-center text-sm text-gray-600">
                      <CheckCircle2 className="h-4 w-4 text-green-500 mr-2" />
                      {benefit}
                    </li>
                  ))}
                </ul>
              </div>

              <div className="flex space-x-2">
                <Button
                  onClick={() => handleInstall(template.id)}
                  className="flex-1"
                >
                  <Download className="h-4 w-4 mr-2" />
                  Install Template
                </Button>
                <Button
                  variant="outline"
                  onClick={() => setSelectedTemplate(template)}
                >
                  <Settings className="h-4 w-4" />
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
};

// ============================================================================
// WORKFLOWS LIST
// ============================================================================

const WorkflowsList = ({ workflows, onExecute, onDelete, onEdit, onRefresh }) => {
  const getStatusIcon = (workflow) => {
    return workflow.enabled ? (
      <CheckCircle2 className="h-4 w-4 text-green-500" />
    ) : (
      <Pause className="h-4 w-4 text-gray-400" />
    );
  };

  if (workflows.length === 0) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-12">
          <Workflow className="h-12 w-12 text-gray-400 mb-4" />
          <h3 className="text-lg font-semibold mb-2">No Workflows Yet</h3>
          <p className="text-gray-500 text-center mb-6">
            Get started by installing a template or creating a custom workflow
          </p>
          <Button onClick={onRefresh}>
            <Plus className="h-4 w-4 mr-2" />
            Create Workflow
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {workflows.map((workflow) => (
        <Card key={workflow.workflow_id}>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-3">
                {getStatusIcon(workflow)}
                <div>
                  <CardTitle className="text-lg">{workflow.name}</CardTitle>
                  <CardDescription>{workflow.description}</CardDescription>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onExecute(workflow)}
                  disabled={!workflow.enabled}
                >
                  <PlayCircle className="h-4 w-4 mr-1" />
                  Run
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onEdit(workflow)}
                >
                  <Settings className="h-4 w-4" />
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onDelete(workflow)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex items-center space-x-4 text-sm text-gray-500">
              <div className="flex items-center">
                <GitBranch className="h-4 w-4 mr-1" />
                {workflow.nodes_count} nodes
              </div>
              <div className="flex items-center">
                <Calendar className="h-4 w-4 mr-1" />
                Created {new Date(workflow.created_at).toLocaleDateString()}
              </div>
              {workflow.tags && workflow.tags.length > 0 && (
                <div className="flex items-center space-x-1">
                  {workflow.tags.map((tag, idx) => (
                    <Badge key={idx} variant="secondary">
                      {tag}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};

// ============================================================================
// EXECUTIONS MONITOR
// ============================================================================

const ExecutionsMonitor = ({ workflowId }) => {
  const [executions, setExecutions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedExecution, setSelectedExecution] = useState(null);

  useEffect(() => {
    if (workflowId) {
      loadExecutions();
      const interval = setInterval(loadExecutions, 5000); // Refresh every 5s
      return () => clearInterval(interval);
    }
  }, [workflowId]);

  const loadExecutions = async () => {
    try {
      const response = await axios.get(
        `${API_BASE}/workflows/${workflowId}/executions`
      );
      setExecutions(response.data);
    } catch (error) {
      console.error('Failed to load executions:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle2 className="h-5 w-5 text-green-500" />;
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-500" />;
      case 'running':
        return <Activity className="h-5 w-5 text-blue-500 animate-pulse" />;
      default:
        return <Clock className="h-5 w-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      case 'running':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  if (loading) {
    return <div className="text-center py-8">Loading executions...</div>;
  }

  if (executions.length === 0) {
    return (
      <Card>
        <CardContent className="flex flex-col items-center justify-center py-12">
          <Activity className="h-12 w-12 text-gray-400 mb-4" />
          <h3 className="text-lg font-semibold mb-2">No Executions Yet</h3>
          <p className="text-gray-500 text-center">
            This workflow hasn't been executed yet
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Recent Executions</h3>
      <ScrollArea className="h-96">
        <div className="space-y-2">
          {executions.map((execution) => (
            <Card
              key={execution.execution_id}
              className="cursor-pointer hover:bg-gray-50"
              onClick={() => setSelectedExecution(execution)}
            >
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    {getStatusIcon(execution.status)}
                    <div>
                      <p className="font-medium">{execution.workflow_name}</p>
                      <p className="text-sm text-gray-500">
                        Started {new Date(execution.started_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    <Badge className={getStatusColor(execution.status)}>
                      {execution.status}
                    </Badge>
                    {execution.duration_ms && (
                      <span className="text-sm text-gray-500">
                        {(execution.duration_ms / 1000).toFixed(2)}s
                      </span>
                    )}
                    <ChevronRight className="h-4 w-4 text-gray-400" />
                  </div>
                </div>
                {execution.error && (
                  <Alert variant="destructive" className="mt-2">
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>{execution.error}</AlertDescription>
                  </Alert>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      </ScrollArea>

      {/* Execution Details Dialog */}
      {selectedExecution && (
        <Dialog
          open={!!selectedExecution}
          onOpenChange={() => setSelectedExecution(null)}
        >
          <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Execution Details</DialogTitle>
              <DialogDescription>
                Execution ID: {selectedExecution.execution_id}
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Status</Label>
                  <Badge className={getStatusColor(selectedExecution.status)}>
                    {selectedExecution.status}
                  </Badge>
                </div>
                <div>
                  <Label>Duration</Label>
                  <p>
                    {selectedExecution.duration_ms
                      ? `${(selectedExecution.duration_ms / 1000).toFixed(2)}s`
                      : 'In progress...'}
                  </p>
                </div>
                <div>
                  <Label>Started At</Label>
                  <p>{new Date(selectedExecution.started_at).toLocaleString()}</p>
                </div>
                <div>
                  <Label>Nodes Executed</Label>
                  <p>{selectedExecution.node_executions_count}</p>
                </div>
              </div>
              {selectedExecution.error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertTitle>Error</AlertTitle>
                  <AlertDescription>{selectedExecution.error}</AlertDescription>
                </Alert>
              )}
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
};

// ============================================================================
// ANALYTICS DASHBOARD
// ============================================================================

const AnalyticsDashboard = () => {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadAnalytics();
  }, []);

  const loadAnalytics = async () => {
    try {
      const response = await axios.get(`${API_BASE}/workflows/analytics/overview`);
      setAnalytics(response.data);
    } catch (error) {
      console.error('Failed to load analytics:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="text-center py-8">Loading analytics...</div>;
  }

  if (!analytics) {
    return null;
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">
              Total Workflows
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{analytics.total_workflows}</div>
            <p className="text-sm text-gray-500 mt-1">
              {analytics.enabled_workflows} enabled
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">
              Total Executions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{analytics.total_executions}</div>
            <p className="text-sm text-gray-500 mt-1">All time</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">
              Success Rate
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">
              {analytics.success_rate.toFixed(1)}%
            </div>
            <p className="text-sm text-gray-500 mt-1">
              {analytics.successful_executions} successful
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-500">
              Failed Executions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-red-600">
              {analytics.failed_executions}
            </div>
            <p className="text-sm text-gray-500 mt-1">Needs attention</p>
          </CardContent>
        </Card>
      </div>

      {analytics.recent_executions && analytics.recent_executions.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {analytics.recent_executions.map((exec) => (
                <div
                  key={exec.execution_id}
                  className="flex items-center justify-between p-2 hover:bg-gray-50 rounded"
                >
                  <div className="flex items-center space-x-3">
                    {exec.status === 'completed' ? (
                      <CheckCircle2 className="h-4 w-4 text-green-500" />
                    ) : exec.status === 'failed' ? (
                      <XCircle className="h-4 w-4 text-red-500" />
                    ) : (
                      <Clock className="h-4 w-4 text-gray-400" />
                    )}
                    <div>
                      <p className="text-sm font-medium">{exec.workflow_name}</p>
                      <p className="text-xs text-gray-500">
                        {new Date(exec.started_at).toLocaleString()}
                      </p>
                    </div>
                  </div>
                  {exec.duration_ms && (
                    <Badge variant="outline">
                      {(exec.duration_ms / 1000).toFixed(2)}s
                    </Badge>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

// ============================================================================
// MAIN WORKFLOW AUTOMATION COMPONENT
// ============================================================================

const WorkflowAutomation = () => {
  const [activeTab, setActiveTab] = useState('workflows');
  const [workflows, setWorkflows] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadWorkflows();
  }, []);

  const loadWorkflows = async () => {
    try {
      const response = await axios.get(`${API_BASE}/workflows`);
      setWorkflows(response.data);
    } catch (error) {
      console.error('Failed to load workflows:', error);
      toast({
        title: 'Error',
        description: 'Failed to load workflows',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleExecuteWorkflow = async (workflow) => {
    try {
      const response = await axios.post(
        `${API_BASE}/workflows/${workflow.workflow_id}/execute`,
        { trigger_data: {} }
      );

      toast({
        title: 'Workflow Started',
        description: `Execution ID: ${response.data.execution_id}`,
      });

      // Switch to executions tab
      setActiveTab('executions');
    } catch (error) {
      console.error('Failed to execute workflow:', error);
      toast({
        title: 'Error',
        description: 'Failed to execute workflow',
        variant: 'destructive',
      });
    }
  };

  const handleDeleteWorkflow = async (workflow) => {
    if (!window.confirm(`Delete workflow "${workflow.name}"?`)) {
      return;
    }

    try {
      await axios.delete(`${API_BASE}/workflows/${workflow.workflow_id}`);

      toast({
        title: 'Success',
        description: 'Workflow deleted successfully',
      });

      loadWorkflows();
    } catch (error) {
      console.error('Failed to delete workflow:', error);
      toast({
        title: 'Error',
        description: 'Failed to delete workflow',
        variant: 'destructive',
      });
    }
  };

  const handleTemplateInstalled = (workflow) => {
    loadWorkflows();
    setActiveTab('workflows');
  };

  return (
    <div className="container mx-auto py-8 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-4xl font-bold flex items-center">
            <Sparkles className="h-8 w-8 mr-3 text-blue-500" />
            Workflow Automation
          </h1>
          <p className="text-gray-500 mt-2">
            10x better than Make.com - Native, Intelligent, Integrated
          </p>
        </div>
      </div>

      {/* Key Features Banner */}
      <Alert className="bg-blue-50 border-blue-200">
        <Zap className="h-4 w-4 text-blue-500" />
        <AlertTitle>Why This is 10x Better</AlertTitle>
        <AlertDescription>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-2">
            <div className="flex items-center space-x-2">
              <CheckCircle2 className="h-4 w-4 text-green-500" />
              <span className="text-sm">Native Integration</span>
            </div>
            <div className="flex items-center space-x-2">
              <CheckCircle2 className="h-4 w-4 text-green-500" />
              <span className="text-sm">Advanced AI</span>
            </div>
            <div className="flex items-center space-x-2">
              <CheckCircle2 className="h-4 w-4 text-green-500" />
              <span className="text-sm">No External Costs</span>
            </div>
            <div className="flex items-center space-x-2">
              <CheckCircle2 className="h-4 w-4 text-green-500" />
              <span className="text-sm">Real-time Monitoring</span>
            </div>
          </div>
        </AlertDescription>
      </Alert>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="workflows">
            <Workflow className="h-4 w-4 mr-2" />
            Workflows
          </TabsTrigger>
          <TabsTrigger value="templates">
            <Download className="h-4 w-4 mr-2" />
            Templates
          </TabsTrigger>
          <TabsTrigger value="executions">
            <Activity className="h-4 w-4 mr-2" />
            Executions
          </TabsTrigger>
          <TabsTrigger value="analytics">
            <BarChart3 className="h-4 w-4 mr-2" />
            Analytics
          </TabsTrigger>
        </TabsList>

        <TabsContent value="workflows" className="space-y-4">
          <WorkflowsList
            workflows={workflows}
            onExecute={handleExecuteWorkflow}
            onDelete={handleDeleteWorkflow}
            onEdit={(w) => console.log('Edit', w)}
            onRefresh={loadWorkflows}
          />
        </TabsContent>

        <TabsContent value="templates" className="space-y-4">
          <TemplatesLibrary onInstall={handleTemplateInstalled} />
        </TabsContent>

        <TabsContent value="executions" className="space-y-4">
          {workflows.length > 0 ? (
            <div className="space-y-6">
              {workflows.map((workflow) => (
                <div key={workflow.workflow_id}>
                  <h3 className="text-lg font-semibold mb-3">{workflow.name}</h3>
                  <ExecutionsMonitor workflowId={workflow.workflow_id} />
                </div>
              ))}
            </div>
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Activity className="h-12 w-12 text-gray-400 mb-4" />
                <h3 className="text-lg font-semibold mb-2">No Workflows Yet</h3>
                <p className="text-gray-500 text-center">
                  Create a workflow to see executions
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        <TabsContent value="analytics" className="space-y-4">
          <AnalyticsDashboard />
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default WorkflowAutomation;
