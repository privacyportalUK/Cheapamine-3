#!/usr/bin/env python3
"""Validate packaging; this cannot verify touch, exploitation, or device boot."""
import io
import plistlib
import sys
import tarfile
import zipfile

with zipfile.ZipFile(sys.argv[1]) as ipa:
    assert ipa.testzip() is None, 'Damaged IPA archive'
    prefix = 'Payload/Dopamine.app/'
    info = plistlib.loads(ipa.read(prefix + 'Info.plist'))
    assert info['CFBundleDisplayName'] == 'Cheapamine 3 Test'
    assert info['CFBundleShortVersionString'] == '3.0.10'
    assert ipa.read(prefix + info['CFBundleExecutable'])[:4] in (
        b'\xcf\xfa\xed\xfe', b'\xca\xfe\xba\xbe', b'\xbe\xba\xfe\xca'
    ), 'Missing Mach-O app executable'
    for resource in ['basebin.tc', 'bootstrap_1800.tar.zst', 'bootstrap_1900.tar.zst']:
        assert ipa.getinfo(prefix + resource).file_size > 0, resource
    with tarfile.open(fileobj=io.BytesIO(ipa.read(prefix + 'basebin.tar'))) as basebin:
        members = {m.name.removeprefix('./'): m for m in basebin.getmembers()}
        version = basebin.extractfile(members['basebin/.version']).read()
        assert version == b'3.0.10-s2'
        assert len(b'DOPA' + version + b'\0') <= 16, 'Basebin version exceeds dyld UUID capacity'
        helper = basebin.extractfile(members['basebin/jbctl']).read()
        assert b'screen_restart\0' in helper, 'IPA contains unmodified jbctl'
        assert b'iPhone10,2\0' in helper and b'iPhone10,5\0' in helper
        assert members['basebin/jbctl'].mode & 0o111, 'jbctl is not executable'
print('IPA packaging checks passed. Device testing is still required.')
