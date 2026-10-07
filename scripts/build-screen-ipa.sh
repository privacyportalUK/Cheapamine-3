#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."

xcrun --sdk iphoneos --show-sdk-path
for tool in gmake ldid trustcache dpkg-deb; do
  command -v "$tool" >/dev/null || { echo "Missing build tool: $tool" >&2; exit 1; }
done
: "${THEOS:?Set THEOS to a Theos installation with iPhoneOS16.5.sdk}"

bash scripts/test-screen-restart.sh
git submodule update --init --recursive
(
  cd Application/Dopamine/Resources
  curl -fL --retry 3 https://apt.procurs.us/bootstraps/1800/bootstrap-iphoneos-arm64.tar.zst -o bootstrap_1800.tar.zst
  curl -fL --retry 3 https://apt.procurs.us/bootstraps/1900/bootstrap-iphoneos-arm64.tar.zst -o bootstrap_1900.tar.zst
  zstd -t bootstrap_1800.tar.zst bootstrap_1900.tar.zst
)
gmake -j2 NIGHTLY=1
mkdir -p .build/artifacts
cp Application/Dopamine.ipa .build/artifacts/Cheapamine3-3.0.10-screen2-iPhone8Plus-16.7.10.ipa
python3 scripts/verify-screen-ipa.py .build/artifacts/Cheapamine3-3.0.10-screen2-iPhone8Plus-16.7.10.ipa
shasum -a 256 .build/artifacts/*.ipa > .build/artifacts/SHA256SUMS.txt
git rev-parse HEAD > .build/artifacts/SOURCE_COMMIT.txt
git submodule status --recursive > .build/artifacts/SUBMODULES.txt
cp SCREEN-WORKAROUND.md .build/artifacts/READ-ME-FIRST.md
