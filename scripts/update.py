#!/usr/bin/env python3
"""Resolve the desktop stable release through OpenAI's signed APT metadata."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://persistent.oaistatic.com/codex-app-prod/linux/deb/'
INDEX = 'main/binary-amd64/Packages'


def fetch(url):
    return subprocess.check_output(['curl', '--fail', '--silent', '--show-error',
                                    '--location', '--retry', '3', '--max-time', '90', url])


def parse_packages(text):
    records = []
    for paragraph in text.strip().split('\n\n'):
        fields = {}
        for line in paragraph.splitlines():
            if line and not line[0].isspace():
                key, value = line.split(':', 1)
                fields[key] = value.strip()
        if fields.get('Package') == 'chatgpt' and fields.get('Architecture') == 'amd64':
            records.append(fields)
    if not records:
        raise ValueError('Missing chatgpt amd64 package in stable index')
    for record in records:
        if not re.fullmatch(r'\d+(?:\.\d+)+', record['Version']):
            raise ValueError('Unexpected upstream version')
    fields = max(records, key=lambda item: tuple(map(int, item['Version'].split('.'))))
    if any(record['Version'] == fields['Version'] and record != fields for record in records):
        raise ValueError('Conflicting metadata for the same version')
    if not re.fullmatch(r'\d+(?:\.\d+)+', fields['Version']):
        raise ValueError('Unexpected upstream version')
    if not re.fullmatch(r'[a-f0-9]{64}', fields['SHA256']):
        raise ValueError('Invalid SHA256')
    filename = fields['Filename']
    if not re.fullmatch(r'pool/main/c/chatgpt/chatgpt_[0-9.]+_amd64\.deb', filename):
        raise ValueError('Unexpected download path')
    if PurePosixPath(filename).name != f"chatgpt_{fields['Version']}_amd64.deb":
        raise ValueError('Filename/version mismatch')
    return fields


def verify_index(release, index):
    match = re.search(r'^SHA256:\n((?:[ \t]+[^\n]+\n)+)', release, re.M)
    if not match:
        raise ValueError('Missing signed SHA256 index')
    for line in match[1].splitlines():
        digest, size, name = line.split()
        if name == INDEX:
            if len(index) != int(size) or hashlib.sha256(index).hexdigest() != digest:
                raise ValueError('APT index does not match signed metadata')
            return
    raise ValueError('Missing amd64 index in signed metadata')


def main():
    with tempfile.TemporaryDirectory() as directory:
        tmp = Path(directory)
        (tmp / 'InRelease').write_bytes(fetch(BASE + 'dists/stable/InRelease'))
        subprocess.run(['gpgv', '--homedir', directory, '--keyring',
                        str(ROOT / 'keys/openai-linux.gpg'), '--output', str(tmp / 'Release'),
                        str(tmp / 'InRelease')], check=True)
        index = fetch(BASE + 'dists/stable/' + INDEX)
        verify_index((tmp / 'Release').read_text(), index)
    fields = parse_packages(index.decode())
    path = ROOT / 'PKGBUILD'
    content = path.read_text()
    old_version = re.search(r'^pkgver=(.+)$', content, re.M)[1]
    old_hash = re.search(r"^sha256sums=\('([^']+)'\)$", content, re.M)[1]
    version, digest = fields['Version'], fields['SHA256']
    if tuple(map(int, version.split('.'))) < tuple(map(int, old_version.split('.'))):
        raise ValueError('Refusing upstream version rollback')
    if version == old_version and digest != old_hash:
        raise ValueError('Upstream replaced a versioned package; manual review required')
    content = re.sub(r'^pkgver=.*$', f'pkgver={version}', content, flags=re.M)
    if version != old_version:
        content = re.sub(r'^pkgrel=.*$', 'pkgrel=1', content, flags=re.M)
    filename = PurePosixPath(fields['Filename']).name
    content = re.sub(r'^source=.*$', f"source=('{filename}::{BASE}{fields['Filename']}')", content, flags=re.M)
    content = re.sub(r'^sha256sums=.*$', f"sha256sums=('{digest}')", content, flags=re.M)
    path.write_text(content)
    (ROOT / 'upstream.json').write_text(json.dumps(fields, indent=2) + '\n')
    print(f'Official desktop: {version} ({digest})')


if __name__ == '__main__':
    main()
