#!/bin/bash
# migrate.sh - Upgrade aishore installations to latest structure
#
# Usage: ./migrate.sh [options] [project-path]
#
# Options:
#   --dry-run    Show what would be changed without making changes
#   --force      Skip confirmation prompts
#
# Handles two migration scenarios:
#   1. Legacy aishore/ → .aishore/ + backlog/
#   2. Old .aishore/plan/ → backlog/ (latest structure)
#
# The new structure separates tool from user content:
#   .aishore/     - Tool (can be updated/replaced)
#   backlog/      - User content (preserved during updates)

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
DIM='\033[2m'
NC='\033[0m'

log()     { echo -e "${BLUE}[migrate]${NC} $1"; }
success() { echo -e "${GREEN}✓${NC} $1"; }
warn()    { echo -e "${YELLOW}⚠${NC} $1"; }
error()   { echo -e "${RED}✗${NC} $1"; }
dry()     { echo -e "${CYAN}[dry-run]${NC} $1"; }
would()   { echo -e "  ${DIM}→${NC} $1"; }

# ============================================================================
# CONFIGURATION
# ============================================================================

DRY_RUN=false
FORCE=false
PROJECT_ROOT=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        -*)
            error "Unknown option: $1"
            echo "Usage: $0 [--dry-run] [--force] [project-path]"
            exit 1
            ;;
        *)
            PROJECT_ROOT="$1"
            shift
            ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="${PROJECT_ROOT:-.}"
PROJECT_ROOT="$(cd "$PROJECT_ROOT" && pwd)"

LEGACY_DIR="$PROJECT_ROOT/aishore"       # Very old: aishore/
OLD_DIR="$PROJECT_ROOT/.aishore"          # Old: .aishore/plan/
BACKLOG_DIR="$PROJECT_ROOT/backlog"       # New: backlog/

# ============================================================================
# DRY-RUN HELPERS
# ============================================================================

# Safe mkdir - respects dry-run
do_mkdir() {
    local dir="$1"
    if [[ "$DRY_RUN" == "true" ]]; then
        if [[ ! -d "$dir" ]]; then
            would "mkdir -p $dir"
        fi
    else
        mkdir -p "$dir"
    fi
}

# Safe copy - respects dry-run
do_copy() {
    local src="$1"
    local dest="$2"
    if [[ "$DRY_RUN" == "true" ]]; then
        would "cp $src → $dest"
    else
        cp "$src" "$dest"
    fi
}

# Safe remove - respects dry-run
do_remove() {
    local path="$1"
    if [[ "$DRY_RUN" == "true" ]]; then
        would "rm -rf $path"
    else
        rm -rf "$path"
    fi
}

# Safe touch - respects dry-run
do_touch() {
    local file="$1"
    if [[ "$DRY_RUN" == "true" ]]; then
        would "touch $file"
    else
        touch "$file"
    fi
}

# Safe chmod - respects dry-run
do_chmod() {
    local mode="$1"
    local file="$2"
    if [[ "$DRY_RUN" == "true" ]]; then
        would "chmod $mode $file"
    else
        chmod "$mode" "$file"
    fi
}

# Safe write - respects dry-run
do_write() {
    local file="$1"
    local content="$2"
    if [[ "$DRY_RUN" == "true" ]]; then
        would "write $file ($(echo "$content" | wc -l | tr -d ' ') lines)"
    else
        echo "$content" > "$file"
    fi
}

# Safe append - respects dry-run
do_append() {
    local file="$1"
    local content="$2"
    if [[ "$DRY_RUN" == "true" ]]; then
        would "append to $file"
    else
        echo "$content" >> "$file"
    fi
}

# ============================================================================
# DETECTION
# ============================================================================

# Scenario 1: Legacy aishore/ (non-hidden) structure
detect_legacy_structure() {
    if [[ -d "$LEGACY_DIR" ]]; then
        if [[ -d "$LEGACY_DIR/bin" ]] || [[ -f "$LEGACY_DIR/bin/aishore.sh" ]]; then
            return 0
        fi
        if [[ -d "$LEGACY_DIR/plan" ]] && [[ -f "$LEGACY_DIR/plan/backlog.json" ]]; then
            return 0
        fi
    fi
    return 1
}

