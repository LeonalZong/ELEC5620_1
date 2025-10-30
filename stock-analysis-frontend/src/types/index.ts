// User Types
export enum UserRole {
  INVESTOR = 'INVESTOR',
  ADVISOR = 'ADVISOR',
  ADMIN = 'ADMIN',
}

export interface User {
  id: number;
  username: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
  last_login?: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  role?: UserRole;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

// Stock Types
export interface Stock {
  id: number;
  symbol: string;
  name: string;
  sector?: string;
  industry?: string;
  market_cap?: number;
  current_price: number;
  currency: string;
  exchange?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface StockData {
  id: number;
  stock_id: number;
  date: string;
  open_price: number;
  close_price: number;
  high_price: number;
  low_price: number;
  volume: number;
  adjusted_close?: number;
}

export interface Portfolio {
  id: number;
  quantity: number;
  purchase_price: number;
  purchase_date: string;
  current_value: number;
  cost_basis: number;
  profit_loss: number;
  profit_loss_pct: number;
}

export interface TrackedStock {
  id: number;
  user_id: number;
  stock_id: number;
  stock: Stock;
  custom_alert_threshold?: number;
  is_active: string;  // "Y" or "N"
  created_at: string;
  updated_at: string;
  portfolio?: Portfolio | null;  // Portfolio information if exists
}

// Alert Types
export enum AlertType {
  PRICE_DROP = 'price_drop',
  PRICE_RISE = 'price_rise',
  VOLUME_SPIKE = 'volume_spike',
  NEWS_ALERT = 'news_alert',
}

export enum AlertStatus {
  PENDING = 'pending',
  TRIGGERED = 'triggered',
  ACKNOWLEDGED = 'acknowledged',
}

export interface Alert {
  id: number;
  user_id: number;
  stock_id: number;
  stock?: Stock;
  alert_type: AlertType;
  threshold_value?: number;
  current_value?: number;
  trigger_count?: number;  // Cumulative trigger count
  trigger_history?: Array<{  // History of trigger events
    timestamp: string;
    price: number;
    change_percent: number;
    baseline_price: number;
  }>;
  required_triggers?: number;  // How many triggers needed to fire alert
  message: string;
  status: AlertStatus;
  triggered_at?: string;
  acknowledged_at?: string;
  created_at: string;
}

export interface AlertSummary {
  total_alerts: number;
  pending_alerts: number;
  triggered_alerts: number;
  acknowledged_alerts: number;
}

// Report Types
export interface Report {
  id: number;
  user_id: number;
  stock_id: number;
  stock?: Stock;
  report_type: string;
  title: string;
  summary: string;
  content?: string;
  recommendations?: string;
  risk_level?: string;
  sentiment_score?: number;
  technical_signal?: string;
  confidence_score?: number;
  generated_at?: string;
  created_at: string;
}

export interface ReportSummary {
  total_reports: number;
  recent_reports: number;
  risk_distribution: {
    LOW: number;
    MEDIUM: number;
    HIGH: number;
  };
  sentiment_distribution: {
    POSITIVE: number;
    NEUTRAL: number;
    NEGATIVE: number;
  };
}

// News Types
export interface News {
  id: number;
  stock_id: number;
  title: string;
  description?: string;
  url: string;
  source: string;
  published_at: string;
  sentiment?: string;
  created_at: string;
}

// Analysis Types
export interface StockAnalysis {
  technical_analysis: {
    trend: string;
    strength: string;
    recommendation: string;
    daily_change: number;
    weekly_change: number;
    monthly_change: number;
  };
  risk_analysis: {
    risk_level: string;
    risk_score: number;
    risk_factors: string[];
    volatility: number;
    beta: number;
    recommendation: string;
  };
  sentiment_analysis: {
    overall_sentiment: string;
    sentiment_score: number;
    key_factors: string[];
    confidence: number;
  };
}

// API Response Types
export interface ApiResponse<T = any> {
  data?: T;
  message?: string;
  error?: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

