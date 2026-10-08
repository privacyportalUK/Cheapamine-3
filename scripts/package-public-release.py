#!/usr/bin/env python3
"""Package a verified R4 build as IPA and a source ZIP."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
PREFIX = 'Cheapmine-3-R4'


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT).decode().strip()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def source_zip(path):
    """Archive the clean tracked checkout, including initialized submodules."""
    if git('status', '--porcelain', '--untracked-files=no'):
        raise RuntimeError('Source checkout must have no tracked changes')
    for line in git('submodule', 'status', '--recursive').splitlines():
        if line.startswith(('-', '+', 'U')):
            raise RuntimeError('Source submodules must match their recorded commits')
    files = subprocess.check_output(
        ['git', 'ls-files', '--recurse-submodules', '-z'], cwd=ROOT
    ).split(b'\0')
    epoch = int(git('show', '-s', '--format=%ct', 'HEAD'))
    stamp = time.gmtime(max(epoch, 315532800))[:6]
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as out:
        for raw in sorted(set(files)):
            if not raw:
                continue
            name = os.fsdecode(raw)
            p = ROOT / name
            if p.is_dir() and not p.is_symlink():
                continue
            if not p.exists() and not p.is_symlink():
                raise RuntimeError('Missing source: ' + name)
            info = zipfile.ZipInfo(PREFIX + '/' + name, stamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (p.lstat().st_mode & 0xffff) << 16
            data = os.readlink(p).encode() if p.is_symlink() else p.read_bytes()
            out.writestr(info, data)


def main():
    os.chdir(ROOT)
    output = Path(sys.argv[1] if len(sys.argv) > 1 else '.build/public-release').resolve()
    output.mkdir(parents=True, exist_ok=True)
    names = {PREFIX + '.ipa', PREFIX + '-source.zip'}
    if any(p.name not in names or not p.is_file() for p in output.iterdir()):
        raise RuntimeError('Use an output directory containing only the two release files or no files')
    if git('status', '--porcelain'):
        raise RuntimeError('Source checkout must be clean')
    publication_commit = git('rev-parse', 'HEAD')
    artifacts = ROOT / '.build/artifacts'
    binary_commit = (artifacts / 'SOURCE_COMMIT.txt').read_text().strip()
    if not re.fullmatch(r'[0-9a-f]{40}', binary_commit):
        raise RuntimeError('Invalid binary source commit')
    ipa_path = artifacts / 'Cheapmine-3-R4-iPhone8Plus-16.7.10.ipa'
    ipa = ipa_path.read_bytes()
    verification = json.loads(subprocess.check_output([
        sys.executable, 'scripts/verify-package-ipa.py', str(ipa_path), binary_commit
    ]))
    verification['ipa'] = PREFIX + '.ipa'
    bootstrap_manifest = json.loads((ROOT / 'release/BOOTSTRAP-PACKAGES.json').read_text())
    for row in bootstrap_manifest:
        with zipfile.ZipFile(ipa_path) as app:
            data = app.read('Payload/Dopamine.app/' + row['archive'])
        if sha(data) != row['sha256']:
            raise RuntimeError('Bootstrap differs from recorded source manifest: ' + row['archive'])
    metadata = {
        'binary_source_commit': binary_commit,
        'publication_source_commit': publication_commit,
        'binary_sha256': sha(ipa),
        'source_scope': 'Tracked fork source with recursive submodules and pinned Zebra dependency source archives.',
        'build_tools': (artifacts / 'BUILD_TOOLS.txt').read_text(),
        'build_submodules': (artifacts / 'SUBMODULES.txt').read_text().splitlines(),
    }
    with tempfile.TemporaryDirectory(prefix='cheapmine-release-') as directory:
        staged = Path(directory)
        archive_path = staged / (PREFIX + '-source.zip')
        source_zip(archive_path)
        subprocess.run([sys.executable, 'scripts/package-zebra-source.py', str(staged)], check=True)
        zebra_name = 'Zebra-1.1.37-source-with-dependencies.zip'
        with zipfile.ZipFile(archive_path, 'a', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            archive.write(staged / zebra_name, PREFIX + '/dependencies/' + zebra_name)
            for name, value in (('BUILD-PROVENANCE.json', metadata), ('VERIFICATION.json', verification)):
                archive.writestr(PREFIX + '/release/' + name, json.dumps(value, indent=2, sort_keys=True) + '\n')
        (output / (PREFIX + '.ipa')).write_bytes(ipa)
        with archive_path.open('rb') as source, (output / archive_path.name).open('wb') as destination:
            while chunk := source.read(1024 * 1024):
                destination.write(chunk)
    print('Prepared verified IPA and source ZIP.')


if __name__ == '__main__':
    main()
