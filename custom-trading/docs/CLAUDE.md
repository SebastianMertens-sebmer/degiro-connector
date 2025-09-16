# DEGIRO Trading API - Claude Documentation

## Project Overview
Production-ready FastAPI server for automated DEGIRO trading with leveraged products support.

## Key Features
- Universal product search (ISIN, name, ticker symbols)
- Leveraged products filtering by underlying assets
- Two-step order validation (check → confirm)
- Bearer token authentication
- VPS deployment with auto-restart capabilities

## API Endpoints
- `GET /api/health` - Health check (public)
- `POST /api/products/search` - Universal product search
- `POST /api/orders/check` - Validate order parameters  
- `POST /api/orders/confirm` - Execute validated order

## Production Deployment
**VPS**: 152.53.200.195:7731  
**Auth**: Bearer `pjFJKB-iEd3_HOLchTcxglzV1yn27QncyzDQAhOhf1Y`  
**Docs**: http://152.53.200.195:7731/docs

## Quick Commands
```bash
# Deploy to VPS
./scripts/deploy_to_vps.sh

# Connect to VPS
ssh -i ~/.ssh/rockettrader_key basti@152.53.200.195

# Start API
cd /home/basti/degiro-trading-api && ./start_api.sh

# Test API
curl -H "Authorization: Bearer pjFJKB-iEd3_HOLchTcxglzV1yn27QncyzDQAhOhf1Y" \
     http://152.53.200.195:7731/api/health
```

## Environment Setup
- Credentials in `.env` file (DEGIRO_USERNAME, DEGIRO_PASSWORD, DEGIRO_TOTP_SECRET)
- Custom port 7731 for security
- Firewall configured for port access
- Python 3.12 virtual environment

## Security
- Secure 32-character API tokens
- Environment variable credential management
- VPS firewall protection
- Bearer token authentication

## Testing
- Run `python _tests/login_2fa.py` to verify DEGIRO connection
- Health endpoint shows connection status
- Complete API documentation at `/docs`

## Dependencies
- FastAPI, uvicorn, pydantic
- degiro-connector (trading API)
- python-dotenv (environment management)