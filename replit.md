# AutoSenseAI

## Overview
AutoSenseAI is an Autonomous Predictive Maintenance & Smart Breakdown Management Platform built for the EY Techathon 6.0. It uses AI agents to predict vehicle service needs, manage breakdowns, and provide comprehensive analytics for automotive OEMs and service centers.

## Tech Stack
- **Frontend**: Streamlit (Dual portals: User & Admin)
- **Backend**: Python Flask with REST-style services
- **Database**: SQLite with SQLAlchemy ORM (PostgreSQL-ready)
- **AI/Logic**: Agent-based architecture with ML + rule-based hybrid

## Project Structure
```
autosenseai/
├── app.py                    # Main Streamlit application
├── database/
│   ├── models.py             # SQLAlchemy models
│   ├── seed_data.py          # Demo data seeding
│   └── __init__.py
├── backend/
│   ├── agents/               # 10 AI agents + orchestrator
│   │   ├── orchestrator.py
│   │   ├── prediction_agent.py
│   │   ├── alert_agent.py
│   │   ├── scheduling_agent.py
│   │   ├── breakdown_agent.py
│   │   ├── location_agent.py
│   │   ├── garage_recommendation_agent.py
│   │   ├── eta_agent.py
│   │   ├── pricing_agent.py
│   │   ├── visualization_agent.py
│   │   ├── feedback_agent.py
│   │   └── base_agent.py
│   ├── services/             # Business logic services
│   │   ├── vehicle_service.py
│   │   ├── service_request_service.py
│   │   ├── breakdown_service.py
│   │   ├── garage_service.py
│   │   ├── spare_parts_service.py
│   │   ├── analytics_service.py
│   │   └── alert_service.py
│   └── routes/
├── frontend/
│   ├── user_portal.py        # User-facing portal
│   ├── admin_portal.py       # Admin/OEM portal
│   └── components/
│       └── charts.py         # Reusable chart components
├── utils/
│   └── auth.py               # JWT authentication
└── .streamlit/
    └── config.toml           # Streamlit configuration
```

## Key Features

### User Portal
- Vehicle Dashboard with health indicators (engine, brakes, battery, tires)
- AI-driven service predictions with urgency scores
- Smart service scheduling with automatic slot finding
- Emergency breakdown assistance with live location
- Nearby garage recommendations with ETA and pricing
- Proactive alerts for service reminders

### Admin Portal
- Dashboard with KPIs (vehicles, services, breakdowns, utilization)
- Service & breakdown management with status updates
- Garage management (add/edit/deactivate)
- Spare parts & pricing management
- Comprehensive analytics with charts
- Agent activity logs

### AI Agents (10 Specialized + 1 Orchestrator)
1. **Prediction Agent**: Predicts next service date
2. **Alert Agent**: Generates proactive alerts
3. **Scheduling Agent**: Finds and books optimal slots
4. **Breakdown Agent**: Handles emergency workflows
5. **Location Tracking Agent**: Tracks vehicle/garage movement
6. **Garage Recommendation Agent**: Finds nearest garages
7. **ETA Estimation Agent**: Calculates arrival/repair times
8. **Pricing Agent**: Estimates repair costs
9. **Visualization Agent**: Converts tables to charts
10. **Feedback/RCA Agent**: Analyzes service quality
11. **Master Orchestrator**: Coordinates all agents

## Demo Credentials
- **User**: john_user / password123 (or sarah_user, mike_user)
- **Admin**: admin / admin123 (or manager / manager123)

## Running the Application
```bash
streamlit run app.py --server.port 5000
```

## Database
- Uses SQLite by default (autosense.db)
- Automatically seeds with demo data on first run
- Tables: users, vehicles, garages, service_requests, breakdown_events, spare_parts, alerts, feedback, agent_logs, service_slots

## Recent Changes
- Initial build with complete feature set
- Dual portal system (User & Admin)
- 10 AI agents with orchestrator
- Interactive visualizations with Plotly
- Map integration with Folium
- Demo data with realistic scenarios
