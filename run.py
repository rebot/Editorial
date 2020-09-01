# -*- coding: utf-8 -*-
# In[0]: Imports
import os
import re
import io
import tarfile
import requests as r

# In[1]: Settings
s = r.session()
s.headers = {
    'User-Agent': 'trenson.gilles@gmail.com'
}

pkg = 'pyx'

uri = 'https://pypi.org/pypi/{package}/json'

# In[2]: Functions

def filter_release_version(release_details, version):
    return next(iter(filter(lambda x: version in x.get('python_version'), release_details)), None)

def select_build(pypi_info, build, version='2'):
    releases = pypi_info.get('releases', None)
    release_versions = sorted([v for v in releases.keys() if build in v])
    print release_versions
    if releases:
        release_details = releases.get(release_versions[-1], None)
        if release_details:
            specific_package = filter_release_version(release_details, version)
            if specific_package == None:
                specific_package = filter_release_version(release_details, 'source')
            return specific_package
    return None

def select_latest(pypi_info, version='2.7'):
    latest_release = pypi_info['info']['version']
    releases = pypi_info.get('releases', None)
    if releases:
        latest_release_details = releases[latest_release]
        specific_package = filter_release_version(latest_release_details, version)
        if specific_package == None:
             specific_package = filter_release_version(latest_release_details, 'source')
        return specific_package
    return None

# In[3]: Accessing the API

response = s.get(uri.format(package=pkg))

if response.status_code == 200:
    pypi_info = response.json()
    latest_release = select_build(pypi_info, build='0.12')
    # Check package type
    package_type = latest_release.get('packagetype', None)
    if package_type == 'bdist_wheel':
        print 'Wheel - I don\'t know what to do with this'
    elif package_type == 'sdist':
        print 'Building from source'
        package_uri = latest_release.get('url', None)
        filename = package_uri.split('/')[-1]
        download = s.get(package_uri, allow_redirects=True)
        download_object = io.BytesIO(download.content)
        # Decompress archive
        with tarfile.open(fileobj=download_object, mode='r') as archive:
            package_folder = re.compile(r'[^/]*?/'+re.escape(pkg.lower()))
            selection = [tarinfo for tarinfo in archive.getmembers() if package_folder.match(tarinfo.name)]
            base_path = selection[0].name.split('/')[0]
            for tarinfo in selection:
                tarinfo.name = tarinfo.name[len(base_path) + 1:]
            archive.extractall(members=selection)
        download_object.close()
else:
    print('Package not found')

# %%
