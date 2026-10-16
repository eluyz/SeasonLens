"""Finalize only an explicitly pinned existing draft; never create or move a tag."""
import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import tomllib
import zipfile


def git(*args):
    return subprocess.check_output(['git', *args])


def browser_mapping(version):
    """Frozen inventories are explicit; future formats require a fresh review."""
    legacy = {'index.html': 'docs/index.html', 'walkthrough.html': 'docs/walkthrough.html',
              'seasonlens-import-template.xlsx': 'docs/seasonlens-import-template.xlsx',
              'sample_prices.csv': 'docs/sample_prices.csv', 'layout-check.html': 'docs/layout-check.html',
              'LICENSE': 'LICENSE', 'SHEETJS-LICENSE.txt': 'src/seasonlens/vendor/LICENSE'}
    if version == '0.1.0':
        return legacy
    if version not in {'0.1.1', '0.1.2', '0.1.3'}:
        raise ValueError('Unsupported frozen browser inventory version.')
    return {**legacy, 'walkthrough-pl.html': 'docs/walkthrough-pl.html',
            'pilot/index.html': 'docs/pilot/index.html',
            'pilot/README_PL.md': 'docs/pilot/README_PL.md',
            'pilot/README_EN.md': 'docs/pilot/README_EN.md',
            'pilot/FEEDBACK_PL.md': 'docs/pilot/FEEDBACK_PL.md',
            'pilot/FEEDBACK_EN.md': 'docs/pilot/FEEDBACK_EN.md',
            'pilot/OPERATIONS.md': 'docs/PILOT_OPERATIONS.md'}


def frozen_browser_readme(target, version):
    """Read a restricted literal template without executing any tagged code."""
    source = ast.parse(git('show', target + ':scripts/prepare_release.py').decode())
    matches = [node for node in ast.walk(source)
               if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
               and isinstance(node.func.value, ast.Name) and node.func.value.id == 'bundle'
               and node.func.attr == 'writestr' and len(node.args) == 2 and not node.keywords
               and isinstance(node.args[0], ast.Constant) and node.args[0].value == 'README-browser.txt']
    if len(matches) != 1 or not isinstance(matches[0].args[1], ast.JoinedStr):
        raise ValueError('Unsupported frozen browser README template.')
    parts = []
    for part in matches[0].args[1].values:
        if isinstance(part, ast.Constant) and isinstance(part.value, str):
            parts.append(part.value)
        elif (isinstance(part, ast.FormattedValue) and isinstance(part.value, ast.Name)
              and part.value.id == 'version' and part.conversion == -1 and part.format_spec is None):
            parts.append(version)
        else:
            raise ValueError('Unsupported frozen browser README interpolation.')
    return ''.join(parts).encode('utf-8')


def request():
    data = json.loads(Path('.github/release-finalization.json').read_text())
    if set(data) != {'version', 'expected_parent', 'tag_commit', 'release_id', 'assets'}:
        raise ValueError('Unexpected finalization fields.')
    version = data['version']
    if not isinstance(version, str) or not re.fullmatch(r'0\.[0-9]+\.[0-9]+', version):
        raise ValueError('Invalid experimental version.')
    browser_mapping(version)
    for field in ('expected_parent', 'tag_commit'):
        if not isinstance(data[field], str) or not re.fullmatch(r'[0-9a-f]{40}', data[field]):
            raise ValueError('Use full reviewed commit identities.')
    if type(data['release_id']) is not int or data['release_id'] <= 0:
        raise ValueError('Use the exact existing draft ID.')
    head = git('rev-parse', 'HEAD').decode().strip()
    if head != os.environ.get('GITHUB_SHA', head):
        raise ValueError('Checkout differs from the finalization workflow commit.')
    if git('rev-parse', 'HEAD^').decode().strip() != data['expected_parent']:
        raise ValueError('Reviewed finalization parent differs.')
    if git('diff', '--name-only', 'HEAD^', 'HEAD').decode().splitlines() != ['.github/release-finalization.json']:
        raise ValueError('Finalization commit must change only its request.')
    subprocess.run(['git', 'merge-base', '--is-ancestor', data['tag_commit'], data['expected_parent']], check=True)
    target = data['tag_commit']
    original = json.loads(git('show', target + ':.github/release-request.json'))
    if original != {'version': version, 'expected_parent': git('rev-parse', target + '^').decode().strip()}:
        raise ValueError('Original release request is not the reviewed version/parent.')
    if git('diff', '--name-only', target + '^', target).decode().splitlines() != ['.github/release-request.json']:
        raise ValueError('Original tag source is not a request-only commit.')
    if tomllib.loads(git('show', target + ':pyproject.toml').decode())['project']['version'] != version:
        raise ValueError('Tagged package version differs.')
    names = {f'seasonlens-{version}-py3-none-any.whl', f'seasonlens-{version}.tar.gz',
             f'seasonlens-browser-v{version}.zip', 'SHA256SUMS'}
    assets = data['assets']
    if not isinstance(assets, list) or len(assets) != 4 or {a['name'] for a in assets} != names:
        raise ValueError('Pin exactly the four original assets.')
    for asset in assets:
        if set(asset) != {'name', 'id', 'size', 'digest'} or type(asset['id']) is not int or asset['id'] <= 0:
            raise ValueError('Invalid asset identity.')
        if type(asset['size']) is not int or not 0 < asset['size'] < 50 * 1024 * 1024:
            raise ValueError('Invalid asset size.')
        if not re.fullmatch(r'sha256:[0-9a-f]{64}', asset['digest']):
            raise ValueError('Pin the complete original SHA-256 digest.')
    if len({a['id'] for a in assets}) != 4:
        raise ValueError('Asset IDs must be unique.')
    return data


