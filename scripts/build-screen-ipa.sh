#!/bin/bash
set -euo pipefail
exec bash "$(dirname "$0")/build-package-ipa.sh" "$@"
