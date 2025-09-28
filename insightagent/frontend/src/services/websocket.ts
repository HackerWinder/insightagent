import { io, Socket } from 'socket.io-client';
import { WebSocketMessage, TaskUpdateMessage, TaskLogMessage } from '../types';

class WebSocketService {
  private socket: Socket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectInterval = 3000;
  private listeners: Map<string, Function[]> = new Map();

  constructor() {
    this.connect();
  }

  private connect() {
    const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';
    
    this.socket = io(wsUrl, {
      transports: ['websocket'],
      timeout: 10000,
      reconnection: true,
      reconnectionAttempts: this.maxReconnectAttempts,
      reconnectionDelay: this.reconnectInterval,
    });

    this.setupEventListeners();
  }

  private setupEventListeners() {
    if (!this.socket) return;

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.emit('connection_status', { connected: true });
    });

    this.socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
      this.emit('connection_status', { connected: false, reason });
    });

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      this.emit('connection_error', error);
    });

    this.socket.on('task_update', (data: TaskUpdateMessage) => {
      console.log('Task update received:', data);
      this.emit('task_update', data);
    });

    this.socket.on('task_log', (data: TaskLogMessage) => {
      console.log('Task log received:', data);
      this.emit('task_log', data);
    });

    this.socket.on('system_status', (data: any) => {
      console.log('System status received:', data);
      this.emit('system_status', data);
    });

    this.socket.on('error', (error: any) => {
      console.error('WebSocket error:', error);
      this.emit('error', error);
    });
  }

  // 监听事件
  on(event: string, callback: Function) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event)!.push(callback);
  }

  // 移除监听器
  off(event: string, callback?: Function) {
    if (!this.listeners.has(event)) return;
    
    if (callback) {
      const callbacks = this.listeners.get(event)!;
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    } else {
      this.listeners.delete(event);
    }
  }

  // 触发事件
  private emit(event: string, data: any) {
    if (this.listeners.has(event)) {
      this.listeners.get(event)!.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in WebSocket event handler for ${event}:`, error);
        }
      });
    }
  }

  // 发送消息
  send(event: string, data: any) {
    if (this.socket && this.socket.connected) {
      this.socket.emit(event, data);
    } else {
      console.warn('WebSocket not connected, cannot send message');
    }
  }

  // 订阅任务更新
  subscribeToTask(taskId: string) {
    this.send('subscribe_task', { task_id: taskId });
  }

  // 取消订阅任务
  unsubscribeFromTask(taskId: string) {
    this.send('unsubscribe_task', { task_id: taskId });
  }

  // 获取连接状态
  isConnected(): boolean {
    return this.socket ? this.socket.connected : false;
  }

  // 手动重连
  reconnect() {
    if (this.socket) {
      this.socket.disconnect();
    }
    this.connect();
  }

  // 断开连接
  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
    this.listeners.clear();
  }

  // 获取连接统计
  getConnectionStats() {
    return {
      connected: this.isConnected(),
      reconnectAttempts: this.reconnectAttempts,
      listeners: this.listeners.size,
    };
  }
}

// 创建单例实例
export const websocketService = new WebSocketService();

// 导出类型
export type { WebSocketMessage, TaskUpdateMessage, TaskLogMessage };
