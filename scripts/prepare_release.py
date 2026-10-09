"""Validate an explicit release request and package only public invented files."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tomllib
import zipfile


def request():
    data = json.loads(Path('.github/release-request.json').read_text())
    if set(data) != {'version', 'expected_parent'}:
        raise ValueError('Release request must declare exactly version and expected_parent.')
    version = data['version']
    if not isinstance(version, str) or not re.fullmatch(r'0\.[0-9]+\.[0-9]+', version):
        raise ValueError('Use an explicit experimental 0.x.y version.')
    if tomllib.loads(Path('pyproject.toml').read_text())['project']['version'] != version:
        raise ValueError('Requested version differs from the package.')
    parent = data['expected_parent']
    if not isinstance(parent, str) or not re.fullmatch(r'[0-9a-f]{40}', parent):
        raise ValueError('Expected parent must be a full commit SHA.')
    actual_parent = subprocess.check_output(['git', 'rev-parse', 'HEAD^'], text=True).strip()
    if actual_parent != parent:
        raise ValueError('Release request no longer has its reviewed parent; do not retag.')
    changes = subprocess.check_output(['git', 'diff', '--name-only', 'HEAD^', 'HEAD'], text=True).splitlines()
    if changes != ['.github/release-request.json']:
        raise ValueError('The release request commit must change only its explicit request file.')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    if os.environ.get('GITHUB_SHA', head) != head:
        raise ValueError('Checkout differs from the workflow commit.')
    if not Path(f'docs/releases/v{version}.md').is_file():
        raise ValueError('Release notes are missing.')
    return version


def package(version):
    expected = {'SYNTHETIC_GRAIN', 'SYNTHETIC_CORN', 'SYNTHETIC_RAPESEED', 'EUR_PLN', 'EUR_USD', 'USD_PLN'}
    html = Path('docs/index.html').read_text()
    data = json.loads(re.search(r'<script id="dataset" type="application/json">(.*?)</script>', html, re.S)[1])
    if set(data) != expected or any(entry['source'] != 'SYNTHETIC' for entry in data.values()):
        raise ValueError('Release browser data must contain only the six invented instruments.')
    if sum(len(entry['views']) for entry in data.values()) != 9:
        raise ValueError('Unexpected public view inventory.')
    if any(view.get('as_of') != '2026-10-06' for entry in data.values() for view in entry['views'].values()):
        raise ValueError('Unexpected public example cutoff.')
    if Path('docs/seasonlens-import-template.xlsx').read_bytes() != base64.b64decode(Path('src/seasonlens/import_template.xlsx.b64').read_text().strip(), validate=True):
        raise ValueError('Published and bundled templates differ.')
    dist = Path('dist')
    dist.mkdir(exist_ok=True)
    archive = dist / f'seasonlens-browser-v{version}.zip'
    files = {'docs/index.html': 'index.html', 'docs/walkthrough.html': 'walkthrough.html',
             'docs/seasonlens-import-template.xlsx': 'seasonlens-import-template.xlsx',
             'docs/sample_prices.csv': 'sample_prices.csv', 'docs/layout-check.html': 'layout-check.html',
             'LICENSE': 'LICENSE', 'src/seasonlens/vendor/LICENSE': 'SHEETJS-LICENSE.txt'}
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED) as bundle:
        for source, target in files.items():
            bundle.write(source, target)
        bundle.writestr('README-browser.txt', f'SeasonLens {version}\nExtract this complete folder, then open index.html. Open walkthrough.html for the wheat + EUR/PLN example. All built-in observations and the workbook are invented. Browser imports disappear on reload. Report HTML download saves visible selected results; PDF saving depends on the browser. This package includes no data collector or running server. Code/examples: MIT; bundled SheetJS: Apache-2.0.\n')
    wheel = dist / f'seasonlens-{version}-py3-none-any.whl'
    source = dist / f'seasonlens-{version}.tar.gz'
    for path in (wheel, source):
        if not path.is_file():
            raise ValueError(f'Missing distribution: {path.name}')
    with (dist / 'SHA256SUMS').open('x') as sums:
        for path in (wheel, source, archive):
            sums.write(f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n')
    print(f'Packaged {version}: wheel, source, invented browser ZIP and SHA256SUMS.')


def verify_assets(version, result_path):
    remote = json.loads(Path(result_path).read_text())
    expected = [f'seasonlens-{version}-py3-none-any.whl', f'seasonlens-{version}.tar.gz',
                f'seasonlens-browser-v{version}.zip', 'SHA256SUMS']
    if remote.get('tag_name') != f'v{version}' or remote.get('draft') is not True:
        raise ValueError('Verify only the matching unpublished draft.')
    assets = remote.get('assets', [])
    if len(assets) != len(expected) or {a['name'] for a in assets} != set(expected):
        raise ValueError('Draft asset inventory must match exactly; unexpected attachments reject.')
    for asset in assets:
        content = (Path('dist') / asset['name']).read_bytes()
        digest = 'sha256:' + hashlib.sha256(content).hexdigest()
        if asset.get('state') != 'uploaded' or asset.get('size') != len(content) or asset.get('digest') != digest:
            raise ValueError(f'Draft asset did not verify: {asset["name"]}')
    print('All four draft assets match local sizes and SHA-256 digests.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--package', action='store_true')
    mode.add_argument('--verify-assets')
    args = parser.parse_args()
    version = request()
    if args.package:
        package(version)
    elif args.verify_assets:
        verify_assets(version, args.verify_assets)
    else:
        if 'GITHUB_ENV' not in os.environ:
            raise SystemExit('Preflight requires the workflow environment.')
        with open(os.environ['GITHUB_ENV'], 'a') as env:
            env.write(f'RELEASE_VERSION={version}\nRELEASE_TAG=v{version}\n')
        print(f'Explicit release request validated: v{version}')
