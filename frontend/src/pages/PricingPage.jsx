import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { useAuth } from "@/contexts/AuthContext";
import { 
  Zap, Check, X, ArrowLeft, Sparkles, Crown, Building2, Rocket,
  FileText, Globe, Search, Calendar, Link2, BarChart3, Mail,
  ShoppingCart, Share2, Shield, Clock, Users, Headphones
} from "lucide-react";
import axios from "axios";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const PricingPage = () => {
  const { isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [annual, setAnnual] = useState(false);
  const [loading, setLoading] = useState(false);
  const [currentPlan, setCurrentPlan] = useState(null);

  useEffect(() => {
    if (isAuthenticated) {
      fetchCurrentPlan();
    }
  }, [isAuthenticated]);

  const fetchCurrentPlan = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${API}/saas/subscription/usage`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCurrentPlan(response.data);
    } catch (error) {
      console.error("Error fetching plan:", error);
    }
  };

  const handleSelectPlan = async (planId) => {
    if (!isAuthenticated) {
      navigate("/register");
      return;
    }
    
    if (planId === currentPlan?.plan) {
      return; // Already on this plan
    }

    setLoading(true);
    try {
      const token = localStorage.getItem("token");
      const response = await axios.post(`${API}/saas/checkout`, {
        plan: planId,
        origin_url: window.location.origin,
        billing_period: annual ? "annual" : "monthly"
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Redirect to Stripe checkout
      window.location.href = response.data.url;
    } catch (error) {
      console.error("Checkout error:", error);
      alert("Eroare la procesarea plății. Te rugăm să încerci din nou.");
    } finally {
      setLoading(false);
    }
  };

  const plans = [
    {
      id: "starter",
      name: "Starter",
      description: "Perfect pentru bloggeri și site-uri mici",
      price: 19,
      priceAnnual: 182,
      icon: <Sparkles className="w-6 h-6" />,
      color: "from-blue-500 to-cyan-500",
      features: {
        sites: "1 site WordPress",
        articles: "15 articole/lună",
        keywords: true,
        calendar: true,
        publish: true,
        gsc: false,
        backlinks: false,
        reports: "Basic",
        woocommerce: false,
        social: false,
        audit: false,
        support: "Email"
      }
    },
    {
      id: "pro",
      name: "Pro",
      description: "Ideal pentru freelanceri și afaceri în creștere",
      price: 49,
      priceAnnual: 470,
      popular: true,
      icon: <Crown className="w-6 h-6" />,
      color: "from-[#00E676] to-emerald-400",
      features: {
        sites: "5 site-uri WordPress",
        articles: "50 articole/lună",
        keywords: true,
        calendar: true,
        publish: true,
        gsc: true,
        backlinks: true,
        reports: "Avansat",
        woocommerce: false,
        social: false,
        audit: false,
        support: "Priority"
      }
    },
    {
      id: "agency",
      name: "Agency",
      description: "Pentru agenții și echipe mari",
      price: 99,
      priceAnnual: 950,
      icon: <Building2 className="w-6 h-6" />,
      color: "from-purple-500 to-pink-500",
      features: {
        sites: "20 site-uri WordPress",
        articles: "200 articole/lună",
        keywords: true,
        calendar: true,
        publish: true,
        gsc: true,
        backlinks: true,
        reports: "Complet",
        woocommerce: true,
        social: true,
        audit: true,
        support: "Prioritar 24/7"
      }
    },
    {
      id: "enterprise",
      name: "Enterprise",
      description: "Soluție completă fără limite",
      price: 199,
      priceAnnual: 1910,
      icon: <Rocket className="w-6 h-6" />,
      color: "from-orange-500 to-red-500",
      features: {
        sites: "Nelimitat",
        articles: "Nelimitat",
        keywords: true,
        calendar: true,
        publish: true,
        gsc: true,
        backlinks: true,
        reports: "Complet + Export",
        woocommerce: true,
        social: true,
        audit: true,
        support: "Dedicat + Training"
      }
    }
  ];

  // Calculate monthly equivalent for annual
  const getMonthlyEquivalent = (annualPrice) => Math.round(annualPrice / 12);

  const featureList = [
    { key: "sites", label: "Site-uri WordPress", icon: <Globe className="w-4 h-4" /> },
    { key: "articles", label: "Articole generate/lună", icon: <FileText className="w-4 h-4" /> },
    { key: "keywords", label: "Keyword Research AI", icon: <Search className="w-4 h-4" /> },
    { key: "calendar", label: "Calendar Editorial 90 zile", icon: <Calendar className="w-4 h-4" /> },
    { key: "publish", label: "Publicare Automată", icon: <Zap className="w-4 h-4" /> },
    { key: "gsc", label: "Google Search Console", icon: <BarChart3 className="w-4 h-4" /> },
    { key: "backlinks", label: "Manager Backlinks + Outreach", icon: <Link2 className="w-4 h-4" /> },
    { key: "reports", label: "Rapoarte Performanță", icon: <BarChart3 className="w-4 h-4" /> },
    { key: "woocommerce", label: "Integrare WooCommerce", icon: <ShoppingCart className="w-4 h-4" /> },
    { key: "social", label: "Social Media Posting", icon: <Share2 className="w-4 h-4" /> },
    { key: "audit", label: "Audit SEO Tehnic + AI", icon: <Shield className="w-4 h-4" /> },
    { key: "support", label: "Suport", icon: <Headphones className="w-4 h-4" /> }
  ];

  const renderFeatureValue = (value) => {
    if (value === true) return <Check className="w-5 h-5 text-[#00E676]" />;
    if (value === false) return <X className="w-5 h-5 text-[#525252]" />;
    return <span className="text-white">{value}</span>;
  };

  return (
    <div className="min-h-screen bg-[#050505]" data-testid="pricing-page">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-[#050505]/90 backdrop-blur-md border-b border-[#262626]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <Link to="/" className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-[#00E676] flex items-center justify-center">
                <Zap className="w-5 h-5 text-black" />
              </div>
              <span className="text-xl font-bold text-white">SEO Automation</span>
            </Link>
            <div className="flex items-center gap-3">
              {isAuthenticated ? (
                <Link to="/dashboard">
                  <Button className="bg-[#00E676] text-black hover:bg-[#00E676]/90">
                    Mergi la Dashboard
                  </Button>
                </Link>
              ) : (
                <>
                  <Link to="/login">
                    <Button variant="ghost" className="text-[#A1A1AA] hover:text-white">
                      Autentificare
                    </Button>
                  </Link>
                  <Link to="/register">
                    <Button className="bg-[#00E676] text-black hover:bg-[#00E676]/90">
                      Începe Gratuit
                    </Button>
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Header */}
      <section className="pt-32 pb-12 px-4">
        <div className="max-w-6xl mx-auto text-center">
          <Link to="/" className="inline-flex items-center gap-2 text-[#A1A1AA] hover:text-white mb-6 transition-colors">
            <ArrowLeft className="w-4 h-4" />
            Înapoi la pagina principală
          </Link>
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-4">
            Prețuri Transparente
          </h1>
          <p className="text-xl text-[#A1A1AA] mb-8 max-w-2xl mx-auto">
            Alege planul potrivit pentru nevoile tale. Toate planurile includ 7 zile trial gratuit.
          </p>
          
          {/* Current Plan Badge */}
          {currentPlan && (
            <Badge className="mb-8 bg-[#00E676]/10 text-[#00E676] border-[#00E676]/20 py-2 px-4">
              Planul tău actual: <strong className="ml-1">{currentPlan.plan_name}</strong>
              {currentPlan.status === "trialing" && ` (Trial - ${currentPlan.days_remaining} zile rămase)`}
            </Badge>
          )}
          
          {/* Annual/Monthly Toggle */}
          <div className="flex items-center justify-center gap-4 mt-8">
            <span className={`text-sm ${!annual ? 'text-white font-medium' : 'text-[#71717A]'}`}>Lunar</span>
            <Switch 
              checked={annual} 
              onCheckedChange={setAnnual}
              className="data-[state=checked]:bg-[#00E676]"
            />
            <span className={`text-sm ${annual ? 'text-white font-medium' : 'text-[#71717A]'}`}>
              Anual
              <Badge className="ml-2 bg-[#00E676] text-black text-xs">-20%</Badge>
            </span>
          </div>
        </div>
      </section>

      {/* Plans Grid */}
      <section className="pb-20 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {plans.map((plan) => (
              <Card 
                key={plan.id}
                className={`relative bg-[#0A0A0A] border-[#262626] overflow-hidden transition-all hover:border-[#00E676]/50 ${
                  plan.popular ? 'ring-2 ring-[#00E676] border-[#00E676]' : ''
                } ${currentPlan?.plan === plan.id ? 'ring-2 ring-blue-500 border-blue-500' : ''}`}
                data-testid={`plan-${plan.id}`}
              >
                {plan.popular && (
                  <div className="absolute top-0 left-0 right-0 bg-[#00E676] text-black text-center text-sm py-1 font-medium">
                    Cel Mai Popular
                  </div>
                )}
                {currentPlan?.plan === plan.id && (
                  <div className="absolute top-0 left-0 right-0 bg-blue-500 text-white text-center text-sm py-1 font-medium">
                    Planul Tău Actual
                  </div>
                )}
                <CardHeader className={`text-center ${plan.popular || currentPlan?.plan === plan.id ? 'pt-10' : 'pt-6'}`}>
                  <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${plan.color} mx-auto mb-4 flex items-center justify-center text-white`}>
                    {plan.icon}
                  </div>
                  <CardTitle className="text-white text-2xl">{plan.name}</CardTitle>
                  <CardDescription className="text-[#71717A]">{plan.description}</CardDescription>
                  <div className="mt-4">
                    {annual ? (
                      <>
                        <span className="text-5xl font-bold text-white">€{getMonthlyEquivalent(plan.priceAnnual)}</span>
                        <span className="text-[#71717A]">/lună</span>
                        <div className="mt-1">
                          <span className="text-sm text-[#525252] line-through">€{plan.price * 12}/an</span>
                          <span className="text-sm text-[#00E676] ml-2">€{plan.priceAnnual}/an</span>
                        </div>
                      </>
                    ) : (
                      <>
                        <span className="text-5xl font-bold text-white">€{plan.price}</span>
                        <span className="text-[#71717A]">/lună</span>
                      </>
                    )}
                  </div>
                </CardHeader>
                <CardContent className="pt-6">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between py-2 border-b border-[#262626]">
                      <span className="text-[#A1A1AA] text-sm">Site-uri</span>
                      <span className="text-white font-medium">{plan.features.sites}</span>
                    </div>
                    <div className="flex items-center justify-between py-2 border-b border-[#262626]">
                      <span className="text-[#A1A1AA] text-sm">Articole/lună</span>
                      <span className="text-white font-medium">{plan.features.articles}</span>
                    </div>
                    <div className="flex items-center justify-between py-2 border-b border-[#262626]">
                      <span className="text-[#A1A1AA] text-sm">Google Search Console</span>
                      {renderFeatureValue(plan.features.gsc)}
                    </div>
                    <div className="flex items-center justify-between py-2 border-b border-[#262626]">
                      <span className="text-[#A1A1AA] text-sm">Manager Backlinks</span>
                      {renderFeatureValue(plan.features.backlinks)}
                    </div>
                    <div className="flex items-center justify-between py-2 border-b border-[#262626]">
                      <span className="text-[#A1A1AA] text-sm">WooCommerce</span>
                      {renderFeatureValue(plan.features.woocommerce)}
                    </div>
                    <div className="flex items-center justify-between py-2">
                      <span className="text-[#A1A1AA] text-sm">Suport</span>
                      <span className="text-white text-sm">{plan.features.support}</span>
                    </div>
                  </div>
                </CardContent>
                <CardFooter className="pt-4">
                  <Button 
                    className={`w-full ${
                      currentPlan?.plan === plan.id 
                        ? 'bg-[#262626] text-[#71717A] cursor-not-allowed' 
                        : plan.popular 
                          ? 'bg-[#00E676] text-black hover:bg-[#00E676]/90' 
                          : 'bg-[#171717] text-white hover:bg-[#262626]'
                    }`}
                    onClick={() => handleSelectPlan(plan.id)}
                    disabled={loading || currentPlan?.plan === plan.id}
                    data-testid={`select-plan-${plan.id}`}
                  >
                    {currentPlan?.plan === plan.id ? 'Planul Actual' : loading ? 'Se procesează...' : 'Selectează'}
                  </Button>
                </CardFooter>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Comparison Table */}
      <section className="py-20 px-4 bg-[#0A0A0A]">
        <div className="max-w-7xl mx-auto">
          <h2 className="text-3xl font-bold text-white text-center mb-12">
            Comparație Detaliată
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-[#262626]">
                  <th className="text-left py-4 px-4 text-[#A1A1AA] font-normal">Funcționalitate</th>
                  {plans.map(plan => (
                    <th key={plan.id} className="text-center py-4 px-4">
                      <span className="text-white font-semibold">{plan.name}</span>
                      <div className="text-[#00E676] text-sm mt-1">€{plan.price}/lună</div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {featureList.map((feature, index) => (
                  <tr key={feature.key} className={index % 2 === 0 ? 'bg-[#0A0A0A]' : 'bg-[#050505]'}>
                    <td className="py-4 px-4">
                      <div className="flex items-center gap-3 text-[#A1A1AA]">
                        {feature.icon}
                        {feature.label}
                      </div>
                    </td>
                    {plans.map(plan => (
                      <td key={plan.id} className="text-center py-4 px-4">
                        {renderFeatureValue(plan.features[feature.key])}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="py-20 px-4">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-3xl font-bold text-white text-center mb-12">
            Întrebări Frecvente
          </h2>
          <div className="space-y-6">
            <Card className="bg-[#0A0A0A] border-[#262626]">
              <CardHeader>
                <CardTitle className="text-white text-lg">Pot să anulez oricând?</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-[#A1A1AA]">
                  Da, poți anula subscripția oricând din setări. Vei avea acces la funcționalități până la sfârșitul perioadei plătite.
                </p>
              </CardContent>
            </Card>
            <Card className="bg-[#0A0A0A] border-[#262626]">
              <CardHeader>
                <CardTitle className="text-white text-lg">Ce se întâmplă după trial?</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-[#A1A1AA]">
                  După cele 7 zile de trial, vei fi rugat să alegi un plan. Fără card salvat, accesul va fi limitat până la alegerea unui plan.
                </p>
              </CardContent>
            </Card>
            <Card className="bg-[#0A0A0A] border-[#262626]">
              <CardHeader>
                <CardTitle className="text-white text-lg">Pot să îmi folosesc propriile API keys?</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-[#A1A1AA]">
                  Da! Suportăm BYOAK (Bring Your Own API Keys). Poți configura cheile tale pentru OpenAI, Gemini, Resend și Pexels din setări.
                </p>
              </CardContent>
            </Card>
            <Card className="bg-[#0A0A0A] border-[#262626]">
              <CardHeader>
                <CardTitle className="text-white text-lg">Pot upgrade/downgrade planul?</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-[#A1A1AA]">
                  Da, poți schimba planul oricând. La upgrade, vei avea acces imediat la funcționalitățile noi. La downgrade, schimbarea se aplică la următoarea perioadă de facturare.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-4 border-t border-[#262626]">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="flex gap-8 text-[#71717A] text-sm">
              <Link to="/terms" className="hover:text-white transition-colors">Termeni și Condiții</Link>
              <Link to="/privacy" className="hover:text-white transition-colors">Confidențialitate</Link>
              <Link to="/contact" className="hover:text-white transition-colors">Contact</Link>
            </div>
            <p className="text-[#71717A] text-sm">
              © 2026 SEO Automation. Toate drepturile rezervate.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default PricingPage;
