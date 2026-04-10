import React, { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { useSite } from '../contexts/SiteContext';
import axios from 'axios';
import { toast } from 'sonner';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend
} from 'recharts';
import {
  Gauge,
  Smartphone,
  Monitor,
  RefreshCw,
  Loader2,
  Zap,
  Search,
  Eye,
  Shield,
  AlertTriangle,
  CheckCircle2,
  Wrench,
  TrendingUp,
  Globe
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL + '/api';

// Circular Gauge Component
const ScoreGauge = ({ score, label, size = 120 }) => {
  const getColor = (score) => {
    if (score >= 90) return '#22c55e'; // Green
    if (score >= 50) return '#eab308'; // Yellow
    return '#ef4444'; // Red
  };
  
  const radius = (size - 20) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = (score / 100) * circumference;
  const color = getColor(score);
  
  return (
    <div className="flex flex-col items-center">
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="transform -rotate-90">
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="currentColor"
            strokeWidth="8"
            className="text-secondary"
          />
          {/* Progress circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={color}
            strokeWidth="8"
            strokeDasharray={circumference}
            strokeDashoffset={circumference - progress}
            strokeLinecap="round"
            className="transition-all duration-500"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-bold" style={{ color }}>{score}</span>
        </div>
      </div>
      <span className="text-sm text-muted-foreground mt-2">{label}</span>
    </div>
  );
};

const PageSpeedPage = () => {
  const { getAuthHeaders } = useAuth();
  const { currentSite, sites } = useSite();
  
  const [loading, setLoading] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [optimizing, setOptimizing] = useState(false);
  const [latestAnalysis, setLatestAnalysis] = useState(null);
  const [history, setHistory] = useState([]);
  const [historyPeriod, setHistoryPeriod] = useState('30');
  const [activeTab, setActiveTab] = useState('mobile');
  const [allSitesData, setAllSitesData] = useState([]);
  
  const fetchLatestAnalysis = useCallback(async () => {
    if (!currentSite?.id) return;
    
    setLoading(true);
    try {
      const response = await axios.get(
        `${API}/pagespeed/latest/${currentSite.id}`,
        { headers: getAuthHeaders() }
      );
      setLatestAnalysis(response.data.latest);
    } catch (error) {
      console.error('Error fetching PageSpeed data:', error);
    } finally {
      setLoading(false);
    }
  }, [currentSite?.id, getAuthHeaders]);
  
  const fetchHistory = useCallback(async () => {
    if (!currentSite?.id) return;
    
    try {
      const response = await axios.get(
        `${API}/pagespeed/history/${currentSite.id}?days=${historyPeriod}`,
        { headers: getAuthHeaders() }
      );
      setHistory(response.data.history || []);
    } catch (error) {
      console.error('Error fetching PageSpeed history:', error);
    }
  }, [currentSite?.id, historyPeriod, getAuthHeaders]);
  
  const fetchAllSites = useCallback(async () => {
    try {
      const response = await axios.get(
        `${API}/pagespeed/all-sites`,
        { headers: getAuthHeaders() }
      );
      setAllSitesData(response.data.sites || []);
    } catch (error) {
      console.error('Error fetching all sites PageSpeed:', error);
    }
  }, [getAuthHeaders]);
  
  useEffect(() => {
    fetchLatestAnalysis();
    fetchHistory();
    fetchAllSites();
  }, [fetchLatestAnalysis, fetchHistory, fetchAllSites]);
  
  const handleAnalyze = async () => {
    if (!currentSite?.id) {
      toast.error('Selectează un site mai întâi');
      return;
    }
    
    setAnalyzing(true);
    try {
      const response = await axios.get(
        `${API}/pagespeed/analyze/${currentSite.id}`,
        { headers: getAuthHeaders() }
      );
      setLatestAnalysis(response.data);
      toast.success('Analiză PageSpeed completă!');
      fetchHistory();
      fetchAllSites();
    } catch (error) {
      const detail = error.response?.data?.detail;
      if (error.response?.status === 429) {
        toast.error('Quota API depășită. Încearcă mai târziu.');
      } else {
        toast.error(detail || 'Eroare la analiza PageSpeed');
      }
    } finally {
      setAnalyzing(false);
    }
  };
  
  const handleOptimize = async (fixType = 'all') => {
    if (!currentSite?.id) {
      toast.error('Selectează un site mai întâi');
      return;
    }
    
    setOptimizing(true);
    try {
      const response = await axios.post(
        `${API}/pagespeed/optimize/${currentSite.id}?fix_type=${fixType}`,
        {},
        { headers: getAuthHeaders() }
      );
      const { successful, total, results } = response.data;
      
      if (successful > 0) {
        toast.success(`${successful}/${total} plugin-uri instalate cu succes!`);
      } else {
        toast.warning('Nu s-au putut instala plugin-urile. Verifică credențialele WordPress.');
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Eroare la optimizare');
    } finally {
      setOptimizing(false);
    }
  };
  
  // Generate chart data with ALL days in period
  const chartData = (() => {
    const days = parseInt(historyPeriod);
    const data = [];
    const now = new Date();
    
    for (let i = days - 1; i >= 0; i--) {
      const date = new Date(now);
      date.setDate(date.getDate() - i);
      date.setHours(0, 0, 0, 0);
      
      const dateStr = date.toLocaleDateString('ro-RO', { day: '2-digit', month: 'short' });
      
      // Find analysis for this day
      const dayAnalyses = history.filter(h => {
        const hDate = new Date(h.analyzed_at);
        return hDate.toDateString() === date.toDateString();
      });
      
      const latestDayAnalysis = dayAnalyses.length > 0 
        ? dayAnalyses[dayAnalyses.length - 1] 
        : null;
      
      data.push({
        date: dateStr,
        performance_mobile: latestDayAnalysis?.mobile?.scores?.performance || null,
        performance_desktop: latestDayAnalysis?.desktop?.scores?.performance || null,
        seo_mobile: latestDayAnalysis?.mobile?.scores?.seo || null,
        seo_desktop: latestDayAnalysis?.desktop?.scores?.seo || null
      });
    }
    
    return data;
  })();
  
  const currentData = latestAnalysis?.[activeTab];
  const scores = currentData?.scores || {};
  const recommendations = currentData?.recommendations || [];
  
  const getScoreColor = (score) => {
    if (score >= 90) return 'text-green-500';
    if (score >= 50) return 'text-yellow-500';
    return 'text-red-500';
  };
  
  const getScoreBgColor = (score) => {
    if (score >= 90) return 'bg-green-500/10 border-green-500/20';
    if (score >= 50) return 'bg-yellow-500/10 border-yellow-500/20';
    return 'bg-red-500/10 border-red-500/20';
  };

  return (
    <div className="space-y-6" data-testid="pagespeed-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Gauge className="w-7 h-7 text-primary" />
            PageSpeed Insights
          </h1>
          <p className="text-muted-foreground">
            Analizează și optimizează performanța site-urilor tale
          </p>
        </div>
        <Button
          onClick={handleAnalyze}
          disabled={analyzing || !currentSite}
          className="bg-primary hover:bg-primary/90"
          data-testid="analyze-btn"
        >
          {analyzing ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Se analizează...
            </>
          ) : (
            <>
              <RefreshCw className="w-4 h-4 mr-2" />
              Analizează Acum
            </>
          )}
        </Button>
      </div>
      
      {!currentSite ? (
        <Card className="bg-card border-border">
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Globe className="w-16 h-16 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">Selectează un site</h3>
            <p className="text-muted-foreground text-center">
              Alege un site din meniul din stânga pentru a vedea analiza PageSpeed
            </p>
          </CardContent>
        </Card>
      ) : (
        <>
          {/* Mobile/Desktop Tabs */}
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="bg-secondary">
              <TabsTrigger value="mobile" className="data-[state=active]:bg-primary">
                <Smartphone className="w-4 h-4 mr-2" />
                Mobile
              </TabsTrigger>
              <TabsTrigger value="desktop" className="data-[state=active]:bg-primary">
                <Monitor className="w-4 h-4 mr-2" />
                Desktop
              </TabsTrigger>
            </TabsList>
            
            <TabsContent value={activeTab} className="space-y-6 mt-6">
              {/* Scores */}
              {latestAnalysis ? (
                <>
                  <Card className="bg-card border-border">
                    <CardHeader>
                      <CardTitle className="text-lg">Scoruri {activeTab === 'mobile' ? 'Mobile' : 'Desktop'}</CardTitle>
                      <CardDescription>
                        Ultima analiză: {new Date(latestAnalysis.analyzed_at).toLocaleString('ro-RO')}
                      </CardDescription>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-6 justify-items-center">
                        <ScoreGauge score={scores.performance || 0} label="Performance" />
                        <ScoreGauge score={scores.seo || 0} label="SEO" />
                        <ScoreGauge score={scores.accessibility || 0} label="Accessibility" />
                        <ScoreGauge score={scores.best_practices || 0} label="Best Practices" />
                      </div>
                    </CardContent>
                  </Card>
                  
                  {/* Recommendations */}
                  <Card className="bg-card border-border">
                    <CardHeader>
                      <div className="flex items-center justify-between">
                        <div>
                          <CardTitle className="text-lg flex items-center gap-2">
                            <AlertTriangle className="w-5 h-5 text-yellow-500" />
                            Recomandări de Optimizare
                          </CardTitle>
                          <CardDescription>
                            {recommendations.filter(r => r.auto_fixable).length} probleme pot fi rezolvate automat
                          </CardDescription>
                        </div>
                        <Button
                          onClick={() => handleOptimize('all')}
                          disabled={optimizing}
                          className="bg-green-600 hover:bg-green-700"
                          data-testid="optimize-all-btn"
                        >
                          {optimizing ? (
                            <>
                              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                              Se optimizează...
                            </>
                          ) : (
                            <>
                              <Zap className="w-4 h-4 mr-2" />
                              Optimizează Tot
                            </>
                          )}
                        </Button>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {recommendations.length === 0 ? (
                          <div className="text-center py-8 text-muted-foreground">
                            <CheckCircle2 className="w-12 h-12 mx-auto mb-3 text-green-500" />
                            <p>Felicitări! Nu există probleme majore de performanță.</p>
                          </div>
                        ) : (
                          recommendations.map((rec, idx) => (
                            <div
                              key={rec.id || idx}
                              className={`p-4 rounded-lg border ${getScoreBgColor(rec.score)}`}
                            >
                              <div className="flex items-start justify-between gap-4">
                                <div className="flex-1">
                                  <div className="flex items-center gap-2 mb-1">
                                    <span className={`font-medium ${getScoreColor(rec.score)}`}>
                                      {rec.score}%
                                    </span>
                                    <h4 className="font-medium">{rec.title}</h4>
                                    {rec.auto_fixable && (
                                      <Badge className="bg-blue-500/20 text-blue-400 border-blue-500/30">
                                        <Wrench className="w-3 h-3 mr-1" />
                                        Auto-fix
                                      </Badge>
                                    )}
                                  </div>
                                  {rec.display_value && (
                                    <p className="text-sm text-muted-foreground">{rec.display_value}</p>
                                  )}
                                  {rec.plugin && (
                                    <p className="text-xs text-muted-foreground mt-1">
                                      Plugin recomandat: <span className="text-primary">{rec.plugin}</span>
                                    </p>
                                  )}
                                </div>
                                {rec.auto_fixable && (
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => handleOptimize(rec.fix_type)}
                                    disabled={optimizing}
                                    className="shrink-0"
                                  >
                                    <Wrench className="w-3 h-3 mr-1" />
                                    Fix
                                  </Button>
                                )}
                              </div>
                            </div>
                          ))
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </>
              ) : (
                <Card className="bg-card border-border">
                  <CardContent className="flex flex-col items-center justify-center py-16">
                    <Gauge className="w-16 h-16 text-muted-foreground mb-4" />
                    <h3 className="text-lg font-semibold mb-2">Nicio analiză disponibilă</h3>
                    <p className="text-muted-foreground text-center mb-4">
                      Apasă butonul "Analizează Acum" pentru a verifica performanța site-ului
                    </p>
                    <Button onClick={handleAnalyze} disabled={analyzing}>
                      {analyzing ? 'Se analizează...' : 'Analizează'}
                    </Button>
                  </CardContent>
                </Card>
              )}
            </TabsContent>
          </Tabs>
          
          {/* History Chart */}
          <Card className="bg-card border-border">
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <TrendingUp className="w-5 h-5 text-primary" />
                    Evoluție Scoruri
                  </CardTitle>
                  <CardDescription>
                    Istoricul performanței în timp
                  </CardDescription>
                </div>
                <Select value={historyPeriod} onValueChange={setHistoryPeriod}>
                  <SelectTrigger className="w-[130px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="7">7 zile</SelectItem>
                    <SelectItem value="30">30 zile</SelectItem>
                    <SelectItem value="90">90 zile</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardHeader>
            <CardContent>
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                    <XAxis 
                      dataKey="date" 
                      stroke="#666"
                      tick={{ fill: '#999', fontSize: 11 }}
                      interval={Math.floor(chartData.length / 7)}
                    />
                    <YAxis 
                      domain={[0, 100]}
                      stroke="#666"
                      tick={{ fill: '#999', fontSize: 11 }}
                    />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: '#1a1a1a', 
                        border: '1px solid #333',
                        borderRadius: '8px'
                      }}
                    />
                    <Legend />
                    <Line 
                      type="monotone"
                      dataKey="performance_mobile"
                      name="Performance (Mobile)"
                      stroke="#22c55e"
                      strokeWidth={2}
                      dot={false}
                      connectNulls={true}
                    />
                    <Line 
                      type="monotone"
                      dataKey="performance_desktop"
                      name="Performance (Desktop)"
                      stroke="#3b82f6"
                      strokeWidth={2}
                      dot={false}
                      connectNulls={true}
                    />
                    <Line 
                      type="monotone"
                      dataKey="seo_mobile"
                      name="SEO (Mobile)"
                      stroke="#eab308"
                      strokeWidth={2}
                      dot={false}
                      connectNulls={true}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </>
      )}
      
      {/* All Sites Overview */}
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Globe className="w-5 h-5 text-primary" />
            Overview Toate Site-urile
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {allSitesData.map((site) => {
              const analysis = site.latest_analysis;
              const mobilePerf = analysis?.mobile?.scores?.performance;
              const desktopPerf = analysis?.desktop?.scores?.performance;
              
              return (
                <div
                  key={site.site_id}
                  className="p-4 rounded-lg bg-secondary/50 border border-border"
                >
                  <h4 className="font-medium mb-2 truncate">{site.site_name}</h4>
                  {analysis ? (
                    <div className="flex items-center gap-4">
                      <div className="flex items-center gap-1">
                        <Smartphone className="w-4 h-4 text-muted-foreground" />
                        <span className={`font-bold ${getScoreColor(mobilePerf || 0)}`}>
                          {mobilePerf || '-'}
                        </span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Monitor className="w-4 h-4 text-muted-foreground" />
                        <span className={`font-bold ${getScoreColor(desktopPerf || 0)}`}>
                          {desktopPerf || '-'}
                        </span>
                      </div>
                      <span className="text-xs text-muted-foreground ml-auto">
                        {new Date(analysis.analyzed_at).toLocaleDateString('ro-RO')}
                      </span>
                    </div>
                  ) : (
                    <p className="text-sm text-muted-foreground">Nicio analiză</p>
                  )}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default PageSpeedPage;
