import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { 
  Users, FileText, Globe, CreditCard, TrendingUp, Activity,
  Search, ChevronLeft, ChevronRight, Trash2, Shield,
  Clock, Edit, UserCog, AlertTriangle, Phone, Mail, MapPin, Save,
  Key, Eye, EyeOff, CheckCircle, Settings, Lock
} from "lucide-react";
import axios from "axios";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const AdminDashboard = () => {
  const [stats, setStats] = useState(null);
  const [extendedStats, setExtendedStats] = useState(null);
  const [systemHealth, setSystemHealth] = useState(null);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const [activeTab, setActiveTab] = useState("stats");
  const usersPerPage = 10;

  // User details modal
  const [userDetails, setUserDetails] = useState(null);
  const [showUserDetailsDialog, setShowUserDetailsDialog] = useState(false);
  const [loadingUserDetails, setLoadingUserDetails] = useState(false);

  // Dialog states
  const [selectedUser, setSelectedUser] = useState(null);
  const [showEditDialog, setShowEditDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showResetPasswordDialog, setShowResetPasswordDialog] = useState(false);
  const [editPlan, setEditPlan] = useState("");
  const [editStatus, setEditStatus] = useState("");
  const [newUserPassword, setNewUserPassword] = useState("");
  const [actionLoading, setActionLoading] = useState(false);

  // Content editing states
  const [contactContent, setContactContent] = useState({
    email: "support@seoautomation.ro",
    phone: "+40 721 234 567",
    address: "Bucuresti, Romania",
    hours: "Luni - Vineri, 9:00 - 18:00"
  });
  const [termsContent, setTermsContent] = useState({
    company_name: "SEO Automation SRL",
    company_address: "Bucuresti, Romania",
    company_email: "legal@seoautomation.ro",
    last_updated: "Martie 2026"
  });
  const [privacyContent, setPrivacyContent] = useState({
    company_name: "SEO Automation SRL",
    company_email: "privacy@seoautomation.ro",
    data_retention: "2 ani",
    last_updated: "Martie 2026"
  });
  const [savingContent, setSavingContent] = useState(false);
  const [savingTerms, setSavingTerms] = useState(false);
  const [savingPrivacy, setSavingPrivacy] = useState(false);

  // Platform settings
  const [platformSettings, setPlatformSettings] = useState({
    has_stripe_key: false,
    has_resend_key: false
  });
  const [stripeKey, setStripeKey] = useState("");
  const [resendKey, setResendKey] = useState("");
  const [showStripeKey, setShowStripeKey] = useState(false);
  const [showResendKey, setShowResendKey] = useState(false);
  const [savingPlatform, setSavingPlatform] = useState(false);

  // Password change
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);
  const [changingPassword, setChangingPassword] = useState(false);

  useEffect(() => {
    fetchData();
    fetchContent();
    fetchPlatformSettings();
  }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem("token");
      const headers = { Authorization: `Bearer ${token}` };
      
      const [statsRes, extendedRes, healthRes, usersRes] = await Promise.all([
        axios.get(`${API}/admin/stats`, { headers }),
        axios.get(`${API}/admin/stats/extended`, { headers }),
        axios.get(`${API}/admin/system/health`, { headers }),
        axios.get(`${API}/admin/users`, { headers })
      ]);
      
      setStats(statsRes.data);
      setExtendedStats(extendedRes.data);
      setSystemHealth(healthRes.data);
      setUsers(usersRes.data);
    } catch (error) {
      console.error("Error fetching admin data:", error);
      if (error.response?.status === 403) {
        toast.error("Nu ai permisiuni de administrator");
      } else {
        toast.error("Eroare la incarcarea datelor");
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchUserDetails = async (userId) => {
    setLoadingUserDetails(true);
    try {
      const token = localStorage.getItem("token");
      const headers = { Authorization: `Bearer ${token}` };
      
      const res = await axios.get(`${API}/admin/users/${userId}/full`, { headers });
      setUserDetails(res.data);
      setShowUserDetailsDialog(true);
    } catch (error) {
      toast.error("Eroare la încărcarea detaliilor utilizatorului");
    } finally {
      setLoadingUserDetails(false);
    }
  };

  const fetchContent = async () => {
    try {
      const token = localStorage.getItem("token");
      const headers = { Authorization: `Bearer ${token}` };
      
      const res = await axios.get(`${API}/admin/content`, { headers });
      
      const contactData = res.data.find(c => c.page_id === "contact");
      if (contactData?.content) {
        setContactContent(contactData.content);
      }
      
      const termsData = res.data.find(c => c.page_id === "terms");
      if (termsData?.content) {
        setTermsContent(termsData.content);
      }
      
      const privacyData = res.data.find(c => c.page_id === "privacy");
      if (privacyData?.content) {
        setPrivacyContent(privacyData.content);
      }
    } catch (error) {
      console.log("Using default content");
    }
  };

  const saveContactContent = async () => {
    setSavingContent(true);
    try {
      const token = localStorage.getItem("token");
      const headers = { Authorization: `Bearer ${token}` };
      
      await axios.put(`${API}/admin/content/contact`, contactContent, { headers });
      toast.success("Informatiile de contact au fost salvate!");
    } catch (error) {
      toast.error("Eroare la salvarea continutului");
    } finally {
      setSavingContent(false);
    }
  };

  const saveTermsContent = async () => {
    setSavingTerms(true);
    try {
      const token = localStorage.getItem("token");
      const headers = { Authorization: `Bearer ${token}` };
      
      await axios.put(`${API}/admin/content/terms`, termsContent, { headers });
      toast.success("Termenii au fost salvati!");
    } catch (error) {
      toast.error("Eroare la salvarea termenilor");
    } finally {
      setSavingTerms(false);
    }
  };

  const savePrivacyContent = async () => {
    setSavingPrivacy(true);
    try {
      const token = localStorage.getItem("token");
      const headers = { Authorization: `Bearer ${token}` };
      
      await axios.put(`${API}/admin/content/privacy`, privacyContent, { headers });
      toast.success("Politica de confidentialitate a fost salvata!");
    } catch (error) {
      toast.error("Eroare la salvare");
    } finally {
      setSavingPrivacy(false);
    }
  };

  const fetchPlatformSettings = async () => {
    try {
      const token = localStorage.getItem("token");
      const headers = { Authorization: `Bearer ${token}` };
      
      const res = await axios.get(`${API}/admin/platform-settings`, { headers });
      setPlatformSettings(res.data);
    } catch (error) {
      console.log("Could not fetch platform settings");
    }
  };

  const savePlatformSettings = async () => {
    setSavingPlatform(true);
    try {
      const token = localStorage.getItem("token");
      const headers = { Authorization: `Bearer ${token}` };
      
      const data = {};
      if (stripeKey.trim()) data.stripe_key = stripeKey.trim();
      if (resendKey.trim()) data.resend_key = resendKey.trim();
      
      if (Object.keys(data).length === 0) {
        toast.error("Introdu cel putin o cheie");
        return;
      }
      
      await axios.put(`${API}/admin/platform-settings`, data, { headers });
      toast.success("Cheile au fost salvate! Serverul va folosi noile chei.");
      setStripeKey("");
      setResendKey("");
      fetchPlatformSettings();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Eroare la salvare");
    } finally {
      setSavingPlatform(false);
    }
  };

  const changePassword = async () => {
    if (newPassword !== confirmPassword) {
      toast.error("Parolele noi nu coincid");
      return;
    }
    if (newPassword.length < 6) {
      toast.error("Parola nouă trebuie să aibă minim 6 caractere");
      return;
    }
    
    setChangingPassword(true);
    try {
      const token = localStorage.getItem("token");
      const headers = { Authorization: `Bearer ${token}` };
      
      await axios.put(`${API}/admin/change-password`, {
        current_password: currentPassword,
        new_password: newPassword
      }, { headers });
      
      toast.success("Parola a fost schimbată cu succes!");
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Eroare la schimbarea parolei");
    } finally {
      setChangingPassword(false);
    }
  };

  const handleEditUser = (user) => {
    setSelectedUser(user);
    setEditPlan(user.plan || "free");
    setEditStatus(user.subscription_status || "expired");
    setShowEditDialog(true);
  };

  const handleDeleteUser = (user) => {
    setSelectedUser(user);
    setShowDeleteDialog(true);
  };

  const handleResetPassword = (user) => {
    setSelectedUser(user);
    setNewUserPassword("");
    setShowResetPasswordDialog(true);
  };

  const resetUserPassword = async () => {
    if (!selectedUser || !newUserPassword) return;
    setActionLoading(true);
    
    try {
      const token = localStorage.getItem("token");
      const headers = { Authorization: `Bearer ${token}` };
      
      await axios.post(
        `${API}/admin/users/${selectedUser.id}/reset-password`,
        { new_password: newUserPassword },
        { headers }
      );
      
      toast.success(`Parola pentru ${selectedUser.email} a fost resetată!`);
      setShowResetPasswordDialog(false);
      setNewUserPassword("");
    } catch (error) {
      toast.error(error.response?.data?.detail || "Eroare la resetare");
    } finally {
      setActionLoading(false);
    }
  };

  const saveUserChanges = async () => {
    if (!selectedUser) return;
    setActionLoading(true);
    
    try {
      const token = localStorage.getItem("token");
      const headers = { Authorization: `Bearer ${token}` };
      
      await axios.patch(
        `${API}/admin/users/${selectedUser.id}/subscription`,
        { plan: editPlan, status: editStatus },
        { headers }
      );
      
      toast.success("Modificarile au fost salvate");
      setShowEditDialog(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Eroare la salvare");
    } finally {
      setActionLoading(false);
    }
  };

  const confirmDeleteUser = async () => {
    if (!selectedUser) return;
    setActionLoading(true);
    
    try {
      const token = localStorage.getItem("token");
      const headers = { Authorization: `Bearer ${token}` };
      
      await axios.delete(`${API}/admin/users/${selectedUser.id}`, { headers });
      
      toast.success("Utilizatorul a fost sters");
      setShowDeleteDialog(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Eroare la stergere");
    } finally {
      setActionLoading(false);
    }
  };

  const toggleAdminRole = async (user) => {
    const newRole = user.role === "admin" ? "user" : "admin";
    
    try {
      const token = localStorage.getItem("token");
      const headers = { Authorization: `Bearer ${token}` };
      
      await axios.patch(
        `${API}/admin/users/${user.id}/role`,
        { role: newRole },
        { headers }
      );
      
      toast.success(`Rol schimbat la ${newRole}`);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || "Eroare la schimbarea rolului");
    }
  };

  const filteredUsers = users.filter(user => 
    user.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    user.name?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const totalPages = Math.ceil(filteredUsers.length / usersPerPage);
  const paginatedUsers = filteredUsers.slice(
    (currentPage - 1) * usersPerPage,
    currentPage * usersPerPage
  );

  const getStatusBadge = (status) => {
    const config = {
      active: { label: "Activ", className: "bg-[#00E676]/10 text-[#00E676]" },
      trialing: { label: "Trial", className: "bg-yellow-500/10 text-yellow-500" },
      expired: { label: "Expirat", className: "bg-red-500/10 text-red-500" },
      canceled: { label: "Anulat", className: "bg-gray-500/10 text-gray-500" }
    };
    const c = config[status] || config.expired;
    return <Badge className={c.className}>{c.label}</Badge>;
  };

  const getPlanBadge = (plan) => {
    const colors = {
      starter: "bg-blue-500/10 text-blue-400",
      pro: "bg-purple-500/10 text-purple-400",
      agency: "bg-orange-500/10 text-orange-400",
      enterprise: "bg-[#00E676]/10 text-[#00E676]",
      free: "bg-gray-500/10 text-gray-400"
    };
    return (
      <Badge className={colors[plan] || colors.free}>
        {plan?.charAt(0).toUpperCase() + plan?.slice(1) || "Free"}
      </Badge>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#00E676]"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="admin-dashboard">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white flex items-center gap-3">
            <Shield className="w-8 h-8 text-[#00E676]" />
            Admin Dashboard
          </h1>
          <p className="text-[#71717A] mt-1">Gestioneaza utilizatorii si platforma</p>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="bg-[#171717] border border-[#262626]">
          <TabsTrigger value="stats" className="data-[state=active]:bg-[#00E676] data-[state=active]:text-black">
            Statistici
          </TabsTrigger>
          <TabsTrigger value="users" className="data-[state=active]:bg-[#00E676] data-[state=active]:text-black">
            Utilizatori
          </TabsTrigger>
          <TabsTrigger value="content" className="data-[state=active]:bg-[#00E676] data-[state=active]:text-black">
            Continut Site
          </TabsTrigger>
          <TabsTrigger value="platform" className="data-[state=active]:bg-[#00E676] data-[state=active]:text-black">
            Setari Platforma
          </TabsTrigger>
        </TabsList>

        {/* STATS TAB */}
        <TabsContent value="stats" className="space-y-6 mt-6">
          {/* Stats Cards */}
          {stats && (
            <>
              <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
                <Card className="bg-[#0A0A0A] border-[#262626]">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-[#71717A] text-sm">Total Utilizatori</p>
                        <p className="text-3xl font-bold text-white">{stats.total_users}</p>
                      </div>
                      <div className="w-12 h-12 rounded-lg bg-blue-500/10 flex items-center justify-center">
                        <Users className="w-6 h-6 text-blue-500" />
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="bg-[#0A0A0A] border-[#262626]">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-[#71717A] text-sm">Subscriptii Active</p>
                        <p className="text-3xl font-bold text-white">{stats.active_subscriptions}</p>
                      </div>
                      <div className="w-12 h-12 rounded-lg bg-[#00E676]/10 flex items-center justify-center">
                        <CreditCard className="w-6 h-6 text-[#00E676]" />
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="bg-[#0A0A0A] border-[#262626]">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-[#71717A] text-sm">Total Articole</p>
                        <p className="text-3xl font-bold text-white">{stats.total_articles}</p>
                      </div>
                      <div className="w-12 h-12 rounded-lg bg-purple-500/10 flex items-center justify-center">
                        <FileText className="w-6 h-6 text-purple-500" />
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="bg-[#0A0A0A] border-[#262626]">
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="text-[#71717A] text-sm">Site-uri Conectate</p>
                        <p className="text-3xl font-bold text-white">{stats.total_sites}</p>
                      </div>
                      <div className="w-12 h-12 rounded-lg bg-orange-500/10 flex items-center justify-center">
                        <Globe className="w-6 h-6 text-orange-500" />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Revenue Stats */}
              <div className="grid md:grid-cols-3 gap-4">
                <Card className="bg-[#0A0A0A] border-[#262626]">
                  <CardContent className="p-6">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-lg bg-[#00E676]/10 flex items-center justify-center">
                        <TrendingUp className="w-6 h-6 text-[#00E676]" />
                      </div>
                      <div>
                        <p className="text-[#71717A] text-sm">Venit Lunar Estimat</p>
                        <p className="text-2xl font-bold text-[#00E676]">{stats.monthly_revenue} EUR</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="bg-[#0A0A0A] border-[#262626]">
                  <CardContent className="p-6">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-lg bg-yellow-500/10 flex items-center justify-center">
                        <Clock className="w-6 h-6 text-yellow-500" />
                      </div>
                      <div>
                        <p className="text-[#71717A] text-sm">Utilizatori in Trial</p>
                        <p className="text-2xl font-bold text-yellow-500">{stats.trial_users}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card className="bg-[#0A0A0A] border-[#262626]">
                  <CardContent className="p-6">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 rounded-lg bg-blue-500/10 flex items-center justify-center">
                        <Activity className="w-6 h-6 text-blue-500" />
                      </div>
                      <div>
                        <p className="text-[#71717A] text-sm">Activi Azi</p>
                        <p className="text-2xl font-bold text-blue-500">{stats.active_today}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Plan Breakdown */}
              {stats?.plan_breakdown && (
                <Card className="bg-[#0A0A0A] border-[#262626]">
                  <CardHeader>
                    <CardTitle className="text-white">Distributie Planuri</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      {Object.entries(stats.plan_breakdown).map(([plan, count]) => (
                        <div key={plan} className="bg-[#171717] rounded-lg p-4 text-center">
                          <p className="text-2xl font-bold text-white">{count}</p>
                          <p className="text-[#71717A] capitalize">{plan}</p>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Extended Stats Section */}
              {extendedStats && (
                <>
                  {/* Registrations */}
                  <Card className="bg-[#0A0A0A] border-[#262626]">
                    <CardHeader>
                      <CardTitle className="text-white flex items-center gap-2">
                        <Users className="w-5 h-5 text-[#00E676]" />
                        Înregistrări Noi
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-3 gap-4">
                        <div className="bg-[#171717] rounded-lg p-4 text-center">
                          <p className="text-3xl font-bold text-[#00E676]">{extendedStats.registrations?.today || 0}</p>
                          <p className="text-[#71717A] text-sm">Azi</p>
                        </div>
                        <div className="bg-[#171717] rounded-lg p-4 text-center">
                          <p className="text-3xl font-bold text-blue-500">{extendedStats.registrations?.this_week || 0}</p>
                          <p className="text-[#71717A] text-sm">Săptămâna asta</p>
                        </div>
                        <div className="bg-[#171717] rounded-lg p-4 text-center">
                          <p className="text-3xl font-bold text-purple-500">{extendedStats.registrations?.this_month || 0}</p>
                          <p className="text-[#71717A] text-sm">Luna asta</p>
                        </div>
                      </div>
                    </CardContent>
                  </Card>

                  {/* Revenue & Conversion */}
                  <div className="grid md:grid-cols-2 gap-4">
                    <Card className="bg-[#0A0A0A] border-[#262626]">
                      <CardHeader>
                        <CardTitle className="text-white flex items-center gap-2">
                          <CreditCard className="w-5 h-5 text-[#00E676]" />
                          Revenue
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          <div className="flex justify-between items-center">
                            <span className="text-[#71717A]">MRR (Monthly Recurring)</span>
                            <span className="text-2xl font-bold text-[#00E676]">€{extendedStats.revenue?.mrr || 0}</span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-[#71717A]">ARR (Annual)</span>
                            <span className="text-xl font-bold text-white">€{extendedStats.revenue?.arr || 0}</span>
                          </div>
                          <div className="border-t border-[#262626] pt-4">
                            <div className="flex justify-between items-center">
                              <span className="text-[#71717A]">Conversie Trial</span>
                              <span className="text-lg font-bold text-blue-500">{extendedStats.revenue?.trial_conversion_rate || 0}%</span>
                            </div>
                            <div className="flex justify-between items-center mt-2">
                              <span className="text-[#71717A]">Churn Rate</span>
                              <span className="text-lg font-bold text-red-500">{extendedStats.revenue?.churn_rate || 0}%</span>
                            </div>
                          </div>
                        </div>
                      </CardContent>
                    </Card>

                    <Card className="bg-[#0A0A0A] border-[#262626]">
                      <CardHeader>
                        <CardTitle className="text-white flex items-center gap-2">
                          <Mail className="w-5 h-5 text-[#00E676]" />
                          Backlink Outreach
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          <div className="flex justify-between items-center">
                            <span className="text-[#71717A]">Total Emailuri Trimise</span>
                            <span className="text-2xl font-bold text-white">{extendedStats.backlinks?.total_sent || 0}</span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-[#71717A]">Răspunsuri Primite</span>
                            <span className="text-xl font-bold text-[#00E676]">{extendedStats.backlinks?.total_responded || 0}</span>
                          </div>
                          <div className="flex justify-between items-center">
                            <span className="text-[#71717A]">Rată Răspuns</span>
                            <span className="text-lg font-bold text-blue-500">{extendedStats.backlinks?.response_rate || 0}%</span>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  </div>

                  {/* Top Users */}
                  {extendedStats.top_users?.length > 0 && (
                    <Card className="bg-[#0A0A0A] border-[#262626]">
                      <CardHeader>
                        <CardTitle className="text-white flex items-center gap-2">
                          <TrendingUp className="w-5 h-5 text-[#00E676]" />
                          Top 10 Utilizatori Activi
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-2">
                          {extendedStats.top_users.map((user, index) => (
                            <div 
                              key={user.user_id} 
                              className="flex items-center justify-between p-3 bg-[#171717] rounded-lg cursor-pointer hover:bg-[#262626]"
                              onClick={() => fetchUserDetails(user.user_id)}
                            >
                              <div className="flex items-center gap-3">
                                <span className="text-[#71717A] w-6">{index + 1}.</span>
                                <div>
                                  <p className="text-white font-medium">{user.name || user.email}</p>
                                  <p className="text-[#71717A] text-sm">{user.email}</p>
                                </div>
                              </div>
                              <Badge className="bg-[#00E676]/10 text-[#00E676]">
                                {user.articles_count} articole
                              </Badge>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {/* Usage by Plan */}
                  {extendedStats.usage_by_plan && (
                    <Card className="bg-[#0A0A0A] border-[#262626]">
                      <CardHeader>
                        <CardTitle className="text-white flex items-center gap-2">
                          <Activity className="w-5 h-5 text-[#00E676]" />
                          Utilizare per Plan
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          {Object.entries(extendedStats.usage_by_plan).map(([plan, data]) => (
                            <div key={plan} className="bg-[#171717] rounded-lg p-4">
                              <p className="text-white font-bold capitalize text-lg">{plan}</p>
                              <div className="mt-2 space-y-1 text-sm">
                                <div className="flex justify-between">
                                  <span className="text-[#71717A]">Utilizatori</span>
                                  <span className="text-white">{data.users}</span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-[#71717A]">Articole</span>
                                  <span className="text-white">{data.articles}</span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-[#71717A]">Site-uri</span>
                                  <span className="text-white">{data.sites}</span>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      </CardContent>
                    </Card>
                  )}

                  {/* User Growth Chart */}
                  {extendedStats.user_growth_chart?.length > 0 && (
                    <Card className="bg-[#0A0A0A] border-[#262626]">
                      <CardHeader>
                        <CardTitle className="text-white flex items-center gap-2">
                          <TrendingUp className="w-5 h-5 text-[#00E676]" />
                          Creștere Utilizatori (30 zile)
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="flex items-end justify-between gap-1 h-32">
                          {extendedStats.user_growth_chart.slice(-30).map((day) => {
                            const maxReg = Math.max(...extendedStats.user_growth_chart.map(d => d.registrations), 1);
                            const height = (day.registrations / maxReg) * 100;
                            return (
                              <div 
                                key={day.date} 
                                className="flex-1 bg-[#00E676]/80 rounded-t min-h-[4px] hover:bg-[#00E676] transition-colors"
                                style={{ height: `${Math.max(height, 4)}%` }}
                                title={`${day.date}: ${day.registrations} înregistrări`}
                              ></div>
                            );
                          })}
                        </div>
                        <div className="flex justify-between mt-2 text-xs text-[#71717A]">
                          <span>{extendedStats.user_growth_chart[0]?.date}</span>
                          <span>{extendedStats.user_growth_chart[extendedStats.user_growth_chart.length - 1]?.date}</span>
                        </div>
                      </CardContent>
                    </Card>
                  )}
                </>
              )}

              {/* System Health */}
              {systemHealth && (
                <Card className="bg-[#0A0A0A] border-[#262626]">
                  <CardHeader>
                    <CardTitle className="text-white flex items-center gap-2">
                      <AlertTriangle className="w-5 h-5 text-yellow-500" />
                      System Health
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid md:grid-cols-4 gap-4">
                      <div className="bg-[#171717] rounded-lg p-4 text-center">
                        <p className={`text-2xl font-bold ${systemHealth.users_missing_api_keys_count > 0 ? 'text-yellow-500' : 'text-[#00E676]'}`}>
                          {systemHealth.users_missing_api_keys_count || 0}
                        </p>
                        <p className="text-[#71717A] text-sm">Utilizatori fără API Keys</p>
                      </div>
                      <div className="bg-[#171717] rounded-lg p-4 text-center">
                        <p className={`text-2xl font-bold ${systemHealth.failed_jobs_today > 0 ? 'text-red-500' : 'text-[#00E676]'}`}>
                          {systemHealth.failed_jobs_today || 0}
                        </p>
                        <p className="text-[#71717A] text-sm">Job-uri Eșuate Azi</p>
                      </div>
                      <div className="bg-[#171717] rounded-lg p-4 text-center">
                        <p className="text-2xl font-bold text-yellow-500">{systemHealth.expired_trials_not_converted || 0}</p>
                        <p className="text-[#71717A] text-sm">Trial-uri Expirate</p>
                      </div>
                      <div className="bg-[#171717] rounded-lg p-4 text-center">
                        <p className={`text-2xl font-bold ${systemHealth.sites_without_niche > 0 ? 'text-yellow-500' : 'text-[#00E676]'}`}>
                          {systemHealth.sites_without_niche || 0}
                        </p>
                        <p className="text-[#71717A] text-sm">Site-uri fără Nișă</p>
                      </div>
                    </div>
                    
                    {systemHealth.users_missing_api_keys?.length > 0 && (
                      <div className="mt-4">
                        <p className="text-[#71717A] text-sm mb-2">Utilizatori care necesită configurare API Keys:</p>
                        <div className="space-y-1 max-h-40 overflow-y-auto">
                          {systemHealth.users_missing_api_keys.slice(0, 10).map((user) => (
                            <div 
                              key={user.user_id} 
                              className="flex items-center justify-between p-2 bg-[#171717] rounded text-sm cursor-pointer hover:bg-[#262626]"
                              onClick={() => fetchUserDetails(user.user_id)}
                            >
                              <span className="text-white">{user.email}</span>
                              <Badge variant="outline" className="text-yellow-500 border-yellow-500">Lipsă LLM Key</Badge>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </TabsContent>

        {/* USERS TAB */}
        <TabsContent value="users" className="mt-6">
          <Card className="bg-[#0A0A0A] border-[#262626]">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="text-white">Utilizatori ({filteredUsers.length})</CardTitle>
                <div className="relative w-64">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#71717A]" />
                  <Input
                    placeholder="Cauta utilizator..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10 bg-[#171717] border-[#262626] text-white"
                    data-testid="admin-user-search"
                  />
                </div>
              </div>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-[#262626]">
                      <th className="text-left py-3 px-4 text-[#71717A] font-normal">Utilizator</th>
                      <th className="text-left py-3 px-4 text-[#71717A] font-normal">Plan</th>
                      <th className="text-left py-3 px-4 text-[#71717A] font-normal">Status</th>
                      <th className="text-left py-3 px-4 text-[#71717A] font-normal">Articole</th>
                      <th className="text-left py-3 px-4 text-[#71717A] font-normal">Inregistrat</th>
                      <th className="text-left py-3 px-4 text-[#71717A] font-normal">Actiuni</th>
                    </tr>
                  </thead>
                  <tbody>
                    {paginatedUsers.map((user) => (
                      <tr key={user.id} className="border-b border-[#262626] hover:bg-[#171717]">
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2">
                            {user.role === "admin" && (
                              <Shield className="w-4 h-4 text-red-400" title="Admin" />
                            )}
                            <div>
                              <p className="text-white font-medium">{user.name || "Fara nume"}</p>
                              <p className="text-[#71717A] text-sm">{user.email}</p>
                            </div>
                          </div>
                        </td>
                        <td className="py-3 px-4">
                          {getPlanBadge(user.plan)}
                        </td>
                        <td className="py-3 px-4">
                          {getStatusBadge(user.subscription_status)}
                        </td>
                        <td className="py-3 px-4 text-white">
                          {user.articles_count || 0}
                        </td>
                        <td className="py-3 px-4 text-[#71717A]">
                          {user.created_at ? new Date(user.created_at).toLocaleDateString('ro-RO') : '-'}
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex gap-2">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => fetchUserDetails(user.id)}
                              className="text-[#00E676] hover:text-[#00E676]/80 hover:bg-[#00E676]/10"
                              title="Vezi Detalii"
                              data-testid={`view-user-${user.id}`}
                            >
                              <Eye className="w-4 h-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleEditUser(user)}
                              className="text-blue-400 hover:text-blue-300 hover:bg-blue-500/10"
                              data-testid={`edit-user-${user.id}`}
                            >
                              <Edit className="w-4 h-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => toggleAdminRole(user)}
                              className="text-yellow-400 hover:text-yellow-300 hover:bg-yellow-500/10"
                              title={user.role === "admin" ? "Retrage Admin" : "Fa Admin"}
                              data-testid={`toggle-admin-${user.id}`}
                            >
                              <UserCog className="w-4 h-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleResetPassword(user)}
                              className="text-purple-400 hover:text-purple-300 hover:bg-purple-500/10"
                              title="Resetează Parola"
                              data-testid={`reset-password-${user.id}`}
                            >
                              <Key className="w-4 h-4" />
                            </Button>
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDeleteUser(user)}
                              className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
                              data-testid={`delete-user-${user.id}`}
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Pagination */}
              {totalPages > 1 && (
                <div className="flex items-center justify-between mt-4 pt-4 border-t border-[#262626]">
                  <p className="text-[#71717A] text-sm">
                    Afisare {(currentPage - 1) * usersPerPage + 1} - {Math.min(currentPage * usersPerPage, filteredUsers.length)} din {filteredUsers.length}
                  </p>
                  <div className="flex gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                      disabled={currentPage === 1}
                      className="border-[#262626]"
                    >
                      <ChevronLeft className="w-4 h-4" />
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                      disabled={currentPage === totalPages}
                      className="border-[#262626]"
                    >
                      <ChevronRight className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* CONTENT TAB */}
        <TabsContent value="content" className="mt-6">
          <div className="grid md:grid-cols-2 gap-6">
            {/* Contact Page Editor */}
            <Card className="bg-[#0A0A0A] border-[#262626]">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Mail className="w-5 h-5 text-[#00E676]" />
                  Pagina Contact
                </CardTitle>
                <CardDescription className="text-[#71717A]">
                  Editeaza informatiile afisate pe pagina de contact
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label className="text-[#A1A1AA] flex items-center gap-2">
                    <Mail className="w-4 h-4" /> Email
                  </Label>
                  <Input
                    value={contactContent.email}
                    onChange={(e) => setContactContent({...contactContent, email: e.target.value})}
                    className="bg-[#171717] border-[#262626] text-white"
                    placeholder="support@exemplu.ro"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label className="text-[#A1A1AA] flex items-center gap-2">
                    <Phone className="w-4 h-4" /> Telefon
                  </Label>
                  <Input
                    value={contactContent.phone}
                    onChange={(e) => setContactContent({...contactContent, phone: e.target.value})}
                    className="bg-[#171717] border-[#262626] text-white"
                    placeholder="+40 721 234 567"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label className="text-[#A1A1AA] flex items-center gap-2">
                    <MapPin className="w-4 h-4" /> Adresa
                  </Label>
                  <Input
                    value={contactContent.address}
                    onChange={(e) => setContactContent({...contactContent, address: e.target.value})}
                    className="bg-[#171717] border-[#262626] text-white"
                    placeholder="Bucuresti, Romania"
                  />
                </div>
                
                <div className="space-y-2">
                  <Label className="text-[#A1A1AA] flex items-center gap-2">
                    <Clock className="w-4 h-4" /> Program
                  </Label>
                  <Input
                    value={contactContent.hours}
                    onChange={(e) => setContactContent({...contactContent, hours: e.target.value})}
                    className="bg-[#171717] border-[#262626] text-white"
                    placeholder="Luni - Vineri, 9:00 - 18:00"
                  />
                </div>
                
                <Button 
                  onClick={saveContactContent}
                  disabled={savingContent}
                  className="w-full bg-[#00E676] text-black hover:bg-[#00E676]/90"
                >
                  <Save className="w-4 h-4 mr-2" />
                  {savingContent ? "Se salveaza..." : "Salveaza Modificarile"}
                </Button>
              </CardContent>
            </Card>

            {/* Preview */}
            <Card className="bg-[#0A0A0A] border-[#262626]">
              <CardHeader>
                <CardTitle className="text-white">Previzualizare</CardTitle>
                <CardDescription className="text-[#71717A]">
                  Asa vor arata informatiile pe site
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="bg-[#171717] rounded-lg p-4 space-y-4">
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-lg bg-[#00E676]/10 flex items-center justify-center">
                      <Mail className="w-5 h-5 text-[#00E676]" />
                    </div>
                    <div>
                      <p className="text-white font-medium">Email</p>
                      <p className="text-[#A1A1AA]">{contactContent.email}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-lg bg-[#00E676]/10 flex items-center justify-center">
                      <Phone className="w-5 h-5 text-[#00E676]" />
                    </div>
                    <div>
                      <p className="text-white font-medium">Telefon</p>
                      <p className="text-[#A1A1AA]">{contactContent.phone}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-lg bg-[#00E676]/10 flex items-center justify-center">
                      <MapPin className="w-5 h-5 text-[#00E676]" />
                    </div>
                    <div>
                      <p className="text-white font-medium">Adresa</p>
                      <p className="text-[#A1A1AA]">{contactContent.address}</p>
                    </div>
                  </div>
                  
                  <div className="flex items-start gap-3">
                    <div className="w-10 h-10 rounded-lg bg-[#00E676]/10 flex items-center justify-center">
                      <Clock className="w-5 h-5 text-[#00E676]" />
                    </div>
                    <div>
                      <p className="text-white font-medium">Program</p>
                      <p className="text-[#A1A1AA]">{contactContent.hours}</p>
                    </div>
                  </div>
                </div>
                
                <p className="text-[#71717A] text-sm text-center">
                  Modificarile vor aparea pe pagina /contact dupa salvare
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Terms and Privacy Editors */}
          <div className="grid md:grid-cols-2 gap-6 mt-6">
            {/* Terms Page Editor */}
            <Card className="bg-[#0A0A0A] border-[#262626]">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <FileText className="w-5 h-5 text-blue-500" />
                  Termeni si Conditii
                </CardTitle>
                <CardDescription className="text-[#71717A]">
                  Editeaza informatiile din pagina Termeni
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label className="text-[#A1A1AA]">Nume Companie</Label>
                  <Input
                    value={termsContent.company_name}
                    onChange={(e) => setTermsContent({...termsContent, company_name: e.target.value})}
                    className="bg-[#171717] border-[#262626] text-white"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-[#A1A1AA]">Adresa Companie</Label>
                  <Input
                    value={termsContent.company_address}
                    onChange={(e) => setTermsContent({...termsContent, company_address: e.target.value})}
                    className="bg-[#171717] border-[#262626] text-white"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-[#A1A1AA]">Email Legal</Label>
                  <Input
                    value={termsContent.company_email}
                    onChange={(e) => setTermsContent({...termsContent, company_email: e.target.value})}
                    className="bg-[#171717] border-[#262626] text-white"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-[#A1A1AA]">Ultima Actualizare</Label>
                  <Input
                    value={termsContent.last_updated}
                    onChange={(e) => setTermsContent({...termsContent, last_updated: e.target.value})}
                    className="bg-[#171717] border-[#262626] text-white"
                    placeholder="Martie 2026"
                  />
                </div>
                <Button 
                  onClick={saveTermsContent}
                  disabled={savingTerms}
                  className="w-full bg-blue-500 text-white hover:bg-blue-600"
                >
                  <Save className="w-4 h-4 mr-2" />
                  {savingTerms ? "Se salveaza..." : "Salveaza Termeni"}
                </Button>
              </CardContent>
            </Card>

            {/* Privacy Page Editor */}
            <Card className="bg-[#0A0A0A] border-[#262626]">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Shield className="w-5 h-5 text-purple-500" />
                  Politica Confidentialitate
                </CardTitle>
                <CardDescription className="text-[#71717A]">
                  Editeaza informatiile din pagina Privacy
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label className="text-[#A1A1AA]">Nume Companie</Label>
                  <Input
                    value={privacyContent.company_name}
                    onChange={(e) => setPrivacyContent({...privacyContent, company_name: e.target.value})}
                    className="bg-[#171717] border-[#262626] text-white"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-[#A1A1AA]">Email Privacy</Label>
                  <Input
                    value={privacyContent.company_email}
                    onChange={(e) => setPrivacyContent({...privacyContent, company_email: e.target.value})}
                    className="bg-[#171717] border-[#262626] text-white"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-[#A1A1AA]">Perioada Retentie Date</Label>
                  <Input
                    value={privacyContent.data_retention}
                    onChange={(e) => setPrivacyContent({...privacyContent, data_retention: e.target.value})}
                    className="bg-[#171717] border-[#262626] text-white"
                    placeholder="2 ani"
                  />
                </div>
                <div className="space-y-2">
                  <Label className="text-[#A1A1AA]">Ultima Actualizare</Label>
                  <Input
                    value={privacyContent.last_updated}
                    onChange={(e) => setPrivacyContent({...privacyContent, last_updated: e.target.value})}
                    className="bg-[#171717] border-[#262626] text-white"
                    placeholder="Martie 2026"
                  />
                </div>
                <Button 
                  onClick={savePrivacyContent}
                  disabled={savingPrivacy}
                  className="w-full bg-purple-500 text-white hover:bg-purple-600"
                >
                  <Save className="w-4 h-4 mr-2" />
                  {savingPrivacy ? "Se salveaza..." : "Salveaza Privacy"}
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* PLATFORM SETTINGS TAB */}
        <TabsContent value="platform" className="mt-6">
          <div className="grid md:grid-cols-2 gap-6">
            {/* Current Status */}
            <Card className="bg-[#0A0A0A] border-[#262626]">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Settings className="w-5 h-5 text-[#00E676]" />
                  Status Chei Platformă
                </CardTitle>
                <CardDescription className="text-[#71717A]">
                  Cheile API necesare pentru funcționarea platformei
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 rounded-lg bg-[#171717]">
                    <div className="flex items-center gap-3">
                      <CreditCard className="w-5 h-5 text-purple-500" />
                      <div>
                        <p className="text-white font-medium">Stripe API Key</p>
                        <p className="text-[#71717A] text-sm">Pentru procesare plăți</p>
                      </div>
                    </div>
                    {platformSettings.has_stripe_key ? (
                      <Badge className="bg-[#00E676]/10 text-[#00E676]">
                        <CheckCircle className="w-3 h-3 mr-1" /> Configurat
                      </Badge>
                    ) : (
                      <Badge className="bg-red-500/10 text-red-400">
                        Neconfigurat
                      </Badge>
                    )}
                  </div>
                  
                  <div className="flex items-center justify-between p-3 rounded-lg bg-[#171717]">
                    <div className="flex items-center gap-3">
                      <Mail className="w-5 h-5 text-blue-500" />
                      <div>
                        <p className="text-white font-medium">Resend API Key</p>
                        <p className="text-[#71717A] text-sm">Pentru emailuri sistem</p>
                      </div>
                    </div>
                    {platformSettings.has_resend_key ? (
                      <Badge className="bg-[#00E676]/10 text-[#00E676]">
                        <CheckCircle className="w-3 h-3 mr-1" /> Configurat
                      </Badge>
                    ) : (
                      <Badge className="bg-yellow-500/10 text-yellow-500">
                        Opțional
                      </Badge>
                    )}
                  </div>
                </div>
                
                <div className="p-3 rounded-lg bg-[#00E676]/5 border border-[#00E676]/20">
                  <p className="text-[#A1A1AA] text-sm">
                    <strong className="text-white">Notă:</strong> Cheile sunt criptate și stocate securizat. 
                    După salvare, serverul le va folosi automat.
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Add/Update Keys */}
            <Card className="bg-[#0A0A0A] border-[#262626]">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Key className="w-5 h-5 text-[#00E676]" />
                  Adaugă/Actualizează Chei
                </CardTitle>
                <CardDescription className="text-[#71717A]">
                  Introdu cheile pentru a le salva în platformă
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label className="text-[#A1A1AA] flex items-center gap-2">
                    <CreditCard className="w-4 h-4" /> Stripe API Key (sk_live_...)
                  </Label>
                  <div className="relative">
                    <Input
                      type={showStripeKey ? "text" : "password"}
                      placeholder="sk_live_..."
                      value={stripeKey}
                      onChange={(e) => setStripeKey(e.target.value)}
                      className="bg-[#171717] border-[#262626] text-white pr-10"
                    />
                    <button
                      type="button"
                      onClick={() => setShowStripeKey(!showStripeKey)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-[#71717A] hover:text-white"
                    >
                      {showStripeKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  <p className="text-[#71717A] text-xs">
                    Obține de la: <a href="https://dashboard.stripe.com/apikeys" target="_blank" rel="noopener noreferrer" className="text-[#00E676] hover:underline">dashboard.stripe.com/apikeys</a>
                  </p>
                </div>
                
                <div className="space-y-2">
                  <Label className="text-[#A1A1AA] flex items-center gap-2">
                    <Mail className="w-4 h-4" /> Resend API Key (re_...)
                  </Label>
                  <div className="relative">
                    <Input
                      type={showResendKey ? "text" : "password"}
                      placeholder="re_..."
                      value={resendKey}
                      onChange={(e) => setResendKey(e.target.value)}
                      className="bg-[#171717] border-[#262626] text-white pr-10"
                    />
                    <button
                      type="button"
                      onClick={() => setShowResendKey(!showResendKey)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-[#71717A] hover:text-white"
                    >
                      {showResendKey ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  <p className="text-[#71717A] text-xs">
                    Obține de la: <a href="https://resend.com/api-keys" target="_blank" rel="noopener noreferrer" className="text-[#00E676] hover:underline">resend.com/api-keys</a>
                  </p>
                </div>
                
                <Button
                  onClick={savePlatformSettings}
                  disabled={savingPlatform || (!stripeKey && !resendKey)}
                  className="w-full bg-[#00E676] text-black hover:bg-[#00E676]/90"
                >
                  <Save className="w-4 h-4 mr-2" />
                  {savingPlatform ? "Se salvează..." : "Salvează Cheile"}
                </Button>
              </CardContent>
            </Card>

            {/* Change Password */}
            <Card className="bg-[#0A0A0A] border-[#262626]">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Lock className="w-5 h-5 text-orange-500" />
                  Schimbă Parola
                </CardTitle>
                <CardDescription className="text-[#71717A]">
                  Schimbă parola contului tău de administrator
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <Label className="text-[#A1A1AA]">Parola curentă</Label>
                  <div className="relative">
                    <Input
                      type={showCurrentPassword ? "text" : "password"}
                      placeholder="Parola actuală"
                      value={currentPassword}
                      onChange={(e) => setCurrentPassword(e.target.value)}
                      className="bg-[#171717] border-[#262626] text-white pr-10"
                    />
                    <button
                      type="button"
                      onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-[#71717A] hover:text-white"
                    >
                      {showCurrentPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <Label className="text-[#A1A1AA]">Parola nouă</Label>
                  <div className="relative">
                    <Input
                      type={showNewPassword ? "text" : "password"}
                      placeholder="Minim 6 caractere"
                      value={newPassword}
                      onChange={(e) => setNewPassword(e.target.value)}
                      className="bg-[#171717] border-[#262626] text-white pr-10"
                    />
                    <button
                      type="button"
                      onClick={() => setShowNewPassword(!showNewPassword)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-[#71717A] hover:text-white"
                    >
                      {showNewPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
                
                <div className="space-y-2">
                  <Label className="text-[#A1A1AA]">Confirmă parola nouă</Label>
                  <Input
                    type="password"
                    placeholder="Repetă parola nouă"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="bg-[#171717] border-[#262626] text-white"
                  />
                </div>
                
                <Button
                  onClick={changePassword}
                  disabled={changingPassword || !currentPassword || !newPassword || !confirmPassword}
                  className="w-full bg-orange-500 text-white hover:bg-orange-600"
                >
                  <Lock className="w-4 h-4 mr-2" />
                  {changingPassword ? "Se schimbă..." : "Schimbă Parola"}
                </Button>
              </CardContent>
            </Card>
          </div>
        </TabsContent>
      </Tabs>

      {/* Edit User Dialog */}
      <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
        <DialogContent className="bg-[#0A0A0A] border-[#262626]">
          <DialogHeader>
            <DialogTitle className="text-white">Editeaza Utilizator</DialogTitle>
            <DialogDescription className="text-[#71717A]">
              {selectedUser?.email}
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label className="text-[#A1A1AA]">Plan</Label>
              <Select value={editPlan} onValueChange={setEditPlan}>
                <SelectTrigger className="bg-[#171717] border-[#262626] text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-[#171717] border-[#262626]">
                  <SelectItem value="free">Free</SelectItem>
                  <SelectItem value="starter">Starter - 19 EUR</SelectItem>
                  <SelectItem value="pro">Pro - 49 EUR</SelectItem>
                  <SelectItem value="agency">Agency - 99 EUR</SelectItem>
                  <SelectItem value="enterprise">Enterprise - 199 EUR</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label className="text-[#A1A1AA]">Status Subscriptie</Label>
              <Select value={editStatus} onValueChange={setEditStatus}>
                <SelectTrigger className="bg-[#171717] border-[#262626] text-white">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="bg-[#171717] border-[#262626]">
                  <SelectItem value="active">Activ</SelectItem>
                  <SelectItem value="trialing">Trial</SelectItem>
                  <SelectItem value="canceled">Anulat</SelectItem>
                  <SelectItem value="expired">Expirat</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowEditDialog(false)}
              className="border-[#262626]"
            >
              Anuleaza
            </Button>
            <Button
              onClick={saveUserChanges}
              disabled={actionLoading}
              className="bg-[#00E676] text-black hover:bg-[#00E676]/90"
            >
              {actionLoading ? "Se salveaza..." : "Salveaza"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete User Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent className="bg-[#0A0A0A] border-[#262626]">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-red-500" />
              Sterge Utilizator
            </DialogTitle>
            <DialogDescription className="text-[#71717A]">
              Esti sigur ca vrei sa stergi utilizatorul <strong className="text-white">{selectedUser?.email}</strong>?
              Aceasta actiune va sterge toate datele asociate si nu poate fi anulata.
            </DialogDescription>
          </DialogHeader>
          
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDeleteDialog(false)}
              className="border-[#262626]"
            >
              Anuleaza
            </Button>
            <Button
              variant="destructive"
              onClick={confirmDeleteUser}
              disabled={actionLoading}
              className="bg-red-500 hover:bg-red-600"
            >
              {actionLoading ? "Se sterge..." : "Sterge"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Reset Password Dialog */}
      <Dialog open={showResetPasswordDialog} onOpenChange={setShowResetPasswordDialog}>
        <DialogContent className="bg-[#0A0A0A] border-[#262626]">
          <DialogHeader>
            <DialogTitle className="text-white flex items-center gap-2">
              <Key className="w-5 h-5 text-purple-500" />
              Resetează Parola
            </DialogTitle>
            <DialogDescription className="text-[#71717A]">
              Setează o parolă nouă pentru <strong className="text-white">{selectedUser?.email}</strong>
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label className="text-[#A1A1AA]">Parola nouă</Label>
              <Input
                type="text"
                placeholder="Minim 6 caractere"
                value={newUserPassword}
                onChange={(e) => setNewUserPassword(e.target.value)}
                className="bg-[#171717] border-[#262626] text-white"
              />
              <p className="text-[#71717A] text-xs">
                Comunică noua parolă utilizatorului prin email sau telefon.
              </p>
            </div>
          </div>
          
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowResetPasswordDialog(false)}
              className="border-[#262626]"
            >
              Anulează
            </Button>
            <Button
              onClick={resetUserPassword}
              disabled={actionLoading || !newUserPassword || newUserPassword.length < 6}
              className="bg-purple-500 text-white hover:bg-purple-600"
            >
              {actionLoading ? "Se resetează..." : "Resetează Parola"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* User Details Dialog */}
      <Dialog open={showUserDetailsDialog} onOpenChange={setShowUserDetailsDialog}>
        <DialogContent className="bg-[#0A0A0A] border-[#262626] text-white max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Users className="w-5 h-5 text-[#00E676]" />
              Detalii Utilizator
            </DialogTitle>
          </DialogHeader>
          
          {loadingUserDetails ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-[#00E676]"></div>
            </div>
          ) : userDetails ? (
            <div className="space-y-6">
              {/* User Info */}
              <div className="grid md:grid-cols-2 gap-4">
                <div className="bg-[#171717] rounded-lg p-4">
                  <h3 className="text-lg font-bold text-white mb-3">Informații Cont</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-[#71717A]">Nume</span>
                      <span className="text-white">{userDetails.user?.name || 'N/A'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#71717A]">Email</span>
                      <span className="text-white">{userDetails.user?.email}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#71717A]">Rol</span>
                      <Badge className={userDetails.user?.role === 'admin' ? 'bg-red-500/10 text-red-500' : 'bg-blue-500/10 text-blue-500'}>
                        {userDetails.user?.role || 'user'}
                      </Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#71717A]">Înregistrat</span>
                      <span className="text-white">{userDetails.user?.created_at ? new Date(userDetails.user.created_at).toLocaleDateString('ro-RO') : 'N/A'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#71717A]">Ultima activitate</span>
                      <span className="text-white">{userDetails.last_activity ? new Date(userDetails.last_activity).toLocaleDateString('ro-RO') : 'N/A'}</span>
                    </div>
                  </div>
                </div>

                <div className="bg-[#171717] rounded-lg p-4">
                  <h3 className="text-lg font-bold text-white mb-3">Abonament</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-[#71717A]">Plan</span>
                      <Badge className="bg-[#00E676]/10 text-[#00E676] capitalize">{userDetails.subscription?.plan || 'free'}</Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#71717A]">Status</span>
                      <Badge className={
                        userDetails.subscription?.status === 'active' ? 'bg-[#00E676]/10 text-[#00E676]' :
                        userDetails.subscription?.status === 'trialing' ? 'bg-yellow-500/10 text-yellow-500' :
                        'bg-red-500/10 text-red-500'
                      }>
                        {userDetails.subscription?.status || 'expired'}
                      </Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#71717A]">Limită articole</span>
                      <span className="text-white">{userDetails.subscription?.articles_limit || 0}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-[#71717A]">Limită site-uri</span>
                      <span className="text-white">{userDetails.subscription?.sites_limit || 0}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Stats */}
              <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
                <div className="bg-[#171717] rounded-lg p-3 text-center">
                  <p className="text-xl font-bold text-[#00E676]">{userDetails.stats?.total_articles || 0}</p>
                  <p className="text-[#71717A] text-xs">Total Articole</p>
                </div>
                <div className="bg-[#171717] rounded-lg p-3 text-center">
                  <p className="text-xl font-bold text-blue-500">{userDetails.stats?.articles_this_month || 0}</p>
                  <p className="text-[#71717A] text-xs">Articole Luna</p>
                </div>
                <div className="bg-[#171717] rounded-lg p-3 text-center">
                  <p className="text-xl font-bold text-purple-500">{userDetails.stats?.published_articles || 0}</p>
                  <p className="text-[#71717A] text-xs">Publicate</p>
                </div>
                <div className="bg-[#171717] rounded-lg p-3 text-center">
                  <p className="text-xl font-bold text-yellow-500">{userDetails.stats?.outreach_sent || 0}</p>
                  <p className="text-[#71717A] text-xs">Emailuri Trimise</p>
                </div>
                <div className="bg-[#171717] rounded-lg p-3 text-center">
                  <p className="text-xl font-bold text-pink-500">{userDetails.stats?.outreach_responded || 0}</p>
                  <p className="text-[#71717A] text-xs">Răspunsuri</p>
                </div>
              </div>

              {/* API Keys Status */}
              <div className="bg-[#171717] rounded-lg p-4">
                <h3 className="text-lg font-bold text-white mb-3">Chei API Configurate</h3>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(userDetails.api_keys_status || {}).map(([key, configured]) => (
                    <Badge 
                      key={key} 
                      className={configured ? 'bg-[#00E676]/10 text-[#00E676]' : 'bg-red-500/10 text-red-500'}
                    >
                      {configured ? <CheckCircle className="w-3 h-3 mr-1" /> : <AlertTriangle className="w-3 h-3 mr-1" />}
                      {key.toUpperCase()}
                    </Badge>
                  ))}
                </div>
              </div>

              {/* Sites */}
              {userDetails.sites?.length > 0 && (
                <div className="bg-[#171717] rounded-lg p-4">
                  <h3 className="text-lg font-bold text-white mb-3">Site-uri WordPress ({userDetails.sites.length})</h3>
                  <div className="space-y-2">
                    {userDetails.sites.map((site) => (
                      <div key={site.id} className="flex items-center justify-between p-2 bg-[#0A0A0A] rounded">
                        <div>
                          <p className="text-white">{site.site_name || site.site_url}</p>
                          <p className="text-[#71717A] text-xs">{site.niche || 'Fără nișă'}</p>
                        </div>
                        <Badge variant="outline" className="text-[#71717A]">{site.site_url}</Badge>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* GSC Connections */}
              {userDetails.gsc_connections?.length > 0 && (
                <div className="bg-[#171717] rounded-lg p-4">
                  <h3 className="text-lg font-bold text-white mb-3">Google Search Console ({userDetails.gsc_connections.length})</h3>
                  <div className="space-y-2">
                    {userDetails.gsc_connections.map((gsc, idx) => (
                      <div key={idx} className="flex items-center justify-between p-2 bg-[#0A0A0A] rounded">
                        <span className="text-white">{gsc.site_url || gsc.property}</span>
                        <Badge className="bg-[#00E676]/10 text-[#00E676]">Conectat</Badge>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Recent Articles */}
              {userDetails.recent_articles?.length > 0 && (
                <div className="bg-[#171717] rounded-lg p-4">
                  <h3 className="text-lg font-bold text-white mb-3">Articole Recente</h3>
                  <div className="space-y-2">
                    {userDetails.recent_articles.map((article) => (
                      <div key={article.id} className="flex items-center justify-between p-2 bg-[#0A0A0A] rounded">
                        <div className="flex-1 truncate">
                          <p className="text-white truncate">{article.title}</p>
                          <p className="text-[#71717A] text-xs">{article.created_at ? new Date(article.created_at).toLocaleDateString('ro-RO') : ''}</p>
                        </div>
                        <Badge className={
                          article.status === 'published' ? 'bg-[#00E676]/10 text-[#00E676]' :
                          article.status === 'draft' ? 'bg-yellow-500/10 text-yellow-500' :
                          'bg-blue-500/10 text-blue-500'
                        }>
                          {article.status}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <p className="text-[#71717A] text-center py-4">Nu s-au găsit date</p>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AdminDashboard;
