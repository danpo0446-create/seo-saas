import { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '@/contexts/AuthContext';
import { useSite } from '@/contexts/SiteContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';
import { 
  Search, 
  TrendingUp, 
  TrendingDown, 
  Minus,
  Trash2,
  Loader2,
  Sparkles,
  RefreshCw,
  Globe
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const trendIcons = {
  up: TrendingUp,
  down: TrendingDown,
  stable: Minus,
};

const trendColors = {
  up: 'text-green-500',
  down: 'text-red-500',
  stable: 'text-yellow-500',
};

const sourceLabels = {
  'site_config': 'Site WP',
  'ai_generated': 'AI Gen',
  'daily_auto': 'Auto Zilnic',
  'bulk_sync': 'Sincronizat',
};

const sourceColors = {
  'site_config': 'bg-blue-500/10 text-blue-400 border-blue-500/20',
  'ai_generated': 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  'daily_auto': 'bg-green-500/10 text-green-400 border-green-500/20',
  'bulk_sync': 'bg-orange-500/10 text-orange-400 border-orange-500/20',
};

export default function KeywordsPage() {
  const [keywords, setKeywords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [researching, setResearching] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [niche, setNiche] = useState('');
  const [seedKeywords, setSeedKeywords] = useState('');
  const { getAuthHeaders } = useAuth();
  const { currentSiteId } = useSite();

  useEffect(() => {
    fetchKeywords();
  }, [currentSiteId]);

  const fetchKeywords = async () => {
    try {
      const params = currentSiteId ? { site_id: currentSiteId } : {};
      const response = await axios.get(`${API}/keywords`, { headers: getAuthHeaders(), params });
      setKeywords(response.data);
    } catch (error) {
      console.error('Failed to fetch keywords:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleResearch = async (e) => {
    e.preventDefault();
    if (!niche.trim()) {
      toast.error('Introdu o nișă pentru cercetare');
      return;
    }

    setResearching(true);
    try {
      const seeds = seedKeywords.split(',').map(k => k.trim()).filter(k => k);
      await axios.post(`${API}/keywords/research`, {
        niche,
        seed_keywords: seeds,
        site_id: currentSiteId
      }, { headers: getAuthHeaders() });
      
      toast.success('Cercetare completă! Cuvinte-cheie noi adăugate.');
      fetchKeywords();
      setNiche('');
      setSeedKeywords('');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Eroare la cercetare');
    } finally {
      setResearching(false);
    }
  };

  const handleDelete = async (id) => {
    try {
      await axios.delete(`${API}/keywords/${id}`, { headers: getAuthHeaders() });
      toast.success('Cuvânt-cheie șters');
      fetchKeywords();
    } catch (error) {
      toast.error('Eroare la ștergere');
    }
  };

  const handleSyncFromSites = async () => {
    setSyncing(true);
    try {
      const response = await axios.post(`${API}/keywords/sync-all-from-sites`, {}, { headers: getAuthHeaders() });
      toast.success(`Sincronizat ${response.data.synced_count} cuvinte-cheie din ${response.data.sites_processed} site-uri`);
      fetchKeywords();
    } catch (error) {
      toast.error('Eroare la sincronizare');
    } finally {
      setSyncing(false);
    }
  };

  const getDifficultyColor = (difficulty) => {
    if (difficulty < 30) return 'bg-green-500/10 text-green-500 border-green-500/20';
    if (difficulty < 60) return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20';
    return 'bg-red-500/10 text-red-500 border-red-500/20';
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
    <div className="space-y-8" data-testid="keywords-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-heading text-3xl font-bold">Cercetare Cuvinte-cheie</h1>
          <p className="text-muted-foreground mt-1">
            Descoperă oportunități SEO cu ajutorul AI
          </p>
        </div>
        <Button
          variant="outline"
          onClick={handleSyncFromSites}
          disabled={syncing}
          className="border-primary/30 hover:bg-primary/10"
          data-testid="sync-keywords-button"
        >
          {syncing ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Se sincronizează...
            </>
          ) : (
            <>
              <RefreshCw className="w-4 h-4 mr-2" />
              Sincronizează din Site-uri
            </>
          )}
        </Button>
      </div>

      {/* Research Form */}
      <Card className="bg-card border-border">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10">
              <Search className="w-5 h-5 text-primary" />
            </div>
            <div>
              <CardTitle className="font-heading text-lg">Cercetare Nouă</CardTitle>
              <CardDescription>Generează sugestii de cuvinte-cheie bazate pe nișă</CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleResearch} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="niche">Nișă / Industrie *</Label>
                <Input
                  id="niche"
                  placeholder="Ex: Marketing Digital"
                  value={niche}
                  onChange={(e) => setNiche(e.target.value)}
                  className="bg-secondary border-border"
                  required
                  data-testid="keyword-niche-input"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="seeds">Cuvinte-cheie de bază (opțional)</Label>
                <Input
                  id="seeds"
                  placeholder="Ex: SEO, content, backlinks"
                  value={seedKeywords}
                  onChange={(e) => setSeedKeywords(e.target.value)}
                  className="bg-secondary border-border"
                  data-testid="keyword-seeds-input"
                />
              </div>
            </div>
            <Button 
              type="submit" 
              className="bg-primary text-primary-foreground hover:bg-primary/90"
              disabled={researching}
              data-testid="research-keywords-button"
            >
              {researching ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Se cercetează...
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4 mr-2" />
                  Cercetează
                </>
              )}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Keywords List */}
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="font-heading text-lg">
            Cuvinte-cheie salvate ({keywords.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {keywords.length === 0 ? (
            <div className="text-center py-12">
              <Search className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground">
                Niciun cuvânt-cheie încă. Începe o cercetare!
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Cuvânt-cheie</th>
                    <th className="text-center py-3 px-4 text-sm font-medium text-muted-foreground">Sursă</th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">Volum</th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">Dificultate</th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">CPC</th>
                    <th className="text-center py-3 px-4 text-sm font-medium text-muted-foreground">Trend</th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">Acțiuni</th>
                  </tr>
                </thead>
                <tbody>
                  {keywords.map((kw) => {
                    const TrendIcon = trendIcons[kw.trend] || Minus;
                    const sourceLabel = sourceLabels[kw.source] || 'Cercetare';
                    const sourceColor = sourceColors[kw.source] || 'bg-gray-500/10 text-gray-400 border-gray-500/20';
                    return (
                      <tr 
                        key={kw.id} 
                        className="border-b border-border/50 hover:bg-secondary/50 transition-colors"
                      >
                        <td className="py-3 px-4 font-medium">{kw.keyword}</td>
                        <td className="py-3 px-4 text-center">
                          <Badge className={`text-xs ${sourceColor}`}>
                            {sourceLabel}
                          </Badge>
                        </td>
                        <td className="py-3 px-4 text-right font-mono text-sm">
                          {kw.volume.toLocaleString()}
                        </td>
                        <td className="py-3 px-4 text-right">
                          <Badge className={getDifficultyColor(kw.difficulty)}>
                            {kw.difficulty}
                          </Badge>
                        </td>
                        <td className="py-3 px-4 text-right font-mono text-sm">
                          ${kw.cpc.toFixed(2)}
                        </td>
                        <td className="py-3 px-4 text-center">
                          <TrendIcon className={`w-4 h-4 mx-auto ${trendColors[kw.trend]}`} />
                        </td>
                        <td className="py-3 px-4 text-right">
                          <Button
                            variant="ghost"
                            size="icon"
                            onClick={() => handleDelete(kw.id)}
                            className="text-muted-foreground hover:text-destructive"
                            data-testid={`delete-keyword-${kw.id}`}
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
