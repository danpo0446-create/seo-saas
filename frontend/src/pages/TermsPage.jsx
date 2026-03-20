import { Link } from "react-router-dom";
import { Zap } from "lucide-react";
import { Button } from "@/components/ui/button";

const TermsPage = () => {
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
          <h1 className="text-4xl font-bold text-white mb-8">Termeni și Condiții</h1>
          
          <div className="prose prose-invert max-w-none space-y-6 text-[#A1A1AA]">
            <p className="text-lg">
              Ultima actualizare: Martie 2026
            </p>

            <section className="space-y-4">
              <h2 className="text-2xl font-semibold text-white">1. Acceptarea Termenilor</h2>
              <p>
                Prin accesarea și utilizarea platformei SEO Automation, acceptați să fiți obligat de acești 
                Termeni și Condiții. Dacă nu sunteți de acord cu oricare parte a termenilor, nu puteți 
                accesa serviciul.
              </p>
            </section>

            <section className="space-y-4">
              <h2 className="text-2xl font-semibold text-white">2. Descrierea Serviciului</h2>
              <p>
                SEO Automation oferă o platformă SaaS pentru automatizarea proceselor de SEO, inclusiv:
              </p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Generarea de articole optimizate pentru SEO folosind inteligență artificială</li>
                <li>Publicarea automată pe site-uri WordPress</li>
                <li>Cercetarea și analiza cuvintelor cheie</li>
                <li>Managementul calendarului editorial</li>
                <li>Monitorizarea și raportarea performanței SEO</li>
              </ul>
            </section>

            <section className="space-y-4">
              <h2 className="text-2xl font-semibold text-white">3. Conturi de Utilizator</h2>
              <p>
                Pentru a utiliza serviciile noastre, trebuie să creați un cont. Sunteți responsabil pentru:
              </p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Menținerea confidențialității datelor de autentificare</li>
                <li>Toate activitățile care au loc sub contul dumneavoastră</li>
                <li>Notificarea imediată în cazul oricărei utilizări neautorizate</li>
              </ul>
            </section>

            <section className="space-y-4">
              <h2 className="text-2xl font-semibold text-white">4. Planuri și Plăți</h2>
              <p>
                Oferim mai multe planuri de abonament cu diferite funcționalități și limite. Plățile sunt 
                procesate prin Stripe și sunt recurente (lunare sau anuale). Puteți anula abonamentul 
                oricând, iar accesul va continua până la sfârșitul perioadei plătite.
              </p>
            </section>

            <section className="space-y-4">
              <h2 className="text-2xl font-semibold text-white">5. Utilizare Acceptabilă</h2>
              <p>
                Nu aveți voie să utilizați serviciul pentru:
              </p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Activități ilegale sau frauduloase</li>
                <li>Generarea de conținut care încalcă drepturile de autor</li>
                <li>Spam sau conținut malițios</li>
                <li>Încercări de a compromite securitatea platformei</li>
              </ul>
            </section>

            <section className="space-y-4">
              <h2 className="text-2xl font-semibold text-white">6. Proprietate Intelectuală</h2>
              <p>
                Conținutul generat prin platforma noastră vă aparține. Cu toate acestea, platforma, 
                design-ul, codul și tehnologia subiacentă rămân proprietatea SEO Automation.
              </p>
            </section>

            <section className="space-y-4">
              <h2 className="text-2xl font-semibold text-white">7. Limitarea Răspunderii</h2>
              <p>
                SEO Automation nu este răspunzătoare pentru daune indirecte, incidentale sau consecvente 
                rezultate din utilizarea sau imposibilitatea de a utiliza serviciul.
              </p>
            </section>

            <section className="space-y-4">
              <h2 className="text-2xl font-semibold text-white">8. Modificări ale Termenilor</h2>
              <p>
                Ne rezervăm dreptul de a modifica acești termeni în orice moment. Modificările vor fi 
                comunicate prin email și/sau prin notificare pe platformă.
              </p>
            </section>

            <section className="space-y-4">
              <h2 className="text-2xl font-semibold text-white">9. Contact</h2>
              <p>
                Pentru întrebări despre acești termeni, contactați-ne la: 
                <a href="mailto:legal@seoautomation.ro" className="text-[#00E676] hover:underline ml-1">
                  legal@seoautomation.ro
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

export default TermsPage;
