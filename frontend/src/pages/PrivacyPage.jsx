import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import axios from "axios";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const PrivacyPage = () => {
  const [content, setContent] = useState({
    company_name: "SEO Automation SRL",
    company_email: "privacy@seoautomation.ro",
    data_retention: "2 ani",
    last_updated: "Martie 2026"
  });

  useEffect(() => {
    fetchContent();
  }, []);

  const fetchContent = async () => {
    try {
      const res = await axios.get(`${API}/saas/content/privacy`);
      if (res.data?.content) {
        setContent(res.data.content);
      }
    } catch (error) {
      console.log("Using default privacy content");
    }
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

      <div className="pt-32 pb-20 px-4">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-4xl font-bold text-white mb-8">Politica de Confidentialitate</h1>
          
          <div className="prose prose-invert max-w-none space-y-6 text-[#A1A1AA]">
            <p className="text-lg">
              Ultima actualizare: {content.last_updated}
            </p>

            <section className="space-y-4">
              <h2 className="text-2xl font-semibold text-white">1. Informatii pe care le Colectam</h2>
              <p>
                {content.company_name} colecteaza urmatoarele tipuri de informatii:
              </p>
              <ul className="list-disc pl-6 space-y-2">
                <li><strong className="text-white">Informatii de cont:</strong> Nume, adresa de email, parola criptata</li>
                <li><strong className="text-white">Date de utilizare:</strong> Articole create, site-uri conectate, activitate pe platforma</li>
                <li><strong className="text-white">Informatii de plata:</strong> Procesate securizat prin Stripe (nu stocam datele cardului)</li>
                <li><strong className="text-white">Chei API:</strong> Daca alegeti sa folositi propriile chei API, acestea sunt criptate</li>
              </ul>
            </section>

            <section className="space-y-4">
              <h2 className="text-2xl font-semibold text-white">2. Cum Folosim Informatiile</h2>
              <p>
                Folosim informatiile colectate pentru:
              </p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Furnizarea si imbunatatirea serviciilor noastre</li>
                <li>Procesarea platilor si gestionarea abonamentelor</li>
                <li>Comunicarea cu dvs. despre cont si servicii</li>
                <li>Detectarea si prevenirea fraudelor</li>
              </ul>
            </section>

            <section className="space-y-4">
              <h2 className="text-2xl font-semibold text-white">3. Partajarea Datelor</h2>
              <p>
                Nu vindem datele dvs. personale. Partajam informatii doar cu:
              </p>
              <ul className="list-disc pl-6 space-y-2">
                <li><strong className="text-white">Procesatori de plati:</strong> Stripe pentru procesarea platilor</li>
                <li><strong className="text-white">Furnizori de servicii:</strong> Necesari pentru functionarea platformei</li>
                <li><strong className="text-white">Autoritati legale:</strong> Cand suntem obligati prin lege</li>
              </ul>
            </section>

            <section className="space-y-4">
              <h2 className="text-2xl font-semibold text-white">4. Retentia Datelor</h2>
              <p>
                Pastram datele dvs. cat timp aveti un cont activ sau conform cerintelor legale. 
                Perioada standard de retentie este de <strong className="text-white">{content.data_retention}</strong> dupa 
                inchiderea contului.
              </p>
            </section>

            <section className="space-y-4">
              <h2 className="text-2xl font-semibold text-white">5. Drepturile Dvs.</h2>
              <p>
                Aveti dreptul sa:
              </p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Accesati datele dvs. personale</li>
                <li>Corectati informatiile inexacte</li>
                <li>Solicitati stergerea datelor</li>
                <li>Exportati datele dvs.</li>
                <li>Va opuneti procesarii in anumite circumstante</li>
              </ul>
            </section>

            <section className="space-y-4">
              <h2 className="text-2xl font-semibold text-white">6. Securitate</h2>
              <p>
                Implementam masuri tehnice si organizationale pentru a proteja datele dvs., inclusiv:
              </p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Criptare SSL/TLS pentru toate conexiunile</li>
                <li>Criptarea parolelor si cheilor API</li>
                <li>Acces restrictionat la date pe baza de rol</li>
                <li>Monitorizare continua a securitatii</li>
              </ul>
            </section>

            <section className="space-y-4">
              <h2 className="text-2xl font-semibold text-white">7. Contact</h2>
              <p>
                Pentru intrebari despre aceasta Politica de Confidentialitate sau pentru a va exercita 
                drepturile, contactati-ne la:
              </p>
              <p>
                <strong className="text-white">{content.company_name}</strong><br />
                Email: {content.company_email}
              </p>
            </section>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="py-8 px-4 border-t border-[#262626]">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <div className="flex gap-6 text-[#71717A] text-sm">
              <Link to="/contact" className="hover:text-white transition-colors">Contact</Link>
              <Link to="/terms" className="hover:text-white transition-colors">Termeni</Link>
            </div>
            <p className="text-[#71717A] text-sm">
              © 2026 {content.company_name}. Toate drepturile rezervate.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default PrivacyPage;
