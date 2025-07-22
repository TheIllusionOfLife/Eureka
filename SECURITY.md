# Security Guidelines for MadSpark Multi-Agent System

## 🔐 API Key Management

### CRITICAL SECURITY NOTICE
**Never commit real API keys to the repository!**

### Secure Configuration Setup

1. **Local Development:**
   ```bash
   # Copy example environment file
   cp web/.env.example web/.env
   
   # Edit with your real API key
   GOOGLE_API_KEY=your-real-api-key-here
   ```

2. **Production Deployment:**
   - Use environment variables or secret management systems
   - Consider AWS Secrets Manager, HashiCorp Vault, or similar
   - Never store secrets in plain text files

3. **CI/CD Environments:**
   - Use GitHub Secrets or equivalent
   - Mock mode is enabled automatically for CI

### Environment Security Checklist

- [ ] `.env` files are in `.gitignore`
- [ ] No hardcoded secrets in source code
- [ ] Production uses secure secret management
- [ ] API keys have appropriate scope restrictions
- [ ] Regular API key rotation implemented

## 🛡️ General Security Best Practices

### Authentication
- Implement JWT-based authentication for production use
- Use strong session management with secure random IDs
- Add rate limiting per authenticated user

### Input Validation
- All user inputs are validated using Pydantic models
- HTML sanitization prevents XSS attacks
- File path validation prevents traversal attacks

### API Security
- CORS properly configured for allowed origins
- Rate limiting implemented on all endpoints
- Structured error responses without sensitive information exposure

### WebSocket Security
- Consider authentication for WebSocket connections in production
- Implement connection limits to prevent abuse

## 🚨 Incident Response

If you suspect a security issue:
1. Do not commit any fixes to public repositories
2. Report to security team immediately
3. Rotate any potentially compromised credentials
4. Review access logs for unauthorized usage

## 📞 Security Contact

For security-related issues, please contact the development team privately.

---
**Last Updated**: 2025-07-22
**Review**: Required before production deployment