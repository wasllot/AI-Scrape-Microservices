# API Usage Guide

## Overview
This guide explains how to interact with the Microservices ecosystem, specifically the AI Chatbot and Scraper services.

## Base URLs
- **Local Development**: `http://localhost/app/api` (via Traefik) or `http://localhost:9000/api` (Direct)
- **Production**: `https://api.yourdomain.com/app/api`
- **Swagger UI**: `http://localhost:9000/api/documentation`

---

## 🤖 AI Chatbot (RAG)

The chatbot uses your CV and Profile Data to answer questions contextually.

### Endpoint
`POST /chat`

### Request Format
**Headers**:
- `Content-Type: application/json`
- `Accept: application/json`

**Body**:
```json
{
  "question": "Your question here",
  "conversation_id": "optional-uuid-for-history", 
  "max_context_items": 5
}
```

### Examples

#### cURL
```bash
curl -X POST http://localhost:9000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question":"What is your experience with Docker?"}'
```

#### JavaScript (Fetch)
```javascript
const response = await fetch('http://localhost/app/api/chat', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    question: "Tell me about your soft skills",
    conversation_id: localStorage.getItem('chat_id')
  })
});
const data = await response.json();
console.log(data.answer);
```

#### Python
```python
import requests

response = requests.post(
    "http://localhost:9000/api/chat",
    json={"question": "Philosophy on Microservices?"}
)
print(response.json()['answer'])
```

---

## 🕷️ Web Scraper

Extracts content from web pages using Playwright (headless browser).

### Endpoint
`POST /scrape/learn`

### Request Format
**Body**:
```json
{
  "url": "https://example.com/article",
  "formats": ["markdown", "json"]
}
```

### Response
```json
{
  "url": "https://example.com/article",
  "title": "Article Title",
  "content": "# Article Title\n\nContent...",
  "metadata": {...}
}
```

---

## 🩺 Health Checks

Use these to verify system status before making requests.

- **System Status**: `GET /system-status` - Checks DB, Redis, and all microservices.
- **AI Service**: `GET /ai/health`
- **Scraper**: `GET /scraper/health`
