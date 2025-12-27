import { useState, useEffect, createContext, useContext } from "react";
import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from "react-router-dom";
import axios from "axios";
import { Toaster, toast } from "sonner";
import {
  LayoutDashboard, Briefcase, Users, FileText, ClipboardList,
  DollarSign, BarChart3, MessageSquare, LogOut, Menu, X,
  Plus, Search, ChevronRight, TrendingUp, TrendingDown,
  Clock, CheckCircle2, AlertCircle, Download, Send, Brain
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
        .catch(() => {
          localStorage.removeItem("token");
          setToken(null);
        })
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

// Protected Route
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
    { path: "/invoices", icon: FileText, label: "Invoices" },
    { path: "/work-orders", icon: ClipboardList, label: "Work Orders" },
    { path: "/accounting", icon: DollarSign, label: "Accounting" },
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
                className={`sidebar-link w-full text-left ${location.pathname === item.path ? 'active' : ''}`}
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

// Layout Component
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

// Auth Pages
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
      if (isRegister) {
        await register(email, password, name);
      } else {
        await login(email, password);
      }
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
            <CardDescription className="text-slate-400">
              {isRegister ? "Get started with RestorationOS" : "Welcome back to your dashboard"}
            </CardDescription>
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

  useEffect(() => {
    axios.get(`${API}/reports/dashboard`)
      .then(res => setStats(res.data))
      .catch(err => toast.error("Failed to load dashboard"))
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
        <Button className="btn-accent gap-2" onClick={() => window.location.href = '/jobs'} data-testid="new-job-btn">
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
                  <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-slate-50 hover:bg-slate-100 transition-colors">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-slate-200 flex items-center justify-center">
                        <Briefcase className="w-5 h-5 text-slate-600" />
                      </div>
                      <div>
                        <p className="font-medium text-slate-900">{job.title}</p>
                        <p className="text-sm text-slate-500">{job.customer_name}</p>
                      </div>
                    </div>
                    <Badge className={`status-${job.status}`}>{job.status}</Badge>
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

// Jobs Page
const JobsPage = () => {
  const [jobs, setJobs] = useState([]);
  const [crews, setCrews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedJob, setSelectedJob] = useState(null);
  const [formData, setFormData] = useState({
    title: "", customer_name: "", customer_phone: "", customer_email: "",
    address: "", scope: "", priority: "medium", status: "pending",
    assigned_crew_id: "", scheduled_date: "", notes: ""
  });

  const loadData = async () => {
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
  };

  useEffect(() => { loadData(); }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (selectedJob) {
        await axios.put(`${API}/jobs/${selectedJob.id}`, formData);
        toast.success("Job updated!");
      } else {
        await axios.post(`${API}/jobs`, formData);
        toast.success("Job created!");
      }
      setDialogOpen(false);
      loadData();
      resetForm();
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to save job");
    }
  };

  const handleEdit = (job) => {
    setSelectedJob(job);
    setFormData({
      title: job.title,
      customer_name: job.customer_name,
      customer_phone: job.customer_phone,
      customer_email: job.customer_email || "",
      address: job.address,
      scope: job.scope,
      priority: job.priority,
      status: job.status,
      assigned_crew_id: job.assigned_crew_id || "",
      scheduled_date: job.scheduled_date || "",
      notes: job.notes || ""
    });
    setDialogOpen(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm("Delete this job?")) return;
    try {
      await axios.delete(`${API}/jobs/${id}`);
      toast.success("Job deleted");
      loadData();
    } catch (err) {
      toast.error("Failed to delete");
    }
  };

  const resetForm = () => {
    setSelectedJob(null);
    setFormData({
      title: "", customer_name: "", customer_phone: "", customer_email: "",
      address: "", scope: "", priority: "medium", status: "pending",
      assigned_crew_id: "", scheduled_date: "", notes: ""
    });
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900"></div></div>;

  return (
    <div className="space-y-6 animate-fade-in" data-testid="jobs-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Jobs</h1>
          <p className="text-slate-500 mt-1">Manage your restoration jobs</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={(open) => { setDialogOpen(open); if (!open) resetForm(); }}>
          <DialogTrigger asChild>
            <Button className="btn-accent gap-2" data-testid="create-job-btn">
              <Plus className="w-4 h-4" /> New Job
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>{selectedJob ? "Edit Job" : "Create New Job"}</DialogTitle>
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
              </div>
              <div>
                <Label>Notes</Label>
                <Textarea value={formData.notes} onChange={e => setFormData({...formData, notes: e.target.value})} placeholder="Additional notes..." rows={2} data-testid="job-notes-input" />
              </div>
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => { setDialogOpen(false); resetForm(); }}>Cancel</Button>
                <Button type="submit" className="btn-accent" data-testid="job-submit-btn">{selectedJob ? "Update" : "Create"} Job</Button>
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
            <Card key={job.id} className="card-hover" data-testid={`job-card-${job.id}`}>
              <CardContent className="p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-2">
                      <h3 className="font-semibold text-slate-900 truncate">{job.title}</h3>
                      <Badge className={`priority-${job.priority}`}>{job.priority}</Badge>
                      <Badge className={`status-${job.status}`}>{job.status.replace('_', ' ')}</Badge>
                    </div>
                    <p className="text-sm text-slate-600 mb-1">{job.customer_name} • {job.customer_phone}</p>
                    <p className="text-sm text-slate-500">{job.address}</p>
                    {job.scheduled_date && (
                      <p className="text-sm text-slate-500 mt-1 flex items-center gap-1">
                        <Clock className="w-3 h-3" /> Scheduled: {job.scheduled_date}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm" onClick={() => handleEdit(job)} data-testid={`edit-job-${job.id}`}>Edit</Button>
                    <Button variant="outline" size="sm" className="text-red-600 hover:text-red-700" onClick={() => handleDelete(job.id)} data-testid={`delete-job-${job.id}`}>Delete</Button>
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

// Crews Page
const CrewsPage = () => {
  const [crews, setCrews] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedCrew, setSelectedCrew] = useState(null);
  const [formData, setFormData] = useState({
    name: "", specialty: "general", status: "available", members: []
  });
  const [newMember, setNewMember] = useState({ name: "", role: "", phone: "", hourly_rate: 0 });

  const loadCrews = async () => {
    try {
      const res = await axios.get(`${API}/crews`);
      setCrews(res.data);
    } catch (err) {
      toast.error("Failed to load crews");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadCrews(); }, []);

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
    setFormData({
      name: crew.name,
      specialty: crew.specialty,
      status: crew.status,
      members: crew.members || []
    });
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
                    <SelectTrigger data-testid="crew-specialty-select"><SelectValue /></SelectTrigger>
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
                    <SelectTrigger data-testid="crew-status-select"><SelectValue /></SelectTrigger>
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
                  <Input placeholder="Name" value={newMember.name} onChange={e => setNewMember({...newMember, name: e.target.value})} data-testid="member-name-input" />
                  <Input placeholder="Role" value={newMember.role} onChange={e => setNewMember({...newMember, role: e.target.value})} data-testid="member-role-input" />
                  <Input placeholder="Phone" value={newMember.phone} onChange={e => setNewMember({...newMember, phone: e.target.value})} />
                  <div className="flex gap-1">
                    <Input type="number" placeholder="Rate" value={newMember.hourly_rate} onChange={e => setNewMember({...newMember, hourly_rate: e.target.value})} />
                    <Button type="button" onClick={addMember} size="icon" data-testid="add-member-btn"><Plus className="w-4 h-4" /></Button>
                  </div>
                </div>
              </div>

              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => { setDialogOpen(false); resetForm(); }}>Cancel</Button>
                <Button type="submit" className="btn-accent" data-testid="crew-submit-btn">{selectedCrew ? "Update" : "Create"} Crew</Button>
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
                  <div className="flex -space-x-2 mb-3">
                    {crew.members.slice(0, 4).map((m, i) => (
                      <div key={i} className="w-8 h-8 rounded-full bg-slate-200 border-2 border-white flex items-center justify-center text-xs font-medium">
                        {m.name.charAt(0)}
                      </div>
                    ))}
                    {crew.members.length > 4 && (
                      <div className="w-8 h-8 rounded-full bg-slate-100 border-2 border-white flex items-center justify-center text-xs text-slate-500">
                        +{crew.members.length - 4}
                      </div>
                    )}
                  </div>
                )}
                <Button variant="outline" size="sm" className="w-full" onClick={() => handleEdit(crew)} data-testid={`edit-crew-${crew.id}`}>
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

// Invoices Page
const InvoicesPage = () => {
  const [invoices, setInvoices] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({ job_id: "", due_date: "", notes: "", tax_rate: 8.25 });

  const loadData = async () => {
    try {
      const [invRes, jobsRes] = await Promise.all([
        axios.get(`${API}/invoices`),
        axios.get(`${API}/jobs`)
      ]);
      setInvoices(invRes.data);
      setJobs(jobsRes.data);
    } catch (err) {
      toast.error("Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/invoices`, formData);
      toast.success("Invoice created!");
      setDialogOpen(false);
      loadData();
      setFormData({ job_id: "", due_date: "", notes: "", tax_rate: 8.25 });
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to create invoice");
    }
  };

  const downloadPDF = async (id, number) => {
    try {
      const res = await axios.get(`${API}/invoices/${id}/pdf`, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([res.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `${number}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      toast.success("PDF downloaded!");
    } catch (err) {
      toast.error("Failed to download PDF");
    }
  };

  const updateStatus = async (id, status) => {
    try {
      await axios.put(`${API}/invoices/${id}/status?status=${status}`);
      toast.success("Status updated!");
      loadData();
    } catch (err) {
      toast.error("Failed to update status");
    }
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900"></div></div>;

  return (
    <div className="space-y-6 animate-fade-in" data-testid="invoices-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Invoices</h1>
          <p className="text-slate-500 mt-1">Manage and track your invoices</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => window.open(`${API}/export/quickbooks?data_type=invoices`, '_blank')} data-testid="export-invoices-btn">
            <Download className="w-4 h-4 mr-2" /> Export CSV
          </Button>
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button className="btn-accent gap-2" data-testid="create-invoice-btn">
                <Plus className="w-4 h-4" /> New Invoice
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create Invoice</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleCreate} className="space-y-4">
                <div>
                  <Label>Select Job</Label>
                  <Select value={formData.job_id} onValueChange={v => setFormData({...formData, job_id: v})}>
                    <SelectTrigger data-testid="invoice-job-select"><SelectValue placeholder="Select a job" /></SelectTrigger>
                    <SelectContent>
                      {jobs.map(job => (
                        <SelectItem key={job.id} value={job.id}>{job.title} - {job.customer_name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Due Date</Label>
                    <Input type="date" value={formData.due_date} onChange={e => setFormData({...formData, due_date: e.target.value})} required data-testid="invoice-due-date" />
                  </div>
                  <div>
                    <Label>Tax Rate (%)</Label>
                    <Input type="number" step="0.01" value={formData.tax_rate} onChange={e => setFormData({...formData, tax_rate: parseFloat(e.target.value)})} data-testid="invoice-tax-rate" />
                  </div>
                </div>
                <div>
                  <Label>Notes</Label>
                  <Textarea value={formData.notes} onChange={e => setFormData({...formData, notes: e.target.value})} placeholder="Invoice notes..." data-testid="invoice-notes" />
                </div>
                <DialogFooter>
                  <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>Cancel</Button>
                  <Button type="submit" className="btn-accent" data-testid="invoice-submit-btn">Create Invoice</Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {invoices.length === 0 ? (
        <Card className="text-center py-12">
          <FileText className="w-12 h-12 text-slate-300 mx-auto mb-4" />
          <p className="text-slate-500">No invoices yet. Create an invoice from a job to get started!</p>
        </Card>
      ) : (
        <div className="overflow-x-auto">
          <table className="data-table">
            <thead>
              <tr>
                <th>Invoice #</th>
                <th>Customer</th>
                <th>Amount</th>
                <th>Due Date</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {invoices.map(inv => (
                <tr key={inv.id} data-testid={`invoice-row-${inv.id}`}>
                  <td className="font-mono text-sm">{inv.invoice_number}</td>
                  <td>{inv.customer_name}</td>
                  <td className="font-semibold">${inv.total.toLocaleString()}</td>
                  <td>{inv.due_date}</td>
                  <td>
                    <Select value={inv.status} onValueChange={v => updateStatus(inv.id, v)}>
                      <SelectTrigger className="w-28 h-8">
                        <Badge className={`status-${inv.status}`}>{inv.status}</Badge>
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="draft">Draft</SelectItem>
                        <SelectItem value="sent">Sent</SelectItem>
                        <SelectItem value="paid">Paid</SelectItem>
                        <SelectItem value="overdue">Overdue</SelectItem>
                      </SelectContent>
                    </Select>
                  </td>
                  <td>
                    <Button variant="ghost" size="sm" onClick={() => downloadPDF(inv.id, inv.invoice_number)} data-testid={`download-invoice-${inv.id}`}>
                      <Download className="w-4 h-4" />
                    </Button>
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

// Work Orders Page
const WorkOrdersPage = () => {
  const [workOrders, setWorkOrders] = useState([]);
  const [jobs, setJobs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({ job_id: "", tasks: [], materials_needed: [], notes: "" });
  const [newTask, setNewTask] = useState("");
  const [newMaterial, setNewMaterial] = useState("");

  const loadData = async () => {
    try {
      const [woRes, jobsRes] = await Promise.all([
        axios.get(`${API}/work-orders`),
        axios.get(`${API}/jobs`)
      ]);
      setWorkOrders(woRes.data);
      setJobs(jobsRes.data);
    } catch (err) {
      toast.error("Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      const payload = {
        ...formData,
        tasks: formData.tasks.map(t => ({ description: t, is_completed: false }))
      };
      await axios.post(`${API}/work-orders`, payload);
      toast.success("Work order created!");
      setDialogOpen(false);
      loadData();
      setFormData({ job_id: "", tasks: [], materials_needed: [], notes: "" });
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to create work order");
    }
  };

  const toggleTask = async (woId, tasks, taskIndex) => {
    const updated = tasks.map((t, i) => i === taskIndex ? { ...t, is_completed: !t.is_completed } : t);
    try {
      await axios.put(`${API}/work-orders/${woId}/tasks`, updated);
      toast.success("Task updated!");
      loadData();
    } catch (err) {
      toast.error("Failed to update task");
    }
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900"></div></div>;

  return (
    <div className="space-y-6 animate-fade-in" data-testid="work-orders-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Work Orders</h1>
          <p className="text-slate-500 mt-1">Track tasks and materials for jobs</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button className="btn-accent gap-2" data-testid="create-work-order-btn">
              <Plus className="w-4 h-4" /> New Work Order
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-xl">
            <DialogHeader>
              <DialogTitle>Create Work Order</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleCreate} className="space-y-4">
              <div>
                <Label>Select Job</Label>
                <Select value={formData.job_id} onValueChange={v => setFormData({...formData, job_id: v})}>
                  <SelectTrigger data-testid="wo-job-select"><SelectValue placeholder="Select a job" /></SelectTrigger>
                  <SelectContent>
                    {jobs.map(job => (
                      <SelectItem key={job.id} value={job.id}>{job.title} - {job.customer_name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label>Tasks</Label>
                <div className="space-y-2 mb-2">
                  {formData.tasks.map((t, i) => (
                    <div key={i} className="flex items-center gap-2 p-2 bg-slate-50 rounded">
                      <span className="flex-1">{t}</span>
                      <Button type="button" variant="ghost" size="sm" onClick={() => setFormData({...formData, tasks: formData.tasks.filter((_, idx) => idx !== i)})} className="text-red-500">
                        <X className="w-4 h-4" />
                      </Button>
                    </div>
                  ))}
                </div>
                <div className="flex gap-2">
                  <Input placeholder="Add task..." value={newTask} onChange={e => setNewTask(e.target.value)} data-testid="wo-task-input" />
                  <Button type="button" onClick={() => { if (newTask) { setFormData({...formData, tasks: [...formData.tasks, newTask]}); setNewTask(""); }}} data-testid="add-task-btn">Add</Button>
                </div>
              </div>

              <div>
                <Label>Materials Needed</Label>
                <div className="flex flex-wrap gap-2 mb-2">
                  {formData.materials_needed.map((m, i) => (
                    <Badge key={i} variant="secondary" className="gap-1">
                      {m}
                      <X className="w-3 h-3 cursor-pointer" onClick={() => setFormData({...formData, materials_needed: formData.materials_needed.filter((_, idx) => idx !== i)})} />
                    </Badge>
                  ))}
                </div>
                <div className="flex gap-2">
                  <Input placeholder="Add material..." value={newMaterial} onChange={e => setNewMaterial(e.target.value)} data-testid="wo-material-input" />
                  <Button type="button" onClick={() => { if (newMaterial) { setFormData({...formData, materials_needed: [...formData.materials_needed, newMaterial]}); setNewMaterial(""); }}} data-testid="add-material-btn">Add</Button>
                </div>
              </div>

              <div>
                <Label>Notes</Label>
                <Textarea value={formData.notes} onChange={e => setFormData({...formData, notes: e.target.value})} placeholder="Additional notes..." data-testid="wo-notes" />
              </div>

              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>Cancel</Button>
                <Button type="submit" className="btn-accent" data-testid="wo-submit-btn">Create Work Order</Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {workOrders.length === 0 ? (
        <Card className="text-center py-12">
          <ClipboardList className="w-12 h-12 text-slate-300 mx-auto mb-4" />
          <p className="text-slate-500">No work orders yet. Create one to track job tasks!</p>
        </Card>
      ) : (
        <div className="grid gap-4">
          {workOrders.map(wo => (
            <Card key={wo.id} data-testid={`work-order-${wo.id}`}>
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
                  {wo.tasks.map((task, i) => (
                    <div key={i} className="flex items-center gap-3 p-2 rounded hover:bg-slate-50 cursor-pointer" onClick={() => toggleTask(wo.id, wo.tasks, i)}>
                      <div className={`w-5 h-5 rounded border-2 flex items-center justify-center ${task.is_completed ? 'bg-green-500 border-green-500' : 'border-slate-300'}`}>
                        {task.is_completed && <CheckCircle2 className="w-4 h-4 text-white" />}
                      </div>
                      <span className={task.is_completed ? 'line-through text-slate-400' : ''}>{task.description}</span>
                    </div>
                  ))}
                </div>
                {wo.materials_needed?.length > 0 && (
                  <div className="mt-4 pt-4 border-t">
                    <p className="text-sm font-medium text-slate-600 mb-2">Materials Needed:</p>
                    <div className="flex flex-wrap gap-2">
                      {wo.materials_needed.map((m, i) => (
                        <Badge key={i} variant="outline">{m}</Badge>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
};

// Accounting Page
const AccountingPage = () => {
  const [expenses, setExpenses] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expenseDialogOpen, setExpenseDialogOpen] = useState(false);
  const [expenseForm, setExpenseForm] = useState({
    description: "", amount: 0, category: "materials", vendor: "", date: "", is_taxable: false
  });

  const loadData = async () => {
    try {
      const [expRes, txRes] = await Promise.all([
        axios.get(`${API}/expenses`),
        axios.get(`${API}/transactions`)
      ]);
      setExpenses(expRes.data);
      setTransactions(txRes.data);
    } catch (err) {
      toast.error("Failed to load data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadData(); }, []);

  const handleAddExpense = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/expenses`, { ...expenseForm, amount: parseFloat(expenseForm.amount) });
      toast.success("Expense added!");
      setExpenseDialogOpen(false);
      loadData();
      setExpenseForm({ description: "", amount: 0, category: "materials", vendor: "", date: "", is_taxable: false });
    } catch (err) {
      toast.error("Failed to add expense");
    }
  };

  if (loading) return <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900"></div></div>;

  return (
    <div className="space-y-6 animate-fade-in" data-testid="accounting-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Accounting</h1>
          <p className="text-slate-500 mt-1">Manage expenses and transactions</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => window.open(`${API}/export/quickbooks?data_type=expenses`, '_blank')} data-testid="export-expenses-btn">
            <Download className="w-4 h-4 mr-2" /> Export CSV
          </Button>
          <Dialog open={expenseDialogOpen} onOpenChange={setExpenseDialogOpen}>
            <DialogTrigger asChild>
              <Button className="btn-accent gap-2" data-testid="add-expense-btn">
                <Plus className="w-4 h-4" /> Add Expense
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Add Expense</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleAddExpense} className="space-y-4">
                <div>
                  <Label>Description</Label>
                  <Input value={expenseForm.description} onChange={e => setExpenseForm({...expenseForm, description: e.target.value})} placeholder="Expense description" required data-testid="expense-description" />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label>Amount</Label>
                    <Input type="number" step="0.01" value={expenseForm.amount} onChange={e => setExpenseForm({...expenseForm, amount: e.target.value})} required data-testid="expense-amount" />
                  </div>
                  <div>
                    <Label>Category</Label>
                    <Select value={expenseForm.category} onValueChange={v => setExpenseForm({...expenseForm, category: v})}>
                      <SelectTrigger data-testid="expense-category"><SelectValue /></SelectTrigger>
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
                    <Input value={expenseForm.vendor} onChange={e => setExpenseForm({...expenseForm, vendor: e.target.value})} placeholder="Vendor name" data-testid="expense-vendor" />
                  </div>
                  <div>
                    <Label>Date</Label>
                    <Input type="date" value={expenseForm.date} onChange={e => setExpenseForm({...expenseForm, date: e.target.value})} required data-testid="expense-date" />
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <input type="checkbox" id="taxable" checked={expenseForm.is_taxable} onChange={e => setExpenseForm({...expenseForm, is_taxable: e.target.checked})} />
                  <Label htmlFor="taxable">Taxable expense</Label>
                </div>
                <DialogFooter>
                  <Button type="button" variant="outline" onClick={() => setExpenseDialogOpen(false)}>Cancel</Button>
                  <Button type="submit" className="btn-accent" data-testid="expense-submit-btn">Add Expense</Button>
                </DialogFooter>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      <Tabs defaultValue="expenses">
        <TabsList>
          <TabsTrigger value="expenses" data-testid="expenses-tab">Expenses</TabsTrigger>
          <TabsTrigger value="transactions" data-testid="transactions-tab">Transactions</TabsTrigger>
        </TabsList>

        <TabsContent value="expenses" className="mt-4">
          {expenses.length === 0 ? (
            <Card className="text-center py-12">
              <DollarSign className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-500">No expenses recorded yet.</p>
            </Card>
          ) : (
            <div className="overflow-x-auto">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Description</th>
                    <th>Category</th>
                    <th>Vendor</th>
                    <th>Amount</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {expenses.map(exp => (
                    <tr key={exp.id}>
                      <td>{exp.date}</td>
                      <td>{exp.description}</td>
                      <td><Badge variant="outline" className="capitalize">{exp.category}</Badge></td>
                      <td>{exp.vendor || '-'}</td>
                      <td className="font-semibold">${exp.amount.toLocaleString()}</td>
                      <td><Badge className={exp.status === 'approved' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}>{exp.status}</Badge></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </TabsContent>

        <TabsContent value="transactions" className="mt-4">
          {transactions.length === 0 ? (
            <Card className="text-center py-12">
              <DollarSign className="w-12 h-12 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-500">No transactions recorded yet.</p>
            </Card>
          ) : (
            <div className="space-y-3">
              {transactions.map(tx => (
                <Card key={tx.id} className="p-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium">{tx.description}</p>
                      <p className="text-sm text-slate-500">{tx.date}</p>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className={`font-semibold ${tx.transaction_type === 'income' ? 'text-green-600' : 'text-red-600'}`}>
                        {tx.transaction_type === 'income' ? '+' : '-'}${tx.amount.toLocaleString()}
                      </span>
                      <Badge variant={tx.is_matched ? 'default' : 'outline'}>
                        {tx.is_matched ? 'Matched' : 'Unmatched'}
                      </Badge>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

// Reports Page
const ReportsPage = () => {
  const [activeReport, setActiveReport] = useState('profit-loss');
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(false);

  const loadReport = async (type) => {
    setLoading(true);
    setActiveReport(type);
    try {
      const endpoints = {
        'profit-loss': '/reports/profit-loss',
        'tax-summary': '/reports/tax-summary',
        'cash-flow': '/reports/cash-flow-forecast'
      };
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
      <div>
        <h1 className="page-title">Financial Reports</h1>
        <p className="text-slate-500 mt-1">View financial summaries and forecasts</p>
      </div>

      <div className="flex gap-2">
        {[
          { id: 'profit-loss', label: 'Profit & Loss' },
          { id: 'tax-summary', label: 'Tax Summary' },
          { id: 'cash-flow', label: 'Cash Flow Forecast' }
        ].map(report => (
          <Button
            key={report.id}
            variant={activeReport === report.id ? 'default' : 'outline'}
            onClick={() => loadReport(report.id)}
            data-testid={`report-${report.id}`}
          >
            {report.label}
          </Button>
        ))}
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-64"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900"></div></div>
      ) : reportData && (
        <Card>
          <CardHeader>
            <CardTitle className="capitalize">{activeReport.replace('-', ' ')}</CardTitle>
          </CardHeader>
          <CardContent>
            {activeReport === 'profit-loss' && (
              <div className="space-y-4">
                <div className="grid grid-cols-3 gap-4">
                  <div className="p-4 bg-green-50 rounded-lg">
                    <p className="text-sm text-green-600">Total Revenue</p>
                    <p className="text-2xl font-bold text-green-700">${reportData.total_revenue?.toLocaleString() || 0}</p>
                  </div>
                  <div className="p-4 bg-red-50 rounded-lg">
                    <p className="text-sm text-red-600">Total Expenses</p>
                    <p className="text-2xl font-bold text-red-700">${reportData.total_expenses?.toLocaleString() || 0}</p>
                  </div>
                  <div className={`p-4 rounded-lg ${reportData.net_profit >= 0 ? 'bg-emerald-50' : 'bg-red-50'}`}>
                    <p className={`text-sm ${reportData.net_profit >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>Net Profit</p>
                    <p className={`text-2xl font-bold ${reportData.net_profit >= 0 ? 'text-emerald-700' : 'text-red-700'}`}>${reportData.net_profit?.toLocaleString() || 0}</p>
                  </div>
                </div>
                {reportData.expenses_by_category && Object.keys(reportData.expenses_by_category).length > 0 && (
                  <div className="mt-6">
                    <h4 className="font-semibold mb-3">Expenses by Category</h4>
                    <div className="space-y-2">
                      {Object.entries(reportData.expenses_by_category).map(([cat, amount]) => (
                        <div key={cat} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                          <span className="capitalize">{cat}</span>
                          <span className="font-semibold">${amount.toLocaleString()}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {activeReport === 'tax-summary' && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-blue-50 rounded-lg">
                    <p className="text-sm text-blue-600">Sales Tax Collected</p>
                    <p className="text-2xl font-bold text-blue-700">${reportData.sales_tax_collected?.toLocaleString() || 0}</p>
                  </div>
                  <div className="p-4 bg-slate-50 rounded-lg">
                    <p className="text-sm text-slate-600">Taxable Revenue</p>
                    <p className="text-2xl font-bold text-slate-700">${reportData.taxable_revenue?.toLocaleString() || 0}</p>
                  </div>
                  <div className="p-4 bg-orange-50 rounded-lg">
                    <p className="text-sm text-orange-600">Taxable Expenses</p>
                    <p className="text-2xl font-bold text-orange-700">${reportData.taxable_expenses?.toLocaleString() || 0}</p>
                  </div>
                  <div className="p-4 bg-green-50 rounded-lg">
                    <p className="text-sm text-green-600">Non-Taxable Expenses</p>
                    <p className="text-2xl font-bold text-green-700">${reportData.non_taxable_expenses?.toLocaleString() || 0}</p>
                  </div>
                </div>
              </div>
            )}

            {activeReport === 'cash-flow' && reportData.forecasts && (
              <div className="space-y-4">
                <div className="p-4 bg-slate-50 rounded-lg mb-4">
                  <p className="text-sm text-slate-600">Outstanding Invoices</p>
                  <p className="text-2xl font-bold text-slate-700">${reportData.outstanding_invoices_total?.toLocaleString() || 0}</p>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  {reportData.forecasts.map((f, i) => (
                    <Card key={i} className="p-4">
                      <h4 className="font-semibold text-slate-900 mb-3">{f.period}</h4>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-slate-500">Expected Income</span>
                          <span className="text-green-600 font-medium">${f.expected_income?.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-slate-500">Expected Expenses</span>
                          <span className="text-red-600 font-medium">${f.expected_expenses?.toLocaleString()}</span>
                        </div>
                        <Separator />
                        <div className="flex justify-between">
                          <span className="font-medium">Net Cash Flow</span>
                          <span className={`font-bold ${f.net_cash_flow >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            ${f.net_cash_flow?.toLocaleString()}
                          </span>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};

// AI Assistant Page
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

  useEffect(() => {
    axios.get(`${API}/jobs`).then(res => setJobs(res.data)).catch(() => {});
  }, []);

  const generateMessage = async () => {
    if (!customerName) {
      toast.error("Please enter a customer name");
      return;
    }
    setLoading(true);
    try {
      const res = await axios.post(`${API}/ai/generate-message`, {
        message_type: messageType,
        customer_name: customerName,
        job_id: selectedJobId || null,
        custom_context: customContext || null
      });
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
      <div>
        <h1 className="page-title flex items-center gap-2">
          <Brain className="w-7 h-7 text-orange-500" />
          AI Assistant
        </h1>
        <p className="text-slate-500 mt-1">AI-powered tools for your restoration business</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Message Generator */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageSquare className="w-5 h-5 text-orange-500" />
              Customer Message Generator
            </CardTitle>
            <CardDescription>Generate professional customer communications</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <Label>Message Type</Label>
              <Select value={messageType} onValueChange={setMessageType}>
                <SelectTrigger data-testid="ai-message-type"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="scheduling">Scheduling Update</SelectItem>
                  <SelectItem value="arrival">Arrival Notice</SelectItem>
                  <SelectItem value="progress">Progress Update</SelectItem>
                  <SelectItem value="payment">Payment Reminder</SelectItem>
                  <SelectItem value="custom">Custom Message</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Customer Name</Label>
              <Input value={customerName} onChange={e => setCustomerName(e.target.value)} placeholder="John Smith" data-testid="ai-customer-name" />
            </div>
            <div>
              <Label>Link to Job (optional)</Label>
              <Select value={selectedJobId} onValueChange={setSelectedJobId}>
                <SelectTrigger data-testid="ai-job-select"><SelectValue placeholder="Select a job" /></SelectTrigger>
                <SelectContent>
                  {jobs.map(job => (
                    <SelectItem key={job.id} value={job.id}>{job.title}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {messageType === 'custom' && (
              <div>
                <Label>Custom Context</Label>
                <Textarea value={customContext} onChange={e => setCustomContext(e.target.value)} placeholder="Describe what the message should be about..." data-testid="ai-custom-context" />
              </div>
            )}
            <Button className="btn-accent w-full" onClick={generateMessage} disabled={loading} data-testid="generate-message-btn">
              {loading ? "Generating..." : "Generate Message"}
            </Button>
            {generatedMessage && (
              <div className="p-4 bg-slate-50 rounded-lg">
                <p className="text-sm font-medium text-slate-600 mb-2">Generated Message:</p>
                <p className="text-slate-900">{generatedMessage}</p>
                <Button variant="outline" size="sm" className="mt-3" onClick={() => { navigator.clipboard.writeText(generatedMessage); toast.success("Copied!"); }}>
                  Copy to Clipboard
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Compliance Analyzer */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-orange-500" />
              Compliance Review
            </CardTitle>
            <CardDescription>AI analysis of financial activity for issues</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button className="btn-accent w-full" onClick={analyzeCompliance} disabled={loading} data-testid="analyze-compliance-btn">
              {loading ? "Analyzing..." : "Run Compliance Check"}
            </Button>
            {complianceReport && (
              <div className="space-y-4">
                <div className="p-4 bg-slate-50 rounded-lg">
                  <p className="text-sm font-medium text-slate-600 mb-2">AI Analysis:</p>
                  <p className="text-slate-900 whitespace-pre-wrap">{complianceReport.analysis}</p>
                </div>
                {complianceReport.potential_duplicates?.length > 0 && (
                  <div className="p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                    <p className="text-sm font-medium text-yellow-700 mb-1">Potential Duplicates Found:</p>
                    <ul className="text-sm text-yellow-600 list-disc list-inside">
                      {complianceReport.potential_duplicates.map((d, i) => (
                        <li key={i}>{d}</li>
                      ))}
                    </ul>
                  </div>
                )}
                {complianceReport.action_items?.filter(Boolean).length > 0 && (
                  <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
                    <p className="text-sm font-medium text-blue-700 mb-1">Action Items:</p>
                    <ul className="text-sm text-blue-600 list-disc list-inside">
                      {complianceReport.action_items.filter(Boolean).map((a, i) => (
                        <li key={i}>{a}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Cash Flow Forecaster */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-orange-500" />
              AI Cash Flow Forecast
            </CardTitle>
            <CardDescription>AI-powered 30/60/90 day cash flow analysis</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <Button className="btn-accent" onClick={forecastCashFlow} disabled={loading} data-testid="forecast-cashflow-btn">
              {loading ? "Analyzing..." : "Generate AI Forecast"}
            </Button>
            {cashFlowAnalysis && (
              <div className="space-y-4">
                <div className="grid grid-cols-4 gap-4">
                  <div className="p-4 bg-blue-50 rounded-lg">
                    <p className="text-sm text-blue-600">Outstanding Invoices</p>
                    <p className="text-xl font-bold text-blue-700">${cashFlowAnalysis.metrics?.outstanding_invoices?.toLocaleString() || 0}</p>
                  </div>
                  <div className="p-4 bg-green-50 rounded-lg">
                    <p className="text-sm text-green-600">Recent Revenue</p>
                    <p className="text-xl font-bold text-green-700">${cashFlowAnalysis.metrics?.recent_revenue?.toLocaleString() || 0}</p>
                  </div>
                  <div className="p-4 bg-red-50 rounded-lg">
                    <p className="text-sm text-red-600">Total Expenses</p>
                    <p className="text-xl font-bold text-red-700">${cashFlowAnalysis.metrics?.total_expenses?.toLocaleString() || 0}</p>
                  </div>
                  <div className="p-4 bg-orange-50 rounded-lg">
                    <p className="text-sm text-orange-600">Active Jobs</p>
                    <p className="text-xl font-bold text-orange-700">{cashFlowAnalysis.metrics?.active_jobs || 0}</p>
                  </div>
                </div>
                <div className="p-4 bg-slate-50 rounded-lg">
                  <p className="text-sm font-medium text-slate-600 mb-2">AI Insights:</p>
                  <p className="text-slate-900 whitespace-pre-wrap">{cashFlowAnalysis.ai_analysis}</p>
                </div>
              </div>
            )}
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
