# Chat API Documentation

## Overview
The Chat API provides endpoints for conversational AI functionality, including intent detection, conversation management, and real-time messaging.

## Base URL
```
http://localhost:8000/api/v1/chat
```

## Authentication
Currently no authentication is required, but user_id should be provided for conversation tracking.

---

## REST API Endpoints

### 1. Start Conversation
**POST** `/conversations`

Start a new conversation or return existing active conversation for user.

**Request Body:**
```json
{
  "user_id": "optional-user-id",
  "initial_message": "Optional initial message",
  "channel": "web",
  "metadata": {}
}
```

**Response:**
```json
{
  "id": "conversation-uuid",
  "user_id": "user-id",
  "status": "active",
  "current_step": "greeting",
  "context": {},
  "message_count": 0,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": null,
  "completed_at": null,
  "duration_minutes": null
}
```

### 2. Send Message
**POST** `/conversations/{conversation_id}/messages`

Send a message to the conversation and receive AI response.

**Request Body:**
```json
{
  "content": "I want to schedule an appointment",
  "user_id": "user-id",
  "metadata": {}
}
```

**Response:**
```json
{
  "message": "AI response message",
  "conversation_id": "conversation-uuid",
  "intent": "AGENDAR_CITA",
  "confidence": 0.95,
  "context": {
    "service_selected": null,
    "date_preference": null
  },
  "step": "service_selection",
  "timestamp": "2024-01-01T00:00:00Z",
  "suggestions": ["Option 1", "Option 2"]
}
```

### 3. Get Conversation
**GET** `/conversations/{conversation_id}`

Retrieve conversation details by ID.

**Response:** Same as Start Conversation response

### 4. Get User Conversations
**GET** `/users/{user_id}/conversations?skip=0&limit=50`

Get paginated list of conversations for a user.

**Response:**
```json
{
  "conversations": [/* array of conversation objects */],
  "total": 10,
  "skip": 0,
  "limit": 50
}
```

### 5. End Conversation
**POST** `/conversations/{conversation_id}/end`

End an active conversation.

**Response:** Updated conversation object with status "completed"

### 6. Escalate Conversation
**POST** `/conversations/{conversation_id}/escalate`

Escalate conversation to human agent.

**Request Body:**
```json
{
  "reason": "User needs complex assistance",
  "priority": "normal",
  "contact_info": "user@example.com"
}
```

### 7. Get Conversation Messages
**GET** `/conversations/{conversation_id}/messages?limit=50`

Get messages for a conversation.

**Response:** Array of message objects

### 8. Get Conversation Analytics
**GET** `/analytics/conversations?start_date=2024-01-01T00:00:00&end_date=2024-01-31T23:59:59`

Get conversation analytics for date range.

**Response:**
```json
{
  "period": {
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-01-31T23:59:59Z"
  },
  "total_conversations": 100,
  "by_status": {
    "active": {"count": 10},
    "completed": {"count": 80},
    "abandoned": {"count": 10}
  },
  "generated_at": "2024-01-01T12:00:00Z"
}
```

### 9. Search Conversations
**POST** `/conversations/search`

Search conversations with filters.

**Request Body:**
```json
{
  "query": "appointment",
  "user_id": "optional-user-id",
  "status": "active",
  "date_from": "2024-01-01T00:00:00Z",
  "date_to": "2024-01-31T23:59:59Z",
  "intent": "AGENDAR_CITA",
  "skip": 0,
  "limit": 50
}
```

### 10. Get Conversation Context
**GET** `/conversations/{conversation_id}/context`

Get current conversation context and step.

**Response:**
```json
{
  "conversation_id": "conversation-uuid",
  "context": {
    "service_selected": "consultation",
    "date_preference": "morning"
  },
  "step": "appointment_scheduling",
  "status": "active"
}
```

### 11. Get Quick Replies
**GET** `/conversations/{conversation_id}/quick-replies`

Get suggested quick reply options based on current conversation step.

**Response:**
```json
[
  {
    "text": "Schedule Appointment",
    "value": "agendar",
    "action": "select"
  },
  {
    "text": "View My Appointments",
    "value": "consultar",
    "action": "navigate"
  }
]
```

### 12. Admin Cleanup
**POST** `/admin/cleanup`

Clean up abandoned conversations (admin endpoint).

**Response:**
```json
{
  "message": "Cleaned up 5 abandoned conversations",
  "count": 5,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 13. Health Check
**GET** `/health`

Check chat service health.

**Response:**
```json
{
  "status": "healthy",
  "service": "chat",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

---

## WebSocket API

### Real-time Chat
**WS** `/ws/chat/{user_id}`

Real-time chat communication via WebSocket.

**Connection:** 
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/chat/user-123');
```

**Message Types:**

#### 1. Connection Established
```json
{
  "type": "connection_established",
  "conversation_id": "conversation-uuid",
  "message": "¡Hola! ¿En qué puedo ayudarte hoy?"
}
```

#### 2. Chat Message (Send)
```json
{
  "type": "chat_message",
  "content": "I want to book an appointment",
  "metadata": {}
}
```

#### 3. AI Response (Receive)
```json
{
  "type": "ai_response",
  "conversation_id": "conversation-uuid",
  "message": "AI response",
  "intent": "AGENDAR_CITA",
  "confidence": 0.95,
  "context": {},
  "step": "service_selection",
  "timestamp": "2024-01-01T00:00:00Z",
  "suggestions": []
}
```

#### 4. Quick Replies (Receive)
```json
{
  "type": "quick_replies",
  "conversation_id": "conversation-uuid",
  "replies": [
    {
      "text": "Medical Consultation",
      "value": "consulta_medica",
      "action": "select"
    }
  ]
}
```

#### 5. Quick Reply Selection (Send)
```json
{
  "type": "quick_reply",
  "text": "Medical Consultation",
  "value": "consulta_medica"
}
```

#### 6. Typing Indicator (Send)
```json
{
  "type": "typing_indicator",
  "is_typing": true
}
```

#### 7. Error Message (Receive)
```json
{
  "type": "error",
  "message": "Error processing message"
}
```

---

## Conversation Flow Steps

1. **greeting** - Initial greeting and option selection
2. **service_selection** - Choose service type
3. **professional_selection** - Choose professional (optional)
4. **date_time_selection** - Select date and time
5. **appointment_scheduling** - Confirm appointment details
6. **confirmation** - Final confirmation and completion

## Intent Types

- `AGENDAR_CITA` - Schedule appointment
- `CONSULTAR_CITA` - Check existing appointments
- `CANCELAR_CITA` - Cancel appointment
- `REPROGRAMAR_CITA` - Reschedule appointment
- `SALUDO` - Greeting
- `DESPEDIDA` - Goodbye
- `AYUDA` - Help request
- `OTRO` - Other/Unknown

## Error Handling

All endpoints return appropriate HTTP status codes:
- `200` - Success
- `400` - Bad Request (validation errors)
- `404` - Not Found
- `500` - Internal Server Error

Error response format:
```json
{
  "detail": "Error message description"
}
```