#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# setup.sh — AI Automation Platform — Week 5
# Full setup script: dependency check, env setup, Docker launch, health check
# ─────────────────────────────────────────────────────────────────────────────
set -e

# ── Colors ────────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# ── Helpers ───────────────────────────────────────────────────────────────────
info()    { echo -e "${BLUE}ℹ️  $*${NC}"; }
success() { echo -e "${GREEN}✅ $*${NC}"; }
warn()    { echo -e "${YELLOW}⚠️  $*${NC}"; }
error()   { echo -e "${RED}❌ $*${NC}"; }
header()  { echo -e "\n${BOLD}${CYAN}$*${NC}\n"; }

# ── Banner ────────────────────────────────────────────────────────────────────
echo -e "${BOLD}${CYAN}"
echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║          🤖 AI Automation Platform — Week 5 Setup               ║"
echo "║          Production-grade company automation suite               ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# ── Step 1: Check Dependencies ────────────────────────────────────────────────
header "🔍 Step 1: Checking dependencies..."

check_command() {
    local cmd="$1"
    local name="$2"
    local install_hint="$3"
    if command -v "$cmd" >/dev/null 2>&1; then
        version=$("$cmd" --version 2>&1 | head -1)
        success "$name found: $version"
    else
        error "$name is required but not installed."
        echo -e "  → Install: ${YELLOW}$install_hint${NC}"
        exit 1
    fi
}

check_command docker        "Docker"         "https://docs.docker.com/get-docker/"
check_command docker-compose "Docker Compose" "https://docs.docker.com/compose/install/"
check_command curl          "curl"            "sudo apt install curl"
check_command python3       "Python 3"        "sudo apt install python3"

# Check Docker daemon is running
if ! docker info >/dev/null 2>&1; then
    error "Docker daemon is not running. Start it with: sudo systemctl start docker"
    exit 1
fi
success "Docker daemon is running"

# ── Step 2: Environment Setup ─────────────────────────────────────────────────
header "⚙️  Step 2: Setting up environment..."

if [ ! -f .env ]; then
    if [ -f .env.example ]; then
        cp .env.example .env
        success "Created .env from .env.example"
        warn "Please update .env with your actual API keys before proceeding."
        echo ""
        echo -e "  Required keys to set:"
        echo -e "  ${YELLOW}  OPENAI_API_KEY=sk-your-key-here${NC}"
        echo -e "  ${YELLOW}  SECRET_KEY=your-32-char-secret${NC}"
        echo ""
        read -r -p "  Have you updated the .env file? [y/N]: " confirm
        if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
            warn "Please edit .env and re-run this script."
            echo -e "  ${CYAN}nano .env${NC}  or  ${CYAN}code .env${NC}"
            exit 0
        fi
    else
        error ".env.example not found. Cannot create .env automatically."
        echo "  Please create a .env file manually based on the README."
        exit 1
    fi
else
    success ".env file already exists"
    info "Using existing .env — update API keys if needed"
fi

# Validate required env vars
source .env 2>/dev/null || true
MISSING_VARS=()

[ -z "${OPENAI_API_KEY:-}" ]   && MISSING_VARS+=("OPENAI_API_KEY")
[ -z "${DATABASE_URL:-}" ]      && MISSING_VARS+=("DATABASE_URL")
[ -z "${REDIS_URL:-}" ]         && MISSING_VARS+=("REDIS_URL")
[ -z "${SECRET_KEY:-}" ]        && MISSING_VARS+=("SECRET_KEY")

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    warn "The following required variables are missing from .env:"
    for var in "${MISSING_VARS[@]}"; do
        echo -e "  ${RED}  $var${NC}"
    done
    warn "Services may not start correctly without them."
fi

# ── Step 3: Create required directories ───────────────────────────────────────
header "📁 Step 3: Creating required directories..."

mkdir -p data/postgres
mkdir -p data/redis
mkdir -p data/minio
mkdir -p data/qdrant
mkdir -p data/n8n
mkdir -p logs
mkdir -p uploads

success "Directories created"

# ── Step 4: Pull Docker images ────────────────────────────────────────────────
header "🐳 Step 4: Pulling Docker images..."
info "This may take a few minutes on first run..."

