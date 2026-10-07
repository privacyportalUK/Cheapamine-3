# Cheapmine 3 — R4 restart implementation

This build starts from the exact revision 2 source that previously reached Sileo
with working touch on iPhone10,5 / iOS 16.7.10 (20H350). It retains Cheapamine's
five-service restart and addresses the separate Sileo package-finish route.

Sileo invokes the bootstrap launchctl with `reboot userspace`. In R4, that exact
command, running with real/effective UID 0 on the target device/build, executes the
checked basebin `jbctl package_restart` coordinator before launchctl starts a full
userspace reboot. Other launchctl commands and device reboot flags are unchanged.
There is no replacement launchctl executable, new privilege grant, firmware write,
or Fresh 2 pre-reboot termination experiment.

The same coordinator serves the app and package finish. It verifies the installed
basebin version, serializes concurrent restart requests and writes a bounded local
status trace. It never falls back to a full userspace reboot after a matched route
failure. App-to-helper privilege cleanup is checked before service termination.

## Scope and remaining validation

This is a Cheapamine compatibility restart, not an equivalent stock full userspace
reboot. It retains launchd and restarts the original five services. It does not
claim systemwide daemon restart or injection into every already-running process.
The upstream initial daemon-bootstrap gap remains; enabling that code blindly can
stall launchd on this target's initial memory primitive. Watchdog recovery and
other direct reboot clients are not intercepted by this narrow package route.

Live basebin updates are rejected before staging or installing an update: they
require a full device restart followed by sideloading and re-jailbreaking. Normal
Sileo package installation remains available. Package-specific daemon behavior,
ElleKit activation and touch after the package button need hardware validation.

The app is **Cheapmine 3 R4**, build 2026.10.74, basebin 3.0.10-s4. Bundle ID
com.privacyportal.DopamineFresh replaces Fresh 2 with the same signing account.

Force-restart before installation, confirm touch, then sideload the IPA with
Impactor. Open Cheapmine 3 R4 and jailbreak. If touch and Sileo work, separately
test the package-finish Reboot Userspace action while USB remains connected.
Local trace: /var/mobile/Media/Cheapamine3-restart.txt. No trace is uploaded.

The IPA is ad-hoc signed for re-signing by a sideloading tool. Build and code-page
verification do not establish device installation acceptance or touch recovery.

Source basis: official Dopamine 3.0.10, revision 2 port 649f835.
Upstream Cheapamine: https://github.com/wumbomumbo/Cheapamine
Package-manager route: https://github.com/Sileo/Sileo/blob/main/Sileo/UI/DownloadsViewController/DownloadsTableViewController.swift

## Device result

R3 was reported working on the target phone: jailbreak, manual package-manager
icon refresh, package installation and respring. Follow-up diagnostics showed
successful transient firmware recovery and a stable transport reset counter.
The initial helper trace completed successfully. The package_restart command
itself was not present in that trace; its hardware execution remains unconfirmed.

## R4 registration and cleanup

The screen_restart helper now runs uicache -a after privilege cleanup and target/
version checks, under the restart lock, before the five-service sequence. A
15-second deadline and bounded child cleanup prevent an indefinite registration
wait. Failure returns exit 71 before any service restart. The package_restart
route does not perform an additional registration pass. App privilege restoration
is checked before the helper receives its release token, and its wait status is
decoded for the UI. These changes have regression coverage; R4 runtime validation
is pending.
