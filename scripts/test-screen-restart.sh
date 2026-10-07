#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p .build/tests
clang -std=c11 -Wall -Wextra -Werror -fsanitize=address,undefined \
  tests/screen_restart_test.c -o .build/tests/screen_restart_test
.build/tests/screen_restart_test
