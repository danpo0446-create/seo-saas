import { useState, useEffect } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { useSite } from '@/contexts/SiteContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Brain,
  Globe,
  Loader2,
  Clock,
  TrendingUp,
  Target,
  FileText,
  ChevronRight,
  Sparkles,
  BarChart3,
  Lightbulb,
  Wrench,
  CheckCircle2,
  XCircle,
  ArrowUp,
  Printer,
  Trash2
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const niches = [
  { value: 'general', label: 'General' },
  { value: 'ecommerce', label: 'E-commerce' },
  { value: 'tech', label: 'Tehnologie' },
  { value: 'health', label: 'Sănătate' },
  { value: 'finance', label: 'Finanțe' },
  { value: 'travel', label: 'Călătorii' },
  { value: 'food', label: 'Food & Cooking' },
  { value: 'fashion', label: 'Fashion' },
  { value: 'education', label: 'Educație' },
  { value: 'real-estate', label: 'Imobiliare' },
  { value: 'automotive', label: 'Auto' },
  { value: 'beauty', label: 'Beauty' },
  { value: 'fitness', label: 'Fitness' },
  { value: 'maritime', label: 'Maritim / Seafarer' },
  { value: 'baby', label: 'Baby & Kids' },
  { value: 'jobs', label: 'Jobs & Careers' },
  { value: 'women', label: 'Women / Ladies' },
  { value: 'shopping', label: 'Shopping' }
];

const gradeColors = {
  A: 'bg-green-500',
  B: 'bg-yellow-500', 
  C: 'bg-orange-500',
  D: 'bg-red-500'
};

