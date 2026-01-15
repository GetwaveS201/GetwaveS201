import { useState, useEffect, createContext, useContext, useCallback } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation, useParams } from "react-router-dom";
import axios from "axios";
import { Toaster, toast } from "sonner";
import {
  LayoutDashboard, Briefcase, Users, FileText, ClipboardList,
  DollarSign, BarChart3, MessageSquare, LogOut, Menu, X,
  Plus, Search, ChevronRight, TrendingUp, TrendingDown,
  Clock, CheckCircle2, AlertCircle, Download, Send, Brain,
  Camera, Trash2, Edit, ArrowLeft, MapPin, Phone, Mail,
  Calendar, Tag, User, Image, FileImage, Receipt, PlusCircle,
  ChevronDown, Eye, Printer, Shield, Building, Droplets, Flame,
  Bug, CloudRain, AlertTriangle, Wrench, FileCheck, PhoneCall,
  History, CreditCard, Banknote
} from "lucide-react";
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "./components/ui/card";
import { Badge } from "./components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from "./components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./components/ui/select";
import { Label } from "./components/ui/label";
import { Textarea } from "./components/ui/textarea";
import { ScrollArea } from "./components/ui/scroll-area";
import { Progress } from "./components/ui/progress";
import { Separator } from "./components/ui/separator";
import { Avatar, AvatarFallback } from "./components/ui/avatar";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "./components/ui/accordion";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext(null);
const useAuth = () => useContext(AuthContext);

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [token, setToken] = useState(localStorage.getItem("token"));
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (token) {
      axios.defaults.headers.common["Authorization"] = `Bearer ${token}`;
      axios.get(`${API}/auth/me`)
        .then(res => setUser(res.data))
        .catch(() => { localStorage.removeItem("token"); setToken(null); })
        .finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  }, [token]);

  const login = async (email, password) => {
    const res = await axios.post(`${API}/auth/login`, { email, password });
    localStorage.setItem("token", res.data.access_token);
    axios.defaults.headers.common["Authorization"] = `Bearer ${res.data.access_token}`;
    setToken(res.data.access_token);
    setUser(res.data.user);
    return res.data;
  };

  const register = async (email, password, name) => {
    const res = await axios.post(`${API}/auth/register`, { email, password, name });
    localStorage.setItem("token", res.data.access_token);
    axios.defaults.headers.common["Authorization"] = `Bearer ${res.data.access_token}`;
    setToken(res.data.access_token);
    setUser(res.data.user);
    return res.data;
  };

  const logout = () => {
    localStorage.removeItem("token");
    delete axios.defaults.headers.common["Authorization"];
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

const ProtectedRoute = ({ children }) => {
  const { token, loading } = useAuth();
  if (loading) return <div className="flex items-center justify-center h-screen"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900"></div></div>;
  if (!token) return <Navigate to="/login" />;
  return children;
};

// Sidebar Component
const Sidebar = ({ isOpen, setIsOpen }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout, user } = useAuth();

  const navItems = [
    { path: "/", icon: LayoutDashboard, label: "Dashboard" },
    { path: "/jobs", icon: Briefcase, label: "Jobs" },
    { path: "/crews", icon: Users, label: "Crews" },
    { path: "/daily-logs", icon: ClipboardList, label: "Daily Logs" },
    { path: "/invoices", icon: FileText, label: "Invoices" },
    { path: "/collections", icon: Banknote, label: "Collections" },
    { path: "/adjuster-followups", icon: Send, label: "Adjuster Follow-Ups" },
    { path: "/accounting", icon: DollarSign, label: "Expenses" },
    { path: "/reports", icon: BarChart3, label: "Reports" },
    { path: "/ai-assistant", icon: MessageSquare, label: "AI Assistant" },
  ];

  return (
    <>
      <div className={`fixed inset-y-0 left-0 z-50 w-64 sidebar transform transition-transform duration-300 lg:translate-x-0 ${isOpen ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="flex flex-col h-full">
          <div className="flex items-center gap-3 px-6 py-5 border-b border-white/10">
            <div className="w-10 h-10 rounded-lg bg-orange-500 flex items-center justify-center">
              <Briefcase className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-white text-lg tracking-tight">RestorationOS</h1>
              <p className="text-xs text-slate-400">Operations Hub</p>
            </div>
          </div>
          <nav className="flex-1 p-4 space-y-1">
            {navItems.map(item => (
              <button
                key={item.path}
                onClick={() => { navigate(item.path); setIsOpen(false); }}
                className={`sidebar-link w-full text-left ${location.pathname === item.path || (item.path === '/jobs' && location.pathname.startsWith('/jobs/')) ? 'active' : ''}`}
                data-testid={`nav-${item.label.toLowerCase().replace(' ', '-')}`}
              >
                <item.icon className="w-5 h-5" />
                <span>{item.label}</span>
              </button>
            ))}
          </nav>
          <div className="p-4 border-t border-white/10">
            <div className="flex items-center gap-3 px-4 py-3">
              <div className="w-8 h-8 rounded-full bg-orange-500 flex items-center justify-center text-white font-semibold text-sm">
                {user?.name?.charAt(0).toUpperCase()}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-white truncate">{user?.name}</p>
                <p className="text-xs text-slate-400 truncate">{user?.email}</p>
              </div>
              <button onClick={logout} className="p-2 text-slate-400 hover:text-white transition-colors" data-testid="logout-btn">
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
      {isOpen && <div className="fixed inset-0 bg-black/50 z-40 lg:hidden" onClick={() => setIsOpen(false)} />}
    </>
  );
};

const Layout = ({ children }) => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar isOpen={sidebarOpen} setIsOpen={setSidebarOpen} />
      <div className="lg:pl-64">
        <header className="sticky top-0 z-30 bg-white border-b border-slate-200 px-4 py-3 lg:px-8">
          <div className="flex items-center gap-4">
            <button className="lg:hidden p-2 rounded-md hover:bg-slate-100" onClick={() => setSidebarOpen(true)} data-testid="mobile-menu-btn">
              <Menu className="w-5 h-5" />
            </button>
            <div className="flex-1 max-w-md relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <Input placeholder="Search jobs, invoices, crews..." className="pl-10 bg-slate-50 border-slate-200" data-testid="global-search" />
            </div>
          </div>
        </header>
        <main className="p-4 lg:p-8">{children}</main>
      </div>
    </div>
  );
};

// Login Page
const LoginPage = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isRegister, setIsRegister] = useState(false);
  const [name, setName] = useState("");
  const [loading, setLoading] = useState(false);
  const { login, register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      if (isRegister) await register(email, password, name);
      else await login(email, password);
      toast.success(isRegister ? "Account created!" : "Welcome back!");
      navigate("/");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Authentication failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-xl bg-orange-500 flex items-center justify-center mx-auto mb-4">
            <Briefcase className="w-8 h-8 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-white mb-2">RestorationOS</h1>
          <p className="text-slate-400">AI-Powered Operations Assistant</p>
        </div>
        <Card className="border-slate-800 bg-slate-800/50 backdrop-blur">
          <CardHeader>
            <CardTitle className="text-white">{isRegister ? "Create Account" : "Sign In"}</CardTitle>
            <CardDescription className="text-slate-400">{isRegister ? "Get started with RestorationOS" : "Welcome back to your dashboard"}</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {isRegister && (
                <div>
                  <Label className="text-slate-300">Full Name</Label>
                  <Input value={name} onChange={e => setName(e.target.value)} placeholder="John Smith" className="bg-slate-700 border-slate-600 text-white" data-testid="register-name" required />
                </div>
              )}
              <div>
                <Label className="text-slate-300">Email</Label>
                <Input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@company.com" className="bg-slate-700 border-slate-600 text-white" data-testid="login-email" required />
              </div>
              <div>
                <Label className="text-slate-300">Password</Label>
                <Input type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" className="bg-slate-700 border-slate-600 text-white" data-testid="login-password" required />
              </div>
              <Button type="submit" className="w-full btn-accent" disabled={loading} data-testid="auth-submit-btn">
                {loading ? "Please wait..." : (isRegister ? "Create Account" : "Sign In")}
              </Button>
            </form>
            <div className="mt-4 text-center">
              <button onClick={() => setIsRegister(!isRegister)} className="text-sm text-orange-400 hover:text-orange-300" data-testid="toggle-auth-mode">
                {isRegister ? "Already have an account? Sign in" : "Need an account? Register"}
              </button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

// Dashboard Page
const DashboardPage = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    axios.get(`${API}/reports/dashboard`)
      .then(res => setStats(res.data))
      .catch(() => toast.error("Failed to load dashboard"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900"></div></div>;

  const TrendBadge = ({ value, suffix = "%" }) => {
    if (value === 0 || value === null || value === undefined) return null;
    const isPositive = value > 0;
    return (
      <span className={`inline-flex items-center text-xs font-medium ${isPositive ? 'text-green-600' : 'text-red-600'}`}>
        {isPositive ? <TrendingUp className="w-3 h-3 mr-0.5" /> : <TrendingDown className="w-3 h-3 mr-0.5" />}
        {isPositive ? '+' : ''}{value.toFixed(1)}{suffix}
      </span>
    );
  };

  const LOSS_TYPE_ICONS = {
    water: { icon: Droplets, color: 'text-blue-500', bg: 'bg-blue-100' },
    fire: { icon: Flame, color: 'text-red-500', bg: 'bg-red-100' },
    mold: { icon: Bug, color: 'text-green-500', bg: 'bg-green-100' },
    storm: { icon: CloudRain, color: 'text-purple-500', bg: 'bg-purple-100' },
    other: { icon: Wrench, color: 'text-slate-500', bg: 'bg-slate-100' }
  };

  return (
    <div className="space-y-6 animate-fade-in" data-testid="dashboard">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Dashboard</h1>
          <p className="text-slate-500 mt-1">Welcome back! Here's your operations overview.</p>
        </div>
        <Button className="btn-accent gap-2" onClick={() => navigate('/jobs')} data-testid="new-job-btn">
          <Plus className="w-4 h-4" /> New Job
        </Button>
      </div>

      {/* Primary Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="metric-card card-hover" data-testid="metric-active-jobs">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-slate-500">Active Jobs</p>
              <p className="text-2xl font-bold text-slate-900 mt-1">{stats?.active_jobs || 0}</p>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-xs text-slate-500">{stats?.jobs_this_week || 0} new this week</span>
                <TrendBadge value={stats?.jobs_change_percent} />
              </div>
            </div>
            <div className="p-2 rounded-lg bg-blue-50">
              <Briefcase className="w-5 h-5 text-blue-600" />
            </div>
          </div>
        </Card>

        <Card className="metric-card card-hover" data-testid="metric-revenue">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-slate-500">Revenue</p>
              <p className="text-2xl font-bold text-slate-900 mt-1">${(stats?.total_revenue || 0).toLocaleString()}</p>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-xs text-slate-500">${(stats?.this_week_revenue || 0).toLocaleString()} this week</span>
                <TrendBadge value={stats?.revenue_change_percent} />
              </div>
            </div>
            <div className="p-2 rounded-lg bg-emerald-50">
              <TrendingUp className="w-5 h-5 text-emerald-600" />
            </div>
          </div>
        </Card>

        <Card className="metric-card card-hover" data-testid="metric-outstanding">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-slate-500">Outstanding</p>
              <p className="text-2xl font-bold text-slate-900 mt-1">${(stats?.outstanding_invoices || 0).toLocaleString()}</p>
              <div className="flex items-center gap-2 mt-1">
                {stats?.overdue_invoices_count > 0 ? (
                  <span className="text-xs text-red-600 font-medium">{stats.overdue_invoices_count} overdue (${(stats.overdue_invoices_total || 0).toLocaleString()})</span>
                ) : (
                  <span className="text-xs text-green-600">No overdue invoices</span>
                )}
              </div>
            </div>
            <div className="p-2 rounded-lg bg-orange-50">
              <Clock className="w-5 h-5 text-orange-600" />
            </div>
          </div>
        </Card>

        <Card className="metric-card card-hover" data-testid="metric-crews">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-slate-500">Crew Utilization</p>
              <p className="text-2xl font-bold text-slate-900 mt-1">{stats?.crew_utilization || 0}%</p>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-xs text-slate-500">{stats?.busy_crews || 0} of {stats?.total_crews || 0} crews active</span>
              </div>
            </div>
            <div className="p-2 rounded-lg bg-green-50">
              <Users className="w-5 h-5 text-green-600" />
            </div>
          </div>
        </Card>
      </div>

      {/* Secondary Metrics Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-4">
        <Card className="p-4">
          <p className="text-xs text-slate-500 uppercase tracking-wide">Avg Job Value</p>
          <p className="text-xl font-bold text-slate-900 mt-1">${(stats?.avg_job_value || 0).toLocaleString()}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs text-slate-500 uppercase tracking-wide">Avg Days to Complete</p>
          <p className="text-xl font-bold text-slate-900 mt-1">{stats?.avg_days_to_complete || 0} days</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs text-slate-500 uppercase tracking-wide">Profit Margin</p>
          <p className={`text-xl font-bold mt-1 ${stats?.profit_margin >= 20 ? 'text-green-600' : stats?.profit_margin >= 10 ? 'text-yellow-600' : 'text-red-600'}`}>
            {stats?.profit_margin || 0}%
          </p>
        </Card>
        <Card className="p-4">
          <p className="text-xs text-slate-500 uppercase tracking-wide">Labor Hours</p>
          <div className="flex items-center gap-2 mt-1">
            <p className="text-xl font-bold text-slate-900">{stats?.labor_hours_this_week || 0}</p>
            <TrendBadge value={stats?.labor_hours_change_percent} />
          </div>
        </Card>
        <Card className="p-4">
          <p className="text-xs text-slate-500 uppercase tracking-wide">Completed This Week</p>
          <p className="text-xl font-bold text-green-600 mt-1">{stats?.completed_this_week || 0}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs text-slate-500 uppercase tracking-wide">Insurance Jobs</p>
          <p className="text-xl font-bold text-slate-900 mt-1">{stats?.jobs_with_insurance || 0}</p>
        </Card>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Jobs by Phase */}
        <Card>
          <CardHeader>
            <CardTitle className="section-title">Jobs by Phase</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {[
              { key: 'intake', label: 'Intake', color: 'bg-slate-500' },
              { key: 'emergency_services', label: 'Emergency', color: 'bg-red-500' },
              { key: 'drying_remediation', label: 'Drying/Remediation', color: 'bg-blue-500' },
              { key: 'repairs_rebuild', label: 'Repairs/Rebuild', color: 'bg-orange-500' },
              { key: 'closeout', label: 'Closeout', color: 'bg-green-500' }
            ].map(phase => {
              const count = stats?.jobs_by_phase?.[phase.key] || 0;
              const total = stats?.active_jobs || 1;
              const percent = Math.round((count / total) * 100) || 0;
              return (
                <div key={phase.key}>
                  <div className="flex items-center justify-between text-sm mb-1">
                    <span className="text-slate-600">{phase.label}</span>
                    <span className="font-semibold">{count}</span>
                  </div>
                  <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                    <div className={`h-full ${phase.color} rounded-full transition-all`} style={{ width: `${percent}%` }} />
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>

        {/* Loss Type Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle className="section-title">Jobs by Loss Type</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {Object.entries(stats?.loss_type_counts || {}).map(([type, count]) => {
              const config = LOSS_TYPE_ICONS[type] || LOSS_TYPE_ICONS.other;
              const Icon = config.icon;
              return (
                <div key={type} className="flex items-center justify-between p-2 rounded-lg bg-slate-50">
                  <div className="flex items-center gap-2">
                    <div className={`w-8 h-8 rounded-lg ${config.bg} flex items-center justify-center`}>
                      <Icon className={`w-4 h-4 ${config.color}`} />
                    </div>
                    <span className="capitalize">{type.replace('_', ' ')}</span>
                  </div>
                  <Badge variant="outline">{count}</Badge>
                </div>
              );
            })}
            {Object.keys(stats?.loss_type_counts || {}).length === 0 && (
              <p className="text-slate-500 text-center py-4">No jobs yet</p>
            )}
          </CardContent>
        </Card>

        {/* Quick Stats */}
        <Card>
          <CardHeader>
            <CardTitle className="section-title">Financial Summary</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-slate-600">Total Revenue</span>
              <span className="font-semibold text-green-600">${(stats?.total_revenue || 0).toLocaleString()}</span>
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <span className="text-slate-600">Total Expenses</span>
              <span className="font-semibold text-red-600">${(stats?.total_expenses || 0).toLocaleString()}</span>
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <span className="text-slate-600">Gross Profit</span>
              <span className={`font-semibold ${stats?.gross_profit >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                ${(stats?.gross_profit || 0).toLocaleString()}
              </span>
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <span className="text-slate-600">Insurance Approved</span>
              <span className="font-semibold">${(stats?.insurance_approved_total || 0).toLocaleString()}</span>
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <span className="text-slate-600">Depreciation Held</span>
              <span className="font-semibold text-orange-600">${(stats?.depreciation_withheld_total || 0).toLocaleString()}</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Alerts and Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Alerts */}
        <Card className={stats?.overdue_invoices_count > 0 || stats?.jobs_over_budget_count > 0 ? 'border-red-200' : ''}>
          <CardHeader>
            <CardTitle className="section-title flex items-center gap-2">
              <AlertCircle className={`w-5 h-5 ${stats?.overdue_invoices_count > 0 ? 'text-red-500' : 'text-slate-400'}`} />
              Alerts & Action Items
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {stats?.overdue_invoices?.length > 0 && (
              <div className="p-3 bg-red-50 rounded-lg border border-red-100">
                <p className="font-semibold text-red-700 mb-2">Overdue Invoices ({stats.overdue_invoices_count})</p>
                {stats.overdue_invoices.map((inv, i) => (
                  <div key={i} className="flex items-center justify-between text-sm py-1">
                    <span>{inv.customer_name}</span>
                    <div className="flex items-center gap-2">
                      <span className="font-semibold">${inv.total.toLocaleString()}</span>
                      <Badge className="bg-red-100 text-red-700">{inv.days_overdue}d overdue</Badge>
                    </div>
                  </div>
                ))}
              </div>
            )}
            {stats?.jobs_over_budget?.length > 0 && (
              <div className="p-3 bg-orange-50 rounded-lg border border-orange-100">
                <p className="font-semibold text-orange-700 mb-2">Jobs Over Budget ({stats.jobs_over_budget_count})</p>
                {stats.jobs_over_budget.map((job, i) => (
                  <div key={i} className="flex items-center justify-between text-sm py-1">
                    <span>{job.title}</span>
                    <Badge className="bg-orange-100 text-orange-700">+${job.variance.toLocaleString()}</Badge>
                  </div>
                ))}
              </div>
            )}
            {!stats?.overdue_invoices?.length && !stats?.jobs_over_budget?.length && (
              <div className="text-center py-6">
                <CheckCircle2 className="w-10 h-10 text-green-500 mx-auto mb-2" />
                <p className="text-green-700 font-medium">All clear!</p>
                <p className="text-sm text-slate-500">No urgent action items</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Recent Jobs */}
        <Card>
          <CardHeader>
            <CardTitle className="section-title">Recent Jobs</CardTitle>
          </CardHeader>
          <CardContent>
            {stats?.recent_jobs?.length > 0 ? (
              <div className="space-y-3">
                {stats.recent_jobs.map((job, i) => {
                  const LossIcon = LOSS_TYPE_ICONS[job.loss_type]?.icon || Wrench;
                  const lossConfig = LOSS_TYPE_ICONS[job.loss_type] || LOSS_TYPE_ICONS.other;
                  return (
                    <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-slate-50 hover:bg-slate-100 transition-colors cursor-pointer" onClick={() => navigate(`/jobs/${job.id}`)}>
                      <div className="flex items-center gap-3">
                        <div className={`w-10 h-10 rounded-lg ${lossConfig.bg} flex items-center justify-center`}>
                          <LossIcon className={`w-5 h-5 ${lossConfig.color}`} />
                        </div>
                        <div>
                          <p className="font-medium text-slate-900">{job.title}</p>
                          <p className="text-sm text-slate-500">{job.customer_name}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge className={`status-${job.status}`}>{job.status?.replace('_', ' ')}</Badge>
                        <ChevronRight className="w-4 h-4 text-slate-400" />
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-slate-500 text-center py-8">No jobs yet. Create your first job to get started!</p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

// Jobs List Page
const JobsPage = () => {
  const [jobs, setJobs] = useState([]);
  const [crews, setCrews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    title: "", customer_name: "", customer_phone: "", customer_email: "",
    property_address: "", billing_address: "", scope: "", priority: "medium", 
    status: "pending", current_phase: "intake", loss_type: "water", loss_date: "",
    assigned_crew_id: "", project_manager: "", scheduled_date: "", estimated_completion: "",
    estimated_amount: 0, budget_amount: 0, notes: "",
    insurance_claim: {
      carrier: "", adjuster_name: "", adjuster_phone: "", adjuster_email: "",
      claim_number: "", policy_number: "", deductible: 0, status: "pending",
      date_of_loss: "", approved_amount: 0, depreciation_withheld: 0, notes: ""
    }
  });
  const [showInsurance, setShowInsurance] = useState(false);
  const navigate = useNavigate();

  const LOSS_TYPES = [
    { value: "water", label: "Water Damage", icon: Droplets },
    { value: "fire", label: "Fire Damage", icon: Flame },
    { value: "mold", label: "Mold Remediation", icon: Bug },
    { value: "storm", label: "Storm Damage", icon: CloudRain },
    { value: "sewage", label: "Sewage Backup", icon: AlertTriangle },
    { value: "biohazard", label: "Biohazard", icon: AlertTriangle },
    { value: "vandalism", label: "Vandalism", icon: AlertTriangle },
    { value: "other", label: "Other", icon: Wrench }
  ];

  const JOB_PHASES = [
    { value: "intake", label: "Intake" },
    { value: "emergency_services", label: "Emergency Services" },
    { value: "drying_remediation", label: "Drying/Remediation" },
    { value: "repairs_rebuild", label: "Repairs/Rebuild" },
    { value: "closeout", label: "Closeout" }
  ];

  const loadData = useCallback(async () => {
    try {
      const [jobsRes, crewsRes] = await Promise.all([
        axios.get(`${API}/jobs`),
        axios.get(`${API}/crews`)
      ]);
      setJobs(jobsRes.data);
      setCrews(crewsRes.data);
    } catch (err) {
      toast.error("Failed to load data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        estimated_amount: parseFloat(formData.estimated_amount) || 0,
        budget_amount: parseFloat(formData.budget_amount) || 0,
        insurance_claim: showInsurance ? {
          ...formData.insurance_claim,
          deductible: parseFloat(formData.insurance_claim.deductible) || 0,
          approved_amount: parseFloat(formData.insurance_claim.approved_amount) || 0,
          depreciation_withheld: parseFloat(formData.insurance_claim.depreciation_withheld) || 0
        } : null
      };
      await axios.post(`${API}/jobs`, payload);
      toast.success("Job created!");
      setDialogOpen(false);
      loadData();
      resetForm();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to create job");
    }
  };

  const resetForm = () => {
    setFormData({
      title: "", customer_name: "", customer_phone: "", customer_email: "",
      property_address: "", billing_address: "", scope: "", priority: "medium", 
      status: "pending", current_phase: "intake", loss_type: "water", loss_date: "",
      assigned_crew_id: "", project_manager: "", scheduled_date: "", estimated_completion: "",
      estimated_amount: 0, budget_amount: 0, notes: "",
      insurance_claim: {
        carrier: "", adjuster_name: "", adjuster_phone: "", adjuster_email: "",
        claim_number: "", policy_number: "", deductible: 0, status: "pending",
        date_of_loss: "", approved_amount: 0, depreciation_withheld: 0, notes: ""
      }
    });
    setShowInsurance(false);
  };

  const getLossTypeIcon = (type) => {
    const found = LOSS_TYPES.find(l => l.value === type);
    return found ? found.icon : Wrench;
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900"></div></div>;

  return (
    <div className="space-y-6 animate-fade-in" data-testid="jobs-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Jobs</h1>
          <p className="text-slate-500 mt-1">Manage restoration jobs from intake to closeout</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
          <DialogTrigger asChild>
            <Button className="btn-accent gap-2" data-testid="create-job-btn">
              <Plus className="w-4 h-4" /> New Job
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Create New Job</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Loss Information */}
              <div className="space-y-4">
                <h3 className="font-semibold text-slate-900 flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 text-orange-500" /> Loss Information
                </h3>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label>Loss Type *</Label>
                    <Select value={formData.loss_type} onValueChange={v => setFormData({...formData, loss_type: v})}>
                      <SelectTrigger data-testid="job-loss-type"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        {LOSS_TYPES.map(type => (
                          <SelectItem key={type.value} value={type.value}>{type.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Date of Loss</Label>
                    <Input type="date" value={formData.loss_date} onChange={e => setFormData({...formData, loss_date: e.target.value})} data-testid="job-loss-date" />
                  </div>
                  <div>
                    <Label>Current Phase</Label>
                    <Select value={formData.current_phase} onValueChange={v => setFormData({...formData, current_phase: v})}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        {JOB_PHASES.map(phase => (
                          <SelectItem key={phase.value} value={phase.value}>{phase.label}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>

              <Separator />

              {/* Customer Information */}
              <div className="space-y-4">
                <h3 className="font-semibold text-slate-900 flex items-center gap-2">
                  <User className="w-4 h-4 text-orange-500" /> Customer Information
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Job Title *</Label>
                    <Input value={formData.title} onChange={e => setFormData({...formData, title: e.target.value})} placeholder="Water Damage - Kitchen" required data-testid="job-title-input" />
                  </div>
                  <div>
                    <Label>Customer Name *</Label>
                    <Input value={formData.customer_name} onChange={e => setFormData({...formData, customer_name: e.target.value})} placeholder="John Smith" required data-testid="job-customer-input" />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Phone *</Label>
                    <Input value={formData.customer_phone} onChange={e => setFormData({...formData, customer_phone: e.target.value})} placeholder="(555) 123-4567" required data-testid="job-phone-input" />
                  </div>
                  <div>
                    <Label>Email</Label>
                    <Input type="email" value={formData.customer_email} onChange={e => setFormData({...formData, customer_email: e.target.value})} placeholder="john@email.com" data-testid="job-email-input" />
                  </div>
                </div>
                <div>
                  <Label>Property Address *</Label>
                  <Input value={formData.property_address} onChange={e => setFormData({...formData, property_address: e.target.value})} placeholder="123 Main St, City, ST 12345" required data-testid="job-address-input" />
                </div>
                <div>
                  <Label>Billing Address (if different)</Label>
                  <Input value={formData.billing_address} onChange={e => setFormData({...formData, billing_address: e.target.value})} placeholder="Leave blank if same as property" />
                </div>
              </div>

              <Separator />

              {/* Job Details */}
              <div className="space-y-4">
                <h3 className="font-semibold text-slate-900 flex items-center gap-2">
                  <Briefcase className="w-4 h-4 text-orange-500" /> Job Details
                </h3>
                <div>
                  <Label>Scope of Work *</Label>
                  <Textarea value={formData.scope} onChange={e => setFormData({...formData, scope: e.target.value})} placeholder="Describe the restoration work needed..." rows={3} required data-testid="job-scope-input" />
                </div>
                <div className="grid grid-cols-4 gap-4">
                  <div>
                    <Label>Priority</Label>
                    <Select value={formData.priority} onValueChange={v => setFormData({...formData, priority: v})}>
                      <SelectTrigger data-testid="job-priority-select"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="low">Low</SelectItem>
                        <SelectItem value="medium">Medium</SelectItem>
                        <SelectItem value="high">High</SelectItem>
                        <SelectItem value="urgent">Urgent</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Status</Label>
                    <Select value={formData.status} onValueChange={v => setFormData({...formData, status: v})}>
                      <SelectTrigger data-testid="job-status-select"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="pending">Pending</SelectItem>
                        <SelectItem value="scheduled">Scheduled</SelectItem>
                        <SelectItem value="in_progress">In Progress</SelectItem>
                        <SelectItem value="on_hold">On Hold</SelectItem>
                        <SelectItem value="completed">Completed</SelectItem>
                        <SelectItem value="cancelled">Cancelled</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Assign Crew</Label>
                    <Select value={formData.assigned_crew_id} onValueChange={v => setFormData({...formData, assigned_crew_id: v})}>
                      <SelectTrigger data-testid="job-crew-select"><SelectValue placeholder="Select crew" /></SelectTrigger>
                      <SelectContent>
                        {crews.map(crew => (
                          <SelectItem key={crew.id} value={crew.id}>{crew.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Project Manager</Label>
                    <Input value={formData.project_manager} onChange={e => setFormData({...formData, project_manager: e.target.value})} placeholder="PM Name" />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Scheduled Start</Label>
                    <Input type="date" value={formData.scheduled_date} onChange={e => setFormData({...formData, scheduled_date: e.target.value})} data-testid="job-date-input" />
                  </div>
                  <div>
                    <Label>Est. Completion</Label>
                    <Input type="date" value={formData.estimated_completion} onChange={e => setFormData({...formData, estimated_completion: e.target.value})} />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Estimated Amount ($)</Label>
                    <Input type="number" step="0.01" value={formData.estimated_amount} onChange={e => setFormData({...formData, estimated_amount: e.target.value})} placeholder="0.00" />
                  </div>
                  <div>
                    <Label>Budget Amount ($)</Label>
                    <Input type="number" step="0.01" value={formData.budget_amount} onChange={e => setFormData({...formData, budget_amount: e.target.value})} placeholder="0.00" />
                  </div>
                </div>
              </div>

              <Separator />

              {/* Insurance Information (Collapsible) */}
              <div className="space-y-4">
                <button type="button" onClick={() => setShowInsurance(!showInsurance)} className="flex items-center gap-2 font-semibold text-slate-900">
                  <Shield className="w-4 h-4 text-orange-500" />
                  Insurance Claim Information
                  <ChevronDown className={`w-4 h-4 transition-transform ${showInsurance ? 'rotate-180' : ''}`} />
                </button>
                
                {showInsurance && (
                  <div className="space-y-4 pl-6 border-l-2 border-orange-200">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>Insurance Carrier</Label>
                        <Input value={formData.insurance_claim.carrier} onChange={e => setFormData({...formData, insurance_claim: {...formData.insurance_claim, carrier: e.target.value}})} placeholder="State Farm" data-testid="insurance-carrier" />
                      </div>
                      <div>
                        <Label>Claim Number</Label>
                        <Input value={formData.insurance_claim.claim_number} onChange={e => setFormData({...formData, insurance_claim: {...formData.insurance_claim, claim_number: e.target.value}})} placeholder="CLM-123456" data-testid="insurance-claim-number" />
                      </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>Policy Number</Label>
                        <Input value={formData.insurance_claim.policy_number} onChange={e => setFormData({...formData, insurance_claim: {...formData.insurance_claim, policy_number: e.target.value}})} placeholder="POL-123456" />
                      </div>
                      <div>
                        <Label>Claim Status</Label>
                        <Select value={formData.insurance_claim.status} onValueChange={v => setFormData({...formData, insurance_claim: {...formData.insurance_claim, status: v}})}>
                          <SelectTrigger><SelectValue /></SelectTrigger>
                          <SelectContent>
                            <SelectItem value="pending">Pending</SelectItem>
                            <SelectItem value="submitted">Submitted</SelectItem>
                            <SelectItem value="approved">Approved</SelectItem>
                            <SelectItem value="partial_approved">Partial Approved</SelectItem>
                            <SelectItem value="denied">Denied</SelectItem>
                            <SelectItem value="paid">Paid</SelectItem>
                            <SelectItem value="closed">Closed</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                    <div className="grid grid-cols-3 gap-4">
                      <div>
                        <Label>Adjuster Name</Label>
                        <Input value={formData.insurance_claim.adjuster_name} onChange={e => setFormData({...formData, insurance_claim: {...formData.insurance_claim, adjuster_name: e.target.value}})} placeholder="Jane Doe" />
                      </div>
                      <div>
                        <Label>Adjuster Phone</Label>
                        <Input value={formData.insurance_claim.adjuster_phone} onChange={e => setFormData({...formData, insurance_claim: {...formData.insurance_claim, adjuster_phone: e.target.value}})} placeholder="(555) 987-6543" />
                      </div>
                      <div>
                        <Label>Adjuster Email</Label>
                        <Input type="email" value={formData.insurance_claim.adjuster_email} onChange={e => setFormData({...formData, insurance_claim: {...formData.insurance_claim, adjuster_email: e.target.value}})} placeholder="adjuster@carrier.com" />
                      </div>
                    </div>
                    <div className="grid grid-cols-3 gap-4">
                      <div>
                        <Label>Deductible ($)</Label>
                        <Input type="number" step="0.01" value={formData.insurance_claim.deductible} onChange={e => setFormData({...formData, insurance_claim: {...formData.insurance_claim, deductible: e.target.value}})} placeholder="1000.00" />
                      </div>
                      <div>
                        <Label>Approved Amount ($)</Label>
                        <Input type="number" step="0.01" value={formData.insurance_claim.approved_amount} onChange={e => setFormData({...formData, insurance_claim: {...formData.insurance_claim, approved_amount: e.target.value}})} placeholder="0.00" />
                      </div>
                      <div>
                        <Label>Depreciation Withheld ($)</Label>
                        <Input type="number" step="0.01" value={formData.insurance_claim.depreciation_withheld} onChange={e => setFormData({...formData, insurance_claim: {...formData.insurance_claim, depreciation_withheld: e.target.value}})} placeholder="0.00" />
                      </div>
                    </div>
                  </div>
                )}
              </div>

              <div>
                <Label>Notes</Label>
                <Textarea value={formData.notes} onChange={e => setFormData({...formData, notes: e.target.value})} placeholder="Additional notes..." rows={2} data-testid="job-notes-input" />
              </div>

              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => { setDialogOpen(false); resetForm(); }}>Cancel</Button>
                <Button type="submit" className="btn-accent" data-testid="job-submit-btn">Create Job</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Phase Filter Tabs */}
      <div className="flex gap-2 flex-wrap">
        <Badge variant="outline" className="cursor-pointer hover:bg-slate-100 px-3 py-1">All Jobs ({jobs.length})</Badge>
        {[
          { value: "intake", label: "Intake" },
          { value: "emergency_services", label: "Emergency" },
          { value: "drying_remediation", label: "Drying" },
          { value: "repairs_rebuild", label: "Repairs" },
          { value: "closeout", label: "Closeout" }
        ].map(phase => (
          <Badge key={phase.value} variant="outline" className="cursor-pointer hover:bg-slate-100 px-3 py-1">
            {phase.label} ({jobs.filter(j => j.current_phase === phase.value).length})
          </Badge>
        ))}
      </div>

      {jobs.length === 0 ? (
        <Card className="text-center py-12">
          <Briefcase className="w-12 h-12 text-slate-300 mx-auto mb-4" />
          <p className="text-slate-500">No jobs yet. Create your first job to get started!</p>
        </Card>
      ) : (
        <div className="grid gap-4">
          {jobs.map(job => {
            const LossIcon = getLossTypeIcon(job.loss_type);
            return (
              <Card key={job.id} className="card-hover cursor-pointer" onClick={() => navigate(`/jobs/${job.id}`)} data-testid={`job-card-${job.id}`}>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex gap-4">
                      <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                        job.loss_type === 'water' ? 'bg-blue-100 text-blue-600' :
                        job.loss_type === 'fire' ? 'bg-red-100 text-red-600' :
                        job.loss_type === 'mold' ? 'bg-green-100 text-green-600' :
                        'bg-slate-100 text-slate-600'
                      }`}>
                        <LossIcon className="w-6 h-6" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="font-semibold text-slate-900 truncate">{job.title}</h3>
                          <Badge className={`priority-${job.priority}`}>{job.priority}</Badge>
                          <Badge className={`status-${job.status}`}>{job.status?.replace('_', ' ')}</Badge>
                          <Badge variant="outline" className="capitalize">{job.current_phase?.replace('_', ' ')}</Badge>
                        </div>
                        <div className="flex items-center gap-4 text-sm text-slate-600">
                          <span className="flex items-center gap-1"><User className="w-3 h-3" /> {job.customer_name}</span>
                          <span className="flex items-center gap-1"><Phone className="w-3 h-3" /> {job.customer_phone}</span>
                          {job.insurance_claim?.claim_number && (
                            <span className="flex items-center gap-1"><Shield className="w-3 h-3" /> {job.insurance_claim.carrier}</span>
                          )}
                        </div>
                        <p className="text-sm text-slate-500 mt-1 flex items-center gap-1">
                          <MapPin className="w-3 h-3" /> {job.property_address}
                        </p>
                        {job.loss_date && (
                          <p className="text-xs text-slate-400 mt-1">Loss Date: {job.loss_date}</p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      {(job.total_amount > 0 || job.estimated_amount > 0) && (
                        <div className="text-right">
                          <p className="text-lg font-bold text-slate-900">${(job.total_amount || job.estimated_amount || 0).toLocaleString()}</p>
                          <p className="text-xs text-slate-500">{job.total_amount > 0 ? 'Total Value' : 'Estimated'}</p>
                        </div>
                      )}
                      <ChevronRight className="w-5 h-5 text-slate-400" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
};

// Job Detail Page
const JobDetailPage = () => {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [jobData, setJobData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [crews, setCrews] = useState([]);
  const [activeTab, setActiveTab] = useState("overview");
  
  // Dialogs
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [lineItemDialogOpen, setLineItemDialogOpen] = useState(false);
  const [logDialogOpen, setLogDialogOpen] = useState(false);
  const [photoDialogOpen, setPhotoDialogOpen] = useState(false);
  const [expenseDialogOpen, setExpenseDialogOpen] = useState(false);
  const [invoiceDialogOpen, setInvoiceDialogOpen] = useState(false);
  const [workOrderDialogOpen, setWorkOrderDialogOpen] = useState(false);

  // Form states
  const [editForm, setEditForm] = useState({});
  const [lineItemForm, setLineItemForm] = useState({ description: "", quantity: 1, unit: "each", unit_price: 0, item_type: "labor", is_taxable: true });
  const [logForm, setLogForm] = useState({ entry_type: "note", content: "" });
  const [photoCaption, setPhotoCaption] = useState("");
  const [photoFile, setPhotoFile] = useState(null);
  const [expenseForm, setExpenseForm] = useState({ description: "", amount: 0, category: "materials", vendor: "", date: "", is_taxable: false });
  const [invoiceForm, setInvoiceForm] = useState({ due_date: "", notes: "", tax_rate: 8.25 });
  const [workOrderForm, setWorkOrderForm] = useState({ tasks: [], materials_needed: [], notes: "" });
  const [newTask, setNewTask] = useState("");
  const [newMaterial, setNewMaterial] = useState("");

  const loadJobData = useCallback(async () => {
    try {
      const [detailsRes, crewsRes] = await Promise.all([
        axios.get(`${API}/jobs/${jobId}/details`),
        axios.get(`${API}/crews`)
      ]);
      setJobData(detailsRes.data);
      setCrews(crewsRes.data);
      setEditForm(detailsRes.data.job);
    } catch (err) {
      toast.error("Failed to load job details");
      navigate('/jobs');
    } finally {
      setLoading(false);
    }
  }, [jobId, navigate]);

  useEffect(() => { loadJobData(); }, [loadJobData]);

  const handleUpdateJob = async () => {
    try {
      await axios.put(`${API}/jobs/${jobId}`, editForm);
      toast.success("Job updated!");
      setEditDialogOpen(false);
      loadJobData();
    } catch (err) {
      toast.error("Failed to update job");
    }
  };

  const handleAddLineItem = async () => {
    try {
      await axios.post(`${API}/jobs/${jobId}/line-items`, { ...lineItemForm, quantity: parseFloat(lineItemForm.quantity), unit_price: parseFloat(lineItemForm.unit_price) });
      toast.success("Line item added!");
      setLineItemDialogOpen(false);
      setLineItemForm({ description: "", quantity: 1, unit: "each", unit_price: 0, item_type: "labor", is_taxable: true });
      loadJobData();
    } catch (err) {
      toast.error("Failed to add line item");
    }
  };

  const handleDeleteLineItem = async (index) => {
    if (!window.confirm("Delete this line item?")) return;
    try {
      await axios.delete(`${API}/jobs/${jobId}/line-items/${index}`);
      toast.success("Line item deleted");
      loadJobData();
    } catch (err) {
      toast.error("Failed to delete");
    }
  };

  const handleAddLog = async () => {
    try {
      await axios.post(`${API}/job-logs`, { job_id: jobId, ...logForm });
      toast.success("Log entry added!");
      setLogDialogOpen(false);
      setLogForm({ entry_type: "note", content: "" });
      loadJobData();
    } catch (err) {
      toast.error("Failed to add log");
    }
  };

  const handleUploadPhoto = async () => {
    if (!photoFile) return toast.error("Please select a photo");
    try {
      const reader = new FileReader();
      reader.onload = async () => {
        try {
          await axios.post(`${API}/jobs/${jobId}/photos`, {
            photo_data: reader.result,
            caption: photoCaption
          });
          toast.success("Photo uploaded!");
          setPhotoDialogOpen(false);
          setPhotoFile(null);
          setPhotoCaption("");
          loadJobData();
        } catch (err) {
          toast.error("Failed to upload photo");
        }
      };
      reader.readAsDataURL(photoFile);
    } catch (err) {
      toast.error("Failed to read photo file");
    }
  };

  const handleDeletePhoto = async (photoId) => {
    if (!window.confirm("Delete this photo?")) return;
    try {
      await axios.delete(`${API}/photos/${photoId}`);
      toast.success("Photo deleted");
      loadJobData();
    } catch (err) {
      toast.error("Failed to delete photo");
    }
  };

  const handleAddExpense = async () => {
    try {
      await axios.post(`${API}/jobs/${jobId}/expenses`, { ...expenseForm, amount: parseFloat(expenseForm.amount) });
      toast.success("Expense added!");
      setExpenseDialogOpen(false);
      setExpenseForm({ description: "", amount: 0, category: "materials", vendor: "", date: "", is_taxable: false });
      loadJobData();
    } catch (err) {
      toast.error("Failed to add expense");
    }
  };

  const handleCreateInvoice = async () => {
    try {
      await axios.post(`${API}/invoices`, { job_id: jobId, ...invoiceForm, tax_rate: parseFloat(invoiceForm.tax_rate) });
      toast.success("Invoice created!");
      setInvoiceDialogOpen(false);
      setInvoiceForm({ due_date: "", notes: "", tax_rate: 8.25 });
      loadJobData();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to create invoice");
    }
  };

  const handleCreateWorkOrder = async () => {
    try {
      const payload = {
        job_id: jobId,
        tasks: workOrderForm.tasks.map(t => ({ description: t, is_completed: false })),
        materials_needed: workOrderForm.materials_needed,
        notes: workOrderForm.notes
      };
      await axios.post(`${API}/work-orders`, payload);
      toast.success("Work order created!");
      setWorkOrderDialogOpen(false);
      setWorkOrderForm({ tasks: [], materials_needed: [], notes: "" });
      loadJobData();
    } catch (err) {
      toast.error("Failed to create work order");
    }
  };

  const handleDeleteJob = async () => {
    if (!window.confirm("Are you sure you want to delete this job? This cannot be undone.")) return;
    try {
      await axios.delete(`${API}/jobs/${jobId}`);
      toast.success("Job deleted");
      navigate('/jobs');
    } catch (err) {
      toast.error("Failed to delete job");
    }
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900"></div></div>;
  if (!jobData) return null;

  const { job, crew, invoices, work_orders, expenses, logs, photos, costing } = jobData;

  return (
    <div className="space-y-6 animate-fade-in" data-testid="job-detail-page">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate('/jobs')} data-testid="back-btn">
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div>
            <div className="flex items-center gap-2 mb-1">
              <h1 className="page-title">{job.title}</h1>
              <Badge className={`priority-${job.priority}`}>{job.priority}</Badge>
              <Badge className={`status-${job.status}`}>{job.status?.replace('_', ' ')}</Badge>
            </div>
            <p className="text-slate-500">{job.customer_name} • {job.address}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="outline" className="gap-2" data-testid="edit-job-btn">
                <Edit className="w-4 h-4" /> Edit
              </Button>
            </DialogTrigger>
            <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
              <DialogHeader>
                <DialogTitle>Edit Job</DialogTitle>
              </DialogHeader>
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Job Title</Label>
                    <Input value={editForm.title || ""} onChange={e => setEditForm({...editForm, title: e.target.value})} />
                  </div>
                  <div>
                    <Label>Customer Name</Label>
                    <Input value={editForm.customer_name || ""} onChange={e => setEditForm({...editForm, customer_name: e.target.value})} />
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Phone</Label>
                    <Input value={editForm.customer_phone || ""} onChange={e => setEditForm({...editForm, customer_phone: e.target.value})} />
                  </div>
                  <div>
                    <Label>Email</Label>
                    <Input type="email" value={editForm.customer_email || ""} onChange={e => setEditForm({...editForm, customer_email: e.target.value})} />
                  </div>
                </div>
                <div>
                  <Label>Address</Label>
                  <Input value={editForm.address || ""} onChange={e => setEditForm({...editForm, address: e.target.value})} />
                </div>
                <div>
                  <Label>Scope of Work</Label>
                  <Textarea value={editForm.scope || ""} onChange={e => setEditForm({...editForm, scope: e.target.value})} rows={3} />
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <Label>Priority</Label>
                    <Select value={editForm.priority} onValueChange={v => setEditForm({...editForm, priority: v})}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="low">Low</SelectItem>
                        <SelectItem value="medium">Medium</SelectItem>
                        <SelectItem value="high">High</SelectItem>
                        <SelectItem value="urgent">Urgent</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Status</Label>
                    <Select value={editForm.status} onValueChange={v => setEditForm({...editForm, status: v})}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="pending">Pending</SelectItem>
                        <SelectItem value="scheduled">Scheduled</SelectItem>
                        <SelectItem value="in_progress">In Progress</SelectItem>
                        <SelectItem value="completed">Completed</SelectItem>
                        <SelectItem value="cancelled">Cancelled</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Assign Crew</Label>
                    <Select value={editForm.assigned_crew_id || ""} onValueChange={v => setEditForm({...editForm, assigned_crew_id: v})}>
                      <SelectTrigger><SelectValue placeholder="Select crew" /></SelectTrigger>
                      <SelectContent>
                        {crews.map(c => (
                          <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Scheduled Date</Label>
                    <Input type="date" value={editForm.scheduled_date || ""} onChange={e => setEditForm({...editForm, scheduled_date: e.target.value})} />
                  </div>
                  <div>
                    <Label>Est. Completion</Label>
                    <Input type="date" value={editForm.estimated_completion || ""} onChange={e => setEditForm({...editForm, estimated_completion: e.target.value})} />
                  </div>
                </div>
                <div>
                  <Label>Notes</Label>
                  <Textarea value={editForm.notes || ""} onChange={e => setEditForm({...editForm, notes: e.target.value})} rows={2} />
                </div>
              </div>
              <DialogFooter className="flex justify-between">
                <Button variant="destructive" onClick={handleDeleteJob} data-testid="delete-job-btn">Delete Job</Button>
                <div className="flex gap-2">
                  <Button variant="outline" onClick={() => setEditDialogOpen(false)}>Cancel</Button>
                  <Button className="btn-accent" onClick={handleUpdateJob} data-testid="save-job-btn">Save Changes</Button>
                </div>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Quick Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="metric-card">
          <p className="text-sm text-slate-500">Job Value</p>
          <p className="text-2xl font-bold text-slate-900">${(job.total_amount || 0).toLocaleString()}</p>
        </Card>
        <Card className="metric-card">
          <p className="text-sm text-slate-500">Total Invoiced</p>
          <p className="text-2xl font-bold text-blue-600">${(costing.total_invoiced || 0).toLocaleString()}</p>
        </Card>
        <Card className="metric-card">
          <p className="text-sm text-slate-500">Total Expenses</p>
          <p className="text-2xl font-bold text-red-600">${(costing.total_expenses || 0).toLocaleString()}</p>
        </Card>
        <Card className="metric-card">
          <p className="text-sm text-slate-500">Profit/Loss</p>
          <p className={`text-2xl font-bold ${costing.profit_margin >= 0 ? 'text-green-600' : 'text-red-600'}`}>
            ${(costing.profit_margin || 0).toLocaleString()}
          </p>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="grid grid-cols-6 w-full max-w-2xl">
          <TabsTrigger value="overview" data-testid="tab-overview">Overview</TabsTrigger>
          <TabsTrigger value="line-items" data-testid="tab-line-items">Line Items</TabsTrigger>
          <TabsTrigger value="photos" data-testid="tab-photos">Photos</TabsTrigger>
          <TabsTrigger value="logs" data-testid="tab-logs">Logs</TabsTrigger>
          <TabsTrigger value="financials" data-testid="tab-financials">Financials</TabsTrigger>
          <TabsTrigger value="documents" data-testid="tab-documents">Documents</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Customer Information</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex items-center gap-3">
                  <User className="w-4 h-4 text-slate-400" />
                  <span>{job.customer_name}</span>
                </div>
                <div className="flex items-center gap-3">
                  <Phone className="w-4 h-4 text-slate-400" />
                  <a href={`tel:${job.customer_phone}`} className="text-blue-600 hover:underline">{job.customer_phone}</a>
                </div>
                {job.customer_email && (
                  <div className="flex items-center gap-3">
                    <Mail className="w-4 h-4 text-slate-400" />
                    <a href={`mailto:${job.customer_email}`} className="text-blue-600 hover:underline">{job.customer_email}</a>
                  </div>
                )}
                <div className="flex items-center gap-3">
                  <MapPin className="w-4 h-4 text-slate-400" />
                  <span>{job.address}</span>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Job Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {job.scheduled_date && (
                  <div className="flex items-center gap-3">
                    <Calendar className="w-4 h-4 text-slate-400" />
                    <span>Scheduled: {job.scheduled_date}</span>
                  </div>
                )}
                {job.estimated_completion && (
                  <div className="flex items-center gap-3">
                    <Clock className="w-4 h-4 text-slate-400" />
                    <span>Est. Completion: {job.estimated_completion}</span>
                  </div>
                )}
                {crew && (
                  <div className="flex items-center gap-3">
                    <Users className="w-4 h-4 text-slate-400" />
                    <span>Crew: {crew.name} ({crew.members?.length || 0} members)</span>
                  </div>
                )}
                <div className="pt-2">
                  <Label className="text-slate-500 text-xs">Scope of Work</Label>
                  <p className="mt-1 text-sm">{job.scope}</p>
                </div>
                {job.notes && (
                  <div className="pt-2">
                    <Label className="text-slate-500 text-xs">Notes</Label>
                    <p className="mt-1 text-sm">{job.notes}</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Line Items Tab */}
        <TabsContent value="line-items" className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="section-title">Line Items</h3>
            <Dialog open={lineItemDialogOpen} onOpenChange={setLineItemDialogOpen}>
              <DialogTrigger asChild>
                <Button className="btn-accent gap-2" data-testid="add-line-item-btn">
                  <PlusCircle className="w-4 h-4" /> Add Item
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Add Line Item</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <Label>Description</Label>
                    <Input value={lineItemForm.description} onChange={e => setLineItemForm({...lineItemForm, description: e.target.value})} placeholder="Labor - Water extraction" data-testid="line-item-description" />
                  </div>
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <Label>Quantity</Label>
                      <Input type="number" value={lineItemForm.quantity} onChange={e => setLineItemForm({...lineItemForm, quantity: e.target.value})} data-testid="line-item-qty" />
                    </div>
                    <div>
                      <Label>Unit</Label>
                      <Select value={lineItemForm.unit} onValueChange={v => setLineItemForm({...lineItemForm, unit: v})}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="each">Each</SelectItem>
                          <SelectItem value="hour">Hour</SelectItem>
                          <SelectItem value="sqft">Sq Ft</SelectItem>
                          <SelectItem value="day">Day</SelectItem>
                          <SelectItem value="lf">Linear Ft</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>Unit Price</Label>
                      <Input type="number" step="0.01" value={lineItemForm.unit_price} onChange={e => setLineItemForm({...lineItemForm, unit_price: e.target.value})} data-testid="line-item-price" />
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Type</Label>
                      <Select value={lineItemForm.item_type} onValueChange={v => setLineItemForm({...lineItemForm, item_type: v})}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="labor">Labor</SelectItem>
                          <SelectItem value="equipment">Equipment</SelectItem>
                          <SelectItem value="material">Material</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="flex items-center gap-2 pt-6">
                      <input type="checkbox" id="taxable" checked={lineItemForm.is_taxable} onChange={e => setLineItemForm({...lineItemForm, is_taxable: e.target.checked})} />
                      <Label htmlFor="taxable">Taxable</Label>
                    </div>
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setLineItemDialogOpen(false)}>Cancel</Button>
                  <Button className="btn-accent" onClick={handleAddLineItem} data-testid="save-line-item-btn">Add Item</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>

          <Card>
            <CardContent className="p-0">
              {job.line_items?.length > 0 ? (
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Description</th>
                      <th>Type</th>
                      <th className="text-right">Qty</th>
                      <th className="text-right">Unit Price</th>
                      <th className="text-right">Total</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {job.line_items.map((item, idx) => (
                      <tr key={idx}>
                        <td>{item.description}</td>
                        <td><Badge variant="outline" className="capitalize">{item.item_type}</Badge></td>
                        <td className="text-right">{item.quantity} {item.unit}</td>
                        <td className="text-right">${item.unit_price?.toFixed(2)}</td>
                        <td className="text-right font-semibold">${(item.quantity * item.unit_price).toFixed(2)}</td>
                        <td>
                          <Button variant="ghost" size="icon" onClick={() => handleDeleteLineItem(idx)} className="text-red-500 hover:text-red-700">
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </td>
                      </tr>
                    ))}
                    <tr className="bg-slate-50 font-semibold">
                      <td colSpan={4} className="text-right">Total</td>
                      <td className="text-right">${job.total_amount?.toFixed(2)}</td>
                      <td></td>
                    </tr>
                  </tbody>
                </table>
              ) : (
                <div className="text-center py-8 text-slate-500">
                  <Receipt className="w-8 h-8 mx-auto mb-2 text-slate-300" />
                  <p>No line items yet. Add items to build your estimate.</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Photos Tab */}
        <TabsContent value="photos" className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="section-title">Job Photos ({photos?.length || 0})</h3>
            <Dialog open={photoDialogOpen} onOpenChange={setPhotoDialogOpen}>
              <DialogTrigger asChild>
                <Button className="btn-accent gap-2" data-testid="upload-photo-btn">
                  <Camera className="w-4 h-4" /> Upload Photo
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Upload Photo</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <div className="border-2 border-dashed border-slate-200 rounded-lg p-6 text-center">
                    {photoFile ? (
                      <div className="space-y-2">
                        <img 
                          src={URL.createObjectURL(photoFile)} 
                          alt="Preview" 
                          className="max-h-48 mx-auto rounded-lg object-contain"
                        />
                        <p className="text-sm text-slate-600">{photoFile.name}</p>
                        <Button variant="outline" size="sm" onClick={() => setPhotoFile(null)}>
                          Remove
                        </Button>
                      </div>
                    ) : (
                      <div className="space-y-2">
                        <Camera className="w-10 h-10 mx-auto text-slate-300" />
                        <p className="text-slate-500">Click to select a photo</p>
                        <Input 
                          type="file" 
                          accept="image/*" 
                          onChange={e => setPhotoFile(e.target.files[0])} 
                          className="max-w-xs mx-auto"
                          data-testid="photo-input" 
                        />
                      </div>
                    )}
                  </div>
                  <div>
                    <Label>Caption (optional)</Label>
                    <Input 
                      value={photoCaption} 
                      onChange={e => setPhotoCaption(e.target.value)} 
                      placeholder="e.g., Before photo - kitchen water damage" 
                      data-testid="photo-caption" 
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => { setPhotoDialogOpen(false); setPhotoFile(null); setPhotoCaption(""); }}>Cancel</Button>
                  <Button className="btn-accent" onClick={handleUploadPhoto} disabled={!photoFile} data-testid="save-photo-btn">
                    Upload Photo
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>

          {photos?.length > 0 ? (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {photos.map(photo => (
                <Card key={photo.id} className="overflow-hidden group relative">
                  <div className="aspect-square bg-slate-100 relative">
                    <img src={photo.data} alt={photo.caption || "Job photo"} className="w-full h-full object-cover" />
                    <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                      <Button variant="secondary" size="icon" onClick={() => window.open(photo.data, '_blank')} title="View full size">
                        <Eye className="w-4 h-4" />
                      </Button>
                      <Button variant="destructive" size="icon" onClick={() => handleDeletePhoto(photo.id)} title="Delete photo">
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                  <CardContent className="p-3">
                    <p className="text-sm text-slate-700 truncate">{photo.caption || "No caption"}</p>
                    <p className="text-xs text-slate-400 mt-1">{new Date(photo.created_at).toLocaleDateString()} by {photo.created_by}</p>
                  </CardContent>
                </Card>
              ))}
            </div>
          ) : (
            <Card className="text-center py-12">
              <Image className="w-16 h-16 text-slate-200 mx-auto mb-4" />
              <h3 className="font-semibold text-slate-700 mb-2">No Photos Yet</h3>
              <p className="text-slate-500 mb-4">Upload photos to document the job progress, before/after shots, and damage.</p>
              <Button className="btn-accent gap-2" onClick={() => setPhotoDialogOpen(true)}>
                <Camera className="w-4 h-4" /> Upload First Photo
              </Button>
            </Card>
          )}
        </TabsContent>

        {/* Logs Tab */}
        <TabsContent value="logs" className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="section-title">Activity Log</h3>
            <Dialog open={logDialogOpen} onOpenChange={setLogDialogOpen}>
              <DialogTrigger asChild>
                <Button className="btn-accent gap-2" data-testid="add-log-btn">
                  <PlusCircle className="w-4 h-4" /> Add Entry
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Add Log Entry</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <Label>Entry Type</Label>
                    <Select value={logForm.entry_type} onValueChange={v => setLogForm({...logForm, entry_type: v})}>
                      <SelectTrigger data-testid="log-type-select"><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="note">Note</SelectItem>
                        <SelectItem value="progress">Progress Update</SelectItem>
                        <SelectItem value="issue">Issue</SelectItem>
                        <SelectItem value="photo">Photo Note</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>Content</Label>
                    <Textarea value={logForm.content} onChange={e => setLogForm({...logForm, content: e.target.value})} placeholder="Enter your note..." rows={4} data-testid="log-content" />
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setLogDialogOpen(false)}>Cancel</Button>
                  <Button className="btn-accent" onClick={handleAddLog} data-testid="save-log-btn">Add Entry</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>

          {logs?.length > 0 ? (
            <div className="space-y-3">
              {logs.map(log => (
                <Card key={log.id} className="p-4">
                  <div className="flex items-start gap-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      log.entry_type === 'issue' ? 'bg-red-100 text-red-600' :
                      log.entry_type === 'progress' ? 'bg-green-100 text-green-600' :
                      'bg-blue-100 text-blue-600'
                    }`}>
                      {log.entry_type === 'issue' ? <AlertCircle className="w-4 h-4" /> :
                       log.entry_type === 'progress' ? <CheckCircle2 className="w-4 h-4" /> :
                       <FileText className="w-4 h-4" />}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant="outline" className="capitalize">{log.entry_type}</Badge>
                        <span className="text-xs text-slate-500">{new Date(log.created_at).toLocaleString()}</span>
                        <span className="text-xs text-slate-500">by {log.created_by}</span>
                      </div>
                      <p className="text-sm">{log.content}</p>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          ) : (
            <Card className="text-center py-12">
              <FileText className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-500">No log entries yet. Add notes to track progress.</p>
            </Card>
          )}
        </TabsContent>

        {/* Financials Tab */}
        <TabsContent value="financials" className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="section-title">Job Expenses</h3>
            <Dialog open={expenseDialogOpen} onOpenChange={setExpenseDialogOpen}>
              <DialogTrigger asChild>
                <Button className="btn-accent gap-2" data-testid="add-expense-btn">
                  <PlusCircle className="w-4 h-4" /> Add Expense
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Add Job Expense</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <Label>Description</Label>
                    <Input value={expenseForm.description} onChange={e => setExpenseForm({...expenseForm, description: e.target.value})} placeholder="Equipment rental" data-testid="expense-description" />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Amount</Label>
                      <Input type="number" step="0.01" value={expenseForm.amount} onChange={e => setExpenseForm({...expenseForm, amount: e.target.value})} data-testid="expense-amount" />
                    </div>
                    <div>
                      <Label>Category</Label>
                      <Select value={expenseForm.category} onValueChange={v => setExpenseForm({...expenseForm, category: v})}>
                        <SelectTrigger><SelectValue /></SelectTrigger>
                        <SelectContent>
                          <SelectItem value="labor">Labor</SelectItem>
                          <SelectItem value="equipment">Equipment</SelectItem>
                          <SelectItem value="materials">Materials</SelectItem>
                          <SelectItem value="overhead">Overhead</SelectItem>
                          <SelectItem value="subcontractor">Subcontractor</SelectItem>
                          <SelectItem value="other">Other</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Vendor</Label>
                      <Input value={expenseForm.vendor} onChange={e => setExpenseForm({...expenseForm, vendor: e.target.value})} placeholder="ABC Supply" />
                    </div>
                    <div>
                      <Label>Date</Label>
                      <Input type="date" value={expenseForm.date} onChange={e => setExpenseForm({...expenseForm, date: e.target.value})} />
                    </div>
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setExpenseDialogOpen(false)}>Cancel</Button>
                  <Button className="btn-accent" onClick={handleAddExpense} data-testid="save-expense-btn">Add Expense</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>

          {/* Cost Breakdown */}
          {Object.keys(costing.expense_breakdown || {}).length > 0 && (
            <Card className="p-4">
              <h4 className="font-semibold mb-3">Cost Breakdown</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {Object.entries(costing.expense_breakdown).map(([cat, amount]) => (
                  <div key={cat} className="p-3 bg-slate-50 rounded-lg">
                    <p className="text-xs text-slate-500 capitalize">{cat}</p>
                    <p className="text-lg font-semibold">${amount.toLocaleString()}</p>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Expenses List */}
          {expenses?.length > 0 ? (
            <Card>
              <CardContent className="p-0">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Description</th>
                      <th>Category</th>
                      <th>Vendor</th>
                      <th className="text-right">Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    {expenses.map(exp => (
                      <tr key={exp.id}>
                        <td>{exp.date}</td>
                        <td>{exp.description}</td>
                        <td><Badge variant="outline" className="capitalize">{exp.category}</Badge></td>
                        <td>{exp.vendor || '-'}</td>
                        <td className="text-right font-semibold">${exp.amount?.toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </CardContent>
            </Card>
          ) : (
            <Card className="text-center py-8">
              <DollarSign className="w-8 h-8 text-slate-300 mx-auto mb-2" />
              <p className="text-slate-500">No expenses tracked yet.</p>
            </Card>
          )}
        </TabsContent>

        {/* Documents Tab */}
        <TabsContent value="documents" className="space-y-4">
          <div className="flex items-center gap-2">
            <Dialog open={invoiceDialogOpen} onOpenChange={setInvoiceDialogOpen}>
              <DialogTrigger asChild>
                <Button className="btn-accent gap-2" data-testid="create-invoice-btn">
                  <FileText className="w-4 h-4" /> Create Invoice
                </Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Create Invoice</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Due Date</Label>
                      <Input type="date" value={invoiceForm.due_date} onChange={e => setInvoiceForm({...invoiceForm, due_date: e.target.value})} data-testid="invoice-due-date" />
                    </div>
                    <div>
                      <Label>Tax Rate (%)</Label>
                      <Input type="number" step="0.01" value={invoiceForm.tax_rate} onChange={e => setInvoiceForm({...invoiceForm, tax_rate: e.target.value})} />
                    </div>
                  </div>
                  <div>
                    <Label>Notes</Label>
                    <Textarea value={invoiceForm.notes} onChange={e => setInvoiceForm({...invoiceForm, notes: e.target.value})} placeholder="Invoice notes..." />
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setInvoiceDialogOpen(false)}>Cancel</Button>
                  <Button className="btn-accent" onClick={handleCreateInvoice} data-testid="save-invoice-btn">Create Invoice</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>

            <Dialog open={workOrderDialogOpen} onOpenChange={setWorkOrderDialogOpen}>
              <DialogTrigger asChild>
                <Button variant="outline" className="gap-2" data-testid="create-work-order-btn">
                  <ClipboardList className="w-4 h-4" /> Create Work Order
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-xl">
                <DialogHeader>
                  <DialogTitle>Create Work Order</DialogTitle>
                </DialogHeader>
                <div className="space-y-4">
                  <div>
                    <Label>Tasks</Label>
                    <div className="space-y-2 mb-2">
                      {workOrderForm.tasks.map((t, i) => (
                        <div key={i} className="flex items-center gap-2 p-2 bg-slate-50 rounded">
                          <span className="flex-1">{t}</span>
                          <Button type="button" variant="ghost" size="sm" onClick={() => setWorkOrderForm({...workOrderForm, tasks: workOrderForm.tasks.filter((_, idx) => idx !== i)})} className="text-red-500">
                            <X className="w-4 h-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                    <div className="flex gap-2">
                      <Input placeholder="Add task..." value={newTask} onChange={e => setNewTask(e.target.value)} />
                      <Button type="button" onClick={() => { if (newTask) { setWorkOrderForm({...workOrderForm, tasks: [...workOrderForm.tasks, newTask]}); setNewTask(""); }}}>Add</Button>
                    </div>
                  </div>
                  <div>
                    <Label>Materials Needed</Label>
                    <div className="flex flex-wrap gap-2 mb-2">
                      {workOrderForm.materials_needed.map((m, i) => (
                        <Badge key={i} variant="secondary" className="gap-1">
                          {m}
                          <X className="w-3 h-3 cursor-pointer" onClick={() => setWorkOrderForm({...workOrderForm, materials_needed: workOrderForm.materials_needed.filter((_, idx) => idx !== i)})} />
                        </Badge>
                      ))}
                    </div>
                    <div className="flex gap-2">
                      <Input placeholder="Add material..." value={newMaterial} onChange={e => setNewMaterial(e.target.value)} />
                      <Button type="button" onClick={() => { if (newMaterial) { setWorkOrderForm({...workOrderForm, materials_needed: [...workOrderForm.materials_needed, newMaterial]}); setNewMaterial(""); }}}>Add</Button>
                    </div>
                  </div>
                  <div>
                    <Label>Notes</Label>
                    <Textarea value={workOrderForm.notes} onChange={e => setWorkOrderForm({...workOrderForm, notes: e.target.value})} placeholder="Additional notes..." />
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setWorkOrderDialogOpen(false)}>Cancel</Button>
                  <Button className="btn-accent" onClick={handleCreateWorkOrder} data-testid="save-work-order-btn">Create Work Order</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>

          {/* Invoices */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Invoices</CardTitle>
            </CardHeader>
            <CardContent>
              {invoices?.length > 0 ? (
                <div className="space-y-2">
                  {invoices.map(inv => (
                    <div key={inv.id} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                      <div>
                        <p className="font-mono text-sm">{inv.invoice_number}</p>
                        <p className="text-sm text-slate-500">Due: {inv.due_date}</p>
                      </div>
                      <div className="flex items-center gap-3">
                        <Badge className={`status-${inv.status}`}>{inv.status}</Badge>
                        <span className="font-semibold">${inv.total?.toLocaleString()}</span>
                        <Button variant="ghost" size="icon" onClick={async () => {
                          const res = await axios.get(`${API}/invoices/${inv.id}/pdf`, { responseType: 'blob' });
                          const url = window.URL.createObjectURL(new Blob([res.data]));
                          const link = document.createElement('a');
                          link.href = url;
                          link.setAttribute('download', `${inv.invoice_number}.pdf`);
                          document.body.appendChild(link);
                          link.click();
                          link.remove();
                        }}>
                          <Download className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-slate-500 text-center py-4">No invoices created yet.</p>
              )}
            </CardContent>
          </Card>

          {/* Work Orders */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Work Orders</CardTitle>
            </CardHeader>
            <CardContent>
              {work_orders?.length > 0 ? (
                <div className="space-y-2">
                  {work_orders.map(wo => (
                    <div key={wo.id} className="p-3 bg-slate-50 rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <Badge className={`status-${wo.status}`}>{wo.status}</Badge>
                        <span className="text-sm font-medium">{Math.round(wo.completion_percentage)}% Complete</span>
                      </div>
                      <Progress value={wo.completion_percentage} className="h-2 mb-2" />
                      <p className="text-sm text-slate-500">{wo.tasks?.length || 0} tasks • {wo.materials_needed?.length || 0} materials</p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-slate-500 text-center py-4">No work orders created yet.</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

// Crews Page (simplified - keeping for navigation)
const CrewsPage = () => {
  const [crews, setCrews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedCrew, setSelectedCrew] = useState(null);
  const [formData, setFormData] = useState({ name: "", specialty: "general", status: "available", members: [] });
  const [newMember, setNewMember] = useState({ name: "", role: "", phone: "", hourly_rate: 0 });

  const loadCrews = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/crews`);
      setCrews(res.data);
    } catch (err) {
      toast.error("Failed to load crews");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadCrews(); }, [loadCrews]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (selectedCrew) {
        await axios.put(`${API}/crews/${selectedCrew.id}`, formData);
        toast.success("Crew updated!");
      } else {
        await axios.post(`${API}/crews`, formData);
        toast.success("Crew created!");
      }
      setDialogOpen(false);
      loadCrews();
      resetForm();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to save crew");
    }
  };

  const addMember = () => {
    if (newMember.name && newMember.role) {
      setFormData({ ...formData, members: [...formData.members, { ...newMember, hourly_rate: parseFloat(newMember.hourly_rate) || 0 }] });
      setNewMember({ name: "", role: "", phone: "", hourly_rate: 0 });
    }
  };

  const removeMember = (index) => {
    setFormData({ ...formData, members: formData.members.filter((_, i) => i !== index) });
  };

  const resetForm = () => {
    setSelectedCrew(null);
    setFormData({ name: "", specialty: "general", status: "available", members: [] });
    setNewMember({ name: "", role: "", phone: "", hourly_rate: 0 });
  };

  const handleEdit = (crew) => {
    setSelectedCrew(crew);
    setFormData({ name: crew.name, specialty: crew.specialty, status: crew.status, members: crew.members || [] });
    setDialogOpen(true);
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900"></div></div>;

  return (
    <div className="space-y-6 animate-fade-in" data-testid="crews-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Crews</h1>
          <p className="text-slate-500 mt-1">Manage your restoration crews</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
          <DialogTrigger asChild>
            <Button className="btn-accent gap-2" data-testid="create-crew-btn">
              <Plus className="w-4 h-4" /> New Crew
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>{selectedCrew ? "Edit Crew" : "Create New Crew"}</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <Label>Crew Name</Label>
                <Input value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} placeholder="Alpha Team" required data-testid="crew-name-input" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Specialty</Label>
                  <Select value={formData.specialty} onValueChange={v => setFormData({...formData, specialty: v})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="general">General</SelectItem>
                      <SelectItem value="water">Water Damage</SelectItem>
                      <SelectItem value="fire">Fire Damage</SelectItem>
                      <SelectItem value="mold">Mold Remediation</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Status</Label>
                  <Select value={formData.status} onValueChange={v => setFormData({...formData, status: v})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="available">Available</SelectItem>
                      <SelectItem value="busy">Busy</SelectItem>
                      <SelectItem value="off">Off Duty</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <Separator />
              <div>
                <Label className="text-base font-semibold">Team Members</Label>
                <div className="mt-2 space-y-2">
                  {formData.members.map((m, i) => (
                    <div key={i} className="flex items-center gap-2 p-2 bg-slate-50 rounded-lg">
                      <span className="flex-1">{m.name} - {m.role}</span>
                      <span className="text-sm text-slate-500">${m.hourly_rate}/hr</span>
                      <Button type="button" variant="ghost" size="sm" onClick={() => removeMember(i)} className="text-red-500">
                        <X className="w-4 h-4" />
                      </Button>
                    </div>
                  ))}
                </div>
                <div className="grid grid-cols-4 gap-2 mt-3">
                  <Input placeholder="Name" value={newMember.name} onChange={e => setNewMember({...newMember, name: e.target.value})} />
                  <Input placeholder="Role" value={newMember.role} onChange={e => setNewMember({...newMember, role: e.target.value})} />
                  <Input placeholder="Phone" value={newMember.phone} onChange={e => setNewMember({...newMember, phone: e.target.value})} />
                  <div className="flex gap-1">
                    <Input type="number" placeholder="Rate" value={newMember.hourly_rate} onChange={e => setNewMember({...newMember, hourly_rate: e.target.value})} />
                    <Button type="button" onClick={addMember} size="icon"><Plus className="w-4 h-4" /></Button>
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => { setDialogOpen(false); resetForm(); }}>Cancel</Button>
                <Button type="submit" className="btn-accent">{selectedCrew ? "Update" : "Create"} Crew</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {crews.length === 0 ? (
        <Card className="text-center py-12">
          <Users className="w-12 h-12 text-slate-300 mx-auto mb-4" />
          <p className="text-slate-500">No crews yet. Create your first crew to get started!</p>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {crews.map(crew => (
            <Card key={crew.id} className="card-hover" data-testid={`crew-card-${crew.id}`}>
              <CardContent className="p-4">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="font-semibold text-slate-900">{crew.name}</h3>
                    <p className="text-sm text-slate-500 capitalize">{crew.specialty} Specialists</p>
                  </div>
                  <Badge className={crew.status === 'available' ? 'bg-green-100 text-green-700' : crew.status === 'busy' ? 'bg-orange-100 text-orange-700' : 'bg-slate-100 text-slate-600'}>
                    {crew.status}
                  </Badge>
                </div>
                <div className="flex items-center gap-1 mb-3">
                  <Users className="w-4 h-4 text-slate-400" />
                  <span className="text-sm text-slate-600">{crew.members?.length || 0} members</span>
                </div>
                {crew.members?.length > 0 && (
                  <div className="space-y-1 mb-3">
                    {crew.members.slice(0, 3).map((m, i) => (
                      <div key={i} className="text-sm text-slate-600 flex items-center gap-2">
                        <div className="w-6 h-6 rounded-full bg-slate-200 flex items-center justify-center text-xs font-medium">{m.name.charAt(0)}</div>
                        <span>{m.name}</span>
                        <span className="text-slate-400">• {m.role}</span>
                      </div>
                    ))}
                    {crew.members.length > 3 && (
                      <p className="text-xs text-slate-400">+{crew.members.length - 3} more</p>
                    )}
                  </div>
                )}
                <Button variant="outline" size="sm" className="w-full" onClick={() => handleEdit(crew)}>
                  Manage Crew
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

// Simple placeholder pages for other sections (Invoices, WorkOrders, Accounting, Reports, AI Assistant)
const InvoicesPage = () => {
  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    axios.get(`${API}/invoices`).then(res => setInvoices(res.data)).catch(() => toast.error("Failed to load")).finally(() => setLoading(false));
  }, []);

  const downloadPDF = async (id, number) => {
    const res = await axios.get(`${API}/invoices/${id}/pdf`, { responseType: 'blob' });
    const url = window.URL.createObjectURL(new Blob([res.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `${number}.pdf`);
    document.body.appendChild(link);
    link.click();
    link.remove();
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900"></div></div>;

  return (
    <div className="space-y-6 animate-fade-in" data-testid="invoices-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Invoices</h1>
          <p className="text-slate-500 mt-1">Manage and track your invoices</p>
        </div>
        <Button variant="outline" onClick={() => window.open(`${API}/export/quickbooks?data_type=invoices`, '_blank')}>
          <Download className="w-4 h-4 mr-2" /> Export CSV
        </Button>
      </div>

      {invoices.length === 0 ? (
        <Card className="text-center py-12">
          <FileText className="w-12 h-12 text-slate-300 mx-auto mb-4" />
          <p className="text-slate-500">No invoices yet. Create invoices from job details.</p>
        </Card>
      ) : (
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead><tr><th>Invoice #</th><th>Customer</th><th>Amount</th><th>Due Date</th><th>Status</th><th>Actions</th></tr></thead>
            <tbody>
              {invoices.map(inv => (
                <tr key={inv.id}>
                  <td className="font-mono text-sm">{inv.invoice_number}</td>
                  <td>{inv.customer_name}</td>
                  <td className="font-semibold">${inv.total?.toLocaleString()}</td>
                  <td>{inv.due_date}</td>
                  <td><Badge className={`status-${inv.status}`}>{inv.status}</Badge></td>
                  <td>
                    <Button variant="ghost" size="sm" onClick={() => downloadPDF(inv.id, inv.invoice_number)}><Download className="w-4 h-4" /></Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

const WorkOrdersPage = () => {
  const [workOrders, setWorkOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${API}/work-orders`).then(res => setWorkOrders(res.data)).catch(() => toast.error("Failed to load")).finally(() => setLoading(false));
  }, []);

  const toggleTask = async (woId, tasks, taskIndex) => {
    const updated = tasks.map((t, i) => i === taskIndex ? { ...t, is_completed: !t.is_completed } : t);
    await axios.put(`${API}/work-orders/${woId}/tasks`, updated);
    toast.success("Task updated!");
    const res = await axios.get(`${API}/work-orders`);
    setWorkOrders(res.data);
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900"></div></div>;

  return (
    <div className="space-y-6 animate-fade-in" data-testid="work-orders-page">
      <div>
        <h1 className="page-title">Work Orders</h1>
        <p className="text-slate-500 mt-1">Track tasks and materials for jobs</p>
      </div>

      {workOrders.length === 0 ? (
        <Card className="text-center py-12">
          <ClipboardList className="w-12 h-12 text-slate-300 mx-auto mb-4" />
          <p className="text-slate-500">No work orders yet. Create them from job details.</p>
        </Card>
      ) : (
        <div className="grid gap-4">
          {workOrders.map(wo => (
            <Card key={wo.id}>
              <CardContent className="p-4">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <h3 className="font-semibold text-slate-900">{wo.job_title}</h3>
                    <Badge className={`status-${wo.status}`}>{wo.status}</Badge>
                  </div>
                  <div className="text-right">
                    <p className="text-2xl font-bold text-slate-900">{Math.round(wo.completion_percentage)}%</p>
                    <p className="text-sm text-slate-500">Complete</p>
                  </div>
                </div>
                <Progress value={wo.completion_percentage} className="mb-4" />
                <div className="space-y-2">
                  {wo.tasks?.map((task, i) => (
                    <div key={i} className="flex items-center gap-3 p-2 rounded hover:bg-slate-50 cursor-pointer" onClick={() => toggleTask(wo.id, wo.tasks, i)}>
                      <div className={`w-5 h-5 rounded border-2 flex items-center justify-center ${task.is_completed ? 'bg-green-500 border-green-500' : 'border-slate-300'}`}>
                        {task.is_completed && <CheckCircle2 className="w-4 h-4 text-white" />}
                      </div>
                      <span className={task.is_completed ? 'line-through text-slate-400' : ''}>{task.description}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

// Daily Logs Page
const DailyLogsPage = () => {
  const [dailyLogs, setDailyLogs] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [crews, setCrews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    job_id: "", date: new Date().toISOString().split('T')[0], phase: "general",
    labor_entries: [], equipment_entries: [], material_entries: [],
    weather_conditions: "", work_performed: "", issues_encountered: "", notes: ""
  });
  const [laborEntry, setLaborEntry] = useState({ crew_member_name: "", hours: 0, hourly_rate: 0, task_description: "" });
  const [equipmentEntry, setEquipmentEntry] = useState({ equipment_name: "", quantity: 1, daily_rate: 0, notes: "" });
  const [materialEntry, setMaterialEntry] = useState({ material_name: "", quantity: 0, unit: "each", unit_cost: 0 });

  const loadData = useCallback(async () => {
    try {
      const [logsRes, jobsRes, crewsRes] = await Promise.all([
        axios.get(`${API}/daily-logs`),
        axios.get(`${API}/jobs`),
        axios.get(`${API}/crews`)
      ]);
      setDailyLogs(logsRes.data);
      setJobs(jobsRes.data);
      setCrews(crewsRes.data);
    } catch (err) {
      toast.error("Failed to load data");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/daily-logs`, formData);
      toast.success("Daily log created!");
      setDialogOpen(false);
      loadData();
      resetForm();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to create log");
    }
  };

  const resetForm = () => {
    setFormData({
      job_id: "", date: new Date().toISOString().split('T')[0], phase: "general",
      labor_entries: [], equipment_entries: [], material_entries: [],
      weather_conditions: "", work_performed: "", issues_encountered: "", notes: ""
    });
  };

  const addLaborEntry = () => {
    if (laborEntry.crew_member_name && laborEntry.hours > 0) {
      setFormData({
        ...formData,
        labor_entries: [...formData.labor_entries, { ...laborEntry, hours: parseFloat(laborEntry.hours), hourly_rate: parseFloat(laborEntry.hourly_rate) || 0 }]
      });
      setLaborEntry({ crew_member_name: "", hours: 0, hourly_rate: 0, task_description: "" });
    }
  };

  const addEquipmentEntry = () => {
    if (equipmentEntry.equipment_name) {
      setFormData({
        ...formData,
        equipment_entries: [...formData.equipment_entries, { ...equipmentEntry, quantity: parseInt(equipmentEntry.quantity), daily_rate: parseFloat(equipmentEntry.daily_rate) || 0 }]
      });
      setEquipmentEntry({ equipment_name: "", quantity: 1, daily_rate: 0, notes: "" });
    }
  };

  const addMaterialEntry = () => {
    if (materialEntry.material_name && materialEntry.quantity > 0) {
      setFormData({
        ...formData,
        material_entries: [...formData.material_entries, { ...materialEntry, quantity: parseFloat(materialEntry.quantity), unit_cost: parseFloat(materialEntry.unit_cost) || 0 }]
      });
      setMaterialEntry({ material_name: "", quantity: 0, unit: "each", unit_cost: 0 });
    }
  };

  const getJobById = (id) => jobs.find(j => j.id === id);

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900"></div></div>;

  return (
    <div className="space-y-6 animate-fade-in" data-testid="daily-logs-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Daily Job Logs</h1>
          <p className="text-slate-500 mt-1">Track labor, equipment, and materials by day</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
          <DialogTrigger asChild>
            <Button className="btn-accent gap-2" data-testid="create-daily-log-btn">
              <Plus className="w-4 h-4" /> New Daily Log
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Create Daily Log</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-6">
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label>Select Job *</Label>
                  <Select value={formData.job_id} onValueChange={v => setFormData({...formData, job_id: v})}>
                    <SelectTrigger><SelectValue placeholder="Select job" /></SelectTrigger>
                    <SelectContent>
                      {jobs.filter(j => j.status !== 'completed').map(job => (
                        <SelectItem key={job.id} value={job.id}>{job.title}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Date *</Label>
                  <Input type="date" value={formData.date} onChange={e => setFormData({...formData, date: e.target.value})} required />
                </div>
                <div>
                  <Label>Phase</Label>
                  <Select value={formData.phase} onValueChange={v => setFormData({...formData, phase: v})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="general">General</SelectItem>
                      <SelectItem value="emergency_services">Emergency Services</SelectItem>
                      <SelectItem value="drying_remediation">Drying/Remediation</SelectItem>
                      <SelectItem value="repairs_rebuild">Repairs/Rebuild</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <Separator />

              {/* Labor Entries */}
              <div className="space-y-3">
                <h4 className="font-semibold flex items-center gap-2"><User className="w-4 h-4 text-blue-500" /> Labor Hours</h4>
                {formData.labor_entries.map((entry, i) => (
                  <div key={i} className="flex items-center gap-2 p-2 bg-blue-50 rounded text-sm">
                    <span className="flex-1">{entry.crew_member_name} - {entry.hours}hrs @ ${entry.hourly_rate}/hr = ${(entry.hours * entry.hourly_rate).toFixed(2)}</span>
                    <Button type="button" variant="ghost" size="sm" onClick={() => setFormData({...formData, labor_entries: formData.labor_entries.filter((_, idx) => idx !== i)})} className="text-red-500"><X className="w-4 h-4" /></Button>
                  </div>
                ))}
                <div className="grid grid-cols-5 gap-2">
                  <Input placeholder="Name" value={laborEntry.crew_member_name} onChange={e => setLaborEntry({...laborEntry, crew_member_name: e.target.value})} />
                  <Input type="number" step="0.5" placeholder="Hours" value={laborEntry.hours || ""} onChange={e => setLaborEntry({...laborEntry, hours: e.target.value})} />
                  <Input type="number" step="0.01" placeholder="Rate" value={laborEntry.hourly_rate || ""} onChange={e => setLaborEntry({...laborEntry, hourly_rate: e.target.value})} />
                  <Input placeholder="Task" value={laborEntry.task_description} onChange={e => setLaborEntry({...laborEntry, task_description: e.target.value})} />
                  <Button type="button" onClick={addLaborEntry}><Plus className="w-4 h-4" /></Button>
                </div>
              </div>

              {/* Equipment Entries */}
              <div className="space-y-3">
                <h4 className="font-semibold flex items-center gap-2"><Wrench className="w-4 h-4 text-orange-500" /> Equipment Used</h4>
                {formData.equipment_entries.map((entry, i) => (
                  <div key={i} className="flex items-center gap-2 p-2 bg-orange-50 rounded text-sm">
                    <span className="flex-1">{entry.equipment_name} x{entry.quantity} @ ${entry.daily_rate}/day = ${(entry.quantity * entry.daily_rate).toFixed(2)}</span>
                    <Button type="button" variant="ghost" size="sm" onClick={() => setFormData({...formData, equipment_entries: formData.equipment_entries.filter((_, idx) => idx !== i)})} className="text-red-500"><X className="w-4 h-4" /></Button>
                  </div>
                ))}
                <div className="grid grid-cols-5 gap-2">
                  <Input placeholder="Equipment" value={equipmentEntry.equipment_name} onChange={e => setEquipmentEntry({...equipmentEntry, equipment_name: e.target.value})} className="col-span-2" />
                  <Input type="number" placeholder="Qty" value={equipmentEntry.quantity || ""} onChange={e => setEquipmentEntry({...equipmentEntry, quantity: e.target.value})} />
                  <Input type="number" step="0.01" placeholder="Daily Rate" value={equipmentEntry.daily_rate || ""} onChange={e => setEquipmentEntry({...equipmentEntry, daily_rate: e.target.value})} />
                  <Button type="button" onClick={addEquipmentEntry}><Plus className="w-4 h-4" /></Button>
                </div>
              </div>

              {/* Material Entries */}
              <div className="space-y-3">
                <h4 className="font-semibold flex items-center gap-2"><Receipt className="w-4 h-4 text-green-500" /> Materials Used</h4>
                {formData.material_entries.map((entry, i) => (
                  <div key={i} className="flex items-center gap-2 p-2 bg-green-50 rounded text-sm">
                    <span className="flex-1">{entry.material_name} - {entry.quantity} {entry.unit} @ ${entry.unit_cost}/ea = ${(entry.quantity * entry.unit_cost).toFixed(2)}</span>
                    <Button type="button" variant="ghost" size="sm" onClick={() => setFormData({...formData, material_entries: formData.material_entries.filter((_, idx) => idx !== i)})} className="text-red-500"><X className="w-4 h-4" /></Button>
                  </div>
                ))}
                <div className="grid grid-cols-5 gap-2">
                  <Input placeholder="Material" value={materialEntry.material_name} onChange={e => setMaterialEntry({...materialEntry, material_name: e.target.value})} />
                  <Input type="number" step="0.01" placeholder="Qty" value={materialEntry.quantity || ""} onChange={e => setMaterialEntry({...materialEntry, quantity: e.target.value})} />
                  <Select value={materialEntry.unit} onValueChange={v => setMaterialEntry({...materialEntry, unit: v})}>
                    <SelectTrigger><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value="each">Each</SelectItem>
                      <SelectItem value="sqft">Sq Ft</SelectItem>
                      <SelectItem value="lf">Linear Ft</SelectItem>
                      <SelectItem value="gallon">Gallon</SelectItem>
                      <SelectItem value="roll">Roll</SelectItem>
                    </SelectContent>
                  </Select>
                  <Input type="number" step="0.01" placeholder="Unit Cost" value={materialEntry.unit_cost || ""} onChange={e => setMaterialEntry({...materialEntry, unit_cost: e.target.value})} />
                  <Button type="button" onClick={addMaterialEntry}><Plus className="w-4 h-4" /></Button>
                </div>
              </div>

              <Separator />

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Weather Conditions</Label>
                  <Input value={formData.weather_conditions} onChange={e => setFormData({...formData, weather_conditions: e.target.value})} placeholder="Clear, 75°F" />
                </div>
                <div>
                  <Label>Work Performed</Label>
                  <Textarea value={formData.work_performed} onChange={e => setFormData({...formData, work_performed: e.target.value})} placeholder="Summary of work done..." rows={2} />
                </div>
              </div>

              <div>
                <Label>Issues Encountered</Label>
                <Textarea value={formData.issues_encountered} onChange={e => setFormData({...formData, issues_encountered: e.target.value})} placeholder="Any problems or delays..." rows={2} />
              </div>

              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => { setDialogOpen(false); resetForm(); }}>Cancel</Button>
                <Button type="submit" className="btn-accent" disabled={!formData.job_id}>Create Log</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {dailyLogs.length === 0 ? (
        <Card className="text-center py-12">
          <ClipboardList className="w-12 h-12 text-slate-300 mx-auto mb-4" />
          <p className="text-slate-500">No daily logs yet. Create your first log to track job progress.</p>
        </Card>
      ) : (
        <div className="space-y-4">
          {dailyLogs.map(log => {
            const job = getJobById(log.job_id);
            const laborTotal = log.labor_entries?.reduce((sum, e) => sum + (e.hours * e.hourly_rate), 0) || 0;
            const equipmentTotal = log.equipment_entries?.reduce((sum, e) => sum + (e.quantity * e.daily_rate), 0) || 0;
            const materialTotal = log.material_entries?.reduce((sum, e) => sum + (e.quantity * e.unit_cost), 0) || 0;
            
            return (
              <Card key={log.id} className="card-hover">
                <CardContent className="p-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-semibold">{job?.title || 'Unknown Job'}</h3>
                        <Badge variant="outline">{log.date}</Badge>
                        <Badge variant="outline" className="capitalize">{log.phase?.replace('_', ' ')}</Badge>
                      </div>
                      {log.work_performed && <p className="text-sm text-slate-600 mt-1">{log.work_performed}</p>}
                      <div className="flex gap-4 mt-2 text-sm">
                        <span className="text-blue-600">Labor: ${laborTotal.toFixed(2)}</span>
                        <span className="text-orange-600">Equipment: ${equipmentTotal.toFixed(2)}</span>
                        <span className="text-green-600">Materials: ${materialTotal.toFixed(2)}</span>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-xl font-bold">${(laborTotal + equipmentTotal + materialTotal).toFixed(2)}</p>
                      <p className="text-xs text-slate-500">Day Total</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
};

// Collections Page
const CollectionsPage = () => {
  const [collectionsData, setCollectionsData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${API}/reports/collections`)
      .then(res => setCollectionsData(res.data))
      .catch(() => toast.error("Failed to load collections data"))
      .finally(() => setLoading(false));
  }, []);

  const markFollowupComplete = async (invoiceId, day) => {
    try {
      await axios.put(`${API}/invoices/${invoiceId}/followup?day=${day}&notes=Followed up`);
      toast.success("Follow-up marked complete!");
      const res = await axios.get(`${API}/reports/collections`);
      setCollectionsData(res.data);
    } catch (err) {
      toast.error("Failed to update follow-up");
    }
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900"></div></div>;

  return (
    <div className="space-y-6 animate-fade-in" data-testid="collections-page">
      <div>
        <h1 className="page-title">Collections & Follow-ups</h1>
        <p className="text-slate-500 mt-1">Track outstanding invoices and payment follow-ups</p>
      </div>

      {/* Aging Buckets */}
      <div className="grid grid-cols-5 gap-4">
        {[
          { label: "Current", key: "current", color: "bg-green-50 text-green-700" },
          { label: "1-30 Days", key: "1-30", color: "bg-yellow-50 text-yellow-700" },
          { label: "31-60 Days", key: "31-60", color: "bg-orange-50 text-orange-700" },
          { label: "61-90 Days", key: "61-90", color: "bg-red-50 text-red-700" },
          { label: "90+ Days", key: "90+", color: "bg-red-100 text-red-800" }
        ].map(bucket => (
          <Card key={bucket.key} className={`${bucket.color} border-0`}>
            <CardContent className="p-4 text-center">
              <p className="text-sm font-medium">{bucket.label}</p>
              <p className="text-2xl font-bold">${(collectionsData?.aging_buckets?.[bucket.key] || 0).toLocaleString()}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <PhoneCall className="w-5 h-5 text-orange-500" />
            Follow-ups Due ({collectionsData?.followups_due_count || 0})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {collectionsData?.followups_due?.length > 0 ? (
            <div className="space-y-3">
              {collectionsData.followups_due.map((item, i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                  <div>
                    <p className="font-semibold">{item.invoice_number}</p>
                    <p className="text-sm text-slate-600">{item.customer_name}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge variant="outline">Day {item.followup_day} Follow-up</Badge>
                      <Badge className={item.days_overdue > 30 ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'}>
                        {item.days_overdue} days overdue
                      </Badge>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="text-lg font-bold">${item.total.toLocaleString()}</p>
                      <p className="text-xs text-slate-500">Due: {item.due_date}</p>
                    </div>
                    <Button size="sm" onClick={() => markFollowupComplete(item.invoice_id, item.followup_day)}>
                      <CheckCircle2 className="w-4 h-4 mr-1" /> Done
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-slate-500 text-center py-8">No follow-ups due. Great job staying on top of collections!</p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Collection Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 bg-slate-50 rounded-lg">
              <p className="text-sm text-slate-600">Total Outstanding</p>
              <p className="text-3xl font-bold text-slate-900">${(collectionsData?.total_outstanding || 0).toLocaleString()}</p>
            </div>
            <div className="p-4 bg-slate-50 rounded-lg">
              <p className="text-sm text-slate-600">Follow-up Schedule</p>
              <p className="text-sm text-slate-700 mt-1">Day 3, 7, 14, 21, 30, 45, 60, 90</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

const AccountingPage = () => {
  const [expenses, setExpenses] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    axios.get(`${API}/expenses`).then(res => setExpenses(res.data)).catch(() => toast.error("Failed to load")).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900"></div></div>;

  return (
    <div className="space-y-6 animate-fade-in" data-testid="accounting-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Accounting</h1>
          <p className="text-slate-500 mt-1">Manage expenses and transactions</p>
        </div>
        <Button variant="outline" onClick={() => window.open(`${API}/export/quickbooks?data_type=expenses`, '_blank')}>
          <Download className="w-4 h-4 mr-2" /> Export CSV
        </Button>
      </div>

      {expenses.length === 0 ? (
        <Card className="text-center py-12">
          <DollarSign className="w-12 h-12 text-slate-300 mx-auto mb-4" />
          <p className="text-slate-500">No expenses recorded yet. Add expenses from job details.</p>
        </Card>
      ) : (
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead><tr><th>Date</th><th>Description</th><th>Category</th><th>Vendor</th><th>Amount</th></tr></thead>
            <tbody>
              {expenses.map(exp => (
                <tr key={exp.id}>
                  <td>{exp.date}</td>
                  <td>{exp.description}</td>
                  <td><Badge variant="outline" className="capitalize">{exp.category}</Badge></td>
                  <td>{exp.vendor || '-'}</td>
                  <td className="font-semibold">${exp.amount?.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

const ReportsPage = () => {
  const [activeReport, setActiveReport] = useState('profit-loss');
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadReport = async (type) => {
    setLoading(true);
    setActiveReport(type);
    try {
      const endpoints = { 'profit-loss': '/reports/profit-loss', 'tax-summary': '/reports/tax-summary', 'cash-flow': '/reports/cash-flow-forecast' };
      const res = await axios.get(`${API}${endpoints[type]}`);
      setReportData(res.data);
    } catch (err) {
      toast.error("Failed to load report");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadReport('profit-loss'); }, []);

  return (
    <div className="space-y-6 animate-fade-in" data-testid="reports-page">
      <div><h1 className="page-title">Financial Reports</h1><p className="text-slate-500 mt-1">View financial summaries and forecasts</p></div>
      <div className="flex gap-2">
        {[{ id: 'profit-loss', label: 'Profit & Loss' }, { id: 'tax-summary', label: 'Tax Summary' }, { id: 'cash-flow', label: 'Cash Flow Forecast' }].map(report => (
          <Button key={report.id} variant={activeReport === report.id ? 'default' : 'outline'} onClick={() => loadReport(report.id)}>{report.label}</Button>
        ))}
      </div>

      {loading ? <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900"></div></div> : reportData && (
        <Card>
          <CardHeader><CardTitle className="capitalize">{activeReport.replace('-', ' ')}</CardTitle></CardHeader>
          <CardContent>
            {activeReport === 'profit-loss' && (
              <div className="grid grid-cols-3 gap-4">
                <div className="p-4 bg-green-50 rounded-lg"><p className="text-sm text-green-600">Total Revenue</p><p className="text-2xl font-bold text-green-700">${reportData.total_revenue?.toLocaleString() || 0}</p></div>
                <div className="p-4 bg-red-50 rounded-lg"><p className="text-sm text-red-600">Total Expenses</p><p className="text-2xl font-bold text-red-700">${reportData.total_expenses?.toLocaleString() || 0}</p></div>
                <div className={`p-4 rounded-lg ${reportData.net_profit >= 0 ? 'bg-emerald-50' : 'bg-red-50'}`}><p className={`text-sm ${reportData.net_profit >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>Net Profit</p><p className={`text-2xl font-bold ${reportData.net_profit >= 0 ? 'text-emerald-700' : 'text-red-700'}`}>${reportData.net_profit?.toLocaleString() || 0}</p></div>
              </div>
            )}
            {activeReport === 'tax-summary' && (
              <div className="grid grid-cols-2 gap-4">
                <div className="p-4 bg-blue-50 rounded-lg"><p className="text-sm text-blue-600">Sales Tax Collected</p><p className="text-2xl font-bold text-blue-700">${reportData.sales_tax_collected?.toLocaleString() || 0}</p></div>
                <div className="p-4 bg-slate-50 rounded-lg"><p className="text-sm text-slate-600">Taxable Revenue</p><p className="text-2xl font-bold text-slate-700">${reportData.taxable_revenue?.toLocaleString() || 0}</p></div>
              </div>
            )}
            {activeReport === 'cash-flow' && reportData.forecasts && (
              <div className="grid grid-cols-3 gap-4">
                {reportData.forecasts.map((f, i) => (
                  <Card key={i} className="p-4">
                    <h4 className="font-semibold text-slate-900 mb-3">{f.period}</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between"><span className="text-slate-500">Expected Income</span><span className="text-green-600 font-medium">${f.expected_income?.toLocaleString()}</span></div>
                      <div className="flex justify-between"><span className="text-slate-500">Expected Expenses</span><span className="text-red-600 font-medium">${f.expected_expenses?.toLocaleString()}</span></div>
                      <Separator />
                      <div className="flex justify-between"><span className="font-medium">Net Cash Flow</span><span className={`font-bold ${f.net_cash_flow >= 0 ? 'text-green-600' : 'text-red-600'}`}>${f.net_cash_flow?.toLocaleString()}</span></div>
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};

// Adjuster Follow-Up Page
const AdjusterFollowUpPage = () => {
  const [pendingThreads, setPendingThreads] = useState([]);
  const [activeThreads, setActiveThreads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('pending');
  const [selectedThread, setSelectedThread] = useState(null);

  const loadData = async () => {
    try {
      const [pendingRes, activeRes] = await Promise.all([
        axios.get(`${API}/adjuster-followups/pending-approval`),
        axios.get(`${API}/adjuster-followups/active`)
      ]);
      setPendingThreads(pendingRes.data);
      setActiveThreads(activeRes.data);
    } catch (err) {
      toast.error("Failed to load follow-up data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const approveThread = async (threadId) => {
    try {
      await axios.put(`${API}/adjuster-followups/${threadId}/approve`);
      toast.success("Follow-up approved and activated!");
      loadData();
    } catch (err) {
      toast.error("Failed to approve thread");
    }
  };

  const rejectThread = async (threadId) => {
    try {
      await axios.put(`${API}/adjuster-followups/${threadId}/reject`);
      toast.success("Follow-up rejected");
      loadData();
    } catch (err) {
      toast.error("Failed to reject thread");
    }
  };

  const pauseThread = async (threadId) => {
    try {
      await axios.put(`${API}/adjuster-followups/${threadId}/pause`);
      toast.success("Follow-up paused");
      loadData();
    } catch (err) {
      toast.error("Failed to pause thread");
    }
  };

  const resumeThread = async (threadId) => {
    try {
      await axios.put(`${API}/adjuster-followups/${threadId}/resume`);
      toast.success("Follow-up resumed");
      loadData();
    } catch (err) {
      toast.error("Failed to resume thread");
    }
  };

  const sendManualFollowup = async (threadId) => {
    try {
      await axios.post(`${API}/adjuster-followups/${threadId}/send`);
      toast.success("Follow-up email sent!");
      loadData();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to send follow-up");
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleDateString();
  };

  const getDaysOutstanding = (firstContactDate) => {
    const first = new Date(firstContactDate);
    const now = new Date();
    return Math.floor((now - first) / (1000 * 60 * 60 * 24));
  };

  const getStatusBadge = (status) => {
    const statusColors = {
      active: 'bg-green-100 text-green-700',
      paused: 'bg-gray-100 text-gray-700',
      paid: 'bg-blue-100 text-blue-700',
      coverage_issued: 'bg-purple-100 text-purple-700',
      disputed: 'bg-red-100 text-red-700',
      escalated_internal: 'bg-orange-100 text-orange-700',
      pending_approval: 'bg-yellow-100 text-yellow-700'
    };
    return (
      <Badge className={statusColors[status] || 'bg-gray-100 text-gray-700'}>
        {status?.replace(/_/g, ' ').toUpperCase()}
      </Badge>
    );
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900"></div></div>;

  return (
    <div className="space-y-6 animate-fade-in" data-testid="adjuster-followup-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Adjuster Follow-Ups</h1>
          <p className="text-slate-500 mt-1">Automated insurance adjuster email follow-up system</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => loadData()}>
            <Clock className="h-4 w-4 mr-2" />
            Refresh
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-4">
        <Card className="bg-yellow-50 border-yellow-200">
          <CardContent className="p-4 text-center">
            <p className="text-sm font-medium text-yellow-700">Pending Approval</p>
            <p className="text-2xl font-bold text-yellow-900">{pendingThreads.length}</p>
          </CardContent>
        </Card>
        <Card className="bg-green-50 border-green-200">
          <CardContent className="p-4 text-center">
            <p className="text-sm font-medium text-green-700">Active Follow-Ups</p>
            <p className="text-2xl font-bold text-green-900">{activeThreads.length}</p>
          </CardContent>
        </Card>
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="p-4 text-center">
            <p className="text-sm font-medium text-blue-700">Total Threads</p>
            <p className="text-2xl font-bold text-blue-900">{pendingThreads.length + activeThreads.length}</p>
          </CardContent>
        </Card>
        <Card className="bg-purple-50 border-purple-200">
          <CardContent className="p-4 text-center">
            <p className="text-sm font-medium text-purple-700">Automation Status</p>
            <p className="text-lg font-bold text-purple-900">ENABLED</p>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="pending">
            Pending Approval ({pendingThreads.length})
          </TabsTrigger>
          <TabsTrigger value="active">
            Active Follow-Ups ({activeThreads.length})
          </TabsTrigger>
        </TabsList>

        {/* Pending Approval Tab */}
        <TabsContent value="pending" className="space-y-4">
          {pendingThreads.length === 0 ? (
            <Card>
              <CardContent className="p-8 text-center text-slate-500">
                <CheckCircle2 className="h-12 w-12 mx-auto mb-3 text-green-500" />
                <p className="font-medium">No pending approvals</p>
                <p className="text-sm mt-1">All qualified emails have been reviewed</p>
              </CardContent>
            </Card>
          ) : (
            pendingThreads.map(thread => (
              <Card key={thread.id} className="border-l-4 border-l-yellow-500">
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-3">
                        <h3 className="text-lg font-semibold text-slate-900">
                          Invoice #{thread.invoice_number}
                        </h3>
                        {getStatusBadge(thread.status)}
                        <Badge variant="outline">{thread.carrier_name}</Badge>
                      </div>

                      <div className="grid grid-cols-2 gap-4 mb-4">
                        <div>
                          <p className="text-xs text-slate-500 uppercase mb-1">Adjuster</p>
                          <p className="font-medium">{thread.adjuster_name}</p>
                          <p className="text-sm text-slate-600">{thread.adjuster_email}</p>
                        </div>
                        <div>
                          <p className="text-xs text-slate-500 uppercase mb-1">Claim Details</p>
                          <p className="text-sm">Claim #: {thread.claim_number}</p>
                          <p className="text-sm">Amount: ${thread.invoice_amount.toLocaleString()}</p>
                        </div>
                        <div>
                          <p className="text-xs text-slate-500 uppercase mb-1">Invoice Date</p>
                          <p className="text-sm">{formatDate(thread.first_contact_date)}</p>
                          <p className="text-xs text-slate-500">
                            {getDaysOutstanding(thread.first_contact_date)} days ago
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-slate-500 uppercase mb-1">Due Date</p>
                          <p className="text-sm">{formatDate(thread.invoice_due_date)}</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  <Separator className="my-4" />

                  <div className="flex gap-2">
                    <Button
                      className="bg-green-600 hover:bg-green-700"
                      onClick={() => approveThread(thread.id)}
                    >
                      <CheckCircle2 className="h-4 w-4 mr-2" />
                      Approve & Activate
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => rejectThread(thread.id)}
                    >
                      <X className="h-4 w-4 mr-2" />
                      Reject
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>

        {/* Active Follow-Ups Tab */}
        <TabsContent value="active" className="space-y-4">
          {activeThreads.length === 0 ? (
            <Card>
              <CardContent className="p-8 text-center text-slate-500">
                <AlertCircle className="h-12 w-12 mx-auto mb-3" />
                <p className="font-medium">No active follow-ups</p>
                <p className="text-sm mt-1">Approve pending threads to start automation</p>
              </CardContent>
            </Card>
          ) : (
            activeThreads.map(thread => (
              <Card key={thread.id} className="border-l-4 border-l-green-500">
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-3">
                        <h3 className="text-lg font-semibold text-slate-900">
                          Invoice #{thread.invoice_number}
                        </h3>
                        {getStatusBadge(thread.status)}
                        <Badge variant="outline">{thread.carrier_name}</Badge>
                      </div>

                      <div className="grid grid-cols-3 gap-4 mb-4">
                        <div>
                          <p className="text-xs text-slate-500 uppercase mb-1">Adjuster</p>
                          <p className="font-medium">{thread.adjuster_name}</p>
                          <p className="text-sm text-slate-600">{thread.adjuster_email}</p>
                        </div>
                        <div>
                          <p className="text-xs text-slate-500 uppercase mb-1">Progress</p>
                          <p className="text-sm">Follow-ups sent: {thread.followup_count}/10</p>
                          <p className="text-sm">Days outstanding: {getDaysOutstanding(thread.first_contact_date)}</p>
                        </div>
                        <div>
                          <p className="text-xs text-slate-500 uppercase mb-1">Next Follow-Up</p>
                          <p className="text-sm font-medium">{formatDate(thread.next_followup_date)}</p>
                          {thread.last_followup_date && (
                            <p className="text-xs text-slate-500">
                              Last sent: {formatDate(thread.last_followup_date)}
                            </p>
                          )}
                        </div>
                      </div>

                      {/* Follow-up history */}
                      {thread.escalation_notes && thread.escalation_notes.length > 0 && (
                        <div className="mb-4">
                          <p className="text-xs text-slate-500 uppercase mb-2">Follow-Up History</p>
                          <div className="flex gap-2 flex-wrap">
                            {thread.escalation_notes.map((note, idx) => (
                              <Badge key={idx} variant="outline" className="text-xs">
                                #{note.followup_number} - {formatDate(note.date)}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </div>

                  <Separator className="my-4" />

                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      onClick={() => sendManualFollowup(thread.id)}
                    >
                      <Send className="h-4 w-4 mr-2" />
                      Send Now
                    </Button>
                    {thread.status === 'active' ? (
                      <Button
                        variant="outline"
                        onClick={() => pauseThread(thread.id)}
                      >
                        <Clock className="h-4 w-4 mr-2" />
                        Pause
                      </Button>
                    ) : (
                      <Button
                        variant="outline"
                        onClick={() => resumeThread(thread.id)}
                      >
                        <CheckCircle2 className="h-4 w-4 mr-2" />
                        Resume
                      </Button>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>
      </Tabs>

      {/* Help Section */}
      <Card className="bg-slate-50 border-slate-200">
        <CardContent className="p-6">
          <div className="flex gap-4">
            <Shield className="h-8 w-8 text-slate-600 flex-shrink-0" />
            <div>
              <h3 className="font-semibold text-slate-900 mb-2">How Adjuster Follow-Ups Work</h3>
              <ul className="text-sm text-slate-600 space-y-1">
                <li>✓ Emails from adjusters are automatically qualified based on domain and keywords</li>
                <li>✓ Qualified emails appear in "Pending Approval" - review and approve to activate</li>
                <li>✓ Approved threads send follow-ups every 3 business days automatically</li>
                <li>✓ System stops when payment received, coverage issued, or claim disputed</li>
                <li>✓ Maximum 10 follow-ups per thread, then escalates internally</li>
                <li>✓ You can manually pause, resume, or send follow-ups at any time</li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

const AIAssistantPage = () => {
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [messageType, setMessageType] = useState('scheduling');
  const [customerName, setCustomerName] = useState('');
  const [selectedJobId, setSelectedJobId] = useState('');
  const [customContext, setCustomContext] = useState('');
  const [generatedMessage, setGeneratedMessage] = useState('');
  const [complianceReport, setComplianceReport] = useState(null);
  const [cashFlowAnalysis, setCashFlowAnalysis] = useState(null);

  useEffect(() => { axios.get(`${API}/jobs`).then(res => setJobs(res.data)).catch(() => {}); }, []);

  const generateMessage = async () => {
    if (!customerName) return toast.error("Please enter a customer name");
    setLoading(true);
    try {
      const res = await axios.post(`${API}/ai/generate-message`, { message_type: messageType, customer_name: customerName, job_id: selectedJobId || null, custom_context: customContext || null });
      setGeneratedMessage(res.data.message);
      toast.success("Message generated!");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to generate message");
    } finally {
      setLoading(false);
    }
  };

  const analyzeCompliance = async () => {
    setLoading(true);
    try {
      const res = await axios.post(`${API}/ai/analyze-compliance`);
      setComplianceReport(res.data);
      toast.success("Compliance analysis complete!");
    } catch (err) {
      toast.error("Failed to analyze compliance");
    } finally {
      setLoading(false);
    }
  };

  const forecastCashFlow = async () => {
    setLoading(true);
    try {
      const res = await axios.post(`${API}/ai/forecast-cashflow`);
      setCashFlowAnalysis(res.data);
      toast.success("Cash flow analysis complete!");
    } catch (err) {
      toast.error("Failed to analyze cash flow");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 animate-fade-in" data-testid="ai-assistant-page">
      <div><h1 className="page-title flex items-center gap-2"><Brain className="w-7 h-7 text-orange-500" />AI Assistant</h1><p className="text-slate-500 mt-1">AI-powered tools for your restoration business</p></div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><MessageSquare className="w-5 h-5 text-orange-500" />Customer Message Generator</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div><Label>Message Type</Label><Select value={messageType} onValueChange={setMessageType}><SelectTrigger><SelectValue /></SelectTrigger><SelectContent><SelectItem value="scheduling">Scheduling Update</SelectItem><SelectItem value="arrival">Arrival Notice</SelectItem><SelectItem value="progress">Progress Update</SelectItem><SelectItem value="payment">Payment Reminder</SelectItem><SelectItem value="custom">Custom Message</SelectItem></SelectContent></Select></div>
            <div><Label>Customer Name</Label><Input value={customerName} onChange={e => setCustomerName(e.target.value)} placeholder="John Smith" /></div>
            <div><Label>Link to Job (optional)</Label><Select value={selectedJobId} onValueChange={setSelectedJobId}><SelectTrigger><SelectValue placeholder="Select a job" /></SelectTrigger><SelectContent>{jobs.map(job => (<SelectItem key={job.id} value={job.id}>{job.title}</SelectItem>))}</SelectContent></Select></div>
            {messageType === 'custom' && <div><Label>Custom Context</Label><Textarea value={customContext} onChange={e => setCustomContext(e.target.value)} placeholder="Describe what the message should be about..." /></div>}
            <Button className="btn-accent w-full" onClick={generateMessage} disabled={loading}>{loading ? "Generating..." : "Generate Message"}</Button>
            {generatedMessage && <div className="p-4 bg-slate-50 rounded-lg"><p className="text-sm font-medium text-slate-600 mb-2">Generated Message:</p><p className="text-slate-900">{generatedMessage}</p><Button variant="outline" size="sm" className="mt-3" onClick={() => { navigator.clipboard.writeText(generatedMessage); toast.success("Copied!"); }}>Copy to Clipboard</Button></div>}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle className="flex items-center gap-2"><AlertCircle className="w-5 h-5 text-orange-500" />Compliance Review</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <Button className="btn-accent w-full" onClick={analyzeCompliance} disabled={loading}>{loading ? "Analyzing..." : "Run Compliance Check"}</Button>
            {complianceReport && <div className="p-4 bg-slate-50 rounded-lg"><p className="text-sm font-medium text-slate-600 mb-2">AI Analysis:</p><p className="text-slate-900 whitespace-pre-wrap text-sm">{complianceReport.analysis}</p></div>}
          </CardContent>
        </Card>

        <Card className="lg:col-span-2">
          <CardHeader><CardTitle className="flex items-center gap-2"><TrendingUp className="w-5 h-5 text-orange-500" />AI Cash Flow Forecast</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <Button className="btn-accent" onClick={forecastCashFlow} disabled={loading}>{loading ? "Analyzing..." : "Generate AI Forecast"}</Button>
            {cashFlowAnalysis && <div className="p-4 bg-slate-50 rounded-lg"><p className="text-sm font-medium text-slate-600 mb-2">AI Insights:</p><p className="text-slate-900 whitespace-pre-wrap text-sm">{cashFlowAnalysis.ai_analysis}</p></div>}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

// Main App
function App() {
  return (
    <AuthProvider>
      <Toaster position="top-right" richColors />
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<ProtectedRoute><Layout><DashboardPage /></Layout></ProtectedRoute>} />
          <Route path="/jobs" element={<ProtectedRoute><Layout><JobsPage /></Layout></ProtectedRoute>} />
          <Route path="/jobs/:jobId" element={<ProtectedRoute><Layout><JobDetailPage /></Layout></ProtectedRoute>} />
          <Route path="/crews" element={<ProtectedRoute><Layout><CrewsPage /></Layout></ProtectedRoute>} />
          <Route path="/daily-logs" element={<ProtectedRoute><Layout><DailyLogsPage /></Layout></ProtectedRoute>} />
          <Route path="/invoices" element={<ProtectedRoute><Layout><InvoicesPage /></Layout></ProtectedRoute>} />
          <Route path="/collections" element={<ProtectedRoute><Layout><CollectionsPage /></Layout></ProtectedRoute>} />
          <Route path="/adjuster-followups" element={<ProtectedRoute><Layout><AdjusterFollowUpPage /></Layout></ProtectedRoute>} />
          <Route path="/work-orders" element={<ProtectedRoute><Layout><WorkOrdersPage /></Layout></ProtectedRoute>} />
          <Route path="/accounting" element={<ProtectedRoute><Layout><AccountingPage /></Layout></ProtectedRoute>} />
          <Route path="/reports" element={<ProtectedRoute><Layout><ReportsPage /></Layout></ProtectedRoute>} />
          <Route path="/ai-assistant" element={<ProtectedRoute><Layout><AIAssistantPage /></Layout></ProtectedRoute>} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
