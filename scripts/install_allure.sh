#!/usr/bin/env bash
# Устанавливает Allure CLI из кэша GitHub Actions или скачивает.
# Требует Java 17+ (actions/setup-java).
set -euo pipefail

ALLURE_VERSION="${ALLURE_VERSION:-2.46.1}"
CACHE_DIR="${ALLURE_HOME:-$HOME/.cache/allure}"
INSTALL_DIR="$CACHE_DIR/allure-$ALLURE_VERSION"
TARGET="/usr/local/bin/allure"

if [ -x "$TARGET" ] && allure --version 2>/dev/null | grep -q "$ALLURE_VERSION"; then
  echo "Allure $ALLURE_VERSION уже установлен"
  exit 0
fi

if [ ! -x "$INSTALL_DIR/bin/allure" ]; then
  mkdir -p "$CACHE_DIR"
  echo "Скачиваем Allure $ALLURE_VERSION"
  curl -fsSL -o "$CACHE_DIR/allure.zip" \
    "https://github.com/allure-framework/allure2/releases/download/${ALLURE_VERSION}/allure-${ALLURE_VERSION}.zip"
  unzip -q -o "$CACHE_DIR/allure.zip" -d "$CACHE_DIR"
fi

sudo ln -sf "$INSTALL_DIR/bin/allure" "$TARGET"
allure --version
