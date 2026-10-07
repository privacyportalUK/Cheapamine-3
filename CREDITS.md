# Cheapmine 3 — credits and source lineage

Cheapmine 3 is an unofficial compatibility fork. R4 continues the working R3 codebase and adds automatic app registration and
checked cleanup. Its app name is **Cheapmine 3 R4**.
The original authors retain their copyrights. This acknowledgement does not imply
that any upstream author has reviewed or endorsed this fork.

## Code this fork builds on

- **Lars Fröder (opa334) and all Dopamine contributors:** the jailbreak, app,
  bootstrap integration, exploits and supporting infrastructure. The source basis
  is [Dopamine 3.0.10, commit 1a54e76d515ff5916b64e44d6afbb57d2bc89ee9](https://github.com/opa334/Dopamine/tree/1a54e76d515ff5916b64e44d6afbb57d2bc89ee9).
  Dopamine's original [MIT license](LICENSE.md), source notices and Git history
  are retained.
- **wumbomumbo and Cheapamine contributors:** the replacement-screen selective
  restart approach. The five-service selection is adapted from
  [`DOEnvironmentManager.m`, commit b55979bdf4469ed2efc55bdafc3dc882d36dce61](https://github.com/wumbomumbo/Cheapamine/blob/b55979bdf4469ed2efc55bdafc3dc882d36dce61/Application/Dopamine/Jailbreak/DOEnvironmentManager.m).
  R3 moves that selection into a checked helper and restarts `backboardd` last.
  Cheapamine retains Dopamine's MIT license. Its
  [README](https://github.com/wumbomumbo/Cheapamine/blob/b55979bdf4469ed2efc55bdafc3dc882d36dce61/README.md)
  also documents the need to refresh jailbreak apps when package-manager icons
  do not appear after the selective restart.
- **Sileo Team and Procursus Team:** their source exposed the package-finish
  command that needed compatibility handling:
  [`launchctl reboot userspace` in Sileo](https://github.com/Sileo/Sileo/blob/c9f70158a037dc76b91c450e72af2de0514dd3ee/Sileo/UI/DownloadsViewController/DownloadsTableViewController.swift)
  and [Procursus launchctl](https://github.com/ProcursusTeam/launchctl).
  The R3 command router is new code in this fork; it does not replace their
  executables or claim authorship of either project.
- **privacyportalUK:** integration, packaging and testing of this device-specific
  port. The device-tested R3 source
  is commit `50d1ed7`; its full commit ID and build hashes accompany the release.

The winaviation Cheapamine fork was examined during investigation. R3 does not
use its broad process-termination implementation and does not claim it as a code
source for the five-service coordinator.

## Preserved Dopamine acknowledgements

The following groups are reproduced from Dopamine's existing
[`Credits.plist`](Application/Dopamine/UI/Settings/Credits.plist). They acknowledge
upstream contributions across the project, not a claim that every component runs
on this one device.

### Developers

[opa334](https://infosec.exchange/@opa334), [kok3shidoll](https://github.com/kok3shidoll), [Alfie](https://x.com/alfiecg_dev), [Clarity](https://x.com/imnotclarity), [staturnz](https://x.com/staturnzdev), [wh1te4ever](https://x.com/wh1te4ever).

### UI and Design

[tomt000](https://twitter.com/tomt000), [sourcelocation](https://twitter.com/sourceloc), [xerus](https://twitter.com/xerusdesign).

### Credits

[Fugu15](https://github.com/pinauten/Fugu15), [Fugu15_Rootful](https://github.com/pinauten/Fugu15_Rootful), [Pinauten GmbH](https://github.com/pinauten), [tihmstar](https://twitter.com/tihmstar), [oct0xor](https://twitter.com/oct0xor), [kucher1n](https://twitter.com/kucher1n), [bzvr_](https://twitter.com/bzvr_), [Op. Triangulation](https://www.youtube.com/watch?v=1f6YyH62jFE), [GTIG/Coruna](https://cloud.google.com/blog/topics/threat-intelligence/coruna-powerful-ios-exploit-kit), [htimesnine](https://github.com/htimesnine), [felix-pb](https://github.com/felix-pb), [John Aakerblom](https://twitter.com/jaakerblom), [potmdehex](https://github.com/potmdehex), [_simo36](https://twitter.com/_simo36), [0x7ff](https://github.com/0x7ff), [évelyne](https://github.com/evelyneee), [sk8ingDuck](https://github.com/sk8ingDuck), [Dhinak G](https://twitter.com/dhinakg), [Capt Inc](https://github.com/captinc), [Nick Chan](https://github.com/asdfugil), [Sam Bingner](https://github.com/sbingner), [Procursus](https://procursus.social/@team), [roothideDev](https://twitter.com/roothideDev), [Amy While](https://github.com/elihwyma), [Adam Demasi](https://github.com/kirb), [Trenchant /s](https://x.com/TrenchantARC).

## Components and their notices

Full license texts remain in
[`Application/Dopamine/Resources`](Application/Dopamine/Resources) and in the
individual source files and dependency repositories. The app's original license
viewer and credit list remain intact. These component terms are not replaced by
the top-level MIT license.

| Component / contributor | Retained notice or source |
| --- | --- |
| Dopamine — Lars Fröder and contributors | [MIT](LICENSE.md) |
| ChOma — Lars Fröder | [MIT](Application/Dopamine/Resources/LICENSE_ChOma.md), [source](https://github.com/opa334/ChOma) |
| XPF — Lars Fröder and contributors | [MIT](Application/Dopamine/Resources/LICENSE_XPF.md), [source](https://github.com/opa334/XPF) |
| opainject — Lars Fröder | [MIT](Application/Dopamine/Resources/LICENSE_opainject.md), [source](https://github.com/opa334/opainject) |
| litehook — Lars Fröder | [MIT in source](https://github.com/opa334/litehook/blob/0d9d17afc011d2a8dfe67a4f7803ff99143d0f0d/LICENSE) |
| kfd — Félix Poulin-Bélanger and contributors | [MIT](Application/Dopamine/Resources/LICENSE_kfd.md), [source](https://github.com/felix-pb/kfd) |
| weightBufs — Mohamed Ghannam | [MIT](Application/Dopamine/Resources/LICENSE_weightBufs.md), [source](https://github.com/0x36/weightBufs) |
| libgrabkernel2 — Alfie CG and contributors | [MIT](Application/Dopamine/Resources/LICENSE_libgrabkernel2.md), [source](https://github.com/alfiecg24/libgrabkernel2) |
| libpartial — Dhinak G | Prebuilt dependency inherited from Dopamine; credited by [TrollInstallerX](https://github.com/alfiecg24/TrollInstallerX) |
| ElleKit — Évelyne Bélanger and contributors | [BSD notice](Application/Dopamine/Resources/LICENSE_ElleKit.md), [source](https://github.com/ellekit/ellekit) |
| Fugu15 and Fugu15_Rootful — Pinauten GmbH | [Fugu15 MIT](Application/Dopamine/Resources/LICENSE_Fugu15.md), [Rootful MIT](Application/Dopamine/Resources/LICENSE_Fugu15_Rootful.md) |
| plooshinit — Nick Chan; Embedded Artistry libc | [both MIT notices](Application/Dopamine/Resources/LICENSE_plooshinit.md) |
| dimentio — 0x7ff and contributors | [Apache-2.0](Application/Dopamine/Resources/LICENSE_dimentio.md), [source](https://github.com/0x7ff/dimentio) |
| Apple libc and Apple-derived headers | [APSL-2.0](Application/Dopamine/Resources/LICENSE_libc.md) and retained file-level notices |
| Procursus Team | [build-system notice](Application/Dopamine/Resources/LICENSE_Procursus.md), [package recipes and patches](https://github.com/ProcursusTeam/Procursus); individual package licenses also apply |
| Sileo Team | [BSD notice with acknowledgement condition](Application/Dopamine/Resources/LICENSE_Sileo.md), [2.5.1 source](https://github.com/Sileo/Sileo/tree/c9f70158a037dc76b91c450e72af2de0514dd3ee) |
| Zebra Team | [GPLv3](Application/Dopamine/Resources/LICENSE_Zebra.md), [1.1.37 source](https://github.com/zbrateam/Zebra/tree/61ba43b5d3ded7b7b4fd922e27b80c0124964243) |
| zstd — Meta/Facebook and contributors | [source and BSD/GPL notices](https://github.com/facebook/zstd); Xcode package dependency |
| img4lib — xerub | [source](https://github.com/xerub/img4lib/tree/69772c72f3c08f021ec9fa4c386f2b3df60a38b7), including its file-level notices |
| lzfse — Apple and contributors | [BSD notice](https://github.com/lzfse/lzfse/blob/88e2d2788b4021d0b2eb9fe2d97352ae9190f128/LICENSE) |
| libarchive — Tim Kientzle, Martin Matuska and contributors | Retained header notices; [source](https://github.com/libarchive/libarchive) |

**This product includes software developed by the Sileo Team.**

Other inherited source acknowledgements remain next to their code, including
Brandon Azad's ktrw, Siguza's iokit-utils, SwiftfulThinking's loading indicators,
Mountainstorm's CoreSymbolication headers, Apple/OpenBSM contributors, Niels
Provos's tree code and Elias Limneos's classdump-dyld notice. The source history
and file headers remain the authoritative record for those individual portions.

## Exact dependency revisions used by R3

| Source dependency | Commit |
| --- | --- |
| ChOma (also nested under XPF) | `7dccded6bc17081c08f5f5cdbd7a4b051543a825` |
| XPF | `9e12b8faa7444f6fe7f699aec6b6c96d151455d3` |
| XPF / img4lib | `69772c72f3c08f021ec9fa4c386f2b3df60a38b7` |
| img4lib / lzfse | `88e2d2788b4021d0b2eb9fe2d97352ae9190f128` |
| litehook | `0d9d17afc011d2a8dfe67a4f7803ff99143d0f0d` |
| opainject | `849bb296ea8bc0643a2966485ea3c3c96ebdcd5b` |

The build also uses Pinauten's [SwiftUtils](https://github.com/pinauten/SwiftUtils),
[SwiftMachO](https://github.com/pinauten/SwiftMachO) and
[PatchfinderUtils](https://github.com/pinauten/PatchfinderUtils); their pinned
revisions are in [MachOMerger's Package.resolved](BaseBin/MachOMerger/Package.resolved).
Theos, the Theos SDK distribution, Procursus ldid, CRKatri's trustcache utility,
Xcode/Clang, Homebrew, GNU tools, Python and GitHub Actions provide the build and
verification tooling. Tool pins are recorded in the workflow; they are not
claimed as code authored by this fork.

The source archive preserves the dependencies that are present in the source
checkout. The IPA additionally contains upstream prebuilt packages and bootstrap
archives; see [NOTICE.md](NOTICE.md) for versions, source access and distribution
notes. Some inherited prebuilt inputs have no exact source revision recorded upstream;
the notices identify their provenance separately from this fork’s source.
