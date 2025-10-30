import api from './api';
import { Stock, TrackedStock, StockData, StockAnalysis } from '@/types';

export const stockService = {
  // Get all stocks
  getStocks: async (params?: { skip?: number; limit?: number }): Promise<Stock[]> => {
    const response = await api.get('/stocks', { params });
    return response.data;
  },

  // Get stock by symbol
  getStockBySymbol: async (symbol: string): Promise<Stock> => {
    const response = await api.get(`/stocks/${symbol}`);
    return response.data;
  },

  // Search stocks
  searchStocks: async (query: string): Promise<Stock[]> => {
    const response = await api.get('/stocks/search', { params: { q: query } });
    return response.data;
  },

  // Get tracked stocks
  getTrackedStocks: async (): Promise<TrackedStock[]> => {
    const response = await api.get('/portfolio/tracked');
    return response.data;
  },

  // Track a stock
  trackStock: async (symbol: string, customThreshold?: number): Promise<TrackedStock> => {
    const response = await api.post('/portfolio/track', {
      symbol,
      custom_alert_threshold: customThreshold,
    });
    return response.data;
  },

  // Untrack a stock
  untrackStock: async (symbol: string): Promise<void> => {
    await api.delete(`/portfolio/untrack/${symbol}`);
  },

  // Get stock data (historical)
  getStockData: async (symbol: string, period: string = '1mo'): Promise<StockData[]> => {
    const response = await api.get(`/stocks/${symbol}/data`, {
      params: { period },
    });
    return response.data;
  },

  // Get stock analysis
  getStockAnalysis: async (symbol: string): Promise<StockAnalysis> => {
    const response = await api.get(`/stocks/${symbol}/analysis`);
    return response.data;
  },

  // Get portfolio summary
  getPortfolioSummary: async (): Promise<any> => {
    const response = await api.get('/portfolio/summary');
    return response.data;
  },
};

