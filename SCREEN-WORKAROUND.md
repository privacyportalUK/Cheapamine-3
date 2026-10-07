# Cheapamine 3 Test — iPhone 8 Plus / iOS 16.7.10

Experimental port of Cheapamine's selective service restart to Dopamine 3.0.10.
This is an unofficial test build. A successful compile does not establish that
the touchscreen works or that the jailbreak remains stable on an actual phone.

## Source and changes

- Dopamine base: `1a54e76d515ff5916b64e44d6afbb57d2bc89ee9` (tag `3.0.10`).
- Cheapamine reference: `wumbomumbo/Cheapamine`, branch `2.x`; the five-service
  restart is adapted from `DOEnvironmentManager` rather than merging old exploits.
- Applies only to `iPhone10,2` / `iPhone10,5`, running exactly iOS `16.7.10`.
- Retains Dopamine 3's exploitation, bootstrap, cleanup, and protection code.
- The app's userspace-reboot requests instead run a `jbctl screen_restart`
  helper. It restarts mediaserverd, installd, userd, networkd, then backboardd.
  Missing optional services are tolerated; other failures stop the sequence.
  There is no automatic fallback to a full userspace reboot.
- Keeps the app's root/sandbox cleanup handshake before restarting services.
  Version comparison uses numeric ordering so `3.0.10` is newer than `3.0.5`.
- Disables app in-place updates on the target device: those require launchd to
  restart and cannot be completed by a selective restart. Update by a normal
  reboot followed by sideloading and re-jailbreaking.
- The `.version` marker is `3.0.10-screen1`, and the app is labelled
  `Cheapamine 3 Test`. The upstream app identifier is retained for compatibility.

## Installation and first test

1. Force-restart normally: quickly press Volume Up, quickly press Volume Down,
   then hold the Side button until the Apple logo appears. Verify touch works
   before opening the jailbreak app.
2. Use your sideloader to sign and install the generated `.ipa`. It is ad-hoc
   signed for packaging, not signed with your Apple account. No signing keys or
   Apple credentials belong in this repository or its build workflow.
3. On iOS 16, enable Developer Mode if the sideloader requires it. Launch
   `Cheapamine 3 Test` and press Jailbreak. Keep the default exploit selection.
4. Test touch at the lock screen and home screen, open Sileo, then lock/unlock
   several times. If Sileo is missing, try Settings → Refresh Jailbreak Apps.
5. If touch fails, force-restart again and leave the device unjailbroken. Record
   whether the display is black or visible, and the last on-screen jailbreak log.

Use the modern Impactor app if that is your existing sideloader. Legacy Cydia
Impactor has different account requirements. Neither is included in this build.

## Known limits

This changes the restart path, not the replacement display's firmware. It is
not a confirmed repair for this particular phone. Selective restart leaves some
existing services uninjected. Third-party launch daemons are not automatically
loaded by the normal full-userspace-reboot path, because that path is skipped.
The upstream source explicitly warns of possible hangs when manually loading
those daemons before the first full userspace reboot, so this port does not
enable that commented-out code. System-wide tweaks and daemon-dependent packages
may therefore be incomplete. Watchdog recovery, external package managers and
command-line tools can still request a genuine userspace reboot; those paths are
not replaced by this app workaround and may reproduce the touchscreen problem.

## Build

The GitHub workflow applies the reviewed `cheapamine3.patch` to the fork,
commits the source changes, and builds on a macOS runner with full Xcode.
It uploads an IPA, SHA-256 checksum, source commit and this document as artifacts.
Local builds require full Xcode with the iPhoneOS SDK, Theos with iPhoneOS16.5.sdk,
GNU make, ldid, trustcache, dpkg-deb, libarchive headers, zstd, and the pinned
recursive submodules. Run `bash scripts/build-screen-ipa.sh`.

Host tests (`bash scripts/test-screen-restart.sh`) check target selection,
restart ordering, absent services and failure propagation with simulated
callbacks. They never signal any processes. Packaging validation checks the
IPA's app metadata, bootstrap resources and the modified jailbreak helper.

## Attribution

Dopamine: https://github.com/opa334/Dopamine

Cheapamine: https://github.com/wumbomumbo/Cheapamine

The upstream MIT license is retained in `LICENSE.md`. Credits remain with
opa334, ElleKit's contributors and Cheapamine's authors. This port is not an
official release of either project.
