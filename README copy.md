# Smart Funding Advisor - SinceAI Hackathon

## Project Overview

AI-powered funding matchmaking system for Business Turku that automatically finds relevant public funding and investment opportunities for companies.

## Architecture

```
Frontend (React + shadcn/ui) → Backend API → Company Enrichment → Funding Discovery → Matching Engine
```

### Core Components:

1. **Company Enrichment Service** - YTJ API + web scraping
2. **Funding Discovery Engine** - Real-time scrapers for Business Finland, ELY, Finnvera
3. **Matching Algorithm** - Prioritized scoring based on 5 criteria
4. **Modern UI** - React with shadcn/ui components and Tailwind CSS

## Performance Targets

- Response time: 10-15 seconds
- Progress indicators for user experience
- Error handling for API failures

## Tech Stack

- **Frontend**: React + TypeScript, shadcn/ui, Tailwind CSS
- **Backend**: FastAPI (Python)
- **AI**: OpenAI API (future enhancement)
- **Data**: In-memory caching + JSON storage

## Quick Setup

### Option 1: Automatic Setup

```bash
# Complete setup (recommended)
./setup.sh
```

### Option 2: Manual Setup

#### Backend Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
cd backend
pip install -r requirements.txt

# Start backend
uvicorn main:app --reload --port 8000
```

#### Frontend Setup

```bash
# Install dependencies
cd frontend
npm install
npm install -D tailwindcss postcss autoprefixer

# Start frontend
npm start
```

## Testing

### Test the Pipeline

```bash
# Test the complete AI pipeline
python test_pipeline.py
```

### Access Points

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## Test Companies

The application includes pre-configured test companies:

1. **CarbonCap Solutions Oy** (Cleantech)

   - 50 employees, €2M R&D funding need
   - Environmental technology focus

2. **TechStart Oy** (Software)
   - 15 employees, €500K investment need
   - AI-powered SaaS platform

## Features

### 🎯 Smart Matching Algorithm

- **Industry alignment** (30% weight)
- **Geographic eligibility** (25% weight)
- **Company size fit** (20% weight)
- **Funding amount match** (15% weight)
- **Application timing** (10% weight)

### 🏢 Company Data Enrichment

- Finnish YTJ/PRH API integration
- Automatic industry classification
- Company size and stage inference
- Missing data completion

### 💰 Funding Source Discovery

- **Business Finland**: Innovation and R&D grants
- **ELY Centers**: Startup grants and SME development
- **Finnvera**: Loans and guarantees
- Real-time deadline validation

### 🎨 Modern UI/UX

- Clean, professional interface with shadcn/ui
- Responsive design with Tailwind CSS
- Progress indicators and error handling
- Detailed match explanations and next steps

## Demo Flow

1. **Load Test Company**: Click pre-configured test company buttons
2. **Enter Details**: Fill in company information form
3. **AI Analysis**: Watch real-time progress as the system:
   - Enriches company data via YTJ API
   - Discovers current funding opportunities
   - Calculates match scores
   - Generates recommendations
4. **Review Results**: See ranked funding recommendations with:
   - Match percentage and breakdown
   - Funding details and requirements
   - Next steps and important notes

## Development

### Project Structure

```
SinceAI/
├── backend/
│   ├── models/schemas.py           # Data models
│   ├── services/
│   │   ├── company_enrichment.py  # YTJ API integration
│   │   ├── funding_discovery.py   # Web scraping
│   │   └── matching_engine.py     # AI matching logic
│   └── main.py                    # FastAPI application
├── frontend/
│   ├── src/
│   │   ├── components/ui/          # shadcn/ui components
│   │   ├── lib/utils.js           # Utilities
│   │   └── App.js                 # Main React component
│   ├── tailwind.config.js         # Tailwind configuration
│   └── package.json               # Dependencies
└── test_pipeline.py               # Integration tests
```

### Key Design Decisions

- **Option A Implementation**: Real-time scraping for current data
- **Modular architecture**: Easy to add new funding sources
- **Modern UI**: Professional look suitable for business advisors
- **Error resilience**: Graceful degradation when services fail

## Future Enhancements

- [ ] OpenAI integration for better company analysis
- [ ] Additional funding sources (EU programs, foundations)
- [ ] CRM integration (MS Dynamics)
- [ ] User authentication and company profiles
- [ ] Advanced filtering and search
- [ ] Application tracking and reminders

## SinceAI Hackathon 2025

**Team**: Smart Funding Advisor  
**Challenge**: AI tool for automatic funding discovery  
**Goal**: Prove technical feasibility and practical utility
