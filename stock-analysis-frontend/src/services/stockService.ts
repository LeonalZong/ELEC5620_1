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
    return response.data.results || [];
  },

  // Get tracked stocks
  getTrackedStocks: async (): Promise<TrackedStock[]> => {
    const response = await api.get('/stocks/tracked');
    return response.data;
  },

  // Track a stock
  trackStock: async (
    symbol: string, 
    customThreshold?: number,
    quantity?: number,
    purchasePrice?: number
  ): Promise<TrackedStock> => {
    const response = await api.post('/stocks/track', {
      symbol,
      custom_alert_threshold: customThreshold,
      quantity,
      purchase_price: purchasePrice,
    });
    return response.data;
  },

  // Update alert threshold for a tracked stock
  updateTrackThreshold: async (symbol: string, threshold?: number): Promise<void> => {
    await api.put(`/stocks/track/${symbol}/threshold`, {
      symbol,
      custom_alert_threshold: threshold,
    });
  },

  // Untrack a stock
  untrackStock: async (symbol: string): Promise<void> => {
    await api.delete(`/stocks/track/${symbol}`);
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

  // Update portfolio holding
  updatePortfolio: async (
    symbol: string,
    quantity: number,
    purchasePrice: number
  ): Promise<void> => {
    await api.put(`/stocks/track/${symbol}/portfolio`, null, {
      params: {
        quantity,
        purchase_price: purchasePrice
      }
    });
  },
};


