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
#   --dir PATH  Install to PATH instead of current directory

set -euo pipefail

# Configuration
REPO="simonplant/aishore"
API_URL="https://api.github.com/repos/$REPO/releases/latest"

resolve_base_url() {
    local tag
    tag=$(curl -sSfL "$API_URL" 2>/dev/null | jq -r '.tag_name // empty') || true
    if [[ -z "$tag" ]]; then
        warn "Could not resolve latest release — falling back to main"
        tag="main"
    else
        log "Latest release: $tag"
    fi
    echo "https://raw.githubusercontent.com/$REPO/$tag"
}

BASE_URL=""

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

while [[ $# -gt 0 ]]; do
    case "$1" in
        --init)
            DO_INIT=true
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

# Files to download — discovered from checksums manifest
discover_files() {
    local checksums
    checksums=$(curl -sSfL "$BASE_URL/.aishore/checksums.sha256" 2>/dev/null) || \
        die "Failed to fetch checksums manifest from $BASE_URL/.aishore/checksums.sha256"
    local files=()
    while IFS= read -r line; do
        local fpath
        fpath=$(echo "$line" | awk '{print $2}')
        [[ -z "$fpath" ]] && continue
        # Validate: must be inside .aishore/, no traversal, no absolute paths
        if [[ "$fpath" != .aishore/* ]] || [[ "$fpath" == *..* ]] || [[ "$fpath" == /* ]]; then
            die "Unsafe path in checksums manifest: $fpath"
        fi
        # Protect user config from overwrite
        if [[ "$fpath" == ".aishore/config.yaml" ]]; then
            continue
        fi
        files+=("$fpath")
    done <<< "$checksums"
    if [[ ${#files[@]} -eq 0 ]]; then
        die "No files found in checksums manifest"
    fi
    printf '%s\n' "${files[@]}"
}

FILES=()

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

    # Resolve latest release tag
    BASE_URL=$(resolve_base_url)

    # Discover files from checksums manifest
    log "Fetching file manifest..."
    local file_list
    file_list=$(discover_files)
    while IFS= read -r f; do
        FILES+=("$f")
    done <<< "$file_list"

    # Create directory structure
    mkdir -p "$AISHORE_DIR"/{data/{logs,status}}
    for file in "${FILES[@]}"; do
        mkdir -p "$(dirname "$INSTALL_DIR/$file")"
    done

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
    touch "$AISHORE_DIR/data/logs/.gitkeep"
    touch "$AISHORE_DIR/data/status/.gitkeep"

    success "aishore installed"
}

run_init() {
    log "Running init..."
    cd "$INSTALL_DIR"
    "$AISHORE_DIR/aishore" init
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
        echo "  2. Add items to your backlog:"
        echo "     .aishore/aishore backlog add"
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
        warn "aishore already installed at $AISHORE_DIR"
        echo ""
        echo "To update:"
        echo "  cd $INSTALL_DIR && .aishore/aishore update"
        echo ""
        echo "To reinstall:"
        echo "  rm -rf $AISHORE_DIR && curl -sSL https://raw.githubusercontent.com/$REPO/main/install.sh | bash"
        exit 0
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