# Scenario 2: Old .aishore/plan/ structure (backlog inside .aishore)
detect_old_aishore_structure() {
    if [[ -d "$OLD_DIR/plan" ]] && [[ -f "$OLD_DIR/plan/backlog.json" ]]; then
        # Check that backlog/ doesn't already exist at project root
        if [[ ! -d "$BACKLOG_DIR" ]]; then
            return 0
        fi
    fi
    return 1
}

# Already migrated to latest
detect_current_structure() {
    if [[ -d "$BACKLOG_DIR" ]] && [[ -f "$BACKLOG_DIR/backlog.json" ]]; then
        return 0
    fi
    return 1
}

detect_validation_command() {
    # Check package.json for common patterns
    if [[ -f "$PROJECT_ROOT/package.json" ]]; then
        if grep -q '"type-check"' "$PROJECT_ROOT/package.json" 2>/dev/null; then
            echo "npm run type-check && npm run lint && npm test"
            return 0
        fi
        if grep -q '"test"' "$PROJECT_ROOT/package.json" 2>/dev/null; then
            echo "npm test"
            return 0
        fi
    fi

    # Check for Python
    if [[ -f "$PROJECT_ROOT/pyproject.toml" ]] || [[ -f "$PROJECT_ROOT/setup.py" ]]; then
        echo "pytest"
        return 0
    fi

    # Check for Go
    if [[ -f "$PROJECT_ROOT/go.mod" ]]; then
        echo "go test ./..."
        return 0
    fi

    # Default
    echo "echo 'Configure validation in .aishore/config.yaml'"
}

# ============================================================================
# MIGRATION: OLD .aishore/plan/ → backlog/
# ============================================================================

