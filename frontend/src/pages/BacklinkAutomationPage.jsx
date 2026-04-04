import { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { toast } from 'sonner';
import {
  Clock,
  Mail,
  TrendingUp,
  RefreshCw,
  CheckCircle2,
  AlertCircle,
  Globe,
  Send,
  Calendar,
  Target,
  Loader2
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function BacklinkAutomationPage() {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [triggering, setTriggering] = useState(false);
  const { getAuthHeaders } = useAuth();

  const fetchStatus = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/backlinks/automation-status`, { headers: getAuthHeaders() });
      setStatus(response.data);
    } catch (error) {
      toast.error('Eroare la încărcarea statusului');
    } finally {
      setLoading(false);
    }
  };

  const triggerAutomation = async () => {
    setTriggering(true);
    try {
      const response = await axios.post(`${API}/backlinks/trigger-outreach`, {}, { headers: getAuthHeaders() });
      toast.success(response.data.message || 'Automatizare declanșată!');
      fetchStatus();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Eroare la declanșare');
    } finally {
      setTriggering(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    // Auto-refresh every 5 minutes
    const interval = setInterval(fetchStatus, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !status) {
    return (
      <div className="flex items-center justify-center min-h-[400px]" data-testid="loading-spinner">
        <Loader2 className="w-8 h-8 animate-spin text-[#00E676]" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="backlink-automation-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Automatizare Backlinks</h1>
          <p className="text-[#71717A]">Monitorizare căutare oportunități și trimitere emailuri</p>
        </div>
        <div className="flex gap-2">
          <Button 
            onClick={triggerAutomation}
            className="bg-[#00E676] text-black hover:bg-[#00E676]/90"
            disabled={triggering}
            data-testid="trigger-automation-btn"
          >
            {triggering ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            ) : (
              <Send className="w-4 h-4 mr-2" />
            )}
            Declanșează Acum
          </Button>
          <Button 
            onClick={fetchStatus} 
            variant="outline" 
            className="border-[#262626] hover:bg-[#171717]"
            disabled={loading}
            data-testid="refresh-btn"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Reîmprospătează
          </Button>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-[#0A0A0A] border-[#262626]">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-[#00E676]/10 rounded-lg">
                <Clock className="w-5 h-5 text-[#00E676]" />
              </div>
              <div>
                <p className="text-sm text-[#71717A]">Următoarea rulare</p>
                <p className="text-xl font-bold text-white">12:30</p>
                <p className="text-xs text-[#71717A]">Ora României</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#0A0A0A] border-[#262626]">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-500/10 rounded-lg">
                <Mail className="w-5 h-5 text-blue-500" />
              </div>
              <div>
                <p className="text-sm text-[#71717A]">Emailuri azi</p>
                <p className="text-xl font-bold text-white">{status?.total_emails_today || 0}</p>
                <p className="text-xs text-[#71717A]">din max {(status?.sites?.length || 0) * 15}</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#0A0A0A] border-[#262626]">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-purple-500/10 rounded-lg">
                <TrendingUp className="w-5 h-5 text-purple-500" />
              </div>
              <div>
                <p className="text-sm text-[#71717A]">Ultimele 7 zile</p>
                <p className="text-xl font-bold text-white">{status?.total_emails_7_days || 0}</p>
                <p className="text-xs text-[#71717A]">emailuri trimise</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-[#0A0A0A] border-[#262626]">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-orange-500/10 rounded-lg">
                <Calendar className="w-5 h-5 text-orange-500" />
              </div>
              <div>
                <p className="text-sm text-[#71717A]">Ultima trimitere</p>
                <p className="text-sm font-medium text-white">
                  {status?.last_outreach
                    ? new Date(status.last_outreach).toLocaleString('ro-RO')
                    : 'Niciuna'
                  }
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Per-Site Status */}
      <Card className="bg-[#0A0A0A] border-[#262626]">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Globe className="w-5 h-5 text-[#00E676]" />
            Status per Site
          </CardTitle>
          <CardDescription className="text-[#71717A]">
            Fiecare site primește max 15 emailuri/zi către oportunități FREE
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {status?.sites?.map((site) => (
            <div 
              key={site.site_id} 
              className="p-4 bg-[#171717] rounded-lg border border-[#262626]"
              data-testid={`site-status-${site.site_id}`}
            >
              <div className="flex items-center justify-between mb-3">
                <div>
                  <h3 className="font-medium text-white">{site.site_name}</h3>
                  <p className="text-sm text-[#71717A]">{site.niche}</p>
                </div>
                <Badge 
                  variant={site.remaining_today > 0 ? "default" : "secondary"}
                  className={site.remaining_today > 0 ? "bg-green-500" : ""}
                >
                  {site.remaining_today > 0
                    ? `${site.remaining_today} emailuri rămase azi`
                    : 'Limită atinsă azi'
                  }
                </Badge>
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4 text-sm">
                <div>
                  <p className="text-[#71717A]">Trimise azi</p>
                  <p className="text-white font-medium">{site.emails_sent_today}</p>
                </div>
                <div>
                  <p className="text-[#71717A]">Trimise ieri</p>
                  <p className="text-white font-medium">{site.emails_sent_yesterday}</p>
                </div>
                <div>
                  <p className="text-[#71717A]">Ultimele 7 zile</p>
                  <p className="text-white font-medium">{site.emails_sent_7_days}</p>
                </div>
                <div>
                  <p className="text-[#71717A]">Oportunități FREE</p>
                  <p className="text-white font-medium">{site.total_free_opportunities}</p>
                </div>
                <div>
                  <p className="text-[#71717A]">Răspunsuri</p>
                  <p className="text-white font-medium">{site.responses_received}</p>
                </div>
              </div>
              
              {site.new_opportunities_today > 0 && (
                <div className="mt-3 flex items-center gap-2 text-green-500 text-sm">
                  <CheckCircle2 className="w-4 h-4" />
                  {site.new_opportunities_today} oportunități noi găsite azi
                </div>
              )}
            </div>
          ))}

          {(!status?.sites || status.sites.length === 0) && (
            <div className="text-center py-8">
              <AlertCircle className="w-12 h-12 text-[#71717A] mx-auto mb-3" />
              <h3 className="text-white font-medium">Nu ai site-uri configurate</h3>
              <p className="text-[#71717A] text-sm">Adaugă site-uri WordPress pentru a activa automatizarea</p>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Info Card */}
      <Card className="bg-[#0A0A0A] border-[#262626]">
        <CardHeader>
          <CardTitle className="text-white">Cum funcționează</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-start gap-3 p-3 bg-[#171717] rounded-lg">
              <div className="p-2 bg-blue-500/10 rounded-lg shrink-0">
                <Target className="w-4 h-4 text-blue-500" />
              </div>
              <div>
                <h4 className="text-white font-medium">06:00 - Căutare oportunități noi</h4>
                <p className="text-[#71717A] text-sm">Se caută oportunități FREE noi pentru fiecare site</p>
              </div>
            </div>
            
            <div className="flex items-start gap-3 p-3 bg-[#171717] rounded-lg">
              <div className="p-2 bg-green-500/10 rounded-lg shrink-0">
                <Send className="w-4 h-4 text-green-500" />
              </div>
              <div>
                <h4 className="text-white font-medium">12:30 - Trimitere emailuri automate</h4>
                <p className="text-[#71717A] text-sm">Max 15 emailuri/zi/site către oportunități FREE necontactate</p>
              </div>
            </div>
            
            <div className="flex items-start gap-3 p-3 bg-[#171717] rounded-lg">
              <div className="p-2 bg-purple-500/10 rounded-lg shrink-0">
                <Globe className="w-4 h-4 text-purple-500" />
              </div>
              <div>
                <h4 className="text-white font-medium">Articole diferite</h4>
                <p className="text-[#71717A] text-sm">Fiecare email promovează un articol diferit din site</p>
              </div>
            </div>
            
            <div className="flex items-start gap-3 p-3 bg-[#171717] rounded-lg">
              <div className="p-2 bg-orange-500/10 rounded-lg shrink-0">
                <Mail className="w-4 h-4 text-orange-500" />
              </div>
              <div>
                <h4 className="text-white font-medium">Emailuri personalizate</h4>
                <p className="text-[#71717A] text-sm">AI generează emailuri personalizate pentru fiecare destinatar</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
