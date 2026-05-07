#!/usr/bin/env bash
#
# Generate a plugin from the template into a timestamped output directory.
#
# Usage:
#   ./scripts/try-locally.sh                  # interactive, defaults to .out/<timestamp>/
#   ./scripts/try-locally.sh MyPlugin          # specify plugin name (still timestamped)
#   ./scripts/try-locally.sh --defaults        # non-interactive, all defaults
#   ./scripts/try-locally.sh --keep            # do not delete previous .out/<latest>
#   ./scripts/try-locally.sh --open            # open the result in $EDITOR after generation
#   ./scripts/try-locally.sh --clean           # remove the entire .out/ directory and exit
#
# Output directory layout:
#   .out/
#   ├── 2026-05-07_14-23-05_MyPlugin/      ← timestamped run
#   ├── 2026-05-07_15-12-44_MyPlugin/
#   └── latest -> 2026-05-07_15-12-44_MyPlugin   (symlink to most recent)
#
# The .out/ directory is gitignored.

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
readonly OUT_DIR="${REPO_ROOT}/.out"

# ANSI colors for nicer output. Disabled if stdout is not a TTY.
if [[ -t 1 ]]; then
    readonly C_RESET=$'\033[0m'
    readonly C_BOLD=$'\033[1m'
    readonly C_DIM=$'\033[2m'
    readonly C_BLUE=$'\033[34m'
    readonly C_GREEN=$'\033[32m'
    readonly C_YELLOW=$'\033[33m'
    readonly C_RED=$'\033[31m'
else
    readonly C_RESET=""
    readonly C_BOLD=""
    readonly C_DIM=""
    readonly C_BLUE=""
    readonly C_GREEN=""
    readonly C_YELLOW=""
    readonly C_RED=""
fi

log() { echo "${C_BLUE}▶${C_RESET} $*"; }
ok() { echo "${C_GREEN}✓${C_RESET} $*"; }
warn() { echo "${C_YELLOW}⚠${C_RESET} $*" >&2; }
err() { echo "${C_RED}✗${C_RESET} $*" >&2; }

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

USE_DEFAULTS=false
KEEP_PREVIOUS=false
OPEN_RESULT=false
CLEAN_ONLY=false
PLUGIN_NAME=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --defaults)  USE_DEFAULTS=true; shift ;;
        --keep)      KEEP_PREVIOUS=true; shift ;;
        --open)      OPEN_RESULT=true; shift ;;
        --clean)     CLEAN_ONLY=true; shift ;;
        -h|--help)
            sed -n '2,21p' "$0" | sed 's/^# \{0,1\}//'
            exit 0
            ;;
        --*)
            err "Unknown flag: $1"
            echo "Run with --help for usage." >&2
            exit 1
            ;;
        *)
            if [[ -n "${PLUGIN_NAME}" ]]; then
                err "Multiple plugin names given: ${PLUGIN_NAME} and $1"
                exit 1
            fi
            PLUGIN_NAME="$1"
            shift
            ;;
    esac
done

# ---------------------------------------------------------------------------
# --clean: nuke the whole output dir and exit
# ---------------------------------------------------------------------------

if [[ "${CLEAN_ONLY}" == true ]]; then
    if [[ -d "${OUT_DIR}" ]]; then
        log "Removing ${OUT_DIR}"
        rm -rf "${OUT_DIR}"
        ok "Output directory cleaned."
    else
        ok "Nothing to clean — ${OUT_DIR} does not exist."
    fi
    exit 0
fi

# ---------------------------------------------------------------------------
# Tool checks
# ---------------------------------------------------------------------------

if ! command -v copier >/dev/null 2>&1; then
    err "copier is not installed."
    echo "" >&2
    echo "  Install it with one of:" >&2
    echo "    pipx install copier" >&2
    echo "    pip install --user copier" >&2
    echo "" >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# Compute output path
# ---------------------------------------------------------------------------

