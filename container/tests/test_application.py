"""Regression cases for package eligibility and reviewed-wheel integrity."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('application', ROOT / 'application.py')
app = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app)


class ApplicationTests(unittest.TestCase):
    def setUp(self):
        self.policy = json.loads((ROOT / 'application-policy.json').read_text())
        self.manifest = json.loads((ROOT / 'application.json').read_text())

    def release(self, name, version, **extra):
        filename = name.replace('-', '_') + '-' + version + '-py3-none-any.whl'
        return dict(filename=filename, url='https://files.pythonhosted.org/packages/' + filename,
                    digests={'sha256': 'a' * 64}, **extra)

    def test_selects_only_newer_compatible_stable_non_yanked_wheels(self):
        def fetch(url):
            name = url.split('/')[-2]
            current = self.manifest['packages'][name]['version']
            major, minor, patch_number = app.version(current)
            next_version = f'{major}.{minor}.{patch_number + 1}'
            upper = self.policy['packages'][name]['exclusive_maximum']
            return {'releases': {
                '0.0.1': [self.release(name, '0.0.1')],
                current: [self.release(name, current)],
                next_version: [self.release(name, next_version)],
                f'{major}.{minor}.90': [self.release(name, f'{major}.{minor}.90', yanked=True)],
                f'{major}.{minor}.91rc1': [self.release(name, f'{major}.{minor}.91rc1')],
                f'{major}.{minor}.92': [],
                upper: [self.release(name, upper)]}}
        result = app.resolve(self.policy, self.manifest, fetch)
        for name, item in result['packages'].items():
            self.assertEqual(app.version(item['version'])[-1], app.version(self.manifest['packages'][name]['version'])[-1] + 1)

    def test_no_eligible_release_fails_instead_of_downgrading(self):
        with self.assertRaises(ValueError):
            app.resolve(self.policy, self.manifest, lambda _: {'releases': {}})

    def test_manifest_rejects_bad_hash_and_external_download_and_range(self):
        name = 'django-overcomingbias-pages'
        for key, value in [('sha256', 'bad'), ('url', 'https://example.org/evil.whl'),
                           ('filename', '../escape.whl'), ('version', '99.0.0')]:
            with self.subTest(key=key):
                invalid = copy.deepcopy(self.manifest)
                invalid['packages'][name][key] = value
                with self.assertRaises(ValueError):
                    app.validate(self.policy, invalid)

    def test_hash_mismatch_never_writes_wheel(self):
        class Response:
            url = 'https://files.pythonhosted.org/packages/file.whl'
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self): return b'tampered wheel'
        with tempfile.TemporaryDirectory() as path, patch.object(app.urllib.request, 'urlopen', return_value=Response()):
            with self.assertRaises(ValueError):
                app.download(self.manifest, Path(path))
            self.assertEqual(list(Path(path).iterdir()), [])

    def test_good_hash_writes_exact_bytes(self):
        data = b'verified wheel'
        manifest = copy.deepcopy(self.manifest)
        for item in manifest['packages'].values():
            item['sha256'] = hashlib.sha256(data).hexdigest()
        class Response:
            url = 'https://files.pythonhosted.org/packages/file.whl'
            def __enter__(self): return self
            def __exit__(self, *args): pass
            def read(self): return data
        with tempfile.TemporaryDirectory() as path, patch.object(app.urllib.request, 'urlopen', return_value=Response()):
            app.download(manifest, Path(path))
            self.assertEqual(len(list(Path(path).iterdir())), 2)
            self.assertTrue(all(p.read_bytes() == data for p in Path(path).iterdir()))

    def test_package_metadata_and_policy_bounds_agree(self):
        import tomllib
        metadata = tomllib.loads((ROOT.parent / 'pyproject.toml').read_text())
        rule = self.policy['packages']['django-overcomingbias-pages']
        interval = '>=' + rule['minimum'] + ',<' + rule['exclusive_maximum']
        self.assertIn('django-overcomingbias-pages' + interval, metadata['project']['dependencies'])
        self.assertIn('django-overcomingbias-pages[production]' + interval, metadata['project']['optional-dependencies']['production'])
