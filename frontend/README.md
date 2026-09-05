# Fraud Detection System - Frontend

Modern React-based dashboard for real-time fraud detection and analysis.

## Features

- 🎨 **Modern UI** - Beautiful, responsive design with glassmorphism effects
- 📊 **Real-time Analytics** - Live dashboard with transaction statistics
- 🔍 **Transaction Analysis** - Analyze transactions for fraud risk
- 🎯 **Risk Scoring** - Get detailed risk scores and predictions
- 📈 **Visual Analytics** - Charts and graphs for better insights
- 🚨 **Fraud Alerts** - Immediate notification for suspicious transactions
- 📱 **Responsive Design** - Works on desktop, tablet, and mobile

## Prerequisites

- Node.js 16+ and npm
- Backend API running on `http://localhost:8000`

## Quick Start

### Development Mode

```bash
cd frontend
npm install
npm start
```

The app will open at `http://localhost:3000`

### Production Build

```bash
npm run build
npm run serve  # or use 'serve' package
```

## Environment Variables

Create a `.env` file in the frontend directory:

```env
REACT_APP_API_URL=http://localhost:8000
```

## Docker

Build and run with Docker:

```bash
docker build -t fraud-detection-frontend .
docker run -p 3000:3000 -e REACT_APP_API_URL=http://localhost:8000 fraud-detection-frontend
```

Or use docker-compose:

```bash
docker-compose up frontend
```

## API Endpoints Used

The frontend communicates with:

- `GET /health` - Health check
- `POST /api/v1/transactions/predict` - Predict fraud for a transaction

## Project Structure

```
frontend/
├── public/
│   └── index.html          # HTML template
├── src/
│   ├── components/
│   │   ├── Dashboard.js     # Results dashboard
│   │   ├── Header.js        # App header
│   │   └── TransactionForm.js # Input form
│   ├── App.js               # Main app component
│   └── index.js             # Entry point
├── package.json
└── Dockerfile
```

## Components

- **Header** - Navigation and API status indicator
- **TransactionForm** - Input form for transaction details
- **Dashboard** - Results display with risk analysis

## Styling

The app uses custom CSS with:
- CSS Grid and Flexbox layouts
- Glassmorphism effects
- Smooth animations and transitions
- Dark theme optimized for data visualization

## Support

For issues or questions, check the main README.md in the project root.
