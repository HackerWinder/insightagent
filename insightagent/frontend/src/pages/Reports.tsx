import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { taskApi } from '../services/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import CircularProgress from '../components/CircularProgress';

const Reports: React.FC = () => {
  const { data: tasks = [] } = useQuery({
    queryKey: ['tasks'],
    queryFn: taskApi.getTasks,
    refetchInterval: 2000,
  });

  // 统计数据
  const completedTasks = tasks.filter((task: any) => task.status === 'completed');
  const totalTasks = tasks.length;
  const completionRate = totalTasks > 0 ? (completedTasks.length / totalTasks) * 100 : 0;

  // 状态分布数据
  const statusData = [
    { name: '已完成', value: completedTasks.length, color: '#10B981' },
    { name: '进行中', value: tasks.filter((t: any) => t.status === 'running').length, color: '#3B82F6' },
    { name: '等待中', value: tasks.filter((t: any) => t.status === 'pending').length, color: '#F59E0B' },
    { name: '失败', value: tasks.filter((t: any) => t.status === 'failed').length, color: '#EF4444' },
  ];

  // 最近任务趋势数据
  const recentTasks = tasks.slice(0, 7).reverse();
  const trendData = recentTasks.map((task: any, index: number) => ({
    name: `任务 ${index + 1}`,
    完成: task.status === 'completed' ? 1 : 0,
    进行中: task.status === 'running' ? 1 : 0,
  }));

  const getStatusConfig = (status: string, progress: number = 0) => {
    switch (status) {
      case 'completed':
        return {
          progress: 100,
          text: '已完成',
          badge: 'bg-green-100 text-green-800'
        };
      case 'failed':
        return {
          progress: 0,
          text: '失败',
          badge: 'bg-red-100 text-red-800'
        };
      case 'running':
        return {
          progress: Math.max(progress, 10),
          text: '分析中',
          badge: 'bg-blue-100 text-blue-800'
        };
      default:
        return {
          progress: 0,
          text: '等待中',
          badge: 'bg-yellow-100 text-yellow-800'
        };
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">数据报告</h1>
        <p className="text-gray-600">查看任务统计和分析数据</p>
      </div>

      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-blue-500 rounded-md flex items-center justify-center">
                  <span className="text-white font-bold text-sm">总</span>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">总任务数</dt>
                  <dd className="text-lg font-medium text-gray-900">{totalTasks}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-green-500 rounded-md flex items-center justify-center">
                  <span className="text-white font-bold text-sm">完</span>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">已完成</dt>
                  <dd className="text-lg font-medium text-gray-900">{completedTasks.length}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-yellow-500 rounded-md flex items-center justify-center">
                  <span className="text-white font-bold text-sm">进</span>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">进行中</dt>
                  <dd className="text-lg font-medium text-gray-900">{tasks.filter((t: any) => t.status === 'running').length}</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-8 h-8 bg-purple-500 rounded-md flex items-center justify-center">
                  <span className="text-white font-bold text-sm">率</span>
                </div>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">完成率</dt>
                  <dd className="text-lg font-medium text-gray-900">{completionRate.toFixed(1)}%</dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 图表区域 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* 状态分布饼图 */}
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">任务状态分布</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={statusData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(props: any) => `${props.name} ${(props.percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {statusData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* 任务趋势柱状图 */}
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">最近任务趋势</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="完成" stackId="a" fill="#10B981" />
              <Bar dataKey="进行中" stackId="a" fill="#3B82F6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* 最近任务列表 */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">最近任务</h3>
        </div>
        <div className="divide-y divide-gray-200">
          {tasks.slice(0, 5).map((task: any) => {
            const statusConfig = getStatusConfig(task.status, task.progress);
            return (
              <div key={task.id} className="px-6 py-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4">
                    <CircularProgress
                      progress={statusConfig.progress}
                      size={40}
                      strokeWidth={3}
                      showPercentage={task.status === 'running'}
                      status={task.status}
                    />
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">{task.product_name}</h4>
                      <p className="text-sm text-gray-500">
                        {new Date(task.created_at).toLocaleString('zh-CN')}
                      </p>
                      {task.status === 'running' && (
                        <p className="text-xs text-blue-600">
                          进度: {Math.round(task.progress || 0)}%
                        </p>
                      )}
                    </div>
                  </div>
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${statusConfig.badge}`}>
                    {statusConfig.text}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default Reports;
