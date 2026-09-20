# ✈️ TravelPilot

## 🌍 What is TravelPilot?

TravelPilot is an **AI-powered travel planning and itinerary management agent**. It does more than just recommend destinations — it **continuously manages your trip** and intelligently adapts your itinerary when circumstances change.

**Key capabilities:**
- 🗓️ Builds detailed day-by-day itineraries based on destination, dates, budget, interests, and preferences
- 🌤️ Integrates real-time weather forecasts to inform scheduling decisions
- 🗺️ Clusters activities geographically to minimize unnecessary travel time
- 💬 Natural language chat interface — ask anything about your trip
- ⚡ Detects scheduling conflicts and suggests alternatives automatically
- 🔄 Handles disruptions (cancellations, weather, delays) and rebuilds the itinerary
- 💰 Tracks budget across accommodation, transport, food, and activities
- 📄 Exports your full trip dashboard as a PDF

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React + Vite)                      │
│  Home ─ PlanTrip Wizard ─ TripView (Dashboard, Chat, Map, Budget)   │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ HTTP / REST
┌──────────────────────────▼──────────────────────────────────────────┐
│                     BACKEND  (FastAPI + Uvicorn)                     │
│                                                                      │
│   /routers                                                           │
│   ├── chat.py        ─ WebSocket + HTTP chat endpoint                │
│   ├── itinerary.py   ─ CRUD + export endpoints                       │
│   ├── dashboard.py   ─ Trip summary & stats                          │
│   └── profile.py     ─ User profile management                       │
│                                                                      │
│   /services                                                          │
│   ├── itinerary_service.py  ─ Save/load itinerary to DB             │
│   ├── export_service.py     ─ PDF export via ReportLab              │
│   ├── currency_service.py   ─ Currency scaling helpers              │
│   └── conflict_detector.py  ─ Schedule conflict detection           │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────────┐
│                   AGENT LAYER  (LangGraph State Machine)             │
│                                                                      │
│   START ──► classify_intent                                          │
│                    │                                                 │
│         ┌──────────┼──────────────────┐                             │
│         ▼          ▼                  ▼                              │
│     plan_trip  handle_disruption  answer_query                       │
│         │          │                  │                              │
│         └──────────┼──────────────────┘                             │
│                    ▼                                                 │
│              update_budget                                           │
│                    │                                                 │
│                    ▼                                                 │
│            generate_response ──► END                                 │
│                                                                      │
│   Agents:                                                            │
│   ├── planner_agent.py    ─ Builds full day-by-day itineraries      │
│   ├── nlq_agent.py        ─ Natural language Q&A over itinerary     │
│   ├── disruption_agent.py ─ Handles disruptions & suggests alts     │
│   └── budget_agent.py     ─ Calculates & tracks budget              │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────────┐
│                      TOOLS / EXTERNAL APIs                           │
│                                                                      │
│   ├── tavily_tool.py     ─ Attractions, restaurants, hotels         │
│   ├── weather_tool.py    ─ Forecasts (OpenWeatherMap / PyOWM)       │
│   ├── maps_tool.py       ─ Geocoding & routing (Nominatim / OSM)    │
│   └── duckduckgo_tool.py ─ Fallback web search                      │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────────┐
│                   DATABASE  (PostgreSQL + SQLAlchemy)                │
│                                                                      │
│  user_profiles ──► trips ──► itinerary_days ──► activities          │
│                        └──► bookings                                 │
│                        └──► conversation_history                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

### Backend

| Layer | Technology | Purpose |
|-------|-----------|---------|
| API Framework | **FastAPI 0.115** | Async REST API + WebSocket |
| Server | **Uvicorn** | ASGI production server |
| AI Orchestration | **LangGraph** | Stateful multi-agent graph |
| LLM | **Google Gemini Flash** | Planning, Q&A, intent classification |
| LLM SDK | **google-genai + langchain-google-genai** | Gemini API client |
| Database ORM | **SQLAlchemy 2 (async)** | Async ORM |
| DB Driver | **asyncpg** | Async PostgreSQL driver |
| Migrations | **Alembic** | Schema migrations |
| Validation | **Pydantic v2** | Request / response models |
| Search | **Tavily Python** | AI-powered travel data search |
| Search (fallback) | **DuckDuckGo Search** | Alternative search backend |
| Weather | **PyOWM 3.3** | OpenWeatherMap API wrapper |
| PDF Export | **ReportLab + Pillow** | Trip report PDF generation |
| Auth Utilities | **python-jose + passlib** | JWT & bcrypt helpers |
| HTTP Client | **httpx** | Async HTTP for external APIs |

