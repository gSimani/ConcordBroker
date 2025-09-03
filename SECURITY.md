# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

We take the security of ConcordBroker seriously. If you discover a security vulnerability, please follow these steps:

1. **DO NOT** create a public GitHub issue
2. Email the details to the project maintainer
3. Include:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

## Security Best Practices

### Secrets Management

- **NEVER** commit secrets to the repository
- Use environment variables for all sensitive data
- Rotate credentials regularly
- Use Railway/Vercel/Supabase secret stores

### API Security

- All endpoints require authentication (except /health)
- Implement rate limiting
- Use CORS allowlist for frontend domain
- Validate all input data
- Use parameterized queries to prevent SQL injection

### Database Security

- Enable Row Level Security (RLS) in Supabase
- Use service role keys only in backend
- Never expose database credentials
- Regular backups

### Authentication

- Use Twilio Verify for multi-factor authentication
- JWT tokens with short expiration
- Secure session management
- Password complexity requirements

### Data Protection

- Encrypt sensitive data at rest
- Use HTTPS for all communications
- PII data minimization
- GDPR compliance where applicable

### Monitoring

- Use Sentry for error tracking
- Monitor for suspicious activity
- Regular security audits
- Dependency vulnerability scanning

## Security Checklist

- [ ] Environment variables configured
- [ ] Secrets not in codebase
- [ ] RLS enabled in Supabase
- [ ] CORS configured correctly
- [ ] Authentication implemented
- [ ] Input validation in place
- [ ] SQL injection prevention
- [ ] HTTPS enforced
- [ ] Error tracking configured
- [ ] Dependencies up to date

## Response Timeline

We aim to:
- Acknowledge receipt within 48 hours
- Provide initial assessment within 1 week
- Release patches for critical issues ASAP
- Release patches for non-critical issues within 30 days

## Disclosure Policy

We follow responsible disclosure:
1. Reporter notifies us privately
2. We acknowledge and assess
3. We develop and test fix
4. We release patch
5. We publicly disclose with credit to reporter