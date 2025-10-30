#!/bin/bash

set -e

echo "🛡️  ThreatCanvas Launcher"
echo "========================="

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    echo -e "${GREEN}Installing dependencies...${NC}"
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

if [ ! -f ".env" ]; then
    echo -e "${YELLOW}No .env file found. Copying from .env.example...${NC}"
    cp .env.example .env
    echo -e "${GREEN}Created .env file. Please review and modify as needed.${NC}"
fi

if [ ! -r "/var/log/auth.log" ]; then
    echo -e "${YELLOW}⚠️  Cannot read /var/log/auth.log${NC}"
    echo "   Using fallback sample log. To use real logs, run with sudo or adjust permissions."
fi

echo -e "${GREEN}Starting ThreatCanvas...${NC}"
python3 app.py &
FLASK_PID=$!

echo -e "${GREEN}✅ ThreatCanvas is running!${NC}"
echo -e "   Local: http://localhost:5000"
echo -e "   PID: $FLASK_PID"

read -p "Start ngrok tunnel? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v ngrok &> /dev/null; then
        echo -e "${GREEN}Starting ngrok tunnel...${NC}"
        ngrok http 5000 &
        NGROK_PID=$!
        echo -e "${GREEN}Ngrok PID: $NGROK_PID${NC}"
        echo -e "View tunnel URLs at: http://localhost:4040"
    else
        echo -e "${RED}ngrok not found. Install from: https://ngrok.com/download${NC}"
    fi
fi

trap "echo -e '\n${YELLOW}Shutting down...${NC}'; kill $FLASK_PID 2>/dev/null; [ ! -z '$NGROK_PID' ] && kill $NGROK_PID 2>/dev/null; exit" INT

wait $FLASK_PID
