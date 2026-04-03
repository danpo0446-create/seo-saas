import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
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
  Globe, 
  Link as LinkIcon,
  CheckCircle2,
  Loader2,
  ExternalLink,
  Trash2,
  Plus,
  Pencil,
  Save,
  X,
  Sparkles,
  Tag,
  RefreshCw,
  Facebook,
  Linkedin,
  Share2
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function WordPressPage() {
  const [searchParams] = useSearchParams();
  const [sites, setSites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [editingSite, setEditingSite] = useState(null);
  const [editForm, setEditForm] = useState({});
  const [saving, setSaving] = useState(false);
  const [keywordsModal, setKeywordsModal] = useState(null);
  const [siteKeywords, setSiteKeywords] = useState([]);
  const [generatingKeywords, setGeneratingKeywords] = useState(false);
  const [newKeyword, setNewKeyword] = useState('');
  const [socialModal, setSocialModal] = useState(null);
  const [socialStatus, setSocialStatus] = useState({});
  const [selectedFacebookPage, setSelectedFacebookPage] = useState('');
  const [savingFacebookPage, setSavingFacebookPage] = useState(false);
  const [manualPageId, setManualPageId] = useState('');
  const [manualPageToken, setManualPageToken] = useState('');
  const [formData, setFormData] = useState({
    site_url: '',
    site_name: '',
    username: '',
    app_password: '',
    niche: ''
  });
  const { getAuthHeaders } = useAuth();
  const { refreshSites } = useSite();

  useEffect(() => {
    fetchSites();
    
    // Check for OAuth callback messages
    const success = searchParams.get('success');
    const error = searchParams.get('error');
    
    if (success === 'facebook_connected') {
      toast.success('Facebook conectat cu succes!');
    } else if (success === 'linkedin_connected') {
      toast.success('LinkedIn conectat cu succes!');
    } else if (error) {
      // User-friendly error messages
      const errorMessages = {
        'no_facebook_pages': 'Nu s-au găsit pagini Facebook. Aplicația ta Facebook trebuie să fie de tip Business cu use case "Manage and access Page content".',
        'facebook_token_error': 'Eroare la obținerea token-ului Facebook. Verifică App ID și App Secret.',
        'facebook_credentials_missing': 'Lipsesc credențialele Facebook. Configurează App ID și App Secret în Chei API.',
        'missing_code_or_state': 'Eroare de autentificare Facebook. Încearcă din nou.',
      };
      const message = errorMessages[error] || `Eroare la conectare: ${error.replace(/_/g, ' ')}`;
      toast.error(message, { duration: 8000 });
    }
  }, [searchParams]);

  const fetchSites = async () => {
    try {
      const response = await axios.get(`${API}/wordpress/sites`, { headers: getAuthHeaders() });
      setSites(response.data);
    } catch (error) {
      console.error('Failed to fetch WordPress sites:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = async (e) => {
    e.preventDefault();
    
    if (!formData.site_url || !formData.username || !formData.app_password) {
      toast.error('Completează toate câmpurile obligatorii');
      return;
    }

    setConnecting(true);
    try {
      await axios.post(`${API}/wordpress/connect`, formData, { 
        headers: getAuthHeaders() 
      });
      toast.success('Site WordPress adăugat cu succes!');
      setFormData({ site_url: '', site_name: '', username: '', app_password: '', niche: '' });
      setShowForm(false);
      fetchSites();
      refreshSites(); // Update global site list
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Eroare la conectare');
    } finally {
      setConnecting(false);
    }
  };

  const handleDelete = async (siteId, siteName) => {
    if (!window.confirm(`Ești sigur că vrei să ștergi site-ul "${siteName}"?`)) return;
    
    try {
      await axios.delete(`${API}/wordpress/site/${siteId}`, { headers: getAuthHeaders() });
      toast.success('Site șters');
      fetchSites();
      refreshSites(); // Update global site list
    } catch (error) {
      toast.error('Eroare la ștergere');
    }
  };

  const startEditing = (site) => {
    setEditingSite(site.id);
    setEditForm({
      site_name: site.site_name || '',
      username: site.username || '',
      app_password: '',
      niche: site.niche || '',
      article_language: site.article_language || 'ro',
      tone: site.tone || ''
    });
  };

  const cancelEditing = () => {
    setEditingSite(null);
    setEditForm({});
  };

  const handleSaveEdit = async (siteId) => {
    setSaving(true);
    try {
      const updateData = { ...editForm };
      if (!updateData.app_password) {
        delete updateData.app_password;
      }
      await axios.patch(`${API}/wordpress/site/${siteId}`, updateData, { 
        headers: getAuthHeaders() 
      });
      toast.success('Site actualizat cu succes!');
      setEditingSite(null);
      fetchSites();
      refreshSites();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Eroare la actualizare');
    } finally {
      setSaving(false);
    }
  };

  const openKeywordsModal = async (site) => {
    setKeywordsModal(site);
    try {
      const response = await axios.get(`${API}/wordpress/site/${site.id}/keywords`, { 
        headers: getAuthHeaders() 
      });
      setSiteKeywords(response.data.keywords || []);
    } catch (error) {
      setSiteKeywords([]);
    }
  };

  const generateKeywords = async () => {
    if (!keywordsModal) return;
    setGeneratingKeywords(true);
    try {
      const response = await axios.post(
        `${API}/wordpress/site/${keywordsModal.id}/generate-keywords`,
        {},
        { headers: getAuthHeaders() }
      );
      setSiteKeywords(response.data.keywords || []);
      const synced = response.data.synced_to_main || 0;
      if (synced > 0) {
        toast.success(`${response.data.count} cuvinte cheie generate! ${synced} sincronizate în secțiunea Keywords.`);
      } else {
        toast.success(`${response.data.count} cuvinte cheie generate!`);
      }
    } catch (error) {
      toast.error('Eroare la generare');
    } finally {
      setGeneratingKeywords(false);
    }
  };

  const addKeyword = () => {
    if (!newKeyword.trim()) return;
    if (siteKeywords.includes(newKeyword.trim())) {
      toast.error('Acest cuvânt cheie există deja');
      return;
    }
    setSiteKeywords([...siteKeywords, newKeyword.trim()]);
    setNewKeyword('');
  };

  const removeKeyword = (keyword) => {
    setSiteKeywords(siteKeywords.filter(k => k !== keyword));
  };

  const saveKeywords = async () => {
    if (!keywordsModal) return;
    try {
      const response = await axios.put(
        `${API}/wordpress/site/${keywordsModal.id}/keywords`,
        { keywords: siteKeywords },
        { headers: getAuthHeaders() }
      );
      const synced = response.data.synced_to_main || 0;
      if (synced > 0) {
        toast.success(`Cuvinte cheie salvate! ${synced} noi sincronizate în secțiunea Keywords.`);
      } else {
        toast.success('Cuvinte cheie salvate!');
      }
      setKeywordsModal(null);
      fetchSites();
    } catch (error) {
      toast.error('Eroare la salvare');
    }
  };

  // Social Media functions
  const openSocialModal = async (site) => {
    setSocialModal(site);
    try {
      const response = await axios.get(`${API}/social/status/${site.id}`, { 
        headers: getAuthHeaders() 
      });
      setSocialStatus(response.data);
    } catch (error) {
      setSocialStatus({});
    }
  };

  const connectFacebook = async (siteId) => {
    try {
      const response = await axios.get(`${API}/social/facebook/auth-url/${siteId}`, { 
        headers: getAuthHeaders() 
      });
      window.location.href = response.data.authorization_url;
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Eroare la conectarea Facebook');
    }
  };

  const connectLinkedIn = async (siteId) => {
    try {
      const response = await axios.get(`${API}/social/linkedin/auth-url/${siteId}`, { 
        headers: getAuthHeaders() 
      });
      window.location.href = response.data.authorization_url;
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Eroare la conectarea LinkedIn');
    }
  };

  const disconnectFacebook = async (siteId) => {
    if (!window.confirm('Sigur vrei să deconectezi Facebook?')) return;
    try {
      await axios.delete(`${API}/social/facebook/disconnect/${siteId}`, { 
        headers: getAuthHeaders() 
      });
      toast.success('Facebook deconectat');
      setSocialStatus({ ...socialStatus, facebook: { connected: false } });
      fetchSites();
    } catch (error) {
      toast.error('Eroare la deconectare');
    }
  };

  const disconnectLinkedIn = async (siteId) => {
    if (!window.confirm('Sigur vrei să deconectezi LinkedIn?')) return;
    try {
      await axios.delete(`${API}/social/linkedin/disconnect/${siteId}`, { 
        headers: getAuthHeaders() 
      });
      toast.success('LinkedIn deconectat');
      setSocialStatus({ ...socialStatus, linkedin: { connected: false } });
      fetchSites();
    } catch (error) {
      toast.error('Eroare la deconectare');
    }
  };

  const testFacebookPost = async (siteId) => {
    try {
      toast.info('Se testează postarea pe Facebook...');
      const response = await axios.post(`${API}/social/facebook/test-post/${siteId}`, {}, {
        headers: getAuthHeaders()
      });
      if (response.data.success) {
        toast.success(`✅ Test reușit! Post ID: ${response.data.post_id}`);
      } else {
        toast.error(`❌ Eroare: ${response.data.error}`);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Eroare la testare');
    }
  };

  const testLinkedInPost = async (siteId) => {
    try {
      toast.info('Se testează postarea pe LinkedIn...');
      const response = await axios.post(`${API}/social/linkedin/test-post/${siteId}`, {}, {
        headers: getAuthHeaders()
      });
      if (response.data.success) {
        toast.success(`✅ Test LinkedIn reușit!`);
      } else {
        toast.error(`❌ Eroare: ${response.data.error}`);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Eroare la testare LinkedIn');
    }
  };

  const selectFacebookPage = async (siteId, pageId) => {
    if (!pageId) {
      toast.error('Selectează o pagină Facebook');
      return;
    }
    setSavingFacebookPage(true);
    try {
      const response = await axios.post(
        `${API}/social/facebook/select-page/${siteId}?page_id=${pageId}`,
        {},
        { headers: getAuthHeaders() }
      );
      if (response.data.success) {
        toast.success(`Pagină selectată: ${response.data.page_name}`);
        // Refresh social status
        const statusResponse = await axios.get(`${API}/social/status/${siteId}`, { 
          headers: getAuthHeaders() 
        });
        setSocialStatus(statusResponse.data);
        setSelectedFacebookPage('');
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Eroare la selectarea paginii');
    } finally {
      setSavingFacebookPage(false);
    }
  };

  const saveManualPageId = async (siteId, pageId, pageToken) => {
    if (!pageId || !pageId.trim()) {
      toast.error('Introdu un Page ID valid');
      return;
    }
    if (!pageToken || !pageToken.trim()) {
      toast.error('Introdu un Page Access Token valid');
      return;
    }
    setSavingFacebookPage(true);
    try {
      const response = await axios.post(
        `${API}/social/facebook/manual-connect/${siteId}`,
        { page_id: pageId.trim(), page_token: pageToken.trim() },
        { headers: getAuthHeaders() }
      );
      if (response.data.success) {
        toast.success('Pagina Facebook conectată!');
        setManualPageId('');
        setManualPageToken('');
        // Refresh social status
        const statusResponse = await axios.get(`${API}/social/status/${siteId}`, { 
          headers: getAuthHeaders() 
        });
        setSocialStatus(statusResponse.data);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Eroare la salvarea Page ID');
    } finally {
      setSavingFacebookPage(false);
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
    <div className="max-w-4xl mx-auto space-y-8" data-testid="wordpress-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="font-heading text-3xl font-bold">Site-uri WordPress</h1>
          <p className="text-muted-foreground mt-1">
            Gestionează site-urile WordPress pentru publicare automată
          </p>
        </div>
        <Button
          className="bg-primary text-primary-foreground hover:bg-primary/90"
          onClick={() => setShowForm(!showForm)}
          data-testid="add-site-button"
        >
          <Plus className="w-4 h-4 mr-2" />
          Adaugă Site
        </Button>
      </div>

      {/* Add Site Form */}
      {showForm && (
        <Card className="bg-card border-border">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/10">
                <LinkIcon className="w-5 h-5 text-primary" />
              </div>
              <div>
                <CardTitle className="font-heading text-lg">Adaugă Site WordPress</CardTitle>
                <CardDescription>
                  Introdu datele de conectare pentru noul site
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleConnect} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="site_url">URL Site WordPress *</Label>
                  <Input
                    id="site_url"
                    placeholder="https://site-ul-tau.ro"
                    value={formData.site_url}
                    onChange={(e) => setFormData({...formData, site_url: e.target.value})}
                    className="bg-secondary border-border"
                    required
                    data-testid="wordpress-url-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="site_name">Nume Site (opțional)</Label>
                  <Input
                    id="site_name"
                    placeholder="Ex: Blog Principal"
                    value={formData.site_name}
                    onChange={(e) => setFormData({...formData, site_name: e.target.value})}
                    className="bg-secondary border-border"
                    data-testid="wordpress-name-input"
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="niche">Nișă / Industrie *</Label>
                <Input
                  id="niche"
                  placeholder="Ex: Maritime Jobs, Real Estate, Fitness"
                  value={formData.niche}
                  onChange={(e) => setFormData({...formData, niche: e.target.value})}
                  className="bg-secondary border-border"
                  required
                  data-testid="wordpress-niche-input"
                />
                <p className="text-xs text-muted-foreground">
                  Nișa va fi folosită pentru a genera backlinks și keywords relevante
                </p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="username">Nume Utilizator *</Label>
                  <Input
                    id="username"
                    placeholder="admin"
                    value={formData.username}
                    onChange={(e) => setFormData({...formData, username: e.target.value})}
                    className="bg-secondary border-border"
                    required
                    data-testid="wordpress-username-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="app_password">Application Password *</Label>
                  <Input
                    id="app_password"
                    type="password"
                    placeholder="xxxx xxxx xxxx xxxx"
                    value={formData.app_password}
                    onChange={(e) => setFormData({...formData, app_password: e.target.value})}
                    className="bg-secondary border-border"
                    required
                    data-testid="wordpress-password-input"
                  />
                </div>
              </div>

              <div className="flex gap-2">
                <Button 
                  type="submit" 
                  className="bg-primary text-primary-foreground hover:bg-primary/90"
                  disabled={connecting}
                  data-testid="connect-wordpress-button"
                >
                  {connecting ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Se conectează...
                    </>
                  ) : (
                    <>
                      <LinkIcon className="w-4 h-4 mr-2" />
                      Conectează Site
                    </>
                  )}
                </Button>
                <Button 
                  type="button"
                  variant="outline"
                  className="border-border"
                  onClick={() => setShowForm(false)}
                >
                  Anulează
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Sites List */}
      {sites.length === 0 ? (
        <Card className="bg-card border-border">
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Globe className="w-16 h-16 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">Niciun site conectat</h3>
            <p className="text-muted-foreground text-center mb-6">
              Adaugă primul tău site WordPress pentru publicare automată
            </p>
            <Button 
              className="bg-primary text-primary-foreground"
              onClick={() => setShowForm(true)}
            >
              <Plus className="w-4 h-4 mr-2" />
              Adaugă Site
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {sites.map((site) => (
            <Card key={site.id} className="bg-card border-border hover:border-primary/30 transition-colors">
              <CardContent className="pt-6">
                {editingSite === site.id ? (
                  /* Edit Mode */
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="space-y-2">
                        <Label>Nume Site</Label>
                        <Input
                          value={editForm.site_name}
                          onChange={(e) => setEditForm({...editForm, site_name: e.target.value})}
                          className="bg-secondary border-border"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Nișă</Label>
                        <Input
                          value={editForm.niche}
                          onChange={(e) => setEditForm({...editForm, niche: e.target.value})}
                          className="bg-secondary border-border"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Limba Articolelor</Label>
                        <select
                          value={editForm.article_language || 'ro'}
                          onChange={(e) => setEditForm({...editForm, article_language: e.target.value})}
                          className="w-full px-3 py-2 rounded-md bg-secondary border border-border text-foreground"
                        >
                          <option value="ro">Română</option>
                          <option value="en">Engleză</option>
                        </select>
                      </div>
                      <div className="space-y-2 md:col-span-2">
                        <Label>Tonul Articolelor</Label>
                        <Input
                          value={editForm.tone || ''}
                          onChange={(e) => setEditForm({...editForm, tone: e.target.value})}
                          placeholder="ex: cald, empatic, de încredere pentru mame"
                          className="bg-secondary border-border"
                        />
                        <p className="text-xs text-muted-foreground">
                          Descrie tonul dorit pentru articole (profesional, prietenos, tehnic, etc.)
                        </p>
                      </div>
                      <div className="space-y-2">
                        <Label>Utilizator WordPress</Label>
                        <Input
                          value={editForm.username}
                          onChange={(e) => setEditForm({...editForm, username: e.target.value})}
                          className="bg-secondary border-border"
                        />
                      </div>
                      <div className="space-y-2">
                        <Label>Application Password (nou)</Label>
                        <Input
                          type="password"
                          value={editForm.app_password}
                          onChange={(e) => setEditForm({...editForm, app_password: e.target.value})}
                          placeholder="Lasă gol pentru a păstra parola veche"
                          className="bg-secondary border-border"
                        />
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button 
                        onClick={() => handleSaveEdit(site.id)}
                        disabled={saving}
                        className="bg-primary"
                      >
                        {saving ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : <Save className="w-4 h-4 mr-2" />}
                        Salvează
                      </Button>
                      <Button variant="outline" onClick={cancelEditing}>
                        <X className="w-4 h-4 mr-2" />
                        Anulează
                      </Button>
                    </div>
                  </div>
                ) : (
                  /* View Mode */
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="p-3 rounded-lg bg-green-500/10">
                        <Globe className="w-6 h-6 text-green-500" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-lg">{site.site_name || site.site_url}</h3>
                        <a 
                          href={site.site_url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-sm text-muted-foreground hover:text-primary flex items-center gap-1"
                        >
                          {site.site_url}
                          <ExternalLink className="w-3 h-3" />
                        </a>
                        <p className="text-xs text-muted-foreground mt-1">
                          Utilizator: {site.username}
                        </p>
                        <div className="flex items-center gap-2 mt-2 flex-wrap">
                          {site.niche && (
                            <Badge variant="outline" className="text-xs">
                              Nișă: {site.niche}
                            </Badge>
                          )}
                          {site.auto_keywords?.length > 0 && (
                            <Badge variant="outline" className="text-xs bg-primary/10 text-primary border-primary/20">
                              <Tag className="w-3 h-3 mr-1" />
                              {site.auto_keywords.length} keywords
                            </Badge>
                          )}
                        </div>
                        {/* Social Media Status Badges - More Visible */}
                        <div className="flex items-center gap-2 mt-2">
                          {site.facebook_connected ? (
                            <Badge className="bg-blue-500 text-white border-0 hover:bg-blue-600 cursor-pointer" onClick={() => openSocialModal(site)}>
                              <Facebook className="w-3 h-3 mr-1" />
                              FB Conectat
                            </Badge>
                          ) : (
                            <Badge variant="outline" className="text-xs text-muted-foreground border-dashed cursor-pointer hover:border-blue-500 hover:text-blue-500" onClick={() => openSocialModal(site)}>
                              <Facebook className="w-3 h-3 mr-1" />
                              FB Neconectat
                            </Badge>
                          )}
                          {site.site_url?.includes('seamanshelp') && (
                            site.linkedin_connected ? (
                              <Badge className="bg-blue-700 text-white border-0 hover:bg-blue-800 cursor-pointer" onClick={() => openSocialModal(site)}>
                                <Linkedin className="w-3 h-3 mr-1" />
                                LI Conectat
                              </Badge>
                            ) : (
                              <Badge variant="outline" className="text-xs text-muted-foreground border-dashed cursor-pointer hover:border-blue-700 hover:text-blue-700" onClick={() => openSocialModal(site)}>
                                <Linkedin className="w-3 h-3 mr-1" />
                                LI Neconectat
                              </Badge>
                            )
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Badge className="bg-green-500/10 text-green-500 border-green-500/20">
                        <CheckCircle2 className="w-3 h-3 mr-1" /> Conectat
                      </Badge>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => openSocialModal(site)}
                        className="text-blue-500 border-blue-500/30 hover:bg-blue-500/10"
                        data-testid={`social-site-${site.id}`}
                      >
                        <Share2 className="w-4 h-4 mr-1" />
                        Social
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => openKeywordsModal(site)}
                        className="text-primary border-primary/30 hover:bg-primary/10"
                        data-testid={`keywords-site-${site.id}`}
                      >
                        <Tag className="w-4 h-4 mr-1" />
                        Keywords
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => startEditing(site)}
                        className="text-muted-foreground hover:text-primary"
                        data-testid={`edit-site-${site.id}`}
                      >
                        <Pencil className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleDelete(site.id, site.site_name || site.site_url)}
                        className="text-muted-foreground hover:text-destructive"
                        data-testid={`delete-site-${site.id}`}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Instructions */}
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="font-heading text-lg">Cum obții Application Password</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <ol className="list-decimal list-inside space-y-2 text-sm text-muted-foreground">
            <li>Conectează-te la WordPress Dashboard</li>
            <li>Navighează la <strong className="text-foreground">Users → Profile</strong></li>
            <li>Derulează până la secțiunea <strong className="text-foreground">Application Passwords</strong></li>
            <li>Introdu un nume pentru aplicație (ex: "SEO Automation")</li>
            <li>Click pe <strong className="text-foreground">Add New Application Password</strong></li>
            <li>Copiază parola generată și introdu-o aici</li>
          </ol>
          <div className="p-4 rounded-lg bg-yellow-500/10 border border-yellow-500/20">
            <p className="text-sm text-yellow-500">
              <strong>Notă:</strong> Application Passwords necesită WordPress 5.6+ și HTTPS activat pe site.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Keywords Modal */}
      {keywordsModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="w-full max-w-2xl max-h-[80vh] overflow-hidden bg-card border-border m-4">
            <CardHeader className="border-b border-border">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Tag className="w-5 h-5 text-primary" />
                    Cuvinte Cheie SEO
                  </CardTitle>
                  <CardDescription>{keywordsModal.site_name || keywordsModal.site_url}</CardDescription>
                </div>
                <Button variant="ghost" size="icon" onClick={() => setKeywordsModal(null)}>
                  <X className="w-5 h-5" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="p-6 space-y-4 max-h-[60vh] overflow-y-auto">
              {/* Generate Button */}
              <div className="flex gap-2">
                <Button
                  onClick={generateKeywords}
                  disabled={generatingKeywords}
                  className="bg-primary hover:bg-primary/90"
                >
                  {generatingKeywords ? (
                    <>
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                      Generează...
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-4 h-4 mr-2" />
                      Generează Automat cu AI
                    </>
                  )}
                </Button>
                <Button variant="outline" onClick={() => setSiteKeywords([])}>
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Resetează
                </Button>
              </div>

              {/* Add Manual Keyword */}
              <div className="flex gap-2">
                <Input
                  placeholder="Adaugă cuvânt cheie manual..."
                  value={newKeyword}
                  onChange={(e) => setNewKeyword(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && addKeyword()}
                  className="bg-secondary border-border"
                />
                <Button variant="outline" onClick={addKeyword}>
                  <Plus className="w-4 h-4" />
                </Button>
              </div>

              {/* Keywords List */}
              <div className="border border-border rounded-lg p-4 min-h-[150px]">
                {siteKeywords.length === 0 ? (
                  <p className="text-center text-muted-foreground py-8">
                    Niciun cuvânt cheie. Generează automat sau adaugă manual.
                  </p>
                ) : (
                  <div className="flex flex-wrap gap-2">
                    {siteKeywords.map((keyword, index) => (
                      <Badge
                        key={index}
                        variant="secondary"
                        className="px-3 py-1.5 text-sm flex items-center gap-1 group"
                      >
                        {keyword}
                        <button
                          onClick={() => removeKeyword(keyword)}
                          className="ml-1 opacity-50 hover:opacity-100 transition-opacity"
                        >
                          <X className="w-3 h-3" />
                        </button>
                      </Badge>
                    ))}
                  </div>
                )}
              </div>

              <p className="text-xs text-muted-foreground">
                {siteKeywords.length} cuvinte cheie • Acestea vor fi folosite automat în articolele generate pentru SEO
              </p>
            </CardContent>
            <div className="border-t border-border p-4 flex justify-end gap-2">
              <Button variant="outline" onClick={() => setKeywordsModal(null)}>
                Anulează
              </Button>
              <Button onClick={saveKeywords} className="bg-primary hover:bg-primary/90">
                <Save className="w-4 h-4 mr-2" />
                Salvează Keywords
              </Button>
            </div>
          </Card>
        </div>
      )}

      {/* Social Media Modal */}
      {socialModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
          <Card className="w-full max-w-lg max-h-[80vh] overflow-hidden bg-card border-border m-4">
            <CardHeader className="border-b border-border">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Share2 className="w-5 h-5 text-primary" />
                    Social Media Auto-Posting
                  </CardTitle>
                  <CardDescription>{socialModal.site_name || socialModal.site_url}</CardDescription>
                </div>
                <Button variant="ghost" size="icon" onClick={() => setSocialModal(null)}>
                  <X className="w-5 h-5" />
                </Button>
              </div>
            </CardHeader>
            <CardContent className="p-6 space-y-4">
              <p className="text-sm text-muted-foreground">
                Când se publică un articol, va fi postat automat pe rețelele sociale conectate.
              </p>

              {/* Facebook */}
              <div className="p-4 rounded-lg border border-border bg-secondary/30 space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-blue-500/10">
                      <Facebook className="w-5 h-5 text-blue-500" />
                    </div>
                    <div>
                      <h4 className="font-medium">Facebook Page</h4>
                      <p className="text-xs text-muted-foreground">
                        {socialStatus.facebook?.page_name || socialStatus.facebook?.page_id || 'Postare automată pe pagina Facebook'}
                      </p>
                    </div>
                  </div>
                  {socialStatus.facebook?.connected && (
                    <div className="flex items-center gap-2">
                      <Badge className="bg-green-500/10 text-green-500">Conectat</Badge>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => testFacebookPost(socialModal.id)}
                        className="border-blue-500/30 text-blue-500"
                        data-testid="test-facebook-post-btn"
                      >
                        Test Post
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => disconnectFacebook(socialModal.id)}
                        className="text-red-500 border-red-500/30"
                        data-testid="disconnect-facebook-btn"
                      >
                        Deconectează
                      </Button>
                    </div>
                  )}
                </div>
                
                {/* Important notice about Facebook Business App */}
                {!socialStatus.facebook?.connected && (
                  <div className="mt-3 p-3 rounded-lg bg-secondary/50 border border-border">
                    <p className="text-sm font-medium mb-3">Conectare Facebook Page:</p>
                    <div className="space-y-3">
                      <div>
                        <label className="text-xs text-muted-foreground block mb-1">Page ID</label>
                        <input
                          type="text"
                          placeholder="Ex: 112431577304128"
                          value={manualPageId || ''}
                          onChange={(e) => setManualPageId(e.target.value)}
                          className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
                          data-testid="manual-page-id-input"
                        />
                        <p className="text-xs text-muted-foreground mt-1">Facebook → Pagina ta → About → Page ID</p>
                      </div>
                      <div>
                        <label className="text-xs text-muted-foreground block mb-1">Page Access Token</label>
                        <input
                          type="text"
                          placeholder="Token generat din Graph API Explorer"
                          value={manualPageToken || ''}
                          onChange={(e) => setManualPageToken(e.target.value)}
                          className="w-full px-3 py-2 rounded-md border border-input bg-background text-sm"
                          data-testid="manual-page-token-input"
                        />
                        <a 
                          href="https://developers.facebook.com/tools/explorer/" 
                          target="_blank" 
                          rel="noopener noreferrer" 
                          className="text-xs text-blue-500 underline"
                        >
                          Generează token aici →
                        </a>
                      </div>
                      <Button
                        onClick={() => saveManualPageId(socialModal.id, manualPageId, manualPageToken)}
                        disabled={!manualPageId || !manualPageToken || savingFacebookPage}
                        className="w-full bg-blue-500 hover:bg-blue-600 text-white"
                        data-testid="save-manual-page-btn"
                      >
                        {savingFacebookPage ? (
                          <Loader2 className="w-4 h-4 animate-spin mr-2" />
                        ) : (
                          <Save className="w-4 h-4 mr-2" />
                        )}
                        Salvează
                      </Button>
                    </div>
                  </div>
                )}
                
                {/* Page Selection Dropdown - shows when pages are pending selection */}
                {socialStatus.facebook?.pages_pending && socialStatus.facebook?.available_pages?.length > 0 && (
                  <div className="mt-3 p-3 rounded-lg bg-amber-500/10 border border-amber-500/30">
                    <p className="text-sm text-amber-600 dark:text-amber-400 mb-2">
                      <strong>Selectează pagina Facebook:</strong>
                    </p>
                    <div className="flex gap-2">
                      <select
                        value={selectedFacebookPage}
                        onChange={(e) => setSelectedFacebookPage(e.target.value)}
                        className="flex-1 px-3 py-2 rounded-md border border-input bg-background text-sm"
                        data-testid="facebook-page-select"
                      >
                        <option value="">-- Selectează o pagină --</option>
                        {socialStatus.facebook.available_pages.map((page) => (
                          <option key={page.id} value={page.id}>
                            {page.name}
                          </option>
                        ))}
                      </select>
                      <Button
                        onClick={() => selectFacebookPage(socialModal.id, selectedFacebookPage)}
                        disabled={!selectedFacebookPage || savingFacebookPage}
                        className="bg-blue-500 hover:bg-blue-600 text-white"
                        data-testid="save-facebook-page-btn"
                      >
                        {savingFacebookPage ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <Save className="w-4 h-4" />
                        )}
                      </Button>
                    </div>
                  </div>
                )}

                {/* Show available pages even when connected, for reference */}
                {socialStatus.facebook?.connected && socialStatus.facebook?.available_pages?.length > 1 && !socialStatus.facebook?.pages_pending && (
                  <div className="mt-2 text-xs text-muted-foreground">
                    Alte pagini disponibile: {socialStatus.facebook.available_pages.filter(p => p.id !== socialStatus.facebook.page_id).map(p => p.name).join(', ')}
                  </div>
                )}
              </div>

              {/* LinkedIn */}
              <div className="p-4 rounded-lg border border-border bg-secondary/30">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 rounded-lg bg-blue-700/10">
                      <Linkedin className="w-5 h-5 text-blue-700" />
                    </div>
                    <div>
                      <h4 className="font-medium">LinkedIn (Profil Personal)</h4>
                      <p className="text-xs text-muted-foreground">
                        {socialStatus.linkedin?.person_name || 'Postări pe profilul tău personal'}
                      </p>
                    </div>
                  </div>
                  {socialStatus.linkedin?.connected ? (
                    <div className="flex items-center gap-2">
                      <Badge className="bg-green-500/10 text-green-500">Conectat</Badge>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => testLinkedInPost(socialModal.id)}
                        className="text-blue-700 border-blue-700/30"
                        data-testid="test-linkedin-post-btn"
                      >
                        Test
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => disconnectLinkedIn(socialModal.id)}
                        className="text-red-500 border-red-500/30"
                        data-testid="disconnect-linkedin-btn"
                      >
                        Deconectează
                      </Button>
                    </div>
                  ) : (
                    <Button
                      onClick={() => connectLinkedIn(socialModal.id)}
                      className="bg-blue-700 hover:bg-blue-800 text-white"
                      data-testid="connect-linkedin-btn"
                    >
                      Conectează
                    </Button>
                  )}
                </div>
              </div>
            </CardContent>
            <div className="border-t border-border p-4 flex justify-end">
              <Button variant="outline" onClick={() => setSocialModal(null)}>
                Închide
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
