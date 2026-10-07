# Cheapmine 3 — distribution notices

This product includes software developed by the Sileo Team.

Cheapmine 3 is an unofficial Dopamine/Cheapamine compatibility fork. Dopamine,
Cheapamine, Sileo, Zebra, ElleKit, Procursus and their contributors do not endorse
this fork by being credited. See [CREDITS.md](CREDITS.md) for source lineage and
contributors. Existing copyright notices and license texts are retained.

## Bundled package source

R4 retains these upstream package inputs from the device-tested R3 archive:

| Package | Version | SHA-256 of bundled `.deb` | Source |
| --- | --- | --- | --- |
| Sileo | 2.5.1 | `8e3c90e5a7d32f4ca207a0ac30d3cfa8a13dca86a2b4e11cb3f9e5c68d7bc97a` | [source at c9f70158a037dc76b91c450e72af2de0514dd3ee](https://github.com/Sileo/Sileo/tree/c9f70158a037dc76b91c450e72af2de0514dd3ee), [source ZIP](https://github.com/Sileo/Sileo/archive/refs/tags/2.5.1.zip) |
| Zebra | 1.1.37 | `962d7af1ea58dff44cc3cc4896533865b18aca10d1ac30cc8d7d8516cd781b9a` | [source at 61ba43b5d3ded7b7b4fd922e27b80c0124964243](https://github.com/zbrateam/Zebra/tree/61ba43b5d3ded7b7b4fd922e27b80c0124964243), [source ZIP](https://github.com/zbrateam/Zebra/archive/refs/tags/v1.1.37.zip) |

Both bundled package hashes match their respective upstream release assets. Zebra's source
includes the build scripts and a Swift package lockfile identifying its dependency
sources. The corresponding upstream source and license remain freely available
at the links above. The release's accompanying Zebra source archive preserves
that revision and the dependency sources identified by its lockfile.

The packaged `launchctl` comes from [Procursus launchctl](https://github.com/ProcursusTeam/launchctl)
and is unmodified. The generated `libroot`, `libkrw-dopamine` and `basebin-link`
packages are built from this repository's `Packages` directory.

## Procursus bootstrap

The IPA embeds the unchanged `1800` and `1900` `iphoneos-arm64` bootstraps from
[apt.procurs.us](https://apt.procurs.us/). Their exact archive SHA-256 values are
recorded in the release's `BOOTSTRAP_SHA256SUMS.txt`. Package versions are recorded
inside each archive at `/var/jb/Library/dpkg/status`; package notices are under
`/var/jb/usr/share/doc/` where supplied by the upstream package.

[Procursus source recipes and patches](https://github.com/ProcursusTeam/Procursus)
identify upstream source URLs, versions and modifications. Each bundled package
remains under its own license. The Procursus build-system license does not
relicense GNU, BSD, Apple or other third-party packages inside the bootstrap.
This fork does not modify those package binaries.

## License preservation

- Keep Dopamine's MIT copyright and permission notice with source and binary
  distributions, and preserve component-specific notices.
- Keep the BSD notices and non-endorsement terms for Sileo, ElleKit and other
  BSD-licensed components. The Sileo acknowledgement above must accompany
  advertising materials that mention its features or use.
- Zebra and applicable GNU/other copyleft bootstrap components retain their
  source-distribution requirements. Publish access to the corresponding sources
  alongside the binary downloads; this repository's own source alone is not the
  source of every prebuilt bootstrap package.
- Preserve Apache and Apple-source notices in the covered files and their full
  licenses. This file summarizes where the notices live; it does not replace
  any component's actual license.

The R4 IPA contains the original app resource license files. Public release notes
and source archives provide the additional credits and source references above.
R4 was rebuilt from its recorded source commit and passed build and artifact
verification; R4 hardware confirmation is pending.
