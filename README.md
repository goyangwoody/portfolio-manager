# Portfolio Manager

A comprehensive portfolio management system built for the 2025 DB GAPS competition by team "The Next Warren Buffetts" from Seoul National University.

## 🚀 Live Demo

The application is deployed on AWS using EC2 with Docker containerization and RDS for database management.

## 🏗️ Architecture

### Tech Stack
- **Frontend**: React + TypeScript with Vite
- **Backend**: FastAPI (Python)
- **Database**: MySQL on AWS RDS
- **Deployment**: Docker on AWS EC2
- **Web Server**: Nginx with SSL/TLS

### Project Structure
```
├── PortfolioPulse/          # Frontend (React + TypeScript)
│   ├── client/
│   │   ├── src/
│   │   │   ├── components/  # Reusable UI components
│   │   │   ├── pages/       # Page components
│   │   │   └── lib/         # Utilities and helpers
│   │   └── package.json
│   └── shared/              # Shared types between frontend and backend
├── api/                     # Backend (FastAPI)
│   ├── main.py             # FastAPI application entry point
│   ├── database.py         # Database configuration
│   ├── requirements.txt    # Python dependencies
│   ├── routers/            # API route handlers
│   ├── services/           # Business logic
│   ├── schemas/            # Pydantic models
│   └── models/             # Database models
├── src/                    # Data processing and utilities
│   ├── scripts/            # Data fetching and processing scripts
│   │   ├── fetch_snapshots.py
│   │   ├── improved_market_data_collector.py
│   │   └── attribution_analyzer_new.py
│   └── pm/                 # Core portfolio management modules
│       ├── data/           # Data handling
│       ├── db/             # Database models and connections
│       └── portfolio/      # Portfolio logic
├── docker-compose.yml      # Docker orchestration
└── nginx/                  # Nginx configuration
```

## 🔧 Installation & Setup

### Prerequisites
- Node.js 18+ and npm
- Python 3.9+
- Docker and Docker Compose
- MySQL (or AWS RDS)

### Local Development

#### 1. Backend Setup
```bash
cd api
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your database credentials and API keys

# Run the FastAPI server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 2. Frontend Setup
```bash
cd PortfolioPulse
npm install

# Start the development server
npm run dev
```

#### 3. Python Package Setup (for data scripts)
From the project root:
```bash
pip install -e .
```

This enables imports from the `src/` directory throughout the project.

### Production Deployment (Docker)

#### 1. Build and Deploy
```bash
# Build frontend
cd PortfolioPulse
npm run build

# Deploy with Docker Compose
docker-compose up -d
```

#### 2. SSL Certificate (Let's Encrypt)
```bash
# Generate SSL certificate
docker-compose run --rm certbot certonly --webroot --webroot-path /var/www/certbot/ -d yourdomain.com

# Auto-renewal (add to crontab)
0 12 * * * docker-compose run --rm certbot renew --quiet
```

## 📊 Features

### Portfolio Management
- **Multi-portfolio tracking** with real-time performance metrics
- **KPI dashboard** showing Total Return, NAV, and Cash Ratio
- **Benchmark comparison** against KOSPI, S&P 500, and other indices
- **Risk analysis** with various risk metrics and attribution

### Data Processing
- **Automated market data collection** using yfinance and web scraping
- **Position snapshot algorithms** for portfolio state tracking
- **Daily return calculations** and performance attribution
- **Market instrument data** for benchmark comparisons

### User Interface
- **Responsive design** optimized for mobile and desktop
- **Dark/Light theme** support
- **Interactive charts** using Recharts
- **Real-time data updates** with React Query

## 🗃️ Database Schema

The system uses MySQL with SQLAlchemy ORM. Key tables include:

- `portfolios` - Portfolio metadata and settings
- `portfolio_nav_daily` - Daily net asset value tracking
- `positions` - Current and historical position data
- `transactions` - All portfolio transactions
- `market_instruments` - Reference data for benchmarks
- `risk_free_rate_daily` - Risk-free rate data for calculations

## 🔑 Key Scripts

### Data Collection
```bash
# Fetch latest market data
python -m src.scripts.improved_market_data_collector

# Update portfolio snapshots
python -m src.scripts.fetch_snapshots

# Run attribution analysis
python -m src.scripts.attribution_analyzer_new
```

### Database Management
```bash
# Initialize database
python api/database.py

# Run data backfill
python -m src.scripts.backfill_asset_name
```

## 🛠️ API Endpoints

### Portfolio Management
- `GET /api/portfolios` - List all portfolios
- `GET /api/portfolios/{id}/performance` - Portfolio performance data
- `GET /api/portfolios/{id}/positions` - Current positions
- `GET /api/portfolios/{id}/risk` - Risk metrics

### Market Data
- `GET /api/assets` - Asset information
- `GET /api/market-data` - Market data and benchmarks

### Health & Monitoring
- `GET /health` - Application health check

## 🏆 Team - The Next Warren Buffetts

Industrial Engineering students from Seoul National University:

- **Sungahn Kwon** - Financial Risk Manager
- **Seungjae Lee** - Macroeconomic Researcher  
- **Yesung Lee** - Equity Strategist

*Competing in 2025 DB GAPS - Turning analysis into alpha, responsibly.*

## 📈 Performance Features

- **Real-time portfolio tracking** with daily NAV updates
- **Multi-timeframe analysis** (1D, 1W, 1M, All Time)
- **Benchmark outperformance** tracking and visualization
- **Risk-adjusted returns** including Sharpe ratio calculations
- **Attribution analysis** for performance breakdown

## 🔒 Security & Deployment

- **SSL/TLS encryption** with Let's Encrypt certificates
- **Environment-based configuration** for secure credential management
- **Docker containerization** for consistent deployment
- **Health checks** and monitoring for high availability
- **AWS RDS** for managed database with automated backups

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

This is a competition project for 2025 DB GAPS. For questions or collaboration opportunities, please contact the team members.

---

*Built with ❤️ by The Next Warren Buffetts team* 
