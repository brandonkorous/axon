#!/usr/bin/env sh
# Axon CLI Installer
# Usage: curl -sS https://get.useaxon.dev | sh
#
# Installs the `axon` CLI to /usr/local/bin (or ~/.local/bin as fallback).
# The CLI handles Docker detection, workspace scaffolding, and lifecycle.

set -e

REPO="brandonkorous/axon"
CLI_URL="https://raw.githubusercontent.com/${REPO}/main/cli/axon"
VERSION_URL="https://raw.githubusercontent.com/${REPO}/main/cli/VERSION"

# ── Colors ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

info()  { printf "${CYAN}  ▸${RESET} %s\n" "$1"; }
ok()    { printf "${GREEN}  ✓${RESET} %s\n" "$1"; }
warn()  { printf "${YELLOW}  !${RESET} %s\n" "$1"; }
fail()  { printf "${RED}  ✗${RESET} %s\n" "$1"; exit 1; }

# ── Banner ──────────────────────────────────────────────────────────────────
printf "\n"
printf "${BOLD}${CYAN}"
printf "    ___   _  ______  _   __\n"
printf "   /   | | |/ / __ \/ | / /\n"
printf "  / /| | |   / / / /  |/ / \n"
printf " / ___ |/   / /_/ / /|  /  \n"
printf "/_/  |_/_/|_\____/_/ |_/   \n"
printf "${RESET}\n"
printf "  ${BOLD}Self-hosted AI Command Center${RESET}\n"
printf "  ${CYAN}https://useaxon.dev${RESET}\n\n"

# ── Detect OS & architecture ────────────────────────────────────────────────
detect_platform() {
  OS="$(uname -s)"
  ARCH="$(uname -m)"

  case "$OS" in
    Linux*)  PLATFORM="linux" ;;
    Darwin*) PLATFORM="macos" ;;
    MINGW*|MSYS*|CYGWIN*) PLATFORM="windows" ;;
    *) fail "Unsupported operating system: $OS" ;;
  esac

  case "$ARCH" in
    x86_64|amd64)  ARCH="x64" ;;
    arm64|aarch64) ARCH="arm64" ;;
    *) ARCH="$ARCH" ;;
  esac

  info "Detected platform: ${PLATFORM} (${ARCH})"
}

# ── Find install directory ──────────────────────────────────────────────────
find_install_dir() {
  if [ -w /usr/local/bin ]; then
    INSTALL_DIR="/usr/local/bin"
  elif [ -n "$HOME" ]; then
    INSTALL_DIR="$HOME/.local/bin"
    mkdir -p "$INSTALL_DIR"
    # Check if it's on PATH
    case ":$PATH:" in
      *":$INSTALL_DIR:"*) ;;
      *)
        warn "$INSTALL_DIR is not on your PATH"
        warn "Add this to your shell profile:"
        warn "  export PATH=\"\$HOME/.local/bin:\$PATH\""
        NEEDS_PATH_UPDATE=1
        ;;
    esac
  else
    fail "Cannot determine install directory. Set \$HOME or run with sudo."
  fi
}

# ── Download CLI ────────────────────────────────────────────────────────────
download_cli() {
  info "Downloading Axon CLI..."

  if command -v curl > /dev/null 2>&1; then
    DOWNLOADER="curl -fsSL"
  elif command -v wget > /dev/null 2>&1; then
    DOWNLOADER="wget -qO-"
  else
    fail "Neither curl nor wget found. Install one and retry."
  fi

  $DOWNLOADER "$CLI_URL" > "$INSTALL_DIR/axon" || fail "Download failed"
  chmod +x "$INSTALL_DIR/axon"
  ok "Installed axon to $INSTALL_DIR/axon"
}

# ── Verify installation ────────────────────────────────────────────────────
verify() {
  if command -v axon > /dev/null 2>&1; then
    ok "axon is ready!"
    printf "\n"
    printf "  ${BOLD}Get started:${RESET}\n"
    printf "    ${CYAN}axon init my-workspace${RESET}\n"
    printf "    ${CYAN}cd my-workspace${RESET}\n"
    printf "    ${CYAN}axon start${RESET}\n"
    printf "\n"
  elif [ "$NEEDS_PATH_UPDATE" = "1" ]; then
    warn "Restart your shell or run: export PATH=\"\$HOME/.local/bin:\$PATH\""
    printf "\n"
    printf "  ${BOLD}Then get started:${RESET}\n"
    printf "    ${CYAN}axon init my-workspace${RESET}\n"
    printf "    ${CYAN}cd my-workspace${RESET}\n"
    printf "    ${CYAN}axon start${RESET}\n"
    printf "\n"
  else
    fail "Installation succeeded but 'axon' command not found on PATH"
  fi
}

# ── Main ────────────────────────────────────────────────────────────────────
detect_platform
find_install_dir
download_cli
verify
