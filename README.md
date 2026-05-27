# AI Agent Orchestration Platform

A full-stack platform for creating, configuring, and orchestrating collaborative AI agents. Build multi-agent workflows visually, monitor executions in real-time, and interact with agents through Telegram.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              NGINX (port 80)                            │
│                         Reverse Proxy / Load Balancer                   │
├──────────────────────────────────┬──────────────────────────────────────┤
│        Frontend (port 5173)      │         Backend (port 8000)          │
│                                  │                                      │
│  React + TypeScript + Vite       │  FastAPI + async SQLAlchemy          │
│  ┌──────────────────────┐        │  ┌────────────────────────────┐      │
│  │  React Flow Canvas   │        │  │      API Layer (/api)      │      │
│  │  (Workflow Builder)   │        │  │  agents / workflows /      │      │
│  └──────────────────────┘        │  │  executions / channels     │      │
│  ┌──────────────────────┐        │  └────────────┬───────────────┘      │
│  │  Zustand Stores      │        │               │                      │
│  │  + API Client Layer   │◄──────►│  ┌────────────▼───────────────┐      │
│  └──────────────────────┘  REST  │  │     Service Layer           │      │
│  ┌──────────────────────┐        │  │  Business logic + CRUD      │      │
│  │  Monitoring Dashboard │◄──WS──►│  └────────────┬───────────────┘      │
│  │  (LogStream, Timeline)│        │               │                      │
│  └──────────────────────┘        │  ┌────────────▼───────────────┐      │
│                                  │  │   LangGraph Engine          │      │
│  Tailwind CSS                    │  │  ┌─────────────────────┐   │      │
│  lucide-react icons              │  │  │ Graph Compiler       │   │      │
│                                  │  │  │ (JSON → StateGraph)  │   │      │
│                                  │  │  ├─────────────────────┤   │      │
│                                  │  │  │ Agent Node Factory   │   │      │
│                                  │  │  │ (LLM + Tools + WS)  │   │      │
│                                  │  │  ├─────────────────────┤   │      │
│                                  │  │  │ Tool Registry        │   │      │
│                                  │  │  │ (search, scrape,     │   │      │
│                                  │  │  │  calc, file_writer)  │   │      │
│                                  │  │  └─────────────────────┘   │      │
│                                  │  └────────────┬───────────────┘      │
│                                  │               │                      │
│                                  │  ┌────────────▼───────────────┐      │
│                                  │  │  Integrations              │      │
│                                  │  │  ├─ Telegram Bot (polling) │      │
│                                  │  │  └─ WebSocket Manager      │      │
│                                  │  └────────────────────────────┘      │
├──────────────────────────────────┴──────────────────────────────────────┤
│                        PostgreSQL 16 (port 5432)                        │
│              agents | workflows | executions | messages | channels       │
└─────────────────────────────────────────────────────────────────────────┘
```

## Tech Stack Justification

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **Backend** | Python + FastAPI | Async-native, best ecosystem for AI/ML libraries, first-class support for LangChain/LangGraph |
| **Frontend** | React + TypeScript + Vite | Type safety, fast HMR, rich component ecosystem (React Flow for visual builder) |
| **AI Framework** | LangGraph | Most flexible for custom workflow topologies — supports conditional routing, feedback loops, and parallel execution natively. Unlike CrewAI (fixed crew patterns) or AutoGen (conversation-centric), LangGraph compiles arbitrary directed graphs, which maps directly to our visual workflow builder |
| **Database** | PostgreSQL + async SQLAlchemy | Robust concurrent access for parallel agent operations, JSONB for flexible agent configs, battle-tested for production |
| **Messaging** | Telegram Bot API | Zero business verification (unlike WhatsApp), instant bot creation, polling mode works locally without ngrok |
| **State Management** | Zustand | Minimal boilerplate, works naturally with React Flow's internal state management |
| **Styling** | Tailwind CSS | Utility-first, consistent design system, fast iteration |

## Features

### Agent Management
- Full CRUD for AI agents with 10+ configurable dimensions
- **Basic config**: name, role, system prompt, model selection (gpt-4o, gpt-4o-mini), temperature, max tokens
- **Tools**: web search (DuckDuckGo), web scraping, calculator, file writer
- **Memory**: toggle on/off, configurable context window size
- **Guardrails**: blocked topics filter, token limits, require human approval
- **Interaction rules**: max conversation turns, handoff targets
- **Scheduling**: cron-based agent activation

### Visual Workflow Builder
- Drag-and-drop canvas powered by React Flow
- Custom node types: Agent, Condition, Start, End
- Conditional routing (e.g., classify input and route to different agents)
- Feedback loops (e.g., Reviewer sends Writer back for revision)
- Save, validate, and run workflows from the builder
- Graph validation before execution

### Pre-built Workflow Templates

**1. Research & Summarize**
```
Start → Researcher (web_search, web_scrape) → Writer → Reviewer → [Condition]
                                                  ↑                     │
                                                  └── needs_revision ───┘
                                                        approved → End
