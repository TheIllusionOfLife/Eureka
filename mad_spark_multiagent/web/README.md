# MadSpark Web Interface - Phase 2.2

This directory contains the web interface for the MadSpark Multi-Agent System, featuring a React frontend and FastAPI backend.

## 🚀 Quick Start

### Prerequisites
- Python 3.10+ (for backend)
- Node.js 16+ (for frontend)
- MadSpark system dependencies (see main README.md)

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables:**
   ```bash
   # Copy from main project
   cp ../../.env.example .env
   # Edit .env to add your GOOGLE_API_KEY and GOOGLE_GENAI_MODEL
   ```

4. **Run the FastAPI server:**
   ```bash
   python main.py
   ```
   
   The API will be available at http://localhost:8000
   - API documentation: http://localhost:8000/docs
   - Health check: http://localhost:8000/api/health

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm start
   ```
   
   The web interface will be available at http://localhost:3000

## 🏗️ Architecture

### Backend (FastAPI)
- **FastAPI**: Modern Python web framework with automatic API documentation
- **WebSockets**: Real-time progress updates during idea generation
- **CORS**: Configured for local development with React
- **Integration**: Direct imports from MadSpark coordinator and components

### Frontend (React + TypeScript)
- **React 18**: Modern React with hooks and concurrent features
- **TypeScript**: Type safety for better development experience
- **Tailwind CSS**: Utility-first CSS framework for styling
- **Recharts**: Data visualization for multi-dimensional evaluation (future)
- **Axios**: HTTP client for API communication

### Key Features
- ✅ **Real-time idea generation** with WebSocket progress updates
- ✅ **All Phase 2.1 features** including enhanced reasoning, multi-dimensional evaluation, logical inference
- ✅ **Temperature control** with presets and custom values
- ✅ **Novelty filtering** with adjustable thresholds
- ✅ **Responsive design** that works on desktop and mobile
- ✅ **Expandable results** with detailed critique, advocacy, and skepticism
- 🔄 **Bookmark management** (in development)
- 🔄 **Export functionality** (in development)

## 📁 Project Structure

```
web/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── requirements.txt     # Python dependencies
│   └── README.md           # Backend-specific docs
├── frontend/
│   ├── public/
│   │   └── index.html      # HTML template
│   ├── src/
│   │   ├── components/     # React components
│   │   │   ├── IdeaGenerationForm.tsx
│   │   │   ├── ResultsDisplay.tsx
│   │   │   └── ProgressIndicator.tsx
│   │   ├── App.tsx         # Main application component
│   │   ├── App.css         # Custom styles
│   │   ├── index.tsx       # React entry point
│   │   └── index.css       # Global styles with Tailwind
│   ├── package.json        # Node.js dependencies
│   ├── tsconfig.json       # TypeScript configuration
│   └── tailwind.config.js  # Tailwind CSS configuration
└── README.md              # This file
```

## 🧪 Testing

### Backend Testing
```bash
cd backend
# Test API health
curl http://localhost:8000/api/health

# Test idea generation (requires API key)
curl -X POST http://localhost:8000/api/generate-ideas \
  -H "Content-Type: application/json" \
  -d '{"theme": "Test theme", "constraints": "Test constraints"}'
```

### Frontend Testing
```bash
cd frontend
npm test
```

## 🔧 Development

### Adding New Features

1. **Backend**: Add new endpoints in `main.py` and update Pydantic models
2. **Frontend**: Create new components in `src/components/` and integrate with API

### Environment Variables
The backend requires the same environment variables as the main MadSpark system:
- `GOOGLE_API_KEY`: Google Gemini API key
- `GOOGLE_GENAI_MODEL`: Model name (e.g., "gemini-pro")

### Hot Reloading
Both backend and frontend support hot reloading:
- Backend: Uvicorn automatically reloads on file changes
- Frontend: React development server automatically reloads on file changes

## 🚢 Deployment

### Development
- Backend: `python main.py` (runs on port 8000)
- Frontend: `npm start` (runs on port 3000)

### Production (Future)
- Backend: Use production WSGI server like Gunicorn
- Frontend: Build with `npm run build` and serve static files
- Docker: Use provided Dockerfile for containerized deployment

## 📊 API Documentation

The FastAPI backend automatically generates interactive API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Key Endpoints

- `GET /` - API information and status
- `GET /api/health` - Health check with component status
- `GET /api/temperature-presets` - Available temperature presets
- `POST /api/generate-ideas` - Main idea generation endpoint
- `GET /api/bookmarks` - List bookmarks (future)
- `POST /api/bookmarks` - Create bookmark (future)
- `WebSocket /ws/progress` - Real-time progress updates

## 🔮 Roadmap

### Phase 2.2 Remaining Features
- [ ] Multi-dimensional evaluation visualization (radar charts)
- [ ] Bookmark management UI
- [ ] Export functionality (PDF, JSON, CSV)
- [ ] Interactive mode templates
- [ ] Result comparison tools

### Phase 2.3 Features
- [ ] User authentication and sessions
- [ ] Database persistence
- [ ] Performance monitoring
- [ ] Advanced analytics

## 🐛 Troubleshooting

### Common Issues

1. **CORS errors**: Ensure backend is running on port 8000 and frontend on port 3000
2. **WebSocket connection failed**: Check that backend WebSocket endpoint is accessible
3. **API key errors**: Verify GOOGLE_API_KEY is set in backend environment
4. **Import errors**: Ensure you're running from the correct directory with MadSpark modules accessible

### Debug Mode
Set `verbose: true` in the form to enable detailed logging in both frontend and backend.

## 🤝 Contributing

1. Follow the existing code style and patterns
2. Add TypeScript types for new API endpoints
3. Include error handling for all API calls
4. Test both frontend and backend functionality
5. Update documentation for new features

This web interface represents the evolution of MadSpark from a CLI-only tool to a user-friendly platform that makes advanced AI capabilities accessible to all users.