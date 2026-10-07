#!/usr/bin/env python3
"""Package a verified R4 build with its corresponding source and notices."""
import hashlib, io, json, os, shutil, subprocess, sys, urllib.request, zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REPO='privacyportalUK/Cheapmine-3'
PREFIX='Cheapmine-3-R4'

def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT).decode().strip()

def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'Cheapmine-release'}),timeout=90).read()

def sha(data): return hashlib.sha256(data).hexdigest()

def source_zip(path):
    files=subprocess.check_output(['git','ls-files','--recurse-submodules','-z'],cwd=ROOT).split(b'\0')
    epoch=int(git('show','-s','--format=%ct','HEAD'))
    import time
    stamp=time.gmtime(max(epoch,315532800))[:6]
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as out:
        for raw in sorted(set(files)):
            if not raw: continue
            name=os.fsdecode(raw); p=ROOT/name
            if p.is_dir(): continue
            if not p.exists() and not p.is_symlink(): raise RuntimeError('Missing source: '+name)
            info=zipfile.ZipInfo(PREFIX+'/'+name,stamp)
            info.compress_type=zipfile.ZIP_DEFLATED
            info.external_attr=(p.lstat().st_mode & 0xffff)<<16
            data=os.readlink(p).encode() if p.is_symlink() else p.read_bytes()
            out.writestr(info,data)


def main():
    os.chdir(ROOT)
    output=Path(sys.argv[1] if len(sys.argv)>1 else '.build/public-release').resolve()
    output.mkdir(parents=True,exist_ok=True)
    if git('status','--porcelain'): raise RuntimeError('Source checkout must be clean')
    commit=git('rev-parse','HEAD')
    artifacts=ROOT/'.build/artifacts'
    ipa=(artifacts/'Cheapmine-3-R4-iPhone8Plus-16.7.10.ipa').read_bytes()
    for suffix in ('ipa','tipa'): (output/(PREFIX+'.'+suffix)).write_bytes(ipa)
    verification=subprocess.check_output([sys.executable,'scripts/verify-package-ipa.py',str(output/(PREFIX+'.ipa')),commit])
    v=json.loads(verification); v['ipa']=PREFIX+'.ipa'
    (output/'VERIFICATION.json').write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
    for name in ('BUILD_TOOLS.txt','BOOTSTRAP_SHA256SUMS.txt','SUBMODULES.txt','SOURCE_COMMIT.txt','SOURCE_PATCH.diff'):
        shutil.copyfile(artifacts/name,output/name)
    for row in json.loads((ROOT/'release/BOOTSTRAP-PACKAGES.json').read_text()):
        data=(ROOT/'Application/Dopamine/Resources'/row['archive']).read_bytes()
        if sha(data)!=row['sha256']: raise RuntimeError('Bootstrap differs from published source manifest: '+row['archive'])
    source_zip(output/(PREFIX+'-source.zip'))
    subprocess.run(['git','bundle','create',str(output/(PREFIX+'-source.bundle')),'HEAD','^1a54e76d515ff5916b64e44d6afbb57d2bc89ee9'],check=True)
    subprocess.run([sys.executable,'scripts/package-zebra-source.py',str(output)],check=True)
    for name in ('CREDITS.md','NOTICE.md','LICENSE.md','README.md','RELEASE.md','PACKAGE-RESTART.md'):
        shutil.copyfile(ROOT/name,output/name)
    shutil.copyfile(ROOT/'release/BOOTSTRAP-PACKAGES.json',output/'BOOTSTRAP-PACKAGES.json')
    provenance={'binary_source_commit':commit,'publication_source_commit':commit,'binary_sha256':sha(ipa),'ipa_tipa_identical':True,'source_archive':'Tracked fork source including recursive submodule files; separately bundled packages are described in NOTICE.md.','validation':'Build and artifact verification passed. R4 adds automatic app registration and checked privilege cleanup; R4 hardware validation is pending.','runtime_scope':'Selective restart; R3 working-device results do not establish R4 hardware behavior.'}
    (output/'PROVENANCE.json').write_text(json.dumps(provenance,indent=2,sort_keys=True)+'\n')
    entries=[]
    for p in sorted(output.iterdir()):
        if p.is_file() and p.name!='SHA256SUMS.txt': entries.append(sha(p.read_bytes())+'  '+p.name)
    (output/'SHA256SUMS.txt').write_text('\n'.join(entries)+'\n')
    print('Prepared verified IPA/TIPA, source archives, notices and checksums.')

if __name__=='__main__': main()