docker-compose pull 2>&1 | grep -E "(Pulling|pulled|up to date|error)" || true
success "Docker images ready"

# ── Step 5: Start Services ────────────────────────────────────────────────────
header "🚀 Step 5: Starting Docker services..."

docker-compose up -d

success "Docker Compose services started"

# ── Step 6: Wait for Services ─────────────────────────────────────────────────
header "⏳ Step 6: Waiting for services to become healthy..."

wait_for_service() {
    local name="$1"
    local url="$2"
    local max_attempts=30
    local attempt=1

    echo -n "  Waiting for $name"
    while [ $attempt -le $max_attempts ]; do
        if curl -sf "$url" >/dev/null 2>&1; then
            echo -e " ${GREEN}✅${NC}"
            return 0
        fi
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    echo -e " ${YELLOW}⏱ (still starting)${NC}"
    return 1
}

wait_for_service "FastAPI Backend" "http://localhost:8000/health"
wait_for_service "n8n"             "http://localhost:5678/healthz"
wait_for_service "Prometheus"      "http://localhost:9090/-/healthy"
wait_for_service "Grafana"         "http://localhost:3001/api/health"
wait_for_service "MinIO"           "http://localhost:9001/minio/health/live"

# ── Step 7: Health Checks ─────────────────────────────────────────────────────
header "🏥 Step 7: Running health checks..."

echo -e "\n  ${BOLD}FastAPI Backend Health:${NC}"
HEALTH_RESPONSE=$(curl -sf http://localhost:8000/health 2>/dev/null || echo '{"status": "starting"}')
echo "$HEALTH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "  $HEALTH_RESPONSE"

echo -e "\n  ${BOLD}Running containers:${NC}"
docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || docker-compose ps

# ── Step 8: Import Workflows (optional) ───────────────────────────────────────
header "📥 Step 8: Workflow import (optional)"

if [ -d "workflows" ] && [ "$(find workflows -name '*.json' 2>/dev/null | wc -l)" -gt 0 ]; then
    WORKFLOW_COUNT=$(find workflows -name '*.json' | wc -l)
    echo -e "  Found ${CYAN}$WORKFLOW_COUNT${NC} workflow JSON files"
    read -r -p "  Import all workflows into n8n now? [y/N]: " import_confirm
    if [[ "$import_confirm" =~ ^[Yy]$ ]]; then
        bash scripts/import_workflows.sh
    else
        info "Skipping workflow import. Run 'bash scripts/import_workflows.sh' later."
    fi
else
    info "No workflow JSON files found in workflows/ — skipping import"
fi

# ── Done ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}${GREEN}╔══════════════════════════════════════════════════════════════════╗"
echo -e "║                   ✅ Setup Complete!                             ║"
echo -e "╚══════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${BOLD}Services:${NC}"
echo -e "  📊 Dashboard:   ${CYAN}http://localhost:3000${NC}"
echo -e "  🔧 n8n:         ${CYAN}http://localhost:5678${NC}   ${YELLOW}(admin / admin123)${NC}"
echo -e "  🚀 FastAPI:     ${CYAN}http://localhost:8000${NC}"
echo -e "  📖 API Docs:    ${CYAN}http://localhost:8000/docs${NC}"
echo -e "  🗄️  MinIO:       ${CYAN}http://localhost:9001${NC}   ${YELLOW}(minioadmin / minioadmin123)${NC}"
echo -e "  📈 Grafana:     ${CYAN}http://localhost:3001${NC}   ${YELLOW}(admin / admin)${NC}"
echo -e "  📡 Prometheus:  ${CYAN}http://localhost:9090${NC}"
echo -e "  🔍 Qdrant:      ${CYAN}http://localhost:6333${NC}"
echo ""
echo -e "  ${BOLD}Useful commands:${NC}"
echo -e "  ${CYAN}docker-compose logs -f backend${NC}    # Stream backend logs"
echo -e "  ${CYAN}docker-compose ps${NC}                 # Check service status"
echo -e "  ${CYAN}docker-compose down${NC}               # Stop all services"
echo -e "  ${CYAN}bash scripts/import_workflows.sh${NC}  # Import n8n workflows"
echo ""