export default function BusinessAnalysisPage() {
  const { currentSite } = useSite();
  const [url, setUrl] = useState('');
  const [niche, setNiche] = useState('general');
  const [loading, setLoading] = useState(false);
  const [fixing, setFixing] = useState(false);
  const [currentAnalysis, setCurrentAnalysis] = useState(null);
  const [fixResult, setFixResult] = useState(null);
  const [analyses, setAnalyses] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [gscStatus, setGscStatus] = useState({ connected: false });
  const [connectingGsc, setConnectingGsc] = useState(false);

  // Auto-fill URL and niche when site is selected
  useEffect(() => {
    if (currentSite) {
      if (currentSite.site_url) {
        setUrl(currentSite.site_url);
      }
      
      // Auto-detect niche from site configuration
      const siteNiche = (currentSite.niche || '').toLowerCase();
      
      if (siteNiche) {
        // Define keyword mappings for each niche (Romanian + English)
        const nicheKeywords = {
          'maritime': ['maritime', 'seafarer', 'shipping', 'seaman', 'sailor', 'vessel', 'nautical', 'stcw', 'crewing', 'marinar'],
          'jobs': ['job', 'career', 'employment', 'hiring', 'recruit', 'employer', 'cariere', 'angajare', 'locuri de munca'],
          'baby': ['baby', 'child', 'infant', 'toddler', 'childhood', 'copii', 'bebelus', 'copil', 'mama', 'parenting'],
          'fashion': ['fashion', 'moda', 'clothing', 'îmbrăcăminte', 'haine', 'style', 'rochii'],
          'women': ['women', 'ladies', 'feminin', 'damă', 'lenjerie', 'feminină', 'femei'],
          'ecommerce': ['shop', 'store', 'buy', 'sell', 'product', 'magazin', 'cumpara', 'vanzare', 'e-commerce', 'shopping'],
          'tech': ['tech', 'software', 'digital', 'computer', 'programming', 'technology', 'tehnologie', 'it'],
          'health': ['health', 'medical', 'sănătate', 'fitness', 'wellness', 'sanatate', 'doctor'],
          'education': ['education', 'training', 'learning', 'school', 'course', 'educație', 'scoala', 'cursuri'],
          'travel': ['travel', 'tourism', 'vacation', 'călătorii', 'hotel', 'calatorie', 'turism'],
          'food': ['food', 'cooking', 'recipe', 'restaurant', 'mâncare', 'rețete', 'bucatarie', 'mancare'],
          'beauty': ['beauty', 'cosmetic', 'makeup', 'skincare', 'frumusețe', 'cosmetice'],
          'finance': ['finance', 'money', 'banking', 'investment', 'finanțe', 'bani', 'investitii', 'financiar'],
          'real-estate': ['real estate', 'property', 'imobiliare', 'apartament', 'casă', 'casa', 'imobiliar'],
          'automotive': ['auto', 'car', 'vehicle', 'masina', 'automobil', 'automotive'],
          'fitness': ['fitness', 'gym', 'sport', 'exercise', 'workout', 'antrenament'],
          'shopping': ['shopping', 'cumpărături', 'cumparaturi', 'outlet', 'reduceri']
        };
        
        // Find the best matching niche
        let bestMatch = 'general';
        let maxMatches = 0;
        
        for (const [nicheValue, keywords] of Object.entries(nicheKeywords)) {
          const matches = keywords.filter(kw => siteNiche.includes(kw)).length;
          if (matches > maxMatches) {
            maxMatches = matches;
            bestMatch = nicheValue;
          }
        }
        
        // If no keyword match, try exact value match
        if (maxMatches === 0) {
          const exactMatch = niches.find(n => 
            n.value.toLowerCase() === siteNiche || 
            n.label.toLowerCase() === siteNiche
          );
          if (exactMatch) {
            bestMatch = exactMatch.value;
          }
        }
        
        setNiche(bestMatch);
        console.log(`Auto-detected niche for "${currentSite.site_name}": ${bestMatch} (from: ${siteNiche})`);
      } else {
        setNiche('general');
      }
    }
  }, [currentSite?.id]); // Only re-run when site ID changes

  useEffect(() => {
    fetchAnalyses();
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

  const fetchAnalyses = async () => {
    try {
      const token = localStorage.getItem('token');
      const params = currentSite?.id ? `?site_id=${currentSite.id}` : '';
      const response = await axios.get(`${API_URL}/api/seo/business-analyses${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAnalyses(response.data);
    } catch (error) {
      console.error('Error fetching analyses:', error);
    } finally {
      setLoadingHistory(false);
    }
  };

  const runAnalysis = async () => {
    if (!url.trim()) {
      toast.error('Introdu un URL valid');
      return;
    }

    setLoading(true);
    setFixResult(null);
    toast.info('Analizez site-ul... Acest proces poate dura 1-2 minute.');
    
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API_URL}/api/seo/business-analysis`,
        { url: url.trim(), niche },
        { 
          headers: { Authorization: `Bearer ${token}` },
          timeout: 180000 // 3 minute timeout
        }
      );
      setCurrentAnalysis(response.data);
      toast.success('Analiză finalizată!');
      fetchAnalyses();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Eroare la analiză');
    } finally {
      setLoading(false);
    }
  };

  const runAutoFix = async () => {
    if (!currentAnalysis) {
      toast.error('Rulează mai întâi o analiză');
      return;
    }

    setFixing(true);
    toast.info('Corectez problemele... Acest proces poate dura 1-2 minute.');
    
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API_URL}/api/seo/auto-fix`,
        { 
          url: currentAnalysis.url,
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

  const handleDeleteAnalysis = async (analysisId, e) => {
    e.stopPropagation();
    if (!window.confirm('Sigur vrei să ștergi această analiză?')) return;
    
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API_URL}/api/seo/analysis/${analysisId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Analiză ștearsă');
      setAnalyses(analyses.filter(a => a.id !== analysisId));
      if (currentAnalysis?.id === analysisId) setCurrentAnalysis(null);
    } catch (error) {
      toast.error('Eroare la ștergere');
    }
  };

  const handleDeleteAllAnalyses = async () => {
    if (!window.confirm('Sigur vrei să ștergi TOT istoricul de analize?')) return;
    
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API_URL}/api/seo/analyses/all`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Istoric șters');
      setAnalyses([]);
      setCurrentAnalysis(null);
    } catch (error) {
      toast.error('Eroare la ștergere');
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const renderAnalysisContent = (content) => {
    if (!content) return null;
    
    // Split by main sections
    const sections = content.split(/(?=\d+\.\s*[📊🎯📈🔧📱🔗📅💡])/);
    
    return sections.map((section, idx) => {
      if (!section.trim()) return null;
      
      // Extract emoji and title
      const titleMatch = section.match(/^(\d+\.\s*[📊🎯📈🔧📱🔗📅💡]\s*[A-ZĂÂÎȘȚ\s]+)/m);
      const title = titleMatch ? titleMatch[1] : '';
      const body = titleMatch ? section.replace(title, '') : section;
      
      return (
        <div key={idx} className="mb-6">
          {title && (
            <h3 className="text-lg font-bold text-primary mb-3">{title}</h3>
          )}
          <div className="prose prose-sm prose-invert max-w-none">
            {body.split('\n').map((line, lineIdx) => {
              const trimmedLine = line.trim();
              if (!trimmedLine) return null;
              
              // Check if it's a bullet point
              if (trimmedLine.startsWith('-') || trimmedLine.startsWith('•')) {
                return (
                  <div key={lineIdx} className="flex items-start gap-2 mb-2 ml-4">
                    <span className="text-primary mt-1">•</span>
                    <span className="text-sm text-muted-foreground">{trimmedLine.substring(1).trim()}</span>
                  </div>
                );
              }
              
              // Check if it's a sub-header
              if (trimmedLine.match(/^[A-ZĂÂÎȘȚ]/)) {
                return (
                  <p key={lineIdx} className="text-sm text-foreground mb-2">{trimmedLine}</p>
                );
              }
              
              return (
                <p key={lineIdx} className="text-sm text-muted-foreground mb-2">{trimmedLine}</p>
              );
            })}
          </div>
        </div>
      );
    });
  };

  return (
    <div className="space-y-6" data-testid="business-analysis-page">
      {/* Header */}
      <div>
        <h1 className="text-2xl sm:text-3xl font-heading font-bold flex items-center gap-3">
          <Brain className="w-8 h-8 text-primary" />
          Business Analysis AI
        </h1>
        <p className="text-muted-foreground mt-1">
          Analiză AI pentru strategie SEO personalizată
          {currentSite && <span className="text-primary ml-1">• {currentSite.site_name || currentSite.site_url}</span>}
        </p>
      </div>

      {/* Input Form */}
      <Card className="bg-card border-border">
        <CardContent className="pt-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <Input
                placeholder="https://site-ul-tau.com"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="bg-secondary border-border"
                data-testid="analysis-url-input"
              />
            </div>
            <div className="w-full md:w-48">
              <Select value={niche} onValueChange={setNiche}>
                <SelectTrigger className="bg-secondary border-border">
                  <SelectValue placeholder="Selectează nișa" />
                </SelectTrigger>
                <SelectContent className="bg-card border-border">
                  {niches.map((n) => (
                    <SelectItem key={n.value} value={n.value}>
                      {n.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <Button
              onClick={runAnalysis}
              disabled={loading}
              className="bg-primary hover:bg-primary/90"
              data-testid="run-analysis-btn"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Analizez...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 mr-2" />
                  Generează Analiză
                </>
              )}
            </Button>
          </div>
          {loading && (
            <div className="mt-4 p-4 bg-primary/10 rounded-lg">
              <div className="flex items-center gap-3">
                <Loader2 className="w-5 h-5 animate-spin text-primary" />
                <div>
                  <p className="font-medium">Analizez site-ul...</p>
                  <p className="text-sm text-muted-foreground">
                    AI-ul analizează structura, conținutul și generează recomandări personalizate. 
                    Acest proces poate dura 1-2 minute.
                  </p>
                </div>
              </div>
            </div>
          )}
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
                  Conectează GSC pentru date reale despre trafic și performanță SEO
                </p>
              </div>
              <Button
                onClick={handleConnectGsc}
                disabled={connectingGsc}
                className="bg-blue-600 hover:bg-blue-700 text-white"
                data-testid="connect-gsc-analysis-btn"
              >
                <Globe className="w-4 h-4 mr-2" />
                {connectingGsc ? 'Se conectează...' : 'Conectează GSC'}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Current Analysis Results */}
      {currentAnalysis && currentAnalysis.success && (
        <Card className="bg-card border-border">
          <CardHeader>
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Globe className="w-5 h-5 text-primary" />
                  {currentAnalysis.url}
                </CardTitle>
                <CardDescription className="flex items-center gap-4 mt-2">
                  <span>Analizat la {formatDate(currentAnalysis.analyzed_at)}</span>
                  <Badge variant="outline">{niches.find(n => n.value === currentAnalysis.niche)?.label || currentAnalysis.niche}</Badge>
                </CardDescription>
              </div>
              <div className="flex items-center gap-6">
                <div className="text-center">
                  <div className={`w-14 h-14 rounded-full ${gradeColors[currentAnalysis.technical_grade] || 'bg-gray-500'} flex items-center justify-center`}>
                    <span className="text-xl font-bold text-white">{currentAnalysis.technical_grade}</span>
                  </div>
                  <span className="text-xs text-muted-foreground mt-1">Scor Tehnic</span>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold">{currentAnalysis.technical_score}</div>
                  <span className="text-xs text-muted-foreground">/100</span>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold">{currentAnalysis.word_count}</div>
                  <span className="text-xs text-muted-foreground">Cuvinte</span>
                </div>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {/* Technical Issues Summary */}
            {currentAnalysis.technical_issues?.length > 0 && (
              <div className="mb-6 p-4 bg-yellow-500/10 rounded-lg border border-yellow-500/30">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                  <div>
                    <h4 className="font-semibold mb-2 flex items-center gap-2">
                      <Target className="w-4 h-4 text-yellow-500" />
                      Probleme Tehnice Identificate ({currentAnalysis.technical_issues.length})
                    </h4>
                    <div className="flex flex-wrap gap-2">
                      {currentAnalysis.technical_issues.slice(0, 5).map((issue, idx) => (
                        <Badge key={idx} variant="outline" className="text-yellow-500 border-yellow-500/30">
                          {issue}
                        </Badge>
                      ))}
                    </div>
                  </div>
                  <Button
                    onClick={runAutoFix}
                    disabled={fixing}
                    className="bg-green-600 hover:bg-green-700 shrink-0"
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
                </div>
              </div>
            )}

            {/* AI Analysis */}
            <div className="bg-secondary/30 rounded-lg p-6">
              <h3 className="text-lg font-bold mb-4 flex items-center gap-2">
                <Lightbulb className="w-5 h-5 text-primary" />
                Strategie SEO Personalizată
              </h3>
              <ScrollArea className="h-[600px] pr-4">
                <div className="space-y-4">
                  {renderAnalysisContent(currentAnalysis.analysis)}
                </div>
              </ScrollArea>
            </div>
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
                <ScrollArea className="h-[250px]">
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

      {/* Analysis History */}
      <Card className="bg-card border-border">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Clock className="w-5 h-5 text-primary" />
              Istoric Analize
            </CardTitle>
            <div className="flex gap-2">
              {currentAnalysis && (
                <Button variant="outline" size="sm" onClick={handlePrint}>
                  <Printer className="w-4 h-4 mr-1" />
                  Print
                </Button>
              )}
              {analyses.length > 0 && (
                <Button variant="outline" size="sm" onClick={handleDeleteAllAnalyses} className="text-red-500 hover:text-red-600">
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
          ) : analyses.length === 0 ? (
            <div className="text-center py-8 text-muted-foreground">
              <Brain className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>Nicio analiză încă. Generează prima ta analiză AI!</p>
            </div>
          ) : (
            <div className="space-y-2">
              {analyses.slice(0, 10).map((analysis) => (
                <div
                  key={analysis.id}
                  className="flex items-center justify-between p-3 bg-secondary/50 rounded-lg hover:bg-secondary/70 cursor-pointer transition-colors"
                  onClick={() => setCurrentAnalysis(analysis)}
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-full ${gradeColors[analysis.technical_grade] || 'bg-gray-500'} flex items-center justify-center`}>
                      <span className="text-sm font-bold text-white">{analysis.technical_grade}</span>
                    </div>
                    <div>
                      <p className="font-medium truncate max-w-[300px]">{analysis.url}</p>
                      <div className="flex items-center gap-2">
                        <p className="text-xs text-muted-foreground">{formatDate(analysis.analyzed_at)}</p>
                        <Badge variant="outline" className="text-xs">{analysis.niche}</Badge>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <div className="font-bold">{analysis.technical_score}/100</div>
                      <div className="text-xs text-muted-foreground">{analysis.word_count} cuvinte</div>
                    </div>
                    <Button 
                      variant="ghost" 
                      size="sm" 
                      onClick={(e) => handleDeleteAnalysis(analysis.id, e)}
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
