import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '@/contexts/AuthContext';
import { useSite } from '@/contexts/SiteContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { 
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { toast } from 'sonner';
import { 
  FileText, 
  Search, 
  Calendar, 
  Link, 
  TrendingUp, 
  ArrowUpRight,
  PlusCircle,
  Eye,
  MousePointer,
  Globe,
  CheckCircle2,
  AlertCircle,
  Bot,
  Sparkles,
  Clock,
  Settings2
} from 'lucide-react';
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  Legend,
  BarChart,
  Bar,
  Cell
} from 'recharts';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const PERIOD_OPTIONS = [
  { value: '7', label: 'Ultimele 7 zile' },
  { value: '28', label: 'Ultimele 28 zile' },
  { value: '90', label: 'Ultimele 3 luni' },
  { value: '180', label: 'Ultimele 6 luni' }
];

export default function DashboardPage() {
  const [stats, setStats] = useState(null);
  const [searchStats, setSearchStats] = useState(null);
  const [gscStatus, setGscStatus] = useState({ connected: false });
  const [gscSites, setGscSites] = useState([]);
  const [selectedGscSite, setSelectedGscSite] = useState('');
  const [selectedPeriod, setSelectedPeriod] = useState('28');
  const [loading, setLoading] = useState(true);
  const [connectingGsc, setConnectingGsc] = useState(false);
  const [automationStats, setAutomationStats] = useState({ sites: [], weeklyArticles: 0 });
  const [siteStats, setSiteStats] = useState({ stats: [], total_monthly: 0, total_all_time: 0 });
  const [gscLoading, setGscLoading] = useState(false);
  const { getAuthHeaders } = useAuth();
  const { currentSiteId, currentSite } = useSite();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    // Check for GSC callback params
    if (searchParams.get('gsc_connected') === 'true') {
      toast.success('Google Search Console conectat cu succes!');
      window.history.replaceState({}, '', '/dashboard');
    } else if (searchParams.get('gsc_error') === 'true') {
      toast.error('Eroare la conectarea Google Search Console');
      window.history.replaceState({}, '', '/dashboard');
    }
    
    // Reset GSC stats when site changes
    setSearchStats(null);
    fetchData();
  }, [currentSiteId]);

  // Fetch GSC stats when site or period changes
  useEffect(() => {
    if (selectedGscSite && gscStatus.connected && !gscLoading) {
      fetchSearchStats(selectedGscSite, selectedPeriod);
    }
  }, [selectedGscSite, selectedPeriod]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const params = currentSiteId ? { site_id: currentSiteId } : {};
      
      // Use combined endpoint for better performance
      const [dashboardAllRes, gscStatusRes] = await Promise.all([
        axios.get(`${API}/dashboard/all`, { headers: getAuthHeaders(), params }),
        axios.get(`${API}/search-console/status`, { headers: getAuthHeaders() })
      ]);
      
      const dashboardData = dashboardAllRes.data;
      setStats(dashboardData.stats);
      setSiteStats(dashboardData.site_stats);
      setAutomationStats({
        sites: dashboardData.automation.sites.filter(
          item => item.automation.mode === 'automatic' && item.automation.enabled
        ),
        totalSites: dashboardData.automation.totalSites,
        weeklyArticles: dashboardData.automation.weeklyArticles,
        totalAutoArticles: dashboardData.automation.totalAutoArticles
      });
      
      setGscStatus(gscStatusRes.data);

      if (gscStatusRes.data.connected) {
        // Fetch GSC sites
        try {
          const sitesRes = await axios.get(`${API}/search-console/sites`, { headers: getAuthHeaders() });
          const sites = sitesRes.data.sites || [];
          setGscSites(sites);
          
          // Match GSC site with currently selected WordPress site
          let matchedSite = null;
          
          if (currentSite?.site_url) {
            // Try to find GSC site that matches the current WordPress site
            const wpDomain = currentSite.site_url
              .replace(/^https?:\/\//, '')
              .replace(/^www\./, '')
              .replace(/\/$/, '')
              .toLowerCase();
            
            // Priority: 1. Domain property, 2. Exact match without www, 3. Any match
            matchedSite = sites.find(gsc => {
              const gscDomain = gsc.url
                .replace(/^sc-domain:/, '')
                .replace(/^https?:\/\//, '')
                .replace(/^www\./, '')
                .replace(/\/$/, '')
                .toLowerCase();
              return gscDomain === wpDomain;
            });
            
            console.log(`[GSC] Matching WP site "${wpDomain}" -> GSC: ${matchedSite?.url || 'not found'}`);
          }
          
          // Use matched site or first site as fallback
          const siteToSelect = matchedSite?.url || (sites.length > 0 ? sites[0].url : '');
          
          if (siteToSelect && siteToSelect !== selectedGscSite) {
            setSelectedGscSite(siteToSelect);
            // Fetch stats immediately for the matched site
            fetchSearchStats(siteToSelect, selectedPeriod);
          }
        } catch (e) {
          console.error('Failed to fetch GSC sites:', e);
        }
      } else {
        // Fetch mock search stats
        const searchRes = await axios.get(`${API}/search-console/stats`, { headers: getAuthHeaders() });
        setSearchStats(searchRes.data);
      }
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    } finally {
      setLoading(false);
    }
  };

  const [fetchingGsc, setFetchingGsc] = useState(false);
  
  const fetchSearchStats = async (siteUrl, days) => {
    if (fetchingGsc || !siteUrl) return;
    setFetchingGsc(true);
    try {
      const searchRes = await axios.get(`${API}/search-console/stats`, { 
        headers: getAuthHeaders(),
        params: { site_url: siteUrl, days: parseInt(days) }
      });
      setSearchStats(searchRes.data);
    } catch (error) {
      console.error('Failed to fetch search stats:', error);
    } finally {
      setFetchingGsc(false);
    }
  };

  const handleConnectGsc = async () => {
    setConnectingGsc(true);
    try {
      const response = await axios.get(`${API}/search-console/auth-url`, { headers: getAuthHeaders() });
      window.location.href = response.data.authorization_url;
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Eroare la conectarea GSC. Verifică configurarea în backend.');
      setConnectingGsc(false);
    }
  };

  const handleDisconnectGsc = async () => {
    if (!window.confirm('Ești sigur că vrei să deconectezi Google Search Console?')) return;
    try {
      await axios.delete(`${API}/search-console/disconnect`, { headers: getAuthHeaders() });
      setGscStatus({ connected: false });
      setGscSites([]);
      setSelectedGscSite('');
      toast.success('Google Search Console deconectat');
      fetchData();
    } catch (error) {
      toast.error('Eroare la deconectare');
    }
  };

  const handlePeriodChange = (value) => {
    setSelectedPeriod(value);
  };

  const handleGscSiteChange = (value) => {
    setSelectedGscSite(value);
  };

  // Format daily traffic data for chart
  const formatChartData = () => {
    if (!searchStats?.daily_traffic || searchStats.daily_traffic.length === 0) {
      // Return demo data if no real data
      return [
        { name: 'Lun', clicks: 120, impressions: 1200 },
        { name: 'Mar', clicks: 150, impressions: 1500 },
        { name: 'Mie', clicks: 180, impressions: 1800 },
        { name: 'Joi', clicks: 220, impressions: 2200 },
        { name: 'Vin', clicks: 280, impressions: 2800 },
        { name: 'Sâm', clicks: 200, impressions: 2000 },
        { name: 'Dum', clicks: 160, impressions: 1600 },
      ];
    }

    return searchStats.daily_traffic.map(day => ({
      name: new Date(day.date).toLocaleDateString('ro-RO', { day: '2-digit', month: 'short' }),
      clicks: day.clicks,
      impressions: day.impressions
    }));
  };

  const statCards = [
    { 
      title: 'Articole Totale', 
      value: stats?.total_articles || 0, 
      icon: FileText, 
      color: 'text-chart-1',
      bgColor: 'bg-chart-1/10'
    },
    { 
      title: 'Publicate', 
      value: stats?.published_articles || 0, 
      icon: TrendingUp, 
      color: 'text-chart-2',
      bgColor: 'bg-chart-2/10'
    },
    { 
      title: 'Cuvinte-cheie', 
      value: stats?.total_keywords || 0, 
      icon: Search, 
      color: 'text-chart-3',
      bgColor: 'bg-chart-3/10'
    },
    { 
      title: 'Programate', 
      value: stats?.scheduled_posts || 0, 
      icon: Calendar, 
      color: 'text-chart-4',
      bgColor: 'bg-chart-4/10'
    },
    { 
      title: 'Backlinks', 
      value: stats?.backlink_requests || 0, 
      icon: Link, 
      color: 'text-chart-5',
      bgColor: 'bg-chart-5/10'
    },
  ];

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-8 bg-secondary rounded w-48" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-32 bg-secondary rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8" data-testid="dashboard-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="font-heading text-3xl font-bold">Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            Privire de ansamblu asupra performanței SEO
            {currentSite && <span className="text-primary"> - {currentSite.site_name || currentSite.site_url}</span>}
          </p>
        </div>
        <Button 
          className="bg-primary text-primary-foreground hover:bg-primary/90 neon-glow-hover"
          onClick={() => navigate('/articles/new')}
          data-testid="new-article-button"
        >
          <PlusCircle className="w-4 h-4 mr-2" />
          Articol Nou
        </Button>
      </div>

      {/* Quota Progress */}
      <Card className="bg-card border-border">
        <CardContent className="pt-6">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium">Cotă Lunară</span>
            <span className="text-sm text-muted-foreground">
              {stats?.used_quota || 0} / {stats?.monthly_quota || 30} articole
            </span>
          </div>
          <Progress 
            value={((stats?.used_quota || 0) / (stats?.monthly_quota || 30)) * 100} 
            className="h-2"
          />
        </CardContent>
      </Card>

      {/* Automation Widget */}
      <Card className="bg-gradient-to-r from-primary/5 to-primary/10 border-primary/20">
        <CardContent className="pt-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-xl bg-primary/20 flex items-center justify-center">
                <Bot className="w-6 h-6 text-primary" />
              </div>
              <div>
                <h3 className="font-heading font-semibold text-lg flex items-center gap-2">
                  Automatizare Articole
                  {automationStats.sites?.length > 0 && (
                    <Badge className="bg-green-500/20 text-green-400 border-green-500/30">
                      <Sparkles className="w-3 h-3 mr-1" />
                      Activă
                    </Badge>
                  )}
                </h3>
                <p className="text-sm text-muted-foreground">
                  {automationStats.sites?.length > 0 
                    ? `${automationStats.sites.length} site-uri cu automatizare activă`
                    : 'Nicio automatizare activă'
                  }
                </p>
              </div>
            </div>
            
            <div className="flex flex-wrap items-center gap-4">
              {/* Weekly Articles Stat */}
              <div className="flex items-center gap-3 px-4 py-2 rounded-lg bg-background/50">
                <div className="flex items-center gap-2">
                  <Clock className="w-4 h-4 text-primary" />
                  <span className="text-sm text-muted-foreground">Ultima săptămână:</span>
                </div>
                <span className="text-lg font-bold text-primary">{automationStats.weeklyArticles || 0}</span>
                <span className="text-sm text-muted-foreground">articole</span>
              </div>
              
              {/* Total Auto Articles */}
              <div className="flex items-center gap-3 px-4 py-2 rounded-lg bg-background/50">
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-blue-400" />
                  <span className="text-sm text-muted-foreground">Total auto:</span>
                </div>
                <span className="text-lg font-bold text-blue-400">{automationStats.totalAutoArticles || 0}</span>
              </div>
              
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => navigate('/automation')}
                className="border-primary/50 hover:bg-primary/10"
                data-testid="go-to-automation-btn"
              >
                <Settings2 className="w-4 h-4 mr-2" />
                Setări
              </Button>
            </div>
          </div>
          
          {/* Active Sites List */}
          {automationStats.sites?.length > 0 && (
            <div className="mt-4 pt-4 border-t border-primary/20">
              <p className="text-xs text-muted-foreground mb-2">Site-uri active:</p>
              <div className="flex flex-wrap gap-2">
                {automationStats.sites.map((item) => (
                  <Badge 
                    key={item.site.id} 
                    variant="secondary"
                    className="bg-background/80 text-foreground"
                  >
                    <Globe className="w-3 h-3 mr-1 text-primary" />
                    {item.site.site_name || item.site.site_url}
                    <span className="ml-2 text-xs text-muted-foreground">
                      ({item.automation.frequency === 'daily' ? 'zilnic' : 
                        item.automation.frequency === 'every_2_days' ? 'la 2 zile' :
                        item.automation.frequency === 'every_3_days' ? 'la 3 zile' : 'săptămânal'})
                    </span>
                  </Badge>
                ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {statCards.map((stat) => (
          <Card 
            key={stat.title} 
            className="bg-card border-border hover:border-primary/30 transition-colors"
          >
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div className={`p-2 rounded-lg ${stat.bgColor}`}>
                  <stat.icon className={`w-5 h-5 ${stat.color}`} />
                </div>
                <ArrowUpRight className="w-4 h-4 text-muted-foreground" />
              </div>
              <div className="mt-4">
                <p className="text-2xl font-bold font-heading">{stat.value}</p>
                <p className="text-sm text-muted-foreground">{stat.title}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Traffic Chart */}
        <Card className="lg:col-span-2 bg-card border-border">
          <CardHeader>
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <CardTitle className="font-heading text-lg">
                  Trafic {gscStatus.connected ? 'Real' : 'Demo'}
                </CardTitle>
                {gscStatus.connected && currentSite && (
                  <CardDescription className="text-xs mt-1">
                    {currentSite.site_name || currentSite.site_url}
                  </CardDescription>
                )}
                {!currentSite && (
                  <CardDescription className="text-xs mt-1 text-yellow-500">
                    Selectează un site din meniul din stânga
                  </CardDescription>
                )}
              </div>
              <div className="flex gap-2">
                <Select value={selectedPeriod} onValueChange={handlePeriodChange}>
                  <SelectTrigger className="w-[160px] bg-secondary border-border">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-card border-border">
                    {PERIOD_OPTIONS.map(option => (
                      <SelectItem key={option.value} value={option.value}>
                        {option.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={formatChartData()}>
                  <defs>
                    <linearGradient id="colorClicks" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#00E676" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#00E676" stopOpacity={0}/>
                    </linearGradient>
                    <linearGradient id="colorImpressions" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#2196F3" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#2196F3" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#262626" />
                  <XAxis dataKey="name" stroke="#A1A1AA" fontSize={12} />
                  <YAxis stroke="#A1A1AA" fontSize={12} />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#0A0A0A', 
                      border: '1px solid #262626',
                      borderRadius: '8px'
                    }}
                  />
                  <Legend />
                  <Area 
                    type="monotone" 
                    dataKey="clicks" 
                    name="Clicks"
                    stroke="#00E676" 
                    fillOpacity={1} 
                    fill="url(#colorClicks)" 
                  />
                  <Area 
                    type="monotone" 
                    dataKey="impressions" 
                    name="Impresii"
                    stroke="#2196F3" 
                    fillOpacity={1} 
                    fill="url(#colorImpressions)" 
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Google Search Console Stats */}
        <Card className="bg-card border-border">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="font-heading text-lg">Google Search Console</CardTitle>
              {gscStatus.connected ? (
                <Badge className="bg-green-500/10 text-green-500 border-green-500/20">
                  <CheckCircle2 className="w-3 h-3 mr-1" /> Conectat
                </Badge>
              ) : (
                <Badge className="bg-yellow-500/10 text-yellow-500 border-yellow-500/20">
                  <AlertCircle className="w-3 h-3 mr-1" /> Demo
                </Badge>
              )}
            </div>
            {gscStatus.connected && (
              <CardDescription className="text-xs mt-2">
                Perioada: {PERIOD_OPTIONS.find(o => o.value === selectedPeriod)?.label}
              </CardDescription>
            )}
            {!gscStatus.connected && (
              <CardDescription className="text-xs mt-2">
                Date simulate. Conectează GSC pentru date reale.
              </CardDescription>
            )}
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 rounded-lg bg-secondary">
                <div className="flex items-center gap-3">
                  <MousePointer className="w-5 h-5 text-chart-1" />
                  <span className="text-sm">Clicks</span>
                </div>
                <span className="font-mono font-bold">{searchStats?.clicks?.toLocaleString() || 0}</span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg bg-secondary">
                <div className="flex items-center gap-3">
                  <Eye className="w-5 h-5 text-chart-2" />
                  <span className="text-sm">Impresii</span>
                </div>
                <span className="font-mono font-bold">{searchStats?.impressions?.toLocaleString() || 0}</span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg bg-secondary">
                <div className="flex items-center gap-3">
                  <TrendingUp className="w-5 h-5 text-chart-3" />
                  <span className="text-sm">CTR</span>
                </div>
                <span className="font-mono font-bold">{searchStats?.ctr || 0}%</span>
              </div>
              <div className="flex items-center justify-between p-3 rounded-lg bg-secondary">
                <div className="flex items-center gap-3">
                  <Search className="w-5 h-5 text-chart-4" />
                  <span className="text-sm">Poziție Medie</span>
                </div>
                <span className="font-mono font-bold">{searchStats?.position || 0}</span>
              </div>
            </div>

            {/* Connect/Disconnect GSC */}
            {!gscStatus.connected ? (
              <Button
                className="w-full bg-blue-600 hover:bg-blue-700 text-white"
                onClick={handleConnectGsc}
                disabled={connectingGsc}
                data-testid="connect-gsc-button"
              >
                <Globe className="w-4 h-4 mr-2" />
                {connectingGsc ? 'Se conectează...' : 'Conectează Google Search Console'}
              </Button>
            ) : (
              <Button
                variant="outline"
                className="w-full border-destructive text-destructive hover:bg-destructive hover:text-white"
                onClick={handleDisconnectGsc}
                data-testid="disconnect-gsc-button"
              >
                Deconectează GSC
              </Button>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Monthly Article Stats per Site */}
      {siteStats.stats?.length > 0 && (
        <Card className="bg-card border-border" data-testid="monthly-stats-widget">
          <CardHeader>
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <CardTitle className="font-heading text-lg flex items-center gap-2">
                  <Bot className="w-5 h-5 text-primary" />
                  Articole Generate Automat - Ultima Lună
                </CardTitle>
                <CardDescription>
                  {siteStats.total_monthly} articole generate în ultimele 30 de zile
                </CardDescription>
              </div>
              <div className="flex items-center gap-3">
                <div className="text-right">
                  <p className="text-2xl font-bold text-primary">{siteStats.total_all_time}</p>
                  <p className="text-xs text-muted-foreground">total articole auto</p>
                </div>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {/* Bar Chart */}
            <div className="h-[250px] mb-6">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart 
                  data={siteStats.stats} 
                  layout="vertical"
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#262626" horizontal={false} />
                  <XAxis type="number" stroke="#A1A1AA" fontSize={12} />
                  <YAxis 
                    type="category" 
                    dataKey="site_name" 
                    stroke="#A1A1AA" 
                    fontSize={11}
                    width={120}
                    tickFormatter={(value) => value.length > 15 ? value.substring(0, 15) + '...' : value}
                  />
                  <Tooltip 
                    contentStyle={{ 
                      backgroundColor: '#0A0A0A', 
                      border: '1px solid #262626',
                      borderRadius: '8px'
                    }}
                    formatter={(value, name) => [value, name === 'monthly_articles' ? 'Luna aceasta' : 'Total']}
                  />
                  <Bar 
                    dataKey="monthly_articles" 
                    name="Luna aceasta"
                    radius={[0, 4, 4, 0]}
                  >
                    {siteStats.stats.map((entry, index) => (
                      <Cell 
                        key={`cell-${index}`} 
                        fill={entry.is_active && !entry.is_paused ? '#00E676' : entry.is_paused ? '#FFC107' : '#6B7280'} 
                      />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Sites Detail List */}
            <div className="space-y-2">
              {siteStats.stats.map((site, index) => (
                <div 
                  key={site.site_id}
                  className="flex items-center justify-between p-3 rounded-lg bg-secondary/50 hover:bg-secondary transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-8 rounded-full ${
                      site.is_active && !site.is_paused ? 'bg-green-500' : 
                      site.is_paused ? 'bg-yellow-500' : 'bg-gray-500'
                    }`} />
                    <div>
                      <p className="font-medium text-sm">{site.site_name}</p>
                      <p className="text-xs text-muted-foreground">{site.niche}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-4">
                    <div className="text-right">
                      <p className="text-lg font-bold text-primary">{site.monthly_articles}</p>
                      <p className="text-xs text-muted-foreground">luna aceasta</p>
                    </div>
                    <div className="text-right border-l border-border pl-4">
                      <p className="text-lg font-semibold text-muted-foreground">{site.total_articles}</p>
                      <p className="text-xs text-muted-foreground">total</p>
                    </div>
                    {site.expected_monthly > 0 && (
                      <div className="text-right border-l border-border pl-4">
                        <p className="text-sm text-muted-foreground">
                          {Math.round((site.monthly_articles / site.expected_monthly) * 100)}%
                        </p>
                        <p className="text-xs text-muted-foreground">din țintă</p>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* Legend */}
            <div className="flex items-center gap-4 mt-4 pt-4 border-t border-border text-xs text-muted-foreground">
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full bg-green-500" />
                <span>Activ</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full bg-yellow-500" />
                <span>În pauză</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 rounded-full bg-gray-500" />
                <span>Manual/Inactiv</span>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Top Queries */}
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="font-heading text-lg">Top Căutări</CardTitle>
          {gscStatus.connected && (
            <CardDescription className="text-xs">
              Cele mai populare căutări pentru {selectedGscSite || 'site-ul selectat'}
            </CardDescription>
          )}
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {searchStats?.top_queries?.map((query, index) => (
              <div 
                key={index}
                className="flex items-center justify-between p-3 rounded-lg bg-secondary hover:bg-accent transition-colors"
              >
                <div className="flex items-center gap-3">
                  <span className="w-6 h-6 rounded-full bg-primary/20 text-primary text-xs font-bold flex items-center justify-center">
                    {index + 1}
                  </span>
                  <span className="font-medium">{query.query}</span>
                </div>
                <div className="flex items-center gap-6 text-sm text-muted-foreground">
                  <span>{query.clicks} clicks</span>
                  <span>{query.impressions} impresii</span>
                  {query.ctr !== undefined && <span>{query.ctr}% CTR</span>}
                  {query.position !== undefined && <span>Pos: {query.position}</span>}
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
