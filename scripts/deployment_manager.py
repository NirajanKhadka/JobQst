"""
Deployment automation and infrastructure management for JobQst
"""

import docker
import subprocess
import sys
import os
from pathlib import Path
from typing import Dict, List, Optional
import yaml

class JobQstDeployer:
    """Deployment manager for JobQst"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.docker_client = None
        try:
            self.docker_client = docker.from_env()
        except Exception:
            print("Docker not available - some features disabled")
    
    def create_docker_compose(self, environment: str = "development"):
        """Create docker-compose.yml for deployment"""
        
        services = {
            'version': '3.8',
            'services': {
                'jobqst-app': {
                    'build': {
                        'context': '.',
                        'dockerfile': 'Dockerfile'
                    },
                    'ports': ['8050:8050'],
                    'environment': [
                        f'JOBQST_ENV={environment}',
                        'DATABASE_URL=postgresql://jobqst:password@postgres:5432/jobqst',
                        'REDIS_URL=redis://redis:6379/0'
                    ],
                    'volumes': [
                        './data:/app/data',
                        './logs:/app/logs',
                        './profiles:/app/profiles'
                    ],
                    'depends_on': ['postgres', 'redis'],
                    'restart': 'unless-stopped'
                },
                'postgres': {
                    'image': 'postgres:15',
                    'environment': [
                        'POSTGRES_DB=jobqst',
                        'POSTGRES_USER=jobqst',
                        'POSTGRES_PASSWORD=password'
                    ],
                    'volumes': [
                        'postgres_data:/var/lib/postgresql/data'
                    ],
                    'restart': 'unless-stopped'
                },
                'redis': {
                    'image': 'redis:7-alpine',
                    'restart': 'unless-stopped'
                }
            },
            'volumes': {
                'postgres_data': {}
            }
        }
        
        # Production-specific settings
        if environment == "production":
            services['services']['jobqst-app']['environment'].extend([
                'AI_ENABLE_HEAVY_PROCESSING=true',
                'SCRAPING_MAX_WORKERS=6'
            ])
            services['services']['nginx'] = {
                'image': 'nginx:alpine',
                'ports': ['80:80', '443:443'],
                'volumes': [
                    './nginx.conf:/etc/nginx/nginx.conf',
                    './ssl:/etc/ssl/certs'
                ],
                'depends_on': ['jobqst-app']
            }
        
        # Write docker-compose file
        compose_file = self.project_root / f"docker-compose.{environment}.yml"
        with open(compose_file, 'w') as f:
            yaml.dump(services, f, default_flow_style=False)
        
        print(f"Created {compose_file}")
        return compose_file
    
    def create_dockerfile(self):
        """Create optimized Dockerfile"""
        dockerfile_content = '''# Multi-stage Dockerfile for JobQst
FROM python:3.11-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /tmp/
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Install Playwright browsers
RUN playwright install chromium && \\
    playwright install-deps chromium

FROM python:3.11-slim as runtime

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /ms-playwright /ms-playwright

# Install runtime dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd --create-home --shell /bin/bash jobqst

# Set working directory
WORKDIR /app

# Copy application code
COPY --chown=jobqst:jobqst . .

# Create necessary directories
RUN mkdir -p data logs profiles cache && \\
    chown -R jobqst:jobqst /app

# Switch to app user
USER jobqst

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \\
    CMD curl -f http://localhost:8050/health || exit 1

# Default command
CMD ["python", "main.py", "DefaultProfile", "--action", "dashboard"]

# Expose port
EXPOSE 8050
'''
        
        dockerfile = self.project_root / "Dockerfile"
        with open(dockerfile, 'w') as f:
            f.write(dockerfile_content)
        
        print(f"Created {dockerfile}")
        return dockerfile
    
    def create_systemd_service(self):
        """Create systemd service file for Linux deployment"""
        service_content = f'''[Unit]
Description=JobQst Job Discovery Platform
After=network.target
Wants=network.target

[Service]
Type=exec
User=jobqst
Group=jobqst
WorkingDirectory={self.project_root.absolute()}
Environment=JOBQST_ENV=production
ExecStart=/usr/bin/conda run -n auto_job python main.py DefaultProfile --action dashboard
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths={self.project_root.absolute()}/data {self.project_root.absolute()}/logs

[Install]
WantedBy=multi-user.target
'''
        
        service_file = self.project_root / "deploy" / "jobqst.service"
        service_file.parent.mkdir(exist_ok=True)
        
        with open(service_file, 'w') as f:
            f.write(service_content)
        
        print(f"Created {service_file}")
        return service_file
    
    def create_nginx_config(self):
        """Create nginx configuration for reverse proxy"""
        nginx_content = '''events {
    worker_connections 1024;
}

http {
    upstream jobqst {
        server jobqst-app:8050;
    }
    
    server {
        listen 80;
        server_name _;
        
        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        
        # Compression
        gzip on;
        gzip_types text/plain text/css application/json application/javascript;
        
        location / {
            proxy_pass http://jobqst;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket support
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
        
        # Health check endpoint
        location /health {
            proxy_pass http://jobqst/health;
            access_log off;
        }
        
        # Static files
        location /static/ {
            alias /app/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }
}
'''
        
        nginx_file = self.project_root / "nginx.conf"
        with open(nginx_file, 'w') as f:
            f.write(nginx_content)
        
        print(f"Created {nginx_file}")
        return nginx_file
    
    def deploy_local(self, environment: str = "development"):
        """Deploy locally using docker-compose"""
        if not self.docker_client:
            print("Docker not available")
            return False
        
        # Create deployment files
        self.create_dockerfile()
        compose_file = self.create_docker_compose(environment)
        
        # Build and start services
        try:
            cmd = f"docker-compose -f {compose_file} up --build -d"
            result = subprocess.run(cmd, shell=True, check=True, 
                                  capture_output=True, text=True)
            print("Deployment successful!")
            print(result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Deployment failed: {e}")
            print(e.stderr)
            return False
    
    def deploy_production(self, server_host: str, ssh_key: Optional[str] = None):
        """Deploy to production server"""
        print(f"Deploying to production server: {server_host}")
        
        # Create deployment package
        deployment_files = [
            "main.py", "requirements.txt", "src/", "config/",
            "profiles/", "docker-compose.production.yml", "Dockerfile"
        ]
        
        # Create systemd service
        self.create_systemd_service()
        
        # TODO: Implement rsync deployment
        print("Production deployment template created")
        print("Manual steps required:")
        print(f"1. rsync files to {server_host}")
        print("2. Install Docker and docker-compose")
        print("3. Run: docker-compose -f docker-compose.production.yml up -d")
    
    def health_check(self, url: str = "http://localhost:8050"):
        """Check deployment health"""
        try:
            import requests
            response = requests.get(f"{url}/health", timeout=10)
            if response.status_code == 200:
                print("✅ Service is healthy")
                return True
            else:
                print(f"❌ Service unhealthy: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False


def main():
    """Main deployment script"""
    import argparse
    
    parser = argparse.ArgumentParser(description="JobQst Deployment Manager")
    parser.add_argument("action", choices=["create-files", "deploy-local", "deploy-prod", "health-check"])
    parser.add_argument("--environment", choices=["development", "testing", "production"], 
                       default="development")
    parser.add_argument("--server", help="Production server hostname")
    
    args = parser.parse_args()
    
    deployer = JobQstDeployer()
    
    if args.action == "create-files":
        deployer.create_dockerfile()
        deployer.create_docker_compose(args.environment)
        deployer.create_nginx_config()
        deployer.create_systemd_service()
        print("All deployment files created!")
    
    elif args.action == "deploy-local":
        deployer.deploy_local(args.environment)
    
    elif args.action == "deploy-prod":
        if not args.server:
            print("Error: --server required for production deployment")
            sys.exit(1)
        deployer.deploy_production(args.server)
    
    elif args.action == "health-check":
        deployer.health_check()


if __name__ == "__main__":
    main()
