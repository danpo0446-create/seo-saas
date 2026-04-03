import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { 
  Key, Eye, EyeOff, Save, Check, AlertCircle, ExternalLink,
  Sparkles, Brain, Mail, Image, HelpCircle, Copy, CheckCircle,
  Facebook, Linkedin
} from "lucide-react";
import axios from "axios";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const ApiKeysPage = () => {
  const [loading, setLoading] = useState(true);
  const [apiKeys, setApiKeys] = useState(null);
  const [showKeys, setShowKeys] = useState({});
  const [keyInputs, setKeyInputs] = useState({
    openai_key: "",
    gemini_key: "",
    resend_key: "",
    sendgrid_key: "",
    pexels_key: "",
    facebook_app_id: "",
    facebook_app_secret: "",
    linkedin_client_id: "",
    linkedin_client_secret: ""
  });
  const [savingKeys, setSavingKeys] = useState(false);
  const [copiedKey, setCopiedKey] = useState(null);

  useEffect(() => {
    fetchApiKeys();
  }, []);

  const fetchApiKeys = async () => {
    try {
      const token = localStorage.getItem("token");
      const headers = { Authorization: `Bearer ${token}` };
      
      const res = await axios.get(`${API}/saas/api-keys`, { headers });
      setApiKeys(res.data);
    } catch (error) {
      console.error("Error fetching API keys:", error);
      toast.error("Eroare la incarcarea cheilor API");
    } finally {
      setLoading(false);
    }
  };

  const saveApiKeys = async () => {
    setSavingKeys(true);
    try {
      const token = localStorage.getItem("token");
      const headers = { Authorization: `Bearer ${token}` };
      
      // Only send non-empty keys
      const keysToSave = {};
      Object.entries(keyInputs).forEach(([key, value]) => {
        if (value.trim()) {
          keysToSave[key] = value.trim();
        }
      });
      
      if (Object.keys(keysToSave).length === 0) {
        toast.error("Introdu cel putin o cheie");
        return;
      }
      
      await axios.put(`${API}/saas/api-keys`, keysToSave, { headers });
      toast.success("Cheile API au fost salvate!");
      setKeyInputs({
        openai_key: "",
        gemini_key: "",
        resend_key: "",
        sendgrid_key: "",
        pexels_key: "",
        facebook_app_id: "",
        facebook_app_secret: "",
        linkedin_client_id: "",
        linkedin_client_secret: ""
      });
      fetchApiKeys();
    } catch (error) {
      toast.error("Eroare la salvarea cheilor");
    } finally {
      setSavingKeys(false);
    }
  };

  const toggleShowKey = (keyName) => {
    setShowKeys(prev => ({ ...prev, [keyName]: !prev[keyName] }));
  };

  const copyToClipboard = (text, keyName) => {
    navigator.clipboard.writeText(text);
    setCopiedKey(keyName);
    setTimeout(() => setCopiedKey(null), 2000);
  };

  const apiKeyConfigs = [
    {
      id: "openai",
      name: "OpenAI",
      key: "openai_key",
      icon: Sparkles,
      color: "text-green-500",
      bgColor: "bg-green-500/10",
      description: "Pentru generarea articolelor cu GPT-4",
      instructions: [
        "Mergi la platform.openai.com",
        "Creaza un cont sau logheaza-te",
        "Click pe 'API Keys' din meniul din stanga",
        "Click pe 'Create new secret key'",
        "Copiaza cheia (incepe cu 'sk-')",
        "Adauga fonduri in sectiunea Billing (minim $5)"
      ],
      link: "https://platform.openai.com/api-keys",
      pricing: "~$0.01 per 1000 tokeni (GPT-4)"
    },
    {
      id: "gemini",
      name: "Google Gemini",
      key: "gemini_key",
      icon: Brain,
      color: "text-blue-500",
      bgColor: "bg-blue-500/10",
      description: "Alternativa la OpenAI pentru generare continut",
      instructions: [
        "Mergi la aistudio.google.com",
        "Logheaza-te cu contul Google",
        "Click pe 'Get API Key'",
        "Selecteaza sau creaza un proiect Google Cloud",
        "Copiaza cheia API generata"
      ],
      link: "https://aistudio.google.com/app/apikey",
      pricing: "Gratuit pana la 60 requesturi/minut"
    },
    {
      id: "resend",
      name: "Resend (Email)",
      key: "resend_key",
      icon: Mail,
      color: "text-purple-500",
      bgColor: "bg-purple-500/10",
      description: "Pentru trimiterea emailurilor de outreach backlinks",
      instructions: [
        "Mergi la resend.com si creaza cont",
        "Verifica domeniul tau de email (DNS records)",
        "Din Dashboard, click pe 'API Keys'",
        "Click pe 'Create API Key'",
        "Copiaza cheia (incepe cu 're_')"
      ],
      link: "https://resend.com/api-keys",
      pricing: "3,000 emailuri/luna GRATUIT, apoi $20/luna"
    },
    {
      id: "sendgrid",
      name: "SendGrid (Email)",
      key: "sendgrid_key",
      icon: Mail,
      color: "text-blue-400",
      bgColor: "bg-blue-400/10",
      description: "Alternativa pentru emailuri outreach",
      instructions: [
        "Mergi la sendgrid.com si creaza cont",
        "Verifica adresa de email",
        "Din Settings > API Keys",
        "Click pe 'Create API Key'",
        "Selecteaza 'Full Access' sau 'Restricted Access'",
        "Copiaza cheia (incepe cu 'SG.')"
      ],
      link: "https://app.sendgrid.com/settings/api_keys",
      pricing: "100 emailuri/zi GRATUIT"
    },
    {
      id: "pexels",
      name: "Pexels (Imagini)",
      key: "pexels_key",
      icon: Image,
      color: "text-teal-500",
      bgColor: "bg-teal-500/10",
      description: "Pentru imagini gratuite in articole",
      instructions: [
        "Mergi la pexels.com/api",
        "Creaza un cont gratuit",
        "Confirma emailul",
        "Din 'Your API Key', copiaza cheia"
      ],
      link: "https://www.pexels.com/api/new/",
      pricing: "GRATUIT - 200 requesturi/ora"
    },
    {
      id: "facebook",
      name: "Facebook App",
      key: "facebook_app_id",
      secondKey: "facebook_app_secret",
      icon: Facebook,
      color: "text-blue-600",
      bgColor: "bg-blue-600/10",
      description: "Pentru postare automata pe pagini Facebook",
      instructions: [
        "1. Mergi la developers.facebook.com/apps/create/",
        "2. Selecteaza 'Manage everything on your Page' din lista",
        "3. Click Next, pune un nume aplicatiei (ex: SEO Automation)",
        "4. Selecteaza Business Portfolio sau creaza unul nou",
        "5. Dupa creare, mergi la App Settings > Basic",
        "6. Copiaza App ID si App Secret",
        "7. La 'App Domains' adauga: saas.seamanshelp.com",
        "8. La Facebook Login > Settings > Valid OAuth Redirect URIs adauga:",
        "   https://saas.seamanshelp.com/api/social/facebook/callback",
        "9. Pune aplicatia in modul Live (toggle sus-dreapta)"
      ],
      link: "https://developers.facebook.com/apps/create/",
      pricing: "GRATUIT",
      hasTwoFields: true,
      field1Label: "App ID",
      field2Label: "App Secret"
    },
    {
      id: "linkedin",
      name: "LinkedIn App",
      key: "linkedin_client_id",
      secondKey: "linkedin_client_secret",
      icon: Linkedin,
      color: "text-blue-700",
      bgColor: "bg-blue-700/10",
      description: "Pentru postare automata pe profilul LinkedIn",
      instructions: [
        "Mergi la linkedin.com/developers",
        "Click pe 'Create App'",
        "Completeaza detaliile aplicatiei",
        "In tab-ul 'Auth', adauga Redirect URL: https://saas.seamanshelp.com/api/social/linkedin/callback",
        "Solicita acces la produsul 'Share on LinkedIn' si 'Sign In with LinkedIn'",
        "Din tab-ul 'Auth', copiaza Client ID si Client Secret"
      ],
      link: "https://www.linkedin.com/developers/apps/new",
      pricing: "GRATUIT",
      hasTwoFields: true,
      field1Label: "Client ID",
      field2Label: "Client Secret"
    }
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#00E676]"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="api-keys-page">
      <div>
        <h1 className="text-3xl font-bold text-white flex items-center gap-3">
          <Key className="w-8 h-8 text-[#00E676]" />
          Chei API (BYOAK)
        </h1>
        <p className="text-[#71717A] mt-1">
          Configureaza-ti propriile chei API pentru serviciile externe
        </p>
      </div>

      {/* Info Banner */}
      <Card className="bg-[#00E676]/5 border-[#00E676]/20">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <HelpCircle className="w-5 h-5 text-[#00E676] mt-0.5" />
            <div>
              <p className="text-white font-medium">De ce am nevoie de chei API proprii?</p>
              <p className="text-[#A1A1AA] text-sm mt-1">
                Folosind propriile tale chei API, platesti direct furnizorilor (OpenAI, Resend, etc.) 
                pentru utilizarea ta. Asta iti ofera control total asupra costurilor si nu depinzi de limitele noastre.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Current Keys Status */}
      <Card className="bg-[#0A0A0A] border-[#262626]">
        <CardHeader>
          <CardTitle className="text-white">Cheile tale configurate</CardTitle>
          <CardDescription className="text-[#71717A]">
            Status-ul cheilor API salvate
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {apiKeyConfigs.map((config) => {
              const hasKey = apiKeys?.[`has_${config.key}`];
              return (
                <div
                  key={config.id}
                  className={`p-4 rounded-lg border ${hasKey ? 'border-[#00E676]/30 bg-[#00E676]/5' : 'border-[#262626] bg-[#171717]'}`}
                >
                  <div className="flex items-center gap-2 mb-2">
                    <config.icon className={`w-5 h-5 ${config.color}`} />
                    <span className="text-white font-medium text-sm">{config.name}</span>
                  </div>
                  {hasKey ? (
                    <Badge className="bg-[#00E676]/10 text-[#00E676]">
                      <Check className="w-3 h-3 mr-1" /> Configurat
                    </Badge>
                  ) : (
                    <Badge className="bg-[#262626] text-[#71717A]">
                      Neconfigurat
                    </Badge>
                  )}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* API Keys Configuration */}
      <Tabs defaultValue="openai" className="w-full">
        <TabsList className="bg-[#171717] border border-[#262626] flex-wrap h-auto p-1">
          {apiKeyConfigs.map((config) => (
            <TabsTrigger 
              key={config.id}
              value={config.id} 
              className="data-[state=active]:bg-[#00E676] data-[state=active]:text-black flex items-center gap-2"
            >
              <config.icon className="w-4 h-4" />
              {config.name}
            </TabsTrigger>
          ))}
        </TabsList>

        {apiKeyConfigs.map((config) => (
          <TabsContent key={config.id} value={config.id} className="mt-6">
            <div className="grid md:grid-cols-2 gap-6">
              {/* Instructions Card */}
              <Card className="bg-[#0A0A0A] border-[#262626]">
                <CardHeader>
                  <CardTitle className="text-white flex items-center gap-2">
                    <config.icon className={`w-5 h-5 ${config.color}`} />
                    Cum obtin cheia {config.name}?
                  </CardTitle>
                  <CardDescription className="text-[#71717A]">
                    {config.description}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <ol className="space-y-3">
                    {config.instructions.map((step, index) => (
                      <li key={index} className="flex gap-3">
                        <span className={`w-6 h-6 rounded-full ${config.bgColor} ${config.color} flex items-center justify-center text-sm font-medium shrink-0`}>
                          {index + 1}
                        </span>
                        <span className="text-[#A1A1AA]">{step}</span>
                      </li>
                    ))}
                  </ol>
                  
                  <div className="pt-4 border-t border-[#262626] space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-[#71717A] text-sm">Pret estimat:</span>
                      <span className="text-white text-sm">{config.pricing}</span>
                    </div>
                    <Button
                      variant="outline"
                      className="w-full border-[#262626] hover:border-[#00E676] hover:text-[#00E676]"
                      onClick={() => window.open(config.link, '_blank')}
                    >
                      <ExternalLink className="w-4 h-4 mr-2" />
                      Deschide {config.name}
                    </Button>
                  </div>
                </CardContent>
              </Card>

              {/* Input Card */}
              <Card className="bg-[#0A0A0A] border-[#262626]">
                <CardHeader>
                  <CardTitle className="text-white">Configureaza cheia</CardTitle>
                  <CardDescription className="text-[#71717A]">
                    Introdu cheia API pentru {config.name}
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {apiKeys?.[`has_${config.key}`] && (
                    <div className="p-3 rounded-lg bg-[#00E676]/10 border border-[#00E676]/20">
                      <div className="flex items-center gap-2 text-[#00E676]">
                        <CheckCircle className="w-4 h-4" />
                        <span className="text-sm font-medium">Cheie configurata</span>
                      </div>
                      <p className="text-[#A1A1AA] text-sm mt-1">
                        Ai deja o cheie salvata. Introdu una noua pentru a o inlocui.
                      </p>
                    </div>
                  )}
                  
                  {config.hasTwoFields ? (
                    <>
                      <div className="space-y-2">
                        <Label className="text-[#A1A1AA]">{config.field1Label}</Label>
                        <div className="relative">
                          <Input
                            type={showKeys[config.key] ? "text" : "password"}
                            placeholder={`Introdu ${config.field1Label}...`}
                            value={keyInputs[config.key]}
                            onChange={(e) => setKeyInputs(prev => ({
                              ...prev,
                              [config.key]: e.target.value
                            }))}
                            className="bg-[#171717] border-[#262626] text-white pr-10"
                          />
                          <button
                            type="button"
                            onClick={() => toggleShowKey(config.key)}
                            className="absolute right-3 top-1/2 -translate-y-1/2 text-[#71717A] hover:text-white"
                          >
                            {showKeys[config.key] ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                          </button>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <Label className="text-[#A1A1AA]">{config.field2Label}</Label>
                        <div className="relative">
                          <Input
                            type={showKeys[config.secondKey] ? "text" : "password"}
                            placeholder={`Introdu ${config.field2Label}...`}
                            value={keyInputs[config.secondKey]}
                            onChange={(e) => setKeyInputs(prev => ({
                              ...prev,
                              [config.secondKey]: e.target.value
                            }))}
                            className="bg-[#171717] border-[#262626] text-white pr-10"
                          />
                          <button
                            type="button"
                            onClick={() => toggleShowKey(config.secondKey)}
                            className="absolute right-3 top-1/2 -translate-y-1/2 text-[#71717A] hover:text-white"
                          >
                            {showKeys[config.secondKey] ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                          </button>
                        </div>
                      </div>
                      <Button
                        onClick={saveApiKeys}
                        disabled={savingKeys || !keyInputs[config.key] || !keyInputs[config.secondKey]}
                        className="w-full bg-[#00E676] text-black hover:bg-[#00E676]/90"
                      >
                        <Save className="w-4 h-4 mr-2" />
                        {savingKeys ? "Se salveaza..." : "Salveaza Cheile"}
                      </Button>
                    </>
                  ) : (
                    <>
                      <div className="space-y-2">
                        <Label className="text-[#A1A1AA]">Cheie API {config.name}</Label>
                        <div className="relative">
                          <Input
                            type={showKeys[config.key] ? "text" : "password"}
                            placeholder={`Introdu cheia ${config.name}...`}
                            value={keyInputs[config.key]}
                            onChange={(e) => setKeyInputs(prev => ({
                              ...prev,
                              [config.key]: e.target.value
                            }))}
                            className="bg-[#171717] border-[#262626] text-white pr-10"
                          />
                          <button
                            type="button"
                            onClick={() => toggleShowKey(config.key)}
                            className="absolute right-3 top-1/2 -translate-y-1/2 text-[#71717A] hover:text-white"
                          >
                            {showKeys[config.key] ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                          </button>
                        </div>
                      </div>
                      <Button
                        onClick={saveApiKeys}
                        disabled={savingKeys || !keyInputs[config.key]}
                        className="w-full bg-[#00E676] text-black hover:bg-[#00E676]/90"
                      >
                        <Save className="w-4 h-4 mr-2" />
                        {savingKeys ? "Se salveaza..." : "Salveaza Cheia"}
                      </Button>
                    </>
                  )}
                  
                  <div className="p-3 rounded-lg bg-[#171717] border border-[#262626]">
                    <div className="flex items-start gap-2">
                      <AlertCircle className="w-4 h-4 text-yellow-500 mt-0.5" />
                      <p className="text-[#A1A1AA] text-sm">
                        Cheile tale sunt stocate securizat. Nu le partajam cu nimeni.
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        ))}
      </Tabs>

      {/* FAQ */}
      <Card className="bg-[#0A0A0A] border-[#262626]">
        <CardHeader>
          <CardTitle className="text-white">Intrebari Frecvente</CardTitle>
        </CardHeader>
        <CardContent>
          <Accordion type="single" collapsible className="w-full">
            <AccordionItem value="item-1" className="border-[#262626]">
              <AccordionTrigger className="text-white hover:text-[#00E676]">
                Ce se intampla daca nu am chei API configurate?
              </AccordionTrigger>
              <AccordionContent className="text-[#A1A1AA]">
                Fara chei API proprii, unele functii vor fi limitate sau nu vor functiona. 
                De exemplu, nu vei putea genera articole cu AI sau trimite emailuri de outreach.
              </AccordionContent>
            </AccordionItem>
            <AccordionItem value="item-2" className="border-[#262626]">
              <AccordionTrigger className="text-white hover:text-[#00E676]">
                Sunt cheile mele in siguranta?
              </AccordionTrigger>
              <AccordionContent className="text-[#A1A1AA]">
                Da! Toate cheile API sunt criptate inainte de a fi salvate in baza de date. 
                Noi nu avem acces la cheile tale in format text clar.
              </AccordionContent>
            </AccordionItem>
            <AccordionItem value="item-3" className="border-[#262626]">
              <AccordionTrigger className="text-white hover:text-[#00E676]">
                Ce cheie de email sa aleg - Resend sau SendGrid?
              </AccordionTrigger>
              <AccordionContent className="text-[#A1A1AA]">
                <strong>Resend</strong> - Mai simplu de configurat, 3,000 emailuri/luna gratuit. Recomandat pentru inceput.<br/>
                <strong>SendGrid</strong> - Mai complex, dar 100 emailuri/zi gratuit pentru totdeauna. Bun pentru volum mic constant.
              </AccordionContent>
            </AccordionItem>
            <AccordionItem value="item-4" className="border-[#262626]">
              <AccordionTrigger className="text-white hover:text-[#00E676]">
                Cat costa sa folosesc aceste servicii?
              </AccordionTrigger>
              <AccordionContent className="text-[#A1A1AA]">
                <ul className="list-disc pl-4 space-y-1">
                  <li><strong>OpenAI:</strong> ~$0.01 per 1000 tokeni - un articol costa ~$0.05-0.10</li>
                  <li><strong>Gemini:</strong> Gratuit pana la 60 req/min</li>
                  <li><strong>Resend:</strong> 3,000 emailuri/luna gratuit</li>
                  <li><strong>SendGrid:</strong> 100 emailuri/zi gratuit</li>
                  <li><strong>Pexels:</strong> Complet gratuit</li>
                </ul>
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </CardContent>
      </Card>
    </div>
  );
};

export default ApiKeysPage;
