# Cheapmine 3

A device-specific Dopamine 3.0.10 fork using Cheapamine's selective restart for
**iPhone 8 Plus (iPhone10,5), iOS 16.7.10 (20H350)**.

## Downloads

[Download R4: IPA, TIPA and source](https://github.com/privacyportalUK/Cheapmine-3/releases/tag/cheapmine-3-r4).
The app appears as **Cheapmine 3 R4**, build **2026.10.74**.

- **IPA:** use your sideloading tool, including Impactor.
- **TIPA:** the identical archive with Dopamine's alternate extension. This does
  not add TrollStore support to stable iOS 16.7.10; see
  [TrollStore's supported versions](https://github.com/opa334/TrollStore#readme).
- **Source:** fork source with recursive submodule files, a Git bundle, component
  sources, build instructions, pinned revisions, checksums and verification.

## R4 changes

- Registers jailbreak apps automatically with `uicache -a` before the initial
  service restart, addressing missing Sileo and Zebra icons.
- Bounds registration to 15 seconds and reports failure before restarting services.
- Checks privilege-cleanup results before releasing the restart helper.
- Decodes helper exit status so registration failures get the correct message.

R3 was reported working after manual icon refresh, package installation and
respring. Its follow-up diagnostics showed transient firmware recovery followed
by a stable reset counter. **R4's changes need confirmation on the device.**

## Installation

1. Start from a normal device restart with working touch.
2. Sideload the IPA with the same signing account when updating an existing install.
3. Open **Cheapmine 3 R4** and run Jailbreak.

Sileo and Zebra should register automatically. If registration fails, the app
reports it without attempting the service restart; Refresh Jailbreak Apps remains
available in settings. The bundle identifier is unchanged for update compatibility.

## Scope

This build retains Cheapamine's five-service restart and the checked bootstrap
`launchctl reboot userspace` route used by Sileo. It does not perform all the work
of a full userspace reboot. Other devices/builds are not enabled. Live basebin
updates require a normal device restart, installation and a fresh jailbreak.
See [restart details](PACKAGE-RESTART.md).

## Build and source

```sh
git clone --recurse-submodules https://github.com/privacyportalUK/Cheapmine-3.git
cd Cheapmine-3
# Requires Xcode, Theos with iPhoneOS16.5 SDK, Procursus ldid,
# trustcache, GNU make, dpkg and zstd.
bash scripts/build-package-ipa.sh
```

The publication workflow pins the build tools. `SOURCE_COMMIT.txt` and
`PROVENANCE.json` identify the exact compiled source. The source ZIP includes
tracked submodules. To inspect a release bundle in a full repository clone:

```sh
git fetch /path/to/Cheapmine-3-R4-source.bundle HEAD
git checkout --detach FETCH_HEAD
git submodule update --init --recursive
```

A fresh build can differ because the upstream bootstrap downloads and build
environment may change. The published release checks those bootstrap hashes
against its package inventory.

## Credits and licenses

Based on [Dopamine by opa334 and contributors](https://github.com/opa334/Dopamine)
and [Cheapamine by wumbomumbo and contributors](https://github.com/wumbomumbo/Cheapamine).
See [CREDITS.md](CREDITS.md) for authors and source lineage, and
[NOTICE.md](NOTICE.md) for bundled package sources and licenses.

**This product includes software developed by the Sileo Team.**
