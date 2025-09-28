/// <reference types="react-scripts" />

// 扩展 ImportMeta 接口以支持 Vite 环境变量
interface ImportMeta {
  readonly env: {
    readonly VITE_API_URL?: string;
  };
}