### Frontend

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Framework | **React 19** | UI library |
| Build Tool | **Vite 6 + TypeScript** | Fast dev server & bundler |
| Routing | **React Router v7** | Client-side navigation |
| State Management | **Zustand** | Lightweight global state |
| HTTP Client | **Axios** | API communication |
| Maps | **Leaflet** | Interactive trip maps |
| Charts | **Recharts** | Budget & stats visualizations |
| Animations | **Framer Motion** | Smooth UI transitions |
| Icons | **Lucide React** | Icon library |

### Infrastructure

| Tool | Purpose |
|------|---------|
| **PostgreSQL 16** | Primary relational database |
| **pytest + pytest-asyncio** | Async backend test suite |

---

## 📁 Project Structure

```
TravelPilot/
├── main.py                     # FastAPI app entry point
├── config.py                   # Central settings (pydantic-settings)
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
│
├── agents/                     # LangGraph agent nodes
│   ├── graph.py                # State machine definition & routing
│   ├── state.py                # Shared TravelState TypedDict
│   ├── planner_agent.py        # Full itinerary builder
│   ├── nlq_agent.py            # Natural language Q&A agent
│   ├── disruption_agent.py     # Disruption handler & rebooker
│   └── budget_agent.py         # Budget tracker & calculator
│
├── routers/                    # FastAPI route handlers
│   ├── chat.py                 # /chat endpoint (streaming)
│   ├── itinerary.py            # /itinerary CRUD + export
│   ├── dashboard.py            # /dashboard summary
│   └── profile.py              # /profile user management
│
├── services/                   # Business logic layer
│   ├── itinerary_service.py    # DB persistence for itineraries
│   ├── export_service.py       # PDF generation
│   ├── currency_service.py     # Currency helpers
│   └── conflict_detector.py    # Schedule conflict detection
│
├── tools/                      # External API integrations
│   ├── tavily_tool.py          # Tavily search (attractions, hotels)
│   ├── weather_tool.py         # OpenWeatherMap integration
│   ├── maps_tool.py            # Geocoding & routing (OpenStreetMap)
│   └── duckduckgo_tool.py      # DuckDuckGo fallback search
│
├── database/                   # Data layer
│   ├── connection.py           # Async SQLAlchemy engine & session
│   ├── models.py               # ORM models (Trip, Activity, Booking…)
│   ├── schemas.py              # Pydantic request/response schemas
│   └── crud.py                 # Database operations
│
├── tests/                      # Test suite
│   ├── test_agents.py
│   ├── test_api.py
│   ├── test_services.py
│   └── test_tools.py
│
└── frontend/                   # React + Vite frontend
    ├── src/
    │   ├── pages/
    │   │   ├── Home.tsx        # Landing page
    │   │   ├── PlanTrip.tsx    # Trip planning wizard
    │   │   └── TripView.tsx    # Main trip dashboard
    │   ├── components/
    │   │   ├── ChatPanel.tsx
    │   │   ├── Dashboard.tsx
    │   │   ├── ItineraryView.tsx
    │   │   ├── BudgetTracker.tsx
    │   │   ├── MapView.tsx
    │   │   ├── WeatherWidget.tsx
    │   │   └── BackupOptionsView.tsx
    │   ├── store/              # Zustand stores
    │   └── hooks/              # Custom React hooks
    └── package.json
```

---

## ⚙️ Prerequisites

- **Python 3.11+**
- **Node.js 18+** and **npm**
- **PostgreSQL 14+** running locally (or remote connection URL)
- API keys for:
  - [Google Gemini]
  - [Tavily]
  - [OpenWeatherMap]

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/vikasboggavarapu/TravelPilot.git
cd TravelPilot
```

### 2. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:

```env

