import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { toast } from 'sonner';
import { useSite } from '@/contexts/SiteContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Search,
  Globe,
  Loader2,
  Clock,
  CheckCircle2,
  XCircle,
  Send,
  RefreshCw,
  Zap,
  FileText,
  ExternalLink,
  TrendingUp,
  AlertTriangle,
  Shield,
  MapPin,
  Bot,
  Activity,
  FileSearch,
  ListChecks,
  Printer,
  Trash2
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function IndexingPage() {
  const navigate = useNavigate();
  const { currentSite, sites } = useSite();
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [bulkLoading, setBulkLoading] = useState(false);
  const [auditLoading, setAuditLoading] = useState(false);
  const [history, setHistory] = useState([]);
  const [audits, setAudits] = useState([]);
  const [currentAudit, setCurrentAudit] = useState(null);
  const [status, setStatus] = useState(null);
  const [loadingStatus, setLoadingStatus] = useState(false);
  const [activeTab, setActiveTab] = useState('indexare');
  const [gscStatus, setGscStatus] = useState({ connected: false });
  const [gscStats, setGscStats] = useState(null);
  const [connectingGsc, setConnectingGsc] = useState(false);

  useEffect(() => {
    fetchGscStatus();
    if (currentSite?.id) {
      fetchHistory();
      fetchStatus();
      fetchAudits();
    }
  }, [currentSite]);

  useEffect(() => {
    if (gscStatus.connected) {
      fetchGscStats();
    }
  }, [gscStatus.connected, currentSite]);

  const fetchGscStatus = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/search-console/status`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setGscStatus(response.data);
    } catch (error) {
      console.error('Error fetching GSC status:', error);
    }
  };

  const fetchGscStats = async () => {
    if (!currentSite?.site_url) return;
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/search-console/stats?site_url=${encodeURIComponent(currentSite.site_url)}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setGscStats(response.data);
    } catch (error) {
      console.error('Error fetching GSC stats:', error);
      setGscStats(null);
    }
  };

  const handleConnectGsc = async () => {
    setConnectingGsc(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/search-console/auth-url`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      window.location.href = response.data.authorization_url;
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Eroare la conectarea GSC. Verifică configurarea în backend.');
      setConnectingGsc(false);
    }
  };

  const fetchHistory = async () => {
    try {
      const token = localStorage.getItem('token');
      const params = currentSite?.id ? `?site_id=${currentSite.id}` : '';
      const response = await axios.get(`${API_URL}/api/indexing/history${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setHistory(response.data);
    } catch (error) {
      console.error('Error fetching history:', error);
    }
  };

  const fetchStatus = async () => {
    if (!currentSite?.id) return;
    
    setLoadingStatus(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/indexing/status/${currentSite.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStatus(response.data);
    } catch (error) {
      console.error('Error fetching status:', error);
    } finally {
      setLoadingStatus(false);
    }
  };

  const fetchAudits = async () => {
    if (!currentSite?.id) return;
    
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/indexing/audits?site_id=${currentSite.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAudits(response.data || []);
      // Set the most recent audit as current
      if (response.data && response.data.length > 0) {
        setCurrentAudit(response.data[0]);
      }
    } catch (error) {
      console.error('Error fetching audits:', error);
    }
  };

  const runFullAudit = async () => {
    if (!currentSite?.id) {
      toast.error('Selectează un site');
      return;
    }

    setAuditLoading(true);
    toast.info('Rulează auditul complet de indexare... Poate dura 1-2 minute.');
    
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API_URL}/api/indexing/full-audit`,
        { site_id: currentSite.id },
        { headers: { Authorization: `Bearer ${token}` }, timeout: 180000 }
      );
      
      setCurrentAudit(response.data);
      toast.success(`Audit complet! Scor: ${response.data.overall_score}/100 (${response.data.grade})`);
      fetchAudits();
      fetchHistory();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Eroare la audit');
    } finally {
      setAuditLoading(false);
    }
  };

  const submitUrl = async () => {
    if (!url.trim()) {
      toast.error('Introdu un URL valid');
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API_URL}/api/indexing/submit-url`,
        { url: url.trim(), site_id: currentSite?.id },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      const successCount = response.data.total_success || 0;
      toast.success(`URL trimis pentru indexare! ${successCount} servicii au acceptat.`);
      setUrl('');
      fetchHistory();
      fetchStatus();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Eroare la trimitere');
    } finally {
      setLoading(false);
    }
  };

  const bulkIndex = async () => {
    if (!currentSite?.id) {
      toast.error('Selectează un site');
      return;
    }

    setBulkLoading(true);
    toast.info('Trimit toate articolele pentru indexare...');
    
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API_URL}/api/indexing/bulk-submit`,
        { site_id: currentSite.id },
        { headers: { Authorization: `Bearer ${token}` }, timeout: 120000 }
      );
      
      toast.success(`${response.data.urls_submitted} articole trimise pentru indexare!`);
      fetchHistory();
      fetchStatus();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Eroare la indexare în masă');
    } finally {
      setBulkLoading(false);
    }
  };

  const formatDate = (isoString) => {
    if (!isoString) return '-';
    return new Date(isoString).toLocaleString('ro-RO', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getServiceBadge = (services) => {
    if (!services) return null;
    
    const badges = [];
    
    if (services.indexnow?.results?.success?.length > 0) {
      services.indexnow.results.success.forEach(s => {
        badges.push(
          <Badge key={s} className="bg-green-500/20 text-green-500 border-green-500/30">
            <CheckCircle2 className="w-3 h-3 mr-1" />
            {s}
          </Badge>
        );
      });
    }
    
    if (services.sitemap_ping?.success?.length > 0) {
      services.sitemap_ping.success.forEach(s => {
        badges.push(
          <Badge key={`ping-${s}`} className="bg-blue-500/20 text-blue-500 border-blue-500/30">
            <CheckCircle2 className="w-3 h-3 mr-1" />
            {s} (ping)
          </Badge>
        );
      });
    }
    
    return badges;
  };

  const getGradeColor = (grade) => {
    switch(grade) {
      case 'A': return 'text-green-500 bg-green-500/20 border-green-500/30';
      case 'B': return 'text-blue-500 bg-blue-500/20 border-blue-500/30';
      case 'C': return 'text-yellow-500 bg-yellow-500/20 border-yellow-500/30';
      case 'D': return 'text-red-500 bg-red-500/20 border-red-500/30';
      default: return 'text-gray-500 bg-gray-500/20 border-gray-500/30';
    }
  };

  const handleDeleteHistory = async (historyId, e) => {
    e.stopPropagation();
    if (!window.confirm('Sigur vrei să ștergi această înregistrare?')) return;
    
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API_URL}/api/indexing/history/${historyId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Înregistrare ștearsă');
      setHistory(history.filter(h => h.id !== historyId));
    } catch (error) {
      toast.error('Eroare la ștergere');
    }
  };

  const handleDeleteAllHistory = async () => {
    if (!window.confirm('Sigur vrei să ștergi TOT istoricul de indexare?')) return;
    
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API_URL}/api/indexing/history/all`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Istoric șters');
      setHistory([]);
    } catch (error) {
      toast.error('Eroare la ștergere');
    }
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-6" data-testid="indexing-page">
      {/* Header */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-heading font-bold flex items-center gap-3">
          <Search className="w-8 h-8 text-primary" />
          Indexare Google & Bing
        </h1>
        <p className="text-muted-foreground mt-1">
          Audit complet și indexare automată pentru site-ul tău
          {currentSite && <span className="text-primary ml-1">• {currentSite.site_name || currentSite.site_url}</span>}
        </p>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full grid-cols-2 bg-secondary">
          <TabsTrigger value="indexare" className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
            <Send className="w-4 h-4 mr-2" />
            Indexare URL-uri
          </TabsTrigger>
          <TabsTrigger value="audit" className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
            <Shield className="w-4 h-4 mr-2" />
            Audit Site-Wide
          </TabsTrigger>
        </TabsList>

        {/* Tab: Indexare URL-uri */}
        <TabsContent value="indexare" className="space-y-6 mt-6">
          {/* Status Card */}
          {currentSite && (
            <Card className="bg-card border-border">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-primary" />
                  Status Indexare - {currentSite.site_name || currentSite.site_url}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {loadingStatus ? (
                  <div className="flex justify-center py-4">
                    <Loader2 className="w-6 h-6 animate-spin text-primary" />
                  </div>
                ) : status ? (
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-4 bg-secondary/50 rounded-lg text-center">
                      <div className="text-2xl font-bold">{status.total_articles}</div>
                      <span className="text-sm text-muted-foreground">Articole Publicate</span>
                    </div>
                    <div className="p-4 bg-secondary/50 rounded-lg text-center">
                      <div className="text-2xl font-bold">{status.indexing_requests}</div>
                      <span className="text-sm text-muted-foreground">Cereri Indexare</span>
                    </div>
                    <div className="p-4 bg-secondary/50 rounded-lg text-center col-span-2">
                      <div className="text-sm font-medium">Ultima Indexare</div>
                      <span className="text-sm text-muted-foreground">
                        {status.last_indexed ? formatDate(status.last_indexed) : 'Niciodată'}
                      </span>
                    </div>
                  </div>
                ) : (
                  <p className="text-center text-muted-foreground py-4">
                    Selectează un site pentru a vedea statusul
                  </p>
                )}
              </CardContent>
            </Card>
          )}

          {/* Submit URL */}
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Send className="w-5 h-5 text-primary" />
                Trimite URL pentru Indexare
              </CardTitle>
              <CardDescription>
                Trimite un URL specific sau toate articolele site-ului
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-col sm:flex-row gap-4">
                <div className="flex-1">
                  <Input
                    placeholder="https://site-ul-tau.com/articol-nou"
                    value={url}
                    onChange={(e) => setUrl(e.target.value)}
                    className="bg-secondary border-border"
                    data-testid="indexing-url-input"
                  />
                </div>
                <Button
                  onClick={submitUrl}
                  disabled={loading}
                  className="bg-primary hover:bg-primary/90"
                  data-testid="submit-url-btn"
                >
                  {loading ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Trimit...
                    </>
                  ) : (
                    <>
                      <Send className="w-4 h-4 mr-2" />
                      Trimite URL
                    </>
                  )}
                </Button>
              </div>
              
              {currentSite && (
                <div className="pt-4 border-t border-border">
                  <Button
                    onClick={bulkIndex}
                    disabled={bulkLoading}
                    variant="outline"
                    className="w-full border-green-500/50 text-green-500 hover:bg-green-500/10"
                    data-testid="bulk-index-btn"
                  >
                    {bulkLoading ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Indexez toate articolele...
                      </>
                    ) : (
                      <>
                        <Zap className="w-4 h-4 mr-2" />
                        Indexează Toate Articolele din {currentSite.site_name || 'Site'}
                      </>
                    )}
                  </Button>
                  <p className="text-xs text-muted-foreground mt-2 text-center">
                    Trimite toate articolele publicate către Google, Bing și Yandex pentru indexare rapidă
                  </p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Info Card */}
          <Card className="bg-blue-500/10 border-blue-500/30">
            <CardContent className="pt-6">
              <div className="flex items-start gap-4">
                <AlertTriangle className="w-6 h-6 text-blue-500 flex-shrink-0" />
                <div className="text-sm">
                  <p className="font-medium text-blue-500 mb-2">Cum funcționează indexarea automată?</p>
                  <ul className="space-y-1 text-muted-foreground">
                    <li>• <strong>IndexNow</strong> - Protocol instant pentru Bing, Yandex (rezultate în minute)</li>
                    <li>• <strong>Sitemap Ping</strong> - Notifică Google și Bing despre actualizări</li>
                    <li>• <strong>Auto-indexare</strong> - Fiecare articol nou e trimis automat la publicare</li>
                    <li>• Indexarea nu garantează poziția în rezultate, doar că Google știe de pagină</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* History */}
          <Card className="bg-card border-border">
            <CardHeader>
              <div className="flex items-center justify-between">
                <CardTitle className="flex items-center gap-2">
                  <Clock className="w-5 h-5 text-primary" />
                  Istoric Indexare
                </CardTitle>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => { fetchHistory(); fetchStatus(); }}
                  >
                    <RefreshCw className="w-4 h-4 mr-1" />
                    Refresh
                  </Button>
                  {history.length > 0 && (
                    <Button variant="outline" size="sm" onClick={handleDeleteAllHistory} className="text-red-500 hover:text-red-600">
                      <Trash2 className="w-4 h-4 mr-1" />
                      Șterge Tot
                    </Button>
                  )}
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {history.length === 0 ? (
                <div className="text-center py-8 text-muted-foreground">
                  <Search className="w-12 h-12 mx-auto mb-4 opacity-50" />
                  <p>Nicio cerere de indexare încă</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {history.map((item) => (
                    <div
                      key={item.id}
                      className="p-4 bg-secondary/50 rounded-lg"
                    >
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                        <div className="flex items-center gap-2">
                          {item.total_success > 0 ? (
                            <CheckCircle2 className="w-5 h-5 text-green-500" />
                          ) : (
                            <XCircle className="w-5 h-5 text-red-500" />
                          )}
                          <span className="font-medium truncate max-w-[300px]">
                            {item.type === 'bulk' 
                              ? `Indexare în masă (${item.urls_submitted} URL-uri)`
                              : item.url
                            }
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-muted-foreground">
                            {formatDate(item.created_at)}
                          </span>
                          <Button 
                            variant="ghost" 
                            size="sm" 
                            onClick={(e) => handleDeleteHistory(item.id, e)}
                            className="text-red-500 hover:text-red-600 hover:bg-red-500/10 h-6 w-6 p-0"
                          >
                            <Trash2 className="w-3 h-3" />
                          </Button>
                        </div>
                      </div>
                      
                      <div className="flex flex-wrap gap-2">
                        {getServiceBadge(item.services || item)}
                        {item.total_success !== undefined && (
                          <Badge variant="outline">
                            {item.total_success} servicii reușite
                          </Badge>
                        )}
                      </div>
                      
                      {item.url && (
                        <a 
                          href={item.url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-xs text-primary hover:underline mt-2 inline-flex items-center gap-1"
                        >
                          <ExternalLink className="w-3 h-3" />
                          Deschide URL
                        </a>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tab: Audit Site-Wide */}
        <TabsContent value="audit" className="space-y-6 mt-6">
          {/* Run Audit Button */}
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5 text-primary" />
                Audit Complet de Indexare
              </CardTitle>
              <CardDescription>
                Verifică robots.txt, sitemap, status Google și trimite toate paginile pentru indexare
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button
                onClick={runFullAudit}
                disabled={auditLoading || !currentSite}
                className="w-full bg-primary hover:bg-primary/90 h-12 text-base"
                data-testid="run-full-audit-btn"
              >
                {auditLoading ? (
                  <>
                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                    Analizez site-ul... (poate dura 1-2 minute)
                  </>
                ) : (
                  <>
                    <FileSearch className="w-5 h-5 mr-2" />
                    Rulează Audit Complet pentru {currentSite?.site_name || 'Site'}
                  </>
                )}
              </Button>
              <p className="text-xs text-muted-foreground mt-3 text-center">
                Verifică robots.txt, găsește toate paginile din sitemap, pingează Google & Bing, 
                și trimite totul la IndexNow
              </p>
            </CardContent>
          </Card>

          {/* Google Search Console Card - Always Visible */}
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Search className="w-5 h-5 text-primary" />
                Google Search Console
                {gscStatus.connected ? (
                  <Badge className="bg-green-500/20 text-green-500 border-green-500/30 ml-2">
                    Conectat
                  </Badge>
                ) : (
                  <Badge className="bg-yellow-500/20 text-yellow-500 border-yellow-500/30 ml-2">
                    Neconectat
                  </Badge>
                )}
              </CardTitle>
              <CardDescription>
                {gscStatus.connected 
                  ? 'Statistici de indexare și performanță din GSC'
                  : 'Conectează GSC pentru date reale despre indexarea site-ului'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {!gscStatus.connected ? (
                <Button
                  onClick={handleConnectGsc}
                  disabled={connectingGsc}
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white h-12"
                  data-testid="connect-gsc-main-btn"
                >
                  <Globe className="w-5 h-5 mr-2" />
                  {connectingGsc ? 'Se conectează...' : 'Conectează Google Search Console'}
                </Button>
              ) : gscStats ? (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-4 bg-secondary/50 rounded-lg text-center">
                    <div className="text-2xl font-bold text-green-500">{gscStats.clicks?.toLocaleString() || 0}</div>
                    <span className="text-sm text-muted-foreground">Click-uri</span>
                  </div>
                  <div className="p-4 bg-secondary/50 rounded-lg text-center">
                    <div className="text-2xl font-bold text-blue-500">{gscStats.impressions?.toLocaleString() || 0}</div>
                    <span className="text-sm text-muted-foreground">Impresii</span>
                  </div>
                  <div className="p-4 bg-secondary/50 rounded-lg text-center">
                    <div className="text-2xl font-bold text-primary">{gscStats.ctr ? `${(gscStats.ctr * 100).toFixed(1)}%` : '0%'}</div>
                    <span className="text-sm text-muted-foreground">CTR</span>
                  </div>
                  <div className="p-4 bg-secondary/50 rounded-lg text-center">
                    <div className="text-2xl font-bold text-yellow-500">{gscStats.position?.toFixed(1) || '-'}</div>
                    <span className="text-sm text-muted-foreground">Poziție Medie</span>
                  </div>
                </div>
              ) : (
                <div className="flex items-center justify-center py-4">
                  <Loader2 className="w-6 h-6 animate-spin text-primary mr-2" />
                  <span className="text-muted-foreground">Se încarcă datele GSC...</span>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Current Audit Results */}
          {currentAudit && (
            <Card className="bg-card border-border">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2">
                    <Activity className="w-5 h-5 text-primary" />
                    Rezultate Audit
                  </CardTitle>
                  <Badge className={`text-2xl px-4 py-2 ${getGradeColor(currentAudit.grade)}`}>
                    {currentAudit.grade}
                  </Badge>
                </div>
                <CardDescription>
                  Scor: {currentAudit.overall_score}/100 • {formatDate(currentAudit.timestamp)}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Score Progress */}
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span>Scor General</span>
                    <span className="font-bold">{currentAudit.overall_score}%</span>
                  </div>
                  <Progress value={currentAudit.overall_score} className="h-3" />
                </div>

                {/* Audit Sections */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Robots.txt */}
                  <div className="p-4 bg-secondary/50 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <Bot className="w-5 h-5 text-primary" />
                      <span className="font-medium">robots.txt</span>
                      {currentAudit.robots_txt?.exists ? (
                        <CheckCircle2 className="w-4 h-4 text-green-500 ml-auto" />
                      ) : (
                        <XCircle className="w-4 h-4 text-red-500 ml-auto" />
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {currentAudit.robots_txt?.exists 
                        ? 'Fișier robots.txt găsit'
                        : 'robots.txt lipsește'}
                    </p>
                    {currentAudit.robots_txt?.issues?.length > 0 && (
                      <ul className="text-xs text-yellow-500 mt-2 space-y-1">
                        {currentAudit.robots_txt.issues.slice(0, 3).map((issue, i) => (
                          <li key={i}>• {issue}</li>
                        ))}
                      </ul>
                    )}
                  </div>

                  {/* Pages Discovered */}
                  <div className="p-4 bg-secondary/50 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <MapPin className="w-5 h-5 text-primary" />
                      <span className="font-medium">Pagini Descoperite</span>
                      <span className="ml-auto font-bold text-primary">
                        {currentAudit.pages_discovered?.pages_found || 0}
                      </span>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {currentAudit.pages_discovered?.sitemaps_found?.length > 0
                        ? `${currentAudit.pages_discovered.sitemaps_found.length} sitemap-uri găsite`
                        : 'Fără sitemap'}
                    </p>
                    {currentAudit.pages_discovered?.sitemaps_found?.length > 0 && (
                      <div className="text-xs text-green-500 mt-2">
                        {currentAudit.pages_discovered.sitemaps_found[0]}
                      </div>
                    )}
                  </div>

                  {/* IndexNow Submission */}
                  <div className="p-4 bg-secondary/50 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <Zap className="w-5 h-5 text-primary" />
                      <span className="font-medium">IndexNow</span>
                      {currentAudit.indexnow_submission?.indexnow?.success?.length > 0 ? (
                        <CheckCircle2 className="w-4 h-4 text-green-500 ml-auto" />
                      ) : (
                        <XCircle className="w-4 h-4 text-yellow-500 ml-auto" />
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {currentAudit.indexnow_submission?.total_urls || 0} URL-uri trimise
                    </p>
                    {currentAudit.indexnow_submission?.indexnow?.success?.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {currentAudit.indexnow_submission.indexnow.success.map(s => (
                          <Badge key={s} className="bg-green-500/20 text-green-500 text-xs">
                            {s}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Ping Results */}
                  <div className="p-4 bg-secondary/50 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <Globe className="w-5 h-5 text-primary" />
                      <span className="font-medium">Sitemap Ping</span>
                      {currentAudit.ping_results?.success?.length > 0 ? (
                        <CheckCircle2 className="w-4 h-4 text-green-500 ml-auto" />
                      ) : (
                        <XCircle className="w-4 h-4 text-yellow-500 ml-auto" />
                      )}
                    </div>
                    <p className="text-sm text-muted-foreground">
                      Ping trimis către motoarele de căutare
                    </p>
                    {currentAudit.ping_results?.success?.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-2">
                        {currentAudit.ping_results.success.map(s => (
                          <Badge key={s} className="bg-blue-500/20 text-blue-500 text-xs">
                            {s}
                          </Badge>
                        ))}
                      </div>
                    )}
                  </div>
                </div>

                {/* Issues & Recommendations */}
                {(currentAudit.issues?.length > 0 || currentAudit.recommendations?.length > 0) && (
                  <div className="space-y-4 pt-4 border-t border-border">
                    {currentAudit.issues?.length > 0 && (
                      <div>
                        <h4 className="font-medium text-red-500 mb-2 flex items-center gap-2">
                          <XCircle className="w-4 h-4" />
                          Probleme Găsite ({currentAudit.issues.length})
                        </h4>
                        <ul className="space-y-1 text-sm text-muted-foreground">
                          {currentAudit.issues.map((issue, i) => (
                            <li key={i} className="flex items-start gap-2">
                              <span className="text-red-500">•</span>
                              {issue}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                    
                    {currentAudit.recommendations?.length > 0 && (
                      <div>
                        <h4 className="font-medium text-blue-500 mb-2 flex items-center gap-2">
                          <ListChecks className="w-4 h-4" />
                          Recomandări ({currentAudit.recommendations.length})
                        </h4>
                        <ul className="space-y-2 text-sm text-muted-foreground">
                          {currentAudit.recommendations.map((rec, i) => (
                            <li key={i} className="flex items-start gap-2">
                              <span className="text-blue-500">•</span>
                              <span className="flex-1">{rec}</span>
                              {rec.toLowerCase().includes('google search console') && !gscStatus.connected && (
                                <Button
                                  onClick={handleConnectGsc}
                                  disabled={connectingGsc}
                                  size="sm"
                                  className="bg-blue-600 hover:bg-blue-700 text-white text-xs h-7"
                                >
                                  {connectingGsc ? 'Se conectează...' : 'Conectează GSC'}
                                </Button>
                              )}
                            </li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                )}

                {/* Google Status */}
                {currentAudit.google_status && (
                  <div className="pt-4 border-t border-border">
                    <h4 className="font-medium mb-3 flex items-center gap-2">
                      <Search className="w-4 h-4 text-primary" />
                      Google Search Console
                      {gscStatus.connected && (
                        <Badge className="bg-green-500/20 text-green-500 border-green-500/30 ml-2">
                          Conectat
                        </Badge>
                      )}
                    </h4>
                    {currentAudit.google_status.success ? (
                      <div className="grid grid-cols-3 gap-4">
                        <div className="p-3 bg-secondary/50 rounded-lg text-center">
                          <div className="text-xl font-bold text-primary">
                            {currentAudit.google_status.indexed_pages_visible || 0}
                          </div>
                          <span className="text-xs text-muted-foreground">Pagini Indexate</span>
                        </div>
                        <div className="p-3 bg-secondary/50 rounded-lg text-center">
                          <div className="text-xl font-bold text-green-500">
                            {currentAudit.google_status.total_clicks_28d || 0}
                          </div>
                          <span className="text-xs text-muted-foreground">Click-uri (28 zile)</span>
                        </div>
                        <div className="p-3 bg-secondary/50 rounded-lg text-center">
                          <div className="text-xl font-bold text-blue-500">
                            {currentAudit.google_status.total_impressions_28d || 0}
                          </div>
                          <span className="text-xs text-muted-foreground">Impresii (28 zile)</span>
                        </div>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        <p className="text-sm text-yellow-500">
                          {currentAudit.google_status.error || currentAudit.google_status.recommendation || 
                           'Conectează Google Search Console pentru date complete'}
                        </p>
                        <Button
                          onClick={handleConnectGsc}
                          disabled={connectingGsc}
                          className="bg-blue-600 hover:bg-blue-700 text-white"
                          data-testid="connect-gsc-btn"
                        >
                          <Globe className="w-4 h-4 mr-2" />
                          {connectingGsc ? 'Se conectează...' : 'Conectează Google Search Console'}
                        </Button>
                      </div>
                    )}
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Audit History */}
          {audits.length > 0 && (
            <Card className="bg-card border-border">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="w-5 h-5 text-primary" />
                  Istoric Audituri
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {audits.slice(0, 10).map((audit) => (
                    <div
                      key={audit.id}
                      className="p-3 bg-secondary/50 rounded-lg flex items-center justify-between cursor-pointer hover:bg-secondary/70 transition-colors"
                      onClick={() => setCurrentAudit(audit)}
                    >
                      <div className="flex items-center gap-3">
                        <Badge className={`${getGradeColor(audit.grade)}`}>
                          {audit.grade}
                        </Badge>
                        <div>
                          <div className="font-medium">{audit.overall_score}/100</div>
                          <div className="text-xs text-muted-foreground">
                            {audit.pages_discovered?.pages_found || 0} pagini • 
                            {audit.issues?.length || 0} probleme
                          </div>
                        </div>
                      </div>
                      <span className="text-xs text-muted-foreground">
                        {formatDate(audit.timestamp)}
                      </span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Info about Site-Wide Indexing */}
          <Card className="bg-green-500/10 border-green-500/30">
            <CardContent className="pt-6">
              <div className="flex items-start gap-4">
                <Shield className="w-6 h-6 text-green-500 flex-shrink-0" />
                <div className="text-sm">
                  <p className="font-medium text-green-500 mb-2">Ce face Auditul Complet?</p>
                  <ul className="space-y-1 text-muted-foreground">
                    <li>• <strong>Verifică robots.txt</strong> - Asigură-te că Google poate accesa site-ul</li>
                    <li>• <strong>Descoperă toate paginile</strong> - Parsează sitemap-ul și găsește toate URL-urile</li>
                    <li>• <strong>Ping Google & Bing</strong> - Notifică motoarele de căutare despre sitemap</li>
                    <li>• <strong>IndexNow Bulk</strong> - Trimite toate paginile pentru indexare instantă</li>
                    <li>• <strong>Verifică GSC</strong> - Statistici din Google Search Console (dacă e conectat)</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