```
A 3-agent pipeline where the Researcher searches the web for a topic, the Writer composes a structured report, and the Reviewer evaluates it. If revision is needed, the Writer receives specific feedback and rewrites. Max 3 revision cycles.

**2. Customer Support Triage**
```
Start → Triage Agent → [Condition] → Billing Agent   → End
                            │       → Technical Agent → End
                            └──────→ General Agent   → End
```
Routes customer queries through a classifier to specialized support agents for billing, technical, or general questions.

### Live Monitoring
- Real-time log streaming via WebSocket
- Animated workflow graph showing active/completed/pending nodes
- Inter-agent message timeline
- Token usage and cost tracking per execution (with model-specific pricing)
- Dashboard with execution history and status overview

### Telegram Integration
- Bot runs in polling mode (no public URL / ngrok required)
- Link a bot to any workflow or individual agent
- Conversation history maintained per chat
- Supports `/start`, `/help`, `/reset` commands
- Automatic message splitting for long responses

## Quick Start

### Prerequisites
- Docker and Docker Compose
- An OpenAI API key ([get one here](https://platform.openai.com/))
- (Optional) A Telegram bot token ([create one via @BotFather](https://t.me/botfather))

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/chakshu-dhannawat/ai-agent-orchestration-platform.git
cd ai-agent-orchestration-platform

# 2. Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY (required)
# Optionally add TELEGRAM_BOT_TOKEN

# 3. Start everything
docker-compose up --build
```

That's it. The platform is now running at:
- **Web UI**: http://localhost:4444 (via nginx) or http://localhost:3333 (direct Vite)
- **API**: http://localhost:9999/api
- **API Docs**: http://localhost:9999/docs
- **PostgreSQL**: localhost:5434

### First Run Walkthrough

1. Open http://localhost:4444 in your browser
2. Go to **Templates** → click **"Use Template"** on "Research & Summarize"
3. This creates the 3 agents and workflow automatically
4. Go to **Workflows** → open the created workflow
5. Click **"Run"** and enter a topic like: *"Latest developments in quantum computing 2025"*
6. Go to **Executions** → click on the running execution to see live monitoring
7. Watch agents collaborate in real-time: Researcher searches the web, Writer drafts, Reviewer provides feedback

### Telegram Setup (Optional)

