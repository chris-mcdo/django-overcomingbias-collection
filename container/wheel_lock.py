"""Generate exact, hashed offline install requirements from the selected wheels."""
from email.parser import BytesParser
import hashlib
from pathlib import Path
import re
import sys
import zipfile

folder = Path(sys.argv[1])
requirements = {}
for wheel in sorted(folder.glob('*.whl')):
    with zipfile.ZipFile(wheel) as archive:
        names = [name for name in archive.namelist()
                 if name.count('/') == 1 and name.endswith('.dist-info/METADATA')]
        if len(names) != 1:
            raise ValueError('Expected exactly one wheel metadata record')
        metadata = BytesParser().parsebytes(archive.read(names[0]))
    name = re.sub(r'[-_.]+', '-', metadata['Name']).lower()
    version = metadata['Version']
    if name in requirements:
        raise ValueError('Multiple wheels selected for ' + name)
    digest = hashlib.sha256(wheel.read_bytes()).hexdigest()
    requirements[name] = name + '==' + version + ' --hash=sha256:' + digest
if not requirements:
    raise ValueError('No wheels selected')
(folder / 'install.lock').write_text('\n'.join(requirements[name] for name in sorted(requirements)) + '\n')
print('Locked', len(requirements), 'wheel distributions for offline installation')
