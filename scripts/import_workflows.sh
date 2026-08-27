#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# import_workflows.sh — AI Automation Platform — Week 5
# Imports all 100 n8n workflow JSON files via the n8n REST API
# ─────────────────────────────────────────────────────────────────────────────

# ── Configuration ─────────────────────────────────────────────────────────────
N8N_URL="${N8N_URL:-http://localhost:5678}"
N8N_USER="${N8N_USER:-admin}"
N8N_PASS="${N8N_PASS:-admin123}"
WORKFLOWS_DIR="${WORKFLOWS_DIR:-workflows}"
MAX_RETRIES=3
RETRY_DELAY=2

# ── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ── Counters ──────────────────────────────────────────────────────────────────
COUNT_SUCCESS=0
COUNT_SKIP=0
COUNT_FAIL=0
FAILED_FILES=()

# ── Banner ────────────────────────────────────────────────────────────────────
echo -e "${BOLD}${CYAN}"
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║         📥 AI Automation Platform — n8n Workflow Importer       ║"
echo "║         Importing 100 workflows across 9 business domains        ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ── Validate prerequisites ────────────────────────────────────────────────────
if ! command -v curl >/dev/null 2>&1; then
    echo -e "${RED}❌ curl is required but not installed.${NC}"
    exit 1
fi

if ! command -v python3 >/dev/null 2>&1; then
    echo -e "${RED}❌ python3 is required but not installed.${NC}"
    exit 1
fi

# ── Check n8n connectivity ────────────────────────────────────────────────────
echo -e "${BLUE}🔌 Connecting to n8n at ${CYAN}${N8N_URL}${NC}..."

MAX_CONNECT_WAIT=60
CONNECT_ATTEMPT=0
while [ $CONNECT_ATTEMPT -lt $MAX_CONNECT_WAIT ]; do
    HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
        -u "${N8N_USER}:${N8N_PASS}" \
        "${N8N_URL}/api/v1/workflows" 2>/dev/null)

    if [ "$HTTP_STATUS" = "200" ] || [ "$HTTP_STATUS" = "201" ]; then
        echo -e "${GREEN}✅ Connected to n8n successfully${NC}\n"
        break
    elif [ "$HTTP_STATUS" = "401" ]; then
        echo -e "${RED}❌ Authentication failed. Check N8N_USER and N8N_PASS.${NC}"
        echo -e "   Current: ${YELLOW}${N8N_USER}${NC} / ${YELLOW}${N8N_PASS}${NC}"
        exit 1
    else
        echo -n "  Waiting for n8n to be ready (attempt $((CONNECT_ATTEMPT+1))/$MAX_CONNECT_WAIT)..."
        sleep 2
        CONNECT_ATTEMPT=$((CONNECT_ATTEMPT + 1))
        echo " HTTP $HTTP_STATUS"
    fi
done

if [ $CONNECT_ATTEMPT -ge $MAX_CONNECT_WAIT ]; then
    echo -e "${RED}❌ Timed out waiting for n8n. Is it running?${NC}"
    echo -e "   Start with: ${CYAN}docker-compose up -d${NC}"
    exit 1
fi

# ── Validate workflows directory ──────────────────────────────────────────────
if [ ! -d "$WORKFLOWS_DIR" ]; then
    echo -e "${RED}❌ Workflows directory not found: ${WORKFLOWS_DIR}${NC}"
    echo -e "   Run from the project root: ${CYAN}bash scripts/import_workflows.sh${NC}"
    exit 1
fi

# Count total workflows
TOTAL_FILES=$(find "$WORKFLOWS_DIR" -name "*.json" 2>/dev/null | wc -l)
if [ "$TOTAL_FILES" -eq 0 ]; then
    echo -e "${YELLOW}⚠️  No JSON workflow files found in ${WORKFLOWS_DIR}/${NC}"
    exit 0
fi

echo -e "${BOLD}📊 Found ${CYAN}${TOTAL_FILES}${NC}${BOLD} workflow files to import${NC}"
echo -e "${BLUE}─────────────────────────────────────────────────────────────────${NC}\n"

