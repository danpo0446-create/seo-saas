import { useState, useEffect } from 'react';
import { useSite } from '@/contexts/SiteContext';
import axios from 'axios';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Switch } from '@/components/ui/switch';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Bot,
  Settings2,
  Play,
  Clock,
  Calendar,
  FileText,
  Link2,
  Globe,
  Loader2,
  CheckCircle2,
  XCircle,
  History,
  Sparkles,
  AlertCircle,
  Bell,
  BellOff,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  List
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Request browser notification permission
const requestNotificationPermission = async () => {
  if (!('Notification' in window)) {
    toast.error('Browserul nu suportă notificări');
    return false;
  }
  
  if (Notification.permission === 'granted') {
    return true;
  }
  
  if (Notification.permission !== 'denied') {
    const permission = await Notification.requestPermission();
    return permission === 'granted';
  }
  
  return false;
};

// Send browser notification
const sendBrowserNotification = (title, body, icon = '🤖') => {
  if (Notification.permission === 'granted') {
    new Notification(title, {
      body,
      icon: '/favicon.ico',
      badge: '/favicon.ico',
      tag: 'seo-automation'
    });
  }
};

export default function AutomationPage() {
  const { sites, currentSite } = useSite();
  const [siteSettings, setSiteSettings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingSite, setEditingSite] = useState(null);
  const [editSettings, setEditSettings] = useState(null);
  const [saving, setSaving] = useState(false);
  const [generating, setGenerating] = useState(null);
  const [history, setHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [notificationsEnabled, setNotificationsEnabled] = useState(false);
  const [calendarMonth, setCalendarMonth] = useState(new Date());
  const [activeTab, setActiveTab] = useState('settings');
  const [publicationLog, setPublicationLog] = useState([]);
  const [loadingLog, setLoadingLog] = useState(false);
  const [publishedArticles, setPublishedArticles] = useState([]);

  // Check notification permission on mount
  useEffect(() => {
    if ('Notification' in window) {
      setNotificationsEnabled(Notification.permission === 'granted');
    }
  }, []);

  // Fetch published articles for calendar checkmarks
  const fetchPublishedArticles = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/automation/publication-log`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      console.log('[BIFA] Fetched published articles:', response.data.length);
      console.log('[BIFA] First 3 articles:', response.data.slice(0, 3).map(a => ({
        title: a.title?.substring(0, 30),
        site_id: a.site_id,
        site_name: a.site_name,
        published_at: a.published_at
      })));
      setPublishedArticles(response.data);
    } catch (error) {
      console.error('Error fetching published articles:', error);
    }
  };

  useEffect(() => {
    fetchPublishedArticles();
    // Refresh calendar data every 30 seconds
    const interval = setInterval(fetchPublishedArticles, 30000);
    return () => clearInterval(interval);
  }, []);

  const toggleNotifications = async () => {
    if (notificationsEnabled) {
      setNotificationsEnabled(false);
      toast.info('Notificările au fost dezactivate');
    } else {
      const granted = await requestNotificationPermission();
      setNotificationsEnabled(granted);
      if (granted) {
        toast.success('Notificările au fost activate!');
        sendBrowserNotification('Notificări Active', 'Vei primi notificări când articolele sunt generate automat.');
      } else {
        toast.error('Nu s-au putut activa notificările');
      }
    }
  };

  const fetchSiteSettings = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/automation/sites`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSiteSettings(response.data);
    } catch (error) {
      toast.error('Eroare la încărcarea setărilor');
    } finally {
      setLoading(false);
    }
  };

  const fetchHistory = async () => {
    setLoadingHistory(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/automation/history`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setHistory(response.data);
    } catch (error) {
      toast.error('Eroare la încărcarea istoricului');
    } finally {
      setLoadingHistory(false);
    }
  };

  const fetchPublicationLog = async () => {
    setLoadingLog(true);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API_URL}/api/automation/publication-log`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPublicationLog(response.data);
    } catch (error) {
      toast.error('Eroare la încărcarea jurnalului de publicări');
    } finally {
      setLoadingLog(false);
    }
  };

  useEffect(() => {
    fetchSiteSettings();
  }, []);

  const openEditDialog = (siteData) => {
    setEditingSite(siteData.site);
    setEditSettings({
      mode: siteData.automation.mode || 'manual',
      enabled: siteData.automation.enabled || false,
      paused: siteData.automation.paused || false,
      generation_hour: siteData.automation.generation_hour || 9,
      frequency: siteData.automation.frequency || 'daily',
      article_length: siteData.automation.article_length || 'medium',
      publish_mode: siteData.automation.publish_mode || 'draft',
      email_notification: siteData.automation.email_notification !== false,
      include_product_links: siteData.automation.include_product_links || false,
      product_links_source: siteData.automation.product_links_source || '',
      max_product_links: siteData.automation.max_product_links || 3
    });
  };

  const saveSettings = async () => {
    if (!editingSite || !editSettings) return;
    
    setSaving(true);
    try {
      const token = localStorage.getItem('token');
      await axios.post(
        `${API_URL}/api/automation/site/${editingSite.id}`,
        {
          site_id: editingSite.id,
          ...editSettings
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Setări salvate cu succes!');
      setEditingSite(null);
      setEditSettings(null);
      fetchSiteSettings();
    } catch (error) {
      toast.error('Eroare la salvarea setărilor');
    } finally {
      setSaving(false);
    }
  };

  const generateNow = async (siteId, siteName) => {
    setGenerating(siteId);
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(
        `${API_URL}/api/automation/generate-now`,
        null,
        { 
          headers: { Authorization: `Bearer ${token}` },
          params: { site_id: siteId }
        }
      );
      toast.success(`Articol generat: "${response.data.title}"`);
      
      // Send browser notification
      if (notificationsEnabled) {
        sendBrowserNotification(
          '🆕 Articol Nou Generat!',
          `"${response.data.title}" pentru ${siteName}`
        );
      }
      
      fetchSiteSettings();
    } catch (error) {
      toast.error(`Eroare la generare: ${error.response?.data?.detail || 'Eroare necunoscută'}`);
    } finally {
      setGenerating(null);
    }
  };

  const getFrequencyLabel = (freq) => {
    const labels = {
      daily: 'Zilnic',
      every_2_days: 'La 2 zile',
      every_3_days: 'La 3 zile',
      weekly: 'Săptămânal'
    };
    return labels[freq] || freq;
  };

  const getLengthLabel = (length) => {
    const labels = {
      short: 'Scurt (~500 cuvinte)',
      medium: 'Mediu (~1000 cuvinte)',
      long: 'Lung (~2000 cuvinte)'
    };
    return labels[length] || length;
  };

  const formatDate = (dateString) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString('ro-RO', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  // Calendar logic - check if article was published on a specific date for a site
  const isPublishedOnDate = (siteId, dateKey) => {
    const found = publishedArticles.some(article => {
      if (article.site_id !== siteId) return false;
      const publishedAt = article.published_at || article.created_at;
      if (!publishedAt) return false;
      
      // Convert UTC time to Romania timezone (UTC+2 or UTC+3 for DST)
      const publishedDate = new Date(publishedAt);
      
      // Format to Romania timezone - YYYY-MM-DD
      const romaniaDate = publishedDate.toLocaleDateString('sv-SE', { 
        timeZone: 'Europe/Bucharest' 
      });
      
      const match = romaniaDate === dateKey;
      if (match) {
        console.log(`[BIFA] Match found! Site: ${siteId}, Date: ${dateKey}, Article: ${article.title}`);
      }
      return match;
    });
    return found;
  };
  
  // Check if ANY article was published on a specific date (regardless of site)
  const anyArticlePublishedOnDate = (dateKey) => {
    return publishedArticles.some(article => {
      const publishedAt = article.published_at || article.created_at;
      if (!publishedAt) return false;
      const publishedDate = new Date(publishedAt);
      const romaniaDate = publishedDate.toLocaleDateString('sv-SE', { 
        timeZone: 'Europe/Bucharest' 
      });
      return romaniaDate === dateKey;
    });
  };
  
  // Get articles published on a specific date
  const getArticlesForDate = (dateKey) => {
    const articles = publishedArticles.filter(article => {
      const publishedAt = article.published_at || article.created_at;
      if (!publishedAt) return false;
      const publishedDate = new Date(publishedAt);
      const romaniaDate = publishedDate.toLocaleDateString('sv-SE', { 
        timeZone: 'Europe/Bucharest' 
      });
      return romaniaDate === dateKey;
    });
    if (articles.length > 0) {
      console.log(`[BIFA] Date ${dateKey}: Found ${articles.length} articles`);
    }
    return articles;
  };

  const getScheduledDates = () => {
    const dates = {};
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    // Get active sites (automatic, enabled, not paused)
    const activeSites = siteSettings.filter(item => 
      item.automation.mode === 'automatic' && 
      item.automation.enabled && 
      !item.automation.paused
    );
    
    activeSites.forEach(item => {
      const freq = item.automation.frequency;
      const freqDays = { daily: 1, every_2_days: 2, every_3_days: 3, weekly: 7 };
      const interval = freqDays[freq] || 1;
      
      // Start from the first day of current month view
      const startOfMonth = new Date(calendarMonth.getFullYear(), calendarMonth.getMonth(), 1);
      
      // Start from the first day of the month
      let scheduleDate = new Date(startOfMonth);
      scheduleDate.setHours(item.automation.generation_hour, 0, 0, 0);
      
      // Generate for 120 days to cover current month and next months
      for (let i = 0; i < 120; i++) {
        const dateKey = scheduleDate.toISOString().split('T')[0];
        
        // Only add if within reasonable range
        if (scheduleDate >= startOfMonth) {
          if (!dates[dateKey]) dates[dateKey] = [];
          
          // Avoid duplicates for the same site on the same day
          const alreadyAdded = dates[dateKey].some(d => d.siteId === item.site.id);
          if (!alreadyAdded) {
            dates[dateKey].push({
              siteId: item.site.id,
              site: item.site.site_name || item.site.site_url,
              hour: item.automation.generation_hour,
              color: getColorForSite(item.site.id)
            });
          }
        }
        
        scheduleDate.setDate(scheduleDate.getDate() + interval);
      }
    });
    
    return dates;
  };

  const getColorForSite = (siteId) => {
    const colors = ['bg-green-500', 'bg-blue-500', 'bg-purple-500', 'bg-orange-500', 'bg-pink-500'];
    const index = siteSettings.findIndex(s => s.site.id === siteId);
    return colors[index % colors.length];
  };

  const renderCalendar = () => {
    const scheduledDates = getScheduledDates();
    const year = calendarMonth.getFullYear();
    const month = calendarMonth.getMonth();
    
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const startPadding = firstDay.getDay() === 0 ? 6 : firstDay.getDay() - 1;
    
    // Calculate dynamic height based on number of active sites
    const activeSitesCount = siteSettings.filter(s => 
      s.automation.mode === 'automatic' && s.automation.enabled && !s.automation.paused
    ).length;
    const cellHeight = Math.max(120, 40 + (activeSitesCount * 28)); // 28px per site + header
    
    const days = [];
    const monthNames = ['Ianuarie', 'Februarie', 'Martie', 'Aprilie', 'Mai', 'Iunie', 
                        'Iulie', 'August', 'Septembrie', 'Octombrie', 'Noiembrie', 'Decembrie'];
    
    // Empty cells for padding
    for (let i = 0; i < startPadding; i++) {
      days.push(<div key={`pad-${i}`} style={{ height: `${cellHeight}px` }} className="bg-secondary/30 rounded-lg" />);
    }
    
    // Days of month
    for (let day = 1; day <= lastDay.getDate(); day++) {
      const dateKey = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
      const scheduled = scheduledDates[dateKey] || [];
      const isToday = new Date().toISOString().split('T')[0] === dateKey;
      const isPast = new Date(dateKey) < new Date(new Date().toISOString().split('T')[0]);
      
      // Get articles published on this date (for showing checkmarks even without schedule)
      const articlesOnDate = getArticlesForDate(dateKey);
      
      days.push(
        <div 
          key={day} 
          style={{ height: `${cellHeight}px` }}
          className={`rounded-lg p-2 transition-colors flex flex-col ${
            isToday ? 'bg-primary/20 border-2 border-primary' : 'bg-secondary/50 hover:bg-secondary'
          }`}
        >
          <div className={`text-sm font-medium mb-2 ${isToday ? 'text-primary' : 'text-muted-foreground'}`}>
            {day}
          </div>
          <div className="flex-1 space-y-1 overflow-auto">
            {/* Show scheduled items */}
            {scheduled.map((item, idx) => {
              // Check if published - works for today AND past dates
              const wasPublished = isPublishedOnDate(item.siteId, dateKey);
              return (
                <div 
                  key={idx}
                  className={`text-xs px-2 py-1.5 rounded flex items-center justify-between ${item.color} text-white`}
                  title={`${item.site} la ${item.hour}:00${wasPublished ? ' ✓ Publicat' : ''}`}
                >
                  <span className="flex items-center gap-1.5 truncate">
                    <Clock className="w-3 h-3 flex-shrink-0" />
                    <span className="font-medium">{item.hour}:00</span>
                    <span className="truncate">{item.site}</span>
                  </span>
                  {wasPublished && (
                    <CheckCircle2 className="w-4 h-4 flex-shrink-0 ml-1" />
                  )}
                </div>
              );
            })}
            
            {/* Show ALL published articles for this date (including manual publications) */}
            {articlesOnDate.length > 0 && (
              articlesOnDate.map((article, idx) => {
                // Check if this article's site is already shown in scheduled items with a checkmark
                const isScheduledSite = scheduled.some(s => s.siteId === article.site_id);
                // If it's a scheduled site AND was published, skip (already shown above with checkmark)
                if (isScheduledSite && isPublishedOnDate(article.site_id, dateKey)) return null;
                return (
                  <div 
                    key={`pub-${idx}`}
                    className="text-xs px-2 py-1.5 rounded flex items-center justify-between bg-green-600 text-white"
                    title={`✓ ${article.title}`}
                  >
                    <span className="flex items-center gap-1.5 truncate">
                      <CheckCircle2 className="w-3 h-3 flex-shrink-0" />
                      <span className="truncate">{article.site_name || 'Publicat'}</span>
                    </span>
                    <CheckCircle2 className="w-4 h-4 flex-shrink-0 ml-1" />
                  </div>
                );
              })
            )}
          </div>
        </div>
      );
    }
    
    return (
      <Card className="bg-card border-border">
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Calendar className="w-5 h-5 text-primary" />
              Calendar Generări
            </CardTitle>
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="icon"
                onClick={() => setCalendarMonth(new Date(year, month - 1, 1))}
              >
                <ChevronLeft className="w-4 h-4" />
              </Button>
              <span className="font-medium min-w-32 text-center">
                {monthNames[month]} {year}
              </span>
              <Button
                variant="outline"
                size="icon"
                onClick={() => setCalendarMonth(new Date(year, month + 1, 1))}
              >
                <ChevronRight className="w-4 h-4" />
              </Button>
            </div>
          </div>
          <CardDescription>
            Vizualizează când vor fi generate articolele automat. <CheckCircle2 className="w-3 h-3 inline text-white" /> = articol publicat
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-7 gap-2 mb-2">
            {['Lun', 'Mar', 'Mie', 'Joi', 'Vin', 'Sâm', 'Dum'].map(d => (
              <div key={d} className="text-center text-sm font-medium text-muted-foreground py-2">
                {d}
              </div>
            ))}
          </div>
          <div className="grid grid-cols-7 gap-2">
            {days}
          </div>
          
          {/* Legend */}
          {siteSettings.filter(s => s.automation.mode === 'automatic' && s.automation.enabled && !s.automation.paused).length > 0 && (
            <div className="mt-4 pt-4 border-t border-border">
              <p className="text-xs text-muted-foreground mb-2">Legendă:</p>
              <div className="flex flex-wrap gap-2">
                {siteSettings
                  .filter(s => s.automation.mode === 'automatic' && s.automation.enabled && !s.automation.paused)
                  .map((item, idx) => (
                    <div key={item.site.id} className="flex items-center gap-1.5">
                      <div className={`w-3 h-3 rounded ${getColorForSite(item.site.id)}`} />
                      <span className="text-xs">{item.site.site_name || item.site.site_url}</span>
                    </div>
                  ))}
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="automation-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-heading font-bold flex items-center gap-3">
            <Bot className="w-8 h-8 text-primary" />
            Automatizare Articole
          </h1>
          <p className="text-muted-foreground mt-1">
            Configurează generarea automată de articole SEO pentru fiecare site
          </p>
        </div>
        <div className="flex items-center gap-2">
          {/* Notifications Toggle */}
          <Button 
            variant={notificationsEnabled ? "default" : "outline"}
            size="sm"
            onClick={toggleNotifications}
            className={notificationsEnabled ? "bg-primary" : ""}
            data-testid="notifications-toggle"
          >
            {notificationsEnabled ? (
              <>
                <Bell className="w-4 h-4 mr-2" />
                Notificări Active
              </>
            ) : (
              <>
                <BellOff className="w-4 h-4 mr-2" />
                Activează Notificări
              </>
            )}
          </Button>
          <Button 
            variant="outline" 
            onClick={() => { setShowHistory(true); fetchHistory(); }}
            data-testid="show-history-btn"
          >
            <History className="w-4 h-4 mr-2" />
            Istoric
          </Button>
        </div>
      </div>

      {/* Info Card */}
      <Card className="bg-primary/5 border-primary/20">
        <CardContent className="pt-6">
          <div className="flex gap-4">
            <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0">
              <Sparkles className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h3 className="font-semibold text-foreground mb-1">Cum funcționează automatizarea?</h3>
              <p className="text-sm text-muted-foreground">
                Setează modul <strong>Automat</strong> pentru a genera articole SEO la ora și frecvența aleasă. 
                Articolele sunt salvate ca Draft pentru a le putea revizui înainte de publicare. 
                Activează <strong>notificările</strong> pentru a fi alertat când un articol nou este generat.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabs for Settings and Publication Log */}
      <Tabs value={activeTab} onValueChange={(v) => { 
        setActiveTab(v); 
        if (v === 'log') fetchPublicationLog(); 
        // Refresh calendar data when switching tabs
        fetchPublishedArticles();
      }}>
        <TabsList className="bg-secondary">
          <TabsTrigger value="settings" className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
            <Settings2 className="w-4 h-4 mr-2" />
            Setări & Calendar
          </TabsTrigger>
          <TabsTrigger value="log" className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
            <List className="w-4 h-4 mr-2" />
            Jurnal Publicări
          </TabsTrigger>
        </TabsList>

        <TabsContent value="settings" className="space-y-6 mt-6">
          {/* Calendar */}
          {siteSettings.some(s => s.automation.mode === 'automatic' && s.automation.enabled && !s.automation.paused) && renderCalendar()}

      {/* Sites Table */}
      {siteSettings.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <Globe className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Niciun site conectat</h3>
            <p className="text-muted-foreground mb-4">
              Adaugă un site WordPress pentru a configura automatizarea
            </p>
            <Button onClick={() => window.location.href = '/wordpress'}>
              Adaugă Site WordPress
            </Button>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Settings2 className="w-5 h-5" />
              Setări Automatizare per Site
            </CardTitle>
            <CardDescription>
              Configurează modul de generare pentru fiecare site în parte
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Site</TableHead>
                    <TableHead>Mod</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Frecvență</TableHead>
                    <TableHead>Ora</TableHead>
                    <TableHead>Linkuri Produse</TableHead>
                    <TableHead>Articole Generate</TableHead>
                    <TableHead className="text-right">Acțiuni</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {siteSettings.map((item) => (
                    <TableRow key={item.site.id} data-testid={`site-row-${item.site.id}`}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <div className={`w-3 h-3 rounded-full ${getColorForSite(item.site.id)}`} />
                          <div>
                            <p className="font-medium">{item.site.site_name || item.site.site_url}</p>
                            <p className="text-xs text-muted-foreground">{item.site.niche || 'General'}</p>
                          </div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant={item.automation.mode === 'automatic' ? 'default' : 'secondary'}>
                          {item.automation.mode === 'automatic' ? 'Automat' : 'Manual'}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        {item.automation.enabled && item.automation.mode === 'automatic' ? (
                          item.automation.paused ? (
                            <div className="flex items-center gap-1 text-yellow-500">
                              <AlertCircle className="w-4 h-4" />
                              <span className="text-sm">Pauză</span>
                            </div>
                          ) : (
                            <div className="flex items-center gap-1 text-green-500">
                              <CheckCircle2 className="w-4 h-4" />
                              <span className="text-sm">Activ</span>
                            </div>
                          )
                        ) : (
                          <div className="flex items-center gap-1 text-muted-foreground">
                            <XCircle className="w-4 h-4" />
                            <span className="text-sm">Inactiv</span>
                          </div>
                        )}
                      </TableCell>
                      <TableCell>
                        <span className="text-sm">
                          {getFrequencyLabel(item.automation.frequency)}
                        </span>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <Clock className="w-4 h-4 text-muted-foreground" />
                          <span>{item.automation.generation_hour}:00</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        {item.automation.include_product_links ? (
                          <div className="flex items-center gap-1 text-primary">
                            <Link2 className="w-4 h-4" />
                            <span className="text-sm">Da ({item.automation.max_product_links})</span>
                          </div>
                        ) : (
                          <span className="text-muted-foreground text-sm">Nu</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-1">
                          <FileText className="w-4 h-4 text-muted-foreground" />
                          <span>{item.automation.articles_generated || 0}</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => generateNow(item.site.id, item.site.site_name)}
                            disabled={generating === item.site.id}
                            data-testid={`generate-now-${item.site.id}`}
                          >
                            {generating === item.site.id ? (
                              <Loader2 className="w-4 h-4 animate-spin" />
                            ) : (
                              <Play className="w-4 h-4" />
                            )}
                            <span className="ml-1 hidden sm:inline">Generează</span>
                          </Button>
                          <Button
                            size="sm"
                            onClick={() => openEditDialog(item)}
                            data-testid={`edit-settings-${item.site.id}`}
                          >
                            <Settings2 className="w-4 h-4" />
                            <span className="ml-1 hidden sm:inline">Setări</span>
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      )}
        </TabsContent>

        {/* Publication Log Tab */}
        <TabsContent value="log" className="mt-6">
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <List className="w-5 h-5 text-primary" />
                Jurnal Publicări
              </CardTitle>
              <CardDescription>
                Istoric complet cu data și ora exactă pentru fiecare articol publicat pe fiecare site
              </CardDescription>
            </CardHeader>
            <CardContent>
              {loadingLog ? (
                <div className="flex items-center justify-center py-12">
                  <Loader2 className="w-8 h-8 animate-spin text-primary" />
                </div>
              ) : publicationLog.length === 0 ? (
                <div className="text-center py-12">
                  <FileText className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">
                    Niciun articol publicat încă
                  </p>
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Site</TableHead>
                        <TableHead>Titlu Articol</TableHead>
                        <TableHead>Data Publicării</TableHead>
                        <TableHead>Ora</TableHead>
                        <TableHead>Tip</TableHead>
                        <TableHead>Cuvinte</TableHead>
                        <TableHead className="text-right">Acțiuni</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {publicationLog
                        .filter(article => !currentSite || currentSite.id === 'all' || article.site_id === currentSite.id)
                        .map((article) => {
                        const publishDate = new Date(article.published_at);
                        return (
                          <TableRow key={article.id} data-testid={`log-row-${article.id}`}>
                            <TableCell>
                              <div className="flex items-center gap-2">
                                <Globe className="w-4 h-4 text-primary" />
                                <div>
                                  <p className="font-medium text-sm">{article.site_name}</p>
                                  <p className="text-xs text-muted-foreground">{article.niche}</p>
                                </div>
                              </div>
                            </TableCell>
                            <TableCell>
                              <p className="font-medium text-sm truncate max-w-[200px]" title={article.title}>
                                {article.title}
                              </p>
                              {article.category && (
                                <Badge variant="outline" className="text-xs mt-1">
                                  {article.category}
                                </Badge>
                              )}
                            </TableCell>
                            <TableCell>
                              <span className="text-sm">
                                {publishDate.toLocaleDateString('ro-RO', {
                                  day: '2-digit',
                                  month: '2-digit',
                                  year: 'numeric'
                                })}
                              </span>
                            </TableCell>
                            <TableCell>
                              <div className="flex items-center gap-1">
                                <Clock className="w-3 h-3 text-muted-foreground" />
                                <span className="text-sm font-mono">
                                  {publishDate.toLocaleTimeString('ro-RO', {
                                    hour: '2-digit',
                                    minute: '2-digit'
                                  })}
                                </span>
                              </div>
                            </TableCell>
                            <TableCell>
                              {article.auto_generated ? (
                                <Badge className="bg-primary/10 text-primary border-primary/20">
                                  <Bot className="w-3 h-3 mr-1" />
                                  Auto
                                </Badge>
                              ) : (
                                <Badge variant="secondary">
                                  Manual
                                </Badge>
                              )}
                            </TableCell>
                            <TableCell>
                              <span className="text-sm text-muted-foreground">
                                {article.word_count?.toLocaleString() || 0}
                              </span>
                            </TableCell>
                            <TableCell className="text-right">
                              {article.wp_post_url && (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => window.open(article.wp_post_url, '_blank')}
                                >
                                  <ExternalLink className="w-4 h-4" />
                                </Button>
                              )}
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Edit Settings Dialog */}
      <Dialog open={!!editingSite} onOpenChange={() => { setEditingSite(null); setEditSettings(null); }}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Settings2 className="w-5 h-5 text-primary" />
              Setări Automatizare
            </DialogTitle>
            <DialogDescription>
              {editingSite?.site_name || editingSite?.site_url}
            </DialogDescription>
          </DialogHeader>

          <div className="flex-1 overflow-y-auto pr-2">
          {editSettings && (
            <div className="space-y-6 py-4">
              {/* Mode Selection */}
              <div className="space-y-3">
                <Label className="text-base font-medium">Mod Generare</Label>
                <div className="grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    onClick={() => setEditSettings({ ...editSettings, mode: 'manual', enabled: false })}
                    className={`p-4 rounded-lg border-2 transition-all ${
                      editSettings.mode === 'manual' 
                        ? 'border-primary bg-primary/10' 
                        : 'border-border hover:border-primary/50'
                    }`}
                    data-testid="mode-manual"
                  >
                    <div className="text-center">
                      <div className="w-10 h-10 rounded-full bg-secondary mx-auto mb-2 flex items-center justify-center">
                        <Play className="w-5 h-5" />
                      </div>
                      <p className="font-medium">Manual</p>
                      <p className="text-xs text-muted-foreground mt-1">
                        Generezi când dorești
                      </p>
                    </div>
                  </button>
                  <button
                    type="button"
                    onClick={() => setEditSettings({ ...editSettings, mode: 'automatic' })}
                    className={`p-4 rounded-lg border-2 transition-all ${
                      editSettings.mode === 'automatic' 
                        ? 'border-primary bg-primary/10' 
                        : 'border-border hover:border-primary/50'
                    }`}
                    data-testid="mode-automatic"
                  >
                    <div className="text-center">
                      <div className="w-10 h-10 rounded-full bg-primary/20 mx-auto mb-2 flex items-center justify-center">
                        <Bot className="w-5 h-5 text-primary" />
                      </div>
                      <p className="font-medium">Automat</p>
                      <p className="text-xs text-muted-foreground mt-1">
                        Generare programată
                      </p>
                    </div>
                  </button>
                </div>
              </div>

              {/* Automatic Mode Settings */}
              {editSettings.mode === 'automatic' && (
                <>
                  {/* Enable Toggle */}
                  <div className="flex items-center justify-between p-4 rounded-lg bg-secondary/50">
                    <div>
                      <Label className="font-medium">Activează Automatizarea</Label>
                      <p className="text-sm text-muted-foreground">
                        Pornește generarea automată
                      </p>
                    </div>
                    <Switch
                      checked={editSettings.enabled}
                      onCheckedChange={(checked) => setEditSettings({ ...editSettings, enabled: checked })}
                      data-testid="automation-toggle"
                    />
                  </div>

                  {/* Pause Toggle */}
                  {editSettings.enabled && (
                    <div className="flex items-center justify-between p-4 rounded-lg bg-yellow-500/10 border border-yellow-500/30">
                      <div>
                        <Label className="font-medium text-yellow-500">Pauză Temporară</Label>
                        <p className="text-sm text-muted-foreground">
                          Oprește temporar fără a dezactiva complet
                        </p>
                      </div>
                      <Switch
                        checked={editSettings.paused}
                        onCheckedChange={(checked) => setEditSettings({ ...editSettings, paused: checked })}
                        data-testid="pause-toggle"
                      />
                    </div>
                  )}

                  {/* Frequency */}
                  <div className="space-y-2">
                    <Label>Frecvență Generare</Label>
                    <Select 
                      value={editSettings.frequency} 
                      onValueChange={(value) => setEditSettings({ ...editSettings, frequency: value })}
                    >
                      <SelectTrigger data-testid="frequency-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="daily">Zilnic</SelectItem>
                        <SelectItem value="every_2_days">La fiecare 2 zile</SelectItem>
                        <SelectItem value="every_3_days">La fiecare 3 zile</SelectItem>
                        <SelectItem value="weekly">Săptămânal</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  {/* Hour */}
                  <div className="space-y-2">
                    <Label>Ora Generării</Label>
                    <Select 
                      value={String(editSettings.generation_hour)} 
                      onValueChange={(value) => setEditSettings({ ...editSettings, generation_hour: parseInt(value) })}
                    >
                      <SelectTrigger data-testid="hour-select">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {Array.from({ length: 24 }, (_, i) => (
                          <SelectItem key={i} value={String(i)}>
                            {String(i).padStart(2, '0')}:00
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </>
              )}

              {/* Article Length */}
              <div className="space-y-2">
                <Label>Lungime Articol</Label>
                <Select 
                  value={editSettings.article_length} 
                  onValueChange={(value) => setEditSettings({ ...editSettings, article_length: value })}
                >
                  <SelectTrigger data-testid="length-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="short">Scurt (~500 cuvinte)</SelectItem>
                    <SelectItem value="medium">Mediu (~1000 cuvinte)</SelectItem>
                    <SelectItem value="long">Lung (~2000 cuvinte)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Publish Mode */}
              <div className="space-y-2">
                <Label>Mod Publicare</Label>
                <Select 
                  value={editSettings.publish_mode} 
                  onValueChange={(value) => setEditSettings({ ...editSettings, publish_mode: value })}
                >
                  <SelectTrigger data-testid="publish-mode-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="draft">Salvează ca Draft (revizuiesc manual)</SelectItem>
                    <SelectItem value="publish">Publică automat pe WordPress</SelectItem>
                  </SelectContent>
                </Select>
                <p className="text-xs text-muted-foreground">
                  {editSettings.publish_mode === 'draft' 
                    ? 'Articolele vor fi salvate ca ciornă pentru revizuire' 
                    : 'Articolele vor fi publicate automat pe site'}
                </p>
              </div>

              {/* Email Notification */}
              <div className="flex items-center justify-between p-4 rounded-lg bg-secondary/50">
                <div>
                  <Label className="font-medium">Notificare Email</Label>
                  <p className="text-sm text-muted-foreground">
                    Primește email când se generează articol
                  </p>
                </div>
                <Switch
                  checked={editSettings.email_notification}
                  onCheckedChange={(checked) => setEditSettings({ ...editSettings, email_notification: checked })}
                  data-testid="email-notification-toggle"
                />
              </div>

              {/* Product Links */}
              <div className="space-y-4 p-4 rounded-lg border border-border">
                <div className="flex items-center justify-between">
                  <div>
                    <Label className="font-medium">Linkuri Produse</Label>
                    <p className="text-sm text-muted-foreground">
                      Include linkuri către produse din site
                    </p>
                  </div>
                  <Switch
                    checked={editSettings.include_product_links}
                    onCheckedChange={(checked) => setEditSettings({ ...editSettings, include_product_links: checked })}
                    data-testid="product-links-toggle"
                  />
                </div>

                {editSettings.include_product_links && (
                  <div className="space-y-4 pt-2">
                    <div className="space-y-2">
                      <Label>Cuvinte cheie produse (opțional)</Label>
                      <Input
                        placeholder="ex: echipament, accesorii, produse premium"
                        value={editSettings.product_links_source}
                        onChange={(e) => setEditSettings({ ...editSettings, product_links_source: e.target.value })}
                        data-testid="product-keywords-input"
                      />
                      <p className="text-xs text-muted-foreground">
                        AI-ul va căuta produse relevante bazate pe aceste cuvinte cheie
                      </p>
                    </div>
                    <div className="space-y-2">
                      <Label>Număr maxim de linkuri</Label>
                      <Select 
                        value={String(editSettings.max_product_links)} 
                        onValueChange={(value) => setEditSettings({ ...editSettings, max_product_links: parseInt(value) })}
                      >
                        <SelectTrigger data-testid="max-links-select">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="1">1 link</SelectItem>
                          <SelectItem value="2">2 linkuri</SelectItem>
                          <SelectItem value="3">3 linkuri</SelectItem>
                          <SelectItem value="5">5 linkuri</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
          </div>

          <DialogFooter className="pt-4 border-t">
            <Button variant="outline" onClick={() => { setEditingSite(null); setEditSettings(null); }}>
              Anulează
            </Button>
            <Button onClick={saveSettings} disabled={saving} data-testid="save-settings-btn">
              {saving ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Se salvează...
                </>
              ) : (
                'Salvează Setările'
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* History Dialog */}
      <Dialog open={showHistory} onOpenChange={setShowHistory}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <History className="w-5 h-5 text-primary" />
              Istoric Articole Generate Automat
            </DialogTitle>
          </DialogHeader>

          <div className="flex-1 overflow-y-auto">
            {loadingHistory ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="w-8 h-8 animate-spin text-primary" />
              </div>
            ) : history.length === 0 ? (
              <div className="text-center py-12">
                <AlertCircle className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
                <p className="text-muted-foreground">
                  Niciun articol generat automat încă
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {history.map((article) => (
                  <div 
                    key={article.id} 
                    className="p-4 rounded-lg border border-border hover:border-primary/50 transition-colors"
                  >
                    <div className="flex justify-between items-start gap-4">
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium truncate">{article.title}</h4>
                        <div className="flex flex-wrap gap-2 mt-2 text-sm text-muted-foreground">
                          <span className="flex items-center gap-1">
                            <Calendar className="w-3 h-3" />
                            {formatDate(article.created_at)}
                          </span>
                          <span className="flex items-center gap-1">
                            <FileText className="w-3 h-3" />
                            {article.word_count} cuvinte
                          </span>
                          {article.has_product_links && (
                            <span className="flex items-center gap-1 text-primary">
                              <Link2 className="w-3 h-3" />
                              Cu linkuri produse
                            </span>
                          )}
                        </div>
                      </div>
                      <Badge variant={article.status === 'published' ? 'default' : 'secondary'}>
                        {article.status === 'published' ? 'Publicat' : 'Draft'}
                      </Badge>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
