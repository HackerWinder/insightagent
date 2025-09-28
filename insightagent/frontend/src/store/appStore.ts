import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

export interface Task {
  id: string;
  product_name: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  created_at: string;
  updated_at: string;
  result?: {
    market_analysis: {
      market_size: string;
      target_audience: string;
      competitive_landscape: string;
      market_trends: string;
    };
    product_analysis: {
      strengths: string[];
      weaknesses: string[];
      opportunities: string[];
      threats: string[];
    };
    recommendations: {
      short_term: string[];
      medium_term: string[];
      long_term: string[];
    };
    data_visualization: {
      charts: Array<{
        type: string;
        title: string;
        data: any;
      }>;
    };
  };
}

export interface Notification {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  title: string;
  message: string;
  duration?: number;
}

interface AppState {
  tasks: Task[];
  currentTask: Task | null;
  notifications: Notification[];
  wsConnected: boolean;
  wsReconnecting: boolean;
  sidebarOpen: boolean;
  
  // 任务管理方法
  setTasks: (tasks: Task[]) => void;
  addTask: (task: Task) => void;
  updateTask: (taskId: string, updates: Partial<Task>) => void;
  setCurrentTask: (task: Task | null) => void;
  getTaskById: (taskId: string) => Task | null;
  
  // 通知管理方法
  addNotification: (notification: Omit<Notification, 'id'>) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
  
  // WebSocket 状态方法
  setWsConnected: (connected: boolean) => void;
  setWsReconnecting: (reconnecting: boolean) => void;
  
  // 侧边栏状态方法
  setSidebarOpen: (open: boolean) => void;
  
  // 重置状态
  reset: () => void;
}

const initialState: Omit<AppState, 
  'setTasks' | 'addTask' | 'updateTask' | 'setCurrentTask' | 'getTaskById' |
  'addNotification' | 'removeNotification' | 'clearNotifications' |
  'setWsConnected' | 'setWsReconnecting' | 'setSidebarOpen' | 'reset'
> = {
  tasks: [],
  currentTask: null,
  notifications: [],
  wsConnected: false,
  wsReconnecting: false,
  sidebarOpen: true,
};

export const useAppStore = create<AppState>()(
  devtools(
    (set, get) => ({
      ...initialState,

      // 任务管理
      setTasks: (tasks: Task[]) => set({ tasks }),
      
      addTask: (task: Task) => set((state) => ({
        tasks: [task, ...state.tasks]
      })),
      
      updateTask: (taskId: string, updates: Partial<Task>) => set((state) => ({
        tasks: state.tasks.map(task => 
          task.id === taskId ? { ...task, ...updates } : task
        )
      })),
      
      setCurrentTask: (task: Task | null) => set({ currentTask: task }),
      
      getTaskById: (taskId: string) => {
        const state = get();
        return state.tasks.find(task => task.id === taskId) || null;
      },

      // 通知管理
      addNotification: (notification: Omit<Notification, 'id'>) => {
        const id = Date.now().toString();
        const newNotification: Notification = {
          id,
          type: notification.type,
          title: notification.title,
          message: notification.message,
          duration: notification.duration || 5000,
        };
        
        set((state) => ({
          notifications: [newNotification, ...state.notifications].slice(0, 10)
        }));
        
        if (newNotification.duration && newNotification.duration > 0) {
          setTimeout(() => {
            set((state) => ({
              notifications: state.notifications.filter(n => n.id !== id)
            }));
          }, newNotification.duration);
        }
      },

      removeNotification: (id: string) => set((state) => ({
        notifications: state.notifications.filter(n => n.id !== id)
      })),

      clearNotifications: () => set({ notifications: [] }),

      // WebSocket 状态
      setWsConnected: (connected: boolean) => set({ wsConnected: connected }),
      
      setWsReconnecting: (reconnecting: boolean) => set({ wsReconnecting: reconnecting }),

      // 侧边栏状态
      setSidebarOpen: (open: boolean) => set({ sidebarOpen: open }),

      // 重置状态
      reset: () => set(initialState),
    }),
    {
      name: 'app-store',
    }
  )
);
