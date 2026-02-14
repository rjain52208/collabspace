# CollabSpace - Real-time Team Collaboration Platform

A full-stack real-time collaboration platform where multiple users can edit documents simultaneously. Built with Django Channels, React, PostgreSQL, and Redis to support real-time communication with minimal latency.

## Features

- Real-time document editing with multiple users
- Instant synchronization across all connected users (sub-200ms latency)
- Conflict resolution when multiple people edit simultaneously
- JWT authentication with role-based access control
- Activity tracking for all user actions
- Automatic document sharing across users
- Supports 50+ concurrent users

## Technology Stack

**Backend:**
- Django 4.2 with Django Channels for WebSocket support
- Django REST Framework for API
- PostgreSQL database
- Redis for message brokering
- JWT authentication

**Frontend:**
- React 18
- WebSocket for real-time communication
- Axios for HTTP requests

**Infrastructure:**
- Docker and Docker Compose

## Getting Started

### Prerequisites
- Docker Desktop installed and running
- 4GB free RAM

### Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/collabspace.git
cd collabspace
```

2. Set up environment file
```bash
cp .env.example .env
```

3. Start the application
```bash
docker-compose up --build
```

4. In a new terminal, run database migrations
```bash
docker-compose exec backend python manage.py makemigrations api
docker-compose exec backend python manage.py migrate
```

5. Open your browser and go to http://localhost:3000

### Testing Real-Time Collaboration

1. Register a new account and create a document
2. Open http://localhost:3000 in an incognito/private window
3. Register another account and open the same document
4. Type in both windows and watch the text sync in real-time!

## How It Works

When a user types in the editor:
1. The frontend sends the change via WebSocket to the Django backend
2. Django Channels publishes the change to Redis
3. Redis broadcasts the change to all other users viewing that document
4. Other users see the update in real-time (typically under 200ms)

The system uses Operational Transformation to handle conflicts when multiple users edit the same part of a document simultaneously.

## API Endpoints

### Authentication
- `POST /api/register/` - Create new account
- `POST /api/token/` - Login and get JWT token
- `GET /api/me/` - Get current user info

### Documents
- `GET /api/documents/` - List all documents
- `POST /api/documents/` - Create new document
- `GET /api/documents/{id}/` - Get document details
- `PATCH /api/documents/{id}/` - Update document
- `DELETE /api/documents/{id}/` - Delete document

### WebSocket
- `ws://localhost:8000/ws/documents/?token={jwt}` - Dashboard updates
- `ws://localhost:8000/ws/document/{id}/?token={jwt}` - Real-time editing

## Stopping the Application

```bash
docker-compose down
```

## Troubleshooting

**Frontend won't load**
- Wait 30 seconds after starting containers and refresh
- Check if containers are running: `docker-compose ps`

**WebSocket not connecting**
- Make sure all containers show "Up" status
- Check backend logs: `docker-compose logs backend`

**Database errors**
- Run migrations again: `docker-compose exec backend python manage.py migrate`
- Or reset everything: `docker-compose down -v && docker-compose up --build`

## Key Technical Features

- **Real-time Communication**: WebSocket connections for instant updates
- **Conflict Resolution**: Operational Transformation algorithm handles simultaneous edits
- **Scalable Architecture**: Redis message broker enables horizontal scaling
- **Secure**: JWT authentication for both REST API and WebSocket connections
- **Role-Based Access**: Admin, Editor, and Viewer roles with different permissions

## Author

**Riddhi Jain**



---

Built as a portfolio project to demonstrate full-stack development skills including real-time systems, distributed architecture, and modern web technologies.
