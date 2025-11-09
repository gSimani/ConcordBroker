# Security Guide for ConcordBroker

## Overview
This guide documents security best practices and configurations for the ConcordBroker project.

## Environment Variables Security

### ✅ Current Security Status
- **All .env files are excluded from Git** ✓
- **Secure templates provided** ✓
- **Environment validation tools implemented** ✓
- **Vercel secrets properly configured** ✓

### 🔐 Security Tools Available

1. **Environment Validator** (`mcp-server/validate-env.js`)
   ```bash
   cd mcp-server
   node validate-env.js
   ```
   - Checks all .env files for security issues
   - Detects exposed tokens and weak passwords
   - Validates Git exclusion status

2. **Security Helper** (`mcp-server/secure-env.js`)
   ```bash
   cd mcp-server
   node secure-env.js
   ```
   - Generate secure tokens and passwords
   - Create secure .env files from templates
   - Rotate secrets in Vercel

### 🚨 Critical Security Rules

1. **NEVER commit .env files to Git**
   - All .env files are in .gitignore
   - Use .env.example files for templates only

2. **Use strong, unique secrets**
   - Minimum 32 characters for tokens
   - 64 characters for JWT secrets
   - Use the security helper to generate them

3. **Rotate secrets regularly**
   - Every 90 days for production
   - Immediately if compromised
   - Use the rotation script provided

## API Keys and Tokens

### Current Services Configured

| Service | Environment Variable | Security Level | Rotation Schedule |
|---------|---------------------|----------------|-------------------|
| Vercel | VERCEL_API_TOKEN | HIGH | 90 days |
| Supabase | SUPABASE_SERVICE_KEY | CRITICAL | 60 days |
| Railway | RAILWAY_TOKEN | HIGH | 90 days |
| JWT | JWT_SECRET | CRITICAL | 30 days |

### Token Security Checklist

- [x] All tokens use high entropy (>4.5 Shannon entropy)
- [x] No hardcoded values in source code
- [x] Different tokens for each environment
- [x] Tokens stored in secure vaults (Vercel/Railway)
- [x] Access logs monitored

## Production Security Configurations

### Vercel Environment Variables
All sensitive data is stored in Vercel's encrypted environment variables:
- Dashboard: https://vercel.com/westbocaexecs-projects/concord-broker/settings/environment-variables
- Encrypted at rest
- Accessible only via Vercel API with authentication

### Railway Backend Security
- HTTPS only for production
- Environment variables encrypted
- Automatic SSL certificates
- DDoS protection enabled

### Supabase Security
- Row Level Security (RLS) enabled
- JWT verification on all requests
- SSL enforced connections
- Service key restricted to backend only

## Security Headers

The following headers are configured in production:

```javascript
// vercel.json
{
  "headers": [
    {
      "source": "/(.*)",
      "headers": [
        { "key": "X-Content-Type-Options", "value": "nosniff" },
        { "key": "X-Frame-Options", "value": "DENY" },
        { "key": "X-XSS-Protection", "value": "1; mode=block" },
        { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" }
      ]
    }
  ]
}
```

## CORS Configuration

Properly configured CORS for API access:
- Production: https://www.concordbroker.com
- Development: http://localhost:5173
- No wildcard (*) in production

## Data Protection

### Database Security
- Encrypted connections (SSL/TLS)
- Parameterized queries (no SQL injection)
- Input validation on all endpoints
- Rate limiting implemented

### User Data
- Passwords hashed with bcrypt (cost factor 12)
- Sessions expire after 7 days
- Secure cookie flags enabled
- HTTPS only in production

## Monitoring & Alerts

### Security Monitoring Tools
1. **Vercel Analytics** - Monitor traffic patterns
2. **Railway Metrics** - Track API usage
3. **Supabase Dashboard** - Database access logs

### Alert Triggers
- Failed authentication attempts > 5
- Unusual traffic patterns
- Database connection failures
- API rate limit exceeded

## Incident Response Plan

### If a Secret is Exposed:
1. **Immediately rotate the affected secret**
   ```bash
   cd mcp-server
   node secure-env.js
   # Select option 4: Rotate secrets
   ```

2. **Update in all services:**
   - Vercel Dashboard
   - Railway Environment
   - Local .env files

3. **Audit access logs:**
   - Check Vercel deployment logs
   - Review Supabase authentication logs
   - Examine Railway request logs

4. **Notify team:**
   - Document the incident
   - Update security protocols
   - Schedule post-mortem

## Security Maintenance Schedule

### Daily
- Monitor error logs
- Check deployment status

### Weekly
- Review access logs
- Update dependencies (`npm audit`)

### Monthly
- Full security audit
- Update security documentation
- Test incident response

### Quarterly
- Rotate all secrets
- Security training update
- Penetration testing (if applicable)

## Quick Security Commands

```bash
# Check all environment files
cd mcp-server && node validate-env.js

# Generate new secure tokens
cd mcp-server && node secure-env.js

# Check for vulnerable dependencies
npm audit

# Fix vulnerabilities automatically
npm audit fix

# Check if any secrets are in Git
git secrets --scan

# View Vercel environment variables
vercel env ls
```

## Security Contacts

- **Security Issues**: security@concordbroker.com
- **Vercel Support**: https://vercel.com/support
- **Railway Support**: https://railway.app/support
- **Supabase Support**: https://supabase.com/support

## Compliance

### GDPR Considerations
- User data deletion endpoints implemented
- Data export functionality available
- Privacy policy updated
- Cookie consent implemented

### Security Standards
- OWASP Top 10 addressed
- SSL/TLS enforced
- Regular security updates
- Dependency scanning enabled

---

**Last Security Audit**: September 5, 2025
**Next Scheduled Audit**: December 5, 2025
**Security Officer**: ConcordBroker Team

⚠️ **Remember**: Security is everyone's responsibility. If you notice anything suspicious, report it immediately.