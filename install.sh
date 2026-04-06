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
#   --force     Reinstall over existing installation (preserves config.yaml and backlog/)
#   --dir PATH  Install to PATH instead of current directory

set -euo pipefail

# Configuration
REPO="simonplant/aishore"
API_URL="https://api.github.com/repos/$REPO/releases/latest"

# GitHub auth token (gh CLI or GITHUB_TOKEN env var)
_GH_TOKEN=""
_resolve_gh_token() {
    [[ -n "$_GH_TOKEN" ]] && return
    if command -v gh >/dev/null 2>&1; then
        _GH_TOKEN=$(gh auth token 2>/dev/null) || true
    fi
    if [[ -z "$_GH_TOKEN" && -n "${GITHUB_TOKEN:-}" ]]; then
        _GH_TOKEN="$GITHUB_TOKEN"
    fi
}

# Low-level curl with auth header injection
_curl() {
    _resolve_gh_token
    if [[ -n "$_GH_TOKEN" ]]; then
        curl -H "Authorization: token $_GH_TOKEN" "$@"
    else
        curl "$@"
    fi
}

# Resolved release tag
_RELEASE_TAG=""

resolve_tag() {
    _RELEASE_TAG=$(_curl -sSfL "$API_URL" 2>/dev/null | jq -r '.tag_name // empty') || true
    if [[ -z "$_RELEASE_TAG" ]]; then
        warn "Could not resolve latest release — falling back to main"
        _RELEASE_TAG="main"
    else
        log "Latest release: $_RELEASE_TAG"
    fi
}

# Fetch a repo file to stdout — tries raw.githubusercontent.com, falls back to Contents API
_fetch_repo_file() {
    local file_path="$1"
    local raw_url="https://raw.githubusercontent.com/$REPO/$_RELEASE_TAG/$file_path"

    # Route 1: raw.githubusercontent.com (fast, no rate limit)
    local content
    if content=$(_curl -sSfL "$raw_url" 2>/dev/null); then
        printf '%s' "$content"
        return 0
    fi

    # Route 2: GitHub Contents API (always fresh, base64-encoded)
    local api_url="https://api.github.com/repos/$REPO/contents/$file_path?ref=$_RELEASE_TAG"
    local json
    if json=$(_curl -sSfL "$api_url" 2>/dev/null); then
        printf '%s' "$json" | jq -r '.content' | base64 -d
        return 0
    fi

    return 1
}

# Fetch a repo file and save to disk
_fetch_repo_file_to() {
    local file_path="$1" dest="$2"
    local content
    if content=$(_fetch_repo_file "$file_path"); then
        printf '%s' "$content" > "$dest"
        return 0
    fi
    return 1
}

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
FORCE=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --init)
            DO_INIT=true
            shift
            ;;
        --force)
            FORCE=true
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

# Checksums manifest content (populated by discover_files)
CHECKSUMS_CONTENT=""

# Files to download — discovered from checksums manifest
discover_files() {
    [[ -z "$CHECKSUMS_CONTENT" ]] && die "Checksums manifest not loaded"
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
    done <<< "$CHECKSUMS_CONTENT"
    if [[ ${#files[@]} -eq 0 ]]; then
        die "No files found in checksums manifest"
    fi
    printf '%s\n' "${files[@]}"
}

verify_file() {
    local file="$1"
    local rel_path="$2"
    local expected
    expected=$(echo "$CHECKSUMS_CONTENT" | awk -v f="$rel_path" '$2 == f {print $1; exit}')
    [[ -z "$expected" ]] && return 1
    local actual
    if command -v sha256sum >/dev/null 2>&1; then
        actual=$(sha256sum "$file" | cut -d' ' -f1)
    elif command -v shasum >/dev/null 2>&1; then
        actual=$(shasum -a 256 "$file" | cut -d' ' -f1)
    else
        warn "No sha256sum or shasum — skipping verification"
        return 0
    fi
    [[ "$actual" == "$expected" ]]
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

install_aishore() {
    log "Installing aishore to $INSTALL_DIR..."
    echo ""

    # Resolve latest release tag
    resolve_tag

    # Fetch checksums manifest and discover files
    log "Fetching file manifest..."
    CHECKSUMS_CONTENT=$(_fetch_repo_file ".aishore/checksums.sha256") || \
        die "Failed to fetch checksums manifest"
    local file_list
    file_list=$(discover_files)
    while IFS= read -r f; do
        FILES+=("$f")
    done <<< "$file_list"

    # Stage all files to temp dir, verify, then install atomically
    STAGING_DIR=$(mktemp -d)
    trap 'rm -rf "$STAGING_DIR"' EXIT

    for file in "${FILES[@]}"; do
        mkdir -p "$STAGING_DIR/$(dirname "$file")"
    done

    # Download and verify in staging
    local failed=0
    local total=${#FILES[@]}
    local fetched=0
    for file in "${FILES[@]}"; do
        local dest="$STAGING_DIR/$file"
        if _fetch_repo_file_to "$file" "$dest"; then
            if ! verify_file "$dest" "$file"; then
                error "Checksum mismatch: $file"
                ((failed++))
            fi
        else
            error "Failed to download $file"
            ((failed++))
        fi
        ((fetched++)) || true
        printf "\r  Downloading... [%d/%d]" "$fetched" "$total"
    done
    printf "\r%40s\r" ""  # clear progress line

    if [[ $failed -gt 0 ]]; then
        die "$failed files failed — nothing was installed"
    fi

    # All verified — install
    mkdir -p "$AISHORE_DIR/data/logs" "$AISHORE_DIR/data/status"
    echo "Installed:"
    for file in "${FILES[@]}"; do
        mkdir -p "$(dirname "$INSTALL_DIR/$file")"
        mv "$STAGING_DIR/$file" "$INSTALL_DIR/$file"
        success "$file"
    done
    chmod +x "$AISHORE_DIR/aishore"
    touch "$AISHORE_DIR/data/logs/.gitkeep"
    touch "$AISHORE_DIR/data/status/.gitkeep"
    echo ""
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
        echo "  .aishore/aishore status    # Backlog overview"
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
        if [[ "$FORCE" == "true" ]]; then
            warn "Reinstalling over existing aishore at $AISHORE_DIR"
        else
            warn "aishore already installed at $AISHORE_DIR"
            echo ""
            echo "To update:"
            echo "  cd $INSTALL_DIR && .aishore/aishore update"
            echo ""
            echo "To reinstall (preserves config.yaml and backlog/):"
            echo "  curl -sSL https://raw.githubusercontent.com/$REPO/main/install.sh | bash -s -- --force"
            exit 0
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
