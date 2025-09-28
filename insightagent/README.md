# InsightAgent - AI-Powered Product Analysis System

![InsightAgent Logo](https://img.shields.io/badge/InsightAgent-AI%20Analysis-blue?style=for-the-badge&logo=robot)

A comprehensive AI-powered system that automatically analyzes product market performance and user feedback by gathering data from multiple sources including Reddit and Product Hunt, then generating detailed insights and reports.

## 🚀 Features

- **Automated Data Collection**: Scrapes user discussions and feedback from Reddit and Product Hunt
- **AI-Powered Analysis**: Uses advanced language models to analyze sentiment and extract key insights
- **Real-time Processing**: WebSocket-based real-time updates and task monitoring
- **Modern Web Interface**: Beautiful React frontend with responsive design
- **Comprehensive API**: RESTful API with FastAPI backend
- **Task Management**: Queue-based task processing with Redis
- **Detailed Reports**: Generates structured analysis reports with actionable insights

## 🏗️ Architecture

```
InsightAgent/
├── backend/                 # FastAPI Backend Service
│   ├── app/
│   │   ├── api/            # API Routes & Endpoints
│   │   ├── core/           # Core Configuration
│   │   ├── models/         # Database Models
│   │   ├── services/       # Business Logic Services
│   │   ├── tools/          # Data Collection Tools
│   │   └── worker.py       # Background Task Worker
│   ├── tests/              # Backend Test Suite
│   └── requirements.txt    # Python Dependencies
├── frontend/               # React Frontend Application
│   ├── src/
│   │   ├── components/     # React Components
│   │   ├── pages/          # Page Components
│   │   ├── services/       # API Client Services
│   │   ├── store/          # State Management
│   │   └── types/          # TypeScript Definitions
│   └── package.json        # Node.js Dependencies
├── docker-compose.yml      # Development Environment
└── README.md
```

## 🛠️ Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **AI/ML**: LangChain, OpenAI API
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache/Queue**: Redis
- **Task Processing**: Celery-like worker system
- **API Documentation**: Swagger/OpenAPI

### Frontend
- **Framework**: React 18 with TypeScript
- **Styling**: Tailwind CSS
- **State Management**: Zustand
- **HTTP Client**: Axios
- **Real-time**: WebSocket connections
- **Build Tool**: Create React App

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Database Migrations**: Alembic
- **Testing**: Pytest (Backend), Jest (Frontend)
- **Code Quality**: ESLint, Prettier

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for frontend development)
- Python 3.11+ (for backend development)

### Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/HackerWinder/insightagent.git
   cd insightagent
   ```

2. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

3. **Start with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Or start services individually**
   ```bash
   # Backend
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python -m app.main

   # Frontend
   cd frontend
   npm install
   npm start
   ```

5. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## 📊 Usage

1. **Create Analysis Task**: Enter a product name in the web interface
2. **Data Collection**: System automatically gathers data from Reddit and Product Hunt
3. **AI Analysis**: Advanced language models analyze the collected data
4. **Report Generation**: Detailed insights and recommendations are generated
5. **View Results**: Access comprehensive reports through the web interface

## 🔧 Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/insightagent

# Redis
REDIS_URL=redis://localhost:6379

# AI Services
OPENAI_API_KEY=your_openai_api_key
SILICONFLOW_API_KEY=your_siliconflow_api_key

# External APIs
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
PRODUCT_HUNT_API_TOKEN=your_product_hunt_token
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 📈 API Endpoints

- `GET /api/v1/tasks/` - List all analysis tasks
- `POST /api/v1/tasks/` - Create new analysis task
- `GET /api/v1/tasks/{task_id}` - Get task details
- `GET /api/v1/reports/{task_id}` - Get analysis report
- `WebSocket /ws` - Real-time task updates

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- OpenAI for providing the language models
- Reddit and Product Hunt for data access
- The open-source community for various libraries and tools

## 📞 Support

For support and questions, please open an issue on GitHub or contact the development team.

---

**Made with ❤️ by the InsightAgent Team**
