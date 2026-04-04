import { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '@/contexts/AuthContext';
import { useSite } from '@/contexts/SiteContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { toast } from 'sonner';
import { 
  Link, 
  Search,
  ExternalLink,
  Send,
  Loader2,
  CheckCircle2,
  Clock,
  Sparkles,
  AlertCircle,
  Mail,
  FileText,
  Eye,
  Edit3,
  Trash2,
  RefreshCw,
  Inbox,
  CheckCheck,
  XCircle,
  Zap
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function BacklinksPage() {
  const [backlinks, setBacklinks] = useState([]);
  const [requests, setRequests] = useState([]);
  const [outreachList, setOutreachList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [searchingNew, setSearchingNew] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [requesting, setRequesting] = useState(null);
  const [preparingOutreach, setPreparingOutreach] = useState(null);
  const [sendingEmail, setSendingEmail] = useState(null);
  const [activeTab, setActiveTab] = useState('opportunities');
  const [pendingOutreach, setPendingOutreach] = useState([]);
  const [outreachStats, setOutreachStats] = useState({});
  const [approvingEmail, setApprovingEmail] = useState(null);
  const [rejectingEmail, setRejectingEmail] = useState(null);
  const [approvingAll, setApprovingAll] = useState(false);
  
  // Outreach dialog state
  const [showOutreachDialog, setShowOutreachDialog] = useState(false);
  const [currentOutreach, setCurrentOutreach] = useState(null);
  const [editingEmail, setEditingEmail] = useState(false);
  const [editSubject, setEditSubject] = useState('');
  const [editBody, setEditBody] = useState('');
  
  const { getAuthHeaders } = useAuth();
  const { currentSite, sites, loading: sitesLoading } = useSite();

  useEffect(() => {
    if (sitesLoading) return; // Wait for sites to load
    
    if (currentSite?.niche) {
      fetchBacklinks();
      fetchPendingOutreach();
    } else {
      setBacklinks([]);
      setPendingOutreach([]);
      setLoading(false);
    }
  }, [currentSite?.id, sitesLoading]);
  
  // Separate effect for less critical data
  useEffect(() => {
    if (sitesLoading) return;
    fetchRequests();
    fetchOutreach();
    fetchOutreachStats();
  }, []);

  const fetchBacklinks = async () => {
    if (!currentSite?.niche) return;
    
    try {
      setLoading(true);
      const response = await axios.get(`${API}/backlinks/niche/${encodeURIComponent(currentSite.niche)}`, { 
        headers: getAuthHeaders() 
      });
      setBacklinks(response.data);
    } catch (error) {
      console.error('Failed to fetch backlinks:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchRequests = async () => {
    try {
      const response = await axios.get(`${API}/backlinks/requests`, { headers: getAuthHeaders() });
      setRequests(response.data);
    } catch (error) {
      console.error('Failed to fetch requests:', error);
    }
  };

  const fetchOutreach = async () => {
    try {
      const response = await axios.get(`${API}/backlinks/outreach`, { headers: getAuthHeaders() });
      setOutreachList(response.data);
    } catch (error) {
      console.error('Failed to fetch outreach:', error);
    }
  };

  const fetchPendingOutreach = async () => {
    try {
      const response = await axios.get(`${API}/backlinks/outreach/pending`, { headers: getAuthHeaders() });
      // Filter by current site if selected
      let filtered = response.data;
      if (currentSite?.id) {
        filtered = response.data.filter(o => o.site_id === currentSite.id);
      }
      setPendingOutreach(filtered);
    } catch (error) {
      console.error('Failed to fetch pending outreach:', error);
    }
  };

  const fetchOutreachStats = async () => {
    try {
      const response = await axios.get(`${API}/backlinks/outreach/stats`, { headers: getAuthHeaders() });
      setOutreachStats(response.data);
    } catch (error) {
      console.error('Failed to fetch outreach stats:', error);
    }
  };

  const handleApproveEmail = async (outreachId) => {
    setApprovingEmail(outreachId);
    try {
      await axios.post(`${API}/backlinks/outreach/${outreachId}/approve`, {}, { headers: getAuthHeaders() });
      toast.success('Email aprobat și trimis!');
      fetchPendingOutreach();
      fetchOutreach();
      fetchOutreachStats();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Eroare la trimiterea email-ului');
    } finally {
      setApprovingEmail(null);
    }
  };

  const handleRejectEmail = async (outreachId) => {
    setRejectingEmail(outreachId);
    try {
      await axios.post(`${API}/backlinks/outreach/${outreachId}/reject`, {}, { headers: getAuthHeaders() });
      toast.success('Email respins');
      fetchPendingOutreach();
      fetchOutreachStats();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Eroare la respingerea email-ului');
    } finally {
      setRejectingEmail(null);
    }
  };

  const handleApproveAll = async () => {
    setApprovingAll(true);
    try {
      const response = await axios.post(`${API}/backlinks/outreach/approve-all`, {}, { headers: getAuthHeaders() });
      toast.success(`${response.data.sent} email-uri trimise din ${response.data.total}!`);
      fetchPendingOutreach();
      fetchOutreach();
      fetchOutreachStats();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Eroare la trimiterea email-urilor');
    } finally {
      setApprovingAll(false);
    }
  };

  const handleSearchNewOpportunities = async () => {
    if (!currentSite?.id) {
      toast.error('Selectează un site mai întâi');
      return;
    }
    
    setSearchingNew(true);
    try {
      // Search opportunities ONLY for current site
      const response = await axios.post(`${API}/backlinks/search-opportunities-for-site`, 
        { site_id: currentSite.id },
        { headers: getAuthHeaders() }
      );
      const data = response.data;
      toast.success(`${data.backlinks_found} oportunități noi + ${data.emails_generated} email-uri generate pentru ${currentSite.site_name || currentSite.site_url}!`);
      fetchBacklinks();
      fetchPendingOutreach();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Eroare la căutarea oportunităților');
    } finally {
      setSearchingNew(false);
    }
  };

  const handleGenerateBacklinks = async () => {
    if (!currentSite?.niche) {
      toast.error('Site-ul selectat nu are o nișă definită. Editează site-ul și adaugă nișa.');
      return;
    }

    setGenerating(true);
    try {
      const response = await axios.get(`${API}/backlinks/generate/${encodeURIComponent(currentSite.niche)}`, { 
        headers: getAuthHeaders() 
      });
      setBacklinks(response.data);
      toast.success(`${response.data.length} oportunități de backlink generate pentru "${currentSite.niche}"!`);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Eroare la generarea backlinks');
    } finally {
      setGenerating(false);
    }
  };

  const handlePrepareOutreach = async (backlink) => {
    if (!currentSite?.id) {
      toast.error('Selectează un site mai întâi');
      return;
    }

    setPreparingOutreach(backlink.id);
    try {
      const response = await axios.post(
        `${API}/backlinks/outreach/prepare`,
        null,
        { 
          headers: getAuthHeaders(),
          params: {
            backlink_id: backlink.id,
            site_id: currentSite.id
          }
        }
      );
      
      setCurrentOutreach(response.data);
      setEditSubject(response.data.email.subject);
      setEditBody(response.data.email.body);
      setShowOutreachDialog(true);
      setEditingEmail(false);
      
      // Add to requests if not already there
      if (!isRequested(backlink.id)) {
        setRequests([...requests, {
          id: backlink.id,
          domain: backlink.domain,
          status: 'outreach_prepared',
          type: backlink.type,
          price: backlink.price
        }]);
      }
      
      toast.success('Email de outreach pregătit!');
      fetchOutreach();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Eroare la pregătirea outreach');
    } finally {
      setPreparingOutreach(null);
    }
  };

  const handleSendEmail = async (outreachId) => {
    setSendingEmail(outreachId || currentOutreach?.id);
    try {
      // If editing, save changes first
      if (editingEmail && currentOutreach) {
        await axios.put(
          `${API}/backlinks/outreach/${currentOutreach.id}`,
          null,
          {
            headers: getAuthHeaders(),
            params: {
              subject: editSubject,
              body: editBody
            }
          }
        );
      }
      
      const id = outreachId || currentOutreach?.id;
      const response = await axios.post(
        `${API}/backlinks/outreach/${id}/send`,
        {},
        { headers: getAuthHeaders() }
      );
      
      toast.success(response.data.message);
      setShowOutreachDialog(false);
      setCurrentOutreach(null);
      fetchOutreach();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Eroare la trimiterea emailului');
    } finally {
      setSendingEmail(null);
    }
  };

  const handleDeleteOutreach = async (outreachId) => {
    try {
      await axios.delete(`${API}/backlinks/outreach/${outreachId}`, {
        headers: getAuthHeaders()
      });
      toast.success('Outreach șters');
      fetchOutreach();
    } catch (error) {
      toast.error('Eroare la ștergere');
    }
  };

  const [sendingAll, setSendingAll] = useState(false);
  
  const handleSendAllDrafts = async () => {
    const drafts = outreachList.filter(o => o.status === 'draft');
    if (drafts.length === 0) {
      toast.info('Nu există emailuri draft de trimis');
      return;
    }
    
    setSendingAll(true);
    let sent = 0;
    let errors = 0;
    
    for (const draft of drafts) {
      try {
        await axios.post(
          `${API}/backlinks/outreach/${draft.id}/send`,
          {},
          { headers: getAuthHeaders() }
        );
        sent++;
      } catch (error) {
        errors++;
      }
    }
    
    setSendingAll(false);
    
    if (sent > 0) {
      toast.success(`${sent} emailuri trimise cu succes!`);
    }
    if (errors > 0) {
      toast.error(`${errors} emailuri au eșuat`);
    }
    
    fetchOutreach();
  };

  const handleMarkResponded = async (outreachId, responseType) => {
    try {
      await axios.post(
        `${API}/backlinks/outreach/${outreachId}/mark-responded`,
        null,
        {
          headers: getAuthHeaders(),
          params: { response_type: responseType }
        }
      );
      toast.success('Status actualizat');
      fetchOutreach();
    } catch (error) {
      toast.error('Eroare la actualizare');
    }
  };

  const isRequested = (backlinkId) => {
    return requests.some(r => r.id === backlinkId || r.domain === backlinks.find(b => b.id === backlinkId)?.domain);
  };

  const hasOutreach = (backlinkId) => {
    return outreachList.some(o => o.backlink_id === backlinkId);
  };

  const filteredBacklinks = backlinks.filter(bl => 
    bl.domain.toLowerCase().includes(searchTerm.toLowerCase()) ||
    bl.category?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    bl.type?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const getDaColor = (da) => {
    if (da >= 60) return 'text-green-500';
    if (da >= 40) return 'text-yellow-500';
    return 'text-orange-500';
  };

  const getTypeColor = (type) => {
    const colors = {
      'Guest Post': 'bg-blue-500/10 text-blue-500 border-blue-500/20',
      'Directory': 'bg-green-500/10 text-green-500 border-green-500/20',
      'Forum': 'bg-purple-500/10 text-purple-500 border-purple-500/20',
      'Blog Comment': 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
      'Resource Page': 'bg-pink-500/10 text-pink-500 border-pink-500/20',
      'Partnership': 'bg-cyan-500/10 text-cyan-500 border-cyan-500/20',
    };
    return colors[type] || 'bg-gray-500/10 text-gray-500 border-gray-500/20';
  };

  const getStatusBadge = (status) => {
    const styles = {
      'draft': { class: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20', text: 'Draft' },
      'sent': { class: 'bg-blue-500/10 text-blue-500 border-blue-500/20', text: 'Trimis' },
      'responded': { class: 'bg-green-500/10 text-green-500 border-green-500/20', text: 'Răspuns' },
    };
    return styles[status] || styles['draft'];
  };

  if (!currentSite) {
    return (
      <div className="space-y-8" data-testid="backlinks-page">
        <div>
          <h1 className="font-heading text-3xl font-bold">Manager Backlinks</h1>
          <p className="text-muted-foreground mt-1">
            Generează oportunități de backlink bazate pe nișa site-ului
          </p>
        </div>
        <Card className="bg-card border-border">
          <CardContent className="flex flex-col items-center justify-center py-16">
            <AlertCircle className="w-16 h-16 text-yellow-500 mb-4" />
            <h3 className="text-lg font-semibold mb-2">Selectează un site</h3>
            <p className="text-muted-foreground text-center">
              Selectează un site din dropdown-ul din stânga sus pentru a vedea și genera backlinks relevante pentru nișa acelui site.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-8" data-testid="backlinks-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="font-heading text-3xl font-bold">Manager Backlinks</h1>
          <p className="text-muted-foreground mt-1">
            Oportunități de backlink pentru <span className="text-primary font-medium">{currentSite.site_name || currentSite.site_url}</span>
          </p>
          {currentSite.niche && (
            <Badge variant="outline" className="mt-2">Nișă: {currentSite.niche}</Badge>
          )}
        </div>
        <div className="flex gap-2">
          <Button
            onClick={handleSearchNewOpportunities}
            disabled={searchingNew}
            variant="outline"
            className="border-primary/50"
            data-testid="search-new-button"
          >
            {searchingNew ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Se caută...
              </>
            ) : (
              <>
                <Zap className="w-4 h-4 mr-2" />
                Caută Noi Oportunități
              </>
            )}
          </Button>
          <Button
            onClick={handleGenerateBacklinks}
            disabled={generating || !currentSite.niche}
            className="bg-primary text-primary-foreground hover:bg-primary/90"
            data-testid="generate-backlinks-button"
          >
            {generating ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Se generează...
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 mr-2" />
                Generează Backlinks AI
              </>
            )}
          </Button>
        </div>
      </div>

      {!currentSite.niche && (
        <Card className="bg-yellow-500/10 border-yellow-500/20">
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-yellow-500" />
              <p className="text-sm">
                Site-ul <strong>{currentSite.site_name}</strong> nu are o nișă definită. 
                Mergi la <strong>WordPress</strong>, șterge site-ul și adaugă-l din nou cu nișa specificată.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-5 gap-4">
        <Card className="bg-card border-border">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/10">
                <Link className="w-5 h-5 text-primary" />
              </div>
              <div>
                <p className="text-2xl font-bold font-heading">{backlinks.length}</p>
                <p className="text-sm text-muted-foreground">Oportunități găsite</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-card border-border">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-orange-500/10">
                <Clock className="w-5 h-5 text-orange-500" />
              </div>
              <div>
                <p className="text-2xl font-bold font-heading">{pendingOutreach.length}</p>
                <p className="text-sm text-muted-foreground">De aprobat</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-card border-border">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-yellow-500/10">
                <Mail className="w-5 h-5 text-yellow-500" />
              </div>
              <div>
                <p className="text-2xl font-bold font-heading">
                  {outreachList.filter(o => o.status === 'draft').length}
                </p>
                <p className="text-sm text-muted-foreground">Drafturi outreach</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-card border-border">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-500/10">
                <Send className="w-5 h-5 text-blue-500" />
              </div>
              <div>
                <p className="text-2xl font-bold font-heading">
                  {outreachList.filter(o => o.status === 'sent').length}
                </p>
                <p className="text-sm text-muted-foreground">Emailuri trimise</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-card border-border">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-green-500/10">
                <CheckCircle2 className="w-5 h-5 text-green-500" />
              </div>
              <div>
                <p className="text-2xl font-bold font-heading">
                  {outreachList.filter(o => o.status === 'responded').length}
                </p>
                <p className="text-sm text-muted-foreground">Răspunsuri primite</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-secondary">
          <TabsTrigger value="opportunities" className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
            <Search className="w-4 h-4 mr-2" />
            Oportunități ({backlinks.length})
          </TabsTrigger>
          <TabsTrigger value="pending" className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
            <Clock className="w-4 h-4 mr-2" />
            De Aprobat ({pendingOutreach.length})
          </TabsTrigger>
          <TabsTrigger value="outreach" className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
            <Mail className="w-4 h-4 mr-2" />
            Outreach ({outreachList.length})
          </TabsTrigger>
        </TabsList>

        {/* Pending Approval Tab */}
        <TabsContent value="pending" className="space-y-6">
          {pendingOutreach.length > 0 && (
            <Card className="bg-card border-border">
              <CardContent className="pt-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold">Email-uri generate automat</h3>
                    <p className="text-sm text-muted-foreground">
                      Aceste email-uri au fost create automat pentru oportunități noi de backlink
                    </p>
                  </div>
                  <Button
                    onClick={handleApproveAll}
                    disabled={approvingAll || pendingOutreach.length === 0}
                    className="bg-green-600 hover:bg-green-700 text-white"
                    data-testid="approve-all-button"
                  >
                    {approvingAll ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Se trimit...
                      </>
                    ) : (
                      <>
                        <CheckCheck className="w-4 h-4 mr-2" />
                        Aprobă & Trimite Toate ({pendingOutreach.length})
                      </>
                    )}
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {pendingOutreach.length === 0 ? (
            <Card className="bg-card border-border">
              <CardContent className="flex flex-col items-center justify-center py-16">
                <Inbox className="w-16 h-16 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">Niciun email în așteptare</h3>
                <p className="text-muted-foreground text-center">
                  Email-urile de outreach generate automat zilnic vor apărea aici pentru aprobare
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {pendingOutreach.map((outreach) => (
                <Card key={outreach.id} className="bg-card border-border">
                  <CardContent className="pt-6">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 space-y-3">
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className="bg-yellow-500/10 text-yellow-500 border-yellow-500/20">
                            Auto-generat
                          </Badge>
                          <span className="text-sm text-muted-foreground">
                            → {outreach.contact_email}
                          </span>
                        </div>
                        <div>
                          <p className="font-medium text-sm text-muted-foreground">Domeniu țintă:</p>
                          <p className="font-semibold">{outreach.backlink_domain}</p>
                        </div>
                        <div>
                          <p className="font-medium text-sm text-muted-foreground">Subject:</p>
                          <p className="font-medium">{outreach.email_subject}</p>
                        </div>
                        <div>
                          <p className="font-medium text-sm text-muted-foreground">Articol promovat:</p>
                          <a 
                            href={outreach.article_url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="text-primary hover:underline flex items-center gap-1"
                          >
                            {outreach.article_title}
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        </div>
                        <div>
                          <p className="font-medium text-sm text-muted-foreground mb-2">Conținut email:</p>
                          <div className="bg-secondary/50 rounded-lg p-3 text-sm whitespace-pre-wrap max-h-40 overflow-y-auto">
                            {outreach.email_body}
                          </div>
                        </div>
                      </div>
                      <div className="flex flex-col gap-2">
                        <Button
                          onClick={() => handleApproveEmail(outreach.id)}
                          disabled={approvingEmail === outreach.id}
                          className="bg-green-600 hover:bg-green-700 text-white"
                          data-testid={`approve-email-${outreach.id}`}
                        >
                          {approvingEmail === outreach.id ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            <>
                              <CheckCircle2 className="w-4 h-4 mr-1" />
                              Aprobă
                            </>
                          )}
                        </Button>
                        <Button
                          onClick={() => handleRejectEmail(outreach.id)}
                          disabled={rejectingEmail === outreach.id}
                          variant="outline"
                          className="text-red-500 border-red-500/30 hover:bg-red-500/10"
                          data-testid={`reject-email-${outreach.id}`}
                        >
                          {rejectingEmail === outreach.id ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                          ) : (
                            <>
                              <XCircle className="w-4 h-4 mr-1" />
                              Respinge
                            </>
                          )}
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Opportunities Tab */}
        <TabsContent value="opportunities" className="space-y-6">
          {/* Search */}
          {backlinks.length > 0 && (
            <Card className="bg-card border-border">
              <CardContent className="pt-6">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                  <Input
                    placeholder="Caută domeniu, categorie sau tip..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10 bg-secondary border-border"
                    data-testid="backlinks-search-input"
                  />
                </div>
              </CardContent>
            </Card>
          )}

          {/* Backlinks List */}
          {backlinks.length === 0 ? (
            <Card className="bg-card border-border">
              <CardContent className="flex flex-col items-center justify-center py-16">
                <Link className="w-16 h-16 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">Niciun backlink generat</h3>
                <p className="text-muted-foreground text-center mb-6">
                  {currentSite.niche 
                    ? `Click pe "Generează Backlinks AI" pentru a găsi oportunități pentru nișa "${currentSite.niche}"`
                    : 'Adaugă o nișă site-ului pentru a genera backlinks relevante'}
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredBacklinks.map((backlink) => (
                <Card 
                  key={backlink.id} 
                  className="bg-card border-border hover:border-primary/30 transition-colors"
                >
                  <CardContent className="pt-6">
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-2">
                          <a 
                            href={`https://${backlink.domain}`} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="font-medium truncate hover:text-primary transition-colors"
                          >
                            {backlink.domain}
                          </a>
                          <ExternalLink className="w-3 h-3 text-muted-foreground flex-shrink-0" />
                        </div>
                        <div className="flex flex-wrap gap-1">
                          <Badge className={getTypeColor(backlink.type)}>
                            {backlink.type}
                          </Badge>
                          {backlink.price === 0 && (
                            <Badge className="bg-green-500/10 text-green-500 border-green-500/20">
                              Gratuit
                            </Badge>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-3 gap-4 mb-4 text-center">
                      <div>
                        <p className={`text-lg font-bold font-mono ${getDaColor(backlink.da)}`}>
                          {backlink.da}
                        </p>
                        <p className="text-xs text-muted-foreground">DA</p>
                      </div>
                      <div>
                        <p className={`text-lg font-bold font-mono ${getDaColor(backlink.pa)}`}>
                          {backlink.pa}
                        </p>
                        <p className="text-xs text-muted-foreground">PA</p>
                      </div>
                      <div>
                        <p className="text-lg font-bold font-mono text-primary">
                          {backlink.price === 0 ? 'Free' : `$${backlink.price}`}
                        </p>
                        <p className="text-xs text-muted-foreground">Preț</p>
                      </div>
                    </div>

                    {backlink.contact_info && (
                      <p className="text-xs text-muted-foreground mb-3 truncate">
                        📧 {backlink.contact_info}
                      </p>
                    )}

                    <Button
                      className={`w-full ${
                        hasOutreach(backlink.id) 
                          ? 'bg-green-500/20 text-green-500 border-green-500/30' 
                          : 'bg-primary text-primary-foreground hover:bg-primary/90'
                      }`}
                      disabled={preparingOutreach === backlink.id}
                      onClick={() => handlePrepareOutreach(backlink)}
                      data-testid={`outreach-${backlink.id}`}
                    >
                      {preparingOutreach === backlink.id ? (
                        <>
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                          Se pregătește...
                        </>
                      ) : hasOutreach(backlink.id) ? (
                        <>
                          <Eye className="w-4 h-4 mr-2" />
                          Vezi Outreach
                        </>
                      ) : (
                        <>
                          <Mail className="w-4 h-4 mr-2" />
                          Pregătește Outreach
                        </>
                      )}
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        {/* Outreach Tab */}
        <TabsContent value="outreach" className="space-y-4">
          {/* Send All Drafts Button */}
          {outreachList.filter(o => o.status === 'draft').length > 0 && (
            <div className="flex justify-end">
              <Button
                onClick={handleSendAllDrafts}
                disabled={sendingAll}
                className="bg-[#00E676] text-black hover:bg-[#00E676]/90"
                data-testid="send-all-drafts-btn"
              >
                {sendingAll ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Send className="w-4 h-4 mr-2" />
                )}
                Trimite toate ({outreachList.filter(o => o.status === 'draft').length})
              </Button>
            </div>
          )}
          
          {outreachList.length === 0 ? (
            <Card className="bg-card border-border">
              <CardContent className="flex flex-col items-center justify-center py-16">
                <Inbox className="w-16 h-16 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">Niciun outreach</h3>
                <p className="text-muted-foreground text-center">
                  Pregătește primul outreach din tab-ul "Oportunități"
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {outreachList.map((outreach) => {
                const statusBadge = getStatusBadge(outreach.status);
                return (
                  <Card key={outreach.id} className="bg-card border-border">
                    <CardContent className="py-4">
                      <div className="flex items-center justify-between gap-4">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="font-medium">{outreach.backlink_domain}</span>
                            <Badge className={statusBadge.class}>{statusBadge.text}</Badge>
                          </div>
                          <p className="text-sm text-muted-foreground truncate">
                            📄 {outreach.article_title}
                          </p>
                          <p className="text-xs text-muted-foreground mt-1">
                            📧 {outreach.contact_email || 'Fără email'}
                          </p>
                        </div>
                        
                        <div className="flex items-center gap-2">
                          {outreach.status === 'draft' && (
                            <>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => {
                                  setCurrentOutreach(outreach);
                                  setEditSubject(outreach.email_subject);
                                  setEditBody(outreach.email_body);
                                  setShowOutreachDialog(true);
                                  setEditingEmail(false);
                                }}
                              >
                                <Eye className="w-4 h-4" />
                              </Button>
                              <Button
                                size="sm"
                                onClick={() => handleSendEmail(outreach.id)}
                                disabled={sendingEmail === outreach.id || !outreach.contact_email}
                                className="bg-primary text-primary-foreground"
                              >
                                {sendingEmail === outreach.id ? (
                                  <Loader2 className="w-4 h-4 animate-spin" />
                                ) : (
                                  <Send className="w-4 h-4" />
                                )}
                              </Button>
                            </>
                          )}
                          
                          {outreach.status === 'sent' && (
                            <>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleMarkResponded(outreach.id, 'positive')}
                                className="text-green-500 border-green-500/30"
                              >
                                <CheckCheck className="w-4 h-4" />
                              </Button>
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handleMarkResponded(outreach.id, 'negative')}
                                className="text-red-500 border-red-500/30"
                              >
                                <XCircle className="w-4 h-4" />
                              </Button>
                            </>
                          )}
                          
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeleteOutreach(outreach.id)}
                            className="text-destructive hover:text-destructive"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Outreach Preview/Edit Dialog */}
      <Dialog open={showOutreachDialog} onOpenChange={setShowOutreachDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Mail className="w-5 h-5 text-primary" />
              Outreach Email
            </DialogTitle>
            <DialogDescription>
              {currentOutreach?.backlink_domain} - {editingEmail ? 'Editare' : 'Preview'}
            </DialogDescription>
          </DialogHeader>

          <div className="flex-1 overflow-y-auto space-y-4 py-4">
            {/* Article Info */}
            <div className="p-3 rounded-lg bg-secondary/50">
              <p className="text-xs text-muted-foreground mb-1">Articol selectat:</p>
              <p className="text-sm font-medium">{currentOutreach?.article?.title || currentOutreach?.article_title}</p>
              {(currentOutreach?.article?.wordpress_url || currentOutreach?.article_url) && (
                <a 
                  href={currentOutreach?.article?.wordpress_url || currentOutreach?.article_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs text-primary hover:underline"
                >
                  {currentOutreach?.article?.wordpress_url || currentOutreach?.article_url}
                </a>
              )}
            </div>

            {/* Email Preview/Edit */}
            <div className="space-y-3">
              <div>
                <Label className="text-sm font-medium">Subiect</Label>
                {editingEmail ? (
                  <Input
                    value={editSubject}
                    onChange={(e) => setEditSubject(e.target.value)}
                    className="mt-1 bg-secondary"
                  />
                ) : (
                  <p className="mt-1 p-2 rounded bg-secondary text-sm">{editSubject}</p>
                )}
              </div>
              
              <div>
                <Label className="text-sm font-medium">Corp email</Label>
                {editingEmail ? (
                  <Textarea
                    value={editBody}
                    onChange={(e) => setEditBody(e.target.value)}
                    className="mt-1 bg-secondary min-h-[200px]"
                  />
                ) : (
                  <div className="mt-1 p-3 rounded bg-secondary text-sm whitespace-pre-wrap">
                    {editBody}
                  </div>
                )}
              </div>

              <div className="p-2 rounded bg-muted/50">
                <p className="text-xs text-muted-foreground">
                  📧 Se va trimite la: <strong>{currentOutreach?.contact_email || 'Email nedisponibil'}</strong>
                </p>
              </div>
            </div>
          </div>

          <DialogFooter className="flex-shrink-0 gap-2">
            <Button
              variant="outline"
              onClick={() => setEditingEmail(!editingEmail)}
            >
              <Edit3 className="w-4 h-4 mr-2" />
              {editingEmail ? 'Anulează Editarea' : 'Editează'}
            </Button>
            <Button
              variant="outline"
              onClick={() => setShowOutreachDialog(false)}
            >
              Închide
            </Button>
            <Button
              onClick={() => handleSendEmail()}
              disabled={sendingEmail || !currentOutreach?.contact_email}
              className="bg-primary text-primary-foreground"
            >
              {sendingEmail ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Se trimite...
                </>
              ) : (
                <>
                  <Send className="w-4 h-4 mr-2" />
                  Trimite Email
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