# ── Helper: import a single workflow with retry ───────────────────────────────
import_workflow() {
    local workflow_file="$1"
    local attempt=1

    # Validate JSON first
    if ! python3 -c "import json; json.load(open('$workflow_file'))" 2>/dev/null; then
        echo -e "  ${RED}⚠️  SKIP (invalid JSON): $(basename "$workflow_file")${NC}"
        COUNT_SKIP=$((COUNT_SKIP + 1))
        return
    fi

    while [ $attempt -le $MAX_RETRIES ]; do
        RESPONSE=$(curl -s \
            -u "${N8N_USER}:${N8N_PASS}" \
            -X POST "${N8N_URL}/api/v1/workflows" \
            -H "Content-Type: application/json" \
            -H "Accept: application/json" \
            --connect-timeout 10 \
            --max-time 30 \
            -d @"$workflow_file" 2>&1)

        # Check for success (n8n returns the created workflow with "id" field)
        if echo "$RESPONSE" | python3 -c "
import json, sys
try:
    data = json.loads(sys.stdin.read())
    if 'id' in data:
        print(data.get('name', 'unnamed'))
        sys.exit(0)
    sys.exit(1)
except:
    sys.exit(1)
" 2>/dev/null; then
            WORKFLOW_NAME=$(echo "$RESPONSE" | python3 -c "
import json, sys
data = json.loads(sys.stdin.read())
print(data.get('name', 'unnamed'))
" 2>/dev/null)
            COUNT_SUCCESS=$((COUNT_SUCCESS + 1))
            echo -e "  ${GREEN}✅ (${COUNT_SUCCESS}) Imported:${NC} ${CYAN}${WORKFLOW_NAME}${NC} ← $(basename "$workflow_file")"
            return
        fi

        # Check if it already exists (409 Conflict)
        if echo "$RESPONSE" | grep -qi "already exists\|duplicate\|conflict"; then
            echo -e "  ${YELLOW}⏭  SKIP (already exists): $(basename "$workflow_file")${NC}"
            COUNT_SKIP=$((COUNT_SKIP + 1))
            return
        fi

        if [ $attempt -lt $MAX_RETRIES ]; then
            echo -e "  ${YELLOW}⟳  Retry $attempt/$MAX_RETRIES for: $(basename "$workflow_file")${NC}"
            sleep $RETRY_DELAY
        fi
        attempt=$((attempt + 1))
    done

    # All retries failed
    echo -e "  ${RED}❌ FAILED: $(basename "$workflow_file")${NC}"
    COUNT_FAIL=$((COUNT_FAIL + 1))
    FAILED_FILES+=("$workflow_file")
}

# ── Process by category ───────────────────────────────────────────────────────
process_category() {
    local dir="$1"
    local category_name
    category_name=$(basename "$dir" | tr '_' ' ' | awk '{for(i=1;i<=NF;i++) $i=toupper(substr($i,1,1)) tolower(substr($i,2)); print}')
    local json_count
    json_count=$(find "$dir" -name "*.json" | wc -l)

    if [ "$json_count" -eq 0 ]; then
        return
    fi

    echo -e "\n${BOLD}📂 ${category_name} (${json_count} workflows)${NC}"
    echo -e "${BLUE}  ──────────────────────────────────────────${NC}"

    while IFS= read -r workflow_file; do
        import_workflow "$workflow_file"
    done < <(find "$dir" -name "*.json" | sort)
}

# Process each category directory
for category_dir in "$WORKFLOWS_DIR"/*/; do
    if [ -d "$category_dir" ]; then
        process_category "$category_dir"
    fi
done

# Also process any JSON files directly in the workflows root
ROOT_JSONS=$(find "$WORKFLOWS_DIR" -maxdepth 1 -name "*.json" 2>/dev/null)
if [ -n "$ROOT_JSONS" ]; then
    echo -e "\n${BOLD}📂 Root Workflows${NC}"
    echo -e "${BLUE}  ──────────────────────────────────────────${NC}"
    while IFS= read -r workflow_file; do
        import_workflow "$workflow_file"
    done <<< "$ROOT_JSONS"
fi

# ── Summary ───────────────────────────────────────────────────────────────────
TOTAL_PROCESSED=$((COUNT_SUCCESS + COUNT_SKIP + COUNT_FAIL))

echo ""
echo -e "${BOLD}${CYAN}╔══════════════════════════════════════════════════════════════════╗"
echo -e "║                     📊 Import Summary                           ║"
echo -e "╚══════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${GREEN}✅ Successfully imported: ${BOLD}${COUNT_SUCCESS}${NC}"
echo -e "  ${YELLOW}⏭  Already existed (skipped): ${BOLD}${COUNT_SKIP}${NC}"
echo -e "  ${RED}❌ Failed: ${BOLD}${COUNT_FAIL}${NC}"
echo -e "  ${BLUE}📋 Total processed: ${BOLD}${TOTAL_PROCESSED}${NC}"
echo ""

if [ ${#FAILED_FILES[@]} -gt 0 ]; then
    echo -e "${RED}${BOLD}Failed files:${NC}"
    for f in "${FAILED_FILES[@]}"; do
        echo -e "  ${RED}  - $f${NC}"
    done
    echo ""
fi

if [ "$COUNT_SUCCESS" -gt 0 ]; then
    echo -e "${GREEN}${BOLD}🎉 Import complete!${NC}"
    echo -e "  🔗 Open n8n:  ${CYAN}${N8N_URL}${NC}"
    echo -e "  🔑 Login:     ${YELLOW}${N8N_USER}${NC} / ${YELLOW}${N8N_PASS}${NC}"
    echo ""
    echo -e "  ${BLUE}Tip:${NC} Activate workflows in the n8n UI before they can run."
fi

# Exit with error if any imports failed
[ "$COUNT_FAIL" -eq 0 ]
