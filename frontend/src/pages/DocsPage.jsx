import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  BookOpen, Search, Play, FileText, Globe, Calendar, Link2,
  Zap, Key, Mail, BarChart3, HelpCircle, ExternalLink,
  CheckCircle, ArrowRight, Clock, Target, Lightbulb
} from "lucide-react";

const DocsPage = () => {
  const [searchTerm, setSearchTerm] = useState("");

  const quickStartSteps = [
    {
      step: 1,
      title: "Configureaza cheile API",
      description: "Adauga cheile pentru OpenAI si alte servicii",
      link: "/app/api-keys",
      time: "5-10 min"
    },
    {
      step: 2,
      title: "Conecteaza site-ul WordPress",
      description: "Adauga site-ul tau pentru publicare automata",
      link: "/app/wordpress",
      time: "2 min"
    },
    {
      step: 3,
      title: "Genereaza primul articol",
      description: "Creaza un articol SEO optimizat cu AI",
      link: "/app/articles",
      time: "1 min"
    },
    {
      step: 4,
      title: "Planifica calendarul editorial",
      description: "Seteaza publicarea automata pe 90 zile",
      link: "/app/calendar",
      time: "5 min"
    }
  ];

  const guides = [
    {
      id: "articles",
      icon: FileText,
      title: "Generare Articole cu AI",
      description: "Cum sa creezi articole SEO optimizate",
      sections: [
        {
          title: "Cum functioneaza?",
          content: `Platforma foloseste OpenAI GPT-4 pentru a genera articole optimizate pentru SEO. 
          Articolele sunt scrise in limba romana, cu structura corecta (H1, H2, H3), 
          meta description si cuvinte cheie integrate natural.`
        },
        {
          title: "Pasii de generare",
          content: `1. Mergi la Articole > Articol Nou
2. Introdu subiectul sau cuvantul cheie principal
3. Selecteaza lungimea dorita (scurt/mediu/lung)
4. Alege tonul (formal/conversational/expert)
5. Click pe "Genereaza" si asteapta 30-60 secunde
6. Revizuieste si editeaza daca e nevoie
7. Publica direct pe WordPress sau salveaza ca draft`
        },
        {
          title: "Sfaturi pentru rezultate mai bune",
          content: `• Fii specific cu subiectul - "Ghid complet renovare baie" e mai bun decat "renovari"
• Foloseste cuvinte cheie long-tail pentru competitie mai mica
• Revizuieste mereu articolul inainte de publicare
• Adauga imagini relevante pentru engagement mai bun`
        }
      ]
    },
    {
      id: "wordpress",
      icon: Globe,
      title: "Conectare WordPress",
      description: "Cum sa conectezi site-ul pentru publicare automata",
      sections: [
        {
          title: "Cerinte",
          content: `• Site WordPress self-hosted (nu WordPress.com gratuit)
• Plugin "Application Passwords" activ (vine preinstalat din WP 5.6+)
• Acces de administrator la WordPress`
        },
        {
          title: "Pasi de conectare",
          content: `1. In WordPress, mergi la Users > Profile
2. Scroll jos la "Application Passwords"
3. Introdu un nume (ex: "SEO Automation")
4. Click "Add New Application Password"
5. Copiaza parola generata (o vezi o singura data!)
6. In platforma noastra, mergi la Site-uri WordPress
7. Click "Adauga Site"
8. Introdu URL-ul site-ului, username-ul si Application Password
9. Click "Testeaza Conexiunea" pentru verificare`
        },
        {
          title: "Probleme frecvente",
          content: `• "401 Unauthorized" - Verifica username-ul si parola
• "403 Forbidden" - Dezactiveaza temporar plugin-uri de securitate
• "404 Not Found" - Asigura-te ca REST API e activ in WordPress
• Site-ul nu apare - Verifica ca URL-ul include https://`
        }
      ]
    },
    {
      id: "calendar",
      icon: Calendar,
      title: "Calendar Editorial",
      description: "Planifica continut pentru 90 de zile",
      sections: [
        {
          title: "Ce este calendarul editorial?",
          content: `Calendarul iti permite sa planifici articole pentru urmatoarele 90 de zile. 
          AI-ul poate genera automat un plan bazat pe nisa ta si cuvintele cheie.`
        },
        {
          title: "Cum sa creezi un calendar",
          content: `1. Mergi la Calendar Editorial
2. Click "Genereaza Calendar AI"
3. Selecteaza nisa si frecventa de publicare
4. Revizuieste sugestiile si ajusteaza
5. Aproba articolele pe care le vrei
6. Seteaza orele de publicare preferate`
        },
        {
          title: "Automatizare publicare",
          content: `Odata aprobate, articolele vor fi:
• Generate automat cu 24h inainte de publicare
• Publicate pe WordPress la ora setata
• Notificari prin email dupa publicare
• Rapoarte saptamanale de performanta`
        }
      ]
    },
    {
      id: "backlinks",
      icon: Link2,
      title: "Manager Backlinks",
      description: "Gaseste oportunitati si trimite outreach",
      sections: [
        {
          title: "Cum functioneaza outreach-ul?",
          content: `Modulul de backlinks te ajuta sa gasesti site-uri relevante pentru nisa ta 
          si sa trimiti emailuri personalizate pentru a obtine backlinks.`
        },
        {
          title: "Configurare email outreach",
          content: `1. Configureaza cheia API Resend sau SendGrid in Chei API
2. Verifica domeniul de email (instructiuni in sectiunea Chei API)
3. In Backlinks, creaza template-uri de email
4. Cauta site-uri relevante sau importa o lista
5. Selecteaza si trimite emailuri personalizate`
        },
        {
          title: "Sfaturi pentru outreach eficient",
          content: `• Personalizeaza fiecare email - mentioneaza articole specifice
• Ofera valoare - propune guest post sau resursa utila
• Urmareste cu 1-2 follow-up-uri la 3-5 zile distanta
• Rata medie de succes: 2-5% - trimite volum mare`
        }
      ]
    },
    {
      id: "reports",
      icon: BarChart3,
      title: "Rapoarte si Export",
      description: "Analizeaza performanta si exporta date",
      sections: [
        {
          title: "Tipuri de rapoarte",
          content: `• Raport Articole - toate articolele generate, status, performanta
• Raport SEO - pozitii cuvinte cheie, trafic organic
• Raport Backlinks - link-uri obtinute, DA/PA
• Raport ROI - costul per articol vs valoarea generata`
        },
        {
          title: "Export date",
          content: `Poti exporta datele in:
• PDF - pentru prezentari si clienti
• CSV - pentru analiza in Excel/Google Sheets
• Selecteaza perioada dorita si tipul de raport
• Click pe butonul Export in pagina Rapoarte`
        }
      ]
    },
    {
      id: "api-keys",
      icon: Key,
      title: "Configurare Chei API",
      description: "Conecteaza serviciile externe",
      sections: [
        {
          title: "Ce chei am nevoie?",
          content: `Obligatorii:
• OpenAI (pentru generare articole) - ~€0.05-0.10/articol

Optionale:
• Gemini (alternativa gratuita la OpenAI)
• Resend/SendGrid (pentru email outreach)
• Pexels (imagini gratuite pentru articole)`
        },
        {
          title: "Unde gasesc instructiuni?",
          content: `In pagina Chei API ai instructiuni pas cu pas pentru fiecare serviciu, 
          inclusiv linkuri directe pentru creare cont si estimari de cost.`
        }
      ]
    }
  ];

  const faqs = [
    {
      question: "Cat costa sa folosesc platforma?",
      answer: `Abonamentul lunar + costuri API externe:
• Starter: €19/luna + ~€1-5 API (10 articole)
• Pro: €49/luna + ~€5-15 API (50 articole)
• Agency: €99/luna + ~€15-50 API (200 articole)
• Enterprise: €199/luna + costuri API nelimitate`
    },
    {
      question: "Articolele trec de detectia AI?",
      answer: `Articolele generate sunt de inalta calitate, dar recomandam:
• Sa revizuiesti si sa adaugi perspectiva personala
• Sa incluzi date si statistici specifice
• Sa adaugi imagini si elemente multimedia
• Google nu penalizeaza continut AI daca e util pentru utilizatori`
    },
    {
      question: "Pot anula oricand?",
      answer: `Da, poti anula abonamentul oricand din Facturare > Gestioneaza Abonament. 
Vei avea acces pana la sfarsitul perioadei platite.`
    },
    {
      question: "Ce se intampla daca termin articolele din plan?",
      answer: `Poti:
• Astepta pana luna urmatoare (reset automat)
• Face upgrade la un plan superior
• Contacta-ne pentru articole suplimentare`
    },
    {
      question: "Pot folosi platforma pentru mai multi clienti?",
      answer: `Da! Cu planurile Agency si Enterprise poti:
• Conecta mai multe site-uri WordPress
• Genera rapoarte separate per client
• Exporta date pentru prezentari`
    },
    {
      question: "Cum obtin suport?",
      answer: `• Email: support@seoautomation.ro
• Documentatia din aceasta pagina
• Pentru Setup Complet (€79): configurare + training personalizat`
    }
  ];

  const filteredGuides = guides.filter(guide =>
    guide.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    guide.description.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6" data-testid="docs-page">
      <div>
        <h1 className="text-3xl font-bold text-white flex items-center gap-3">
          <BookOpen className="w-8 h-8 text-[#00E676]" />
          Documentatie
        </h1>
        <p className="text-[#71717A] mt-1">
          Ghiduri complete pentru a folosi platforma eficient
        </p>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#71717A]" />
        <Input
          placeholder="Cauta in documentatie..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="pl-10 bg-[#171717] border-[#262626] text-white"
        />
      </div>

      {/* Quick Start */}
      <Card className="bg-gradient-to-r from-[#00E676]/5 to-[#0A0A0A] border-[#00E676]/20">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Zap className="w-5 h-5 text-[#00E676]" />
            Start Rapid - 4 Pasi
          </CardTitle>
          <CardDescription className="text-[#71717A]">
            Configureaza totul in ~15 minute
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-4 gap-4">
            {quickStartSteps.map((item) => (
              <a 
                key={item.step}
                href={item.link}
                className="block p-4 bg-[#171717] rounded-lg border border-[#262626] hover:border-[#00E676]/50 transition-colors"
              >
                <div className="flex items-center gap-3 mb-2">
                  <span className="w-8 h-8 rounded-full bg-[#00E676] text-black flex items-center justify-center font-bold">
                    {item.step}
                  </span>
                  <span className="text-[#71717A] text-xs flex items-center gap-1">
                    <Clock className="w-3 h-3" /> {item.time}
                  </span>
                </div>
                <h4 className="text-white font-medium mb-1">{item.title}</h4>
                <p className="text-[#71717A] text-sm">{item.description}</p>
              </a>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Guides */}
      <div className="grid md:grid-cols-2 gap-6">
        {filteredGuides.map((guide) => (
          <Card key={guide.id} className="bg-[#0A0A0A] border-[#262626]">
            <CardHeader>
              <CardTitle className="text-white flex items-center gap-3">
                <div className="w-10 h-10 rounded-lg bg-[#00E676]/10 flex items-center justify-center">
                  <guide.icon className="w-5 h-5 text-[#00E676]" />
                </div>
                {guide.title}
              </CardTitle>
              <CardDescription className="text-[#71717A]">
                {guide.description}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Accordion type="single" collapsible className="w-full">
                {guide.sections.map((section, index) => (
                  <AccordionItem key={index} value={`${guide.id}-${index}`} className="border-[#262626]">
                    <AccordionTrigger className="text-[#A1A1AA] hover:text-white text-sm">
                      {section.title}
                    </AccordionTrigger>
                    <AccordionContent className="text-[#71717A] text-sm whitespace-pre-line">
                      {section.content}
                    </AccordionContent>
                  </AccordionItem>
                ))}
              </Accordion>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* FAQ */}
      <Card className="bg-[#0A0A0A] border-[#262626]">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <HelpCircle className="w-5 h-5 text-[#00E676]" />
            Intrebari Frecvente
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Accordion type="single" collapsible className="w-full">
            {faqs.map((faq, index) => (
              <AccordionItem key={index} value={`faq-${index}`} className="border-[#262626]">
                <AccordionTrigger className="text-white hover:text-[#00E676]">
                  {faq.question}
                </AccordionTrigger>
                <AccordionContent className="text-[#A1A1AA] whitespace-pre-line">
                  {faq.answer}
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </CardContent>
      </Card>

      {/* Need Help */}
      <Card className="bg-[#171717] border-[#262626]">
        <CardContent className="p-6">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="w-12 h-12 rounded-lg bg-[#00E676]/10 flex items-center justify-center">
                <Lightbulb className="w-6 h-6 text-[#00E676]" />
              </div>
              <div>
                <h3 className="text-white font-medium">Ai nevoie de ajutor personalizat?</h3>
                <p className="text-[#71717A] text-sm">
                  Oferim serviciu de Setup Complet - configurare + training 1-la-1
                </p>
              </div>
            </div>
            <a href="/contact">
              <Button className="bg-[#00E676] text-black hover:bg-[#00E676]/90">
                Contacteaza-ne (€79)
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </a>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default DocsPage;
