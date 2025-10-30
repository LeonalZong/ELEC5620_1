import api from './api';
import { Report, ReportSummary } from '@/types';

export const reportService = {
  // Generate a new report
  generateReport: async (stockId: number, reportType: string): Promise<Report> => {
    const response = await api.post('/reports/generate', {
      stock_id: stockId,
      report_type: reportType,
    });
    return response.data;
  },

  // Get all reports for current user
  getReports: async (): Promise<Report[]> => {
    const response = await api.get('/reports');
    return response.data;
  },

  // Get report summary
  getReportSummary: async (): Promise<ReportSummary> => {
    const response = await api.get('/reports/summary');
    return response.data;
  },

  // Get report by ID
  getReport: async (reportId: number): Promise<Report> => {
    const response = await api.get(`/reports/${reportId}`);
    return response.data;
  },
};






