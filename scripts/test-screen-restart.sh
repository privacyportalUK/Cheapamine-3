#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 - <<'PY'
from pathlib import Path
version = Path('BaseBin/_external/basebin/.version').read_bytes()
# basebin_gen.m puts DOPA + the raw version + NUL into a 16-byte LC_UUID.
# This exercises the actual build input, including accidental trailing newlines.
assert version and b'\0' not in version, 'Invalid basebin version marker'
assert version == version.strip(), 'Version marker must have no surrounding whitespace'
assert len(b'DOPA' + version + b'\0') <= 16, 'Basebin version exceeds dyld LC_UUID capacity'
print('Basebin version fits the dyld UUID field.')
PY
mkdir -p .build/tests
clang -std=c11 -Wall -Wextra -Werror -fsanitize=address,undefined \
  tests/screen_restart_test.c -o .build/tests/screen_restart_test
.build/tests/screen_restart_test
