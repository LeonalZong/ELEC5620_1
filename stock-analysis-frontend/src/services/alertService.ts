import api from './api';
import { Alert, AlertSummary } from '@/types';

export const alertService = {
  // Get all alerts for current user
  getAlerts: async (): Promise<Alert[]> => {
    const response = await api.get('/alerts');
    return response.data;
  },

  // Get active alerts
  getActiveAlerts: async (): Promise<Alert[]> => {
    const response = await api.get('/alerts/active');
    return response.data;
  },

  // Get alert summary
  getAlertSummary: async (): Promise<AlertSummary> => {
    const response = await api.get('/alerts/summary');
    return response.data;
  },

  // Acknowledge an alert
  acknowledgeAlert: async (alertId: number): Promise<void> => {
    await api.post(`/alerts/${alertId}/acknowledge`);
  },

  // Update alert threshold
  updateAlertThreshold: async (alertId: number, newThreshold: number): Promise<void> => {
    await api.put(`/alerts/${alertId}/threshold`, { newThreshold });
  },
};






