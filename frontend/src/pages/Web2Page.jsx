import { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '@/contexts/AuthContext';
import { useSite } from '@/contexts/SiteContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { toast } from 'sonner';
import { 
  Globe,
  FileText,
  Copy,
  ExternalLink,
  Loader2,
  CheckCircle2,
  Sparkles,
  AlertCircle,
  Trash2,
  Eye,
  Link2,
  Hash
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const PLATFORMS = [
  { id: 'medium', name: 'Medium', icon: '📝', description: 'Articole de calitate', color: 'bg-green-500' },
  { id: 'blogger', name: 'Blogger', icon: '🅱️', description: 'Blog Google gratuit', color: 'bg-orange-500' },
  { id: 'linkedin', name: 'LinkedIn', icon: '💼', description: 'Articole profesionale', color: 'bg-blue-500' },
  { id: 'tumblr', name: 'Tumblr', icon: '📱', description: 'Microblogging', color: 'bg-indigo-500' },
  { id: 'pinterest', name: 'Pinterest', icon: '📌', description: 'Imagini + linkuri', color: 'bg-red-500' },
];

export default function Web2Page() {
  const [articles, setArticles] = useState([]);
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(null);
  const [selectedArticle, setSelectedArticle] = useState(null);
  const [selectedPlatform, setSelectedPlatform] = useState('medium');
  const [activeTab, setActiveTab] = useState('generate');
  
  // Preview dialog
  const [showPreview, setShowPreview] = useState(false);
  const [currentPost, setCurrentPost] = useState(null);
  
  const { getAuthHeaders } = useAuth();
  const { currentSite } = useSite();

  // Refetch when currentSite changes
  useEffect(() => {
    setLoading(true);
    fetchArticles();
    fetchPosts();
  }, [currentSite?.id]);

  const fetchArticles = async () => {
    try {
      const params = {};
      if (currentSite?.id) {
        params.site_id = currentSite.id;
      }
      const response = await axios.get(`${API}/articles`, { 
        headers: getAuthHeaders(),
        params
      });
      // Only show published articles for the current site
      const publishedArticles = response.data.filter(a => a.status === 'published');
      setArticles(publishedArticles);
    } catch (error) {
      console.error('Failed to fetch articles:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchPosts = async () => {
    try {
      const response = await axios.get(`${API}/web2/posts`, { headers: getAuthHeaders() });
      setPosts(response.data);
    } catch (error) {
      console.error('Failed to fetch posts:', error);
    }
  };

  const handleGeneratePost = async () => {
    if (!selectedArticle) {
      toast.error('Selectează un articol');
      return;
    }

    setGenerating(selectedPlatform);
    try {
      const response = await axios.post(
        `${API}/web2/generate-post/${selectedArticle}`,
        null,
        {
          headers: getAuthHeaders(),
          params: { platform: selectedPlatform }
        }
      );
      
      setCurrentPost(response.data);
      setShowPreview(true);
      toast.success(`Post ${selectedPlatform} generat!`);
      fetchPosts();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Eroare la generare');
    } finally {
      setGenerating(null);
    }
  };

  const handleCopyContent = () => {
    if (currentPost) {
      const fullContent = `${currentPost.title}\n\n${currentPost.content}\n\nTags: ${currentPost.tags?.join(', ')}`;
      navigator.clipboard.writeText(fullContent);
      toast.success('Conținut copiat!');
    }
  };

  const handleMarkPublished = async (postId, url = '') => {
    try {
      await axios.post(
        `${API}/web2/posts/${postId}/mark-published`,
        null,
        {
          headers: getAuthHeaders(),
          params: { published_url: url }
        }
      );
      toast.success('Marcat ca publicat!');
      fetchPosts();
      setShowPreview(false);
    } catch (error) {
      toast.error('Eroare');
    }
  };

  const handleDeletePost = async (postId) => {
    try {
      await axios.delete(`${API}/web2/posts/${postId}`, { headers: getAuthHeaders() });
      toast.success('Post șters');
      fetchPosts();
    } catch (error) {
      toast.error('Eroare la ștergere');
    }
  };

  const getPlatformInfo = (platformId) => {
    return PLATFORMS.find(p => p.id === platformId) || PLATFORMS[0];
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="space-y-8" data-testid="web2-page">
      {/* Header */}
      <div>
        <h1 className="font-heading text-3xl font-bold flex items-center gap-3">
          <Globe className="w-8 h-8 text-primary" />
          Web 2.0 Backlinks
        </h1>
        <p className="text-muted-foreground mt-1">
          Generează și publică articole pe platforme Web 2.0 pentru backlinks
        </p>
      </div>

      {/* Info Card */}
      <Card className="bg-primary/5 border-primary/20">
        <CardContent className="pt-6">
          <div className="flex gap-4">
            <div className="w-10 h-10 rounded-full bg-primary/20 flex items-center justify-center flex-shrink-0">
              <Sparkles className="w-5 h-5 text-primary" />
            </div>
            <div>
              <h3 className="font-semibold text-foreground mb-1">Cum funcționează?</h3>
              <p className="text-sm text-muted-foreground">
                1. Selectezi un articol publicat pe WordPress<br/>
                2. Alegi platforma (Medium, Blogger, LinkedIn, etc.)<br/>
                3. AI-ul generează o versiune optimizată cu link către original<br/>
                4. Copiezi și postezi manual pe platformă
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <Card className="bg-card border-border">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/10">
                <FileText className="w-5 h-5 text-primary" />
              </div>
              <div>
                <p className="text-2xl font-bold font-heading">{posts.length}</p>
                <p className="text-sm text-muted-foreground">Posturi generate</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-card border-border">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-yellow-500/10">
                <Globe className="w-5 h-5 text-yellow-500" />
              </div>
              <div>
                <p className="text-2xl font-bold font-heading">
                  {posts.filter(p => p.status === 'draft').length}
                </p>
                <p className="text-sm text-muted-foreground">De publicat</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-card border-border">
          <CardContent className="pt-6">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-green-500/10">
                <CheckCircle2 className="w-5 h-5 text-green-500" />
              </div>
              <div>
                <p className="text-2xl font-bold font-heading">
                  {posts.filter(p => p.status === 'published').length}
                </p>
                <p className="text-sm text-muted-foreground">Publicate</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-secondary">
          <TabsTrigger value="generate" className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
            <Sparkles className="w-4 h-4 mr-2" />
            Generează Post
          </TabsTrigger>
          <TabsTrigger value="posts" className="data-[state=active]:bg-primary data-[state=active]:text-primary-foreground">
            <FileText className="w-4 h-4 mr-2" />
            Posturi ({posts.length})
          </TabsTrigger>
        </TabsList>

        {/* Generate Tab */}
        <TabsContent value="generate" className="space-y-6">
          <Card className="bg-card border-border">
            <CardHeader>
              <CardTitle>Generează Post Web 2.0</CardTitle>
              <CardDescription>
                Selectează un articol și o platformă pentru a genera conținut optimizat
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Article Selection */}
              <div className="space-y-2">
                <Label>Articol sursă</Label>
                {articles.length === 0 ? (
                  <div className="p-3 rounded-lg bg-yellow-500/10 border border-yellow-500/20 text-sm text-yellow-500">
                    Niciun articol publicat. Publică mai întâi un articol pe WordPress.
                  </div>
                ) : (
                  <Select value={selectedArticle || ''} onValueChange={setSelectedArticle}>
                    <SelectTrigger className="bg-secondary">
                      <SelectValue placeholder="Selectează un articol publicat" />
                    </SelectTrigger>
                    <SelectContent>
                      {articles.map(article => (
                        <SelectItem key={article.id} value={article.id}>
                          {article.title}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              </div>

              {/* Platform Selection */}
              <div className="space-y-2">
                <Label>Platformă</Label>
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                  {PLATFORMS.map(platform => (
                    <button
                      key={platform.id}
                      type="button"
                      onClick={() => setSelectedPlatform(platform.id)}
                      className={`p-4 rounded-lg border-2 transition-all text-center ${
                        selectedPlatform === platform.id
                          ? 'border-primary bg-primary/10'
                          : 'border-border hover:border-primary/50'
                      }`}
                    >
                      <span className="text-2xl block mb-1">{platform.icon}</span>
                      <span className="text-sm font-medium block">{platform.name}</span>
                    </button>
                  ))}
                </div>
              </div>

              <Button
                onClick={handleGeneratePost}
                disabled={!selectedArticle || generating}
                className="w-full bg-primary text-primary-foreground"
              >
                {generating ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Se generează pentru {getPlatformInfo(generating).name}...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 mr-2" />
                    Generează Post {getPlatformInfo(selectedPlatform).name}
                  </>
                )}
              </Button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Posts Tab */}
        <TabsContent value="posts" className="space-y-4">
          {posts.length === 0 ? (
            <Card className="bg-card border-border">
              <CardContent className="flex flex-col items-center justify-center py-16">
                <Globe className="w-16 h-16 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">Niciun post generat</h3>
                <p className="text-muted-foreground text-center">
                  Generează primul post din tab-ul "Generează Post"
                </p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-3">
              {posts.map((post) => {
                const platform = getPlatformInfo(post.platform);
                return (
                  <Card key={post.id} className="bg-card border-border">
                    <CardContent className="py-4">
                      <div className="flex items-center justify-between gap-4">
                        <div className="flex items-center gap-3 flex-1 min-w-0">
                          <span className="text-2xl">{platform.icon}</span>
                          <div className="min-w-0">
                            <p className="font-medium truncate">{post.title}</p>
                            <div className="flex items-center gap-2 mt-1">
                              <Badge variant="outline" className="text-xs">
                                {platform.name}
                              </Badge>
                              <Badge 
                                className={post.status === 'published' 
                                  ? 'bg-green-500/10 text-green-500' 
                                  : 'bg-yellow-500/10 text-yellow-500'
                                }
                              >
                                {post.status === 'published' ? 'Publicat' : 'Draft'}
                              </Badge>
                            </div>
                          </div>
                        </div>
                        
                        <div className="flex items-center gap-2">
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => {
                              setCurrentPost(post);
                              setShowPreview(true);
                            }}
                          >
                            <Eye className="w-4 h-4" />
                          </Button>
                          {post.status === 'draft' && (
                            <Button
                              size="sm"
                              onClick={() => handleMarkPublished(post.id)}
                              className="bg-green-500 hover:bg-green-600"
                            >
                              <CheckCircle2 className="w-4 h-4" />
                            </Button>
                          )}
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleDeletePost(post.id)}
                            className="text-destructive"
                          >
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Preview Dialog */}
      <Dialog open={showPreview} onOpenChange={setShowPreview}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <span className="text-xl">{currentPost && getPlatformInfo(currentPost.platform).icon}</span>
              Post {currentPost && getPlatformInfo(currentPost.platform).name}
            </DialogTitle>
            <DialogDescription>
              Copiază conținutul și postează manual pe platformă
            </DialogDescription>
          </DialogHeader>

          <div className="flex-1 overflow-y-auto space-y-4 py-4">
            {currentPost && (
              <>
                <div>
                  <Label className="text-sm font-medium">Titlu</Label>
                  <div className="mt-1 p-3 rounded bg-secondary font-medium">
                    {currentPost.title}
                  </div>
                </div>

                <div>
                  <Label className="text-sm font-medium">Conținut</Label>
                  <div className="mt-1 p-3 rounded bg-secondary text-sm whitespace-pre-wrap max-h-[300px] overflow-y-auto">
                    {currentPost.content}
                  </div>
                </div>

                {currentPost.tags && currentPost.tags.length > 0 && (
                  <div>
                    <Label className="text-sm font-medium flex items-center gap-1">
                      <Hash className="w-4 h-4" /> Tags
                    </Label>
                    <div className="mt-1 flex flex-wrap gap-1">
                      {currentPost.tags.map((tag, idx) => (
                        <Badge key={idx} variant="secondary">{tag}</Badge>
                      ))}
                    </div>
                  </div>
                )}

                {currentPost.original_url && (
                  <div className="p-3 rounded bg-primary/10 flex items-center gap-2">
                    <Link2 className="w-4 h-4 text-primary" />
                    <span className="text-sm">Link original inclus: </span>
                    <a 
                      href={currentPost.original_url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-primary text-sm hover:underline truncate"
                    >
                      {currentPost.original_url}
                    </a>
                  </div>
                )}
              </>
            )}
          </div>

          <DialogFooter className="flex-shrink-0 gap-2">
            <Button variant="outline" onClick={handleCopyContent}>
              <Copy className="w-4 h-4 mr-2" />
              Copiază Tot
            </Button>
            {currentPost?.status === 'draft' && (
              <Button 
                onClick={() => handleMarkPublished(currentPost.id)}
                className="bg-green-500 hover:bg-green-600"
              >
                <CheckCircle2 className="w-4 h-4 mr-2" />
                Marchează Publicat
              </Button>
            )}
            <Button variant="outline" onClick={() => setShowPreview(false)}>
              Închide
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
