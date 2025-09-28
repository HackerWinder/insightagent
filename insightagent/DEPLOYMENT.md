# Deployment Guide

## Manual GitHub Upload Instructions

Since GitHub CLI authentication requires interactive login, here are the manual steps to upload your project to GitHub:

### Step 1: Create GitHub Repository

1. Go to [GitHub.com](https://github.com) and sign in
2. Click the "+" icon in the top right corner
3. Select "New repository"
4. Repository name: `insightagent`
5. Description: `InsightAgent - AI-powered product analysis system with Reddit and Product Hunt integration`
6. Set to **Public**
7. **Do NOT** initialize with README, .gitignore, or license (we already have these)
8. Click "Create repository"

### Step 2: Upload Code

After creating the repository, GitHub will show you instructions. Use these commands:

```bash
# Navigate to your project directory
cd /Users/vincent/个人文件/project/insightagent

# Add the remote repository (replace with your actual GitHub username if different)
git remote add origin https://github.com/HackerWinder/insightagent.git

# Push your code to GitHub
git push -u origin main
```

### Step 3: Verify Upload

1. Go to your repository: `https://github.com/HackerWinder/insightagent`
2. Verify all files are uploaded correctly
3. Check that the README displays properly

## Alternative: Using GitHub Desktop

1. Download and install [GitHub Desktop](https://desktop.github.com/)
2. Sign in with your GitHub account
3. Click "Add an Existing Repository from your Hard Drive"
4. Select the `/Users/vincent/个人文件/project/insightagent` folder
5. Click "Publish repository"
6. Choose "Public" and click "Publish Repository"

## Docker Deployment

### Production Deployment

1. **Build and run with Docker Compose**
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

2. **Environment Configuration**
   ```bash
   # Copy production environment file
   cp .env.production .env
   
   # Edit with production values
   nano .env
   ```

3. **Database Setup**
   ```bash
   # Run database migrations
   docker-compose exec backend alembic upgrade head
   ```

### Cloud Deployment Options

#### Heroku
1. Install Heroku CLI
2. Create Heroku app: `heroku create insightagent-app`
3. Add PostgreSQL addon: `heroku addons:create heroku-postgresql:hobby-dev`
4. Deploy: `git push heroku main`

#### AWS/GCP/Azure
- Use container services (ECS, Cloud Run, Container Instances)
- Set up managed databases (RDS, Cloud SQL, Azure Database)
- Configure load balancers and auto-scaling

## Environment Variables for Production

```bash
# Production Database
DATABASE_URL=postgresql://user:password@prod-db-host:5432/insightagent

# Redis Cache
REDIS_URL=redis://prod-redis-host:6379

# AI Services (use production API keys)
OPENAI_API_KEY=your_production_openai_key
SILICONFLOW_API_KEY=your_production_siliconflow_key

# External APIs
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
PRODUCT_HUNT_API_TOKEN=your_product_hunt_token

# Security
SECRET_KEY=your_very_secure_secret_key
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Monitoring
SENTRY_DSN=your_sentry_dsn_for_error_tracking
```

## Monitoring and Maintenance

### Health Checks
- Backend: `GET /api/v1/health/`
- Database connectivity
- Redis connectivity
- External API availability

### Logging
- Application logs: `/var/log/insightagent/`
- Error tracking: Sentry integration
- Performance monitoring: APM tools

### Backup Strategy
- Database backups: Daily automated backups
- Code backups: Git repository
- Configuration backups: Environment files

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Check DATABASE_URL format
   - Verify database server is running
   - Check network connectivity

2. **Redis Connection Issues**
   - Verify REDIS_URL
   - Check Redis server status
   - Monitor memory usage

3. **API Rate Limiting**
   - Implement exponential backoff
   - Use multiple API keys if available
   - Monitor usage quotas

4. **Frontend Build Issues**
   - Check Node.js version compatibility
   - Clear npm cache: `npm cache clean --force`
   - Delete node_modules and reinstall

### Performance Optimization

1. **Database Optimization**
   - Add appropriate indexes
   - Use connection pooling
   - Monitor query performance

2. **Caching Strategy**
   - Implement Redis caching for API responses
   - Use CDN for static assets
   - Cache computed analysis results

3. **Scaling Considerations**
   - Horizontal scaling with multiple workers
   - Load balancing for API requests
   - Database read replicas for heavy queries

## Security Considerations

1. **API Security**
   - Use HTTPS in production
   - Implement rate limiting
   - Validate all inputs

2. **Data Protection**
   - Encrypt sensitive data
   - Use secure environment variables
   - Regular security updates

3. **Access Control**
   - Implement authentication if needed
   - Use API keys for external services
   - Monitor access logs
