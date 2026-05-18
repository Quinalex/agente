# Architecture Documentation

## System Design

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (Next.js)                       │
│  Chat Interface | Task Management | Tools Gallery | Analytics   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    HTTP/WebSocket
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                    Backend (FastAPI)                             │
├──────────────────────────────────────────────────────────────────┤
│  API Layer (REST + WebSocket)                                    │
│  ├── Task Management                                             │
│  ├── Tool Registry                                               │
│  ├── Agent Orchestration                                         │
│  └── Real-time Updates                                           │
├──────────────────────────────────────────────────────────────────┤
│  Multi-Agent System (LangGraph)                                  │
│  ├── Planner Agent      → Task decomposition & planning         │
│  ├── Executor Agent     → Step execution & tool management      │
│  ├── Memory Agent       → Context & knowledge management         │
│  ├── Browser Agent      → Web automation & scraping             │
│  └── Reflection Loop    → Self-critique & improvement           │
├──────────────────────────────────────────────────────────────────┤
│  Tool System                                                      │
│  ├── Search Tool                                                 │
│  ├── Code Executor                                               │
│  ├── File Operations                                             │
│  ├── Email Sending                                               │
│  └── API Caller                                                  │
├──────────────────────────────────────────────────────────────────┤
│  Memory System (Redis + Vector DB)                               │
│  ├── Short-term Memory  (1 hour TTL)                            │
│  ├── Long-term Memory   (30 day TTL)                            │
│  ├── Semantic Search    (embeddings)                            │
│  └── Context Persistence                                        │
├──────────────────────────────────────────────────────────────────┤
│  Data Layer                                                       │
│  ├── PostgreSQL         (persistent storage)                     │
│  ├── Redis              (caching & queues)                       │
│  └── SQLAlchemy         (async ORM)                             │
└──────────────────────────────────────────────────────────────────┘
```

## Component Architecture

### 1. Frontend Architecture

```typescript
App (layout)
├── Dashboard (page)
│   ├── Chat Component
│   │   ├── Message List
│   │   ├── Input Area
│   │   └── WebSocket Handler
│   ├── Tasks Component
│   │   ├── Task Creator
│   │   └── Task List
│   └── Tools Component
│       └── Tools Gallery
├── Providers
│   ├── QueryClient
│   ├── Zustand Store
│   └── Toast Notifications
└── Stores
    ├── useChatStore
    └── useTaskStore
```

### 2. Backend Architecture

```python
main.py (FastAPI App)
├── Lifespan Manager
│   ├── Database Init
│   ├── Redis Init
│   └── Queue Processor
├── Middleware
│   └── CORS
├── WebSocket Handler
│   └── ConnectionManager
└── API Routes
    ├── /api/v1/tasks
    ├── /api/v1/tools
    └── /ws

agents/
├── base.py (BaseAgent)
├── planner.py (PlannerAgent)
├── executor.py (ExecutorAgent)
├── memory.py (MemoryAgent)
├── browser.py (BrowserAgent)
├── reflection.py (ReflectionLoop)
└── orchestrator.py (AgentOrchestrator)

tools/
├── base.py (BaseTool)
├── registry.py (ToolRegistry)
└── builtin.py (SearchTool, CodeExecutor, etc.)

memory/
└── manager.py (MemoryManager)

llm/
├── provider.py (LLMProvider base)
├── openai_provider.py
├── anthropic_provider.py
└── client.py (LLMClient factory)

tasks/
├── models.py (Task, TaskStatus, TaskQueue)
└── manager.py (TaskManager)

core/
├── config.py (Settings)
├── database.py (SQLAlchemy setup)
├── logging.py (Structured logging)
└── redis_client.py (Redis setup)
```

## Data Flow

### Task Execution Flow

```
1. User Input (Chat/Task Creation)
        │
        ▼
2. API Endpoint (POST /api/v1/tasks)
        │
        ▼
3. TaskManager.create_task()
        │
        ▼
4. Task Queue (add to queue)
        │
        ▼
5. Queue Processor (async loop)
        │
        ▼
6. AgentOrchestrator.execute_workflow()
        │
        ├─────────────────────────────────────────┐
        │                                         │
        ▼                                         ▼
7a. PlannerAgent.execute()          (Parallel execution)
    - Analyze task                   
    - Create plan                    
    - Store in memory                
        │                                         │
        ▼                                         ▼
7b. ExecutorAgent.execute()
    - Execute steps
    - Select tools
    - Invoke tools
    - Handle results
        │                                         │
        ▼                                         ▼
7c. ReflectionLoop.evaluate_result()
    - Assess success
    - Identify issues
    - Suggest improvements
        │
        ▼
