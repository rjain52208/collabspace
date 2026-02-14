#!/bin/bash

echo "🚀 Starting CollabSpace..."
echo ""

# Check Docker
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

# Create .env if needed
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ Created .env file"
fi

# Start containers
echo "📦 Starting containers..."
docker-compose up -d --build

echo "⏳ Waiting for services..."
sleep 15

# Run migrations
echo "🗄️ Setting up database..."
docker-compose exec -T backend python manage.py makemigrations api
docker-compose exec -T backend python manage.py migrate

echo ""
echo "✅ CollabSpace is running!"
echo ""
echo "🌐 Open: http://localhost:3000"
echo ""
echo "📝 First time? Register an account and create a document!"
echo "🔄 To stop: docker-compose down"
echo ""
