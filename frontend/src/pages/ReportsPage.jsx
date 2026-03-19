import { useState, useEffect } from 'react';
import { useSite } from '@/contexts/SiteContext';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { useToast } from '@/hooks/use-toast';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  Legend,
  Area,
  AreaChart
} from 'recharts';
import {
  FileText,
  TrendingUp,
  Calendar,
  BarChart3,
  RefreshCw,
  CheckCircle,
  Clock,
  ShoppingCart,
  Sparkles,
  Globe,
  PieChart as PieChartIcon
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Chart colors
const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];
const PRIMARY_COLOR = '#10b981';
const SECONDARY_COLOR = '#3b82f6';

export default function ReportsPage() {
  const { currentSite } = useSite();
  const { toast } = useToast();
  const [loading, setLoading] = useState(false);
  const [weeklyReport, setWeeklyReport] = useState(null);
  const [monthlyReport, setMonthlyReport] = useState(null);
  const [activeTab, setActiveTab] = useState('weekly');

  const fetchReports = async () => {
    setLoading(true);
    const token = localStorage.getItem('token');

    try {
      const [weeklyRes, monthlyRes] = await Promise.all([
        fetch(`${API_URL}/api/reports/weekly`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        fetch(`${API_URL}/api/reports/monthly`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);

      if (weeklyRes.ok) {
        const data = await weeklyRes.json();
        setWeeklyReport(data);
      }

      if (monthlyRes.ok) {
        const data = await monthlyRes.json();
        setMonthlyReport(data);
      }
    } catch (error) {
      toast({
        title: 'Eroare',
        description: 'Nu s-au putut încărca rapoartele',
        variant: 'destructive'
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const formatDate = (isoString) => {
    if (!isoString) return '-';
    const date = new Date(isoString);
    return date.toLocaleDateString('ro-RO', {
      day: 'numeric',
      month: 'short',
      year: 'numeric'
    });
  };

  const formatShortDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('ro-RO', { day: 'numeric', month: 'short' });
  };

  const StatCard = ({ icon: Icon, label, value, subtext, color = 'primary' }) => (
    <Card className="bg-card/50 border-border/50">
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm text-muted-foreground">{label}</p>
            <p className="text-2xl font-bold mt-1">{value}</p>
            {subtext && <p className="text-xs text-muted-foreground mt-1">{subtext}</p>}
          </div>
          <div className={`p-2 rounded-lg bg-${color}/10`}>
            <Icon className={`w-5 h-5 text-${color}`} />
          </div>
        </div>
      </CardContent>
    </Card>
  );

  // Custom tooltip for charts
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-card border border-border rounded-lg p-3 shadow-lg">
          <p className="text-sm font-medium text-foreground">{label}</p>
          {payload.map((entry, index) => (
            <p key={index} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {entry.value}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  const renderReport = (report, periodLabel) => {
    if (!report) {
      return (
        <div className="text-center py-12 text-muted-foreground">
          <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
          <p>Nu sunt date disponibile pentru această perioadă</p>
        </div>
      );
    }

    const { summary, article_types, sites_stats, daily_stats, period } = report;

    // Prepare daily chart data
    const dailyChartData = daily_stats 
      ? Object.entries(daily_stats)
          .sort(([a], [b]) => new Date(a) - new Date(b))
          .map(([date, stats]) => ({
            date: formatShortDate(date),
            fullDate: date,
            generate: stats.generated,
            publicate: stats.published
          }))
      : [];

    // Prepare article types pie chart data
    const articleTypesData = article_types 
      ? Object.entries(article_types).map(([type, count], index) => ({
          name: type,
          value: count,
          color: COLORS[index % COLORS.length]
        }))
      : [];

    // Prepare sites bar chart data
    const sitesChartData = sites_stats 
      ? sites_stats.map(site => ({
          name: site.site_name?.length > 15 
            ? site.site_name.substring(0, 15) + '...' 
            : site.site_name,
          fullName: site.site_name,
          generate: site.articles_generated,
          publicate: site.articles_published,
          draft: site.articles_draft
        }))
      : [];

    const hasData = summary?.total_articles > 0;

    return (
      <div className="space-y-6">
        {/* Period Header */}
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold">Raport {periodLabel}</h3>
            <p className="text-sm text-muted-foreground">
              {formatDate(period?.start)} - {formatDate(period?.end)}
            </p>
          </div>
          <Badge variant="outline" className="text-primary">
            <Calendar className="w-3 h-3 mr-1" />
            {period?.days || 7} zile
          </Badge>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard
            icon={FileText}
            label="Total Articole"
            value={summary?.total_articles || 0}
            color="primary"
          />
          <StatCard
            icon={CheckCircle}
            label="Publicate"
            value={summary?.published || 0}
            subtext={`${summary?.drafts || 0} draft-uri`}
            color="green-500"
          />
          <StatCard
            icon={ShoppingCart}
            label="Cu Produse"
            value={summary?.with_product_links || 0}
            color="blue-500"
          />
          <StatCard
            icon={Sparkles}
            label="Cu Trending"
            value={summary?.with_trending_keywords || 0}
            color="yellow-500"
          />
        </div>

        {/* Charts Row 1: Daily Activity + Quality Metrics */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Daily Activity Chart */}
          <Card className="bg-card/50 border-border/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center gap-2">
                <TrendingUp className="w-4 h-4 text-primary" />
                Activitate Zilnică
              </CardTitle>
              <CardDescription>Articole generate și publicate pe zi</CardDescription>
            </CardHeader>
            <CardContent>
              {dailyChartData.length > 0 ? (
                <ResponsiveContainer width="100%" height={250}>
                  <AreaChart data={dailyChartData}>
                    <defs>
                      <linearGradient id="colorGenerate" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={PRIMARY_COLOR} stopOpacity={0.3}/>
                        <stop offset="95%" stopColor={PRIMARY_COLOR} stopOpacity={0}/>
                      </linearGradient>
                      <linearGradient id="colorPublicate" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={SECONDARY_COLOR} stopOpacity={0.3}/>
                        <stop offset="95%" stopColor={SECONDARY_COLOR} stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#333" />
                    <XAxis 
                      dataKey="date" 
                      stroke="#888" 
                      fontSize={12}
                      tickLine={false}
                    />
                    <YAxis 
                      stroke="#888" 
                      fontSize={12}
                      tickLine={false}
                      allowDecimals={false}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Area
                      type="monotone"
                      dataKey="generate"
                      name="Generate"
                      stroke={PRIMARY_COLOR}
                      fill="url(#colorGenerate)"
                      strokeWidth={2}
                    />
                    <Area
                      type="monotone"
                      dataKey="publicate"
                      name="Publicate"
                      stroke={SECONDARY_COLOR}
                      fill="url(#colorPublicate)"
                      strokeWidth={2}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-[250px] flex items-center justify-center text-muted-foreground">
                  <p>Nu sunt date pentru grafic</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Quality Metrics */}
          <Card className="bg-card/50 border-border/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-base flex items-center gap-2">
                <BarChart3 className="w-4 h-4 text-primary" />
                Metrici de Calitate
              </CardTitle>
              <CardDescription>Scor SEO și lungime medie articole</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span>Scor SEO Mediu</span>
                  <span className="font-bold text-lg text-primary">{summary?.avg_seo_score || 0}/100</span>
                </div>
                <Progress value={summary?.avg_seo_score || 0} className="h-3" />
                <p className="text-xs text-muted-foreground mt-1">
                  {summary?.avg_seo_score >= 80 ? '✓ Excelent' : 
                   summary?.avg_seo_score >= 60 ? '○ Bun' : 
                   summary?.avg_seo_score > 0 ? '✗ Necesită îmbunătățiri' : '-'}
                </p>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span>Cuvinte Medii per Articol</span>
                  <span className="font-bold text-lg text-blue-500">{summary?.avg_word_count || 0}</span>
                </div>
                <Progress 
                  value={Math.min((summary?.avg_word_count || 0) / 20, 100)} 
                  className="h-3" 
                />
                <p className="text-xs text-muted-foreground mt-1">
                  {summary?.avg_word_count >= 1500 ? '✓ Articole comprehensive' : 
                   summary?.avg_word_count >= 800 ? '○ Lungime standard' : 
                   summary?.avg_word_count > 0 ? '✗ Articole scurte' : '-'}
                </p>
              </div>
              
              {/* Mini stats */}
              <div className="grid grid-cols-2 gap-4 pt-4 border-t border-border/50">
                <div className="text-center">
                  <p className="text-2xl font-bold text-green-500">
                    {summary?.total_articles > 0 
                      ? Math.round((summary?.published / summary?.total_articles) * 100) 
                      : 0}%
                  </p>
                  <p className="text-xs text-muted-foreground">Rată Publicare</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold text-yellow-500">
                    {summary?.with_product_links || 0}
                  </p>
                  <p className="text-xs text-muted-foreground">Cu Link-uri Produse</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Charts Row 2: Article Types Pie + Sites Bar */}
        {hasData && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Article Types Pie Chart */}
            {articleTypesData.length > 0 && (
              <Card className="bg-card/50 border-border/50">
                <CardHeader className="pb-2">
                  <CardTitle className="text-base flex items-center gap-2">
                    <PieChartIcon className="w-4 h-4 text-primary" />
                    Distribuție Tipuri Articole
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={250}>
                    <PieChart>
                      <Pie
                        data={articleTypesData}
                        cx="50%"
                        cy="50%"
                        innerRadius={60}
                        outerRadius={90}
                        paddingAngle={2}
                        dataKey="value"
                        label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                        labelLine={false}
                      >
                        {articleTypesData.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip content={<CustomTooltip />} />
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="flex flex-wrap justify-center gap-3 mt-2">
                    {articleTypesData.map((entry, index) => (
                      <div key={index} className="flex items-center gap-1">
                        <div 
                          className="w-3 h-3 rounded-full" 
                          style={{ backgroundColor: entry.color }}
                        />
                        <span className="text-xs text-muted-foreground">
                          {entry.name}: {entry.value}
                        </span>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Sites Performance Bar Chart */}
            {sitesChartData.length > 0 && (
              <Card className="bg-card/50 border-border/50">
                <CardHeader className="pb-2">
                  <CardTitle className="text-base flex items-center gap-2">
                    <Globe className="w-4 h-4 text-primary" />
                    Performanță per Site
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={250}>
                    <BarChart data={sitesChartData} layout="vertical">
                      <CartesianGrid strokeDasharray="3 3" stroke="#333" horizontal={false} />
                      <XAxis type="number" stroke="#888" fontSize={12} allowDecimals={false} />
                      <YAxis 
                        type="category" 
                        dataKey="name" 
                        stroke="#888" 
                        fontSize={11}
                        width={100}
                        tickLine={false}
                      />
                      <Tooltip content={<CustomTooltip />} />
                      <Bar dataKey="generate" name="Generate" fill={PRIMARY_COLOR} radius={[0, 4, 4, 0]} />
                      <Bar dataKey="publicate" name="Publicate" fill={SECONDARY_COLOR} radius={[0, 4, 4, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                  <div className="flex justify-center gap-6 mt-2">
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded" style={{ backgroundColor: PRIMARY_COLOR }} />
                      <span className="text-xs text-muted-foreground">Generate</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="w-3 h-3 rounded" style={{ backgroundColor: SECONDARY_COLOR }} />
                      <span className="text-xs text-muted-foreground">Publicate</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        )}

        {/* Sites Stats Table (compact view) */}
        {sites_stats && sites_stats.length > 0 && (
          <Card className="bg-card/50 border-border/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-base">Detalii Site-uri</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {sites_stats.map((site) => (
                  <div
                    key={site.site_id}
                    className="flex items-center justify-between p-3 rounded-lg bg-secondary/30 hover:bg-secondary/50 transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <Globe className="w-4 h-4 text-primary" />
                      <span className="font-medium text-sm">{site.site_name}</span>
                    </div>
                    <div className="flex items-center gap-6 text-sm">
                      <div className="text-center">
                        <span className="font-bold text-foreground">{site.articles_generated}</span>
                        <span className="text-muted-foreground ml-1">gen.</span>
                      </div>
                      <div className="text-center">
                        <span className="font-bold text-green-500">{site.articles_published}</span>
                        <span className="text-muted-foreground ml-1">pub.</span>
                      </div>
                      <div className="text-center">
                        <span className="font-bold text-yellow-500">{site.articles_draft}</span>
                        <span className="text-muted-foreground ml-1">draft</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-6" data-testid="reports-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold">Rapoarte de Performanță</h1>
          <p className="text-muted-foreground">
            Vizualizează statisticile și performanța articolelor generate
          </p>
        </div>
        <Button
          onClick={fetchReports}
          disabled={loading}
          variant="outline"
          data-testid="refresh-reports-btn"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Actualizează
        </Button>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="grid w-full max-w-md grid-cols-2">
          <TabsTrigger value="weekly" data-testid="weekly-tab">
            <Clock className="w-4 h-4 mr-2" />
            Săptămânal
          </TabsTrigger>
          <TabsTrigger value="monthly" data-testid="monthly-tab">
            <BarChart3 className="w-4 h-4 mr-2" />
            Lunar
          </TabsTrigger>
        </TabsList>

        <TabsContent value="weekly" className="mt-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <RefreshCw className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : (
            renderReport(weeklyReport, 'Săptămânal')
          )}
        </TabsContent>

        <TabsContent value="monthly" className="mt-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <RefreshCw className="w-8 h-8 animate-spin text-primary" />
            </div>
          ) : (
            renderReport(monthlyReport, 'Lunar')
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
