import api from './api';

export interface AdvisorClient {
  id: number;
  username: string;
  email?: string;
}

export const advisorService = {
  getDashboard: async (): Promise<{ total_clients: number; active_portfolios: number; total_alerts: number; pending_reviews: number; }> => {
    const res = await api.get('/advisor/dashboard');
    return res.data;
  },
  // Fetch clients of current advisor; backend route to be provided
  getClients: async (): Promise<AdvisorClient[]> => {
    try {
      const res = await api.get('/advisor/clients');
      return res.data?.clients || res.data || [];
    } catch (e) {
      // Graceful fallback when API not implemented yet
      return [];
    }
  },
  getClientSummary: async (clientId: number): Promise<any> => {
    const res = await api.get(`/advisor/clients/${clientId}/summary`);
    return res.data;
  },
  getClientPortfolio: async (clientId: number): Promise<any[]> => {
    const res = await api.get('/advisor/portfolios', { params: { client_id: clientId } });
    return res.data || [];
  },
  getReports: async (clientId: number, extraParams?: any): Promise<any[]> => {
    const res = await api.get('/advisor/reports', { params: { client_id: clientId, ...(extraParams || {}) } });
    return res.data || [];
  },
  getAnalytics: async (clientId: number): Promise<any> => {
    const res = await api.get('/advisor/analytics', { params: { client_id: clientId } });
    return res.data;
  },
  getReturns: async (clientId: number, days = 30): Promise<{days:number; equity: {date:string; value:number; change_pct:number}[]}> => {
    const res = await api.get('/advisor/analytics/returns', { params: { client_id: clientId, days } });
    return res.data;
  },
  generateReport: async (clientId: number, payload?: { title?: string; start?: string; end?: string }): Promise<any> => {
    const res = await api.post('/advisor/reports/generate', null, { params: { client_id: clientId, ...(payload || {}) } });
    return res.data;
  },
  getReport: async (reportId: number): Promise<any> => {
    const res = await api.get(`/advisor/reports/${reportId}`);
    return res.data;
  },
};


