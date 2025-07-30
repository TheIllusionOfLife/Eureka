# Web Interface Guide

## Overview

The MadSpark Web Interface provides a modern, user-friendly way to generate ideas with real-time progress tracking and interactive results display.

## Getting Started

### 1. Start the Web Interface

```bash
cd web
docker compose up
```

Services will start on:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### 2. First-Time Setup

Ensure your `.env` file contains:
```env
GOOGLE_API_KEY=your_api_key_here
GOOGLE_GENAI_MODEL=gemini-2.5-flash
```

## User Interface Overview

### Main Components

```
┌─────────────────────────────────────────┐
│          🧠 MadSpark                    │
│  AI-Powered Multi-Agent Idea System     │
├─────────────────────────────────────────┤
│                                         │
│  ┌──── Input Form ────┐  ┌─ Results ─┐ │
│  │                    │  │           │ │
│  │ Theme: [____]      │  │ Ideas     │ │
│  │ Constraints: [___] │  │ Display   │ │
│  │ [Advanced ▼]      │  │ Area      │ │
│  │                    │  │           │ │
│  │ [Generate Ideas]   │  │           │ │
│  └────────────────────┘  └───────────┘ │
│                                         │
│  [Progress Bar ████████████... 80%]     │
└─────────────────────────────────────────┘
```

## Features

### 1. Basic Idea Generation

1. **Enter Theme**: Type your main topic (required)
   - Example: "Sustainable transportation"

2. **Add Constraints**: Optional requirements
   - Example: "Under $10,000, works in cities"

3. **Select Options**:
   - Number of ideas (1-5)
   - Temperature preset or custom value

4. **Click Generate**: Watch real-time progress

### 2. Enhanced Features

Toggle advanced options:

- **Enhanced Reasoning**: Context-aware AI agents
- **Multi-Dimensional Evaluation**: 7-factor analysis
- **Logical Inference**: Formal reasoning chains
- **Novelty Filter**: Remove duplicate ideas

### 3. Real-Time Progress

Watch as your ideas are generated:
```
🚀 Generating Ideas
████████████████░░░░ 80%
Running complete feedback loop for 3 candidates...
```

Status updates include:
- Current agent (Idea Generator, Critic, Advocate, Skeptic)
- Processing stage
- Completion percentage

### 4. Results Display

#### Compact View (Default)
Shows improved ideas with:
- Enhanced idea text
- Score comparison (original → improved)
- Multi-dimensional radar chart
- Quick actions (Copy, Export, Bookmark)

#### Detailed View
Toggle "Show Detailed Results" to see:
- Original idea
- Complete critiques
- Advocacy points
- Skeptical analysis
- Score improvements

### 5. Interactive Elements

#### Expandable Sections
Click arrows to expand/collapse:
- Individual idea details
- Multi-dimensional evaluations
- Agent outputs

#### Score Visualization
- **Progress Bars**: Visual score representation
- **Delta Indicators**: ↑ +1.5 (green), ↓ -0.3 (red)
- **Radar Charts**: 7-dimension analysis

#### Action Buttons
- **Copy**: Copy idea to clipboard
- **Export**: Download in various formats
- **Bookmark**: Save for later remix
- **Share**: Generate shareable link

## Advanced Usage

### 1. Keyboard Shortcuts

- `?`: Show keyboard shortcuts help
- `Ctrl/Cmd + Enter`: Generate ideas (submit form)
- `Ctrl/Cmd + G`: Focus on idea generation form
- `Escape`: Close dialogs
- `Tab`: Navigate between fields

### 2. URL Parameters

Direct link to pre-filled form:
```
http://localhost:3000?theme=AI+healthcare&constraints=Privacy+focused
```

Supported parameters:
- `theme`: Main topic
- `constraints`: Requirements
- `temp`: Temperature (0.1-2.0)
- `candidates`: Number of ideas (1-5)

### 3. Export Options

Click export button to download as:
- **JSON**: Complete data with all fields
- **CSV**: Tabular format for spreadsheets
- **Markdown**: Formatted text document
- **PDF**: Professional report format

### 4. WebSocket Connection

Real-time updates via WebSocket:
- Auto-reconnect on disconnect
- Progress events every 2-3 seconds
- Error handling with retry

## Tips & Best Practices

### 1. Optimal Settings

**For Practical Ideas**:
- Temperature: Conservative (0.3-0.5)
- Features: Enhanced reasoning ON
- Candidates: 2-3

**For Innovation**:
- Temperature: Creative (0.9-1.2)
- Features: All ON
- Candidates: 4-5

### 2. Performance Tips

- Start with fewer candidates
- Use specific constraints
- Enable caching for repeated themes
- Close other browser tabs

### 3. Mobile Usage

The interface is responsive:
- Touch-friendly buttons
- Collapsible sections
- Swipe to navigate results
- Pinch to zoom charts

## Troubleshooting

### Connection Issues

**"WebSocket connection failed"**
- Check backend is running: `docker ps`
- Verify URL: `http://localhost:8000/api/health`
- Check browser console for errors

### Slow Generation

**Taking too long?**
- Reduce number of candidates
- Check API key is valid
- Monitor backend logs: `docker logs web-backend-1`

### Display Problems

**Charts not showing?**
- Enable JavaScript
- Try different browser
- Clear cache: `Ctrl+Shift+R`

## Integration Examples

### 1. Embed in Website

```html
<iframe 
  src="http://localhost:3000?theme=Your+Topic" 
  width="100%" 
  height="800px">
</iframe>
```

### 2. API Direct Access

```javascript
// Direct API call
fetch('http://localhost:8000/api/generate-ideas', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    theme: 'AI healthcare',
    constraints: 'Privacy-focused',
    num_candidates: 2
  })
})
```

### 3. WebSocket Monitoring

```javascript
// Connect to progress updates
const ws = new WebSocket('ws://localhost:8000/ws/progress');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`Progress: ${data.progress * 100}%`);
};
```

## Security Notes

- API keys are never sent to frontend
- All data is processed server-side
- WebSocket connections are isolated
- CORS configured for localhost only

## Customization

### Theme Variables

Edit `frontend/src/index.css`:
```css
:root {
  --primary-color: #2563eb;
  --background: #0f172a;
  --text-primary: #f8fafc;
}
```

### Layout Modifications

Components in `frontend/src/components/`:
- `InputForm.tsx`: Modify form fields
- `ResultsDisplay.tsx`: Change result layout
- `ProgressTracker.tsx`: Customize progress display