readonly TIMESTAMP="$(date +'%Y-%m-%d_%H-%M-%S')"
readonly DEFAULT_PLUGIN_NAME="ExamplePlugin"
readonly EFFECTIVE_NAME="${PLUGIN_NAME:-${DEFAULT_PLUGIN_NAME}}"
readonly RUN_DIR="${OUT_DIR}/${TIMESTAMP}_${EFFECTIVE_NAME}"
readonly OUTPUT_PATH="${RUN_DIR}/${EFFECTIVE_NAME}"

mkdir -p "${OUT_DIR}"

# ---------------------------------------------------------------------------
# Optional: clean older runs (keep only the latest 4 unless --keep)
# After a fresh run is added, exactly 5 directories remain.
# ---------------------------------------------------------------------------

if [[ "${KEEP_PREVIOUS}" == false ]]; then
    runs=( "${OUT_DIR}"/*/ )
    if [[ ${#runs[@]} -gt 4 ]] && [[ -d "${runs[0]}" ]]; then
        old_runs="$(ls -1tdr "${OUT_DIR}"/*/ 2>/dev/null | head -n -4 || true)"
        if [[ -n "${old_runs}" ]]; then
            log "Pruning old runs (keeping 5 total after this run)"
            while IFS= read -r old; do
                [[ "$(basename "${old%/}")" == "latest" ]] && continue
                echo "  ${C_DIM}removing $(basename "${old%/}")${C_RESET}"
                rm -rf "${old}"
            done <<< "${old_runs}"
        fi
    fi
fi

# ---------------------------------------------------------------------------
# Generate
# ---------------------------------------------------------------------------

log "Generating into ${C_BOLD}${OUTPUT_PATH#${REPO_ROOT}/}${C_RESET}"
echo ""

copier_args=("copy" "--trust")

if [[ "${USE_DEFAULTS}" == true ]]; then
    copier_args+=("--defaults")
    if [[ -n "${PLUGIN_NAME}" ]]; then
        copier_args+=("--data" "plugin_name=${PLUGIN_NAME}")
    fi
fi

copier_args+=("${REPO_ROOT}" "${OUTPUT_PATH}")

if ! copier "${copier_args[@]}"; then
    err "copier failed — see output above."
    rmdir "${RUN_DIR}" 2>/dev/null || true
    exit 1
fi

# Update the `latest` symlink with a relative target.
ln -sfn "${TIMESTAMP}_${EFFECTIVE_NAME}" "${OUT_DIR}/latest"

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

echo ""
ok "Generated: ${C_BOLD}${OUTPUT_PATH}${C_RESET}"
echo ""
echo "${C_DIM}File tree:${C_RESET}"
if command -v tree >/dev/null 2>&1; then
    tree -a -I 'vendor|node_modules' --noreport "${OUTPUT_PATH}" | sed 's/^/  /'
else
    (cd "${OUTPUT_PATH}" && find . -type f -not -path '*/\.*/*' | sort | sed 's|^\./|  |')
fi

echo ""
echo "${C_DIM}Quick links:${C_RESET}"
echo "  cd ${OUTPUT_PATH#${REPO_ROOT}/}"
echo "  ${OUT_DIR#${REPO_ROOT}/}/latest -> ${TIMESTAMP}_${EFFECTIVE_NAME}"
echo ""

# ---------------------------------------------------------------------------
# Optional: open in editor
# ---------------------------------------------------------------------------

if [[ "${OPEN_RESULT}" == true ]]; then
    if [[ -n "${EDITOR:-}" ]]; then
        log "Opening in \$EDITOR (${EDITOR})"
        "${EDITOR}" "${OUTPUT_PATH}"
    elif command -v code >/dev/null 2>&1; then
        log "Opening in VS Code"
        code "${OUTPUT_PATH}"
    elif command -v phpstorm >/dev/null 2>&1; then
        log "Opening in PhpStorm"
        phpstorm "${OUTPUT_PATH}"
    else
        warn "No editor found. Set \$EDITOR or install code/phpstorm."
    fi
fi