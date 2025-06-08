# Quick Setup Guide

## Prerequisites
1. Docker and Docker Compose installed
2. Git (to clone the repository)

## Setup Steps

### 1. Prepare Environment
```bash
# Copy environment template
cp .env.example .env

# Edit with your passwords (use a text editor)
notepad .env  # Windows
# or
nano .env     # Linux/Mac
```

### 2. Set Strong Passwords
Edit `.env` file and replace:
- `your_secure_password_here` with a strong Neo4j password
- `your_mongo_password_here` with a strong MongoDB password

### 3. Build and Run

#### For Development (MCP + Neo4j only):
```bash
# Windows
run.bat dev

# Linux/Mac
chmod +x run.sh
./run.sh dev
```

#### For Production (with LibreChat):
```bash
# Windows
run.bat prod

# Linux/Mac
./run.sh prod
```

## Access Points
- **LibreChat**: http://localhost:3080
- **Neo4j Browser**: http://localhost:7474
- **Neo4j Credentials**: neo4j / [your_password_from_.env]

## First Time Setup
1. Wait for all containers to start (2-3 minutes)
2. Access LibreChat at http://localhost:3080
3. Your Neo4j Memory MCP server should be available as tools in the chat

## Troubleshooting
```bash
# Check container status
docker-compose ps

# View logs
docker-compose logs neo4j
docker-compose logs librechat

# Restart if needed
docker-compose restart
```
