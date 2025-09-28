import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { Task, TaskStatus, TaskLog, AnalysisResult } from '../types';

interface TaskState {
  tasks: Task[];
  currentTask: Task | null;
  taskLogs: Map<string, TaskLog[]>;
  
  // 任务管理方法
  setTasks: (tasks: Task[]) => void;
  addTask: (task: Task) => void;
  updateTask: (taskId: string, updates: Partial<Task>) => void;
  removeTask: (taskId: string) => void;
  setCurrentTask: (task: Task | null) => void;
  getTaskById: (taskId: string) => Task | null;
  
  // 任务日志管理
  addTaskLog: (taskId: string, log: TaskLog) => void;
  getTaskLogs: (taskId: string) => TaskLog[];
  clearTaskLogs: (taskId: string) => void;
  
  // 任务状态更新
  updateTaskStatus: (taskId: string, status: TaskStatus) => void;
  updateTaskProgress: (taskId: string, progress: number) => void;
  updateTaskResult: (taskId: string, result: AnalysisResult) => void;
  
  // 任务筛选和排序
  getTasksByStatus: (status: TaskStatus) => Task[];
  getRecentTasks: (limit?: number) => Task[];
  getCompletedTasks: () => Task[];
  getRunningTasks: () => Task[];
  
  // 统计信息
  getTaskStats: () => {
    total: number;
    completed: number;
    running: number;
    failed: number;
    pending: number;
    completionRate: number;
  };
  
  // 重置状态
  reset: () => void;
}

const initialState = {
  tasks: [],
  currentTask: null,
  taskLogs: new Map(),
};

export const useTaskStore = create<TaskState>()(
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

      removeTask: (taskId: string) => set((state) => ({
        tasks: state.tasks.filter(task => task.id !== taskId)
      })),

      setCurrentTask: (task: Task | null) => set({ currentTask: task }),

      getTaskById: (taskId: string) => {
        const state = get();
        return state.tasks.find(task => task.id === taskId) || null;
      },

      // 任务日志管理
      addTaskLog: (taskId: string, log: TaskLog) => set((state) => {
        const newLogs = new Map(state.taskLogs);
        const existingLogs = newLogs.get(taskId) || [];
        newLogs.set(taskId, [...existingLogs, log]);
        return { taskLogs: newLogs };
      }),

      getTaskLogs: (taskId: string) => {
        const state = get();
        return state.taskLogs.get(taskId) || [];
      },

      clearTaskLogs: (taskId: string) => set((state) => {
        const newLogs = new Map(state.taskLogs);
        newLogs.delete(taskId);
        return { taskLogs: newLogs };
      }),

      // 任务状态更新
      updateTaskStatus: (taskId: string, status: TaskStatus) => set((state) => ({
        tasks: state.tasks.map(task => 
          task.id === taskId ? { ...task, status, updated_at: new Date().toISOString() } : task
        )
      })),

      updateTaskProgress: (taskId: string, progress: number) => set((state) => ({
        tasks: state.tasks.map(task => 
          task.id === taskId ? { ...task, progress, updated_at: new Date().toISOString() } : task
        )
      })),

      updateTaskResult: (taskId: string, result: AnalysisResult) => set((state) => ({
        tasks: state.tasks.map(task => 
          task.id === taskId ? { ...task, result, updated_at: new Date().toISOString() } : task
        )
      })),

      // 任务筛选和排序
      getTasksByStatus: (status: TaskStatus) => {
        const state = get();
        return state.tasks.filter(task => task.status === status);
      },

      getRecentTasks: (limit = 10) => {
        const state = get();
        return state.tasks
          .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
          .slice(0, limit);
      },

      getCompletedTasks: () => {
        const state = get();
        return state.tasks.filter(task => task.status === TaskStatus.COMPLETED);
      },

      getRunningTasks: () => {
        const state = get();
        return state.tasks.filter(task => task.status === TaskStatus.RUNNING);
      },

      // 统计信息
      getTaskStats: () => {
        const state = get();
        const total = state.tasks.length;
        const completed = state.tasks.filter(task => task.status === TaskStatus.COMPLETED).length;
        const running = state.tasks.filter(task => task.status === TaskStatus.RUNNING).length;
        const failed = state.tasks.filter(task => task.status === TaskStatus.FAILED).length;
        const pending = state.tasks.filter(task => task.status === TaskStatus.QUEUED).length;
        const completionRate = total > 0 ? (completed / total) * 100 : 0;

        return {
          total,
          completed,
          running,
          failed,
          pending,
          completionRate,
        };
      },

      // 重置状态
      reset: () => set(initialState),
    }),
    {
      name: 'task-store',
    }
  )
);

// 导出类型
export type { TaskState };
