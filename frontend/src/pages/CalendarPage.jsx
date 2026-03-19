import { useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from '@/contexts/AuthContext';
import { useSite } from '@/contexts/SiteContext';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Calendar } from '@/components/ui/calendar';
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
  Calendar as CalendarIcon, 
  PlusCircle, 
  Trash2,
  Loader2,
  Sparkles,
  FileText
} from 'lucide-react';
import { format, parseISO, isSameDay } from 'date-fns';
import { ro } from 'date-fns/locale';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const statusColors = {
  planned: 'bg-blue-500/10 text-blue-500 border-blue-500/20',
  in_progress: 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20',
  completed: 'bg-green-500/10 text-green-500 border-green-500/20',
};

export default function CalendarPage() {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [dialogOpen, setDialogOpen] = useState(false);
  const [newEntry, setNewEntry] = useState({ title: '', keywords: '', scheduled_date: '' });
  const [niche, setNiche] = useState('');
  const { getAuthHeaders } = useAuth();
  const { currentSiteId, currentSite } = useSite();

  useEffect(() => {
    fetchEntries();
  }, [currentSiteId]);

  const fetchEntries = async () => {
    try {
      const params = currentSiteId ? { site_id: currentSiteId } : {};
      const response = await axios.get(`${API}/calendar`, { headers: getAuthHeaders(), params });
      setEntries(response.data);
    } catch (error) {
      console.error('Failed to fetch calendar:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddEntry = async (e) => {
    e.preventDefault();
    try {
      const keywords = newEntry.keywords.split(',').map(k => k.trim()).filter(k => k);
      await axios.post(`${API}/calendar`, {
        title: newEntry.title,
        keywords,
        scheduled_date: newEntry.scheduled_date,
        status: 'planned',
        site_id: currentSiteId
      }, { headers: getAuthHeaders() });
      
      toast.success('Intrare adăugată în calendar');
      setDialogOpen(false);
      setNewEntry({ title: '', keywords: '', scheduled_date: '' });
      fetchEntries();
    } catch (error) {
      toast.error('Eroare la adăugare');
    }
  };

  const handleGenerate90Days = async () => {
    if (!niche.trim()) {
      toast.error('Introdu o nișă pentru generare');
      return;
    }
    
    if (!currentSiteId) {
      toast.error('Selectează un site WordPress din meniul de sus');
      return;
    }
    
    setGenerating(true);
    try {
      await axios.post(`${API}/calendar/generate-90-days?niche=${encodeURIComponent(niche)}&site_id=${currentSiteId}`, {}, { 
        headers: getAuthHeaders() 
      });
      toast.success('Calendar 90 zile generat cu succes!');
      fetchEntries();
      setNiche('');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Eroare la generare');
    } finally {
      setGenerating(false);
    }
  };

  const handleDelete = async (id) => {
    try {
      await axios.delete(`${API}/calendar/${id}`, { headers: getAuthHeaders() });
      toast.success('Intrare ștearsă');
      fetchEntries();
    } catch (error) {
      toast.error('Eroare la ștergere');
    }
  };

  const getEntriesForDate = (date) => {
    return entries.filter(e => {
      const entryDate = parseISO(e.scheduled_date);
      return isSameDay(entryDate, date);
    });
  };

  const selectedEntries = getEntriesForDate(selectedDate);

  const datesWithEntries = entries.map(e => parseISO(e.scheduled_date));

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-8 bg-secondary rounded w-48" />
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="h-96 bg-secondary rounded-lg" />
          <div className="h-96 bg-secondary rounded-lg" />
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8" data-testid="calendar-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="font-heading text-3xl font-bold">Calendar Editorial</h1>
          <p className="text-muted-foreground mt-1">
            Planifică conținut pentru următoarele 90 de zile
          </p>
        </div>
        <div className="flex gap-2">
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="outline" className="border-border" data-testid="add-entry-button">
                <PlusCircle className="w-4 h-4 mr-2" />
                Adaugă Manual
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-card border-border">
              <DialogHeader>
                <DialogTitle>Adaugă Intrare</DialogTitle>
                <DialogDescription>
                  Planifică un articol nou în calendar
                </DialogDescription>
              </DialogHeader>
              <form onSubmit={handleAddEntry} className="space-y-4">
                <div className="space-y-2">
                  <Label>Titlu articol</Label>
                  <Input
                    value={newEntry.title}
                    onChange={(e) => setNewEntry({...newEntry, title: e.target.value})}
                    className="bg-secondary border-border"
                    required
                    data-testid="entry-title-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Cuvinte-cheie</Label>
                  <Input
                    value={newEntry.keywords}
                    onChange={(e) => setNewEntry({...newEntry, keywords: e.target.value})}
                    placeholder="Separate prin virgulă"
                    className="bg-secondary border-border"
                    data-testid="entry-keywords-input"
                  />
                </div>
                <div className="space-y-2">
                  <Label>Data programată</Label>
                  <Input
                    type="date"
                    value={newEntry.scheduled_date}
                    onChange={(e) => setNewEntry({...newEntry, scheduled_date: e.target.value})}
                    className="bg-secondary border-border"
                    required
                    data-testid="entry-date-input"
                  />
                </div>
                <Button type="submit" className="w-full bg-primary text-primary-foreground">
                  Adaugă
                </Button>
              </form>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {/* Generate 90 Days */}
      <Card className="bg-card border-border">
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-primary/10">
              <Sparkles className="w-5 h-5 text-primary" />
            </div>
            <div>
              <CardTitle className="font-heading text-lg">Generare Automată 90 Zile</CardTitle>
              <CardDescription>
                Lasă AI-ul să creeze un calendar editorial complet pentru 3 luni
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4">
            <Input
              placeholder="Introdu nișa (ex: Marketing Digital)"
              value={niche}
              onChange={(e) => setNiche(e.target.value)}
              className="bg-secondary border-border flex-1"
              data-testid="generate-niche-input"
            />
            <Button
              onClick={handleGenerate90Days}
              disabled={generating}
              className="bg-primary text-primary-foreground hover:bg-primary/90"
              data-testid="generate-90-days-button"
            >
              {generating ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Se generează...
                </>
              ) : (
                <>
                  <CalendarIcon className="w-4 h-4 mr-2" />
                  Generează 90 Zile
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Calendar Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Calendar */}
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="font-heading text-lg">Calendar</CardTitle>
          </CardHeader>
          <CardContent className="flex justify-center">
            <Calendar
              mode="single"
              selected={selectedDate}
              onSelect={(date) => date && setSelectedDate(date)}
              locale={ro}
              className="rounded-md"
              modifiers={{
                hasEntry: datesWithEntries
              }}
              modifiersStyles={{
                hasEntry: {
                  backgroundColor: 'hsl(var(--primary) / 0.2)',
                  borderRadius: '50%'
                }
              }}
            />
          </CardContent>
        </Card>

        {/* Selected Date Entries */}
        <Card className="bg-card border-border">
          <CardHeader>
            <CardTitle className="font-heading text-lg">
              {format(selectedDate, 'dd MMMM yyyy', { locale: ro })}
            </CardTitle>
            <CardDescription>
              {selectedEntries.length} articol(e) programat(e)
            </CardDescription>
          </CardHeader>
          <CardContent>
            {selectedEntries.length === 0 ? (
              <div className="text-center py-8">
                <FileText className="w-10 h-10 text-muted-foreground mx-auto mb-3" />
                <p className="text-sm text-muted-foreground">
                  Nicio intrare pentru această dată
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {selectedEntries.map((entry) => (
                  <div 
                    key={entry.id}
                    className="p-4 rounded-lg bg-secondary border border-border"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <Badge className={statusColors[entry.status]}>
                            {entry.status === 'planned' && 'Planificat'}
                            {entry.status === 'in_progress' && 'În lucru'}
                            {entry.status === 'completed' && 'Completat'}
                          </Badge>
                        </div>
                        <h4 className="font-medium mb-2">{entry.title}</h4>
                        <div className="flex flex-wrap gap-1">
                          {entry.keywords.slice(0, 3).map((kw, i) => (
                            <span 
                              key={i}
                              className="text-xs px-2 py-0.5 rounded bg-accent text-muted-foreground"
                            >
                              {kw}
                            </span>
                          ))}
                        </div>
                      </div>
                      <Button
                        variant="ghost"
                        size="icon"
                        onClick={() => handleDelete(entry.id)}
                        className="text-muted-foreground hover:text-destructive"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* All Entries List */}
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="font-heading text-lg">
            Toate Intrările ({entries.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {entries.length === 0 ? (
            <div className="text-center py-8">
              <CalendarIcon className="w-10 h-10 text-muted-foreground mx-auto mb-3" />
              <p className="text-muted-foreground">
                Calendarul este gol. Generează un plan de 90 zile!
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Data</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Titlu</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-muted-foreground">Status</th>
                    <th className="text-right py-3 px-4 text-sm font-medium text-muted-foreground">Acțiuni</th>
                  </tr>
                </thead>
                <tbody>
                  {entries.slice(0, 20).map((entry) => (
                    <tr 
                      key={entry.id}
                      className="border-b border-border/50 hover:bg-secondary/50 transition-colors"
                    >
                      <td className="py-3 px-4 font-mono text-sm">
                        {format(parseISO(entry.scheduled_date), 'dd.MM.yyyy')}
                      </td>
                      <td className="py-3 px-4">{entry.title}</td>
                      <td className="py-3 px-4">
                        <Badge className={statusColors[entry.status]}>
                          {entry.status === 'planned' && 'Planificat'}
                          {entry.status === 'in_progress' && 'În lucru'}
                          {entry.status === 'completed' && 'Completat'}
                        </Badge>
                      </td>
                      <td className="py-3 px-4 text-right">
                        <Button
                          variant="ghost"
                          size="icon"
                          onClick={() => handleDelete(entry.id)}
                          className="text-muted-foreground hover:text-destructive"
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {entries.length > 20 && (
                <p className="text-center text-sm text-muted-foreground mt-4">
                  Afișate 20 din {entries.length} intrări
                </p>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
