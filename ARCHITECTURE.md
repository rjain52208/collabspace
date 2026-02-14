# Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────┐
│         Frontend (React)                │
│         Port: 3000                      │
│  - Authentication UI                    │
│  - Document Dashboard                   │
│  - Real-time Editor                     │
│  - WebSocket Client                     │
└──────────────┬──────────────────────────┘
               │ HTTP/WebSocket
               ↓
┌─────────────────────────────────────────┐
│    Backend (Django + Channels)          │
│         Port: 8000                      │
│  - REST API                             │
│  - WebSocket Consumers                  │
│  - JWT Authentication                   │
│  - RBAC                                 │
└──────┬───────────┬──────────────────────┘
       │           │
       ↓           ↓
┌────────────┐  ┌──────────┐  ┌──────────┐
│ PostgreSQL │  │  Redis   │  │  AWS S3  │
│ Port: 5432 │  │Port: 6379│  │ (Cloud)  │
│            │  │          │  │          │
│ - Users    │  │ - Channel│  │ - Files  │
│ - Documents│  │   Layer  │  │          │
│ - Activity │  │ - Message│  │          │
│ - Versions │  │   Broker │  │          │
└────────────┘  └──────────┘  └──────────┘
```

## Real-Time Flow

```
User A types "H"
       ↓
Frontend sends WebSocket message
       ↓
Django Consumer receives edit
       ↓
Publishes to Redis channel "document_1"
       ↓
Redis broadcasts to all subscribers
       ↓
User B's Consumer receives message
       ↓
WebSocket sends to User B's browser
       ↓
User B sees "H" appear (< 200ms)
```

## Key Components

### 1. Django Channels (WebSocket)
- Extends Django to support ASGI and WebSocket
- Real-time bidirectional communication
- Handles 50+ concurrent connections

### 2. Redis (Message Broker)
- Channel layer for Django Channels
- Pub/Sub messaging between server instances
- Enables horizontal scaling
- Sub-millisecond message routing

### 3. Operational Transformation
- Resolves conflicts when multiple users edit simultaneously
- Tracks operation type, position, and timestamp
- Transforms concurrent operations to maintain consistency

### 4. JWT Authentication
- Stateless authentication for REST API
- Custom middleware for WebSocket authentication
- Token passed via query string for WebSocket

### 5. PostgreSQL
- Stores users, documents, versions, and activity logs
- Optimized with indexes on foreign keys
- Supports ACID transactions

## Database Schema

```sql
User (Django Auth)
  ↓
UserProfile (role: admin/editor/viewer)

Document
  - title, content, version
  - owner (FK → User)
  - collaborators (M2M → User)
  ↓
├── DocumentVersion (version history)
├── DocumentEdit (OT tracking)
├── FileUpload (S3 files)
└── ActivityLog (audit trail)
```

## WebSocket Messages

### Client → Server
```json
{
  "type": "edit",
  "operation": "insert",
  "position": 10,
  "content": "H",
  "version": 5
}
```

### Server → Client
```json
{
  "type": "edit",
  "user": "demo2",
  "operation": "insert",
  "position": 10,
  "content": "H",
  "version": 6
}
```

## Scalability

### Current Setup
- Single server instance
- 50+ concurrent users
- 10+ simultaneous editors per document

### Production Scaling
- Multiple Django servers behind load balancer
- Redis Cluster for high availability
- PostgreSQL read replicas
- CDN for static assets
- Kubernetes for orchestration

## Security

1. **Authentication**: JWT tokens for both REST and WebSocket
2. **Authorization**: RBAC with document-level permissions
3. **WebSocket Security**: Custom middleware validates tokens
4. **Activity Logging**: Complete audit trail
5. **CORS**: Configured allowed origins

## Performance Optimizations

- Redis in-memory messaging
- WebSocket connection pooling
- Database query optimization
- Async WebSocket consumers
- Optimistic UI updates
