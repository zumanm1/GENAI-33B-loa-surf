
#!/bin/bash
# Network Automation Platform Setup Script

echo "🚀 Setting up Network Automation Platform..."

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "📋 Installing requirements..."
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p backups logs

# Test EVE-NG connectivity
echo "🔍 Testing EVE-NG connectivity..."
ping -c 3 172.16.39.102

# Test telnet connectivity to routers
echo "📡 Testing router connectivity..."
echo "Testing R15 (port 32783)..."
timeout 5 telnet 172.16.39.102 32783 < /dev/null

echo "Testing R16 (port 32773)..."
timeout 5 telnet 172.16.39.102 32773 < /dev/null

echo "✅ Setup complete!"
echo ""
echo "🚀 To start the application:"
echo "  source venv/bin/activate"
echo "  python app.py"
echo ""
echo "🔍 To test the API:"
echo "  python test_api.py"
echo ""
echo "📡 EVE-NG Management IP: 172.16.39.102"
echo "🖥️  R15 Console: telnet 172.16.39.102 32783"
echo "🖥️  R16 Console: telnet 172.16.39.102 32773"
echo "🔑 Credentials: cisco/cisco"
