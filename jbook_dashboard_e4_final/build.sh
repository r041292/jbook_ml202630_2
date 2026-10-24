#!/usr/bin/env bash
# Build local estricto del informe E4 con la ruta base de GitHub Pages.
# MSYS2_ENV_CONV_EXCL evita que Git Bash convierta BASE_URL en una ruta de Windows.
# Falla si MyST informa cualquier error (⛔) o advertencia (⚠️), además del código de salida.
cd "$(dirname "$0")"
log=$(MSYS2_ENV_CONV_EXCL=BASE_URL BASE_URL=/jbook_ml202630_2/e4_final \
      ../Precalculo/venv/Scripts/jupyter-book.exe build --html --strict 2>&1)
status=$?
echo "$log" | grep -v -E "npm notice|GET |^$|DeprecationWarning|node --trace"
if echo "$log" | grep -q -E "⛔|⚠️"; then
  echo "BUILD CON ERRORES O ADVERTENCIAS"; exit 1
fi
exit $status
