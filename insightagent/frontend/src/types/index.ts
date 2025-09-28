// 任务相关类型
export interface Task {
  id: string;
  product_name: string;
  status: TaskStatus;
  progress: number;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  user_id: string;
  result?: AnalysisResult;
  logs?: TaskLog[];
}

export enum TaskStatus {
  QUEUED = 'QUEUED',
  RUNNING = 'RUNNING',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
  CANCELLED = 'CANCELLED'
}

export interface TaskLog {
  id: string;
  task_id: string;
  level: LogLevel;
  message: string;
  step?: string;
  created_at: string;
}

export enum LogLevel {
  DEBUG = 'DEBUG',
  INFO = 'INFO',
  WARNING = 'WARNING',
  ERROR = 'ERROR'
}

// 分析结果类型
export interface AnalysisResult {
  id: string;
  task_id: string;
  market_analysis: MarketAnalysis;
  product_analysis: ProductAnalysis;
  recommendations: Recommendations;
  data_visualization: DataVisualization;
  created_at: string;
}

export interface MarketAnalysis {
  market_size: string;
  target_audience: string;
  competitive_landscape: string;
  market_trends: string;
}

export interface ProductAnalysis {
  strengths: string[];
  weaknesses: string[];
  opportunities: string[];
  threats: string[];
}

export interface Recommendations {
  short_term: string[];
  medium_term: string[];
  long_term: string[];
}

export interface DataVisualization {
  charts: Chart[];
}

export interface Chart {
  type: string;
  title: string;
  data: any;
}

// API响应类型
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
}

export interface PaginatedResponse<T> extends ApiResponse<T[]> {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// WebSocket消息类型
export interface WebSocketMessage {
  type: 'task_update' | 'task_log' | 'system_status' | 'error';
  data: any;
  timestamp: string;
}

export interface TaskUpdateMessage {
  task_id: string;
  status: TaskStatus;
  progress: number;
  message?: string;
}

export interface TaskLogMessage {
  task_id: string;
  level: LogLevel;
  message: string;
  step?: string;
}

// 通知类型
export interface Notification {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  title: string;
  message: string;
  duration?: number;
  created_at: string;
}

// 工具类型
export interface Tool {
  name: string;
  description: string;
  enabled: boolean;
  config: Record<string, any>;
}

// 系统监控类型
export interface SystemStatus {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  services: ServiceStatus[];
  metrics: SystemMetrics;
}

export interface ServiceStatus {
  name: string;
  status: 'up' | 'down' | 'degraded';
  response_time?: number;
  last_check: string;
}

export interface SystemMetrics {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  active_tasks: number;
  queue_size: number;
}

// 队列状态类型
export interface QueueStats {
  total_tasks: number;
  pending_tasks: number;
  running_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  average_processing_time: number;
}

// 用户类型
export interface User {
  id: string;
  username: string;
  email: string;
  created_at: string;
  last_login?: string;
}

// 表单类型
export interface TaskCreateForm {
  product_name: string;
  priority?: 'low' | 'normal' | 'high';
  options?: Record<string, any>;
}

export interface TaskUpdateForm {
  status?: TaskStatus;
  progress?: number;
  result?: AnalysisResult;
}

// 路由类型
export interface RouteConfig {
  path: string;
  component: React.ComponentType;
  exact?: boolean;
  protected?: boolean;
}

// 状态管理类型
export interface AppState {
  tasks: Task[];
  currentTask: Task | null;
  notifications: Notification[];
  wsConnected: boolean;
  wsReconnecting: boolean;
  sidebarOpen: boolean;
  systemStatus: SystemStatus | null;
  queueStats: QueueStats | null;
}

// 错误类型
export interface AppError {
  code: string;
  message: string;
  details?: any;
  timestamp: string;
}

// 配置类型
export interface AppConfig {
  apiUrl: string;
  wsUrl: string;
  version: string;
  environment: 'development' | 'production' | 'test';
}
