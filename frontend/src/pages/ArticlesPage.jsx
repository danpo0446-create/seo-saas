import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '@/contexts/AuthContext';
import { useSite } from '@/contexts/SiteContext';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { 
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { 
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSub,
  DropdownMenuSubTrigger,
  DropdownMenuSubContent,
  DropdownMenuPortal,
} from '@/components/ui/dropdown-menu';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { toast } from 'sonner';
import { 
  PlusCircle, 
  MoreVertical, 
  FileText, 
  Trash2, 
  Eye,
  Send,
  Clock,
  Edit,
  Save,
  X,
  Loader2,
  Globe,
  RefreshCw
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const statusColors = {
  draft: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
  published: 'bg-green-500/10 text-green-500 border-green-500/20',
  scheduled: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
};

export default function ArticlesPage() {
  const [articles, setArticles] = useState([]);
  const [wpSites, setWpSites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedArticle, setSelectedArticle] = useState(null);
  const [editMode, setEditMode] = useState(false);
  const [editData, setEditData] = useState({ title: '', content: '', keywords: '' });
  const [saving, setSaving] = useState(false);
  const [publishingSiteId, setPublishingSiteId] = useState(null);
  const [selectedSiteForPublish, setSelectedSiteForPublish] = useState('');
  const [showPublishDialog, setShowPublishDialog] = useState(false);
  const [articleToPublish, setArticleToPublish] = useState(null);
  const { currentSiteId, currentSite, sites, loading: sitesLoading } = useSite();
  const { getAuthHeaders } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    // Wait for sites to load AND have a selected site before fetching articles
    if (!sitesLoading && (currentSiteId || currentSite?.id)) {
      fetchData();
    }
  }, [currentSiteId, currentSite?.id, sitesLoading]);

  const fetchData = async () => {
    try {
      // ALWAYS filter by site_id - use currentSiteId or currentSite.id
      const siteIdToFilter = currentSiteId || currentSite?.id;
      
      // Don't fetch if no site selected
      if (!siteIdToFilter) {
        setArticles([]);
        setLoading(false);
        return;
      }
      
      const [articlesRes, sitesRes] = await Promise.all([
        axios.get(`${API}/articles`, { headers: getAuthHeaders(), params: { site_id: siteIdToFilter } }),
        axios.get(`${API}/wordpress/sites`, { headers: getAuthHeaders() })
      ]);
      // Sort articles by created_at descending (newest first)
      const sortedArticles = articlesRes.data.sort((a, b) => 
        new Date(b.created_at) - new Date(a.created_at)
      );
      setArticles(sortedArticles);
      setWpSites(sitesRes.data);
    } catch (error) {
      toast.error('Eroare la încărcarea datelor');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Ești sigur că vrei să ștergi acest articol?')) return;
    try {
      await axios.delete(`${API}/articles/${id}`, { headers: getAuthHeaders() });
      toast.success('Articol șters');
      fetchData();
    } catch (error) {
      toast.error('Eroare la ștergere');
    }
  };

  const handlePublishClick = (article) => {
    if (wpSites.length === 0) {
      toast.error('Niciun site WordPress conectat. Du-te la WordPress pentru a adăuga un site.');
      return;
    }
    if (wpSites.length === 1) {
      handlePublish(article.id, wpSites[0].id);
    } else {
      setArticleToPublish(article);
      setSelectedSiteForPublish(wpSites[0].id);
      setShowPublishDialog(true);
    }
  };

  const handlePublish = async (articleId, siteId) => {
    setPublishingSiteId(siteId);
    try {
      await axios.post(`${API}/wordpress/publish/${articleId}?site_id=${siteId}`, {}, { headers: getAuthHeaders() });
      const site = wpSites.find(s => s.id === siteId);
      toast.success(`Articol publicat pe ${site?.site_name || site?.site_url}!`);
      setShowPublishDialog(false);
      setArticleToPublish(null);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Eroare la publicare');
    } finally {
      setPublishingSiteId(null);
    }
  };

  const [regenerating, setRegenerating] = useState(null);

  const handleRegenerate = async (articleId) => {
    if (!window.confirm('Regenerezi articolul în format HTML? Conținutul vechi va fi înlocuit.')) return;
    setRegenerating(articleId);
    try {
      const response = await axios.post(`${API}/articles/${articleId}/regenerate`, {}, { headers: getAuthHeaders() });
      toast.success('Articol regenerat în HTML!');
      fetchData();
      if (selectedArticle?.id === articleId) {
        setSelectedArticle(response.data);
        setEditData({
          title: response.data.title,
          content: response.data.content,
          keywords: response.data.keywords.join(', ')
        });
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Eroare la regenerare');
    } finally {
      setRegenerating(null);
    }
  };

  const handleViewArticle = (article) => {
    setSelectedArticle(article);
    setEditMode(false);
    setEditData({
      title: article.title,
      content: article.content,
      keywords: article.keywords.join(', ')
    });
  };

  const handleEditToggle = () => {
    if (!editMode) {
      setEditData({
        title: selectedArticle.title,
        content: selectedArticle.content,
        keywords: selectedArticle.keywords.join(', ')
      });
    }
    setEditMode(!editMode);
  };

  const handleSaveEdit = async () => {
    setSaving(true);
    try {
      const keywords = editData.keywords.split(',').map(k => k.trim()).filter(k => k);
      await axios.put(`${API}/articles/${selectedArticle.id}`, {
        title: editData.title,
        content: editData.content,
        keywords
      }, { headers: getAuthHeaders() });
      
      toast.success('Articol actualizat cu succes!');
      setEditMode(false);
      fetchData();
      
      setSelectedArticle({
        ...selectedArticle,
        title: editData.title,
        content: editData.content,
        keywords,
        word_count: editData.content.split(/\s+/).length
      });
    } catch (error) {
      toast.error('Eroare la salvare');
    } finally {
      setSaving(false);
    }
  };

  const handleCloseModal = () => {
    setSelectedArticle(null);
    setEditMode(false);
  };

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-8 bg-secondary rounded w-48" />
        <div className="grid gap-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-32 bg-secondary rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8" data-testid="articles-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="font-heading text-3xl font-bold">Articole</h1>
          <p className="text-muted-foreground mt-1">
            Gestionează și generează articole SEO
          </p>
        </div>
        <Button 
          className="bg-primary text-primary-foreground hover:bg-primary/90 neon-glow-hover"
          onClick={() => navigate('/articles/new')}
          data-testid="generate-article-button"
        >
          <PlusCircle className="w-4 h-4 mr-2" />
          Generează Articol
        </Button>
      </div>

      {/* Articles List */}
      {articles.length === 0 ? (
        <Card className="bg-card border-border">
          <CardContent className="flex flex-col items-center justify-center py-16">
            <FileText className="w-16 h-16 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">Niciun articol încă</h3>
            <p className="text-muted-foreground text-center mb-6">
              Începe prin a genera primul tău articol SEO optimizat
            </p>
            <Button 
              className="bg-primary text-primary-foreground"
              onClick={() => navigate('/articles/new')}
            >
              <PlusCircle className="w-4 h-4 mr-2" />
              Primul Articol
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {articles.map((article) => (
            <Card 
              key={article.id} 
              className="bg-card border-border hover:border-primary/30 transition-colors"
            >
              <CardContent className="pt-6">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-3 mb-2">
                      <Badge className={statusColors[article.status] || statusColors.draft}>
                        {article.status === 'draft' && 'Ciornă'}
                        {article.status === 'published' && 'Publicat'}
                        {article.status === 'scheduled' && 'Programat'}
                      </Badge>
                      <span className="text-xs text-muted-foreground flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {new Date(article.created_at).toLocaleDateString('ro-RO')}
                      </span>
                    </div>
                    <h3 className="font-heading font-semibold text-lg mb-2 truncate">
                      {article.title}
                    </h3>
                    <div className="flex flex-wrap gap-2 mb-3">
                      {article.keywords.slice(0, 3).map((kw, i) => (
                        <span 
                          key={i}
                          className="text-xs px-2 py-1 rounded-full bg-secondary text-muted-foreground"
                        >
                          {kw}
                        </span>
                      ))}
                      {article.keywords.length > 3 && (
                        <span className="text-xs px-2 py-1 rounded-full bg-secondary text-muted-foreground">
                          +{article.keywords.length - 3}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <span>{article.word_count} cuvinte</span>
                      <span>Scor SEO: {article.seo_score}%</span>
                    </div>
                  </div>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="icon" data-testid={`article-menu-${article.id}`}>
                        <MoreVertical className="w-4 h-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="bg-card border-border">
                      <DropdownMenuItem 
                        onClick={() => handleViewArticle(article)}
                        className="cursor-pointer"
                      >
                        <Eye className="w-4 h-4 mr-2" />
                        Vizualizează / Editează
                      </DropdownMenuItem>
                      <DropdownMenuItem 
                        onClick={() => handleRegenerate(article.id)}
                        className="cursor-pointer"
                        disabled={regenerating === article.id}
                      >
                        {regenerating === article.id ? (
                          <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        ) : (
                          <RefreshCw className="w-4 h-4 mr-2" />
                        )}
                        Regenerează (HTML)
                      </DropdownMenuItem>
                      {article.status === 'draft' && wpSites.length > 0 && (
                        <DropdownMenuItem 
                          onClick={() => handlePublishClick(article)}
                          className="cursor-pointer"
                        >
                          <Send className="w-4 h-4 mr-2" />
                          Publică pe WordPress
                        </DropdownMenuItem>
                      )}
                      <DropdownMenuItem 
                        onClick={() => handleDelete(article.id)}
                        className="cursor-pointer text-destructive"
                      >
                        <Trash2 className="w-4 h-4 mr-2" />
                        Șterge
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Publish Site Selection Dialog */}
      <Dialog open={showPublishDialog} onOpenChange={setShowPublishDialog}>
        <DialogContent className="bg-card border-border">
          <DialogHeader>
            <DialogTitle className="font-heading">Alege site-ul pentru publicare</DialogTitle>
            <DialogDescription>
              Selectează pe care site WordPress vrei să publici articolul
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Site WordPress</Label>
              <Select value={selectedSiteForPublish} onValueChange={setSelectedSiteForPublish}>
                <SelectTrigger className="bg-secondary border-border">
                  <SelectValue placeholder="Selectează site" />
                </SelectTrigger>
                <SelectContent className="bg-card border-border">
                  {wpSites.map(site => (
                    <SelectItem key={site.id} value={site.id}>
                      <div className="flex items-center gap-2">
                        <Globe className="w-4 h-4" />
                        {site.site_name || site.site_url}
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex gap-2 justify-end">
              <Button variant="outline" onClick={() => setShowPublishDialog(false)}>
                Anulează
              </Button>
              <Button 
                className="bg-primary text-primary-foreground"
                onClick={() => handlePublish(articleToPublish?.id, selectedSiteForPublish)}
                disabled={publishingSiteId !== null}
              >
                {publishingSiteId ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Se publică...
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4 mr-2" />
                    Publică
                  </>
                )}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Article Preview/Edit Modal */}
      <Dialog open={!!selectedArticle} onOpenChange={(open) => !open && handleCloseModal()}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden bg-card border-border">
          <DialogHeader>
            <div className="flex items-center justify-between">
              <div className="flex-1">
                {editMode ? (
                  <Input
                    value={editData.title}
                    onChange={(e) => setEditData({...editData, title: e.target.value})}
                    className="text-xl font-heading font-semibold bg-secondary border-border"
                    data-testid="edit-article-title"
                  />
                ) : (
                  <DialogTitle className="font-heading text-xl">{selectedArticle?.title}</DialogTitle>
                )}
              </div>
              <div className="flex gap-2 ml-4">
                {editMode ? (
                  <>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={handleEditToggle}
                      disabled={saving}
                    >
                      <X className="w-4 h-4 mr-1" />
                      Anulează
                    </Button>
                    <Button
                      size="sm"
                      className="bg-primary text-primary-foreground"
                      onClick={handleSaveEdit}
                      disabled={saving}
                      data-testid="save-article-button"
                    >
                      {saving ? (
                        <Loader2 className="w-4 h-4 mr-1 animate-spin" />
                      ) : (
                        <Save className="w-4 h-4 mr-1" />
                      )}
                      Salvează
                    </Button>
                  </>
                ) : (
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleEditToggle}
                    className="border-border"
                    data-testid="edit-article-button"
                  >
                    <Edit className="w-4 h-4 mr-1" />
                    Editează
                  </Button>
                )}
              </div>
            </div>
            {selectedArticle && (
              <DialogDescription className="flex items-center gap-4 mt-2">
                <Badge className={statusColors[selectedArticle.status]}>
                  {selectedArticle.status === 'draft' && 'Ciornă'}
                  {selectedArticle.status === 'published' && 'Publicat'}
                </Badge>
                <span>{selectedArticle.word_count} cuvinte</span>
                <span>Scor SEO: {selectedArticle.seo_score}%</span>
              </DialogDescription>
            )}
          </DialogHeader>
          
          <div className="overflow-y-auto max-h-[60vh] py-4">
            {editMode ? (
              <div className="space-y-4">
                <div>
                  <Label className="text-sm text-muted-foreground">Cuvinte-cheie (separate prin virgulă)</Label>
                  <Input
                    value={editData.keywords}
                    onChange={(e) => setEditData({...editData, keywords: e.target.value})}
                    className="mt-1 bg-secondary border-border"
                    placeholder="SEO, marketing, content"
                    data-testid="edit-article-keywords"
                  />
                </div>
                <div>
                  <Label className="text-sm text-muted-foreground">Conținut articol</Label>
                  <Textarea
                    value={editData.content}
                    onChange={(e) => setEditData({...editData, content: e.target.value})}
                    className="mt-1 bg-secondary border-border min-h-[400px] font-mono text-sm"
                    data-testid="edit-article-content"
                  />
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="flex flex-wrap gap-2">
                  {selectedArticle?.keywords.map((kw, i) => (
                    <span 
                      key={i}
                      className="text-xs px-3 py-1 rounded-full bg-primary/10 text-primary border border-primary/20"
                    >
                      {kw}
                    </span>
                  ))}
                </div>
                <div className="prose prose-invert max-w-none">
                  <div className="whitespace-pre-wrap text-foreground leading-relaxed">
                    {selectedArticle?.content}
                  </div>
                </div>
              </div>
            )}
          </div>

          {!editMode && selectedArticle?.status === 'draft' && wpSites.length > 0 && (
            <div className="flex justify-end gap-2 pt-4 border-t border-border">
              <Button
                className="bg-primary text-primary-foreground hover:bg-primary/90"
                onClick={() => handlePublishClick(selectedArticle)}
              >
                <Send className="w-4 h-4 mr-2" />
                Publică pe WordPress
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
