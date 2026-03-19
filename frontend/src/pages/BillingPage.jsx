import { useState, useEffect } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  CreditCard, Package, Key, Check, AlertCircle, Loader2, 
  ExternalLink, Eye, EyeOff, Save, Trash2, Shield,
  FileText, Globe, Calendar, Zap, ArrowUpRight
} from "lucide-react";
import axios from "axios";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const BillingPage = () => {
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(true);
  const [subscription, setSubscription] = useState(null);
  const [usage, setUsage] = useState(null);
  const [apiKeys, setApiKeys] = useState(null);
  const [showKeys, setShowKeys] = useState({});
  const [keyInputs, setKeyInputs] = useState({
    openai_key: "",
    gemini_key: "",
    resend_key: "",
    pexels_key: ""
  });
  const [savingKeys, setSavingKeys] = useState(false);
  const [checkingPayment, setCheckingPayment] = useState(false);

  useEffect(() => {
    fetchData();
    
    // Check for Stripe redirect
    const sessionId = searchParams.get("session_id");
    if (sessionId) {
      checkPaymentStatus(sessionId);
    }
  }, [searchParams]);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem("token");
      const headers = { Authorization: `Bearer ${token}` };
      
      const [subRes, usageRes, keysRes] = await Promise.all([
        axios.get(`${API}/saas/subscription`, { headers }),
        axios.get(`${API}/saas/subscription/usage`, { headers }),
        axios.get(`${API}/saas/api-keys`, { headers })
      ]);
      
      setSubscription(subRes.data);
      setUsage(usageRes.data);
      setApiKeys(keysRes.data);
    } catch (error) {
      console.error("Error fetching billing data:", error);
      toast.error("Eroare la încărcarea datelor");
    } finally {
      setLoading(false);
    }
  };

  const checkPaymentStatus = async (sessionId) => {
    setCheckingPayment(true);
    let attempts = 0;
    const maxAttempts = 10;
    
    const poll = async () => {
      try {
        const token = localStorage.getItem("token");
        const response = await axios.get(`${API}/saas/checkout/status/${sessionId}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        
        if (response.data.payment_status === "paid") {
          toast.success("Plată procesată cu succes! Planul tău a fost actualizat.");
          fetchData();
          setCheckingPayment(false);
          // Clean URL
          window.history.replaceState({}, document.title, "/billing");
          return;
        }
        
        if (response.data.status === "expired" || attempts >= maxAttempts) {
          toast.error("Plata nu a fost finalizată.");
          setCheckingPayment(false);
          return;
        }
        
        attempts++;
        setTimeout(poll, 2000);
      } catch (error) {
        console.error("Error checking payment:", error);
        setCheckingPayment(false);
      }
    };
    
    poll();
  };

  const handleSaveApiKeys = async () => {
    setSavingKeys(true);
    try {
      const token = localStorage.getItem("token");
      const keysToSave = {};
      
      // Only include keys that have values
      Object.entries(keyInputs).forEach(([key, value]) => {
        if (value.trim()) {
          keysToSave[key] = value.trim();
        }
      });
      
      if (Object.keys(keysToSave).length === 0) {
        toast.warning("Nu ai introdus nicio cheie nouă");
        return;
      }
      
      await axios.put(`${API}/saas/api-keys`, keysToSave, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      toast.success("Cheile API au fost salvate");
      setKeyInputs({ openai_key: "", gemini_key: "", resend_key: "", pexels_key: "" });
      fetchData();
    } catch (error) {
      toast.error("Eroare la salvarea cheilor");
    } finally {
      setSavingKeys(false);
    }
  };

  const getStatusBadge = (status) => {
    const statusConfig = {
      active: { label: "Activ", variant: "default", className: "bg-[#00E676] text-black" },
      trialing: { label: "Trial", variant: "outline", className: "border-yellow-500 text-yellow-500" },
      canceled: { label: "Anulat", variant: "destructive", className: "bg-red-500" },
      expired: { label: "Expirat", variant: "destructive", className: "bg-red-500" },
      past_due: { label: "Plată Restantă", variant: "destructive", className: "bg-orange-500" }
    };
    const config = statusConfig[status] || statusConfig.expired;
    return <Badge className={config.className}>{config.label}</Badge>;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Loader2 className="w-8 h-8 animate-spin text-[#00E676]" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="billing-page">
      {/* Payment Processing Banner */}
      {checkingPayment && (
        <Card className="bg-[#00E676]/10 border-[#00E676]">
          <CardContent className="flex items-center gap-3 py-4">
            <Loader2 className="w-5 h-5 animate-spin text-[#00E676]" />
            <span className="text-[#00E676]">Se verifică plata... Te rugăm să aștepți.</span>
          </CardContent>
        </Card>
      )}

      {/* Trial Banner */}
      {usage?.status === "trialing" && usage?.days_remaining !== null && (
        <Card className="bg-yellow-500/10 border-yellow-500/50">
          <CardContent className="flex items-center justify-between py-4">
            <div className="flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-yellow-500" />
              <span className="text-yellow-500">
                Ai <strong>{usage.days_remaining} zile</strong> rămase din perioada de trial
              </span>
            </div>
            <Link to="/pricing">
              <Button size="sm" className="bg-yellow-500 text-black hover:bg-yellow-500/90">
                Alege un Plan
              </Button>
            </Link>
          </CardContent>
        </Card>
      )}

      {/* Expired Banner */}
      {usage?.status === "expired" && (
        <Card className="bg-red-500/10 border-red-500/50">
          <CardContent className="flex items-center justify-between py-4">
            <div className="flex items-center gap-3">
              <AlertCircle className="w-5 h-5 text-red-500" />
              <span className="text-red-500">
                Perioada de trial a expirat. Alege un plan pentru a continua.
              </span>
            </div>
            <Link to="/pricing">
              <Button size="sm" className="bg-red-500 text-white hover:bg-red-500/90">
                Alege un Plan
              </Button>
            </Link>
          </CardContent>
        </Card>
      )}

      <Tabs defaultValue="subscription" className="space-y-6">
        <TabsList className="bg-[#171717]">
          <TabsTrigger value="subscription" className="data-[state=active]:bg-[#262626]">
            <Package className="w-4 h-4 mr-2" />
            Subscripție
          </TabsTrigger>
          <TabsTrigger value="api-keys" className="data-[state=active]:bg-[#262626]">
            <Key className="w-4 h-4 mr-2" />
            Chei API (BYOAK)
          </TabsTrigger>
        </TabsList>

        {/* Subscription Tab */}
        <TabsContent value="subscription" className="space-y-6">
          <div className="grid md:grid-cols-2 gap-6">
            {/* Current Plan */}
            <Card className="bg-[#0A0A0A] border-[#262626]">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="text-white flex items-center gap-2">
                    <CreditCard className="w-5 h-5 text-[#00E676]" />
                    Planul Actual
                  </CardTitle>
                  {getStatusBadge(usage?.status)}
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="text-center py-4">
                  <div className="text-3xl font-bold text-white mb-1">{usage?.plan_name}</div>
                  {subscription?.current_period_end && (
                    <p className="text-[#71717A] text-sm">
                      {usage?.status === "trialing" ? "Trial expiră" : "Următoarea facturare"}: {" "}
                      {new Date(subscription.current_period_end).toLocaleDateString("ro-RO")}
                    </p>
                  )}
                </div>
                <div className="flex gap-3">
                  <Link to="/pricing" className="flex-1">
                    <Button variant="outline" className="w-full border-[#262626] hover:bg-[#171717]">
                      Schimbă Planul
                    </Button>
                  </Link>
                </div>
              </CardContent>
            </Card>

            {/* Usage Stats */}
            <Card className="bg-[#0A0A0A] border-[#262626]">
              <CardHeader>
                <CardTitle className="text-white flex items-center gap-2">
                  <Zap className="w-5 h-5 text-[#00E676]" />
                  Utilizare Lunară
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Articles Usage */}
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-[#A1A1AA] flex items-center gap-2">
                      <FileText className="w-4 h-4" />
                      Articole Generate
                    </span>
                    <span className="text-white">
                      {usage?.articles_used} / {usage?.articles_limit === -1 ? "∞" : usage?.articles_limit}
                    </span>
                  </div>
                  <Progress 
                    value={usage?.articles_limit === -1 ? 0 : (usage?.articles_used / usage?.articles_limit) * 100} 
                    className="h-2 bg-[#262626]"
                  />
                </div>

                {/* Sites Usage */}
                <div>
                  <div className="flex justify-between text-sm mb-2">
                    <span className="text-[#A1A1AA] flex items-center gap-2">
                      <Globe className="w-4 h-4" />
                      Site-uri WordPress
                    </span>
                    <span className="text-white">
                      {usage?.sites_used} / {usage?.sites_limit === -1 ? "∞" : usage?.sites_limit}
                    </span>
                  </div>
                  <Progress 
                    value={usage?.sites_limit === -1 ? 0 : (usage?.sites_used / usage?.sites_limit) * 100} 
                    className="h-2 bg-[#262626]"
                  />
                </div>

                {/* Status indicators */}
                <div className="flex gap-4 pt-2">
                  <div className="flex items-center gap-2 text-sm">
                    {usage?.can_generate_article ? (
                      <Check className="w-4 h-4 text-[#00E676]" />
                    ) : (
                      <AlertCircle className="w-4 h-4 text-red-500" />
                    )}
                    <span className="text-[#A1A1AA]">Poți genera articole</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    {usage?.can_add_site ? (
                      <Check className="w-4 h-4 text-[#00E676]" />
                    ) : (
                      <AlertCircle className="w-4 h-4 text-red-500" />
                    )}
                    <span className="text-[#A1A1AA]">Poți adăuga site-uri</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Quick Actions */}
          <Card className="bg-[#0A0A0A] border-[#262626]">
            <CardHeader>
              <CardTitle className="text-white">Acțiuni Rapide</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid sm:grid-cols-3 gap-4">
                <Link to="/pricing">
                  <Button variant="outline" className="w-full border-[#262626] hover:bg-[#171717] justify-start">
                    <ArrowUpRight className="w-4 h-4 mr-2" />
                    Upgrade Plan
                  </Button>
                </Link>
                <Button variant="outline" className="border-[#262626] hover:bg-[#171717] justify-start" disabled>
                  <ExternalLink className="w-4 h-4 mr-2" />
                  Portal Facturare
                </Button>
                <Button variant="outline" className="border-[#262626] hover:bg-[#171717] justify-start text-red-400 hover:text-red-400" disabled>
                  <Trash2 className="w-4 h-4 mr-2" />
                  Anulează Subscripția
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* API Keys Tab */}
        <TabsContent value="api-keys" className="space-y-6">
          <Card className="bg-[#0A0A0A] border-[#262626]">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-2">
                <Shield className="w-5 h-5 text-[#00E676]" />
                BYOAK - Bring Your Own API Keys
              </CardTitle>
              <CardDescription className="text-[#71717A]">
                Configurează-ți propriile chei API pentru a folosi serviciile tale personale. 
                Cheile sunt criptate și stocate în siguranță.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* OpenAI Key */}
              <div className="space-y-2">
                <Label className="text-[#A1A1AA]">OpenAI API Key</Label>
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <Input
                      type={showKeys.openai ? "text" : "password"}
                      placeholder={apiKeys?.has_openai_key ? "••••••••••••••••" : "sk-..."}
                      value={keyInputs.openai_key}
                      onChange={(e) => setKeyInputs({ ...keyInputs, openai_key: e.target.value })}
                      className="bg-[#171717] border-[#262626] text-white pr-10"
                    />
                    <button
                      type="button"
                      onClick={() => setShowKeys({ ...showKeys, openai: !showKeys.openai })}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-[#71717A] hover:text-white"
                    >
                      {showKeys.openai ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  {apiKeys?.has_openai_key && (
                    <Badge className="bg-[#00E676]/10 text-[#00E676] border-[#00E676]/20">
                      <Check className="w-3 h-3 mr-1" />
                      Configurat
                    </Badge>
                  )}
                </div>
                <p className="text-xs text-[#525252]">Pentru generare articole cu GPT. Obține de la platform.openai.com</p>
              </div>

              {/* Gemini Key */}
              <div className="space-y-2">
                <Label className="text-[#A1A1AA]">Google Gemini API Key</Label>
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <Input
                      type={showKeys.gemini ? "text" : "password"}
                      placeholder={apiKeys?.has_gemini_key ? "••••••••••••••••" : "AIza..."}
                      value={keyInputs.gemini_key}
                      onChange={(e) => setKeyInputs({ ...keyInputs, gemini_key: e.target.value })}
                      className="bg-[#171717] border-[#262626] text-white pr-10"
                    />
                    <button
                      type="button"
                      onClick={() => setShowKeys({ ...showKeys, gemini: !showKeys.gemini })}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-[#71717A] hover:text-white"
                    >
                      {showKeys.gemini ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  {apiKeys?.has_gemini_key && (
                    <Badge className="bg-[#00E676]/10 text-[#00E676] border-[#00E676]/20">
                      <Check className="w-3 h-3 mr-1" />
                      Configurat
                    </Badge>
                  )}
                </div>
                <p className="text-xs text-[#525252]">Alternativă la OpenAI. Obține de la aistudio.google.com</p>
              </div>

              {/* Resend Key */}
              <div className="space-y-2">
                <Label className="text-[#A1A1AA]">Resend API Key</Label>
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <Input
                      type={showKeys.resend ? "text" : "password"}
                      placeholder={apiKeys?.has_resend_key ? "••••••••••••••••" : "re_..."}
                      value={keyInputs.resend_key}
                      onChange={(e) => setKeyInputs({ ...keyInputs, resend_key: e.target.value })}
                      className="bg-[#171717] border-[#262626] text-white pr-10"
                    />
                    <button
                      type="button"
                      onClick={() => setShowKeys({ ...showKeys, resend: !showKeys.resend })}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-[#71717A] hover:text-white"
                    >
                      {showKeys.resend ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  {apiKeys?.has_resend_key && (
                    <Badge className="bg-[#00E676]/10 text-[#00E676] border-[#00E676]/20">
                      <Check className="w-3 h-3 mr-1" />
                      Configurat
                    </Badge>
                  )}
                </div>
                <p className="text-xs text-[#525252]">Pentru notificări email. Obține de la resend.com</p>
              </div>

              {/* Pexels Key */}
              <div className="space-y-2">
                <Label className="text-[#A1A1AA]">Pexels API Key</Label>
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <Input
                      type={showKeys.pexels ? "text" : "password"}
                      placeholder={apiKeys?.has_pexels_key ? "••••••••••••••••" : "Introdu cheia Pexels"}
                      value={keyInputs.pexels_key}
                      onChange={(e) => setKeyInputs({ ...keyInputs, pexels_key: e.target.value })}
                      className="bg-[#171717] border-[#262626] text-white pr-10"
                    />
                    <button
                      type="button"
                      onClick={() => setShowKeys({ ...showKeys, pexels: !showKeys.pexels })}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-[#71717A] hover:text-white"
                    >
                      {showKeys.pexels ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                  {apiKeys?.has_pexels_key && (
                    <Badge className="bg-[#00E676]/10 text-[#00E676] border-[#00E676]/20">
                      <Check className="w-3 h-3 mr-1" />
                      Configurat
                    </Badge>
                  )}
                </div>
                <p className="text-xs text-[#525252]">Pentru imagini în articole. Obține de la pexels.com/api</p>
              </div>

              <Button 
                onClick={handleSaveApiKeys}
                disabled={savingKeys}
                className="bg-[#00E676] text-black hover:bg-[#00E676]/90"
              >
                {savingKeys ? (
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                ) : (
                  <Save className="w-4 h-4 mr-2" />
                )}
                Salvează Cheile
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default BillingPage;
