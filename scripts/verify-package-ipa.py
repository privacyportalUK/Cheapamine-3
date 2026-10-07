#!/usr/bin/env python3
"""Validate an actual Cheapmine R4 IPA. Packaging checks cannot establish runtime safety."""
import argparse
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import plistlib
import re
import struct
import sys
import tarfile
import uuid
import zipfile


# Check that every systemhook architecture contains the package command route.
# Presence establishes packaging only; device execution is tested separately.
PACKAGE_ROUTE_MARKERS = (b"package_restart\x00", b"3.0.10-s4\x00", b"20H350\x00")
REGISTRATION_MARKERS = (b"uicache-started\x00", b"uicache-complete\x00")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def code_directories(signature, executable):
    require(len(signature) >= 12, "Truncated signature")
    magic, length, count = struct.unpack_from(">III", signature)
    require(magic == 0xFADE0CC0 and 12 + count * 8 <= length <= len(signature),
            "Invalid embedded signature")
    result = []
    for i in range(count):
        slot, offset = struct.unpack_from(">II", signature, 12 + i * 8)
        require(offset + 8 <= length, "Signature blob offset outside signature")
        blob_magic, blob_length = struct.unpack_from(">II", signature, offset)
        require(blob_length >= 8 and offset + blob_length <= length, "Invalid signature blob length")
        if blob_magic != 0xFADE0C02:
            continue
        cd = signature[offset:offset + blob_length]
        require(len(cd) >= 44, "Truncated CodeDirectory")
        version, = struct.unpack_from(">I", cd, 8)
        hash_offset, _, special, pages, limit = struct.unpack_from(">IIIII", cd, 16)
        hash_size, hash_type, _, page_shift = struct.unpack_from("BBBB", cd, 36)
        algorithms = {1: "sha1", 2: "sha256", 3: "sha256", 4: "sha384"}
        require(hash_type in algorithms and page_shift <= 30, "Unsupported CodeDirectory hash or page size")
        algorithm = algorithms[hash_type]
        require(0 < hash_size <= hashlib.new(algorithm).digest_size, "Invalid code hash size")
        if version >= 0x20300:
            require(len(cd) >= 64, "Truncated extended CodeDirectory")
            limit64, = struct.unpack_from(">Q", cd, 56)
            if limit == 0xFFFFFFFF:
                limit = limit64
        require(limit <= len(executable), "Code limit exceeds Mach-O slice")
        page_size = (1 << page_shift) if page_shift else max(limit, 1)
        require(pages == (limit + page_size - 1) // page_size, "Unexpected code slot count")
        require(hash_offset >= special * hash_size and hash_offset + pages * hash_size <= len(cd),
                "Code hash array outside CodeDirectory")
        for page in range(pages):
            content = executable[page * page_size:min((page + 1) * page_size, limit)]
            expected = cd[hash_offset + page * hash_size:hash_offset + (page + 1) * hash_size]
            require(hashlib.new(algorithm, content).digest()[:hash_size] == expected,
                    f"Code page {page} does not match signature")
        result.append({"slot": slot, "hash_type": hash_type,
                       "cdhash": hashlib.new(algorithm, cd).digest()[:20].hex(),
                       "verified_code_pages": pages})
    require(result, "No CodeDirectory found")
    return result


def macho(data, require_signature=True, required_markers=()):
    magic = data[:4]
    slices = []
    if magic in (b"\xca\xfe\xba\xbe", b"\xca\xfe\xba\xbf",
                 b"\xbe\xba\xfe\xca", b"\xbf\xba\xfe\xca"):
        endian = ">" if magic[:1] == b"\xca" else "<"
        fat64 = magic in (b"\xca\xfe\xba\xbf", b"\xbf\xba\xfe\xca")
        require(len(data) >= 8, "Truncated fat header")
        count, = struct.unpack_from(endian + "I", data, 4)
        stride = 32 if fat64 else 20
        require(0 < count <= 32 and 8 + stride * count <= len(data), "Invalid fat architecture count")
        for i in range(count):
            values = struct.unpack_from(endian + ("IIQQII" if fat64 else "IIIII"), data, 8 + i * stride)
            offset, size = values[2:4]
            require(size >= 28 and offset + size <= len(data), "Mach-O slice outside file")
            slices.append(data[offset:offset + size])
    elif magic in (b"\xcf\xfa\xed\xfe", b"\xce\xfa\xed\xfe"):
        slices = [data]
    else:
        return None
    result = []
    for binary in slices:
        require(binary[:4] in (b"\xcf\xfa\xed\xfe", b"\xce\xfa\xed\xfe"), "Unsupported Mach-O endian")
        header_size = 32 if binary[:4] == b"\xcf\xfa\xed\xfe" else 28
        _, cpu, subtype, _, commands, command_bytes, _ = struct.unpack_from("<7I", binary)
        require(header_size + command_bytes <= len(binary), "Load commands exceed slice")
        pos, signature, identifier = header_size, None, None
        for _ in range(commands):
            require(pos + 8 <= header_size + command_bytes, "Truncated load command")
            command, size = struct.unpack_from("<II", binary, pos)
            require(size >= 8 and pos + size <= header_size + command_bytes, "Invalid load command length")
            if command == 0x1B:
                require(size >= 24, "Truncated UUID command")
                identifier = str(uuid.UUID(bytes=binary[pos + 8:pos + 24]))
            elif command == 0x1D:
                require(size >= 16, "Truncated code signature command")
                start, length = struct.unpack_from("<II", binary, pos + 8)
                require(start + length <= len(binary), "Signature outside slice")
                signature = binary[start:start + length]
            pos += size
        require(pos == header_size + command_bytes, "Load command size mismatch")
        architecture = "arm64e" if cpu == 0x100000C and subtype & 0xFFFFFF == 2 else {
            0x100000C: "arm64", 0x1000007: "x86_64", 12: "arm"}.get(cpu, hex(cpu))
        require(not require_signature or signature is not None, "Unsigned Mach-O slice")
        for marker in required_markers:
            require(marker in binary, f"Required marker absent from {architecture} slice: {marker!r}")
        result.append({"architecture": architecture, "uuid": identifier,
                       "code_directories": code_directories(signature, binary) if signature else []})
    return result


def trustcache(data):
    require(len(data) >= 24, "Truncated trustcache")
    version, _, count = struct.unpack_from("<I16sI", data)
    require(version == 1 and len(data) == 24 + count * 22, "Invalid v1 trustcache length/version")
    entries = {(data[24 + i * 22:44 + i * 22].hex(), data[44 + i * 22]) for i in range(count)}
    require(entries, "Empty trustcache")
    return entries


def validate(path, expected_commit=None):
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        require(len(names) == len(set(names)), "Duplicate ZIP members")
        require(all(not PurePosixPath(n).is_absolute() and ".." not in PurePosixPath(n).parts for n in names),
                "Unsafe ZIP path")
        require(archive.testzip() is None, "ZIP CRC failure")
        roots = [n[:-len("Info.plist")] for n in names if re.fullmatch(r"Payload/[^/]+\.app/Info\.plist", n)]
        require(len(roots) == 1, "Expected one application bundle")
        root = roots[0]
        info = plistlib.loads(archive.read(root + "Info.plist"))
        for key, expected in {"CFBundleIdentifier": "com.privacyportal.DopamineFresh",
                              "CFBundleDisplayName": "Cheapmine 3 R4", "CFBundleVersion": "2026.10.74"}.items():
            require(info.get(key) == expected, f"Wrong {key}: {info.get(key)!r}")
        executable_name = info.get("CFBundleExecutable")
        require(executable_name and "/" not in executable_name, "Invalid bundle executable name")
        app = archive.read(root + executable_name)
        require(b"screen_restart\x00" in app, "App restart coordinator command is missing")
        app_slices = macho(app)
        require(app_slices and any(s["architecture"] == "arm64" for s in app_slices), "App lacks arm64")
        require(all(s["uuid"] for s in app_slices), "App lacks LC_UUID fingerprint")
        candidates = sorted({m.decode() for m in re.findall(rb"(?<![0-9a-f])[0-9a-f]{40}(?=\x00)", app)})
        require(candidates, "No compiled source commit string found")
        if expected_commit:
            require(re.fullmatch(r"[0-9a-f]{40}", expected_commit), "Expected commit must be 40 lowercase hex characters")
            require(expected_commit in candidates, "Expected source commit absent from compiled app")
        required = ["bootstrap_1800.tar.zst", "bootstrap_1900.tar.zst", "basebin.tar", "basebin.tc",
                    "libjailbreak.dylib", "libchoma.dylib", "libxpf.dylib", "sileo.deb", "zebra.deb",
                    "libroot.deb", "basebin-link.deb", "libkrw-dopamine.deb", "PkgManagers.plist", "Assets.car"]
        for name in required:
            require(archive.getinfo(root + name).file_size > 0, f"Empty required resource: {name}")
        for name in required[:2]:
            require(archive.read(root + name)[:4] == b"\x28\xb5\x2f\xfd", f"Invalid zstd bootstrap: {name}")
        for name in ("libjailbreak.dylib", "libchoma.dylib", "libxpf.dylib"):
            require(macho(archive.read(root + name)), f"Invalid bundled library: {name}")
        exploit_names = ["ClearSword", "DarkSword", "Titan", "badRecovery", "dmaFail", "kfd",
                         "momentarius", "multicast_bytecopy", "weightBufs"]
        for name in exploit_names:
            prefix = root + f"Frameworks/{name}.framework/"
            framework = plistlib.loads(archive.read(prefix + "Info.plist"))
            executable = framework.get("CFBundleExecutable")
            require(executable and "/" not in executable, f"Invalid exploit executable: {name}")
            require(macho(archive.read(prefix + executable)), f"Invalid exploit Mach-O: {name}")
        for name in names:
            require(not any(t in name.lower() for t in ("touchlog", "jbctl-original")),
                    f"Unexpected diagnostic/workaround file: {name}")
        outer_tc = archive.read(root + "basebin.tc")
        basebin_tar = archive.read(root + "basebin.tar")
        with tarfile.open(fileobj=io.BytesIO(basebin_tar)) as tar:
            members = tar.getmembers()
            require(len(members) == len({m.name for m in members}), "Duplicate TAR members")
            files = {}
            for member in members:
                parts = PurePosixPath(member.name).parts
                require(parts and parts[0] == "basebin" and ".." not in parts, "Unexpected TAR path")
                require(member.isdir() or member.isfile(), "Unexpected TAR link/device member")
                if member.name in ("basebin/.version", "basebin/jbctl"):
                    require(member.isfile() and member.uid == 0 and not (member.mode & 0o022),
                            f"Restart helper rejects packaged ownership/mode: {member.name}")
                    if member.name == "basebin/jbctl":
                        require(member.mode & 0o111, "Packaged restart helper is not executable")
                require(not any(t in member.name.lower() for t in ("touchlog", "jbctl-original")),
                        "Diagnostic or workaround content in basebin")
                if member.isfile():
                    files[member.name] = tar.extractfile(member).read()
            require(files.get("basebin/.version") == b"3.0.10-s4", "Incorrect exact basebin version")
            require(files.get("basebin/basebin.tc") == outer_tc, "Inner/outer trustcaches differ")
            entries = trustcache(outer_tc)
            jbctl = files["basebin/jbctl"]
            launchdhook = files["basebin/launchdhook.dylib"]
            require(b"reboot_userspace\x00" in jbctl, "Full userspace reboot command missing")
            require(b"screen_restart\x00" in jbctl and b"package_restart\x00" in jbctl, "Restart coordinator missing")
            require(b"DopamineFresh2-reboot.txt" not in launchdhook, "Failed Fresh 2 ordering code remains")
            require(b"/var/jb/usr/lib/TweakLoader.dylib\x00" in files["basebin/systemhook.dylib"],
                    "Upstream tweak-loader path missing")
            covered, exceptions = 0, []
            fingerprints = {}
            for name, content in files.items():
                require(b"jbctl-original\x00" not in content, f"Unexpected old wrapper in {name}")
                exempt = PurePosixPath(name).name.startswith("dyldhook_merge.")
                markers = (PACKAGE_ROUTE_MARKERS if name == "basebin/systemhook.dylib" else
                           REGISTRATION_MARKERS if name == "basebin/jbctl" else ())
                slices = macho(content, require_signature=not exempt, required_markers=markers)
                if markers:
                    require(slices, "Systemhook is not a valid Mach-O binary")
                if not slices:
                    continue
                if exempt:
                    exceptions.append(name)
                    continue
                for item in slices:
                    require(any((cd["cdhash"], cd["hash_type"]) in entries for cd in item["code_directories"]),
                            f"Trustcache does not cover {name}/{item['architecture']}")
                    covered += 1
                if name in ("basebin/jbctl", "basebin/launchdhook.dylib", "basebin/systemhook.dylib"):
                    fingerprints[name] = {"sha256": digest(content), "slices": slices}
        return {"status": "passed", "scope": "Packaging and code-page integrity only; no runtime or touchscreen proof",
                "ipa": str(path.resolve()), "ipa_sha256": digest(path.read_bytes()),
                "identity": {k: info[k] for k in ("CFBundleIdentifier", "CFBundleDisplayName", "CFBundleVersion")},
                "compiled_source_commit": expected_commit or (candidates[0] if len(candidates) == 1 else None),
                "compiled_commit_candidates": candidates, "app_sha256": digest(app), "app_slices": app_slices,
                "exploit_bundles": len(exploit_names), "basebin_version": "3.0.10-s4",
                "basebin_tar_sha256": digest(basebin_tar), "trustcache_sha256": digest(outer_tc),
                "trustcache_entries": len(entries), "covered_basebin_slices": covered,
                "upstream_trustcache_exceptions": exceptions, "basebin_fingerprints": fingerprints,
                "package_route_required_markers": [m.rstrip(b"\x00").decode() for m in PACKAGE_ROUTE_MARKERS],
                "signing_note": "CodeDirectory page hashes checked; Apple provisioning and device acceptance not asserted"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ipa", type=Path)
    parser.add_argument("expected_commit", nargs="?")
    args = parser.parse_args()
    try:
        report = validate(args.ipa, args.expected_commit)
    except (ValueError, KeyError, OSError, struct.error, zipfile.BadZipFile, tarfile.TarError) as error:
        print(json.dumps({"status": "failed", "error": str(error), "runtime_tested": False}))
        sys.exit(1)
    print(json.dumps(report, sort_keys=True, indent=2))
