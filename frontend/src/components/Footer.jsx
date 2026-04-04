import { Link } from "react-router-dom";
import { Zap } from "lucide-react";

const Footer = () => {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-[#0A0A0A] border-t border-[#262626] mt-auto">
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Logo & Description */}
          <div className="col-span-1 md:col-span-2">
            <Link to="/" className="flex items-center gap-2 mb-4">
              <div className="p-2 bg-[#00E676]/10 rounded-lg">
                <Zap className="w-5 h-5 text-[#00E676]" />
              </div>
              <span className="text-xl font-bold text-white">SEO Auto</span>
            </Link>
            <p className="text-[#71717A] text-sm max-w-md">
              Platformă de automatizare SEO cu inteligență artificială. 
              Generare articole, backlinks, monitorizare și optimizare automată pentru WordPress.
            </p>
          </div>

          {/* Links */}
          <div>
            <h3 className="text-white font-semibold mb-4">Linkuri Utile</h3>
            <ul className="space-y-2">
              <li>
                <Link to="/pricing" className="text-[#71717A] hover:text-[#00E676] transition-colors text-sm">
                  Prețuri
                </Link>
              </li>
              <li>
                <Link to="/docs" className="text-[#71717A] hover:text-[#00E676] transition-colors text-sm">
                  Documentație
                </Link>
              </li>
              <li>
                <Link to="/contact" className="text-[#71717A] hover:text-[#00E676] transition-colors text-sm">
                  Contact
                </Link>
              </li>
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h3 className="text-white font-semibold mb-4">Legal</h3>
            <ul className="space-y-2">
              <li>
                <Link to="/terms" className="text-[#71717A] hover:text-[#00E676] transition-colors text-sm">
                  Termeni și Condiții
                </Link>
              </li>
              <li>
                <Link to="/privacy" className="text-[#71717A] hover:text-[#00E676] transition-colors text-sm">
                  Politica de Confidențialitate
                </Link>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="border-t border-[#262626] mt-8 pt-6 flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-[#71717A] text-sm">
            © {currentYear} SEO Auto. Toate drepturile rezervate.
          </p>
          <div className="flex items-center gap-4">
            <span className="text-[#71717A] text-xs">
              Powered by AI
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
