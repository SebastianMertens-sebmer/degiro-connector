# Custom DEGIRO Trading API

This directory contains custom trading API implementation separate from the main degiro-connector library.

## Structure
```
custom-trading/
├── api/                 # FastAPI trading server
├── scripts/             # Deployment and utility scripts  
├── config/              # Environment configuration (gitignored)
├── docs/                # API documentation
└── README.md           # This file
```

## Quick Start
```bash
# Setup environment
cp config/.env.example config/.env
# Edit config/.env with your credentials

# Install dependencies  
pip install -r requirements.txt

# Test connection
python ../examples/trading/login_2fa.py

# Run API locally
python api/main.py

# Deploy to VPS
./scripts/deploy_to_vps.sh
```

## Production Deployment
- **VPS**: 152.53.200.195:7731
- **Docs**: http://152.53.200.195:7731/docs
- **Auth**: Bearer token in config/.env

## Upstream Updates
This setup allows seamless updates from upstream degiro-connector:
```bash
git fetch upstream
git merge upstream/main  # No conflicts with custom-trading/
```

Your custom code stays safe while benefiting from upstream improvements!