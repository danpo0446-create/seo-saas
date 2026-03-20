import { useState } from "react";
import { Link } from "react-router-dom";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { 
  Zap, Key, Sparkles, Brain, Mail, Image, ExternalLink, 
  Check, ArrowRight, Clock, Shield, HeadphonesIcon, Settings,
  CheckCircle, HelpCircle, Euro
} from "lucide-react";

const SetupGuidePage = () => {
  const apiServices = [
    {
      id: "openai",
      name: "OpenAI (GPT-4)",
      icon: Sparkles,
      color: "text-green-500",
      bgColor: "bg-green-500/10",
      required: true,
      description: "Genereaza articole SEO optimizate cu inteligenta artificiala",
      pricing: {
        free: false,
        cost: "~€0.05-0.10 per articol",
        monthly: "Platesti per utilizare (pay-as-you-go)"
      },
      steps: [
        "Acceseaza platform.openai.com si creaza cont",
        "Confirma adresa de email",
        "Din meniu, selecteaza 'API Keys'",
        "Click pe 'Create new secret key'",
        "Copiaza cheia (incepe cu 'sk-')",
        "Important: Adauga credit in sectiunea Billing (minim $5)"
      ],
      link: "https://platform.openai.com/api-keys",
      tips: "Recomandam sa setezi un limit lunar de $10-20 pentru inceput"
    },
    {
      id: "gemini",
      name: "Google Gemini",
      icon: Brain,
      color: "text-blue-500",
      bgColor: "bg-blue-500/10",
      required: false,
      description: "Alternativa gratuita la OpenAI pentru generare continut",
      pricing: {
        free: true,
        cost: "GRATUIT",
        monthly: "Pana la 60 requesturi/minut"
      },
      steps: [
        "Acceseaza aistudio.google.com",
        "Logheaza-te cu contul Google",
        "Click pe 'Get API Key'",
        "Selecteaza sau creaza un proiect",
        "Copiaza cheia API"
      ],
      link: "https://aistudio.google.com/app/apikey",
      tips: "Ideal pentru teste sau daca vrei sa reduci costurile"
    },
    {
      id: "resend",
      name: "Resend (Email Outreach)",
      icon: Mail,
      color: "text-purple-500",
      bgColor: "bg-purple-500/10",
      required: false,
      description: "Trimite emailuri pentru campanii de backlinks si outreach",
      pricing: {
        free: true,
        cost: "3,000 emailuri/luna GRATUIT",
        monthly: "Apoi €20/luna pentru 50,000 emailuri"
      },
      steps: [
        "Creaza cont pe resend.com",
        "Verifica domeniul tau (adaugi recorduri DNS)",
        "Din Dashboard, click pe 'API Keys'",
        "Creaza o cheie noua",
        "Copiaza cheia (incepe cu 're_')"
      ],
      link: "https://resend.com",
      tips: "Necesita domeniu propriu pentru trimitere. Planul gratuit e suficient pentru inceput."
    },
    {
      id: "sendgrid",
      name: "SendGrid (Email)",
      icon: Mail,
      color: "text-blue-400",
      bgColor: "bg-blue-400/10",
      required: false,
      description: "Alternativa pentru email outreach cu plan gratuit permanent",
      pricing: {
        free: true,
        cost: "100 emailuri/zi GRATUIT",
        monthly: "Pentru totdeauna (3,000/luna)"
      },
      steps: [
        "Creaza cont pe sendgrid.com",
        "Verifica identitatea (poate dura 1-2 zile)",
        "Din Settings > API Keys",
        "Creaza cheie cu 'Full Access'",
        "Copiaza cheia (incepe cu 'SG.')"
      ],
      link: "https://sendgrid.com",
      tips: "Verificarea contului poate dura. Incepe procesul din timp."
    },
    {
      id: "pexels",
      name: "Pexels (Imagini)",
      icon: Image,
      color: "text-teal-500",
      bgColor: "bg-teal-500/10",
      required: false,
      description: "Imagini gratuite de calitate pentru articolele tale",
      pricing: {
        free: true,
        cost: "GRATUIT",
        monthly: "200 requesturi/ora, nelimitat"
      },
      steps: [
        "Creaza cont pe pexels.com",
        "Confirma emailul",
        "Acceseaza pexels.com/api",
        "Copiaza cheia API din dashboard"
      ],
      link: "https://www.pexels.com/api/new/",
      tips: "Cel mai simplu de configurat. Recomandat pentru toti utilizatorii."
    }
  ];

  const setupService = {
    name: "Serviciu Setup Complet",
    price: "€79",
    description: "Nu vrei sa te ocupi de configurari tehnice? Noi facem totul pentru tine!",
    includes: [
      "Creare conturi pe toate serviciile necesare",
      "Configurare si verificare chei API",
      "Conectare cu platforma SEO Automation",
      "Configurare domeniu pentru email (daca e cazul)",
      "Testare completa a tuturor functiilor",
      "Ghid personalizat de utilizare (30 min video call)",
      "Suport prioritar 30 zile"
    ],
    note: "Ideal pentru antreprenori si agentii care vor sa inceapa rapid fara batai de cap tehnice."
  };

  return (
    <div className="min-h-screen bg-[#050505]">
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
              <Link to="/pricing">
                <Button variant="ghost" className="text-[#A1A1AA] hover:text-white">
                  Preturi
                </Button>
              </Link>
              <Link to="/login">
                <Button variant="ghost" className="text-[#A1A1AA] hover:text-white">
                  Autentificare
                </Button>
              </Link>
              <Link to="/register">
                <Button className="bg-[#00E676] text-black hover:bg-[#00E676]/90">
                  Incepe Gratuit
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="pt-32 pb-16 px-4">
        <div className="max-w-4xl mx-auto text-center">
          <Badge className="bg-[#00E676]/10 text-[#00E676] mb-4">
            <Key className="w-3 h-3 mr-1" /> Ghid de Configurare
          </Badge>
          <h1 className="text-4xl md:text-5xl font-bold text-white mb-6">
            Tot ce trebuie sa stii inainte sa incepi
          </h1>
          <p className="text-xl text-[#A1A1AA] mb-8">
            SEO Automation foloseste propriile tale chei API pentru serviciile externe. 
            Asta inseamna <span className="text-white">control total asupra costurilor</span> si 
            <span className="text-white"> fara surprize</span>.
          </p>
        </div>
      </div>

      {/* Why BYOAK Section */}
      <div className="py-12 px-4 border-t border-[#262626]">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-2xl font-bold text-white mb-8 text-center">De ce folosim aceasta abordare?</h2>
          <div className="grid md:grid-cols-3 gap-6">
            <Card className="bg-[#0A0A0A] border-[#262626]">
              <CardContent className="p-6">
                <div className="w-12 h-12 rounded-lg bg-[#00E676]/10 flex items-center justify-center mb-4">
                  <Euro className="w-6 h-6 text-[#00E676]" />
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">Transparenta Costuri</h3>
                <p className="text-[#A1A1AA]">
                  Platesti direct furnizorilor (OpenAI, etc.) exact cat consumi. 
                  Fara comisioane ascunse sau markup-uri.
                </p>
              </CardContent>
            </Card>

            <Card className="bg-[#0A0A0A] border-[#262626]">
              <CardContent className="p-6">
                <div className="w-12 h-12 rounded-lg bg-[#00E676]/10 flex items-center justify-center mb-4">
                  <Shield className="w-6 h-6 text-[#00E676]" />
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">Control Total</h3>
                <p className="text-[#A1A1AA]">
                  Setezi propriile limite de cheltuieli. Daca vrei sa opresti, 
                  dezactivezi cheia si gata.
                </p>
              </CardContent>
            </Card>

            <Card className="bg-[#0A0A0A] border-[#262626]">
              <CardContent className="p-6">
                <div className="w-12 h-12 rounded-lg bg-[#00E676]/10 flex items-center justify-center mb-4">
                  <Settings className="w-6 h-6 text-[#00E676]" />
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">Flexibilitate</h3>
                <p className="text-[#A1A1AA]">
                  Alegi ce servicii folosesti. Vrei doar articole? Folosesti doar OpenAI. 
                  Vrei si outreach? Adaugi Resend.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      {/* Cost Estimation */}
      <div className="py-12 px-4 bg-[#0A0A0A]">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold text-white mb-8 text-center">Cat costa in realitate?</h2>
          <Card className="bg-[#171717] border-[#262626]">
            <CardContent className="p-6">
              <div className="space-y-4">
                <div className="flex items-center justify-between py-3 border-b border-[#262626]">
                  <span className="text-[#A1A1AA]">10 articole SEO / luna</span>
                  <span className="text-white font-medium">~€1.00</span>
                </div>
                <div className="flex items-center justify-between py-3 border-b border-[#262626]">
                  <span className="text-[#A1A1AA]">50 articole SEO / luna</span>
                  <span className="text-white font-medium">~€5.00</span>
                </div>
                <div className="flex items-center justify-between py-3 border-b border-[#262626]">
                  <span className="text-[#A1A1AA]">100 emailuri outreach / luna</span>
                  <span className="text-white font-medium">GRATUIT</span>
                </div>
                <div className="flex items-center justify-between py-3 border-b border-[#262626]">
                  <span className="text-[#A1A1AA]">Imagini pentru articole</span>
                  <span className="text-white font-medium">GRATUIT</span>
                </div>
                <div className="flex items-center justify-between py-3 bg-[#00E676]/5 rounded-lg px-4 -mx-4">
                  <span className="text-white font-medium">Total estimat / luna</span>
                  <span className="text-[#00E676] font-bold text-xl">€1 - €10</span>
                </div>
              </div>
              <p className="text-[#71717A] text-sm mt-4 text-center">
                * Estimare pentru utilizare medie. Costurile variaza in functie de volum.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Setup Service - Premium Offer */}
      <div className="py-16 px-4 border-t border-[#262626]">
        <div className="max-w-4xl mx-auto">
          <Card className="bg-gradient-to-br from-[#00E676]/10 to-[#0A0A0A] border-[#00E676]/30 overflow-hidden">
            <CardContent className="p-8">
              <div className="flex flex-col md:flex-row gap-8">
                <div className="flex-1">
                  <Badge className="bg-[#00E676] text-black mb-4">
                    <HeadphonesIcon className="w-3 h-3 mr-1" /> Serviciu Premium
                  </Badge>
                  <h2 className="text-3xl font-bold text-white mb-4">
                    {setupService.name}
                  </h2>
                  <p className="text-[#A1A1AA] mb-6">
                    {setupService.description}
                  </p>
                  <ul className="space-y-3 mb-6">
                    {setupService.includes.map((item, index) => (
                      <li key={index} className="flex items-start gap-3">
                        <CheckCircle className="w-5 h-5 text-[#00E676] shrink-0 mt-0.5" />
                        <span className="text-white">{item}</span>
                      </li>
                    ))}
                  </ul>
                  <p className="text-[#71717A] text-sm italic">
                    {setupService.note}
                  </p>
                </div>
                <div className="md:w-64 flex flex-col justify-center items-center p-6 bg-[#171717] rounded-xl">
                  <span className="text-[#71717A] text-sm">Pret unic</span>
                  <span className="text-5xl font-bold text-white mb-2">{setupService.price}</span>
                  <span className="text-[#71717A] text-sm mb-6">platire o singura data</span>
                  <Link to="/contact" className="w-full">
                    <Button className="w-full bg-[#00E676] text-black hover:bg-[#00E676]/90">
                      Contacteaza-ne
                      <ArrowRight className="w-4 h-4 ml-2" />
                    </Button>
                  </Link>
                  <p className="text-[#71717A] text-xs mt-4 text-center">
                    Configurare in 24-48h
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* API Services Details */}
      <div className="py-16 px-4 border-t border-[#262626]">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold text-white mb-2 text-center">Ghid Pas cu Pas</h2>
          <p className="text-[#A1A1AA] text-center mb-8">
            Configureaza singur in 15-30 minute
          </p>

          <div className="space-y-6">
            {apiServices.map((service) => (
              <Card key={service.id} className="bg-[#0A0A0A] border-[#262626]">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-4">
                      <div className={`w-12 h-12 rounded-lg ${service.bgColor} flex items-center justify-center`}>
                        <service.icon className={`w-6 h-6 ${service.color}`} />
                      </div>
                      <div>
                        <CardTitle className="text-white flex items-center gap-2">
                          {service.name}
                          {service.required && (
                            <Badge className="bg-red-500/10 text-red-400 text-xs">Necesar</Badge>
                          )}
                          {service.pricing.free && (
                            <Badge className="bg-[#00E676]/10 text-[#00E676] text-xs">Plan Gratuit</Badge>
                          )}
                        </CardTitle>
                        <CardDescription className="text-[#71717A]">
                          {service.description}
                        </CardDescription>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-white font-semibold">{service.pricing.cost}</p>
                      <p className="text-[#71717A] text-sm">{service.pricing.monthly}</p>
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <Accordion type="single" collapsible>
                    <AccordionItem value="steps" className="border-[#262626]">
                      <AccordionTrigger className="text-[#A1A1AA] hover:text-white">
                        <span className="flex items-center gap-2">
                          <Settings className="w-4 h-4" />
                          Vezi pasii de configurare
                        </span>
                      </AccordionTrigger>
                      <AccordionContent>
                        <ol className="space-y-3 mb-4">
                          {service.steps.map((step, index) => (
                            <li key={index} className="flex gap-3">
                              <span className={`w-6 h-6 rounded-full ${service.bgColor} ${service.color} flex items-center justify-center text-sm font-medium shrink-0`}>
                                {index + 1}
                              </span>
                              <span className="text-[#A1A1AA]">{step}</span>
                            </li>
                          ))}
                        </ol>
                        
                        <div className="flex items-start gap-2 p-3 rounded-lg bg-[#171717] mb-4">
                          <HelpCircle className="w-4 h-4 text-yellow-500 mt-0.5 shrink-0" />
                          <p className="text-[#A1A1AA] text-sm">
                            <strong className="text-yellow-500">Sfat:</strong> {service.tips}
                          </p>
                        </div>
                        
                        <Button
                          variant="outline"
                          className="border-[#262626] hover:border-[#00E676] hover:text-[#00E676]"
                          onClick={() => window.open(service.link, '_blank')}
                        >
                          <ExternalLink className="w-4 h-4 mr-2" />
                          Deschide {service.name}
                        </Button>
                      </AccordionContent>
                    </AccordionItem>
                  </Accordion>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>

      {/* FAQ */}
      <div className="py-16 px-4 bg-[#0A0A0A] border-t border-[#262626]">
        <div className="max-w-4xl mx-auto">
          <h2 className="text-2xl font-bold text-white mb-8 text-center">Intrebari Frecvente</h2>
          <Accordion type="single" collapsible className="space-y-4">
            <AccordionItem value="faq-1" className="bg-[#171717] border-[#262626] rounded-lg px-4">
              <AccordionTrigger className="text-white hover:text-[#00E676]">
                Pot folosi platforma fara chei API?
              </AccordionTrigger>
              <AccordionContent className="text-[#A1A1AA]">
                Poti explora platforma si vedea toate functiile, dar pentru a genera articole 
                sau trimite emailuri vei avea nevoie de cheile respective. Functii ca managementul 
                site-urilor WordPress, calendarul editorial si monitorizarea functioneaza fara chei externe.
              </AccordionContent>
            </AccordionItem>
            
            <AccordionItem value="faq-2" className="bg-[#171717] border-[#262626] rounded-lg px-4">
              <AccordionTrigger className="text-white hover:text-[#00E676]">
                E sigur sa imi pun cheile API in platforma?
              </AccordionTrigger>
              <AccordionContent className="text-[#A1A1AA]">
                Da. Toate cheile sunt criptate inainte de a fi salvate. Noi nu avem acces la cheile 
                tale in format text. Plus, poti oricand sa le revoci din dashboard-ul furnizorului 
                daca ai suspiciuni.
              </AccordionContent>
            </AccordionItem>
            
            <AccordionItem value="faq-3" className="bg-[#171717] border-[#262626] rounded-lg px-4">
              <AccordionTrigger className="text-white hover:text-[#00E676]">
                Ce se intampla daca imi termin creditul la OpenAI?
              </AccordionTrigger>
              <AccordionContent className="text-[#A1A1AA]">
                Generarea de articole se va opri pana adaugi credit. Vei primi o notificare 
                si poti adauga fonduri oricand din contul OpenAI. Restul platformei functioneaza normal.
              </AccordionContent>
            </AccordionItem>
            
            <AccordionItem value="faq-4" className="bg-[#171717] border-[#262626] rounded-lg px-4">
              <AccordionTrigger className="text-white hover:text-[#00E676]">
                Pot schimba intre OpenAI si Gemini?
              </AccordionTrigger>
              <AccordionContent className="text-[#A1A1AA]">
                Da! Poti configura ambele si alegi care sa fie folosit pentru generare. 
                Gemini e gratuit dar poate avea calitate usor mai scazuta pentru texte in romana.
              </AccordionContent>
            </AccordionItem>
            
            <AccordionItem value="faq-5" className="bg-[#171717] border-[#262626] rounded-lg px-4">
              <AccordionTrigger className="text-white hover:text-[#00E676]">
                Nu am timp/cunostinte pentru configurare. Ce fac?
              </AccordionTrigger>
              <AccordionContent className="text-[#A1A1AA]">
                Oferim serviciul de <strong className="text-white">Setup Complet la €79</strong> - 
                noi facem toata configurarea pentru tine in 24-48h. Include si un call de 30 minute 
                unde iti explicam cum sa folosesti platforma eficient.
                <Link to="/contact" className="text-[#00E676] ml-1 hover:underline">
                  Contacteaza-ne →
                </Link>
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </div>
      </div>

      {/* CTA */}
      <div className="py-16 px-4 border-t border-[#262626]">
        <div className="max-w-4xl mx-auto text-center">
          <h2 className="text-3xl font-bold text-white mb-4">Gata sa incepi?</h2>
          <p className="text-[#A1A1AA] mb-8">
            7 zile gratuit, fara card. Configureaza cheile si testeaza toate functiile.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/register">
              <Button size="lg" className="bg-[#00E676] text-black hover:bg-[#00E676]/90">
                Incepe Gratuit
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
            <Link to="/contact">
              <Button size="lg" variant="outline" className="border-[#262626] hover:border-[#00E676]">
                Vreau Setup Complet (€79)
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="py-8 px-4 border-t border-[#262626]">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="flex gap-6 text-[#71717A] text-sm">
              <Link to="/terms" className="hover:text-white transition-colors">Termeni</Link>
              <Link to="/privacy" className="hover:text-white transition-colors">Confidentialitate</Link>
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

export default SetupGuidePage;
