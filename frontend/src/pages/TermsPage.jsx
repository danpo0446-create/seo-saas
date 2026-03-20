import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Zap } from "lucide-react";
import { Button } from "@/components/ui/button";
import axios from "axios";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const TermsPage = () => {
  const [content, setContent] = useState({
    company_name: "SEO Automation SRL",
    company_address: "Bucuresti, Romania",
    company_email: "legal@seoautomation.ro",
    last_updated: "Martie 2026"
  });

  useEffect(() => {
    fetchContent();
  }, []);

  const fetchContent = async () => {
    try {
      const res = await axios.get(`${API}/saas/content/terms`);
      if (res.data?.content) {
        setContent(res.data.content);
      }
    } catch (error) {
      console.log("Using default terms content");
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
            <Link to="/register">
              <Button className="bg-[#00E676] text-black hover:bg-[#00E676]/90">
                Incepe Gratuit
              </Button>
            </Link>
          </div>
        </div>
      </nav>

      <div className="pt-32 pb-20 px-4">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-4xl font-bold text-white mb-8">Termeni si Conditii</h1>
          
          <div className="prose prose-invert max-w-none space-y-6 text-[#A1A1AA]">
            <p className="text-lg">
              Ultima actualizare: {content.last_updated}
            </p>

            <section className="space-y-4">
              <h2 className="text-2xl font-semibold text-white">1. Acceptarea Termenilor</h2>
              <p>
                Prin accesarea si utilizarea platformei {content.company_name}, acceptati sa fiti obligat de acesti 
                Termeni si Conditii. Daca nu sunteti de acord cu oricare parte a termenilor, nu puteti 
                accesa serviciul.
              </p>
            </section>

            <section className="space-y-4">
              <h2 className="text-2xl font-semibold text-white">2. Descrierea Serviciului</h2>
              <p>
                {content.company_name} ofera o platforma SaaS pentru automatizarea proceselor de SEO, inclusiv:
              </p>
              <ul className="list-disc pl-6 space-y-2">
                <li>Generarea de articole optimizate pentru SEO folosind inteligenta artificiala</li>
                <li>Publicarea automata pe site-uri WordPress</li>
                <li>Cercetarea si analiza cuvintelor cheie</li>
                <li>Managementul calendarului editorial</li>
                <li>Monitorizarea si raportarea performantei SEO</li>
              </ul>
            </section>

            <section className="space-y-4">
              <h2 className="text-2xl font-semibold text-white">3. Conturi de Utilizator</h2>
              <p>
                Pentru a utiliza serviciile noastre, trebuie sa creati un cont. Sunteti responsabil pentru
                mentinerea confidentialitatii contului si parolei si pentru restrictionarea accesului la computer.
              </p>
            </section>

            <section className="space-y-4">
              <h2 className="text-2xl font-semibold text-white">4. Planuri si Plati</h2>
              <p>
                Oferim mai multe planuri de abonament cu diferite caracteristici si limite. Platile sunt 
                procesate securizat prin Stripe. Puteti anula abonamentul in orice moment din contul dvs.
              </p>
            </section>

            <section className="space-y-4">
              <h2 className="text-2xl font-semibold text-white">5. Proprietate Intelectuala</h2>
              <p>
                Continutul generat folosind platforma noastra va apartine. Totusi, {content.company_name} isi 
                rezerva dreptul de a utiliza date anonimizate pentru imbunatatirea serviciilor.
              </p>
            </section>

            <section className="space-y-4">
              <h2 className="text-2xl font-semibold text-white">6. Limitarea Raspunderii</h2>
              <p>
                {content.company_name} nu va fi raspunzator pentru daune indirecte, incidentale, speciale sau 
                consecvente rezultate din utilizarea sau incapacitatea de a utiliza serviciul.
              </p>
            </section>

            <section className="space-y-4">
              <h2 className="text-2xl font-semibold text-white">7. Contact</h2>
              <p>
                Pentru intrebari despre acesti Termeni si Conditii, ne puteti contacta la:
              </p>
              <p>
                <strong className="text-white">{content.company_name}</strong><br />
                {content.company_address}<br />
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
              <Link to="/privacy" className="hover:text-white transition-colors">Confidentialitate</Link>
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

export default TermsPage;
