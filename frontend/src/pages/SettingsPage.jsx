import { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '@/contexts/AuthContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { toast } from 'sonner';
import { 
  Settings, 
  Palette,
  Bell,
  Building,
  Save,
  Loader2,
  FileText,
  Send
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function SettingsPage() {
  const [settings, setSettings] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [sendingReport, setSendingReport] = useState(false);
  const { getAuthHeaders, user } = useAuth();

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await axios.get(`${API}/settings`, { headers: getAuthHeaders() });
      setSettings(response.data);
    } catch (error) {
      console.error('Failed to fetch settings:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const response = await axios.patch(`${API}/settings`, settings, { 
        headers: getAuthHeaders() 
      });
      setSettings(response.data);
      toast.success('Setări salvate cu succes!');
    } catch (error) {
      toast.error('Eroare la salvare');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-8 bg-secondary rounded w-48" />
        <div className="h-64 bg-secondary rounded-lg" />
      </div>
    );
  }

  return (
    <div className="max-w-3xl mx-auto space-y-8" data-testid="settings-page">
      {/* Header */}
      <div>
        <h1 className="font-heading text-3xl font-bold">Setări</h1>
        <p className="text-muted-foreground mt-1">
          Configurează platforma și opțiunile white-label
        </p>
      </div>

      {/* Profile */}
      <Card className="bg-card border-border">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10">
              <Settings className="w-5 h-5 text-primary" />
            </div>
            <div>
              <CardTitle className="font-heading text-lg">Profil</CardTitle>
              <CardDescription>Informații despre contul tău</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center gap-4 p-4 rounded-lg bg-secondary">
              <div className="w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center">
                <span className="text-xl font-bold text-primary">
                  {user?.name?.charAt(0).toUpperCase() || 'U'}
                </span>
              </div>
              <div>
                <p className="font-medium">{user?.name}</p>
                <p className="text-sm text-muted-foreground">{user?.email}</p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* White Label Settings */}
      <Card className="bg-card border-border">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-chart-3/10">
              <Building className="w-5 h-5 text-chart-3" />
            </div>
            <div>
              <CardTitle className="font-heading text-lg">White Label</CardTitle>
              <CardDescription>
                Personalizează platforma cu brandul tău (100% fără mențiuni terțe)
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="company_name">Numele Companiei</Label>
            <Input
              id="company_name"
              value={settings?.company_name || ''}
              onChange={(e) => setSettings({...settings, company_name: e.target.value})}
              className="bg-secondary border-border"
              placeholder="My SEO Agency"
              data-testid="company-name-input"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="logo_url">URL Logo</Label>
            <Input
              id="logo_url"
              value={settings?.logo_url || ''}
              onChange={(e) => setSettings({...settings, logo_url: e.target.value})}
              className="bg-secondary border-border"
              placeholder="https://example.com/logo.png"
              data-testid="logo-url-input"
            />
            <p className="text-xs text-muted-foreground">
              URL către imaginea logo-ului companiei tale
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="primary_color" className="flex items-center gap-2">
              <Palette className="w-4 h-4" />
              Culoare Principală
            </Label>
            <div className="flex gap-3">
              <Input
                id="primary_color"
                type="color"
                value={settings?.primary_color || '#00E676'}
                onChange={(e) => setSettings({...settings, primary_color: e.target.value})}
                className="w-16 h-10 p-1 bg-secondary border-border cursor-pointer"
                data-testid="primary-color-input"
              />
              <Input
                value={settings?.primary_color || '#00E676'}
                onChange={(e) => setSettings({...settings, primary_color: e.target.value})}
                className="flex-1 bg-secondary border-border font-mono"
                placeholder="#00E676"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Notifications */}
      <Card className="bg-card border-border">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-chart-4/10">
              <Bell className="w-5 h-5 text-chart-4" />
            </div>
            <div>
              <CardTitle className="font-heading text-lg">Notificări</CardTitle>
              <CardDescription>Configurează alertele pe email</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between p-4 rounded-lg bg-secondary">
            <div>
              <p className="font-medium">Notificări Email</p>
              <p className="text-sm text-muted-foreground">
                Primește alerte despre articole publicate și statistici
              </p>
            </div>
            <Switch
              checked={settings?.email_notifications ?? true}
              onCheckedChange={(checked) => setSettings({...settings, email_notifications: checked})}
              data-testid="email-notifications-switch"
            />
          </div>
        </CardContent>
      </Card>

      {/* Outreach Contact Info */}
      <Card className="bg-card border-border">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-blue-500/10">
              <Send className="w-5 h-5 text-blue-500" />
            </div>
            <div>
              <CardTitle className="font-heading text-lg">Date Contact Outreach</CardTitle>
              <CardDescription>
                Aceste date vor fi folosite în email-urile de outreach generate automat
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="outreach_position">Poziție / Funcție</Label>
            <Input
              id="outreach_position"
              value={settings?.outreach_position || ''}
              onChange={(e) => setSettings({...settings, outreach_position: e.target.value})}
              className="bg-secondary border-border"
              placeholder="Administrator, CEO, Marketing Manager..."
              data-testid="outreach-position-input"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="outreach_phone">Telefon</Label>
            <Input
              id="outreach_phone"
              value={settings?.outreach_phone || ''}
              onChange={(e) => setSettings({...settings, outreach_phone: e.target.value})}
              className="bg-secondary border-border"
              placeholder="0721 234 567"
              data-testid="outreach-phone-input"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="outreach_email">Email Contact (opțional)</Label>
            <Input
              id="outreach_email"
              type="email"
              value={settings?.outreach_email || ''}
              onChange={(e) => setSettings({...settings, outreach_email: e.target.value})}
              className="bg-secondary border-border"
              placeholder="Lasă gol pentru a folosi emailul contului"
              data-testid="outreach-email-input"
            />
            <p className="text-xs text-muted-foreground">
              Dacă lași gol, se va folosi emailul contului: {user?.email}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Monthly Report */}
      <Card className="bg-card border-border">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10">
              <FileText className="w-5 h-5 text-primary" />
            </div>
            <div>
              <CardTitle className="font-heading text-lg">Raport SEO Lunar</CardTitle>
              <CardDescription>
                Raportul se trimite automat pe 1 a fiecărei luni la ora 9:00
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="p-4 rounded-lg bg-secondary/50">
            <p className="text-sm text-muted-foreground mb-3">
              Raportul include:
            </p>
            <ul className="text-sm space-y-1 text-muted-foreground">
              <li>• Articole generate în ultima lună</li>
              <li>• Articole automate vs manuale</li>
              <li>• Articole publicate pe WordPress</li>
              <li>• Statistici outreach (trimise / răspunsuri)</li>
              <li>• Performanță per site</li>
            </ul>
          </div>
          
          <Button
            onClick={async () => {
              setSendingReport(true);
              try {
                const response = await axios.post(`${API}/reports/send-monthly`, {}, {
                  headers: getAuthHeaders()
                });
                toast.success(`Raport trimis la ${response.data.sent_to}`);
              } catch (error) {
                toast.error(error.response?.data?.detail || 'Eroare la trimiterea raportului');
              } finally {
                setSendingReport(false);
              }
            }}
            disabled={sendingReport}
            variant="outline"
            className="w-full border-primary/50"
            data-testid="send-report-button"
          >
            {sendingReport ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Se trimite...
              </>
            ) : (
              <>
                <Send className="w-4 h-4 mr-2" />
                Trimite Raport Acum
              </>
            )}
          </Button>
        </CardContent>
      </Card>

      {/* Save Button */}
      <Button
        onClick={handleSave}
        disabled={saving}
        className="w-full bg-primary text-primary-foreground hover:bg-primary/90 h-12"
        data-testid="save-settings-button"
      >
        {saving ? (
          <>
            <Loader2 className="w-4 h-4 mr-2 animate-spin" />
            Se salvează...
          </>
        ) : (
          <>
            <Save className="w-4 h-4 mr-2" />
            Salvează Setările
          </>
        )}
      </Button>
    </div>
  );
}
