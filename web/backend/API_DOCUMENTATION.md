# MadSpark API Documentation

## Overview

The MadSpark API provides programmatic access to the multi-agent idea generation system. This document describes how to access and use the API documentation.

## Interactive Documentation

FastAPI automatically generates interactive API documentation using the OpenAPI (Swagger) standard. You can access it in two formats:

### 1. Swagger UI
- **URL**: http://localhost:8000/docs
- **Features**:
  - Interactive API explorer
  - Try out endpoints directly from the browser
  - View request/response schemas
  - Test with different parameters

### 2. ReDoc
- **URL**: http://localhost:8000/redoc
- **Features**:
  - Clean, readable documentation
  - Better for printing/PDF export
  - Detailed schema descriptions
  - Search functionality

### 3. OpenAPI JSON Schema
- **URL**: http://localhost:8000/openapi.json
- **Use Cases**:
  - Generate client SDKs
  - Import into API testing tools (Postman, Insomnia)
  - API contract validation
  - Custom documentation generation

## Key Endpoints

### Idea Generation
- **POST** `/api/generate-ideas` - Generate creative ideas using the multi-agent system
- **POST** `/api/generate-ideas-async` - Async version with WebSocket progress updates

### Bookmarks
- **GET** `/api/bookmarks` - List all saved bookmarks
- **POST** `/api/bookmarks` - Create a new bookmark
- **DELETE** `/api/bookmarks/{bookmark_id}` - Delete a bookmark
- **POST** `/api/bookmarks/check-duplicates` - Check for duplicate ideas
- **GET** `/api/bookmarks/similar` - Find similar bookmarks

### Configuration
- **GET** `/api/temperature-presets` - Get available creativity presets

### System
- **GET** `/health` - Health check endpoint
- **WebSocket** `/ws/progress` - Real-time progress updates

## Rate Limits

- Idea generation: 5 requests per minute
- Bookmark operations: 15 requests per minute
- Other endpoints: 60 requests per minute

## Authentication

Currently, the API does not require authentication. This may change in future versions.

## Examples

### Generate Ideas
```bash
curl -X POST "http://localhost:8000/api/generate-ideas" \
  -H "Content-Type: application/json" \
  -d '{
    "theme": "sustainable urban transportation",
    "constraints": "budget-friendly, implementable within 2 years",
    "num_top_candidates": 3,
    "temperature_preset": "creative"
  }'
```

### Check for Duplicates
```bash
curl -X POST "http://localhost:8000/api/bookmarks/check-duplicates" \
  -H "Content-Type: application/json" \
  -d '{
    "idea": "Create a network of electric vehicle charging stations",
    "theme": "sustainable transportation"
  }'
```

## Error Handling

All endpoints return consistent error responses:
```json
{
  "detail": "Error description",
  "status": "error",
  "timestamp": "2024-01-15T10:30:45Z"
}
```

Common HTTP status codes:
- `200` - Success
- `422` - Validation error
- `429` - Rate limit exceeded
- `500` - Internal server error

## WebSocket Usage

Connect to the WebSocket endpoint for real-time progress updates:

```javascript
const ws = new WebSocket('ws://localhost:8000/ws/progress');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`Progress: ${data.progress}% - ${data.message}`);
};
```

## Development Tips

1. Use the Swagger UI to explore and test endpoints
2. Check the schemas section for detailed request/response formats
3. Use the "Try it out" feature to test endpoints with real data
4. Export the OpenAPI spec to generate client libraries
5. Monitor rate limits to avoid 429 errors

## Testing the Documentation

Run the test script to verify documentation is working:
```bash
cd web/backend
python test_openapi.py
```