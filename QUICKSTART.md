# Quick Start Guide

Get CollabSpace running in 5 minutes!

## Prerequisites

- Docker Desktop installed and running
- Ports 3000, 8000, 5432, 6379 available

## Steps

### 1. Start Docker Desktop
Make sure Docker is running (look for whale icon in menu bar)

### 2. Setup Environment
```bash
cp .env.example .env
```

### 3. Start Application
```bash
./run-project.sh
```

OR manually:
```bash
docker-compose up --build -d
docker-compose exec backend python manage.py makemigrations api
docker-compose exec backend python manage.py migrate
```

### 4. Access Application
Open your browser: **http://localhost:3000**

### 5. Create Account
- Click "Register"
- Username: `demo1`
- Password: `password123`
- Click "Register" → then "Login"

### 6. Test Real-Time Collaboration
- Create a document
- Open http://localhost:3000 in incognito window
- Register as `demo2`
- Open the same document in both windows
- Type simultaneously - see instant updates!

## Stop Application

```bash
docker-compose down
```

## Troubleshooting

**Can't connect?**
- Wait 30 seconds after `docker-compose up`
- Check: `docker-compose ps` (all should be "Up")

**Database errors?**
```bash
docker-compose down -v
docker-compose up --build
```

**Need help?** See README.md for full documentation.
