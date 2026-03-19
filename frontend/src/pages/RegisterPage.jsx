import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { toast } from 'sonner';
import { Zap, Mail, Lock, User } from 'lucide-react';

export default function RegisterPage() {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (password.length < 6) {
      toast.error('Parola trebuie să aibă cel puțin 6 caractere');
      return;
    }
    setLoading(true);
    try {
      await register(name, email, password);
      toast.success('Cont creat cu succes!');
      navigate('/dashboard');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Eroare la înregistrare');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="absolute inset-0 grid-bg opacity-30" />
      
      <Card className="w-full max-w-md relative z-10 bg-card/80 backdrop-blur-xl border-border">
        <CardHeader className="text-center space-y-4">
          <div className="mx-auto w-14 h-14 rounded-xl bg-primary flex items-center justify-center neon-glow">
            <Zap className="w-8 h-8 text-primary-foreground" />
          </div>
          <div>
            <CardTitle className="font-heading text-2xl">Creează cont</CardTitle>
            <CardDescription className="text-muted-foreground">
              Începe să automatizezi SEO-ul în câteva minute
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Nume</Label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  id="name"
                  type="text"
                  placeholder="Numele tău"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="pl-10 bg-secondary border-border"
                  required
                  data-testid="register-name-input"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  id="email"
                  type="email"
                  placeholder="email@exemplu.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="pl-10 bg-secondary border-border"
                  required
                  data-testid="register-email-input"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Parolă</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  id="password"
                  type="password"
                  placeholder="Minim 6 caractere"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="pl-10 bg-secondary border-border"
                  required
                  data-testid="register-password-input"
                />
              </div>
            </div>
            <Button 
              type="submit" 
              className="w-full bg-primary text-primary-foreground hover:bg-primary/90 neon-glow-hover"
              disabled={loading}
              data-testid="register-submit-button"
            >
              {loading ? 'Se creează contul...' : 'Creează cont'}
            </Button>
          </form>
          <p className="mt-6 text-center text-sm text-muted-foreground">
            Ai deja cont?{' '}
            <Link to="/login" className="text-primary hover:underline" data-testid="login-link">
              Conectează-te
            </Link>
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
