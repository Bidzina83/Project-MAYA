#!/usr/bin/env python3
"""Installer: extract artifact tar.gz into /opt/data/.hermes/scripts/<skill>/<timestamp>
Usage: install_runtime.py <artifact.tgz> <skill-name>
Creates manifest with per-file sha256 and updates current symlink.
"""
import sys, os, tarfile, hashlib, json, time

def sha256_file(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()

if len(sys.argv)<3:
    print('usage: install_runtime.py <artifact.tgz> <skill-name>')
    sys.exit(2)
art=sys.argv[1]
skill=sys.argv[2]
if not os.path.exists(art):
    print('artifact not found', art); sys.exit(1)
TS=time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())
install_base='/opt/data/.hermes/scripts'
install_dir=os.path.join(install_base, skill, TS)
os.makedirs(install_dir, exist_ok=True)
# extract
with tarfile.open(art,'r:gz') as t:
    t.extractall(install_dir)
# walk files and compute checksums
files=[]
for root,dirs,fnames in os.walk(install_dir):
    for fn in fnames:
        p=os.path.join(root,fn)
        rel=os.path.relpath(p, install_dir)
        try:
            sha=sha256_file(p)
        except Exception as e:
            sha=None
        files.append({'path':rel,'sha256':sha})
manifest={'installed_at':TS,'source_artifact':os.path.abspath(art),'install_dir':install_dir,'files':files}
man_dir='/opt/data/.hermes/installed-manifests'
os.makedirs(man_dir, exist_ok=True)
man_path=os.path.join(man_dir, f'{skill}_{TS}.json')
with open(man_path,'w',encoding='utf-8') as f:
    json.dump(manifest,f,indent=2)
# update current symlink
current_link=os.path.join(install_base, skill, 'current')
try:
    if os.path.islink(current_link) or os.path.exists(current_link):
        os.remove(current_link)
    os.symlink(install_dir, current_link)
except Exception as e:
    print('symlink update failed:', e)
print('installed to', install_dir)
print('manifest written to', man_path)
