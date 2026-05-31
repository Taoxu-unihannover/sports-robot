#!/bin/bash
# -----------------------------------------------------------------------------
# Ball Perception Plugin - Environment Initializer
# -----------------------------------------------------------------------------

set -e

# --- Color & output helpers ---
if [ -t 1 ]; then
  GREEN='\033[0;32m'; YELLOW='\033[0;33m'; RED='\033[0;31m'
  CYAN='\033[0;36m'; BOLD='\033[1m'; DIM='\033[2m'; NC='\033[0m'
else
  GREEN=''; YELLOW=''; RED=''; CYAN=''; BOLD=''; DIM=''; NC=''
fi

ok()   { echo -e "  ${DIM}${GREEN}✓${NC}${DIM} $*${NC}"; }
warn() { echo -e "  ${YELLOW}⚠${NC}${DIM} $*${NC}"; }
err()  { echo -e "  ${RED}✗${NC}${DIM} $*${NC}"; }
info() { echo -e "  ${DIM}${CYAN}→${NC}${DIM} $*${NC}"; }
step() { echo -e "${DIM}$*${NC}"; }

BRAND="sports-robot"
VERSION="1.0.0"

show_banner() {
  echo ""
  echo -e "${CYAN}"
  cat << 'BANNER'
   ____            _     ____       _
  / ___| _ __ ___ | |_  |  _ \ ___ | |__   ___  _ __ ___
  \___ \| '_ \` _ \| __| | |_) / _ \| '_ \ / _ \| '__/ __|
   ___) | | | | | | |_  |  _ < (_) | |_) | (_) | |  \__ \
  |____/|_| |_| |_|\__| |_| \_\___/|_.__/ \___/|_|  |___/
BANNER
  echo -e "${NC}"
  echo -e "  ${BOLD}Ball Perception Development Team${NC}"
  echo ""
}

show_help() {
    cat << EOF
SportsRobot Ball Perception - Development Environment Installer

Usage: init.sh [level] [tool] [install_path]

Arguments:
  level        - Installation level: "project" (default) or "global"
  tool         - Target tool: "trae" (default), "claude", or "cursor"
  install_path - Project-level installation directory (default: current working directory)

Options:
  --help  - Show this help message
EOF
}

install_dependencies() {
    step "Installing Python dependencies..."
    if command -v pip &> /dev/null; then
        pip install -r "$PLUGIN_ROOT/requirements.txt" 2>/dev/null && \
            ok "Python dependencies installed" || \
            warn "Some dependencies may need manual installation"
    else
        warn "pip not found, skipping Python dependency installation"
    fi
}

verify_skills() {
    step "Verifying skills..."
    local skills=("ball-detector" "ball-tracker" "ball-filter" "ball-geometry")
    local all_ok=true

    for skill in "${skills[@]}"; do
        if [ -f "$SKILLS_ROOT/$skill/SKILL.md" ]; then
            ok "Skill '$skill' found"
        else
            err "Skill '$skill' not found at $SKILLS_ROOT/$skill/SKILL.md"
            all_ok=false
        fi
    done

    if [ "$all_ok" = true ]; then
        ok "All skills verified"
    else
        err "Some skills are missing"
    fi
}

verify_agents() {
    step "Verifying agents..."
    local agents=("perception-architect" "perception-developer" "perception-reviewer")
    local all_ok=true

    for agent in "${agents[@]}"; do
        if [ -f "$PLUGIN_ROOT/agents/$agent.md" ]; then
            ok "Agent '$agent' found"
        else
            err "Agent '$agent' not found"
            all_ok=false
        fi
    done

    if [ "$all_ok" = true ]; then
        ok "All agents verified"
    fi
}

# --- Main ---
LEVEL="${1:-project}"
TOOL="${2:-trae}"
INSTALL_PATH="${3:-$(pwd)}"

if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
    show_help
    exit 0
fi

PLUGIN_ROOT="$(cd "$(dirname "$0")" && pwd)"
SKILLS_ROOT="$(cd "$PLUGIN_ROOT/../../skills" 2>/dev/null && pwd || echo "$PLUGIN_ROOT/../../skills")"

show_banner

info "Plugin root: $PLUGIN_ROOT"
info "Skills root: $SKILLS_ROOT"
info "Install level: $LEVEL"
info "Target tool: $TOOL"

echo ""

verify_skills
verify_agents
install_dependencies

echo ""
ok "Ball Perception plugin initialized successfully!"
echo ""
echo -e "  ${BOLD}Quick start:${NC}"
echo -e "    cat AGENTS.md          # Team overview"
echo -e "    cat quickstart.md      # Getting started guide"
echo ""
