.PHONY: help install dev test clean build

help: ## 显示帮助信息
	@echo "InsightAgent 开发命令:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## 安装所有依赖
	@echo "安装后端依赖..."
	cd backend && pip install -r requirements.txt
	@echo "安装前端依赖..."
	cd frontend && npm install

dev: ## 启动开发环境
	@echo "启动开发环境..."
	docker-compose up -d

dev-logs: ## 查看开发环境日志
	docker-compose logs -f

stop: ## 停止开发环境
	docker-compose down

test-backend: ## 运行后端测试
	cd backend && python -m pytest tests/ -v

test-frontend: ## 运行前端测试
	cd frontend && npm test

test: test-backend test-frontend ## 运行所有测试

lint-backend: ## 后端代码检查
	cd backend && black . && isort . && flake8 .

lint-frontend: ## 前端代码检查
	cd frontend && npm run lint && npm run format

lint: lint-backend lint-frontend ## 运行所有代码检查

clean: ## 清理环境
	docker-compose down -v
	docker system prune -f

build: ## 构建生产镜像
	docker-compose -f docker-compose.prod.yml build

deploy: ## 部署到生产环境
	docker-compose -f docker-compose.prod.yml up -d