GEMINI_API_KEY=your_gemini_api_key_here

TAVILY_API_KEY=your_tavily_api_key_here

OPENWEATHER_API_KEY=your_openweather_api_key_here

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=your_database_name
POSTGRES_USER=your_username
POSTGRES_PASSWORD=your_password
DATABASE_URL=postgresql+asyncpg://your_username:your_password@localhost:5432/your_database_name

# Server
APP_HOST=0.0.0.0
APP_PORT=8000
APP_DEBUG=true
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

### 3. Set up the Backend

```bash
# Create virtual environment
python -m venv venv

# Activate — Windows
venv\Scripts\activate

# Activate — macOS / Linux
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 4. Set up the Database

Ensure PostgreSQL is running, then create the database:

```sql
CREATE DATABASE travelpilot;
```

> Tables are auto-created on first startup via SQLAlchemy's `init_db()` — no manual migration needed.

### 5. Run the Backend

```bash
python main.py
```

Or using Uvicorn directly:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

| URL | Description |
|-----|-------------|
| http://localhost:8000 | API root |
| http://localhost:8000/docs | Swagger UI (interactive docs) |
| http://localhost:8000/redoc | ReDoc documentation |
| http://localhost:8000/health | Health check |

### 6. Run the Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend available at: **http://localhost:5173**

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Welcome message |
| `GET` | `/health` | Service health check |
| `POST` | `/trips` | Create a new trip |
| `GET` | `/trips/{trip_id}` | Get trip by ID |
| `POST` | `/chat` | Send a message to the AI agent |
| `GET` | `/itinerary/{trip_id}` | Fetch full itinerary |
| `GET` | `/itinerary/{trip_id}/export` | Export itinerary as PDF |
| `GET` | `/dashboard/{trip_id}` | Trip dashboard & summary |
| `POST` | `/profile` | Create / update user profile |
| `GET` | `/profile/{user_id}` | Get user profile |

---

## 🤖 How the AI Agent Works

TravelPilot uses a **LangGraph state machine** to route each message to the right specialized agent node:

```
User Message
    │
    ▼
classify_intent  ◄── Gemini classifies: plan | modify | query | disrupt
    │
    ├── plan / modify ──► planner_agent   (Gemini builds itinerary JSON
    │                          │           using weather + search + maps)
    │                          ▼
    │                     update_budget   (recalculates all costs)
    │
    ├── disrupt ──────► disruption_agent  (finds affected activities,
    │                          │           fetches alternatives, reschedules)
    │                          ▼
    │                     update_budget
    │
    └── query ────────► nlq_agent         (answers NL questions about
                               │           the itinerary using Gemini)
                               ▼
                        generate_response ──► User
```

### Intent Examples

| User says… | Intent | Agent |
|---|---|---|
| "Plan a 5-day trip to Goa" | `plan` | Planner Agent |
| "Change my hotel to 4-star" | `modify` | Planner Agent |
| "What's the weather on Day 3?" | `query` | NLQ Agent |
| "My flight got cancelled" | `disrupt` | Disruption Agent |
| "Can I fit this activity today?" | `query` | NLQ Agent |

---

## 🧪 Running Tests

```bash
# Run the full test suite (activate venv first)
pytest tests/ -v

# Run specific test files
pytest tests/test_agents.py -v
pytest tests/test_tools.py -v
pytest tests/test_services.py -v
pytest tests/test_api.py -v
```

---

## 🗄️ Database Schema

| Table | Description |
|-------|-------------|
| `user_profiles` | Traveller profiles and preferences |
| `trips` | Core trip entity — destination, dates, budget, status |
| `itinerary_days` | Day-level plan — theme, weather summary, daily cost |
| `activities` | Individual activities — location, times, cost, alternatives |
| `bookings` | Flights, hotel, and activity bookings |
| `conversation_history` | Full chat history per trip (multi-turn Gemini context) |

---


## 📄 License

This project is for educational and portfolio purposes.

---

*Built with ❤️ using Google Gemini, LangGraph, FastAPI & React*
