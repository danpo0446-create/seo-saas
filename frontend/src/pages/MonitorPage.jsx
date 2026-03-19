import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import {
  Activity,
  RefreshCw,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  Pause,
  Globe,
  TrendingUp,
  Calendar,
  FileText,
  ExternalLink,
  Loader2,
  Zap,
  BarChart3
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const statusConfig = {
  healthy: { color: 'bg-green-500', icon: CheckCircle2, label: 'Sănătos', textColor: 'text-green-500' },
  warning: { color: 'bg-yellow-500', icon: AlertTriangle, label: 'Atenție', textColor: 'text-yellow-500' },
  pending: { color: 'bg-blue-500', icon: Clock, label: 'În așteptare', textColor: 'text-blue-500' },
  paused: { color: 'bg-orange-500', icon: Pause, label: 'Pauză', textColor: 'text-orange-500' },
  manual: { color: 'bg-gray-500', icon: Globe, label: 'Manual', textColor: 'text-gray-500' },
  inactive: { color: 'bg-gray-700', icon: XCircle, label: 'Inactiv', textColor: 'text-gray-500' }
};

const frequencyLabels = {
  daily: 'Zilnic',
  every_2_days: 'La 2 zile',
  every_3_days: 'La 3 zile',
  weekly: 'Săptămânal'
};

export default function MonitorPage() {
  const [monitorData, setMonitorData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [lastRefresh, setLastRefresh] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  const fetchMonitorData = useCallback(async (showToast = false) => {
    try {
      setRefreshing(true);
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/automation/monitor`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMonitorData(response.data);
      setLastRefresh(new Date());
      if (showToast) {
        toast.success('Date actualizate');
      }
    } catch (error) {
      toast.error('Eroare la încărcarea datelor de monitorizare');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    fetchMonitorData();
  }, [fetchMonitorData]);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    if (!autoRefresh) return;
    const interval = setInterval(() => {
      fetchMonitorData();
    }, 30000);
    return () => clearInterval(interval);
  }, [autoRefresh, fetchMonitorData]);

  const formatDateTime = (isoString) => {
    if (!isoString) return '-';
    const date = new Date(isoString);
    return date.toLocaleString('ro-RO', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatTime = (isoString) => {
    if (!isoString) return '-';
    const date = new Date(isoString);
    return date.toLocaleTimeString('ro-RO', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getTimeUntil = (isoString) => {
    if (!isoString) return null;
    const target = new Date(isoString);
    const now = new Date();
    const diff = target - now;
    
    if (diff < 0) return 'Acum';
    
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    
    if (hours > 24) {
      const days = Math.floor(hours / 24);
      return `${days}z ${hours % 24}h`;
    }
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="monitor-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-heading font-bold flex items-center gap-3">
            <Activity className="w-8 h-8 text-primary" />
            Monitorizare Timp Real
          </h1>
          <p className="text-muted-foreground mt-1">
            Status automatizare și istoric ultimele 7 zile
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-xs text-muted-foreground">
            {lastRefresh && (
              <span>Actualizat: {formatTime(lastRefresh.toISOString())}</span>
            )}
          </div>
          <Button
            variant={autoRefresh ? "default" : "outline"}
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
            data-testid="auto-refresh-toggle"
          >
            <Zap className={`w-4 h-4 mr-1 ${autoRefresh ? 'text-yellow-300' : ''}`} />
            {autoRefresh ? 'Auto ON' : 'Auto OFF'}
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => fetchMonitorData(true)}
            disabled={refreshing}
            data-testid="refresh-btn"
          >
            <RefreshCw className={`w-4 h-4 mr-1 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      {monitorData?.summary && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <Card className="bg-card border-border">
            <CardContent className="pt-4 pb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-primary/20 flex items-center justify-center">
                  <Globe className="w-5 h-5 text-primary" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{monitorData.summary.total_sites}</p>
                  <p className="text-xs text-muted-foreground">Site-uri Total</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-card border-border">
            <CardContent className="pt-4 pb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-green-500/20 flex items-center justify-center">
                  <CheckCircle2 className="w-5 h-5 text-green-500" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{monitorData.summary.active_sites}</p>
                  <p className="text-xs text-muted-foreground">Active</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-card border-border">
            <CardContent className="pt-4 pb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-orange-500/20 flex items-center justify-center">
                  <Pause className="w-5 h-5 text-orange-500" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{monitorData.summary.paused_sites}</p>
                  <p className="text-xs text-muted-foreground">În Pauză</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-card border-border">
            <CardContent className="pt-4 pb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-blue-500/20 flex items-center justify-center">
                  <FileText className="w-5 h-5 text-blue-500" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{monitorData.summary.total_articles_7days}</p>
                  <p className="text-xs text-muted-foreground">Articole 7 zile</p>
                </div>
              </div>
            </CardContent>
          </Card>
          
          <Card className="bg-card border-border">
            <CardContent className="pt-4 pb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-purple-500/20 flex items-center justify-center">
                  <TrendingUp className="w-5 h-5 text-purple-500" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{monitorData.summary.total_published_7days}</p>
                  <p className="text-xs text-muted-foreground">Publicate</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Sites Monitor Table */}
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-primary" />
            Status Site-uri
          </CardTitle>
          <CardDescription>
            Monitorizare în timp real pentru fiecare site cu istoric 7 zile
          </CardDescription>
        </CardHeader>
        <CardContent>
          {!monitorData?.sites?.length ? (
            <div className="text-center py-12">
              <Globe className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground">Niciun site conectat</p>
            </div>
          ) : (
            <div className="space-y-4">
              {monitorData.sites.map((site) => {
                const StatusIcon = statusConfig[site.status]?.icon || Globe;
                const statusColor = statusConfig[site.status]?.color || 'bg-gray-500';
                const statusLabel = statusConfig[site.status]?.label || site.status;
                const textColor = statusConfig[site.status]?.textColor || 'text-gray-500';
                
                return (
                  <div 
                    key={site.site_id} 
                    className="border border-border rounded-lg p-4 hover:border-primary/50 transition-colors"
                    data-testid={`monitor-site-${site.site_id}`}
                  >
                    {/* Site Header */}
                    <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-4">
                      <div className="flex items-center gap-3">
                        <div className={`w-3 h-3 rounded-full ${statusColor}`} />
                        <div>
                          <h3 className="font-semibold">{site.site_name}</h3>
                          <p className="text-xs text-muted-foreground">{site.niche}</p>
                        </div>
                        <Badge variant="outline" className={textColor}>
                          <StatusIcon className="w-3 h-3 mr-1" />
                          {statusLabel}
                        </Badge>
                      </div>
                      
                      <div className="flex flex-wrap items-center gap-4 text-sm">
                        {/* Automation Info */}
                        {site.automation.mode === 'automatic' && site.automation.enabled && (
                          <>
                            <div className="flex items-center gap-1 text-muted-foreground">
                              <Clock className="w-4 h-4" />
                              <span>{site.automation.generation_hour}:00</span>
                              <span className="text-xs">({frequencyLabels[site.automation.frequency]})</span>
                            </div>
                            
                            {site.automation.next_scheduled && (
                              <TooltipProvider>
                                <Tooltip>
                                  <TooltipTrigger>
                                    <Badge className="bg-primary/20 text-primary border-primary/30">
                                      <Calendar className="w-3 h-3 mr-1" />
                                      Următorul: {getTimeUntil(site.automation.next_scheduled)}
                                    </Badge>
                                  </TooltipTrigger>
                                  <TooltipContent>
                                    {formatDateTime(site.automation.next_scheduled)}
                                  </TooltipContent>
                                </Tooltip>
                              </TooltipProvider>
                            )}
                          </>
                        )}
                        
                        {/* Stats */}
                        <div className="flex items-center gap-2">
                          <span className="text-muted-foreground text-xs">7 zile:</span>
                          <Badge variant="secondary">
                            {site.stats_7days.published}/{site.stats_7days.total}
                          </Badge>
                          {site.stats_7days.total > 0 && (
                            <span className={`text-xs ${site.stats_7days.success_rate >= 80 ? 'text-green-500' : site.stats_7days.success_rate >= 50 ? 'text-yellow-500' : 'text-red-500'}`}>
                              ({site.stats_7days.success_rate}%)
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    {/* 7-Day History Chart */}
                    <div className="mb-4">
                      <p className="text-xs text-muted-foreground mb-2">Istoric 7 zile:</p>
                      <div className="flex gap-1">
                        {site.daily_history.map((day, idx) => (
                          <TooltipProvider key={day.date}>
                            <Tooltip>
                              <TooltipTrigger className="flex-1">
                                <div className="flex flex-col items-center gap-1">
                                  <div 
                                    className={`w-full h-8 rounded flex items-center justify-center text-xs font-medium ${
                                      day.count === 0 
                                        ? 'bg-secondary/50' 
                                        : day.published === day.count 
                                          ? 'bg-green-500/80 text-white' 
                                          : day.published > 0 
                                            ? 'bg-yellow-500/80 text-white'
                                            : 'bg-red-500/80 text-white'
                                    }`}
                                  >
                                    {day.count > 0 ? day.count : '-'}
                                  </div>
                                  <span className="text-[10px] text-muted-foreground">
                                    {day.label.split(' ')[0]}
                                  </span>
                                </div>
                              </TooltipTrigger>
                              <TooltipContent>
                                <div className="text-xs">
                                  <p className="font-semibold">{day.label}</p>
                                  <p>Total: {day.count}</p>
                                  <p>Publicate: {day.published}</p>
                                  {day.failed > 0 && <p className="text-red-400">Eșuate: {day.failed}</p>}
                                </div>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        ))}
                      </div>
                    </div>
                    
                    {/* Recent Articles */}
                    {site.recent_articles?.length > 0 && (
                      <div>
                        <p className="text-xs text-muted-foreground mb-2">Articole recente:</p>
                        <div className="space-y-1">
                          {site.recent_articles.slice(0, 3).map((article) => (
                            <div 
                              key={article.id}
                              className="flex items-center justify-between text-xs bg-secondary/30 rounded px-2 py-1"
                            >
                              <div className="flex items-center gap-2 truncate flex-1">
                                {article.status === 'published' ? (
                                  <CheckCircle2 className="w-3 h-3 text-green-500 flex-shrink-0" />
                                ) : (
                                  <FileText className="w-3 h-3 text-muted-foreground flex-shrink-0" />
                                )}
                                <span className="truncate">{article.title}</span>
                              </div>
                              <div className="flex items-center gap-2 flex-shrink-0 ml-2">
                                <span className="text-muted-foreground">
                                  {formatDateTime(article.created_at)}
                                </span>
                                {article.wp_post_url && (
                                  <a 
                                    href={article.wp_post_url} 
                                    target="_blank" 
                                    rel="noopener noreferrer"
                                    className="text-primary hover:text-primary/80"
                                  >
                                    <ExternalLink className="w-3 h-3" />
                                  </a>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                    
                    {/* Last Generation Info */}
                    {site.automation.last_generation && (
                      <div className="mt-3 pt-3 border-t border-border/50 text-xs text-muted-foreground">
                        Ultima generare: {formatDateTime(site.automation.last_generation)} • 
                        Total articole: {site.automation.articles_generated}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Current Time Display */}
      {monitorData?.current_time && (
        <div className="text-center text-xs text-muted-foreground">
          <Clock className="w-3 h-3 inline mr-1" />
          Ora server: {formatDateTime(monitorData.current_time)} ({monitorData.timezone})
        </div>
      )}
    </div>
  );
}
