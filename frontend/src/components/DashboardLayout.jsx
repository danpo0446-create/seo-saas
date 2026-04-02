import { useState } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '@/contexts/AuthContext';
import { useSite } from '@/contexts/SiteContext';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  LayoutDashboard,
  PenTool,
  Search,
  Calendar,
  Link,
  Settings,
  LogOut,
  Menu,
  X,
  Globe,
  Zap,
  Plus,
  Bot,
  Share2,
  Activity,
  Brain,
  FileSearch,
  SearchCheck,
  BarChart3,
  CreditCard,
  Shield,
  Key
} from 'lucide-react';

const navItems = [
  { path: '/app/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { path: '/app/articles', icon: PenTool, label: 'Articole' },
  { path: '/app/keywords', icon: Search, label: 'Cuvinte-cheie' },
  { path: '/app/calendar', icon: Calendar, label: 'Calendar Editorial' },
  { path: '/app/backlinks', icon: Link, label: 'Backlinks' },
  { path: '/app/backlinks/automation', icon: Bot, label: 'Automatizare Backlinks' },
  { path: '/app/web2', icon: Share2, label: 'Web 2.0 Links', adminOnly: true },
  { path: '/app/wordpress', icon: Globe, label: 'Site-uri WordPress' },
  { path: '/app/automation', icon: Bot, label: 'Automatizare' },
  { path: '/app/reports', icon: BarChart3, label: 'Rapoarte' },
  { path: '/app/monitor', icon: Activity, label: 'Monitorizare' },
  { path: '/app/technical-audit', icon: FileSearch, label: 'Audit Tehnic' },
  { path: '/app/business-analysis', icon: Brain, label: 'Analiză Business' },
  { path: '/app/indexing', icon: SearchCheck, label: 'Indexare Google' },
  { path: '/app/api-keys', icon: Key, label: 'Chei API' },
  { path: '/app/docs', icon: FileSearch, label: 'Documentație' },
  { path: '/app/billing', icon: CreditCard, label: 'Facturare' },
  { path: '/app/settings', icon: Settings, label: 'Setări' },
];

export const DashboardLayout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { user, logout } = useAuth();
  const { sites, currentSite, selectSite } = useSite();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const handleSiteChange = (siteId) => {
    if (siteId === 'add-new') {
      navigate('/app/wordpress');
    } else if (siteId === 'all') {
      selectSite(null);
    } else {
      const site = sites.find(s => s.id === siteId);
      selectSite(site);
    }
  };

  return (
    <div className="min-h-screen bg-background flex">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed lg:static inset-y-0 left-0 z-50
        w-64 bg-card border-r border-border
        transform transition-transform duration-200 ease-in-out
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
      `}>
        <div className="flex flex-col h-full">
          {/* Logo */}
          <div className="h-16 flex items-center px-6 border-b border-border">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center neon-glow">
                <Zap className="w-5 h-5 text-primary-foreground" />
              </div>
              <span className="font-heading font-bold text-lg">SEO Auto</span>
            </div>
            <button 
              className="ml-auto lg:hidden"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Site Selector */}
          <div className="px-3 py-4 border-b border-border">
            <label className="text-xs text-muted-foreground mb-2 block">Site activ:</label>
            <Select 
              value={currentSite?.id || 'all'} 
              onValueChange={handleSiteChange}
            >
              <SelectTrigger className="bg-secondary border-border" data-testid="site-selector">
                <SelectValue placeholder="Selectează site">
                  {currentSite ? (
                    <div className="flex items-center gap-2">
                      <Globe className="w-4 h-4 text-primary" />
                      <span className="truncate">{currentSite.site_name || currentSite.site_url}</span>
                    </div>
                  ) : (
                    <span className="text-muted-foreground">Toate site-urile</span>
                  )}
                </SelectValue>
              </SelectTrigger>
              <SelectContent className="bg-card border-border">
                <SelectItem value="all">
                  <span className="text-muted-foreground">Toate site-urile</span>
                </SelectItem>
                {sites.map(site => (
                  <SelectItem key={site.id} value={site.id}>
                    <div className="flex items-center gap-2">
                      <Globe className="w-4 h-4" />
                      {site.site_name || site.site_url}
                    </div>
                  </SelectItem>
                ))}
                <SelectItem value="add-new" className="text-primary">
                  <div className="flex items-center gap-2">
                    <Plus className="w-4 h-4" />
                    Adaugă site nou
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Navigation */}
          <ScrollArea className="flex-1 py-4">
            <nav className="px-3 space-y-1">
              {navItems
                .filter(item => !item.adminOnly || user?.role === 'admin')
                .map((item) => (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={() => setSidebarOpen(false)}
                  className={({ isActive }) => `
                    flex items-center gap-3 px-3 py-2.5 rounded-lg
                    transition-colors duration-150
                    ${isActive 
                      ? 'bg-primary/10 text-primary border border-primary/20' 
                      : 'text-muted-foreground hover:bg-accent hover:text-foreground'
                    }
                  `}
                  data-testid={`nav-${item.path.slice(1)}`}
                >
                  <item.icon className="w-5 h-5" />
                  <span className="font-medium">{item.label}</span>
                </NavLink>
              ))}
              
              {/* Admin Dashboard - only for admin users */}
              {user?.role === 'admin' && (
                <NavLink
                  to="/app/admin"
                  onClick={() => setSidebarOpen(false)}
                  className={({ isActive }) => `
                    flex items-center gap-3 px-3 py-2.5 rounded-lg
                    transition-colors duration-150
                    ${isActive 
                      ? 'bg-red-500/10 text-red-500 border border-red-500/20' 
                      : 'text-red-400 hover:bg-red-500/10 hover:text-red-400'
                    }
                  `}
                  data-testid="nav-admin"
                >
                  <Shield className="w-5 h-5" />
                  <span className="font-medium">Admin</span>
                </NavLink>
              )}
            </nav>
          </ScrollArea>

          {/* User section */}
          <div className="p-4 border-t border-border">
            <div className="flex items-center gap-3 mb-3">
              <div className="w-9 h-9 rounded-full bg-secondary flex items-center justify-center">
                <span className="text-sm font-semibold">
                  {user?.name?.charAt(0).toUpperCase() || 'U'}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">{user?.name}</p>
                <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
              </div>
            </div>
            <Button 
              variant="ghost" 
              className="w-full justify-start text-muted-foreground hover:text-destructive"
              onClick={handleLogout}
              data-testid="logout-button"
            >
              <LogOut className="w-4 h-4 mr-2" />
              Deconectare
            </Button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-h-screen">
        {/* Header */}
        <header className="h-16 bg-background/70 backdrop-blur-xl border-b border-border sticky top-0 z-30">
          <div className="h-full px-4 lg:px-8 flex items-center">
            <button 
              className="lg:hidden p-2 -ml-2"
              onClick={() => setSidebarOpen(true)}
              data-testid="mobile-menu-button"
            >
              <Menu className="w-5 h-5" />
            </button>
            
            {/* Current site indicator on mobile */}
            {currentSite && (
              <div className="ml-4 lg:hidden flex items-center gap-2 text-sm">
                <Globe className="w-4 h-4 text-primary" />
                <span className="truncate max-w-32">{currentSite.site_name || currentSite.site_url}</span>
              </div>
            )}
            
            <div className="ml-auto flex items-center gap-4">
              <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full bg-secondary text-sm">
                <span className="w-2 h-2 rounded-full bg-primary animate-pulse"></span>
                <span className="text-muted-foreground">Status:</span>
                <span className="text-foreground font-medium">Activ</span>
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 p-4 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
};
