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

  const metricCards = [
    { label: "Active Jobs", value: stats?.active_jobs || 0, icon: Briefcase, color: "text-blue-600", bg: "bg-blue-50" },
    { label: "Available Crews", value: stats?.available_crews || 0, icon: Users, color: "text-green-600", bg: "bg-green-50" },
    { label: "Revenue", value: `$${(stats?.total_revenue || 0).toLocaleString()}`, icon: TrendingUp, color: "text-emerald-600", bg: "bg-emerald-50" },
    { label: "Outstanding", value: `$${(stats?.outstanding_invoices || 0).toLocaleString()}`, icon: Clock, color: "text-orange-600", bg: "bg-orange-50" },
  ];

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

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {metricCards.map((card, i) => (
          <Card key={i} className="metric-card card-hover" data-testid={`metric-${card.label.toLowerCase().replace(' ', '-')}`}>
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm text-slate-500">{card.label}</p>
                <p className="text-2xl font-bold text-slate-900 mt-1">{card.value}</p>
              </div>
              <div className={`p-2 rounded-lg ${card.bg}`}>
                <card.icon className={`w-5 h-5 ${card.color}`} />
              </div>
            </div>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="section-title">Recent Jobs</CardTitle>
          </CardHeader>
          <CardContent>
            {stats?.recent_jobs?.length > 0 ? (
              <div className="space-y-3">
                {stats.recent_jobs.map((job, i) => (
                  <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-slate-50 hover:bg-slate-100 transition-colors cursor-pointer" onClick={() => navigate(`/jobs/${job.id}`)}>
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-slate-200 flex items-center justify-center">
                        <Briefcase className="w-5 h-5 text-slate-600" />
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
                ))}
              </div>
            ) : (
              <p className="text-slate-500 text-center py-8">No recent jobs. Create your first job to get started!</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="section-title">Quick Stats</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-slate-600">Total Jobs</span>
              <span className="font-semibold">{stats?.total_jobs || 0}</span>
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <span className="text-slate-600">Total Crews</span>
              <span className="font-semibold">{stats?.total_crews || 0}</span>
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
              <span className="text-slate-600">Pending Invoices</span>
              <span className="font-semibold text-orange-600">{stats?.pending_invoices || 0}</span>
            </div>
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
    address: "", scope: "", priority: "medium", status: "pending",
    assigned_crew_id: "", scheduled_date: "", estimated_completion: "", notes: ""
  });
  const navigate = useNavigate();

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
      await axios.post(`${API}/jobs`, formData);
      toast.success("Job created!");
      setDialogOpen(false);
      loadData();
      setFormData({ title: "", customer_name: "", customer_phone: "", customer_email: "", address: "", scope: "", priority: "medium", status: "pending", assigned_crew_id: "", scheduled_date: "", estimated_completion: "", notes: "" });
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to create job");
    }
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900"></div></div>;

  return (
    <div className="space-y-6 animate-fade-in" data-testid="jobs-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Jobs</h1>
          <p className="text-slate-500 mt-1">Manage your restoration jobs</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button className="btn-accent gap-2" data-testid="create-job-btn">
              <Plus className="w-4 h-4" /> New Job
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Create New Job</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Job Title</Label>
                  <Input value={formData.title} onChange={e => setFormData({...formData, title: e.target.value})} placeholder="Water Damage - Kitchen" required data-testid="job-title-input" />
                </div>
                <div>
                  <Label>Customer Name</Label>
                  <Input value={formData.customer_name} onChange={e => setFormData({...formData, customer_name: e.target.value})} placeholder="John Smith" required data-testid="job-customer-input" />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Phone</Label>
                  <Input value={formData.customer_phone} onChange={e => setFormData({...formData, customer_phone: e.target.value})} placeholder="(555) 123-4567" required data-testid="job-phone-input" />
                </div>
                <div>
                  <Label>Email</Label>
                  <Input type="email" value={formData.customer_email} onChange={e => setFormData({...formData, customer_email: e.target.value})} placeholder="john@email.com" data-testid="job-email-input" />
                </div>
              </div>
              <div>
                <Label>Address</Label>
                <Input value={formData.address} onChange={e => setFormData({...formData, address: e.target.value})} placeholder="123 Main St, City, ST 12345" required data-testid="job-address-input" />
              </div>
              <div>
                <Label>Scope of Work</Label>
                <Textarea value={formData.scope} onChange={e => setFormData({...formData, scope: e.target.value})} placeholder="Describe the restoration work needed..." rows={3} required data-testid="job-scope-input" />
              </div>
              <div className="grid grid-cols-3 gap-4">
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
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label>Scheduled Date</Label>
                  <Input type="date" value={formData.scheduled_date} onChange={e => setFormData({...formData, scheduled_date: e.target.value})} data-testid="job-date-input" />
                </div>
                <div>
                  <Label>Est. Completion</Label>
                  <Input type="date" value={formData.estimated_completion} onChange={e => setFormData({...formData, estimated_completion: e.target.value})} />
                </div>
              </div>
              <div>
                <Label>Notes</Label>
                <Textarea value={formData.notes} onChange={e => setFormData({...formData, notes: e.target.value})} placeholder="Additional notes..." rows={2} data-testid="job-notes-input" />
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>Cancel</Button>
                <Button type="submit" className="btn-accent" data-testid="job-submit-btn">Create Job</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {jobs.length === 0 ? (
        <Card className="text-center py-12">
          <Briefcase className="w-12 h-12 text-slate-300 mx-auto mb-4" />
          <p className="text-slate-500">No jobs yet. Create your first job to get started!</p>
        </Card>
      ) : (
        <div className="grid gap-4">
          {jobs.map(job => (
            <Card key={job.id} className="card-hover cursor-pointer" onClick={() => navigate(`/jobs/${job.id}`)} data-testid={`job-card-${job.id}`}>
              <CardContent className="p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <h3 className="font-semibold text-slate-900 truncate">{job.title}</h3>
                      <Badge className={`priority-${job.priority}`}>{job.priority}</Badge>
                      <Badge className={`status-${job.status}`}>{job.status?.replace('_', ' ')}</Badge>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-slate-600">
                      <span className="flex items-center gap-1"><User className="w-3 h-3" /> {job.customer_name}</span>
                      <span className="flex items-center gap-1"><Phone className="w-3 h-3" /> {job.customer_phone}</span>
                    </div>
                    <p className="text-sm text-slate-500 mt-1 flex items-center gap-1">
                      <MapPin className="w-3 h-3" /> {job.address}
                    </p>
                    {job.scheduled_date && (
                      <p className="text-sm text-slate-500 mt-1 flex items-center gap-1">
                        <Calendar className="w-3 h-3" /> Scheduled: {job.scheduled_date}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    {job.total_amount > 0 && (
                      <div className="text-right">
                        <p className="text-lg font-bold text-slate-900">${job.total_amount?.toLocaleString()}</p>
                        <p className="text-xs text-slate-500">Total Value</p>
                      </div>
                    )}
                    <ChevronRight className="w-5 h-5 text-slate-400" />
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
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
          <Route path="/invoices" element={<ProtectedRoute><Layout><InvoicesPage /></Layout></ProtectedRoute>} />
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
