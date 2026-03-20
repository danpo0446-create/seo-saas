import { Link } from "react-router-dom";
import { Zap } from "lucide-react";
import { Button } from "@/components/ui/button";

const PrivacyPage = () => {
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
            <Link to="/register">
              <Button className="bg-[#00E676] text-black hover:bg-[#00E676]/90">
                Începe Gratuit
              </Button>
            </Link>
          </div>
        </div>
      </nav>

      <div className="pt-32 pb-20 px-4">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-4xl font-bold text-white mb-8">Politica de Confidențialitate</h1>
          
          <div className="prose prose-invert max-w-none space-y-6 text-[#A1A1AA]">
            <p className="text-lg">
              Ultima actualizare: Martie 2026
            </p>

            <section className="space-y-4">
              <h2 className="text-2xl font-semibold text-white">1. Introducere</h2>
              <p>
                SEO Automation respectă confidențialitatea dumneavoastră și se angajează să protejeze 
                datele personale. Această politică explică cum colectăm, utilizăm și protejăm informațiile 
                dumneavoastră.
              </p>
            </section>

            <section className="space-y-4">
              <h2 className="text-2xl font-semibold text-white">2. Date Colectate</h2>
              <p>Colectăm următoarele tipuri de date:</p>
              <ul className="list-disc pl-6 space-y-2">
                <li><strong>Date de cont:</strong> Nume, email, parolă (criptată)</li>
                <li><strong>Date de utilizare:</strong> Articole generate, site-uri conectate, activitate pe platformă</li>
                <li><strong>Date tehnice:</strong> Adresă IP, tip browser, dispozitiv</li>
                <li><strong>Date de plată:</strong> Procesate securizat prin Stripe (nu stocăm date de card)</li>
              </ul>
            </section>

            <section className="space-y-4">
              <h2 className="text-2xl font-semibold text-white">3. Utilizarea Datelor</h2>
              <p>Utilizăm datele pentru:</p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Furnizarea și îmbunătățirea serviciilor</li>
                <li>Procesarea plăților și gestionarea abonamentelor</li>
                <li>Comunicarea cu dumneavoastră (suport, notificări)</li>
                <li>Analiza utilizării pentru îmbunătățirea platformei</li>
                <li>Prevenirea fraudei și asigurarea securității</li>
              </ul>
            </section>

            <section className="space-y-4">
              <h2 className="text-2xl font-semibold text-white">4. Partajarea Datelor</h2>
              <p>
                Nu vindem datele dumneavoastră. Partajăm date doar cu:
              </p>
              <ul className="list-disc pl-6 space-y-2">
                <li><strong>Stripe:</strong> Pentru procesarea plăților</li>
                <li><strong>Furnizori de servicii:</strong> Care ne ajută să operăm platforma</li>
                <li><strong>Autorități:</strong> Când suntem obligați legal</li>
              </ul>
            </section>

            <section className="space-y-4">
              <h2 className="text-2xl font-semibold text-white">5. Securitatea Datelor</h2>
              <p>
                Implementăm măsuri de securitate standard în industrie:
              </p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Criptare SSL/TLS pentru toate conexiunile</li>
                <li>Parole criptate cu algoritmi siguri</li>
                <li>Chei API criptate în baza de date</li>
                <li>Backup-uri regulate și monitorizare continuă</li>
              </ul>
            </section>

            <section className="space-y-4">
              <h2 className="text-2xl font-semibold text-white">6. Drepturile Dumneavoastră (GDPR)</h2>
              <p>Aveți dreptul să:</p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Accesați datele personale pe care le deținem</li>
                <li>Corectați datele inexacte</li>
                <li>Solicitați ștergerea datelor</li>
                <li>Exportați datele într-un format portabil</li>
                <li>Vă opuneți procesării în anumite circumstanțe</li>
              </ul>
            </section>

            <section className="space-y-4">
              <h2 className="text-2xl font-semibold text-white">7. Cookie-uri</h2>
              <p>
                Utilizăm cookie-uri esențiale pentru funcționarea platformei și cookie-uri de analiză 
                pentru a înțelege cum este utilizat serviciul. Puteți controla cookie-urile din setările 
                browser-ului.
              </p>
            </section>

            <section className="space-y-4">
              <h2 className="text-2xl font-semibold text-white">8. Retenția Datelor</h2>
              <p>
                Păstrăm datele atât timp cât aveți un cont activ sau cât este necesar pentru a furniza 
                serviciile. După ștergerea contului, datele sunt eliminate în termen de 30 de zile, cu 
                excepția cazurilor în care legea impune păstrarea lor.
              </p>
            </section>

            <section className="space-y-4">
              <h2 className="text-2xl font-semibold text-white">9. Contact</h2>
              <p>
                Pentru întrebări despre confidențialitate sau pentru a vă exercita drepturile:
                <a href="mailto:privacy@seoautomation.ro" className="text-[#00E676] hover:underline ml-1">
                  privacy@seoautomation.ro
                </a>
              </p>
            </section>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="py-8 px-4 border-t border-[#262626]">
        <div className="max-w-6xl mx-auto text-center">
          <p className="text-[#71717A] text-sm">
            © 2026 SEO Automation. Toate drepturile rezervate.
          </p>
        </div>
      </footer>
    </div>
  );
};

export default PrivacyPage;
