import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { toast } from 'sonner';
import { Zap, Mail, Lock, Eye, EyeOff, ArrowLeft } from 'lucide-react';
import axios from 'axios';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  // Forgot password state
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [resetEmail, setResetEmail] = useState('');
  const [resetSending, setResetSending] = useState(false);
  const [resetSent, setResetSent] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(email, password);
      toast.success('Autentificare reușită!');
      navigate('/app/dashboard');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Email sau parolă incorectă');
    } finally {
      setLoading(false);
    }
  };

  const handleForgotPassword = async (e) => {
    e.preventDefault();
    setResetSending(true);
    try {
      await axios.post(`${API}/auth/forgot-password`, { email: resetEmail });
      setResetSent(true);
      toast.success('Email trimis! Verifică inbox-ul.');
    } catch (error) {
      // Show success anyway to prevent email enumeration
      setResetSent(true);
      toast.success('Dacă există un cont cu acest email, vei primi instrucțiuni.');
    } finally {
      setResetSending(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#050505] flex items-center justify-center p-4">
      {/* Background grid */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#1a1a1a_1px,transparent_1px),linear-gradient(to_bottom,#1a1a1a_1px,transparent_1px)] bg-[size:4rem_4rem] opacity-20" />
      
      {/* Back to home */}
      <Link 
        to="/" 
        className="absolute top-6 left-6 flex items-center gap-2 text-[#A1A1AA] hover:text-white transition-colors"
      >
        <ArrowLeft className="w-4 h-4" />
        Înapoi la site
      </Link>

      <Card className="w-full max-w-md relative z-10 bg-[#0A0A0A]/90 backdrop-blur-xl border-[#262626]">
        <CardHeader className="text-center space-y-4">
          <Link to="/" className="mx-auto">
            <div className="w-14 h-14 rounded-xl bg-[#00E676] flex items-center justify-center">
              <Zap className="w-8 h-8 text-black" />
            </div>
          </Link>
          <div>
            <CardTitle className="text-2xl text-white">Bine ai revenit!</CardTitle>
            <CardDescription className="text-[#A1A1AA]">
              Conectează-te pentru a accesa platforma SEO
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email" className="text-[#A1A1AA]">Email</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#71717A]" />
                <Input
                  id="email"
                  type="email"
                  placeholder="email@exemplu.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="pl-10 bg-[#171717] border-[#262626] text-white placeholder:text-[#71717A]"
                  required
                  data-testid="login-email-input"
                />
              </div>
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="password" className="text-[#A1A1AA]">Parolă</Label>
                <button
                  type="button"
                  onClick={() => setShowForgotPassword(true)}
                  className="text-sm text-[#00E676] hover:underline"
                >
                  Am uitat parola
                </button>
              </div>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#71717A]" />
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="pl-10 pr-10 bg-[#171717] border-[#262626] text-white placeholder:text-[#71717A]"
                  required
                  data-testid="login-password-input"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[#71717A] hover:text-white"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
            <Button 
              type="submit" 
              className="w-full bg-[#00E676] text-black hover:bg-[#00E676]/90 font-medium"
              disabled={loading}
              data-testid="login-submit-button"
            >
              {loading ? 'Se conectează...' : 'Conectare'}
            </Button>
          </form>

          <div className="mt-6 pt-6 border-t border-[#262626]">
            <p className="text-center text-sm text-[#A1A1AA]">
              Nu ai cont?{' '}
              <Link to="/register" className="text-[#00E676] hover:underline font-medium" data-testid="register-link">
                Înregistrează-te gratuit
              </Link>
            </p>
            <p className="text-center text-xs text-[#71717A] mt-2">
              7 zile trial gratuit • Fără card de credit
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Forgot Password Dialog */}
      <Dialog open={showForgotPassword} onOpenChange={setShowForgotPassword}>
        <DialogContent className="bg-[#0A0A0A] border-[#262626]">
          <DialogHeader>
            <DialogTitle className="text-white">Resetare parolă</DialogTitle>
            <DialogDescription className="text-[#A1A1AA]">
              {resetSent 
                ? "Verifică email-ul pentru instrucțiuni de resetare."
                : "Introdu adresa de email asociată contului tău."
              }
            </DialogDescription>
          </DialogHeader>
          
          {!resetSent ? (
            <form onSubmit={handleForgotPassword} className="space-y-4">
              <div className="space-y-2">
                <Label className="text-[#A1A1AA]">Email</Label>
                <Input
                  type="email"
                  placeholder="email@exemplu.com"
                  value={resetEmail}
                  onChange={(e) => setResetEmail(e.target.value)}
                  className="bg-[#171717] border-[#262626] text-white"
                  required
                />
              </div>
              <div className="flex gap-3">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowForgotPassword(false)}
                  className="flex-1 border-[#262626]"
                >
                  Anulează
                </Button>
                <Button
                  type="submit"
                  disabled={resetSending}
                  className="flex-1 bg-[#00E676] text-black hover:bg-[#00E676]/90"
                >
                  {resetSending ? "Se trimite..." : "Trimite email"}
                </Button>
              </div>
            </form>
          ) : (
            <div className="space-y-4">
              <div className="p-4 rounded-lg bg-[#00E676]/10 border border-[#00E676]/20">
                <p className="text-[#00E676] text-sm text-center">
                  Dacă există un cont cu adresa <strong>{resetEmail}</strong>, vei primi un email cu instrucțiuni pentru resetarea parolei.
                </p>
              </div>
              <Button
                onClick={() => {
                  setShowForgotPassword(false);
                  setResetSent(false);
                  setResetEmail('');
                }}
                className="w-full bg-[#00E676] text-black hover:bg-[#00E676]/90"
              >
                Închide
              </Button>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Footer */}
      <footer className="absolute bottom-0 left-0 right-0 py-4 px-4 border-t border-[#262626]">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center gap-2 text-xs">
          <div className="flex gap-4 text-[#71717A]">
            <Link to="/terms" className="hover:text-white transition-colors">Termeni</Link>
            <Link to="/privacy" className="hover:text-white transition-colors">Confidențialitate</Link>
            <Link to="/contact" className="hover:text-white transition-colors">Contact</Link>
          </div>
          <p className="text-[#71717A]">
            © {new Date().getFullYear()} SEO Automation
          </p>
        </div>
      </footer>
    </div>
  );
}
