#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# import_workflows.sh — AI Automation Platform — Week 5
# Imports all 100 n8n workflow JSON files via the n8n CLI inside Docker
# ─────────────────────────────────────────────────────────────────────────────

CONTAINER_NAME="${CONTAINER_NAME:-n8n}"
WORKFLOWS_DIR="${WORKFLOWS_DIR:-workflows}"

# ── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ── Banner ────────────────────────────────────────────────────────────────────
echo -e "${BOLD}${CYAN}"
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║         📥 AI Automation Platform — n8n Workflow Importer       ║"
echo "║         Importing 100 workflows across 9 business domains        ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Check Docker container
if ! docker ps | grep -q "$CONTAINER_NAME"; then
    echo -e "${RED}❌ Docker container '$CONTAINER_NAME' is not running.${NC}"
    echo -e "   Run: ${CYAN}docker-compose up -d${NC}"
    exit 1
fi

echo -e "${BLUE}📦 Copying workflow files into n8n container...${NC}"
docker cp "$WORKFLOWS_DIR" "$CONTAINER_NAME":/tmp/

echo -e "${BLUE}📥 Importing workflows into n8n database...${NC}"
docker exec -i "$CONTAINER_NAME" sh -c '
for dir in /tmp/workflows/*/; do
  echo "  --> Importing category: $(basename $dir)"
  n8n import:workflow --separate --input="$dir"
done
'

echo ""
echo -e "${GREEN}${BOLD}🎉 Import complete! All 100 workflows loaded into n8n.${NC}"
echo -e "  🔗 Open n8n Dashboard: ${CYAN}http://localhost:5678${NC}"
echo ""

