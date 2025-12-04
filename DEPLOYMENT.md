# Deployment Guide

This guide covers deploying ResumeKit to production environments.

## Prerequisites

- Docker and Docker Compose installed
- PostgreSQL database (or use provided docker-compose setup)
- OpenAI API key (for resume tailoring features)
- Environment variables configured

## Quick Start with Docker Compose

1. **Clone repository and navigate to project directory**

2. **Create `.env` file** (copy from `.env.example` if available):

```bash
# Database
DATABASE_URL=postgresql+psycopg2://resumekit:resumekit_password@db:5432/resumekit

# OpenAI
OPENAI_API_KEY=your-openai-api-key
OPENAI_API_BASE=https://api.openai.com/v1

# Authentication
AUTH_SECRET_KEY=your-secret-key-change-in-production
AUTH_TOKEN_EXPIRE_MINUTES=30

# Rate Limiting
RATE_LIMIT_ENABLED=true
```

3. **Start services**:

```bash
docker-compose up -d
```

4. **Run database migrations**:

```bash
docker-compose exec backend alembic upgrade head
```

5. **Access application**:
   - Backend API: http://localhost:8000
   - Frontend: http://localhost:5173
   - API Docs: http://localhost:8000/docs

## Production Deployment

### Backend Deployment

#### Option 1: Docker

```bash
# Build image
docker build -t resumekit-backend .

# Run container
docker run -d \
  --name resumekit-backend \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@host:5432/dbname \
  -e OPENAI_API_KEY=your-key \
  -e AUTH_SECRET_KEY=your-secret \
  resumekit-backend
```

#### Option 2: Direct Python

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL=postgresql://user:pass@host:5432/dbname
export OPENAI_API_KEY=your-key
export AUTH_SECRET_KEY=your-secret

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend Deployment

#### Option 1: Docker

```bash
cd frontend
docker build -t resumekit-frontend .
docker run -d --name resumekit-frontend -p 80:80 resumekit-frontend
```

#### Option 2: Static Hosting

Build and deploy to static hosting (Netlify, Vercel, etc.):

```bash
cd frontend
npm install
npm run build
# Deploy dist/ directory to your hosting provider
```

### Database Setup

1. **Create PostgreSQL database**:

```sql
CREATE DATABASE resumekit;
CREATE USER resumekit WITH PASSWORD 'your-password';
GRANT ALL PRIVILEGES ON DATABASE resumekit TO resumekit;
```

2. **Run migrations**:

```bash
export DATABASE_URL=postgresql://resumekit:password@localhost:5432/resumekit
alembic upgrade head
```

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Yes | `sqlite:///./resumekit.db` |
| `OPENAI_API_KEY` | OpenAI API key | Yes (for LLM features) | None |
| `OPENAI_API_BASE` | OpenAI API base URL | No | `https://api.openai.com/v1` |
| `AUTH_SECRET_KEY` | JWT secret key | Yes (for auth) | None |
| `AUTH_TOKEN_EXPIRE_MINUTES` | JWT token expiration | No | `30` |
| `RATE_LIMIT_ENABLED` | Enable rate limiting | No | `true` |

## Health Checks

The application provides a health check endpoint:

```bash
curl http://localhost:8000/health
```

Returns: `{"status": "healthy"}` or `{"status": "unhealthy"}`

## Monitoring

- Health endpoint: `GET /health`
- Metrics endpoint: `GET /api/metrics`
- API documentation: `GET /docs`

## Security Considerations

1. **Change default passwords** in production
2. **Use strong `AUTH_SECRET_KEY`** (generate with `openssl rand -hex 32`)
3. **Enable HTTPS** in production (use reverse proxy like nginx)
4. **Set up firewall rules** to restrict database access
5. **Regular backups** of PostgreSQL database
6. **Keep dependencies updated** (`pip list --outdated`)

## Scaling

### Horizontal Scaling

- Backend: Run multiple instances behind a load balancer
- Database: Use PostgreSQL read replicas for read-heavy workloads
- Frontend: Static files can be served from CDN

### Vertical Scaling

- Increase database connection pool size
- Adjust rate limiting thresholds
- Monitor OpenAI API usage and costs

## Troubleshooting

### Database Connection Issues

```bash
# Test database connection
psql $DATABASE_URL -c "SELECT 1"

# Check migrations status
alembic current
alembic history
```

### Migration Issues

```bash
# Rollback last migration
alembic downgrade -1

# View migration SQL without applying
alembic upgrade head --sql
```

### Container Issues

```bash
# View logs
docker-compose logs backend
docker-compose logs frontend

# Restart services
docker-compose restart

# Rebuild containers
docker-compose up --build
```

## Backup and Recovery

### Database Backup

```bash
# Backup PostgreSQL database
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Restore from backup
psql $DATABASE_URL < backup_20231204.sql
```

### Automated Backups

Set up cron job or scheduled task:

```bash
0 2 * * * pg_dump $DATABASE_URL > /backups/resumekit_$(date +\%Y\%m\%d).sql
```

