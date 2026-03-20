import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { Zap, Mail, MapPin, Phone, Clock } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import axios from "axios";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const ContactPage = () => {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    subject: "",
    message: ""
  });
  const [sending, setSending] = useState(false);
  
  // Dynamic content from admin
  const [contactInfo, setContactInfo] = useState({
    email: "support@seoautomation.ro",
    phone: "+40 721 234 567",
    address: "Bucuresti, Romania",
    hours: "Luni - Vineri, 9:00 - 18:00"
  });

  useEffect(() => {
    fetchContactInfo();
  }, []);

  const fetchContactInfo = async () => {
    try {
      // Try to get content from public endpoint
      const res = await axios.get(`${API}/saas/content/contact`);
      if (res.data?.content) {
        setContactInfo(res.data.content);
      }
    } catch (error) {
      // Use default values if endpoint doesn't exist or fails
      console.log("Using default contact info");
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSending(true);
    // Simulare trimitere
    await new Promise(resolve => setTimeout(resolve, 1000));
    toast.success("Mesajul a fost trimis! Te vom contacta in curand.");
    setFormData({ name: "", email: "", subject: "", message: "" });
    setSending(false);
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
        <div className="max-w-6xl mx-auto">
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold text-white mb-4">Contacteaza-ne</h1>
            <p className="text-[#A1A1AA] text-lg">
              Ai intrebari? Suntem aici sa te ajutam.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-12">
            {/* Contact Info */}
            <div className="space-y-8">
              <Card className="bg-[#0A0A0A] border-[#262626]">
                <CardContent className="p-6">
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 rounded-lg bg-[#00E676]/10 flex items-center justify-center">
                      <Mail className="w-6 h-6 text-[#00E676]" />
                    </div>
                    <div>
                      <h3 className="text-white font-semibold mb-1">Email</h3>
                      <p className="text-[#A1A1AA]">{contactInfo.email}</p>
                      <p className="text-[#71717A] text-sm mt-1">Raspundem in 24h</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-[#0A0A0A] border-[#262626]">
                <CardContent className="p-6">
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 rounded-lg bg-[#00E676]/10 flex items-center justify-center">
                      <Phone className="w-6 h-6 text-[#00E676]" />
                    </div>
                    <div>
                      <h3 className="text-white font-semibold mb-1">Telefon</h3>
                      <p className="text-[#A1A1AA]">{contactInfo.phone}</p>
                      <p className="text-[#71717A] text-sm mt-1">{contactInfo.hours}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-[#0A0A0A] border-[#262626]">
                <CardContent className="p-6">
                  <div className="flex items-start gap-4">
                    <div className="w-12 h-12 rounded-lg bg-[#00E676]/10 flex items-center justify-center">
                      <MapPin className="w-6 h-6 text-[#00E676]" />
                    </div>
                    <div>
                      <h3 className="text-white font-semibold mb-1">Adresa</h3>
                      <p className="text-[#A1A1AA]">{contactInfo.address}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Contact Form */}
            <Card className="bg-[#0A0A0A] border-[#262626]">
              <CardHeader>
                <CardTitle className="text-white">Trimite un mesaj</CardTitle>
              </CardHeader>
              <CardContent>
                <form onSubmit={handleSubmit} className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label className="text-[#A1A1AA]">Nume</Label>
                      <Input
                        required
                        value={formData.name}
                        onChange={(e) => setFormData({...formData, name: e.target.value})}
                        className="bg-[#171717] border-[#262626] text-white"
                        placeholder="Numele tau"
                      />
                    </div>
                    <div className="space-y-2">
                      <Label className="text-[#A1A1AA]">Email</Label>
                      <Input
                        required
                        type="email"
                        value={formData.email}
                        onChange={(e) => setFormData({...formData, email: e.target.value})}
                        className="bg-[#171717] border-[#262626] text-white"
                        placeholder="email@exemplu.ro"
                      />
                    </div>
                  </div>
                  <div className="space-y-2">
                    <Label className="text-[#A1A1AA]">Subiect</Label>
                    <Input
                      required
                      value={formData.subject}
                      onChange={(e) => setFormData({...formData, subject: e.target.value})}
                      className="bg-[#171717] border-[#262626] text-white"
                      placeholder="Despre ce e vorba?"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-[#A1A1AA]">Mesaj</Label>
                    <Textarea
                      required
                      value={formData.message}
                      onChange={(e) => setFormData({...formData, message: e.target.value})}
                      className="bg-[#171717] border-[#262626] text-white min-h-[150px]"
                      placeholder="Scrie mesajul tau aici..."
                    />
                  </div>
                  <Button 
                    type="submit" 
                    disabled={sending}
                    className="w-full bg-[#00E676] text-black hover:bg-[#00E676]/90"
                  >
                    {sending ? "Se trimite..." : "Trimite Mesajul"}
                  </Button>
                </form>
              </CardContent>
            </Card>
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

export default ContactPage;
