# Deployment Guide

This guide covers deploying the Face Recognition Authentication System to production environments.

## Pre-Deployment Checklist

- [ ] All tests passing: `pytest`
- [ ] Security checks passed: `bandit -r . && safety check`
- [ ] Code follows style guide: `flake8 . && black .`
- [ ] Environment variables configured
- [ ] Database backups created
- [ ] SSL/TLS certificates obtained
- [ ] Monitoring and logging configured

## Environment Configuration

### Production Environment Variables

Create a `.env` file (never commit to git):

```env
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=your_very_secure_secret_key_here
SECURITY_PASSWORD_SALT=another_secure_salt
DATABASE_URL=postgresql://user:pass@localhost/face_recognition
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_DEFAULT_SENDER=noreply@face-recognition.com
```

### Security Considerations

1. **Secret Key**: Generate a strong secret key
```python
python -c "import secrets; print(secrets.token_hex(32))"
```

2. **Database**: Use PostgreSQL or MySQL, not SQLite, for production
3. **SSL/TLS**: Enable HTTPS and HTTP/2
4. **CORS**: Configure CORS headers appropriately
5. **Rate Limiting**: Enable rate limiting on authentication endpoints

## Database Setup

### PostgreSQL Setup

```bash
# Install PostgreSQL (Ubuntu)
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE face_recognition;
CREATE USER face_user WITH PASSWORD 'secure_password';
ALTER ROLE face_user SET client_encoding TO 'utf8';
ALTER ROLE face_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE face_user SET default_transaction_deferrable TO on;
ALTER ROLE face_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE face_recognition TO face_user;
```

### Initialize Database

```bash
python
from app import db, create_app
app = create_app()
with app.app_context():
    db.create_all()
```

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "wsgi:app"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://face_user:password@db:5432/face_recognition
      - FLASK_ENV=production
    depends_on:
      - db
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  db:
    image: postgres:14
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=face_recognition
      - POSTGRES_USER=face_user
      - POSTGRES_PASSWORD=secure_password
    restart: unless-stopped

  nginx:
    image: nginx:latest
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - web
    restart: unless-stopped

volumes:
  postgres_data:
```

## Kubernetes Deployment

### ConfigMap

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: face-recognition-config
data:
  FLASK_ENV: production
  DATABASE_HOST: postgres
  MAIL_SERVER: smtp.gmail.com
```

### Secret

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: face-recognition-secret
type: Opaque
stringData:
  SECRET_KEY: your-secret-key-here
  DATABASE_URL: postgresql://user:password@postgres:5432/face_recognition
```

### Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: face-recognition
spec:
  replicas: 3
  selector:
    matchLabels:
      app: face-recognition
  template:
    metadata:
      labels:
        app: face-recognition
    spec:
      containers:
      - name: app
        image: your-registry/face-recognition:latest
        ports:
        - containerPort: 5000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: face-recognition-secret
              key: DATABASE_URL
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 30
          periodSeconds: 10
```

## Traditional Server Deployment (Ubuntu/Debian)

### 1. Server Setup

```bash
# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install dependencies
sudo apt-get install -y python3-pip python3-venv nginx supervisor postgresql postgresql-contrib
```

### 2. Application Setup

```bash
# Create app directory
sudo mkdir -p /var/www/face-recognition
cd /var/www/face-recognition

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn

# Set permissions
sudo chown -R www-data:www-data /var/www/face-recognition
```

### 3. Systemd Service

Create `/etc/systemd/system/face-recognition.service`:

```ini
[Unit]
Description=Face Recognition Application
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/var/www/face-recognition
Environment="PATH=/var/www/face-recognition/venv/bin"
ExecStart=/var/www/face-recognition/venv/bin/gunicorn \
    --workers 4 \
    --bind unix:///var/run/face-recognition.sock \
    --timeout 120 \
    wsgi:app

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable face-recognition
sudo systemctl start face-recognition
sudo systemctl status face-recognition
```

### 4. Nginx Configuration

Create `/etc/nginx/sites-available/face-recognition`:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;

    location / {
        proxy_pass http://unix:/var/run/face-recognition.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    location /static {
        alias /var/www/face-recognition/static;
        expires 30d;
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/face-recognition /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 5. SSL Certificate (Let's Encrypt)

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot certonly --nginx -d your-domain.com
```

## Monitoring & Logging

### Application Logging

```python
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    if not os.path.exists('logs'):
        os.mkdir('logs')
    
    file_handler = RotatingFileHandler('logs/face_recognition.log',
                                     maxBytes=10240000, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
```

### Health Checks

```bash
# Monitor application
curl https://your-domain.com/health

# Check logs
tail -f /var/www/face-recognition/logs/face_recognition.log
```

## Backup & Recovery

### Database Backup

```bash
# Daily backup
pg_dump -U face_user face_recognition > /backup/face_recognition_$(date +%Y%m%d).sql

# Add to crontab
0 2 * * * pg_dump -U face_user face_recognition > /backup/face_recognition_$(date +\%Y\%m\%d).sql
```

### Database Restore

```bash
psql -U face_user face_recognition < /backup/face_recognition_YYYYMMDD.sql
```

## Performance Tuning

### Gunicorn Workers

Recommended: `2 * CPU_count + 1`

For 4 CPU cores: `9 workers`

```bash
gunicorn --workers 9 --worker-class sync --worker-connections 1000 wsgi:app
```

### Database Connection Pooling

```python
from sqlalchemy.pool import QueuePool

db = SQLAlchemy(
    engine_options={
        'poolclass': QueuePool,
        'pool_size': 10,
        'max_overflow': 20,
    }
)
```

## Rollback Plan

In case of deployment issues:

```bash
# Stop application
sudo systemctl stop face-recognition

# Revert code
cd /var/www/face-recognition
git revert <commit-hash>

# Rollback database if needed
psql -U face_user face_recognition < /backup/face_recognition_YYYYMMDD.sql

# Restart
sudo systemctl start face-recognition

# Verify
curl https://your-domain.com/health
```

## Post-Deployment

- [ ] Verify application running: `curl https://your-domain.com/health`
- [ ] Check logs: `tail -f logs/face_recognition.log`
- [ ] Run smoke tests
- [ ] Monitor error rates
- [ ] Validate SSL certificate
- [ ] Test authentication flows
- [ ] Verify database connections
- [ ] Check performance metrics

---

**Need Help?** See [CONTRIBUTING.md](CONTRIBUTING.md) or open an issue.
