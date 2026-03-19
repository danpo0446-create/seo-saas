import "@/App.css";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";
import { AuthProvider, useAuth } from "@/contexts/AuthContext";
import { SiteProvider } from "@/contexts/SiteContext";
import { DashboardLayout } from "@/components/DashboardLayout";
import LoginPage from "@/pages/LoginPage";
import RegisterPage from "@/pages/RegisterPage";
import DashboardPage from "@/pages/DashboardPage";
import ArticlesPage from "@/pages/ArticlesPage";
import ArticleGeneratorPage from "@/pages/ArticleGeneratorPage";
import KeywordsPage from "@/pages/KeywordsPage";
import CalendarPage from "@/pages/CalendarPage";
import BacklinksPage from "@/pages/BacklinksPage";
import Web2Page from "@/pages/Web2Page";
import WordPressPage from "@/pages/WordPressPage";
import SettingsPage from "@/pages/SettingsPage";
import AutomationPage from "@/pages/AutomationPage";
import MonitorPage from "@/pages/MonitorPage";
import TechnicalAuditPage from "@/pages/TechnicalAuditPage";
import BusinessAnalysisPage from "@/pages/BusinessAnalysisPage";
import IndexingPage from "@/pages/IndexingPage";
import ReportsPage from "@/pages/ReportsPage";
import LandingPage from "@/pages/LandingPage";
import PricingPage from "@/pages/PricingPage";
import BillingPage from "@/pages/BillingPage";

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="animate-pulse-glow w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center">
          <div className="w-6 h-6 rounded-full bg-primary"></div>
        </div>
      </div>
    );
  }
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  return children;
};

const PublicRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();
  
  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="animate-pulse-glow w-12 h-12 rounded-full bg-primary/20 flex items-center justify-center">
          <div className="w-6 h-6 rounded-full bg-primary"></div>
        </div>
      </div>
    );
  }
  
  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }
  
  return children;
};

function App() {
  return (
    <AuthProvider>
      <SiteProvider>
        <BrowserRouter>
          <Routes>
            {/* Public Pages */}
            <Route path="/" element={<LandingPage />} />
            <Route path="/pricing" element={<PricingPage />} />
            <Route path="/login" element={
              <PublicRoute><LoginPage /></PublicRoute>
            } />
            <Route path="/register" element={
              <PublicRoute><RegisterPage /></PublicRoute>
            } />
            
            {/* Protected Dashboard */}
            <Route path="/app" element={
              <ProtectedRoute>
                <DashboardLayout />
              </ProtectedRoute>
            }>
              <Route index element={<Navigate to="/app/dashboard" replace />} />
              <Route path="dashboard" element={<DashboardPage />} />
              <Route path="articles" element={<ArticlesPage />} />
              <Route path="articles/new" element={<ArticleGeneratorPage />} />
              <Route path="keywords" element={<KeywordsPage />} />
              <Route path="calendar" element={<CalendarPage />} />
              <Route path="backlinks" element={<BacklinksPage />} />
              <Route path="web2" element={<Web2Page />} />
              <Route path="wordpress" element={<WordPressPage />} />
              <Route path="automation" element={<AutomationPage />} />
              <Route path="reports" element={<ReportsPage />} />
              <Route path="monitor" element={<MonitorPage />} />
              <Route path="technical-audit" element={<TechnicalAuditPage />} />
              <Route path="business-analysis" element={<BusinessAnalysisPage />} />
              <Route path="indexing" element={<IndexingPage />} />
              <Route path="settings" element={<SettingsPage />} />
              <Route path="billing" element={<BillingPage />} />
            </Route>
            
            {/* Legacy routes redirect */}
            <Route path="/dashboard" element={<Navigate to="/app/dashboard" replace />} />
            <Route path="/articles/*" element={<Navigate to="/app/articles" replace />} />
            <Route path="/billing" element={<Navigate to="/app/billing" replace />} />
          </Routes>
        </BrowserRouter>
        <Toaster position="top-right" theme="dark" />
      </SiteProvider>
    </AuthProvider>
  );
}

export default App;
