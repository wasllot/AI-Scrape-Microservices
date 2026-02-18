# Secrets Management Guide

This document outlines how to manage secrets for the microservices project.

## GitHub Secrets

Configure these secrets in your GitHub repository settings (`Settings > Secrets and variables > Actions`):

### Required Secrets

| Secret | Description | Example |
|--------|-------------|---------|
| `DROPLET_IP` | DigitalOcean droplet IP | `123.45.67.890` |
| `SSH_PRIVATE_KEY` | SSH private key for droplet access | `-----BEGIN RSA PRIVATE KEY-----...` |
| `DROPLET_USER` | SSH username (optional) | `root` |

### Optional Secrets

| Secret | Description | Example |
|--------|-------------|---------|
| `SLACK_WEBHOOK` | Slack webhook for notifications | `https://hooks.slack.com/...` |
| `DISCORD_WEBHOOK` | Discord webhook | `https://discord.com/api/webhooks/...` |

## Setting Up SSH Key for Deployment

1. **Generate SSH Key** (if not exists):
   ```bash
   ssh-keygen -t rsa -b 4096 -C "deploy@microservices" -f deploy_key
   ```

2. **Add Public Key to Droplet**:
   ```bash
   ssh root@DROPLET_IP "echo '$(cat deploy_key.pub)' >> ~/.ssh/authorized_keys"
   ```

3. **Add Private Key to GitHub**:
   ```bash
   # Copy private key content (without newlines)
   cat deploy_key
   # Add to GitHub Secrets as SSH_PRIVATE_KEY
   ```

4. **Test Connection**:
   ```bash
   ssh -i deploy_key root@DROPLET_IP
   ```

## Environment Variables for Production

Set these in your `.env.production` file (never commit this file):

```bash
# Environment
ENV=production
DEBUG=false

# Database
POSTGRES_PASSWORD=secure_random_password
POSTGRES_POOL_SIZE=20
POSTGRES_MAX_OVERFLOW=40

# Redis
REDIS_PASSWORD=secure_redis_password

# API Keys
GEMINI_API_KEY=your_production_gemini_key
GROQ_API_KEY=your_production_groq_key

# Security
ALLOWED_ORIGINS=https://yourdomain.com
```

## DigitalOcean Secrets (for Spaces/Registry)

```bash
# Add as repository variables, not secrets
AWS_ACCESS_KEY_ID=your_spaces_key
AWS_SECRET_ACCESS_KEY=your_spaces_secret
REGISTRY=registry.digitalocean.com/your-registry
```

## Secret Rotation Policy

- **API Keys**: Rotate every 90 days
- **SSH Keys**: Rotate every 180 days
- **Database Passwords**: Rotate every 60 days

## Emergency Secret Revocation

If secrets are compromised:

1. **Immediate Actions**:
   - Revoke compromised keys in provider dashboard
   - Update GitHub secrets
   - Redeploy (triggers new keys)

2. **Rollback** (if needed):
   ```bash
   git revert HEAD
   git push origin main
   ```

## Local Development Secrets

Create `.env` from `.env.example`:
```bash
cp .env.example .env
# Edit with your local values - never commit .env
```

## Verifying Secrets in CI

The CI pipeline includes secret verification:
- Checks required secrets exist before deployment
- Validates SSH key format
- Tests connectivity before deploy

## References

- [GitHub Secrets Documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [DigitalOcean Spaces](https://docs.digitalocean.com/products/spaces/)
