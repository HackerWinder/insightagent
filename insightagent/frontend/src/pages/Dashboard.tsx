import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { 
  Plus, 
  Trash2,
  CheckCircle, 
  Loader, 
  TrendingUp, 
  BarChart3, 
  Zap,
  Search,
  Eye,
  Calendar
} from 'lucide-react';
import { useAppStore } from '../store/appStore';
import { taskApi } from '../services/api';
import CircularProgress from '../components/CircularProgress';

const Dashboard: React.FC = () => {
  const [productName, setProductName] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [deleteConfirm, setDeleteConfirm] = useState<string | null>(null);
  const [deletingTasks, setDeletingTasks] = useState<Set<string>>(new Set());
  const { addNotification } = useAppStore();

  // 获取任务列表
  const { data: tasks = [], refetch, isLoading } = useQuery({
    queryKey: ['tasks'],
    queryFn: taskApi.getTasks,
    refetchInterval: 2000,
  });

  // 创建任务
  const handleCreateTask = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!productName.trim()) return;

    setIsCreating(true);
    try {
      await taskApi.createTask(productName.trim());
      setProductName('');
      addNotification({
        type: 'success',
        title: '任务创建成功',
        message: `正在分析产品: ${productName}`,
      });
      refetch();
    } catch (error) {
      addNotification({
        type: 'error',
        title: '任务创建失败',
        message: '请检查网络连接或稍后重试',
      });
    } finally {
      setIsCreating(false);
    }
  };

  // 删除任务
  const handleDeleteTask = async (taskId: string) => {
    setDeletingTasks(prev => {
      const newSet = new Set(prev);
      newSet.add(taskId);
      return newSet;
    });
    try {
      await taskApi.deleteTask(taskId);
      addNotification({
        type: 'success',
        title: '任务删除成功',
        message: '任务已从列表中移除',
      });
      refetch();
    } catch (error) {
      addNotification({
        type: 'error',
        title: '删除失败',
        message: '请稍后重试',
      });
    } finally {
      setDeletingTasks(prev => {
        const newSet = new Set(prev);
        newSet.delete(taskId);
        return newSet;
      });
      setDeleteConfirm(null);
    }
  };

  const getStatusConfig = (status: string, progress: number = 0) => {
    switch (status) {
      case 'completed':
        return {
          progress: 100,
          text: '已完成',
          color: 'text-emerald-600',
          bg: 'bg-emerald-50',
          border: 'border-emerald-200',
          badge: 'bg-emerald-100 text-emerald-800'
        };
      case 'failed':
        return {
          progress: 0,
          text: '失败',
          color: 'text-red-600',
          bg: 'bg-red-50',
          border: 'border-red-200',
          badge: 'bg-red-100 text-red-800'
        };
      case 'running':
        return {
          progress: Math.max(progress || 0, 5), // 确保运行中的任务至少显示5%进度
          text: '分析中',
          color: 'text-blue-600',
          bg: 'bg-blue-50',
          border: 'border-blue-200',
          badge: 'bg-blue-100 text-blue-800'
        };
      default:
        return {
          progress: 0,
          text: '等待中',
          color: 'text-amber-600',
          bg: 'bg-amber-50',
          border: 'border-amber-200',
          badge: 'bg-amber-100 text-amber-800'
        };
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleString('zh-CN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const completedTasks = tasks.filter((task: any) => task.status === 'completed').length;
  const runningTasks = tasks.filter((task: any) => task.status === 'running').length;
  const totalTasks = tasks.length;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-indigo-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* 页面标题 */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            <span className="bg-gradient-to-r from-indigo-600 to-purple-600 bg-clip-text text-transparent">
              InsightAgent
            </span>
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            智能市场洞察分析平台，自动收集和分析市场数据，生成深度用户洞察报告
          </p>
        </div>

        {/* 统计卡片 */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border border-white/50 p-6">
            <div className="flex items-center">
              <div className="p-3 bg-gradient-to-r from-indigo-500 to-purple-500 rounded-xl">
                <TrendingUp className="h-6 w-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">总任务数</p>
                <p className="text-2xl font-bold text-gray-900">{totalTasks}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border border-white/50 p-6">
            <div className="flex items-center">
              <div className="p-3 bg-gradient-to-r from-emerald-500 to-teal-500 rounded-xl">
                <CheckCircle className="h-6 w-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">已完成</p>
                <p className="text-2xl font-bold text-gray-900">{completedTasks}</p>
              </div>
            </div>
          </div>
          
          <div className="bg-white/80 backdrop-blur-sm rounded-2xl shadow-lg border border-white/50 p-6">
            <div className="flex items-center">
              <div className="p-3 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-xl">
                <Zap className="h-6 w-6 text-white" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">进行中</p>
                <p className="text-2xl font-bold text-gray-900">{runningTasks}</p>
              </div>
            </div>
          </div>
        </div>

        {/* 创建任务表单 */}
        <div className="bg-white/80 backdrop-blur-sm rounded-3xl shadow-xl border border-white/50 mb-8">
          <div className="px-8 py-6 border-b border-gray-100">
            <h3 className="text-2xl font-bold text-gray-900">创建新任务</h3>
            <p className="text-gray-600 mt-1">输入产品名称，开始市场洞察分析</p>
          </div>
          
          <div className="px-8 py-6">
            <form onSubmit={handleCreateTask} className="flex gap-4">
              <div className="flex-1">
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <input
                    type="text"
                    value={productName}
                    onChange={(e) => setProductName(e.target.value)}
                    placeholder="输入产品名称，如：iPhone 15 Pro、Tesla Model Y..."
                    className="w-full pl-10 pr-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all duration-200"
                    disabled={isCreating}
                  />
                </div>
              </div>
              <div className="flex-shrink-0">
                <button
                  type="submit"
                  disabled={!productName.trim() || isCreating}
                  className="inline-flex items-center px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-medium rounded-xl shadow-lg hover:from-indigo-700 hover:to-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-105"
                >
                  {isCreating ? (
                    <>
                      <Loader className="h-4 w-4 mr-2 animate-spin" />
                      创建中...
                    </>
                  ) : (
                    <>
                      <Plus className="h-4 w-4 mr-2" />
                      开始分析
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>

        {/* 任务列表 */}
        <div className="bg-white/80 backdrop-blur-sm rounded-3xl shadow-xl border border-white/50 overflow-hidden">
          <div className="px-8 py-6 border-b border-gray-100">
            <h3 className="text-2xl font-bold text-gray-900">任务列表</h3>
            <p className="text-gray-600 mt-1">管理您的市场洞察分析任务</p>
          </div>
          
          <div className="divide-y divide-gray-100">
            {isLoading ? (
              <div className="px-8 py-12 text-center">
                <Loader className="h-8 w-8 animate-spin mx-auto text-blue-600 mb-4" />
                <p className="text-gray-500">加载中...</p>
              </div>
            ) : tasks.length === 0 ? (
              <div className="px-8 py-16 text-center">
                <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <BarChart3 className="h-8 w-8 text-gray-400" />
                </div>
                <h4 className="text-lg font-semibold text-gray-900 mb-2">暂无任务</h4>
                <p className="text-gray-500 mb-6">创建您的第一个市场洞察任务，开始数据分析之旅</p>
              </div>
            ) : (
              tasks.map((task: any) => {
                const statusConfig = getStatusConfig(task.status, task.progress);
                const isDeleting = deletingTasks.has(task.id);
                
                return (
                  <div key={task.id} className="px-8 py-6 hover:bg-gray-50/50 transition-colors duration-200">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center space-x-4">
                        <div className="relative">
                          <CircularProgress
                            progress={statusConfig.progress}
                            size={48}
                            strokeWidth={4}
                            showPercentage={task.status === 'running'}
                            status={task.status}
                          />
                        </div>
                        <div>
                          <h4 className="text-lg font-semibold text-gray-900">
                            {task.product_name}
                          </h4>
                          <div className="flex items-center text-sm text-gray-500 mt-1">
                            <Calendar className="h-4 w-4 mr-1" />
                            创建时间: {formatDate(task.created_at)}
                          </div>
                          {task.status === 'running' && (
                            <div className="text-sm text-blue-600 mt-1">
                              进度: {Math.round(task.progress || 0)}%
                            </div>
                          )}
                        </div>
                      </div>
                      
                      <div className="flex items-center space-x-4">
                        <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${statusConfig.badge}`}>
                          {statusConfig.text}
                        </span>
                        
                        {task.status === 'completed' && (
                          <a
                            href={`/tasks/${task.id}`}
                            className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-medium rounded-xl shadow-lg hover:from-indigo-700 hover:to-purple-700 transition-all duration-200 transform hover:scale-105"
                          >
                            <Eye className="h-4 w-4 mr-2" />
                            查看报告
                          </a>
                        )}
                        
                        {/* 删除按钮 - 只有非运行中的任务才显示 */}
                        {task.status !== 'running' && (
                          <button
                            onClick={() => setDeleteConfirm(task.id)}
                            disabled={isDeleting}
                            className="inline-flex items-center px-3 py-2 text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-all duration-200"
                            title="删除任务"
                          >
                            {isDeleting ? (
                              <Loader className="h-4 w-4 animate-spin" />
                            ) : (
                              <Trash2 className="h-4 w-4" />
                            )}
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>

      {/* 删除确认对话框 */}
      {deleteConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl p-6 max-w-md w-mx-4 shadow-2xl">
            <div className="flex items-center mb-4">
              <div className="p-3 bg-red-100 rounded-full mr-4">
                <Trash2 className="h-6 w-6 text-red-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">确认删除</h3>
                <p className="text-sm text-gray-500">此操作无法撤销</p>
              </div>
            </div>
            <p className="text-gray-700 mb-6">
              确定要删除这个任务吗？所有相关数据都将被永久删除。
            </p>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setDeleteConfirm(null)}
                className="px-4 py-2 text-gray-600 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              >
                取消
              </button>
              <button
                onClick={() => handleDeleteTask(deleteConfirm)}
                className="px-4 py-2 bg-red-600 text-white hover:bg-red-700 rounded-lg transition-colors"
              >
                删除
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;