1. Message [@BotFather](https://t.me/botfather) on Telegram to create a new bot
2. Copy the bot token into `.env` as `TELEGRAM_BOT_TOKEN`
3. Restart the backend: `docker-compose restart backend`
4. In the Web UI, go to **Channels** → create a new Telegram channel
5. Link it to a workflow or agent
6. Message your bot on Telegram — it will execute the linked workflow and respond

## Project Structure

```
ai-agent-orchestration-platform/
├── docker-compose.yml          # Single-command orchestration
├── .env.example                # Environment template
├── Makefile                    # Development shortcuts
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py             # FastAPI app + lifespan
│   │   ├── config.py           # Environment settings
│   │   ├── database.py         # Async SQLAlchemy
│   │   ├── seed.py             # Template + sample data seeding
│   │   │
│   │   ├── models/             # SQLAlchemy ORM models
│   │   │   ├── agent.py        # Agent (10+ configurable fields)
│   │   │   ├── workflow.py     # Workflow + graph definition
│   │   │   ├── execution.py    # Execution + logs
│   │   │   ├── message.py      # Inter-agent messages
│   │   │   └── channel.py      # External channel configs
│   │   │
│   │   ├── schemas/            # Pydantic request/response models
│   │   ├── api/                # FastAPI route handlers
│   │   │   ├── agents.py       # Agent CRUD
│   │   │   ├── workflows.py    # Workflow CRUD + validation
│   │   │   ├── executions.py   # Start/monitor/cancel executions
│   │   │   ├── templates.py    # Template catalog + instantiation
│   │   │   ├── channels.py     # Channel management
│   │   │   └── ws.py           # WebSocket endpoints
│   │   │
│   │   ├── services/           # Business logic layer
│   │   ├── engine/             # LangGraph runtime (core)
│   │   │   ├── runtime.py      # Graph compiler + executor
│   │   │   ├── nodes.py        # Agent node factory
│   │   │   ├── state.py        # Workflow state definition
│   │   │   ├── tools.py        # Tool registry
│   │   │   └── callbacks.py    # Streaming callbacks
│   │   │
│   │   ├── integrations/       # External channel adapters
│   │   │   ├── telegram.py     # Telegram bot (polling mode)
│   │   │   └── base.py         # Abstract channel interface
│   │   │
│   │   └── templates/          # Pre-built workflow definitions
│   │       ├── research_summarize.py
│   │       └── customer_support.py
│   │
│   └── tests/                  # 93 tests (pytest + pytest-asyncio)
│       ├── test_agents_api.py
│       ├── test_workflows_api.py
│       ├── test_execution_engine.py
│       ├── test_templates.py
│       └── test_telegram.py
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   └── src/
│       ├── pages/              # Route pages
│       │   ├── Dashboard.tsx
│       │   ├── AgentList.tsx / AgentDetail.tsx
│       │   ├── WorkflowList.tsx / WorkflowBuilder.tsx
│       │   ├── ExecutionList.tsx / ExecutionMonitor.tsx
│       │   ├── TemplateGallery.tsx
│       │   └── ChannelList.tsx
│       │
│       ├── components/
│       │   ├── layout/         # Sidebar, Header, Layout
│       │   ├── workflow/nodes/  # React Flow custom nodes
│       │   └── monitoring/     # LogStream, MessageTimeline, TokenCostTracker
│       │
│       ├── api/                # Axios client + API modules
│       ├── store/              # Zustand state stores
│       ├── types/              # TypeScript interfaces
│       └── hooks/              # Custom hooks (useWebSocket)
│
└── nginx/
    └── nginx.conf              # Reverse proxy config
```

## Architecture Decisions

### Why compile React Flow JSON → LangGraph at runtime?
The visual workflow builder (React Flow) operates natively on a node/edge JSON format. Rather than maintaining two parallel graph representations, we store the React Flow JSON directly and compile it to a LangGraph `StateGraph` only at execution time. This means:
- Zero translation overhead in the builder
- Workflows are versioned as simple JSON diffs
- The builder never needs to know about LangGraph internals

### Why async SQLAlchemy?
The engine runs multiple LLM calls concurrently within a single execution. Async DB access ensures message persistence and log writes don't block the event loop while agents are communicating.

### Why DuckDuckGo for web search?
Zero-configuration. No API key needed. The evaluator can `docker-compose up` and web search tools work immediately without signing up for any additional service.

### Why Telegram polling mode?
The evaluator runs this locally without a public URL. Polling mode means Telegram integration works out of the box without ngrok or similar tunneling tools.

## Adding New Workflow Templates

1. Create a new file in `backend/app/templates/` (e.g., `my_template.py`)
2. Define the template with:
   - `TEMPLATE_ID`, `TEMPLATE_NAME`, `TEMPLATE_DESCRIPTION`
   - `AGENTS` list with full agent configurations
   - `GRAPH_DEFINITION` dict in React Flow format (nodes + edges)
3. Add the template to the `TEMPLATES` list in `backend/app/templates/__init__.py`
4. Restart the backend — the template will appear in the Template Gallery

## Adding New Messaging Channels

1. Create a new adapter in `backend/app/integrations/` inheriting from `ChannelAdapter`
2. Implement `start()`, `stop()`, `send_message()`, and `handle_incoming()`
3. Register the adapter in `backend/app/main.py` lifespan (similar to Telegram)
4. Add the channel type to the frontend's `ChannelList.tsx` type selector

## Running Tests

```bash
# Run all tests (no Docker needed — uses in-memory SQLite)
cd backend
pip install -r requirements.txt
pytest -v

# Run specific test file
pytest tests/test_agents_api.py -v

# Run with coverage
pytest --cov=app --cov-report=term-missing
```

## Development Commands

```bash
make up          # Start all services
make down        # Stop all services
make build       # Rebuild containers
make logs        # Follow logs
make test        # Run backend tests
make migrate     # Run database migrations
make seed        # Seed sample data
make backend-shell   # Open shell in backend container
make frontend-shell  # Open shell in frontend container
```

## API Documentation

Interactive API docs are available at http://localhost:9999/docs when the backend is running.

### Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET/POST` | `/api/agents` | List / create agents |
| `GET/PUT/DELETE` | `/api/agents/{id}` | Get / update / delete agent |
| `GET/POST` | `/api/workflows` | List / create workflows |
| `POST` | `/api/workflows/{id}/validate` | Validate workflow graph |
| `POST` | `/api/executions` | Start a workflow execution |
| `GET` | `/api/executions/{id}` | Get execution details + status |
| `GET` | `/api/executions/{id}/messages` | Get inter-agent messages |
| `GET` | `/api/templates/catalog` | Browse pre-built templates |
| `POST` | `/api/templates/catalog/{id}/instantiate` | Create workflow from template |
| `WS` | `/ws/executions/{id}` | Stream real-time execution events |
| `WS` | `/ws/dashboard` | Stream all execution updates |

## License

MIT
