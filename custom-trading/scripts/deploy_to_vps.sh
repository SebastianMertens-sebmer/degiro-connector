#!/bin/bash
# Deploy DEGIRO Trading API to VPS

set -e

# Configuration
VPS_HOST="basti@152.53.200.195"
VPS_PATH="/home/basti/degiro-trading-api"
LOCAL_PATH=$(pwd)

echo "🚀 Deploying DEGIRO Trading API to VPS..."
echo "   Target: $VPS_HOST:$VPS_PATH"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found!"
    echo "Please create .env file with your configuration"
    exit 1
fi

# Create deployment package
echo "📦 Creating deployment package..."
mkdir -p tmp/deploy

# Copy essential files
cp -r api/ tmp/deploy/
cp -r config/ tmp/deploy/
cp -r docs/ tmp/deploy/
cp requirements.txt tmp/deploy/
cp .env tmp/deploy/
cp docker-compose.yml tmp/deploy/
cp Dockerfile tmp/deploy/

# Create systemd service file
cat > tmp/deploy/degiro-api.service << 'EOF'
[Unit]
Description=DEGIRO Trading API
After=network.target

[Service]
Type=simple
User=basti
WorkingDirectory=/home/basti/degiro-trading-api
Environment=PATH=/home/basti/degiro-trading-api/venv/bin
ExecStart=/home/basti/degiro-trading-api/venv/bin/python api/main.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# Create setup script for VPS
cat > tmp/deploy/setup_vps.sh << 'EOF'
#!/bin/bash
# VPS setup script

set -e

echo "🔧 Setting up DEGIRO Trading API on VPS..."

# Update system
sudo apt update
sudo apt install -y python3 python3-pip python3-venv curl

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Install additional production dependencies
pip install python-dotenv gunicorn

# Create logs directory
mkdir -p logs

# Copy systemd service
sudo cp degiro-api.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable degiro-api
sudo systemctl start degiro-api

echo "✅ Setup complete!"
echo "   • Service: sudo systemctl status degiro-api"
echo "   • Logs: journalctl -u degiro-api -f"
echo "   • API: http://$(hostname -I | awk '{print $1}'):8000"
EOF

chmod +x tmp/deploy/setup_vps.sh

# Upload to VPS
echo "📤 Uploading files to VPS..."
ssh $VPS_HOST "mkdir -p $VPS_PATH"
rsync -avz --delete tmp/deploy/ $VPS_HOST:$VPS_PATH/

# Run setup on VPS
echo "🔧 Running setup on VPS..."
ssh $VPS_HOST "cd $VPS_PATH && bash setup_vps.sh"

# Check service status
echo "📊 Checking service status..."
ssh $VPS_HOST "systemctl status degiro-api --no-pager"

# Get VPS IP
VPS_IP=$(ssh $VPS_HOST "hostname -I | awk '{print \$1}'")

# Cleanup
rm -rf tmp/

echo ""
echo "✅ Deployment successful!"
echo "   🌐 API URL: http://$VPS_IP:8000"
echo "   📖 Docs: http://$VPS_IP:8000/docs"
echo "   🔍 Health: http://$VPS_IP:8000/api/health"
echo ""
echo "📋 Useful commands:"
echo "   ssh $VPS_HOST 'systemctl status degiro-api'"
echo "   ssh $VPS_HOST 'journalctl -u degiro-api -f'"
echo "   ssh $VPS_HOST 'systemctl restart degiro-api'"