# Cheapamine 3

Maintained by [PrivacyPortal](https://PrivacyPortal.co.uk).

**A jailbreak with a fix for the frozen or unresponsive touchscreen glitch after jailbreaking or restarting jailbreak services on an iPhone with a third-party replacement screen. Tested on iPhone 8 Plus running iOS 16.7.10.**

Based on Dopamine 3.0.10, with Cheapamine's selective restart behavior and automatic Sileo and Zebra registration.

## Replacement-screen freeze fix

Some replacement screens can lose touch input when jailbreak services restart. Cheapamine 3 uses Cheapamine's selective restart approach to address the freeze encountered on the tested iPhone 8 Plus, while retaining package-manager and tweak support.

On the test device, touch remained responsive after jailbreaking, installing a tweak and respringing. The tested configuration is **iPhone 8 Plus (`iPhone10,5`), iOS 16.7.10 (`20H350`), with a reported third-party replacement screen**. Other iPhone models and replacement-screen variants have not been verified.

## Download R4.1

- [Cheapamine-3-R4.1.ipa](https://github.com/privacyportalUK/Cheapamine-3/releases/download/cheapmine-3-r4.1/Cheapamine-3-R4.1.ipa)
- [Cheapamine-3-R4.1-source.zip](https://github.com/privacyportalUK/Cheapamine-3/releases/download/cheapmine-3-r4.1/Cheapamine-3-R4.1-source.zip)
- [Release notes](https://github.com/privacyportalUK/Cheapamine-3/releases/tag/cheapmine-3-r4.1)

## Supported device

This build targets **iPhone 8 Plus (`iPhone10,5`) on iOS 16.7.10 (`20H350`)**.

R4.1 has been confirmed working on this device configuration. The follow-up diagnostic check found successful app registration and restart, a stable touch reset counter, and no new relevant crash reports.

## Install

### 1. Check your device and download the app

This release has been tested on **iPhone 8 Plus (`iPhone10,5`), iOS 16.7.10 (`20H350`)**. Check your model and iOS version in **Settings → General → About**; other configurations are not confirmed by this release.

Download [Cheapamine-3-R4.1.ipa](https://github.com/privacyportalUK/Cheapamine-3/releases/download/cheapmine-3-r4.1/Cheapamine-3-R4.1.ipa) to your computer. The **IPA is the installable app**; the source ZIP is for building it yourself. You will need a Mac or Windows PC, a USB cable, and an Apple account for signing.

### 2. Install the IPA

One option is [Sideloadly for macOS or Windows](https://sideloadly.io/):

1. Install Sideloadly from its official website. Windows users should follow its Apple iTunes/iCloud dependency instructions.
2. Connect the iPhone by USB, unlock it, and accept **Trust This Computer** if prompted.
3. Select the connected iPhone in Sideloadly and drag the downloaded **IPA** into the app.
4. Enter your Apple account in Sideloadly, start installation, and complete any authentication prompts. Wait for installation to finish.

If you already have a working IPA signing tool, you can use it instead. Downloading the IPA in Safari alone does not install it.

### 3. Open the app and jailbreak

1. If iOS asks you to trust the signing account, open **Settings → General → VPN & Device Management**, select that account's developer profile, and follow the trust prompt.
2. If iOS requests **Developer Mode**, open **Settings → Privacy & Security → Developer Mode** and follow the restart and confirmation prompts. See [Apple's Developer Mode guide](https://developer.apple.com/documentation/xcode/enabling-developer-mode-on-a-device).
3. Open the installed jailbreak app and tap **Jailbreak**. Allow setup and the service restart to finish.
4. Unlock the phone and open **Sileo** or **Zebra**. R4.1 registers the package-manager apps automatically. Let the package manager refresh before installing packages.

### After restarting and refreshing the app

After a full power-off or device restart, open the jailbreak app and tap **Jailbreak** again. A respring is different from a full device restart.

With a free Apple account, Sideloadly-signed apps normally need refreshing every **7 days**. Use Sideloadly's refresh feature or re-sign the IPA before it expires. If the jailbreak app stops opening, check its signing status first.

### Troubleshooting

| What you see | What to do |
| --- | --- |
| Sileo or Zebra is missing after a successful jailbreak | Open the jailbreak app's settings and use **Refresh Jailbreak Apps**, then check the Home Screen again. |
| Setup stops with an error | Save the exact error message, restart the phone normally, and try again. If it repeats, include the log when reporting the problem. |
| The app will not open | Check the developer profile, Developer Mode prompt, and signing expiry. Re-sign using the same account and bundle identifier if needed. |
| Touch becomes unresponsive | On iPhone 8 Plus, quickly press Volume Up, quickly press Volume Down, then hold Side until the Apple logo appears. After it restarts, check touch before jailbreaking again. Record which action caused the freeze. |

For PrivacyPortal information and contact options, visit **[PrivacyPortal.co.uk](https://PrivacyPortal.co.uk)**. When reporting a problem, include the device model, iOS version, release version, exact error, and what happened immediately before it. Remove account details and device identifiers from any shared logs.

## Build from source (developers only)

**The released app targets iOS 16.7.10.** To install it, use the IPA and the installation steps above; Xcode and an SDK are not needed.

To compile the source, use macOS with full Xcode, Theos, GNU make, Procursus ldid, trustcache, dpkg, libarchive, OpenSSL and zstd. The build scripts require **iPhoneOS16.5.sdk** in Theos: this is the compiler SDK used to build the app, not the iOS version required on your phone. You do not need to downgrade from iOS 16.7.10.

Set `THEOS` to your Theos installation, then run:

```sh
git clone --recursive https://github.com/privacyportalUK/Cheapamine-3.git
cd Cheapamine-3
bash scripts/build-package-ipa.sh
```

The script builds and verifies the IPA. The release source ZIP includes recursive submodules, dependency sources and build records.

## Credits and licenses

- [Dopamine](https://github.com/opa334/Dopamine) — opa334 and contributors.
- [Cheapamine](https://github.com/wumbomumbo/Cheapamine) — wumbomumbo and contributors; the basis for selective restart support.
- Sileo Team, Zebra Team, Procursus Team, ElleKit, and the upstream component authors listed in the [app credits](Application/Dopamine/UI/Settings/Credits.plist).

Original copyrights and licenses are retained in [LICENSE.md](LICENSE.md) and the [component license files](Application/Dopamine/Resources).

**This product includes software developed by the Sileo Team.**
