# Cheapmine 3 — R4

For **iPhone 8 Plus (iPhone10,5), iOS 16.7.10 (20H350)**.
App: **Cheapmine 3 R4**, build **2026.10.74**, basebin **3.0.10-s4**.

## Fixes

- Automatically registers Sileo, Zebra and other jailbreak apps before the initial
  service restart. R3 required a manual Refresh Jailbreak Apps action.
- Gives registration a 15-second limit; failure returns a specific message before
  any service restart is attempted.
- Blocks helper release if privilege cleanup fails.
- Decodes the helper's wait status so its failure message is accurate.

The Cheapamine restart order is preserved. No firmware changes or broad daemon
bootstrap are added. R3 worked on the target phone; **R4 hardware confirmation is
pending**. Compilation and regression checks are not a substitute for that test.

## Downloads and installation

Download `Cheapmine-3-R4.ipa`, normally restart the phone, then sideload and run
Jailbreak. Use the same signing account to update an existing installation.

`Cheapmine-3-R4.tipa` is byte-identical to the IPA. The alternate extension does
not add TrollStore support; stable iOS 16.7.10 is outside
[TrollStore's supported versions](https://github.com/opa334/TrollStore#readme).

The release also includes the corresponding fork source ZIP and Git bundle,
Zebra 1.1.37 source with pinned dependencies, component credits/licenses, bootstrap
package inventory, build provenance and SHA-256 checksums. Other bundled source
access is documented in `NOTICE.md`.

This remains a selective-restart compatibility build. Live basebin updates
require a normal device restart and a fresh jailbreak. See `PACKAGE-RESTART.md`
for the full scope.

## Credits

**opa334 and Dopamine contributors**, **wumbomumbo and Cheapamine contributors**,
**Procursus**, **Sileo**, **Zebra**, and all component authors listed in
`CREDITS.md`. Original copyrights and license notices are retained.

**This product includes software developed by the Sileo Team.**
