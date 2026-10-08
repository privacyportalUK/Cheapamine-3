#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."

xcrun --sdk iphoneos --show-sdk-path
for tool in gmake ldid trustcache dpkg-deb; do
  command -v "$tool" >/dev/null || { echo "Missing build tool: $tool" >&2; exit 1; }
done
: "${THEOS:?Set THEOS to an installation with iPhoneOS16.5.sdk}"

git submodule update --init --recursive
(
  cd Application/Dopamine/Resources
  curl -fL --retry 3 https://apt.procurs.us/bootstraps/1800/bootstrap-iphoneos-arm64.tar.zst -o bootstrap_1800.tar.zst
  curl -fL --retry 3 https://apt.procurs.us/bootstraps/1900/bootstrap-iphoneos-arm64.tar.zst -o bootstrap_1900.tar.zst
  zstd -t bootstrap_1800.tar.zst bootstrap_1900.tar.zst
)

# A clean Actions checkout compiles the app and basebin from this source commit.
gmake -j2 NIGHTLY=1
mkdir -p .build/artifacts
ipa_path=.build/artifacts/Cheapmine-3-R4.1-iPhone8Plus-16.7.10.ipa
cp Application/Dopamine.ipa "$ipa_path"
python3 scripts/verify-package-ipa.py "$ipa_path" "$(git rev-parse HEAD)" > .build/artifacts/VERIFICATION.json
(
  cd .build/artifacts
  shasum -a 256 *.ipa > SHA256SUMS.txt
)
git rev-parse HEAD > .build/artifacts/SOURCE_COMMIT.txt
git submodule status --recursive > .build/artifacts/SUBMODULES.txt
shasum -a 256 Application/Dopamine/Resources/bootstrap_*.tar.zst > .build/artifacts/BOOTSTRAP_SHA256SUMS.txt
xcodebuild -version > .build/artifacts/BUILD_TOOLS.txt
clang --version >> .build/artifacts/BUILD_TOOLS.txt
