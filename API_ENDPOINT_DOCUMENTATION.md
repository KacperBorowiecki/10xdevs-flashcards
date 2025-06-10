# AI Generate Flashcards Endpoint Documentation

## Endpoint: `POST /api/v1/ai/generate-flashcards`

### Overview
Generate educational flashcards from provided text using AI (Google Gemma 3 27B model via OpenRouter). The service creates source text records, generates flashcard suggestions with `pending_review` status, and tracks generation events for analytics.

### Authentication
- **Required**: Bearer JWT token in Authorization header
- **Format**: `Authorization: Bearer <supabase-jwt-token>`

### Request

#### URL
```
POST /api/v1/ai/generate-flashcards
```

#### Headers
```
Content-Type: application/json
Authorization: Bearer <your-jwt-token>
```

#### Request Body
```json
{
  "text_content": "Your educational text content here (1000-10000 characters)..."
}
```

#### Validation Rules
- `text_content`: Required string, 1000-10000 characters
- Text content cannot be empty or only whitespace

### Response

#### Success Response (200 OK)
```json
{
  "source_text_id": "550e8400-e29b-41d4-a716-446655440000",
  "ai_generation_event_id": "550e8400-e29b-41d4-a716-446655440001",
  "suggested_flashcards": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440002",
      "user_id": "550e8400-e29b-41d4-a716-446655440003",
      "source_text_id": "550e8400-e29b-41d4-a716-446655440000",
      "front_content": "What is the main concept explained in the text?",
      "back_content": "The main concept is...",
      "source": "ai_suggestion",
      "status": "pending_review",
      "created_at": "2024-01-01T12:00:00.000Z",
      "updated_at": "2024-01-01T12:00:00.000Z"
    }
  ]
}
```

#### Error Responses

**400 Bad Request**
```json
{
  "detail": "Text content cannot be empty"
}
```

**401 Unauthorized**
```json
{
  "detail": "Invalid authentication credentials"
}
```

**422 Unprocessable Entity**
```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "text_content"],
      "msg": "String should have at least 1000 characters",
      "input": "short text"
    }
  ]
}
```

**429 Too Many Requests**
```json
{
  "detail": "Rate limit exceeded. Maximum 10 requests per 60 minutes."
}
```

**503 Service Unavailable**
```json
{
  "detail": "AI service is temporarily unavailable. Please try again later."
}
```

**500 Internal Server Error**
```json
{
  "detail": "Internal server error occurred while generating flashcards"
}
```

### Rate Limiting
- **Limit**: 10 requests per 60 minutes per authenticated user
- **Headers**: Rate limit information returned in response headers

### Security Features
- JWT token validation via Supabase Auth
- Rate limiting to prevent abuse
- Input validation and sanitization
- Request integrity validation
- Security headers (X-Content-Type-Options, X-Frame-Options, etc.)
- Structured logging for monitoring

### Database Operations
The endpoint performs the following database operations:

1. **Creates source_text record**: Stores the original text content
2. **Generates flashcards**: Creates multiple flashcard records with status `pending_review`
3. **Creates ai_generation_event**: Tracks generation statistics and costs

### AI Model Configuration
- **Model**: Google Gemma 3 27B (`google/gemma-3-27b-it`)
- **Provider**: OpenRouter.ai
- **Context Window**: 131K tokens
- **Pricing**: $0.10/M input tokens, $0.20/M output tokens

### Example Usage

#### cURL
```bash
curl -X POST "http://localhost:8000/api/v1/ai/generate-flashcards" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-jwt-token" \
  -d '{
    "text_content": "Photosynthesis is the process by which plants convert sunlight, carbon dioxide, and water into glucose and oxygen. This process occurs in the chloroplasts of plant cells and is essential for life on Earth as it produces the oxygen we breathe and forms the base of most food chains. The process can be divided into two main stages: the light-dependent reactions and the Calvin cycle..."
  }'
```

#### JavaScript (fetch)
```javascript
const response = await fetch('/api/v1/ai/generate-flashcards', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    text_content: "Your educational text content here..."
  })
});

const data = await response.json();
console.log('Generated flashcards:', data.suggested_flashcards);
```

#### Python (requests)
```python
import requests

response = requests.post(
    'http://localhost:8000/api/v1/ai/generate-flashcards',
    headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    },
    json={
        'text_content': 'Your educational text content here...'
    }
)

data = response.json()
print(f"Generated {len(data['suggested_flashcards'])} flashcards")
```

### Environment Variables Required

Add to your `.env` file:
```env
OPENROUTER_API_KEY=sk-or-your-api-key-here
```

### Next Steps After Generation

After flashcards are generated with `pending_review` status, users can:

1. **Review suggestions**: Use existing flashcard endpoints to view generated cards
2. **Approve cards**: Update status from `pending_review` to `active` using PATCH `/api/v1/flashcards/{id}`
3. **Reject cards**: Update status to `rejected` 
4. **Edit content**: Modify front/back content before approval

### Monitoring and Analytics

The service tracks:
- Generation costs and token usage
- Success/failure rates
- Response times
- User patterns and usage statistics
- AI model performance metrics 