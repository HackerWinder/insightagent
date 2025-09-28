import React from 'react';

interface CircularProgressProps {
  progress: number; // 0-100
  size?: number;
  strokeWidth?: number;
  className?: string;
  showPercentage?: boolean;
  status?: 'pending' | 'running' | 'completed' | 'failed';
}

const CircularProgress: React.FC<CircularProgressProps> = ({
  progress,
  size = 40,
  strokeWidth = 3,
  className = '',
  showPercentage = false,
  status = 'running'
}) => {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDasharray = circumference;
  const strokeDashoffset = circumference - (progress / 100) * circumference;

  const getStatusColor = () => {
    switch (status) {
      case 'completed':
        return '#10b981'; // emerald-500
      case 'failed':
        return '#ef4444'; // red-500
      case 'running':
        return '#3b82f6'; // blue-500
      case 'pending':
        return '#f59e0b'; // amber-500
      default:
        return '#3b82f6';
    }
  };

  const getStatusBgColor = () => {
    switch (status) {
      case 'completed':
        return '#d1fae5'; // emerald-100
      case 'failed':
        return '#fee2e2'; // red-100
      case 'running':
        return '#dbeafe'; // blue-100
      case 'pending':
        return '#fef3c7'; // amber-100
      default:
        return '#dbeafe';
    }
  };

  return (
    <div className={`relative inline-flex items-center justify-center ${className}`}>
      <svg
        width={size}
        height={size}
        className="transform -rotate-90"
      >
        {/* 背景圆环 */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={getStatusBgColor()}
          strokeWidth={strokeWidth}
          fill="none"
        />
        {/* 进度圆环 */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={getStatusColor()}
          strokeWidth={strokeWidth}
          fill="none"
          strokeDasharray={strokeDasharray}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          style={{
            transition: 'stroke-dashoffset 0.5s ease-in-out',
          }}
        />
      </svg>
      
      {/* 百分比文字 */}
      {showPercentage && (
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="text-xs font-medium text-gray-700">
            {Math.round(progress)}%
          </span>
        </div>
      )}
      
      {/* 状态图标 */}
      {!showPercentage && (
        <div className="absolute inset-0 flex items-center justify-center">
          {status === 'completed' && (
            <svg className="w-4 h-4 text-emerald-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
            </svg>
          )}
          {status === 'failed' && (
            <svg className="w-4 h-4 text-red-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          )}
          {status === 'running' && (
            <div className="w-2 h-2 bg-blue-600 rounded-full animate-pulse" />
          )}
          {status === 'pending' && (
            <div className="w-2 h-2 bg-amber-600 rounded-full" />
          )}
        </div>
      )}
    </div>
  );
};

export default CircularProgress;