def verify(data, result_path, downloaded):
    mapping = browser_mapping(data['version'])
    remote = json.loads(Path(result_path).read_text())
    if remote.get('id') != data['release_id'] or remote.get('tag_name') != 'v' + data['version'] or remote.get('draft') is not True:
        raise ValueError('Only the pinned unpublished draft may be finalized.')
    assets = remote.get('assets', [])
    if len(assets) != 4:
        raise ValueError('Unexpected remote attachments.')
    expected = {a['name']: a for a in data['assets']}
    if {a['name'] for a in assets} != set(expected):
        raise ValueError('Unexpected remote asset names.')
    for asset in assets:
        pinned = expected[asset['name']]
        if asset.get('state') != 'uploaded' or any(asset.get(k) != v for k, v in pinned.items()):
            raise ValueError('Existing draft assets changed; require new review.')
        if downloaded:
            content = (Path('dist') / asset['name']).read_bytes()
            if len(content) != pinned['size'] or 'sha256:' + hashlib.sha256(content).hexdigest() != pinned['digest']:
                raise ValueError('Downloaded bytes differ from the pinned draft.')
    if not downloaded:
        return
    lines = (Path('dist') / 'SHA256SUMS').read_text().splitlines()
    wanted = {a['digest'][7:] + '  ' + a['name'] for a in data['assets'] if a['name'] != 'SHA256SUMS'}
    if len(lines) != 3 or set(lines) != wanted:
        raise ValueError('Checksum manifest differs from downloaded assets.')
    with zipfile.ZipFile(Path('dist') / f'seasonlens-browser-v{data["version"]}.zip') as bundle:
        if len(bundle.namelist()) != len(mapping) + 1 or set(bundle.namelist()) != set(mapping) | {'README-browser.txt'}:
            raise ValueError('Browser archive has unexpected files.')
        for name, source in mapping.items():
            if bundle.read(name) != git('show', data['tag_commit'] + ':' + source):
                raise ValueError('Frozen browser bytes differ from the unchanged tag.')
        if bundle.read('README-browser.txt') != frozen_browser_readme(data['tag_commit'], data['version']):
            raise ValueError('Frozen browser README differs from the unchanged tag.')
    print('Pinned draft IDs, downloaded bytes, checksums and frozen tagged browser verified.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify')
    parser.add_argument('--downloaded', action='store_true')
    args = parser.parse_args()
    data = request()
    if args.verify:
        verify(data, args.verify, args.downloaded)
    else:
        with open(os.environ['GITHUB_ENV'], 'a') as env:
            env.write(f'RELEASE_VERSION={data["version"]}\nRELEASE_TAG=v{data["version"]}\nRELEASE_ID={data["release_id"]}\nTAG_COMMIT={data["tag_commit"]}\n')
        print('Reviewed request to finalize the unchanged existing draft validated.')
