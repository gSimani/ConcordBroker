# Secrets Management

## Overview

This directory contains templates and documentation for managing secrets in the ConcordBroker application. **NEVER commit actual secrets to the repository.**

## Important Security Rules

1. **NEVER** commit real credentials to Git
2. **ALWAYS** use environment variables for sensitive data
3. **ROTATE** credentials immediately if exposed
4. **USE** separate credentials for each environment (dev/staging/prod)
5. **ENABLE** audit logging for all secret access

## Setup Instructions

### Local Development

1. Copy the template file:
```bash
cp .template.env ../../.env
```

2. Fill in your actual values in the `.env` file

3. The `.env` file is gitignored and will not be committed

### Railway Deployment

1. Navigate to your Railway project dashboard
2. Select your service (API or Worker)
3. Go to the Variables tab
4. Add each environment variable from `.template.env`
5. Railway will automatically inject these into your application

#### Using Railway CLI:
```bash
railway variables set SUPABASE_URL="https://your-project.supabase.co"
railway variables set SUPABASE_SERVICE_ROLE_KEY="your-key"
# ... repeat for all variables
```

### Vercel Deployment

1. Navigate to your Vercel project dashboard
2. Go to Settings → Environment Variables
3. Add each variable for the appropriate environments:
   - Development
   - Preview
   - Production

#### Using Vercel CLI:
```bash
vercel env add NEXT_PUBLIC_API_URL
vercel env add NEXT_PUBLIC_SUPABASE_URL
# ... repeat for public variables
```

### Supabase Configuration

1. Get your project URL and keys from:
   - Dashboard → Settings → API
   - Copy:
     - Project URL → `SUPABASE_URL`
     - anon/public key → `SUPABASE_ANON_KEY`
     - service_role key → `SUPABASE_SERVICE_ROLE_KEY`
     - JWT Secret → `SUPABASE_JWT_SECRET`

## Environment Variables by Service

### Frontend (Vercel)
- `NEXT_PUBLIC_API_URL`
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `NEXT_PUBLIC_SENTRY_DSN`

### API (Railway)
- All variables from `.template.env`

### Workers (Railway)
- Database credentials
- FTP/SFTP credentials
- Sentry configuration
- Service-specific variables

## Secrets Rotation Schedule

| Secret Type | Rotation Frequency | Notes |
|-------------|-------------------|-------|
| API Keys | 90 days | Rotate immediately if exposed |
| Database Passwords | 60 days | Use connection pooling |
| JWT Secrets | 30 days | Coordinate with token expiry |
| Service Tokens | 90 days | Monitor usage patterns |

## Using Infisical (Recommended)

For production environments, we recommend using [Infisical](https://infisical.com) for centralized secret management:

1. Install Infisical CLI:
```bash
curl -1sLf 'https://dl.cloudsmith.io/public/infisical/infisical-cli/setup.rpm.sh' | sudo -E bash
sudo apt-get install infisical
```

2. Login and pull secrets:
```bash
infisical login
infisical pull --env=prod --path=/
```

3. Integrate with Railway/Vercel:
```bash
infisical secrets push --env=prod --service=railway
```

## Troubleshooting

### Missing Environment Variables

If you see errors about missing environment variables:

1. Check that all required variables are set:
```bash
# Local
python -c "from dotenv import load_dotenv; import os; load_dotenv(); print(os.environ.get('SUPABASE_URL'))"

# Railway
railway variables

# Vercel
vercel env ls
```

2. Ensure the variable names match exactly (case-sensitive)

3. Restart your application after adding variables

### Invalid Credentials

1. Verify credentials are correct in the source system
2. Check for extra whitespace or quotes
3. Ensure you're using the correct environment's credentials
4. Verify network access (IP allowlists, etc.)

## Security Incident Response

If credentials are exposed:

1. **IMMEDIATELY** rotate the affected credentials
2. Audit access logs for unauthorized use
3. Update all services using those credentials
4. Document the incident
5. Review and improve security practices

## Best Practices

1. **Principle of Least Privilege**: Only grant the minimum required permissions
2. **Environment Isolation**: Never use production credentials in development
3. **Audit Logging**: Enable logging for all secret access
4. **Encryption**: Use encrypted connections (TLS/SSL) always
5. **Multi-Factor Authentication**: Enable MFA for all service accounts
6. **Regular Audits**: Review secret access patterns monthly
7. **Backup Keys**: Store backup keys in a secure vault
8. **Documentation**: Keep this README updated with any changes

## Contact

For security concerns or questions about secret management, contact the project maintainer immediately.