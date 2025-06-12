# Supabase Auth Setup Guide

## Environment Variables Configuration

Create a `.env` file in the root directory with the following variables:

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key  # Optional, only if needed

# Application Configuration
APP_SECRET_KEY=your-very-secret-key-for-jwt  # Generate a strong random key
APP_ENV=development  # Change to 'production' for production

# JWT Configuration (optional, defaults are set)
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440  # 24 hours
```

## Getting Supabase Credentials

1. Go to your Supabase project dashboard
2. Navigate to Settings > API
3. Copy your Project URL (this is your `SUPABASE_URL`)
4. Copy your `anon` public key (this is your `SUPABASE_ANON_KEY`)
5. Optionally, copy your `service_role` key if needed (this is your `SUPABASE_SERVICE_KEY`)

## Generating APP_SECRET_KEY

Generate a secure secret key for JWT signing:

```bash
# Using Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Or using OpenSSL
openssl rand -base64 32
```

## Supabase Auth Configuration

Make sure your Supabase project has the following settings:

1. **Email Auth**: Enable email/password authentication in Authentication > Providers
2. **Email Confirmation**: Configure whether email confirmation is required
3. **JWT Secret**: Note your JWT secret for production token verification

## Testing the Integration

1. Create a test user in Supabase Dashboard or via the app
2. Try logging in with the test credentials
3. Check browser developer tools for auth cookies:
   - `access_token`: Supabase JWT access token
   - `refresh_token`: Supabase refresh token

## Troubleshooting

### Common Issues:

1. **"Invalid API key"**: Check that your `SUPABASE_ANON_KEY` is correct
2. **"Network error"**: Verify `SUPABASE_URL` is correct and accessible
3. **"User already exists"**: The email is already registered in Supabase
4. **Cookies not setting**: Check if you're using HTTPS in production

### Debug Mode

Enable debug logging to see detailed auth flow:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Security Considerations

1. Never commit `.env` file to version control
2. Use different Supabase projects for development and production
3. Enable Row Level Security (RLS) on all tables
4. Use secure cookies in production (`secure=True`)
5. Implement proper CORS settings for your domain

## Next Steps

1. Configure email templates in Supabase for confirmation emails
2. Implement password reset flow
3. Add social auth providers (Google, GitHub, etc.)
4. Set up webhook for user events
5. Implement proper session management and token refresh 