8. Store Result
    - Save to database
    - Update memory
    - Emit WebSocket update
        │
        ▼
9. Return Result to User
```

### WebSocket Communication

```
Client → Server: { type: "subscribe", channel: "tasks" }
Server → Client: { type: "subscribed", channel: "tasks" }

[Task Executes]

Server → Client: { 
  type: "task_update",
  channel: "tasks",
  data: {
    task_id: "xxx",
    status: "running",
    progress: 50
  }
}

Client → Server: { type: "unsubscribe", channel: "tasks" }
Server → Client: { type: "unsubscribed", channel: "tasks" }
```

## Agent Execution Lifecycle

### Planner Agent
```
Input: Task description
  ↓
Thinking Phase: Analyze requirements
  ↓
LLM Call: Generate execution plan
  ↓
Plan Structuring: Create step breakdown
  ↓
Memory Store: Save for executor
  ↓
Output: Structured plan with steps
```

### Executor Agent
```
Input: Execution plan
  ↓
Loop: For each step
  ├─ Thinking Phase: Analyze step
  ├─ Tool Selection: Choose tool
  ├─ Argument Preparation: Get params
  ├─ Tool Execution: Invoke tool
  ├─ Result Processing: Handle output
  └─ Error Handling: Retry if needed
  ↓
Output: Execution results
```

### Memory Agent
```
Actions:
├─ store_short_term(key, value, ttl)
├─ store_long_term(key, value, tags)
├─ retrieve(key, scope)
├─ search(pattern, scope)
├─ delete(key, scope)
└─ get_stats()

Storage:
├─ Redis (short-term, fast access)
├─ Redis (long-term, persistent)
└─ Vector DB (semantic search)
```

## Error Handling & Retry Strategy

```
Task Execution
  ├─ Error Detected
  │  ├─ Retry Count < Max Retries
  │  │  ├─ Log error
  │  │  ├─ Increment retry
  │  │  ├─ Requeue task
  │  │  └─ Wait (exponential backoff)
  │  │
  │  └─ Retry Count >= Max Retries
  │     ├─ Mark as FAILED
  │     ├─ Store error details
  │     └─ Notify user
  │
  └─ Success
     ├─ Store result
     ├─ Update memory
     └─ Notify user
```

## Performance Considerations

### Concurrency
- Max concurrent tasks: configurable (default: 5)
- Async/await for all I/O
- Connection pooling for DB
- Redis for fast cache

### Memory Management
- Short-term memory: 1 hour TTL
- Long-term memory: 30 day TTL
- Automatic cleanup of expired entries
- Vector DB for semantic search

### Scalability
- Horizontal scaling via task queue
- Load balancing for API
- Database replication
- Redis cluster for caching

## Security Architecture

```
┌──────────────────────────────┐
│ Input Validation             │
│ ├─ Pydantic schemas          │
│ ├─ Type checking             │
│ └─ Sanitization              │
└────────────┬─────────────────┘
             │
┌────────────▼─────────────────┐
│ Authentication/Authorization │
│ ├─ JWT tokens               │
│ ├─ Role-based access        │
│ └─ Permission checks        │
└────────────┬─────────────────┘
             │
┌────────────▼─────────────────┐
│ Tool Execution Sandbox       │
│ ├─ Isolated namespace        │
│ ├─ Resource limits           │
│ └─ Timeout controls          │
└────────────┬─────────────────┘
             │
┌────────────▼─────────────────┐
│ Output Filtering             │
│ ├─ XSS prevention            │
│ ├─ SQL injection prevention  │
│ └─ Secret masking            │
└──────────────────────────────┘
```

## Deployment Architecture

### Docker Compose
```yaml
Services:
├── PostgreSQL (database)
├── Redis (cache & queue)
├── Backend (FastAPI)
├── Frontend (Next.js)
└── Optional:
    ├── Nginx (reverse proxy)
    ├── Prometheus (monitoring)
    └── Grafana (visualization)

Networks:
└── agente_network (internal)

Volumes:
├── postgres_data
└── redis_data
```

### Production Deployment
```
Load Balancer
├─ Backend Instance 1
├─ Backend Instance 2
└─ Backend Instance N

PostgreSQL (Primary/Replica)
Redis Cluster
Object Storage (for files)
Monitoring & Logging
```

## Integration Points

### LLM Providers
- OpenAI (gpt-4-turbo)
- Anthropic (claude-3-opus)
- Gemini (future)
- Custom providers (extensible)

### External Services
- Web search APIs
- Email services
- Cloud storage
- Third-party APIs

### Monitoring
- Sentry (error tracking)
- Datadog (APM)
- LogStash (logging)
- Prometheus (metrics)
