# Cheapamine 3

A Dopamine 3.0.10 fork with Cheapamine's selective restart behavior for iPhone 8 Plus. Includes automatic Sileo and Zebra registration and the R4.1 fix for error 13 during initial jailbreak setup.

## Download R4.1

- [Cheapamine-3-R4.1.ipa](https://github.com/privacyportalUK/Cheapamine-3/releases/download/cheapmine-3-r4.1/Cheapamine-3-R4.1.ipa)
- [Cheapamine-3-R4.1-source.zip](https://github.com/privacyportalUK/Cheapamine-3/releases/download/cheapmine-3-r4.1/Cheapamine-3-R4.1-source.zip)
- [Release notes](https://github.com/privacyportalUK/Cheapamine-3/releases/tag/cheapmine-3-r4.1)

## Supported device

This build targets **iPhone 8 Plus (`iPhone10,5`) on iOS 16.7.10 (`20H350`)**.

R4.1 has been confirmed working on this device configuration. The follow-up diagnostic check found successful app registration and restart, a stable touch reset counter, and no new relevant crash reports.

## Install

1. Restart the phone normally before upgrading from an earlier build.
2. Sign and sideload the IPA. Use the same signing account and bundle identifier when updating the existing app.
3. Open the installed jailbreak app and tap **Jailbreak**.

After a full device restart, open the app and jailbreak again. The bootstrap `launchctl reboot userspace` command uses Cheapamine's selective restart on this device.

## Build from source

Use macOS with full Xcode, Theos and the iPhoneOS 16.5 SDK, GNU make, Procursus ldid, trustcache, dpkg, libarchive, OpenSSL and zstd. Set `THEOS` to your Theos installation, then run:

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
