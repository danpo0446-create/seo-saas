import { createContext, useContext, useState, useEffect } from 'react';
import axios from 'axios';
import { useAuth } from './AuthContext';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const SiteContext = createContext(null);

export const SiteProvider = ({ children }) => {
  const [sites, setSites] = useState([]);
  const [currentSite, setCurrentSite] = useState(null);
  const [loading, setLoading] = useState(true);
  const { token, isAuthenticated, getAuthHeaders } = useAuth();

  useEffect(() => {
    if (isAuthenticated) {
      fetchSites();
    } else {
      setSites([]);
      setCurrentSite(null);
      setLoading(false);
    }
  }, [isAuthenticated, token]);

  const fetchSites = async () => {
    try {
      const response = await axios.get(`${API}/wordpress/sites`, { headers: getAuthHeaders() });
      setSites(response.data);
      
      // Restore selected site from localStorage or pick first
      const savedSiteId = localStorage.getItem('currentSiteId');
      if (savedSiteId && response.data.find(s => s.id === savedSiteId)) {
        setCurrentSite(response.data.find(s => s.id === savedSiteId));
      } else if (response.data.length > 0) {
        setCurrentSite(response.data[0]);
        localStorage.setItem('currentSiteId', response.data[0].id);
      }
    } catch (error) {
      console.error('Failed to fetch sites:', error);
    } finally {
      setLoading(false);
    }
  };

  const selectSite = (site) => {
    setCurrentSite(site);
    if (site) {
      localStorage.setItem('currentSiteId', site.id);
    } else {
      localStorage.removeItem('currentSiteId');
    }
  };

  const refreshSites = () => {
    fetchSites();
  };

  return (
    <SiteContext.Provider value={{
      sites,
      currentSite,
      loading,
      selectSite,
      refreshSites,
      currentSiteId: currentSite?.id || null
    }}>
      {children}
    </SiteContext.Provider>
  );
};

export const useSite = () => {
  const context = useContext(SiteContext);
  if (!context) {
    throw new Error('useSite must be used within a SiteProvider');
  }
  return context;
};
