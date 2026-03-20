import { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { 
  Zap, FileText, Search, Calendar, Link2, Globe, BarChart3, 
  Mail, CheckCircle, ArrowRight, Star, Shield, Clock, Users,
  Sparkles, TrendingUp, Target, Rocket
} from "lucide-react";

const LandingPage = () => {
  const features = [
    {
      icon: <FileText className="w-6 h-6" />,
      title: "Articole SEO Generate cu AI",
      description: "Articole optimizate pentru SEO, scrise automat în limba română, cu lungime și ton personalizabile."
    },
    {
      icon: <Search className="w-6 h-6" />,
      title: "Keyword Research Inteligent",
      description: "Descoperă cuvinte-cheie profitabile pentru nișa ta cu analiza volumului și dificultății."
    },
    {
      icon: <Calendar className="w-6 h-6" />,
      title: "Calendar Editorial 90 Zile",
      description: "Planifică conținutul pe 3 luni înainte cu calendar generat automat de AI."
    },
    {
      icon: <Globe className="w-6 h-6" />,
      title: "Multi-Site WordPress",
      description: "Gestionează multiple site-uri WordPress dintr-un singur dashboard."
    },
    {
      icon: <Zap className="w-6 h-6" />,
      title: "Publicare Automată",
      description: "Articolele sunt publicate automat pe WordPress la ora programată."
    },
    {
      icon: <Link2 className="w-6 h-6" />,
      title: "Manager Backlinks",
      description: "Găsește oportunități de backlinks și trimite email-uri de outreach automat."
    },
    {
      icon: <BarChart3 className="w-6 h-6" />,
      title: "Google Search Console",
      description: "Monitorizează traficul și performanța direct din dashboard."
    },
    {
      icon: <Mail className="w-6 h-6" />,
      title: "Notificări Email",
      description: "Primește notificări când articolele sunt publicate și rapoarte săptămânale."
    }
  ];

  const plans = [
    {
      name: "Starter",
      price: "19",
      popular: false,
      features: ["1 site WordPress", "15 articole/lună", "Keyword research", "Calendar editorial", "Publicare automată"]
    },
    {
      name: "Pro",
      price: "49",
      popular: true,
      features: ["5 site-uri WordPress", "50 articole/lună", "Google Search Console", "Manager backlinks", "Rapoarte avansate", "Email notificări"]
    },
    {
      name: "Agency",
      price: "99",
      popular: false,
      features: ["20 site-uri WordPress", "200 articole/lună", "WooCommerce integrare", "Social Media posting", "Audit SEO tehnic", "Suport prioritar"]
    }
  ];

  const testimonials = [
    {
      name: "Maria D.",
      company: "E-commerce Fashion",
      quote: "Am economisit 20+ ore pe săptămână cu automatizarea articolelor. Traficul organic a crescut cu 150%!",
      avatar: "MD"
    },
    {
      name: "Alexandru P.",
      company: "Agenție SEO",
      quote: "Gestionez 15 site-uri ale clienților dintr-un singur loc. Productivitatea echipei s-a dublat.",
      avatar: "AP"
    },
    {
      name: "Elena R.",
      company: "Blog Parenting",
      quote: "Calitatea articolelor generate este impresionantă. Cititorii nici nu își dau seama că sunt scrise de AI.",
      avatar: "ER"
    }
  ];

  return (
    <div className="min-h-screen bg-[#050505]" data-testid="landing-page">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-[#050505]/90 backdrop-blur-md border-b border-[#262626]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-[#00E676] flex items-center justify-center">
                <Zap className="w-5 h-5 text-black" />
              </div>
              <span className="text-xl font-bold text-white">SEO Automation</span>
            </div>
            <div className="hidden md:flex items-center gap-8">
              <a href="#features" className="text-[#A1A1AA] hover:text-white transition-colors">Funcționalități</a>
              <a href="#pricing" className="text-[#A1A1AA] hover:text-white transition-colors">Prețuri</a>
              <a href="#testimonials" className="text-[#A1A1AA] hover:text-white transition-colors">Testimoniale</a>
            </div>
            <div className="flex items-center gap-3">
              <Link to="/login">
                <Button variant="ghost" className="text-[#A1A1AA] hover:text-white" data-testid="login-btn">
                  Autentificare
                </Button>
              </Link>
              <Link to="/register">
                <Button className="bg-[#00E676] text-black hover:bg-[#00E676]/90" data-testid="register-btn">
                  Începe Gratuit
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-4">
        <div className="max-w-6xl mx-auto text-center">
          <Badge className="mb-6 bg-[#00E676]/10 text-[#00E676] border-[#00E676]/20 py-1 px-3">
            <Sparkles className="w-3.5 h-3.5 mr-1.5" />
            7 zile gratuit • Fără card de credit
          </Badge>
          <h1 className="text-4xl md:text-6xl font-bold text-white mb-6 leading-tight">
            Automatizează-ți SEO-ul<br />
            <span className="text-[#00E676]">cu Inteligență Artificială</span>
          </h1>
          <p className="text-xl text-[#A1A1AA] mb-8 max-w-3xl mx-auto">
            Generează articole SEO, publică automat pe WordPress, monitorizează traficul 
            și crește organic fără efort manual. Tot ce ai nevoie într-o singură platformă.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/register">
              <Button size="lg" className="bg-[#00E676] text-black hover:bg-[#00E676]/90 text-lg px-8 h-14" data-testid="hero-cta">
                Începe Trial Gratuit
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </Link>
            <a href="#features">
              <Button size="lg" variant="outline" className="border-[#262626] text-white hover:bg-[#171717] text-lg px-8 h-14">
                Vezi Funcționalitățile
              </Button>
            </a>
          </div>
          <div className="mt-12 flex flex-wrap justify-center gap-8 text-sm text-[#71717A]">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-[#00E676]" />
              100% White-Label
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-[#00E676]" />
              Articole în Română
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-[#00E676]" />
              Suport 24/7
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-16 border-y border-[#262626] bg-[#0A0A0A]">
        <div className="max-w-6xl mx-auto px-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            <div className="text-center">
              <div className="text-4xl font-bold text-[#00E676] mb-2">10K+</div>
              <div className="text-[#71717A]">Articole Generate</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-[#00E676] mb-2">500+</div>
              <div className="text-[#71717A]">Clienți Activi</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-[#00E676] mb-2">150%</div>
              <div className="text-[#71717A]">Creștere Trafic Mediu</div>
            </div>
            <div className="text-center">
              <div className="text-4xl font-bold text-[#00E676] mb-2">24/7</div>
              <div className="text-[#71717A]">Automatizare Non-Stop</div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <Badge className="mb-4 bg-[#171717] text-[#A1A1AA] border-[#262626]">
              Funcționalități
            </Badge>
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Tot ce ai nevoie pentru SEO de succes
            </h2>
            <p className="text-[#A1A1AA] max-w-2xl mx-auto">
              O platformă completă care automatizează întregul proces de content marketing și SEO.
            </p>
          </div>
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {features.map((feature, index) => (
              <Card key={index} className="bg-[#0A0A0A] border-[#262626] hover:border-[#00E676]/50 transition-colors">
                <CardHeader>
                  <div className="w-12 h-12 rounded-lg bg-[#00E676]/10 flex items-center justify-center text-[#00E676] mb-4">
                    {feature.icon}
                  </div>
                  <CardTitle className="text-white text-lg">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-[#71717A] text-sm">{feature.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* BYOAK Info Section */}
      <section className="py-16 px-4 border-t border-[#262626]">
        <div className="max-w-4xl mx-auto">
          <Card className="bg-gradient-to-r from-[#00E676]/5 to-[#0A0A0A] border-[#00E676]/20">
            <CardContent className="p-8">
              <div className="flex flex-col md:flex-row items-center gap-8">
                <div className="flex-1">
                  <Badge className="mb-3 bg-[#00E676]/10 text-[#00E676]">Transparenta Totala</Badge>
                  <h3 className="text-2xl font-bold text-white mb-3">
                    Folosesti propriile tale chei API
                  </h3>
                  <p className="text-[#A1A1AA] mb-4">
                    Platesti direct la OpenAI, Resend, etc. pentru ce consumi. 
                    Fara comisioane ascunse, control total asupra costurilor.
                    <span className="text-white"> Costuri extra estimate: €1-10/luna.</span>
                  </p>
                  <Link to="/ghid-configurare">
                    <Button variant="outline" className="border-[#00E676] text-[#00E676] hover:bg-[#00E676]/10">
                      Vezi Ghidul Complet
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </Button>
                  </Link>
                </div>
                <div className="md:w-48 text-center p-6 bg-[#171717] rounded-xl">
                  <p className="text-[#71717A] text-sm mb-1">Nu vrei sa configurezi?</p>
                  <p className="text-2xl font-bold text-white mb-2">€79</p>
                  <p className="text-[#71717A] text-xs">Setup Complet de la noi</p>
                  <Link to="/ghid-configurare">
                    <Button size="sm" className="mt-3 bg-[#00E676] text-black hover:bg-[#00E676]/90 text-xs">
                      Afla mai multe
                    </Button>
                  </Link>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="py-20 px-4 bg-[#0A0A0A]">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <Badge className="mb-4 bg-[#171717] text-[#A1A1AA] border-[#262626]">
              Prețuri Simple
            </Badge>
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Alege planul potrivit pentru tine
            </h2>
            <p className="text-[#A1A1AA] max-w-2xl mx-auto">
              Începe cu 7 zile gratuit, fără obligații. Anulează oricând.
            </p>
          </div>
          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {plans.map((plan, index) => (
              <Card 
                key={index} 
                className={`relative bg-[#0A0A0A] ${plan.popular ? 'border-[#00E676] ring-1 ring-[#00E676]' : 'border-[#262626]'}`}
                data-testid={`plan-card-${plan.name.toLowerCase()}`}
              >
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <Badge className="bg-[#00E676] text-black">Cel Mai Popular</Badge>
                  </div>
                )}
                <CardHeader className="text-center pb-2">
                  <CardTitle className="text-white text-xl">{plan.name}</CardTitle>
                  <div className="mt-4">
                    <span className="text-4xl font-bold text-white">€{plan.price}</span>
                    <span className="text-[#71717A]">/lună</span>
                  </div>
                </CardHeader>
                <CardContent className="pt-6">
                  <ul className="space-y-3 mb-6">
                    {plan.features.map((feature, i) => (
                      <li key={i} className="flex items-center gap-3 text-[#A1A1AA]">
                        <CheckCircle className="w-4 h-4 text-[#00E676] flex-shrink-0" />
                        {feature}
                      </li>
                    ))}
                  </ul>
                  <Link to="/register">
                    <Button 
                      className={`w-full ${plan.popular ? 'bg-[#00E676] text-black hover:bg-[#00E676]/90' : 'bg-[#171717] text-white hover:bg-[#262626]'}`}
                      data-testid={`plan-btn-${plan.name.toLowerCase()}`}
                    >
                      Începe Gratuit
                    </Button>
                  </Link>
                </CardContent>
              </Card>
            ))}
          </div>
          <div className="text-center mt-8">
            <Link to="/pricing" className="text-[#00E676] hover:underline">
              Vezi toate planurile și funcționalitățile →
            </Link>
          </div>
        </div>
      </section>

      {/* Testimonials Section */}
      <section id="testimonials" className="py-20 px-4">
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-16">
            <Badge className="mb-4 bg-[#171717] text-[#A1A1AA] border-[#262626]">
              Testimoniale
            </Badge>
            <h2 className="text-3xl md:text-4xl font-bold text-white mb-4">
              Ce spun clienții noștri
            </h2>
          </div>
          <div className="grid md:grid-cols-3 gap-8">
            {testimonials.map((testimonial, index) => (
              <Card key={index} className="bg-[#0A0A0A] border-[#262626]">
                <CardContent className="pt-6">
                  <div className="flex gap-1 mb-4">
                    {[...Array(5)].map((_, i) => (
                      <Star key={i} className="w-4 h-4 fill-[#00E676] text-[#00E676]" />
                    ))}
                  </div>
                  <p className="text-[#A1A1AA] mb-6">"{testimonial.quote}"</p>
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-full bg-[#00E676]/20 flex items-center justify-center text-[#00E676] font-medium">
                      {testimonial.avatar}
                    </div>
                    <div>
                      <div className="text-white font-medium">{testimonial.name}</div>
                      <div className="text-[#71717A] text-sm">{testimonial.company}</div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-4 bg-gradient-to-b from-[#0A0A0A] to-[#050505]">
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-[#00E676]/10 text-[#00E676] text-sm mb-6">
            <Rocket className="w-4 h-4" />
            Gata să începi?
          </div>
          <h2 className="text-3xl md:text-4xl font-bold text-white mb-6">
            Transformă-ți strategia SEO astăzi
          </h2>
          <p className="text-[#A1A1AA] mb-8 text-lg">
            Înregistrează-te gratuit și începe să generezi articole în mai puțin de 5 minute.
          </p>
          <Link to="/register">
            <Button size="lg" className="bg-[#00E676] text-black hover:bg-[#00E676]/90 text-lg px-10 h-14" data-testid="final-cta">
              Începe Trial Gratuit de 7 Zile
              <ArrowRight className="w-5 h-5 ml-2" />
            </Button>
          </Link>
          <p className="mt-4 text-sm text-[#71717A]">
            Fără card de credit necesar • Anulează oricând
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-12 px-4 border-t border-[#262626]">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-[#00E676] flex items-center justify-center">
                <Zap className="w-5 h-5 text-black" />
              </div>
              <span className="text-lg font-bold text-white">SEO Automation</span>
            </div>
            <div className="flex gap-8 text-[#71717A] text-sm">
              <Link to="/terms" className="hover:text-white transition-colors">Termeni și Condiții</Link>
              <Link to="/privacy" className="hover:text-white transition-colors">Confidențialitate</Link>
              <Link to="/contact" className="hover:text-white transition-colors">Contact</Link>
            </div>
            <div className="text-[#71717A] text-sm">
              © 2026 SEO Automation. Toate drepturile rezervate.
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
