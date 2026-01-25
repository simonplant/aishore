#!/bin/bash
# install.sh - Install aishore into current project
#
# Usage:
#   curl -sSL https://raw.githubusercontent.com/simonplant/aishore/main/install.sh | bash
#
# Or with options:
#   curl -sSL https://raw.githubusercontent.com/simonplant/aishore/main/install.sh | bash -s -- --init
#
# Options:
#   --init      Run 'aishore init' after install (creates backlog/)
#   --migrate   Run migration if old structure detected
#   --dir PATH  Install to PATH instead of current directory

set -euo pipefail

# Configuration
REPO="simonplant/aishore"
BRANCH="main"
BASE_URL="https://raw.githubusercontent.com/$REPO/$BRANCH"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log()     { echo -e "${BLUE}[aishore]${NC} $1"; }
success() { echo -e "${GREEN}✓${NC} $1"; }
warn()    { echo -e "${YELLOW}⚠${NC} $1"; }
error()   { echo -e "${RED}✗${NC} $1" >&2; }
die()     { error "$1"; exit 1; }

# Parse arguments
INSTALL_DIR="."
DO_INIT=false
DO_MIGRATE=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --init)
            DO_INIT=true
            shift
            ;;
        --migrate)
            DO_MIGRATE=true
            shift
            ;;
        --dir)
            INSTALL_DIR="$2"
            shift 2
            ;;
        *)
            die "Unknown option: $1"
            ;;
    esac
done

# Resolve install directory
INSTALL_DIR="$(cd "$INSTALL_DIR" 2>/dev/null && pwd)" || die "Directory not found: $INSTALL_DIR"
AISHORE_DIR="$INSTALL_DIR/.aishore"

# Files to download
FILES=(
    ".aishore/aishore"
    ".aishore/gitignore-entries.txt"
    ".aishore/agents/developer.md"
    ".aishore/agents/validator.md"
    ".aishore/agents/tech-lead.md"
    ".aishore/agents/product-owner.md"
    ".aishore/agents/architect.md"
)

# ============================================================================
# FUNCTIONS
# ============================================================================

check_requirements() {
    command -v curl >/dev/null 2>&1 || die "curl is required"
    command -v jq >/dev/null 2>&1 || die "jq is required (install: brew install jq / apt install jq)"
}

detect_existing() {
    if [[ -d "$AISHORE_DIR" ]]; then
        if [[ -f "$AISHORE_DIR/aishore" ]]; then
            return 0  # Already installed
        fi
    fi
    return 1
}

detect_old_structure() {
    # Check for old .aishore/plan/ structure
    if [[ -d "$AISHORE_DIR/plan" ]] && [[ -f "$AISHORE_DIR/plan/backlog.json" ]]; then
        return 0
    fi
    # Check for legacy aishore/ structure
    if [[ -d "$INSTALL_DIR/aishore/plan" ]]; then
        return 0
    fi
    return 1
}

download_file() {
    local file="$1"
    local url="$BASE_URL/$file"
    local dest="$INSTALL_DIR/$file"
    local dir
    dir="$(dirname "$dest")"

    mkdir -p "$dir"

    if curl -sSfL "$url" -o "$dest" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

install_aishore() {
    log "Installing aishore to $INSTALL_DIR..."
    echo ""

    # Create directory structure
    mkdir -p "$AISHORE_DIR"/{agents,data/{archive,logs,status}}

    # Download files
    local failed=0
    for file in "${FILES[@]}"; do
        if download_file "$file"; then
            success "Downloaded $(basename "$file")"
        else
            warn "Failed to download $file"
            ((failed++))
        fi
    done

    if [[ $failed -gt 0 ]]; then
        warn "$failed files failed to download"
    fi

    # Make CLI executable
    chmod +x "$AISHORE_DIR/aishore"

    # Create data directory placeholders
    touch "$AISHORE_DIR/data/archive/.gitkeep"
    touch "$AISHORE_DIR/data/logs/.gitkeep"
    touch "$AISHORE_DIR/data/status/.gitkeep"

    success "aishore installed"
}

run_init() {
    log "Running init..."
    cd "$INSTALL_DIR"
    "$AISHORE_DIR/aishore" init
}

run_migrate() {
    log "Downloading migration script..."
    local migrate_script
    migrate_script=$(mktemp)

    if curl -sSfL "$BASE_URL/migrate.sh" -o "$migrate_script"; then
        chmod +x "$migrate_script"
        "$migrate_script" "$INSTALL_DIR"
        rm -f "$migrate_script"
    else
        warn "Could not download migration script"
        echo "Run manually: curl -sSL $BASE_URL/migrate.sh | bash -s -- $INSTALL_DIR"
    fi
}

show_next_steps() {
    echo ""
    log "Installation complete!"
    echo ""
    echo "Next steps:"
    echo ""
    if [[ ! -d "$INSTALL_DIR/backlog" ]]; then
        echo "  1. Initialize backlog:"
        echo "     cd $INSTALL_DIR && .aishore/aishore init"
        echo ""
        echo "  2. Add items to backlog/backlog.json"
        echo ""
        echo "  3. Run a sprint:"
        echo "     .aishore/aishore run"
    else
        echo "  .aishore/aishore help      # Show commands"
        echo "  .aishore/aishore metrics   # Show metrics"
        echo "  .aishore/aishore run       # Run sprint"
    fi
    echo ""
    echo "Add to .gitignore:"
    echo "  cat .aishore/gitignore-entries.txt >> .gitignore"
    echo ""
}

# ============================================================================
# MAIN
# ============================================================================

main() {
    echo ""
    echo -e "${BLUE}════════════════════════════════════════${NC}"
    echo -e "${BLUE}  aishore installer${NC}"
    echo -e "${BLUE}════════════════════════════════════════${NC}"
    echo ""

    check_requirements

    # Check for existing installation
    if detect_existing; then
        if [[ "$DO_MIGRATE" == "true" ]] && detect_old_structure; then
            warn "Existing installation found with old structure"
            run_migrate
            exit 0
        else
            warn "aishore already installed at $AISHORE_DIR"
            echo ""
            echo "To update:"
            echo "  cd $INSTALL_DIR && .aishore/aishore update"
            echo ""
            echo "To reinstall:"
            echo "  rm -rf $AISHORE_DIR && curl -sSL $BASE_URL/install.sh | bash"
            exit 0
        fi
    fi

    # Check for old structure needing migration
    if detect_old_structure; then
        if [[ "$DO_MIGRATE" == "true" ]]; then
            run_migrate
            exit 0
        else
            warn "Old aishore structure detected"
            echo ""
            echo "To migrate:"
            echo "  curl -sSL $BASE_URL/install.sh | bash -s -- --migrate"
            exit 1
        fi
    fi

    # Fresh install
    install_aishore

    # Optional init
    if [[ "$DO_INIT" == "true" ]]; then
        run_init
    fi

    show_next_steps
}

main "$@"
