#!/bin/bash

# Onwords Desktop Agent - Mac Setup Script

echo "╔═══════════════════════════════════════════════════════╗"
echo "║     🤖 Onwords Desktop Agent - Mac Setup              ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed."
    echo "   Install it from: https://www.python.org/downloads/"
    exit 1
fi

echo "✅ Python 3 found: $(python3 --version)"

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install dependencies
echo ""
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check for API key
echo ""
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  ANTHROPIC_API_KEY not set."
    echo ""
    echo "To set it permanently, add to your ~/.zshrc or ~/.bash_profile:"
    echo ""
    echo "  export ANTHROPIC_API_KEY='your-api-key-here'"
    echo ""
    echo "Then run: source ~/.zshrc"
    echo ""
    read -p "Enter your API key now (or press Enter to skip): " api_key
    if [ ! -z "$api_key" ]; then
        export ANTHROPIC_API_KEY="$api_key"
        echo "✅ API key set for this session"
    fi
else
    echo "✅ ANTHROPIC_API_KEY is set"
fi

# macOS permissions reminder
echo ""
echo "═══════════════════════════════════════════════════════"
echo "⚠️  IMPORTANT: macOS Permissions Required!"
echo "═══════════════════════════════════════════════════════"
echo ""
echo "This agent needs the following permissions:"
echo ""
echo "1. 🖥️  Screen Recording"
echo "   System Settings → Privacy & Security → Screen Recording"
echo "   → Enable for Terminal (or your terminal app)"
echo ""
echo "2. ⌨️  Accessibility"
echo "   System Settings → Privacy & Security → Accessibility"
echo "   → Enable for Terminal (or your terminal app)"
echo ""
echo "Without these, the agent cannot capture screen or control input!"
echo ""
echo "═══════════════════════════════════════════════════════"

# Create launcher script
cat > run.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python3 agent.py
EOF
chmod +x run.sh

echo ""
echo "✅ Setup complete!"
echo ""
echo "To run the agent:"
echo "  ./run.sh"
echo ""
echo "Or manually:"
echo "  source venv/bin/activate"
echo "  python3 agent.py"
echo ""
