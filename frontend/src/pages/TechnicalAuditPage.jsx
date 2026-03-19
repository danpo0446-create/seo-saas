import { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { useSite } from '@/contexts/SiteContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Search,
  Globe,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  FileText,
  Image,
  Link2,
  Code,
  Clock,
  Loader2,
  RefreshCw,
  ChevronRight,
  Shield,
  Smartphone,
  Zap,
  Wrench,
  Sparkles,
  ArrowUp,
  Lightbulb,
  Printer,
  Trash2
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const gradeColors = {
  A: 'bg-green-500',
  B: 'bg-yellow-500',
  C: 'bg-orange-500',
  D: 'bg-red-500'
};

export default function TechnicalAuditPage() {
  const { currentSite } = useSite();
  const [url, setUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [fixing, setFixing] = useState(false);
  const [currentAudit, setCurrentAudit] = useState(null);
  const [fixResult, setFixResult] = useState(null);
  const [audits, setAudits] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [gscStatus, setGscStatus] = useState({ connected: false });
  const [connectingGsc, setConnectingGsc] = useState(false);

  // Auto-fill URL when site is selected
  useEffect(() => {
    if (currentSite?.site_url) {
      setUrl(currentSite.site_url);
    }
  }, [currentSite]);

  useEffect(() => {
    fetchAudits();
    fetchGscStatus();
  }, [currentSite]);

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

  const handleConnectGsc = async () => {
    setConnectingGsc(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/search-console/auth-url`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      window.location.href = response.data.authorization_url;
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Eroare la conectarea GSC');
      setConnectingGsc(false);
    }
  };

  const fetchAudits = async () => {
    try {
      const token = localStorage.getItem('token');
      const params = currentSite?.id ? `?site_id=${currentSite.id}` : '';
      const response = await axios.get(`${API_URL}/api/seo/audits${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAudits(response.data);
    } catch (error) {
      console.error('Error fetching audits:', error);
    } finally {
      setLoadingHistory(false);
    }
  };

  const runAudit = async () => {
    if (!url.trim()) {
      toast.error('Introdu un URL valid');
      return;
    }

    setLoading(true);
    setFixResult(null);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API_URL}/api/seo/technical-audit`,
        { url: url.trim() },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setCurrentAudit(response.data);
      toast.success('Audit finalizat!');
      fetchAudits();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Eroare la audit');
    } finally {
      setLoading(false);
    }
  };

  const runAutoFix = async () => {
    if (!currentAudit) {
      toast.error('Rulează mai întâi un audit');
      return;
    }

    setFixing(true);
    toast.info('Corectez problemele... Acest proces poate dura 1-2 minute.');
    
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API_URL}/api/seo/auto-fix`,
        { 
          url: currentAudit.url,
          site_id: currentSite?.id 
        },
        { 
          headers: { Authorization: `Bearer ${token}` },
          timeout: 180000
        }
      );
      setFixResult(response.data);
      toast.success(`Corectat! ${response.data.fixes_applied?.length || 0} probleme rezolvate.`);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Eroare la corectare');
    } finally {
      setFixing(false);
    }
  };

  const formatDate = (isoString) => {
    return new Date(isoString).toLocaleString('ro-RO', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const handleDeleteAudit = async (auditId, e) => {
    e.stopPropagation();
    if (!window.confirm('Sigur vrei să ștergi acest audit?')) return;
    
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API_URL}/api/seo/audit/${auditId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Audit șters');
      setAudits(audits.filter(a => a.id !== auditId));
      if (currentAudit?.id === auditId) setCurrentAudit(null);
    } catch (error) {
      toast.error('Eroare la ștergere');
    }
  };

  const handleDeleteAllAudits = async () => {
    if (!window.confirm('Sigur vrei să ștergi TOT istoricul de audituri?')) return;
    
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API_URL}/api/seo/audits/all`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Istoric șters');
      setAudits([]);
      setCurrentAudit(null);
    } catch (error) {
      toast.error('Eroare la ștergere');
    }
  };

  const handlePrint = () => {
    window.print();
  };

  return (
    <div className="space-y-6" data-testid="technical-audit-page">
      {/* Header */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-heading font-bold flex items-center gap-3">
          <Search className="w-8 h-8 text-primary" />
          Technical SEO Audit
        </h1>
        <p className="text-muted-foreground mt-1">
          Scanează site-ul pentru probleme tehnice SEO
          {currentSite && <span className="text-primary ml-1">• {currentSite.site_name || currentSite.site_url}</span>}
        </p>
      </div>

      {/* URL Input */}
      <Card className="bg-card border-border">
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <Input
                placeholder="https://exemplu.com"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="bg-secondary border-border"
                data-testid="audit-url-input"
              />
            </div>
            <Button
              onClick={runAudit}
              disabled={loading}
              className="bg-primary hover:bg-primary/90"
              data-testid="run-audit-btn"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Analizez...
                </>
              ) : (
                <>
                  <Search className="w-4 h-4 mr-2" />
                  Rulează Audit
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Google Search Console Card */}
      {!gscStatus.connected && (
        <Card className="bg-blue-500/10 border-blue-500/30">
          <CardContent className="pt-6">
            <div className="flex flex-col sm:flex-row items-center gap-4">
              <div className="flex-1">
                <h3 className="font-medium text-blue-500 mb-1">Google Search Console</h3>
                <p className="text-sm text-muted-foreground">
                  Conectează GSC pentru date reale despre indexare și erori de crawl
                </p>
              </div>
              <Button
                onClick={handleConnectGsc}
                disabled={connectingGsc}
                className="bg-blue-600 hover:bg-blue-700 text-white"
                data-testid="connect-gsc-audit-btn"
              >
                <Globe className="w-4 h-4 mr-2" />
                {connectingGsc ? 'Se conectează...' : 'Conectează GSC'}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Current Audit Results */}
      {currentAudit && currentAudit.success && (
        <Card className="bg-card border-border">
          <CardHeader>
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Globe className="w-5 h-5 text-primary" />
                  {currentAudit.url}
                </CardTitle>
                <CardDescription>
                  Analizat la {formatDate(currentAudit.analyzed_at)}
                </CardDescription>
              </div>
              <div className="flex items-center gap-4">
                <div className="text-center">
                  <div className={`w-16 h-16 rounded-full ${gradeColors[currentAudit.grade]} flex items-center justify-center`}>
                    <span className="text-2xl font-bold text-white">{currentAudit.grade}</span>
                  </div>
                  <span className="text-sm text-muted-foreground mt-1">Nota</span>
                </div>
                <div className="text-center">
                  <div className="text-3xl font-bold">{currentAudit.score}</div>
                  <span className="text-sm text-muted-foreground">/100</span>
                </div>
                {currentAudit.total_issues > 0 && (
                  <Button
                    onClick={runAutoFix}
                    disabled={fixing}
                    className="bg-green-600 hover:bg-green-700"
                    data-testid="auto-fix-btn"
                  >
                    {fixing ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Corectez...
                      </>
                    ) : (
                      <>
                        <Wrench className="w-4 h-4 mr-2" />
                        Corectează Automat
                      </>
                    )}
                  </Button>
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="issues" className="w-full">
              <TabsList className="grid w-full grid-cols-5 bg-secondary">
                <TabsTrigger value="issues">Probleme ({currentAudit.total_issues})</TabsTrigger>
                <TabsTrigger value="meta">Meta Tags</TabsTrigger>
                <TabsTrigger value="content">Conținut</TabsTrigger>
                <TabsTrigger value="technical">Tehnic</TabsTrigger>
                <TabsTrigger value="links">Link-uri</TabsTrigger>
              </TabsList>

              <TabsContent value="issues" className="mt-4">
                <div className="space-y-2">
                  {currentAudit.issues?.length > 0 ? (
                    currentAudit.issues.map((issue, idx) => (
                      <div key={idx} className="flex items-start gap-3 p-3 bg-secondary/50 rounded-lg">
                        <AlertTriangle className="w-5 h-5 text-yellow-500 flex-shrink-0 mt-0.5" />
                        <span className="text-sm">{issue}</span>
                      </div>
                    ))
                  ) : (
                    <div className="flex items-center gap-3 p-4 bg-green-500/10 rounded-lg">
                      <CheckCircle2 className="w-6 h-6 text-green-500" />
                      <span>Nu s-au găsit probleme majore!</span>
                    </div>
                  )}
                </div>
              </TabsContent>

              <TabsContent value="meta" className="mt-4 space-y-4">
                <div className="grid gap-4">
                  <div className="p-4 bg-secondary/50 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <FileText className="w-4 h-4 text-primary" />
                      <span className="font-medium">Titlu</span>
                      <Badge variant="outline">{currentAudit.meta?.title_length} caractere</Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">{currentAudit.meta?.title || 'Lipsește'}</p>
                  </div>
                  <div className="p-4 bg-secondary/50 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <FileText className="w-4 h-4 text-primary" />
                      <span className="font-medium">Meta Description</span>
                      <Badge variant="outline">{currentAudit.meta?.description_length} caractere</Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">{currentAudit.meta?.description || 'Lipsește'}</p>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 bg-secondary/50 rounded-lg">
                      <span className="font-medium">Canonical</span>
                      <p className="text-sm text-muted-foreground mt-1 truncate">
                        {currentAudit.meta?.canonical || 'Lipsește'}
                      </p>
                    </div>
                    <div className="p-4 bg-secondary/50 rounded-lg">
                      <span className="font-medium">Open Graph</span>
                      <p className="text-sm text-muted-foreground mt-1">
                        {Object.keys(currentAudit.meta?.og_tags || {}).length} tag-uri
                      </p>
                    </div>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="content" className="mt-4 space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-4 bg-secondary/50 rounded-lg text-center">
                    <div className="text-2xl font-bold">{currentAudit.content?.word_count}</div>
                    <span className="text-sm text-muted-foreground">Cuvinte</span>
                  </div>
                  <div className="p-4 bg-secondary/50 rounded-lg text-center">
                    <div className="text-2xl font-bold">{currentAudit.headings?.h1_count}</div>
                    <span className="text-sm text-muted-foreground">H1</span>
                  </div>
                  <div className="p-4 bg-secondary/50 rounded-lg text-center">
                    <div className="text-2xl font-bold">{currentAudit.headings?.h2_count}</div>
                    <span className="text-sm text-muted-foreground">H2</span>
                  </div>
                  <div className="p-4 bg-secondary/50 rounded-lg text-center">
                    <div className="text-2xl font-bold">{currentAudit.images?.total_images}</div>
                    <span className="text-sm text-muted-foreground">Imagini</span>
                  </div>
                </div>
                {currentAudit.headings?.h1_texts?.length > 0 && (
                  <div className="p-4 bg-secondary/50 rounded-lg">
                    <span className="font-medium">H1:</span>
                    <p className="text-sm text-muted-foreground mt-1">{currentAudit.headings.h1_texts[0]}</p>
                  </div>
                )}
              </TabsContent>

              <TabsContent value="technical" className="mt-4 space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div className="p-4 bg-secondary/50 rounded-lg flex items-center gap-3">
                    <Shield className={`w-6 h-6 ${currentAudit.technical?.https ? 'text-green-500' : 'text-red-500'}`} />
                    <div>
                      <div className="font-medium">HTTPS</div>
                      <div className="text-sm text-muted-foreground">
                        {currentAudit.technical?.https ? 'Activ' : 'Inactiv'}
                      </div>
                    </div>
                  </div>
                  <div className="p-4 bg-secondary/50 rounded-lg flex items-center gap-3">
                    <Smartphone className={`w-6 h-6 ${currentAudit.technical?.has_viewport ? 'text-green-500' : 'text-red-500'}`} />
                    <div>
                      <div className="font-medium">Mobile</div>
                      <div className="text-sm text-muted-foreground">
                        {currentAudit.technical?.has_viewport ? 'Optimizat' : 'Neoptimizat'}
                      </div>
                    </div>
                  </div>
                  <div className="p-4 bg-secondary/50 rounded-lg flex items-center gap-3">
                    <Clock className="w-6 h-6 text-primary" />
                    <div>
                      <div className="font-medium">Timp răspuns</div>
                      <div className="text-sm text-muted-foreground">
                        {currentAudit.technical?.response_time?.toFixed(2)}s
                      </div>
                    </div>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="links" className="mt-4 space-y-4">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-4 bg-secondary/50 rounded-lg text-center">
                    <div className="text-2xl font-bold">{currentAudit.links?.total_links}</div>
                    <span className="text-sm text-muted-foreground">Total Link-uri</span>
                  </div>
                  <div className="p-4 bg-secondary/50 rounded-lg text-center">
                    <div className="text-2xl font-bold">{currentAudit.links?.internal_links}</div>
                    <span className="text-sm text-muted-foreground">Interne</span>
                  </div>
                  <div className="p-4 bg-secondary/50 rounded-lg text-center">
                    <div className="text-2xl font-bold">{currentAudit.links?.external_links}</div>
                    <span className="text-sm text-muted-foreground">Externe</span>
                  </div>
                  <div className="p-4 bg-secondary/50 rounded-lg text-center">
                    <div className="text-2xl font-bold">{currentAudit.images?.images_without_alt}</div>
                    <span className="text-sm text-muted-foreground">Imagini fără ALT</span>
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      )}

      {/* Auto-Fix Results */}
      {fixResult && (
        <Card className="bg-card border-border border-green-500/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-green-500">
              <Sparkles className="w-5 h-5" />
              Rezultate Corectare Automată
            </CardTitle>
            <CardDescription>
              Scor original: {fixResult.original_score}/100 → Scor estimat: {fixResult.estimated_new_score}/100
              <span className="ml-2 text-green-500">
                (+{fixResult.estimated_new_score - fixResult.original_score} puncte)
              </span>
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Fixes Applied */}
            {fixResult.fixes_applied?.length > 0 && (
              <div>
                <h4 className="font-medium text-green-500 mb-2 flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4" />
                  Corecții Aplicate ({fixResult.fixes_applied.length})
                </h4>
                <div className="space-y-2">
                  {fixResult.fixes_applied.map((fix, idx) => (
                    <div key={idx} className="flex items-start gap-2 p-2 bg-green-500/10 rounded">
                      <CheckCircle2 className="w-4 h-4 text-green-500 mt-0.5" />
                      <span className="text-sm">{fix}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Suggestions */}
            {fixResult.suggestions?.length > 0 && (
              <div>
                <h4 className="font-medium text-blue-500 mb-2 flex items-center gap-2">
                  <Lightbulb className="w-4 h-4" />
                  Sugestii de Implementat Manual ({fixResult.suggestions.length})
                </h4>
                <ScrollArea className="h-[300px]">
                  <div className="space-y-3 pr-4">
                    {fixResult.suggestions.map((suggestion, idx) => (
                      <div key={idx} className="p-3 bg-blue-500/10 rounded-lg border border-blue-500/30">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge variant="outline" className="text-blue-500 border-blue-500/30">
                            {suggestion.type === 'meta_description' && 'Meta Description'}
                            {suggestion.type === 'title' && 'Titlu'}
                            {suggestion.type === 'open_graph' && 'Open Graph'}
                          </Badge>
                        </div>
                        {suggestion.type !== 'open_graph' ? (
                          <>
                            <p className="text-xs text-muted-foreground mb-1">
                              <strong>Actual:</strong> {suggestion.current || 'Lipsește'}
                            </p>
                            <p className="text-sm text-green-400 mb-2">
                              <strong>Sugerat:</strong> {suggestion.suggested}
                            </p>
                          </>
                        ) : (
                          <div className="text-xs space-y-1 mb-2">
                            {Object.entries(suggestion.suggested || {}).map(([key, value]) => (
                              <p key={key}><code className="text-primary">{key}</code>: {value}</p>
                            ))}
                          </div>
                        )}
                        <p className="text-xs text-muted-foreground">
                          <ArrowUp className="w-3 h-3 inline mr-1" />
                          {suggestion.action}
                        </p>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </div>
            )}

            {/* Fixes Failed */}
            {fixResult.fixes_failed?.length > 0 && (
              <div>
                <h4 className="font-medium text-red-500 mb-2 flex items-center gap-2">
                  <XCircle className="w-4 h-4" />
                  Eșuate ({fixResult.fixes_failed.length})
                </h4>
                <div className="space-y-2">
                  {fixResult.fixes_failed.map((fail, idx) => (
                    <div key={idx} className="flex items-start gap-2 p-2 bg-red-500/10 rounded">
                      <XCircle className="w-4 h-4 text-red-500 mt-0.5" />
                      <span className="text-sm text-red-400">{fail}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Audit History */}
      <Card className="bg-card border-border">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Clock className="w-5 h-5 text-primary" />
              Istoric Audituri
            </CardTitle>
            <div className="flex gap-2">
              {currentAudit && (
                <Button variant="outline" size="sm" onClick={handlePrint}>
                  <Printer className="w-4 h-4 mr-1" />
                  Print
                </Button>
              )}
              {audits.length > 0 && (
                <Button variant="outline" size="sm" onClick={handleDeleteAllAudits} className="text-red-500 hover:text-red-600">
                  <Trash2 className="w-4 h-4 mr-1" />
                  Șterge Tot
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {loadingHistory ? (
            <div className="flex justify-center py-8">
              <Loader2 className="w-6 h-6 animate-spin text-primary" />
            </div>
          ) : audits.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Search className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>Niciun audit încă. Rulează primul tău audit!</p>
            </div>
          ) : (
            <div className="space-y-2">
              {audits.slice(0, 10).map((audit) => (
                <div
                  key={audit.id}
                  className="flex items-center justify-between p-3 bg-secondary/50 rounded-lg hover:bg-secondary/70 cursor-pointer transition-colors"
                  onClick={() => setCurrentAudit(audit)}
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-full ${gradeColors[audit.grade] || 'bg-gray-500'} flex items-center justify-center`}>
                      <span className="text-sm font-bold text-white">{audit.grade}</span>
                    </div>
                    <div>
                      <p className="font-medium truncate max-w-[300px]">{audit.url}</p>
                      <p className="text-xs text-muted-foreground">{formatDate(audit.analyzed_at)}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <div className="font-bold">{audit.score}/100</div>
                      <div className="text-xs text-muted-foreground">{audit.total_issues} probleme</div>
                    </div>
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      onClick={(e) => handleDeleteAudit(audit.id, e)}
                      className="text-red-500 hover:text-red-600 hover:bg-red-500/10"
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
