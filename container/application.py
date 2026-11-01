"""Select compatible stable packages; verify reviewed wheels before image builds."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parent
PACKAGES = {'django-overcomingbias-api', 'django-overcomingbias-pages'}


def version(value):
    if not isinstance(value, str) or not re.fullmatch(r'(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)', value):
        raise ValueError('Expected a stable three-component version')
    return tuple(map(int, value.split('.')))


def read_json(url):
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.load(response)


def validate(policy, manifest):
    if policy['schema'] != 1 or manifest['schema'] != 1:
        raise ValueError('Unsupported application manifest schema')
    version(policy['collection_version'])
    if manifest['collection_version'] != policy['collection_version']:
        raise ValueError('Collection version differs from reviewed policy')
    if set(policy['packages']) != PACKAGES or set(manifest['packages']) != PACKAGES:
        raise ValueError('Expected exactly the API and pages packages')
    for name, rule in policy['packages'].items():
        lower, upper = version(rule['minimum']), version(rule['exclusive_maximum'])
        item = manifest['packages'][name]
        if not lower <= version(item['version']) < upper:
            raise ValueError('Package outside compatibility interval: ' + name)
        filename = item['filename']
        expected = name.replace('-', '_') + '-' + item['version'] + '-py3-none-any.whl'
        if filename != expected:
            raise ValueError('Expected the universal wheel for ' + name)
        if not re.fullmatch(r'[0-9a-f]{64}', item['sha256']):
            raise ValueError('Invalid wheel digest')
        url = urllib.parse.urlsplit(item['url'])
        if (url.scheme != 'https' or url.netloc != 'files.pythonhosted.org'
                or url.query or url.fragment or url.path.rsplit('/', 1)[-1] != filename):
            raise ValueError('Expected a canonical PyPI wheel URL')
    return manifest


def resolve(policy, current, fetch=read_json):
    """Never downgrade, select prereleases, or select yanked distributions."""
    result = {'schema': 1, 'collection_version': policy['collection_version'], 'packages': {}}
    for name, rule in policy['packages'].items():
        lower, upper = version(rule['minimum']), version(rule['exclusive_maximum'])
        floor = max(lower, version(current['packages'][name]['version']))
        releases = fetch('https://pypi.org/pypi/' + name + '/json')['releases']
        choices = []
        for candidate, files in releases.items():
            try:
                selected = version(candidate)
            except ValueError:
                continue
            if not floor <= selected < upper:
                continue
            expected = name.replace('-', '_') + '-' + candidate + '-py3-none-any.whl'
            wheels = [f for f in files if f['filename'] == expected and not f.get('yanked', False)]
            if len(wheels) == 1:
                choices.append((selected, candidate, wheels[0]))
        if not choices:
            raise ValueError('No compatible non-yanked universal wheel for ' + name)
        _, selected, wheel = max(choices, key=lambda item: item[0])
        result['packages'][name] = dict(version=selected, filename=wheel['filename'],
            url=wheel['url'], sha256=wheel['digests']['sha256'])
    return validate(policy, result)


def download(manifest, directory):
    directory.mkdir(parents=True, exist_ok=True)
    for item in manifest['packages'].values():
        with urllib.request.urlopen(item['url'], timeout=60) as response:
            if urllib.parse.urlsplit(response.url).netloc != 'files.pythonhosted.org':
                raise ValueError('Unexpected wheel download redirect')
            data = response.read()
        if hashlib.sha256(data).hexdigest() != item['sha256']:
            raise ValueError('Published wheel hash differs from the reviewed manifest')
        (directory / item['filename']).write_bytes(data)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['validate', 'resolve', 'download', 'env'])
    parser.add_argument('--directory', type=Path, default=Path('/application-wheels'))
    args = parser.parse_args()
    policy = json.loads((ROOT / 'application-policy.json').read_text())
    path = ROOT / 'application.json'
    manifest = json.loads(path.read_text())
    if args.command == 'resolve':
        manifest = resolve(policy, manifest)
        path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    else:
        validate(policy, manifest)
    if args.command == 'download':
        download(manifest, args.directory)
    elif args.command == 'env':
        print('COLLECTION_VERSION=' + manifest['collection_version'])
        print('OBAPI_VERSION=' + manifest['packages']['django-overcomingbias-api']['version'])
        print('OBPAGES_VERSION=' + manifest['packages']['django-overcomingbias-pages']['version'])


if __name__ == '__main__':
    main()
