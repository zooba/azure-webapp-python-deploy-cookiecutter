{% set python_version_dir = cookiecutter.python_version|replace('.', '')|truncate(2, end='') %}

from __future__ import print_function

import json
import os, os.path
import sys

from fnmatch import filter as fnfilter
from xml.etree import ElementTree

if sys.version_info[0] < 3:
    from codecs import open

sys.path.insert(0, 'site')
try:
    from requests import Session
except ImportError:
    print("""Failed to import 'requests'. Please launch deployment from
one of the shell scripts, or 'pip install requests' and restart.""", file=sys.stderr)
    sys.exit(1)

VERBOSE = os.getenv('VERBOSE') not in {None, '', '0'} or '-v' in sys.argv

def get_publish_session():
    last_used_setting = os.path.join(os.path.abspath(__file__), '..', 'lastusedprofile.json')
    try:
        with open(last_used_setting, 'r', encoding='utf-8') as f:
            path = json.load(f)["path"]
    except (OSError, LookupError, json.JSONDecodeError):
        path = input("Please enter the path to your publishing profile: ").strip('"\'')

    try:
        profile = ElementTree.parse(path)
        data = profile.getroot().find('./publishProfile[@publishMethod="MSDeploy"]')

        session = Session()
        session.auth = data.get('userName'), data.get('userPWD')
        session.headers['If-Match'] = '*'   # allow replacing files on upload
        api_url = 'https://{}/api/'.format(data.get('publishUrl'))
    except OSError:
        print("Unable to read the profile at {}.".format(path), file=sys.stderr)
        print("Please restart deployment and provide the path to your publishing profile.", file=sys.stderr)
        try:
            os.unlink(last_used_setting)
        except OSError:
            pass
        sys.exit(2)

    try:
        with open(last_used_setting, 'w', encoding='utf-8') as f:
            json.dump({
                'path': path,
                'NOTE': 'Your profile contains secret information. It should not be checked into your repository.'
            }, f)
    except OSError:
        print("Unable to save profile path. You will need to provide the path again", file=sys.stderr)
        print("for your next deployment.", file=sys.stderr)

    return session, api_url

def get_deployment_files():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    ignore_file = next((os.path.join(root, f) for f in ['.gitignore', '.hgignore', '.tfignore', '.ignore']
                       if os.path.isfile(os.path.join(root, f))), None)
    if ignore_file:
        with open(ignore_file, 'r', encoding='utf-8') as f:
            ignore = set(line.strip() for line in f
                         if line and not line.lstrip().startswith('#') and not line.lstrip().startswith('//'))
        ignore.add(os.path.relpath(ignore_file, root))
    else:
        ignore = set()
    ignore.add(os.path.basename(os.path.dirname(os.path.abspath(__file__))))

    all_files = []
    for dirpath, dirnames, filenames in os.walk(root):
        reldirs = [os.path.relpath(os.path.join(dirpath, d), root) for d in dirnames]
        relfiles = [os.path.relpath(os.path.join(dirpath, f), root) for f in filenames]
        if ignore:
            remove = set(os.path.basename(d) for pat in ignore for d in fnfilter(reldirs, pat))
            if VERBOSE and remove:
                print('Excluding:\n  ' + '\n  '.join(remove))
            dirnames[:] = (d for d in dirnames if d not in remove)
            remove = set(os.path.basename(f) for pat in ignore for f in fnfilter(relfiles, pat))
            if VERBOSE and remove:
                print('Excluding:\n  ' + '\n  '.join(remove))
            filenames[:] = (f for f in filenames if f not in remove)
        all_files.extend((f, os.path.relpath(f, root).replace('\\', '/')) for f in 
            (os.path.join(dirpath, basef) for basef in filenames))

    return all_files

def publish(session, api_url, all_files):
    print('Uploading', len(all_files), 'files')
    for src, dest in all_files:
        if VERBOSE:
            print('  ', src, '->', dest)
        with open(src, 'rb') as f:
            r = session.put('{}vfs/site/wwwroot/{}'.format(api_url, dest), data=f, stream=True)
            r.raise_for_status()
    print('Upload complete')
    print()

    print('Executing pip install')

    cmd = {
        'command': r'D:\home\Python{{ python_version_dir }}\python.exe -m pip install -r D:\home\site\wwwroot\{{ requirements_filename }}',
        'dir': r'D:\home\site\wwwroot',
    }
    r = session.post('{}command'.format(api_url), json=cmd)
    if r.status_code != 200:
        print('pip install failed')
        if VERBOSE:
            print(r.json())
        sys.exit(2)
    print('pip install complete')
    print()

if __name__ == '__main__':
    session, api_url = get_publish_session()
    try:
        all_files = get_deployment_files()
        publish(session, api_url, all_files)
        sys.exit(0)
    finally:
        session.close()

