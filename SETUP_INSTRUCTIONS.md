# Setup Instructions for AI Generate Flashcards

## Quick Start

### 1. Install Dependencies
```bash
pip install openai>=1.12.0
# or if using requirements.txt:
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Add to your `.env` file:
```env
# Existing variables
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key

# New required variable for AI functionality
OPENROUTER_API_KEY=sk-or-your-api-key-here
```

**How to get OpenRouter API Key:**
1. Visit [OpenRouter.ai](https://openrouter.ai)
2. Sign up for an account
3. Go to API Keys section
4. Create a new API key
5. Add credits to your account (minimum $5 recommended)

### 3. Verify Installation
```bash
# Test that all modules import correctly
python -c "from src.services.llm_client import LLMClient; from src.services.ai_service import AIService; print('✅ AI services imported successfully')"

# Test configuration loading
python -c "from src.core.config import Settings; s = Settings(); print(f'✅ Config loaded, LLM Model: {s.LLM_MODEL}')"
```

### 4. Start the Application
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Test the Endpoint

**Check API Documentation:**
- Visit: http://localhost:8000/docs
- Look for the `/ai/generate-flashcards` endpoint under "ai" tag

**Test with cURL:**
```bash
curl -X POST "http://localhost:8000/api/v1/ai/generate-flashcards" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "text_content": "Photosynthesis is the process by which plants and some bacteria convert light energy into chemical energy. This process involves the absorption of light by chlorophyll, the conversion of carbon dioxide and water into glucose, and the release of oxygen as a byproduct. The overall equation for photosynthesis is: 6CO2 + 6H2O + light energy → C6H12O6 + 6O2. This process is essential for life on Earth as it provides oxygen for respiration and forms the base of most food chains. Photosynthesis occurs in two main stages: the light-dependent reactions that occur in the thylakoids, and the light-independent reactions (Calvin cycle) that occur in the stroma of chloroplasts."
  }'
```

## Configuration Options

### LLM Model Settings (in src/core/config.py)
```python
LLM_MODEL = "google/gemma-3-27b-it"  # Current model
LLM_TIMEOUT = 30                     # Request timeout in seconds
LLM_MAX_TOKENS = 2000               # Maximum tokens in response
```

### Available Models on OpenRouter
You can change the model by updating `LLM_MODEL` in config:
- `google/gemma-3-27b-it` (Current, $0.10/$0.20 per M tokens)
- `google/gemma-2-27b-it` (Older version, $0.80/$0.80 per M tokens)
- `anthropic/claude-3-haiku` (Fast, $0.25/$1.25 per M tokens)
- `openai/gpt-4o-mini` (Affordable, $0.15/$0.60 per M tokens)

### Rate Limiting Settings
Current limits (can be adjusted in ai_router.py):
- **10 requests per 60 minutes** per authenticated user
- More restrictive than regular flashcard operations due to AI costs

## Troubleshooting

### Common Issues

**1. Missing OpenRouter API Key**
```
ValidationError: Field required [type=missing] OPENROUTER_API_KEY
```
**Solution:** Add `OPENROUTER_API_KEY=sk-or-...` to your `.env` file

**2. Invalid API Key**
```
HTTP 401: Invalid API key
```
**Solution:** Check your OpenRouter dashboard, ensure key is active and has credits

**3. Rate Limit Exceeded**
```
HTTP 429: Rate limit exceeded
```
**Solution:** Wait for the rate limit window to reset (60 minutes)

**4. Text Too Short/Long**
```
HTTP 422: String should have at least 1000 characters
```
**Solution:** Ensure text is between 1000-10000 characters

**5. AI Service Unavailable**
```
HTTP 503: AI service is temporarily unavailable
```
**Solution:** OpenRouter service may be down, try again later

### Debugging Steps

**1. Check Logs**
```bash
# Application logs show detailed error information
tail -f logs/app.log  # if you have file logging configured
```

**2. Test LLM Client Directly**
```python
import asyncio
from src.services.llm_client import LLMClient

async def test_llm():
    async with LLMClient() as client:
        response = await client.generate_flashcards("Your test text here...")
        print(f"Generated {len(response.flashcards)} flashcards")

asyncio.run(test_llm())
```

**3. Check Database Connectivity**
```python
from src.db.supabase_client import get_supabase_client
client = get_supabase_client()
print("✅ Supabase client created successfully")
```

### Performance Monitoring

**Response Time Expectations:**
- **Typical**: 3-8 seconds for 2000-5000 character text
- **Large texts**: 8-15 seconds for 8000-10000 character text
- **Timeout**: 30 seconds maximum

**Cost Estimates (Gemma 3 27B):**
- **Small text** (1000 chars): ~$0.001-0.002
- **Medium text** (5000 chars): ~$0.003-0.005  
- **Large text** (10000 chars): ~$0.005-0.010

### Scaling Considerations

**For Production:**
1. **Increase rate limits** based on user tier/subscription
2. **Add caching** for similar text inputs
3. **Implement queuing** for high-volume usage
4. **Monitor costs** and set alerts
5. **Add retry logic** for transient failures

## Security Notes

- API keys are never logged or exposed in responses
- All requests require valid JWT authentication
- Rate limiting prevents abuse
- Input validation prevents injection attacks
- Security headers protect against common attacks
- Structured logging enables security monitoring 