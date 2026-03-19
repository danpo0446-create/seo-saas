import { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { 
  TrendingUp, TrendingDown, DollarSign, FileText, Globe, 
  Search, Link2, BarChart3, Target, Zap, ArrowUpRight, ArrowDownRight
} from "lucide-react";
import axios from "axios";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const AnalyticsDashboard = () => {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      const token = localStorage.getItem("token");
      const response = await axios.get(`${API}/saas/analytics/overview`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAnalytics(response.data);
    } catch (error) {
      console.error("Error fetching analytics:", error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4 animate-pulse">
        {[...Array(4)].map((_, i) => (
          <Card key={i} className="bg-[#0A0A0A] border-[#262626]">
            <CardContent className="p-6">
              <div className="h-20 bg-[#171717] rounded"></div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (!analytics) return null;

  const { articles, sites, keywords, backlinks, financial, subscription } = analytics;

  const statCards = [
    {
      title: "Articole Generate",
      value: articles.total,
      subValue: `${articles.this_month} luna aceasta`,
      icon: <FileText className="w-5 h-5" />,
      color: "text-[#00E676]",
      bgColor: "bg-[#00E676]/10"
    },
    {
      title: "Site-uri Conectate",
      value: sites.total,
      subValue: `din ${sites.limit === -1 ? "∞" : sites.limit} disponibile`,
      icon: <Globe className="w-5 h-5" />,
      color: "text-blue-400",
      bgColor: "bg-blue-400/10"
    },
    {
      title: "Cuvinte-cheie",
      value: keywords.total,
      subValue: "în baza de date",
      icon: <Search className="w-5 h-5" />,
      color: "text-purple-400",
      bgColor: "bg-purple-400/10"
    },
    {
      title: "Backlinks",
      value: backlinks.total,
      subValue: "găsite",
      icon: <Link2 className="w-5 h-5" />,
      color: "text-orange-400",
      bgColor: "bg-orange-400/10"
    }
  ];

  return (
    <div className="space-y-6" data-testid="analytics-dashboard">
      {/* ROI Overview Card */}
      <Card className="bg-gradient-to-br from-[#0A0A0A] to-[#0F0F0F] border-[#262626]">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-white flex items-center gap-2">
                <Target className="w-5 h-5 text-[#00E676]" />
                ROI & Valoare Estimată
              </CardTitle>
              <CardDescription className="text-[#71717A]">
                Performanța investiției tale în SEO Automation
              </CardDescription>
            </div>
            <Badge className={`${financial.roi_percentage >= 0 ? 'bg-[#00E676]/10 text-[#00E676]' : 'bg-red-500/10 text-red-400'}`}>
              {financial.roi_percentage >= 0 ? (
                <ArrowUpRight className="w-3 h-3 mr-1" />
              ) : (
                <ArrowDownRight className="w-3 h-3 mr-1" />
              )}
              {financial.roi_percentage}% ROI
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-4 gap-6">
            {/* Plan Cost */}
            <div className="space-y-2">
              <p className="text-[#71717A] text-sm">Cost Lunar Plan</p>
              <p className="text-2xl font-bold text-white">
                €{financial.plan_cost}
                <span className="text-sm text-[#71717A] font-normal">/lună</span>
              </p>
              <p className="text-xs text-[#525252]">
                Plan: {subscription.plan.charAt(0).toUpperCase() + subscription.plan.slice(1)}
              </p>
            </div>

            {/* Cost per Article */}
            <div className="space-y-2">
              <p className="text-[#71717A] text-sm">Cost per Articol</p>
              <p className="text-2xl font-bold text-white">
                €{financial.cost_per_article}
              </p>
              <p className="text-xs text-[#525252]">
                {articles.this_month} articole luna aceasta
              </p>
            </div>

            {/* Estimated Value */}
            <div className="space-y-2">
              <p className="text-[#71717A] text-sm">Valoare Estimată SEO</p>
              <p className="text-2xl font-bold text-[#00E676]">
                €{financial.estimated_value}
              </p>
              <p className="text-xs text-[#525252]">
                ~€12 per articol în valoare SEO
              </p>
            </div>

            {/* Net Value */}
            <div className="space-y-2">
              <p className="text-[#71717A] text-sm">Câștig Net Estimat</p>
              <p className={`text-2xl font-bold ${financial.estimated_value - financial.plan_cost >= 0 ? 'text-[#00E676]' : 'text-red-400'}`}>
                €{financial.estimated_value - financial.plan_cost}
              </p>
              <p className="text-xs text-[#525252]">
                valoare - cost plan
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Stats Cards */}
      <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
        {statCards.map((stat, index) => (
          <Card key={index} className="bg-[#0A0A0A] border-[#262626] hover:border-[#363636] transition-colors">
            <CardContent className="p-6">
              <div className="flex items-start justify-between">
                <div>
                  <p className="text-[#71717A] text-sm mb-1">{stat.title}</p>
                  <p className="text-3xl font-bold text-white">{stat.value}</p>
                  <p className="text-xs text-[#525252] mt-1">{stat.subValue}</p>
                </div>
                <div className={`w-10 h-10 rounded-lg ${stat.bgColor} flex items-center justify-center ${stat.color}`}>
                  {stat.icon}
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Usage Progress */}
      <div className="grid md:grid-cols-2 gap-6">
        {/* Articles Usage */}
        <Card className="bg-[#0A0A0A] border-[#262626]">
          <CardHeader>
            <CardTitle className="text-white text-lg flex items-center gap-2">
              <Zap className="w-4 h-4 text-[#00E676]" />
              Utilizare Articole
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <div className="flex justify-between text-sm mb-2">
                <span className="text-[#A1A1AA]">Articole generate luna aceasta</span>
                <span className="text-white">
                  {subscription.articles_used} / {subscription.articles_limit === -1 ? "∞" : subscription.articles_limit}
                </span>
              </div>
              <Progress 
                value={subscription.articles_limit === -1 ? 0 : (subscription.articles_used / subscription.articles_limit) * 100} 
                className="h-3 bg-[#262626]"
              />
            </div>
            <div className="grid grid-cols-3 gap-4 pt-4 border-t border-[#262626]">
              <div className="text-center">
                <p className="text-2xl font-bold text-white">{articles.published}</p>
                <p className="text-xs text-[#71717A]">Publicate</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-yellow-400">{articles.scheduled}</p>
                <p className="text-xs text-[#71717A]">Programate</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-[#00E676]">{articles.this_week}</p>
                <p className="text-xs text-[#71717A]">Săptămâna asta</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Performance Summary */}
        <Card className="bg-[#0A0A0A] border-[#262626]">
          <CardHeader>
            <CardTitle className="text-white text-lg flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-[#00E676]" />
              Sumar Performanță
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-[#171717] rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-[#00E676]/10 flex items-center justify-center">
                    <FileText className="w-4 h-4 text-[#00E676]" />
                  </div>
                  <span className="text-[#A1A1AA]">Total Articole</span>
                </div>
                <span className="text-white font-semibold">{articles.total}</span>
              </div>
              
              <div className="flex items-center justify-between p-3 bg-[#171717] rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-blue-400/10 flex items-center justify-center">
                    <Globe className="w-4 h-4 text-blue-400" />
                  </div>
                  <span className="text-[#A1A1AA]">Site-uri Active</span>
                </div>
                <span className="text-white font-semibold">{sites.total}</span>
              </div>
              
              <div className="flex items-center justify-between p-3 bg-[#171717] rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-purple-400/10 flex items-center justify-center">
                    <Search className="w-4 h-4 text-purple-400" />
                  </div>
                  <span className="text-[#A1A1AA]">Keywords Tracked</span>
                </div>
                <span className="text-white font-semibold">{keywords.total}</span>
              </div>
              
              <div className="flex items-center justify-between p-3 bg-[#171717] rounded-lg">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded-lg bg-orange-400/10 flex items-center justify-center">
                    <Link2 className="w-4 h-4 text-orange-400" />
                  </div>
                  <span className="text-[#A1A1AA]">Backlinks</span>
                </div>
                <span className="text-white font-semibold">{backlinks.total}</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default AnalyticsDashboard;
