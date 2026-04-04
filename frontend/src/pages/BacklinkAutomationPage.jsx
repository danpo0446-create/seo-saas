import { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import {
  Clock,
  Mail,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Globe,
  Send,
  Calendar,
  Target,
  Loader2,
  BarChart3,
  ArrowUpRight,
  ArrowDownRight,
  Percent,
  MessageSquare,
  Zap,
  Building2
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function BacklinkAutomationPage() {
  const [sites, setSites] = useState([]);
  const [selectedSiteId, setSelectedSiteId] = useState('all');
  const [status, setStatus] = useState(null);
  const [detailedStats, setDetailedStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);
  const { getAuthHeaders } = useAuth();

  // Fetch sites list
  const fetchSites = async () => {
    try {
      const response = await axios.get(`${API}/wordpress/sites`, { headers: getAuthHeaders() });
      setSites(response.data || []);
    } catch (error) {
      console.error('Failed to fetch sites:', error);
    }
  };

  const fetchStatus = async () => {
    setLoading(true);
    try {
      const siteParam = selectedSiteId !== 'all' ? `?site_id=${selectedSiteId}` : '';
      const [statusRes, statsRes] = await Promise.all([
        axios.get(`${API}/backlinks/automation-status${siteParam}`, { headers: getAuthHeaders() }),
        axios.get(`${API}/backlinks/outreach/detailed-stats${siteParam}`, { headers: getAuthHeaders() })
      ]);
      setStatus(statusRes.data);
      setDetailedStats(statsRes.data);
    } catch (error) {
      toast.error('Eroare la încărcarea statusului');
    } finally {
      setLoading(false);
    }
  };

  const triggerAutomation = async () => {
    setTriggering(true);
    try {
      const siteParam = selectedSiteId !== 'all' ? `?site_id=${selectedSiteId}` : '';
      const response = await axios.post(`${API}/backlinks/trigger-outreach${siteParam}`, {}, { headers: getAuthHeaders() });
      toast.success(response.data.message || 'Automatizare declanșată!');
      fetchStatus();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Eroare la declanșare');
    } finally {
      setTriggering(false);
    }
  };

  useEffect(() => {
    fetchSites();
  }, []);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [selectedSiteId]);

  const selectedSite = sites.find(s => s.id === selectedSiteId);

  if (loading && !status) {
    return (
      <div className="flex items-center justify-center min-h-[400px]" data-testid="loading-spinner">
        <Loader2 className="w-8 h-8 animate-spin text-[#00E676]" />
      </div>
    );
  }

  const overview = detailedStats?.overview || {};
  const weeklyComparison = detailedStats?.weekly_comparison || {};

  return (
    <div className="space-y-6" data-testid="backlink-automation-page">
      {/* Header with Site Selector */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Automatizare Backlinks</h1>
          <p className="text-[#71717A]">Dashboard statistici și monitorizare outreach</p>
        </div>
        
        <div className="flex flex-col sm:flex-row gap-2">
          {/* Site Selector */}
          <Select value={selectedSiteId} onValueChange={setSelectedSiteId}>
            <SelectTrigger className="w-[220px] bg-[#171717] border-[#262626] text-white" data-testid="site-selector">
              <Building2 className="w-4 h-4 mr-2 text-[#71717A]" />
              <SelectValue placeholder="Selectează site" />
            </SelectTrigger>
            <SelectContent className="bg-[#171717] border-[#262626]">
              <SelectItem value="all" className="text-white hover:bg-[#262626]">
                Toate site-urile
              </SelectItem>
              {sites.map((site) => (
                <SelectItem key={site.id} value={site.id} className="text-white hover:bg-[#262626]">
                  {site.site_name || site.site_url}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Button 
            onClick={triggerAutomation}
            className="bg-[#00E676] text-black hover:bg-[#00E676]/90"
            disabled={triggering}
            data-testid="trigger-automation-btn"
          >
            {triggering ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Zap className="w-4 h-4 mr-2" />
            )}
            {selectedSiteId !== 'all' ? 'Declanșează pentru Site' : 'Declanșează Toate'}
          </Button>
          <Button 
            onClick={fetchStatus} 
            variant="outline" 
            className="border-[#262626] hover:bg-[#171717]"
            disabled={loading}
            data-testid="refresh-btn"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
      </div>

      {/* Current Site Info Badge */}
      {selectedSiteId !== 'all' && selectedSite && (
        <div className="flex items-center gap-2">
          <Badge className="bg-[#00E676]/10 text-[#00E676] border-[#00E676]/30 px-3 py-1">
            <Globe className="w-3 h-3 mr-1" />
            {selectedSite.site_name || selectedSite.site_url}
          </Badge>
          {selectedSite.niche && (
            <Badge variant="outline" className="border-[#262626] text-[#71717A]">
              {selectedSite.niche}
            </Badge>
          )}
        </div>
      )}

      {/* Main Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <Card className="bg-gradient-to-br from-[#00E676]/20 to-[#0A0A0A] border-[#00E676]/30">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[#71717A]">Total Trimise</p>
                <p className="text-3xl font-bold text-white">{overview.total_sent || 0}</p>
              </div>
              <div className="p-3 bg-[#00E676]/20 rounded-full">
                <Send className="w-6 h-6 text-[#00E676]" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-500/20 to-[#0A0A0A] border-blue-500/30">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[#71717A]">Răspunsuri</p>
                <p className="text-3xl font-bold text-white">{overview.total_responded || 0}</p>
              </div>
              <div className="p-3 bg-blue-500/20 rounded-full">
                <MessageSquare className="w-6 h-6 text-blue-500" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-500/20 to-[#0A0A0A] border-purple-500/30">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[#71717A]">Rată Răspuns</p>
                <p className="text-3xl font-bold text-white">{overview.response_rate || 0}%</p>
              </div>
              <div className="p-3 bg-purple-500/20 rounded-full">
                <Percent className="w-6 h-6 text-purple-500" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-yellow-500/20 to-[#0A0A0A] border-yellow-500/30">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[#71717A]">Conversii</p>
                <p className="text-3xl font-bold text-white">{overview.conversions || 0}</p>
              </div>
              <div className="p-3 bg-yellow-500/20 rounded-full">
                <Target className="w-6 h-6 text-yellow-500" />
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-pink-500/20 to-[#0A0A0A] border-pink-500/30">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-[#71717A]">Rată Conversie</p>
                <p className="text-3xl font-bold text-white">{overview.conversion_rate || 0}%</p>
              </div>
              <div className="p-3 bg-pink-500/20 rounded-full">
                <TrendingUp className="w-6 h-6 text-pink-500" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Weekly Comparison & Schedule */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="bg-[#0A0A0A] border-[#262626]">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-[#71717A]">Comparație Săptămânală</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-2xl font-bold text-white">{weeklyComparison.this_week || 0}</p>
                <p className="text-xs text-[#71717A]">emailuri săptămâna asta</p>
              </div>
              <div className="text-right">
                <div className={`flex items-center gap-1 ${weeklyComparison.change_percent >= 0 ? 'text-[#00E676]' : 'text-red-500'}`}>
                  {weeklyComparison.change_percent >= 0 ? (
                    <ArrowUpRight className="w-4 h-4" />
                  ) : (
                    <ArrowDownRight className="w-4 h-4" />
                  )}
                  <span className="font-bold">{Math.abs(weeklyComparison.change_percent || 0)}%</span>
                </div>
                <p className="text-xs text-[#71717A]">vs săpt. trecută ({weeklyComparison.last_week || 0})</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#0A0A0A] border-[#262626]">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-[#71717A]">Următoarea Rulare Automată</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center gap-3">
              <div className="p-2 bg-[#00E676]/10 rounded-lg">
                <Clock className="w-5 h-5 text-[#00E676]" />
              </div>
              <div>
                <p className="text-2xl font-bold text-white">12:30</p>
                <p className="text-xs text-[#71717A]">Ora României (zilnic)</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#0A0A0A] border-[#262626]">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm text-[#71717A]">
              Emailuri Azi {selectedSiteId !== 'all' && selectedSite ? `- ${selectedSite.site_name || 'Site'}` : ''}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-[#71717A]">Trimise</span>
                <span className="text-white font-bold">
                  {status?.total_emails_today || 0} / {selectedSiteId !== 'all' ? 15 : (status?.sites?.length || 0) * 15}
                </span>
              </div>
              <Progress 
                value={((status?.total_emails_today || 0) / (selectedSiteId !== 'all' ? 15 : ((status?.sites?.length || 1) * 15))) * 100} 
                className="h-2 bg-[#262626]"
              />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Drafts & Pending Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="bg-[#0A0A0A] border-[#262626]">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-[#00E676]" />
              Status Emailuri {selectedSiteId !== 'all' && '(Site selectat)'}
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                  <span className="text-[#71717A]">Draft</span>
                </div>
                <span className="text-white font-bold">{overview.total_drafts || 0}</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                  <span className="text-[#71717A]">În așteptare</span>
                </div>
                <span className="text-white font-bold">{overview.total_pending || 0}</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-[#00E676]"></div>
                  <span className="text-[#71717A]">Trimise</span>
                </div>
                <span className="text-white font-bold">{overview.total_sent || 0}</span>
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-purple-500"></div>
                  <span className="text-[#71717A]">Cu răspuns</span>
                </div>
                <span className="text-white font-bold">{overview.total_responded || 0}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#0A0A0A] border-[#262626]">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Globe className="w-5 h-5 text-[#00E676]" />
              Top Domenii Responsive
            </CardTitle>
          </CardHeader>
          <CardContent>
            {detailedStats?.top_domains?.length > 0 ? (
              <div className="space-y-3">
                {detailedStats.top_domains.map((domain, index) => (
                  <div key={domain.domain} className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-[#71717A] text-sm w-4">{index + 1}.</span>
                      <span className="text-white truncate max-w-[200px]">{domain.domain}</span>
                    </div>
                    <Badge className="bg-[#00E676]/10 text-[#00E676] border-[#00E676]/30">
                      {domain.responses} răspunsuri
                    </Badge>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-6 text-[#71717A]">
                <MessageSquare className="w-8 h-8 mx-auto mb-2 opacity-50" />
                <p>Niciun răspuns încă</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Sites Status - Only show when viewing all sites */}
      {selectedSiteId === 'all' && (
        <Card className="bg-[#0A0A0A] border-[#262626]">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Globe className="w-5 h-5 text-[#00E676]" />
              Status per Site
            </CardTitle>
            <CardDescription>Click pe un site pentru a vedea detaliile</CardDescription>
          </CardHeader>
          <CardContent>
            {status?.sites?.length > 0 ? (
              <div className="space-y-4">
                {status.sites.map((site) => (
                  <div 
                    key={site.site_id} 
                    className="p-4 bg-[#171717] rounded-lg border border-[#262626] hover:border-[#00E676]/50 cursor-pointer transition-colors"
                    onClick={() => setSelectedSiteId(site.site_id)}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <h3 className="font-medium text-white">{site.site_name}</h3>
                        <p className="text-xs text-[#71717A]">{site.niche || 'Nișă nedefinită'}</p>
                      </div>
                      <Badge className={site.niche ? 'bg-[#00E676]/10 text-[#00E676]' : 'bg-red-500/10 text-red-500'}>
                        {site.niche ? 'Activ' : 'Lipsește nișa'}
                      </Badge>
                    </div>
                    
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <p className="text-[#71717A]">Azi</p>
                        <p className="text-white font-bold">{site.emails_sent_today} / 15</p>
                      </div>
                      <div>
                        <p className="text-[#71717A]">7 zile</p>
                        <p className="text-white font-bold">{site.emails_sent_7_days}</p>
                      </div>
                      <div>
                        <p className="text-[#71717A]">Oportunități FREE</p>
                        <p className="text-white font-bold">{site.total_free_opportunities}</p>
                      </div>
                      <div>
                        <p className="text-[#71717A]">Răspunsuri</p>
                        <p className="text-white font-bold">{site.responses_received}</p>
                      </div>
                    </div>
                    
                    <div className="mt-3">
                      <Progress 
                        value={(site.emails_sent_today / 15) * 100} 
                        className="h-1.5 bg-[#262626]"
                      />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-[#71717A]">
                <Globe className="w-12 h-12 mx-auto mb-3 opacity-50" />
                <p>Niciun site configurat</p>
                <p className="text-sm mt-1">Adaugă un site WordPress pentru a începe automatizarea</p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Single Site Details - Only show when a specific site is selected */}
      {selectedSiteId !== 'all' && status?.sites?.[0] && (
        <Card className="bg-[#0A0A0A] border-[#262626]">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Globe className="w-5 h-5 text-[#00E676]" />
                Detalii Site
              </CardTitle>
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={() => setSelectedSiteId('all')}
                className="text-[#71717A] hover:text-white"
              >
                ← Toate site-urile
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div className="text-center p-4 bg-[#171717] rounded-lg">
                <Mail className="w-8 h-8 mx-auto mb-2 text-[#00E676]" />
                <p className="text-2xl font-bold text-white">{status.sites[0].emails_sent_today}</p>
                <p className="text-sm text-[#71717A]">Emailuri azi</p>
              </div>
              <div className="text-center p-4 bg-[#171717] rounded-lg">
                <Calendar className="w-8 h-8 mx-auto mb-2 text-blue-500" />
                <p className="text-2xl font-bold text-white">{status.sites[0].emails_sent_7_days}</p>
                <p className="text-sm text-[#71717A]">Ultimele 7 zile</p>
              </div>
              <div className="text-center p-4 bg-[#171717] rounded-lg">
                <Target className="w-8 h-8 mx-auto mb-2 text-purple-500" />
                <p className="text-2xl font-bold text-white">{status.sites[0].total_free_opportunities}</p>
                <p className="text-sm text-[#71717A]">Oportunități FREE</p>
              </div>
              <div className="text-center p-4 bg-[#171717] rounded-lg">
                <MessageSquare className="w-8 h-8 mx-auto mb-2 text-yellow-500" />
                <p className="text-2xl font-bold text-white">{status.sites[0].responses_received}</p>
                <p className="text-sm text-[#71717A]">Răspunsuri</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Activity Chart - Last 7 Days */}
      <Card className="bg-[#0A0A0A] border-[#262626]">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5 text-[#00E676]" />
            Activitate Ultimele 7 Zile {selectedSiteId !== 'all' && '(Site selectat)'}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-end justify-between gap-2 h-32">
            {detailedStats?.daily_stats?.slice(-7).map((day, index) => {
              const maxSent = Math.max(...(detailedStats?.daily_stats?.slice(-7).map(d => d.sent) || [1]), 1);
              const height = (day.sent / maxSent) * 100;
              return (
                <div key={day.date} className="flex-1 flex flex-col items-center gap-1">
                  <div className="w-full flex flex-col items-center">
                    <span className="text-xs text-[#00E676] mb-1">{day.sent}</span>
                    <div 
                      className="w-full bg-[#00E676]/80 rounded-t"
                      style={{ height: `${Math.max(height, 4)}px` }}
                    ></div>
                    {day.responded > 0 && (
                      <div 
                        className="w-full bg-purple-500/80 rounded-b"
                        style={{ height: `${(day.responded / maxSent) * 100}px` }}
                      ></div>
                    )}
                  </div>
                  <span className="text-xs text-[#71717A]">
                    {new Date(day.date).toLocaleDateString('ro-RO', { weekday: 'short' })}
                  </span>
                </div>
              );
            })}
          </div>
          <div className="flex justify-center gap-6 mt-4 text-xs">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-[#00E676]"></div>
              <span className="text-[#71717A]">Trimise</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded bg-purple-500"></div>
              <span className="text-[#71717A]">Răspunsuri</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