migrate_plan_to_backlog() {
    log "Migrating .aishore/plan/ to backlog/..."

    # Create backlog directory
    do_mkdir "$BACKLOG_DIR/archive"

    # Move backlog files
    for file in backlog.json bugs.json icebox.json sprint.json definitions.md; do
        if [[ -f "$OLD_DIR/plan/$file" ]]; then
            do_copy "$OLD_DIR/plan/$file" "$BACKLOG_DIR/$file"
            success "Migrated $file"
        fi
    done

    # Move archive contents
    if [[ -d "$OLD_DIR/plan/archive" ]]; then
        for file in "$OLD_DIR/plan/archive"/*; do
            if [[ -f "$file" ]]; then
                do_copy "$file" "$BACKLOG_DIR/archive/"
                success "Migrated archive/$(basename "$file")"
            fi
        done
    fi

    # Create archive .gitkeep
    do_touch "$BACKLOG_DIR/archive/.gitkeep"

    success "Backlog migrated to $BACKLOG_DIR/"
}

remove_old_directories() {
    log "Cleaning up old structure..."

    # Remove lib/ (now inlined)
    if [[ -d "$OLD_DIR/lib" ]]; then
        do_remove "$OLD_DIR/lib"
        success "Removed .aishore/lib/ (now inlined)"
    fi

    # Remove context/ (now auto-detected)
    if [[ -d "$OLD_DIR/context" ]]; then
        do_remove "$OLD_DIR/context"
        success "Removed .aishore/context/ (CLAUDE.md auto-detected)"
    fi

    # Remove old plan/ after successful migration
    if [[ -d "$OLD_DIR/plan" ]] && [[ -d "$BACKLOG_DIR" || "$DRY_RUN" == "true" ]]; then
        do_remove "$OLD_DIR/plan"
        success "Removed .aishore/plan/ (migrated to backlog/)"
    fi
}

update_aishore_cli() {
    log "Updating aishore CLI..."

    if [[ -f "$SCRIPT_DIR/.aishore/aishore" ]]; then
        do_copy "$SCRIPT_DIR/.aishore/aishore" "$OLD_DIR/aishore"
        do_chmod "+x" "$OLD_DIR/aishore"
        success "CLI updated to latest version"
    else
        warn "Source CLI not found - update manually from upstream"
    fi
}

update_agents() {
    log "Updating agent prompts..."

    if [[ -d "$SCRIPT_DIR/.aishore/agents" ]]; then
        if [[ "$DRY_RUN" == "true" ]]; then
            for agent in "$SCRIPT_DIR/.aishore/agents/"*.md; do
                would "cp $(basename "$agent") → .aishore/agents/"
            done
        else
            cp "$SCRIPT_DIR/.aishore/agents/"*.md "$OLD_DIR/agents/" 2>/dev/null || true
        fi
        success "Agent prompts updated"
    else
        warn "Source agents not found - update manually from upstream"
    fi
}

update_gitignore_for_backlog() {
    log "Updating .gitignore..."

    local gitignore="$PROJECT_ROOT/.gitignore"

    if [[ -f "$gitignore" ]]; then
        # Remove old .aishore/plan entries if present
        if grep -q ".aishore/plan" "$gitignore" 2>/dev/null; then
            # Don't auto-modify, just warn
            warn ".gitignore has old .aishore/plan entries - review manually"
        fi

        # Add backlog archive entry if not present
        if ! grep -q ".aishore/data/logs/" "$gitignore" 2>/dev/null; then
            local content=$'\n# aishore runtime (v0.1.2+)\n.aishore/data/logs/\n.aishore/data/status/'
            do_append "$gitignore" "$content"
            success "Added runtime entries to .gitignore"
        fi
    fi
}

# ============================================================================
# MIGRATION: LEGACY aishore/ → .aishore/ + backlog/
# ============================================================================

migrate_from_legacy() {
    log "Migrating from legacy aishore/ structure..."

    # Create new .aishore structure
    do_mkdir "$OLD_DIR/agents"
    do_mkdir "$OLD_DIR/data/archive"
    do_mkdir "$OLD_DIR/data/logs"
    do_mkdir "$OLD_DIR/data/status"

    # Copy new CLI
    if [[ -f "$SCRIPT_DIR/.aishore/aishore" ]]; then
        do_copy "$SCRIPT_DIR/.aishore/aishore" "$OLD_DIR/aishore"
        do_chmod "+x" "$OLD_DIR/aishore"
        success "CLI installed"
    fi

    # Copy agents
    if [[ -d "$SCRIPT_DIR/.aishore/agents" ]]; then
        if [[ "$DRY_RUN" == "true" ]]; then
            for agent in "$SCRIPT_DIR/.aishore/agents/"*.md; do
                would "cp $(basename "$agent") → .aishore/agents/"
            done
        else
            cp "$SCRIPT_DIR/.aishore/agents/"*.md "$OLD_DIR/agents/" 2>/dev/null || true
        fi
        success "Agent prompts installed"
    fi

    # Create backlog directory
    do_mkdir "$BACKLOG_DIR/archive"

    # Migrate plan files from legacy location
    for file in backlog.json bugs.json icebox.json sprint.json definitions.md; do
        if [[ -f "$LEGACY_DIR/plan/$file" ]]; then
            do_copy "$LEGACY_DIR/plan/$file" "$BACKLOG_DIR/$file"
            success "Migrated $file"
        fi
    done

    # Migrate archives
    for file in done.jsonl sprints.jsonl failed.jsonl; do
        if [[ -f "$LEGACY_DIR/plan/archive/$file" ]]; then
            do_copy "$LEGACY_DIR/plan/archive/$file" "$OLD_DIR/data/archive/$file"
            success "Migrated archive/$file"
        elif [[ -f "$LEGACY_DIR/plan/.archive/$file" ]]; then
            do_copy "$LEGACY_DIR/plan/.archive/$file" "$OLD_DIR/data/archive/$file"
            success "Migrated .archive/$file"
        fi
    done

    # Create .gitkeep files
    do_touch "$OLD_DIR/data/archive/.gitkeep"
    do_touch "$OLD_DIR/data/logs/.gitkeep"
    do_touch "$OLD_DIR/data/status/.gitkeep"
    do_touch "$BACKLOG_DIR/archive/.gitkeep"

    # Create config.yaml if it doesn't exist
    if [[ ! -f "$OLD_DIR/config.yaml" ]]; then
        local validate_cmd
        validate_cmd=$(detect_validation_command)

        local config_content="# aishore configuration (optional - defaults are sensible)

validation:
  command: \"$validate_cmd\"
  timeout: 120

models:
  primary: \"claude-opus-4-5-20251101\"
  fast: \"claude-sonnet-4-20250514\"

agent:
  timeout: 3600"

        if [[ "$DRY_RUN" == "true" ]]; then
            would "write .aishore/config.yaml"
        else
            echo "$config_content" > "$OLD_DIR/config.yaml"
        fi
        success "Created config.yaml"
    fi

    success "Legacy migration complete"
}

# ============================================================================
# SUMMARY
# ============================================================================

show_summary() {
    echo ""
    log "Migration complete!"
    echo ""
    echo "New structure:"
    echo "  your-project/"
    echo "  ├── backlog/            # YOUR CONTENT (version controlled)"
    echo "  │   ├── backlog.json"
    echo "  │   ├── bugs.json"
    echo "  │   ├── sprint.json"
    echo "  │   └── archive/"
    echo "  ├── CLAUDE.md           # Auto-detected"
    echo "  └── .aishore/           # TOOL (can be updated)"
    echo "      ├── aishore"
    echo "      ├── agents/"
    echo "      ├── config.yaml"
    echo "      └── data/"
    echo ""
    echo "Test the migration:"
    echo "  .aishore/aishore help"
    echo "  .aishore/aishore metrics"
    echo ""

    if [[ -d "$LEGACY_DIR" ]]; then
        warn "Old aishore/ directory still exists"
        echo "After verifying migration works: rm -rf aishore/"
    fi

    if [[ -d "$OLD_DIR/plan" ]]; then
        warn "Old .aishore/plan/ directory still exists"
        echo "After verifying migration works: rm -rf .aishore/plan/"
    fi
}

# ============================================================================
# MAIN
# ============================================================================

analyze_current_state() {
    echo "Current state:"
    echo ""

    # Check .aishore contents
    if [[ -d "$OLD_DIR" ]]; then
        echo "  .aishore/"
        [[ -f "$OLD_DIR/aishore" ]] && echo "    ├── aishore (CLI)"
        [[ -d "$OLD_DIR/agents" ]] && echo "    ├── agents/"
        [[ -f "$OLD_DIR/config.yaml" ]] && echo "    ├── config.yaml"
        [[ -d "$OLD_DIR/context" ]] && echo -e "    ├── context/ ${YELLOW}← will remove${NC}"
        [[ -d "$OLD_DIR/lib" ]] && echo -e "    ├── lib/ ${YELLOW}← will remove${NC}"
        [[ -d "$OLD_DIR/plan" ]] && echo -e "    ├── plan/ ${YELLOW}← will move to backlog/${NC}"
        [[ -d "$OLD_DIR/data" ]] && echo "    └── data/"
    fi

    # Check legacy aishore/
    if [[ -d "$LEGACY_DIR" ]]; then
        echo "  aishore/ (legacy)"
        [[ -d "$LEGACY_DIR/plan" ]] && echo -e "    └── plan/ ${YELLOW}← will move to backlog/${NC}"
    fi

    # Check backlog
    if [[ -d "$BACKLOG_DIR" ]]; then
        echo "  backlog/ (already exists)"
    else
        echo -e "  backlog/ ${GREEN}← will create${NC}"
    fi

    # Check CLAUDE.md
    if [[ -f "$PROJECT_ROOT/CLAUDE.md" ]]; then
        echo "  CLAUDE.md (auto-detected)"
    fi

    echo ""
}

show_dry_run_summary() {
    echo ""
    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${CYAN}════════════════════════════════════════${NC}"
        echo -e "${CYAN}  DRY RUN COMPLETE - No changes made${NC}"
        echo -e "${CYAN}════════════════════════════════════════${NC}"
        echo ""
        echo "To apply these changes, run:"
        echo "  $0 $PROJECT_ROOT"
        echo ""
    fi
}

main() {
    echo ""
    echo -e "${BLUE}════════════════════════════════════════${NC}"
    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${BLUE}  aishore Migration Tool ${CYAN}(DRY RUN)${NC}"
    else
        echo -e "${BLUE}  aishore Migration Tool (v0.1.2)${NC}"
    fi
    echo -e "${BLUE}════════════════════════════════════════${NC}"
    echo ""
    echo "Project: $PROJECT_ROOT"
    if [[ "$DRY_RUN" == "true" ]]; then
        echo -e "${CYAN}Mode: DRY RUN (no changes will be made)${NC}"
    fi
    echo ""

    # Check if already current
    if detect_current_structure; then
        if [[ ! -d "$OLD_DIR/plan" ]] && [[ ! -d "$OLD_DIR/lib" ]] && [[ ! -d "$OLD_DIR/context" ]]; then
            success "Already using latest structure (backlog/ at project root)"
            echo ""
            echo "To update aishore CLI:"
            echo "  cp $SCRIPT_DIR/.aishore/aishore $OLD_DIR/aishore"
            exit 0
        fi
    fi

    # Scenario 1: Legacy aishore/ (non-hidden)
    if detect_legacy_structure; then
        success "Found legacy aishore/ structure"
        echo ""

        if [[ "$DRY_RUN" == "true" ]]; then
            analyze_current_state
            dry "Showing what would be changed..."
            echo ""
        elif [[ "$FORCE" != "true" ]]; then
            read -p "Migrate to new structure (.aishore/ + backlog/)? [Y/n] " response
            if [[ "$response" =~ ^[Nn]$ ]]; then
                echo "Aborted"
                exit 0
            fi
            echo ""
        fi

        migrate_from_legacy
        update_gitignore_for_backlog

        if [[ "$DRY_RUN" == "true" ]]; then
            show_dry_run_summary
        else
            show_summary
        fi
        exit 0
    fi

    # Scenario 2: Old .aishore/plan/ structure
    if detect_old_aishore_structure; then
        success "Found old .aishore/plan/ structure"
        echo ""

        if [[ "$DRY_RUN" == "true" ]]; then
            analyze_current_state
            dry "Showing what would be changed..."
            echo ""
            echo "Changes planned:"
            echo "  1. Move .aishore/plan/* to backlog/"
            echo "  2. Remove .aishore/lib/ (now inlined)"
            echo "  3. Remove .aishore/context/ (auto-detects CLAUDE.md)"
            echo "  4. Update CLI and agents"
            echo ""
        elif [[ "$FORCE" != "true" ]]; then
            echo "This will:"
            echo "  1. Move .aishore/plan/* to backlog/"
            echo "  2. Remove .aishore/lib/ (now inlined)"
            echo "  3. Remove .aishore/context/ (auto-detects CLAUDE.md)"
            echo "  4. Update CLI and agents"
            echo ""
            read -p "Proceed with migration? [Y/n] " response
            if [[ "$response" =~ ^[Nn]$ ]]; then
                echo "Aborted"
                exit 0
            fi
            echo ""
        fi

        migrate_plan_to_backlog
        update_aishore_cli
        update_agents
        remove_old_directories
        update_gitignore_for_backlog

        if [[ "$DRY_RUN" == "true" ]]; then
            show_dry_run_summary
        else
            show_summary
        fi
        exit 0
    fi

    # No migratable structure found
    error "No migratable structure found"
    echo ""
    echo "Expected one of:"
    echo "  - aishore/plan/backlog.json (legacy)"
    echo "  - .aishore/plan/backlog.json (old)"
    echo ""
    echo "For fresh install:"
    echo "  curl -sSL https://raw.githubusercontent.com/simonplant/aishore/main/install.sh | bash"
    exit 1
}

main
