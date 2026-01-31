#!/bin/bash
# sync_to_public.sh
#
# Syncs selected files from the private TEA-Taylor-Series-Chapter repo
# to the public TEA-AI-Calculus-Code repo for Overleaf and reproducibility.
#
# Usage: ./sync_to_public.sh [--dry-run] [--push]
#   --dry-run  Show what would be copied without actually copying
#   --push     Commit and push changes to GitHub after syncing

set -e

# Paths
PRIVATE_REPO="/home/todd/TEA-repos/TEA-Taylor-Series-Chapter"
PUBLIC_REPO="/home/todd/TEA-repos/TEA-Taylor-Series-Paper"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

DRY_RUN=false
PUSH=false

# Parse arguments
for arg in "$@"; do
    case $arg in
        --dry-run) DRY_RUN=true ;;
        --push) PUSH=true ;;
    esac
done

echo "========================================"
echo "Syncing Private → Public Repository"
echo "========================================"
echo "From: $PRIVATE_REPO"
echo "To:   $PUBLIC_REPO"
if $DRY_RUN; then
    echo -e "${YELLOW}DRY RUN - no files will be changed${NC}"
fi
echo ""

# Rsync options
RSYNC_OPTS="-av --delete"
if $DRY_RUN; then
    RSYNC_OPTS="$RSYNC_OPTS --dry-run"
fi

# ============================================
# 1. MANUSCRIPT (for Overleaf)
# ============================================
echo -e "${GREEN}[1/4] Syncing Manuscript...${NC}"
mkdir -p "$PUBLIC_REPO/Manuscript"
rsync $RSYNC_OPTS \
    --include='*.tex' \
    --include='*.bib' \
    --include='*.pdf' \
    --include='*.png' \
    --include='*.jpg' \
    --include='*.eps' \
    --include='figures/***' \
    --exclude='*.backup*' \
    --exclude='*.bak' \
    --exclude='*.aux' \
    --exclude='*.log' \
    --exclude='*.out' \
    --exclude='*.synctex*' \
    --exclude='*.fls' \
    --exclude='*.fdb_latexmk' \
    --exclude='current.txt' \
    --exclude='test.*' \
    --exclude='Student Handout/' \
    "$PRIVATE_REPO/Manuscript/" "$PUBLIC_REPO/Manuscript/"

# ============================================
# 2. SCRIPTS (for reproducibility - Python only)
# ============================================
echo -e "${GREEN}[2/4] Syncing Scripts...${NC}"
mkdir -p "$PUBLIC_REPO/Scripts"

# Copy only specific Python scripts (not data files)
SCRIPTS=(
    "pk_screen_v2_2.py"
    "pkwap_analyzer.py"
    "analyze_pkwap_memos.py"
    "select_anchor_transcripts.py"
    "process_anchor_cases.py"
    "validate_counting.py"
    "reconcile_counts.py"
    "review_candidates.py"
    "transcript_reviewer.py"
    "test_all_calibration.py"
    "test_comprehensive_count.py"
    "test_flipped_count.py"
    "recount_from_annot.py"
)

for script in "${SCRIPTS[@]}"; do
    if [ -f "$PRIVATE_REPO/Analysis/Scripts/$script" ]; then
        if $DRY_RUN; then
            echo "  Would copy: $script"
        else
            cp "$PRIVATE_REPO/Analysis/Scripts/$script" "$PUBLIC_REPO/Scripts/"
            echo "  Copied: $script"
        fi
    fi
done

# ============================================
# 3. TEMPLATES
# ============================================
echo -e "${GREEN}[3/4] Syncing Templates...${NC}"
mkdir -p "$PUBLIC_REPO/Templates"
# Copy PK-WAP template if it exists
if [ -d "$PRIVATE_REPO/Analysis/PK-WAP Memos" ]; then
    find "$PRIVATE_REPO/Analysis/PK-WAP Memos" -name "*TEMPLATE*" -exec cp {} "$PUBLIC_REPO/Templates/" \; 2>/dev/null || true
fi

# ============================================
# 4. DOCUMENTATION (add, don't delete existing)
# ============================================
echo -e "${GREEN}[4/4] Syncing Documentation...${NC}"
mkdir -p "$PUBLIC_REPO/Documentation"

# Copy markdown files from private Documentation (without deleting existing)
if $DRY_RUN; then
    echo "  Would copy .md files from Documentation/"
    ls "$PRIVATE_REPO/Documentation/"*.md 2>/dev/null || echo "  (no .md files found)"
else
    cp "$PRIVATE_REPO/Documentation/"*.md "$PUBLIC_REPO/Documentation/" 2>/dev/null || true
    echo "  Copied documentation files"
fi

# ============================================
# Summary
# ============================================
echo ""
echo "========================================"
echo "Sync complete!"
echo "========================================"

# Show what changed
cd "$PUBLIC_REPO"
echo ""
echo "Changes in public repo:"
git status --short

# Count files
echo ""
echo "File counts in public repo:"
find . -type f -not -path './.git/*' | wc -l | xargs echo "  Total files:"

# Push if requested
if $PUSH && ! $DRY_RUN; then
    echo ""
    echo -e "${GREEN}Committing and pushing changes...${NC}"
    git add -A
    git commit -m "Sync from private repo $(date +%Y-%m-%d)" || echo "Nothing to commit"
    git push
    echo -e "${GREEN}Pushed to GitHub!${NC}"
elif $PUSH && $DRY_RUN; then
    echo ""
    echo -e "${YELLOW}Would commit and push (dry run)${NC}"
fi

echo ""
echo "To commit manually:"
echo "  cd $PUBLIC_REPO"
echo "  git add -A && git commit -m 'Sync updates' && git push"
