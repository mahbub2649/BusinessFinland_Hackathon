# Smart Funding Advisor 🚀

AI-powered funding matchmaking platform that helps Finnish companies discover and match with relevant public funding opportunities in under 15 seconds.

## Overview

Smart Funding Advisor is a full-stack web application that automates the discovery and matching of public funding opportunities for Finnish companies. The system combines real-time web scraping, xAI-powered analysis with web search capabilities, and intelligent matching algorithms to deliver personalized funding recommendations.

### Key Features

- **AI-Powered Company Analysis**: Uses xAI Grok with web search to generate comprehensive company insights, market analysis, and growth potential assessments
- **Automated Funding Discovery**: Scrapes and discovers funding programs from Business Finland, ELY-keskus, and Finnvera
- **Intelligent Matching Engine**: Multi-criteria scoring algorithm (industry 30%, geography 25%, company size 20%, funding amount 15%, deadline 10%)
- **Real-time Translation**: Finnish to English translation for funding program descriptions
- **Smart Caching**: 24-hour cache with 85%+ hit rate reduces costs and improves performance
- **Citation Tracking**: Transparent AI responses with source citations for all web research

### Tech Stack

**Backend:**
- Python 3.11+ with FastAPI
- xAI SDK (Grok with web search)
- Beautiful Soup 4 (web scraping)
- HTTPX (async HTTP client)
- Pydantic (data validation)

**Frontend:**
- React 18
- shadcn/ui components
- Tailwind CSS
- Axios (HTTP client)
- Lucide React (icons)

**Infrastructure:**
- Docker & Docker Compose
- File-based caching (24-hour TTL)
- YTJ API integration (Finnish company data)

---

## Prerequisites

### Required Software

- **Python**: 3.11 or higher
- **Node.js**: 18.x or higher
- **npm**: 9.x or higher (comes with Node.js)
- **Docker**: 20.x or higher (optional, for containerized deployment)
- **Docker Compose**: 2.x or higher (optional)

### API Keys

