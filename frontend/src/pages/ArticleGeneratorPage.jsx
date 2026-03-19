import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '@/contexts/AuthContext';
import { useSite } from '@/contexts/SiteContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
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
  DialogTrigger,
} from '@/components/ui/dialog';
import { toast } from 'sonner';
import { 
  ArrowLeft, 
  Sparkles, 
  Loader2,
  FileText,
  Wand2,
  ChevronRight
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const toneLabels = {
  professional: 'Profesional',
  casual: 'Casual',
  friendly: 'Prietenos',
  authoritative: 'Autoritar'
};

const lengthLabels = {
  short: 'Scurt (~500 cuvinte)',
  medium: 'Mediu (~1000 cuvinte)',
  long: 'Lung (~2000 cuvinte)'
};

export default function ArticleGeneratorPage() {
  const [mode, setMode] = useState('manual'); // 'manual' or 'template'
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  
  // Manual mode state
  const [title, setTitle] = useState('');
  const [keywords, setKeywords] = useState('');
  const [niche, setNiche] = useState('');
  const [tone, setTone] = useState('professional');
  const [length, setLength] = useState('medium');
  
  // Template mode state
  const [topic, setTopic] = useState('');
  const [templateKeywords, setTemplateKeywords] = useState('');
  const [templateNiche, setTemplateNiche] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [loadingTemplates, setLoadingTemplates] = useState(true);
  const { getAuthHeaders } = useAuth();
  const { currentSiteId, currentSite } = useSite();
  const navigate = useNavigate();

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      const response = await axios.get(`${API}/templates`, { headers: getAuthHeaders() });
      setTemplates(response.data);
    } catch (error) {
      console.error('Failed to fetch templates:', error);
    } finally {
      setLoadingTemplates(false);
    }
  };

  const handleGenerateManual = async (e) => {
    e.preventDefault();
    
    if (!title.trim() || !keywords.trim() || !niche.trim()) {
      toast.error('Completează toate câmpurile obligatorii');
      return;
    }

    setLoading(true);
    try {
      const keywordList = keywords.split(',').map(k => k.trim()).filter(k => k);
      
      await axios.post(`${API}/articles/generate`, {
        title,
        keywords: keywordList,
        niche,
        tone,
        length,
        site_id: currentSiteId
      }, { headers: getAuthHeaders() });

      toast.success('Articol generat cu succes!');
      navigate('/articles');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Eroare la generarea articolului');
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateFromTemplate = async (e) => {
    e.preventDefault();
    
    if (!selectedTemplate || !topic.trim() || !templateKeywords.trim() || !templateNiche.trim()) {
      toast.error('Completează toate câmpurile și selectează un template');
      return;
    }

    setLoading(true);
    try {
      const keywordList = templateKeywords.split(',').map(k => k.trim()).filter(k => k);
      
      await axios.post(`${API}/articles/generate-from-template`, null, {
        headers: getAuthHeaders(),
        params: {
          template_id: selectedTemplate.id,
          topic,
          keywords: keywordList,
          niche: templateNiche
        }
      });

      toast.success('Articol generat cu succes din template!');
      navigate('/articles');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Eroare la generarea articolului');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6" data-testid="article-generator-page">
      {/* Back Button */}
      <Button 
        variant="ghost" 
        onClick={() => navigate('/articles')}
        className="text-muted-foreground hover:text-foreground"
        data-testid="back-button"
      >
        <ArrowLeft className="w-4 h-4 mr-2" />
        Înapoi la articole
      </Button>

      {/* Mode Selector */}
      <div className="flex gap-4">
        <Button
          variant={mode === 'manual' ? 'default' : 'outline'}
          className={mode === 'manual' ? 'bg-primary text-primary-foreground' : 'border-border'}
          onClick={() => setMode('manual')}
        >
          <Sparkles className="w-4 h-4 mr-2" />
          Generare Manuală
        </Button>
        <Button
          variant={mode === 'template' ? 'default' : 'outline'}
          className={mode === 'template' ? 'bg-primary text-primary-foreground' : 'border-border'}
          onClick={() => setMode('template')}
        >
          <Wand2 className="w-4 h-4 mr-2" />
          Din Template
        </Button>
      </div>

      {/* Manual Mode */}
      {mode === 'manual' && (
        <Card className="bg-card border-border">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-primary/10">
                <Sparkles className="w-6 h-6 text-primary" />
              </div>
              <div>
                <CardTitle className="font-heading text-2xl">Generator Articole AI</CardTitle>
                <CardDescription>
                  Creează articole SEO optimizate automat cu GPT-5.2
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleGenerateManual} className="space-y-6">
              <div className="space-y-2">
                <Label htmlFor="title">Titlu articol *</Label>
                <Input
                  id="title"
                  placeholder="Ex: Ghid complet pentru SEO în 2024"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="bg-secondary border-border"
                  required
                  data-testid="article-title-input"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="keywords">Cuvinte-cheie (separate prin virgulă) *</Label>
                <Textarea
                  id="keywords"
                  placeholder="Ex: SEO, optimizare site, marketing digital"
                  value={keywords}
                  onChange={(e) => setKeywords(e.target.value)}
                  className="bg-secondary border-border min-h-[80px]"
                  required
                  data-testid="article-keywords-input"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="niche">Nișă / Industrie *</Label>
                <Input
                  id="niche"
                  placeholder="Ex: Marketing Digital, E-commerce, Sănătate"
                  value={niche}
                  onChange={(e) => setNiche(e.target.value)}
                  className="bg-secondary border-border"
                  required
                  data-testid="article-niche-input"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Ton</Label>
                  <Select value={tone} onValueChange={setTone}>
                    <SelectTrigger className="bg-secondary border-border" data-testid="article-tone-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-card border-border">
                      <SelectItem value="professional">Profesional</SelectItem>
                      <SelectItem value="casual">Casual</SelectItem>
                      <SelectItem value="friendly">Prietenos</SelectItem>
                      <SelectItem value="authoritative">Autoritar</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                <div className="space-y-2">
                  <Label>Lungime</Label>
                  <Select value={length} onValueChange={setLength}>
                    <SelectTrigger className="bg-secondary border-border" data-testid="article-length-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-card border-border">
                      <SelectItem value="short">Scurt (~500 cuvinte)</SelectItem>
                      <SelectItem value="medium">Mediu (~1000 cuvinte)</SelectItem>
                      <SelectItem value="long">Lung (~2000 cuvinte)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <Button 
                type="submit" 
                className="w-full bg-primary text-primary-foreground hover:bg-primary/90 neon-glow-hover h-12"
                disabled={loading}
                data-testid="generate-article-submit"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Se generează articolul... (poate dura 30-60s)
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 mr-2" />
                    Generează Articol
                  </>
                )}
              </Button>
            </form>
          </CardContent>
        </Card>
      )}

      {/* Template Mode */}
      {mode === 'template' && (
        <div className="space-y-6">
          {/* Template Selection */}
          <Card className="bg-card border-border">
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="p-2 rounded-lg bg-chart-3/10">
                  <Wand2 className="w-6 h-6 text-chart-3" />
                </div>
                <div>
                  <CardTitle className="font-heading text-xl">Alege un Template</CardTitle>
                  <CardDescription>
                    Selectează un format predefinit pentru articolul tău
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent>
              {loadingTemplates ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {[...Array(4)].map((_, i) => (
                    <div key={i} className="h-32 bg-secondary rounded-lg animate-pulse" />
                  ))}
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {templates.map((template) => (
                    <div
                      key={template.id}
                      className={`p-4 rounded-lg border cursor-pointer transition-all ${
                        selectedTemplate?.id === template.id
                          ? 'border-primary bg-primary/5'
                          : 'border-border bg-secondary hover:border-primary/50'
                      }`}
                      onClick={() => setSelectedTemplate(template)}
                      data-testid={`template-${template.id}`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <h3 className="font-semibold">{template.name}</h3>
                        <div className="flex gap-1">
                          <Badge variant="outline" className="text-xs">
                            {toneLabels[template.default_tone]}
                          </Badge>
                        </div>
                      </div>
                      <p className="text-sm text-muted-foreground mb-3">
                        {template.description}
                      </p>
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <FileText className="w-3 h-3" />
                        <span>{lengthLabels[template.default_length]}</span>
                      </div>
                      {template.keywords_hint && (
                        <p className="text-xs text-primary mt-2">
                          Keywords sugerați: {template.keywords_hint}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Template Form */}
          {selectedTemplate && (
            <Card className="bg-card border-border">
              <CardHeader>
                <CardTitle className="font-heading text-lg flex items-center gap-2">
                  <ChevronRight className="w-5 h-5 text-primary" />
                  Completează detaliile pentru "{selectedTemplate.name}"
                </CardTitle>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleGenerateFromTemplate} className="space-y-6">
                  <div className="p-4 rounded-lg bg-secondary/50 border border-border mb-4">
                    <p className="text-sm text-muted-foreground italic">
                      "{selectedTemplate.prompt_template.replace('{topic}', '<span class="text-primary">[TOPIC]</span>')}"
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="topic">Subiect / Topic *</Label>
                    <Input
                      id="topic"
                      placeholder="Ex: Optimizarea vitezei site-ului WordPress"
                      value={topic}
                      onChange={(e) => setTopic(e.target.value)}
                      className="bg-secondary border-border"
                      required
                      data-testid="template-topic-input"
                    />
                    <p className="text-xs text-muted-foreground">
                      Acest subiect va înlocui {'{topic}'} în template
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="templateKeywords">Cuvinte-cheie (separate prin virgulă) *</Label>
                    <Input
                      id="templateKeywords"
                      placeholder={selectedTemplate.keywords_hint || "Ex: WordPress, viteză, optimizare"}
                      value={templateKeywords}
                      onChange={(e) => setTemplateKeywords(e.target.value)}
                      className="bg-secondary border-border"
                      required
                      data-testid="template-keywords-input"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="templateNiche">Nișă / Industrie *</Label>
                    <Input
                      id="templateNiche"
                      placeholder="Ex: Web Development, Marketing"
                      value={templateNiche}
                      onChange={(e) => setTemplateNiche(e.target.value)}
                      className="bg-secondary border-border"
                      required
                      data-testid="template-niche-input"
                    />
                  </div>

                  <div className="flex gap-2 p-3 rounded-lg bg-primary/5 border border-primary/20">
                    <div className="text-sm">
                      <span className="text-muted-foreground">Setări template: </span>
                      <span className="font-medium">{toneLabels[selectedTemplate.default_tone]}</span>
                      <span className="text-muted-foreground"> • </span>
                      <span className="font-medium">{lengthLabels[selectedTemplate.default_length]}</span>
                    </div>
                  </div>

                  <Button 
                    type="submit" 
                    className="w-full bg-primary text-primary-foreground hover:bg-primary/90 neon-glow-hover h-12"
                    disabled={loading}
                    data-testid="generate-from-template-submit"
                  >
                    {loading ? (
                      <>
                        <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                        Se generează articolul... (poate dura 30-60s)
                      </>
                    ) : (
                      <>
                        <Wand2 className="w-4 h-4 mr-2" />
                        Generează din Template
                      </>
                    )}
                  </Button>
                </form>
              </CardContent>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