- **xAI API Key**: Required for AI-powered features ([Get API key](https://x.ai))

### System Requirements

- **RAM**: Minimum 4GB (8GB recommended)
- **Storage**: 2GB free space
- **OS**: Linux, macOS, or Windows with WSL2

---

## Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd BusinessFinland_Hackathon
```

### 2. Configure Environment Variables

Copy the example environment file and add your xAI API key:

```bash
cp .env.example .env
```

Edit `.env` file:

```bash
# Required: Add your xAI API key
XAI_API_KEY=your-actual-xai-api-key-here

# Optional: Configuration
USE_XAI_FUNDING_DISCOVERY=true
REACT_APP_BACKEND_URL=http://localhost:8000
GENERATE_SOURCEMAP=false
BROWSER=none
```

---

## Running the Application

### Option 1: Docker (Recommended)

Easiest way to run the entire stack with a single command.

#### Quick Start

```bash
# Make the script executable
chmod +x docker-run.sh

# Start everything (builds containers on first run)
./docker-run.sh
```

#### Manual Docker Commands

```bash
# Build and start all services
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

#### Access Points

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

---

### Option 2: Local Development Setup

Run backend and frontend separately for development with hot reload.

#### Backend Setup

```bash
# Navigate to project root
cd BusinessFinland_Hackathon

# Make setup script executable
chmod +x setup-backend.sh

# Run automated setup
./setup-backend.sh

# Or manual setup:
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
cd backend
pip install -r requirements.txt
```

#### Start Backend

```bash
# From project root with venv activated
source venv/bin/activate
cd backend
uvicorn main:app --reload --port 8000
```

Backend will be available at: **http://localhost:8000**

#### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Make setup script executable (from project root)
chmod +x setup-frontend.sh

# Run automated setup
./setup-frontend.sh

# Or manual setup:
npm install
```

#### Start Frontend

```bash
# From frontend directory
npm start
```

Frontend will be available at: **http://localhost:3000**

---

### Option 3: GUI Server Manager

For users who prefer a graphical interface.

```bash
# From project root
python3 server_manager.py
```

Features:
- Start/stop backend and frontend with buttons
- View real-time console output
- Restart services independently
- Visual status indicators

---

## Project Structure

```
BusinessFinland_Hackathon/
├── backend/
│   ├── main.py                    # FastAPI application entry point
│   ├── requirements.txt           # Python dependencies
│   ├── cache/                     # File-based cache directory
│   ├── models/
│   │   └── schemas.py            # Pydantic data models
│   └── services/
│       ├── company_enrichment.py  # YTJ API & data enrichment
│       ├── xai_service.py        # xAI Grok integration
│       ├── funding_discovery.py   # Web scraping engine
│       ├── xai_funding_discovery.py # AI-powered discovery
│       └── matching_engine.py     # Scoring & ranking algorithm
├── frontend/
│   ├── package.json              # Node.js dependencies
│   ├── src/
│   │   ├── App.js               # Main React component
│   │   ├── App.css              # Styles
│   │   └── components/ui/       # shadcn/ui components
│   └── public/
│       └── index.html           # HTML template
├── docker-compose.yml            # Multi-container Docker config
├── Dockerfile                    # Production Docker image
├── .env                         # Environment variables (create from .env.example)
├── .env.example                 # Environment template
├── server_manager.py            # GUI server manager
└── README.md                    # This file
```

---

## API Endpoints

### Main Endpoints

| Endpoint | Method | Purpose | Response Time |
|----------|--------|---------|---------------|
| `/api/analyze-company` | POST | Complete analysis pipeline | 10-15s (first), <2s (cached) |
| `/api/generate-company-description` | POST | AI company analysis with web search | 3-5s |
| `/api/translate-description` | POST | Finnish to English translation | 2-3s |
| `/api/clear-cache` | DELETE | Clear all cached data | <1s |
| `/api/health` | GET | System health check | <100ms |

### Example Request

```bash
curl -X POST http://localhost:8000/api/analyze-company \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Example Oy",
    "business_id": "1234567-8",
    "industry": "Technology",
    "employee_count": 25,
    "funding_need_amount": 500000,
    "growth_stage": "growth",
    "funding_purpose": "rdi",
    "additional_info": "AI and machine learning solutions"
  }'
```

---

## Configuration

### Backend Configuration

Edit [`backend/main.py`](backend/main.py) for:
- Cache duration (default: 24 hours)
- Rate limiting settings
- CORS origins
- Funding discovery mode (XAI vs scraping)

### Frontend Configuration

Edit [`frontend/src/setupProxy.js`](frontend/src/setupProxy.js) for:
- Backend API URL
- Proxy settings

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `XAI_API_KEY` | xAI API authentication key | **Required** |
| `USE_XAI_FUNDING_DISCOVERY` | Enable AI-powered funding discovery | `true` |
| `REACT_APP_BACKEND_URL` | Backend API endpoint | `http://localhost:8000` |
| `GENERATE_SOURCEMAP` | React source maps | `false` |
| `PYTHONUNBUFFERED` | Python output buffering | `1` |

---

## Usage

### Quick Test with Sample Companies

The application includes 6 pre-configured test companies:

1. **CarbonCap Solutions Oy** - Environmental tech (€2M)
2. **Turku Tech Hub Oy** - Software development (€750K)
3. **Nordic BioInnovations Oy** - Biotechnology (€1.5M)
4. **Meyer Turku Oy** - Shipbuilding (€10M)
5. **Turku Science Park Oy** - Business development (€1.5M)
6. **Kongsberg Maritime Finland OY** - Maritime tech (€3M)
7. **Reaktor Advanced Technologies Oy** - Software consulting (€1M)

Click any test company button to auto-fill the form and see results instantly.

### Manual Company Input

1. **Company Information**:
   - Company Name (required)
   - Business ID (optional, e.g., 1234567-8)
   - Industry (required)
   - Employee Count (required)

2. **Funding Details**:
   - Funding Need Amount (€)
   - Growth Stage (pre-seed, seed, growth, scale-up)
   - Funding Purpose (R&D, internationalization, investments, equipment, working capital)
   - Additional Information (optional context)

3. Click **"Find Funding Opportunities"**

### Understanding Results

**AI Company Analysis:**
- Company description and market insights
- Market size estimation
- Company website (auto-discovered)
- Research sources with citations
- AI confidence level

**Funding Recommendations:**
- Match score (0-100%)
- Detailed scoring breakdown by criteria
- Funding range and program type
- Eligibility requirements
- Application deadlines
- Next steps to apply
- Why this program matches

---

## Troubleshooting

### Common Issues

#### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000  # macOS/Linux
netstat -ano | findstr :8000  # Windows

# Kill process or change port in .env
```

#### Module Not Found Errors

```bash
# Backend
source venv/bin/activate
pip install -r backend/requirements.txt

# Frontend
cd frontend
npm install
```

#### Docker Container Not Starting

```bash
# Check logs
docker-compose logs backend
docker-compose logs frontend

# Rebuild from scratch
docker-compose down -v
docker-compose build --no-cache
docker-compose up
```

#### API Key Issues

```bash
# Verify .env file exists and contains XAI_API_KEY
cat .env | grep XAI_API_KEY

# Restart services after changing .env
docker-compose restart  # Docker
# or restart backend manually
```

#### Cache Issues

```bash
# Clear cache via API
curl -X DELETE http://localhost:8000/api/clear-cache

# Or manually delete cache files
rm -rf backend/cache/*

# Docker: Clear cache volume
docker-compose down -v
```

---

## Performance & Cost

### Performance Metrics

- **First Request**: 10-15 seconds (uncached)
- **Cached Request**: <2 seconds (85%+ cache hit rate)
- **AI Analysis**: 3-5 seconds
- **Target Uptime**: 99.9%

### Cost Estimates

**Pilot Environment (€300-500/month):**
- Cloud VM: €60/month
- xAI API (~500 requests/day): €225/month
- Redis Cache: €15/month
- Storage & Bandwidth: €15/month

**Production Environment (€800-1200/month):**
- 2x App Service instances: €140/month
- xAI API (~2000 requests/day): €900/month
- Redis Cache: €60/month
- Database, storage, monitoring: €120/month

**Cost Optimization:**
- 85%+ cache hit rate reduces API costs by 80%
- Estimated production cost: €600-700/month with caching

---

## Development

### Running Tests

```bash
# Backend tests (future)
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

### Code Style

```bash
# Python formatting
pip install black
black backend/

# JavaScript formatting
cd frontend
npm run format
```

### Adding New Funding Sources

1. Create scraper in [`backend/services/funding_discovery.py`](backend/services/funding_discovery.py)
2. Implement `scrape()` method returning `List[FundingProgram]`
3. Add to `FundingDiscoveryService.discover_funding()`
4. Update cache key generation

---

## Deployment

### Production Docker

```bash
# Build production image
docker build -t smart-funding-advisor:latest .

# Run production container
docker run -d \
  -p 8000:8000 \
  -e XAI_API_KEY=your-key \
  -v $(pwd)/backend/cache:/app/backend/cache \
  --name funding-advisor \
  smart-funding-advisor:latest
```

### Cloud Deployment (Azure/AWS)

See [`project_documentation.html`](project_documentation.html) for detailed deployment guide including:
- Infrastructure as Code (Terraform)
- Auto-scaling configuration
- Multi-region setup
- CI/CD pipeline
- Monitoring & alerting

---

## Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## License

This project was developed for the SinceAI Hackathon 2025.

---

## Support & Documentation

- **Full Documentation**: See [`project_documentation.html`](project_documentation.html)
- **Docker Guide**: See [`DOCKER.md`](DOCKER.md)
- **API Documentation**: http://localhost:8000/docs (when running)
- **Issues**: Open an issue on GitHub

---

## Acknowledgments

- **SinceAI Hackathon 2025** for the opportunity
- **Business Turku** for domain expertise and requirements
- **xAI** for Grok API with web search capabilities
- **YTJ/PRH** for Finnish company data API

---

**Built with ❤️ using xAI Grok, FastAPI, and React**