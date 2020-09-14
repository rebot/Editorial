#coding: utf-8
import os
import io
import re
import ui
import sys
import shutil
import urllib
import zipfile
import tarfile
import workflow
import requests as r
import console

# In[0]: Settings

s = r.session()
s.headers = {
    'User-Agent': 'trenson.gilles@gmail.com'
}

uri = 'https://pypi.org/pypi/{package}/json'

python2packages = {
    'pyx': '0.12'
}

# In[1]: Helper functions

def filter_release_version(release_details, version):
    return next(iter(filter(lambda x: version in x.get('python_version'), release_details)), None)

def select_build(pypi_info, build, version='2'):
    releases = pypi_info.get('releases', None)
    release_versions = sorted([v for v in releases.keys() if build in v])
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

# In[2]: UI Class

class TextFieldDelegate (object):
	def textfield_did_begin_editing(self, textfield):
		textfield.text_color = 'black'

class InputView(ui.View):
	
	def __init__(self):
		# Size
		self.width = 300
		self.height = 80
		# Attributes
		self.name = 'Install'
		self.tint_color = 'white'
		self.background_color = '#545659'
		self.border_width = 2
		self.border_color = '#545659'
		# Initialise
		self.initialise()
		# Add controls
		self.add_controls()
	
	def initialise(self):
		# Add label
		label = ui.Label(text='pip install')
		label.name = 'label_1'
		label.frame = (15, self.height * 0.5 - 20, 90, 40)
		label.flex = 'TB'
		label.font = ('<system-bold>', 18)
		label.text_color = '#FAFAFA'
		self.add_subview(label)
		textfield = ui.TextField()
		textfield.frame = (105, self.height * 0.5 - 20, 185, 40)
		textfield.placeholder = 'python package'
		textfield.flex = 'TB'
		textfield.autocapitalization_type = ui.AUTOCAPITALIZE_NONE
		textfield.clear_button_mode = 'while_editing'
		textfield.action = self.request_download
		textfield.delegate = TextFieldDelegate()
		self.add_subview(textfield)
	
	def add_controls(self):
		# Add button
		search_button = ui.ButtonItem(title='Search')
		self.right_button_items = [search_button]
		# Refresh view
		self.set_needs_display()
	
	@ui.in_background
	def request_download(self, sender):
		# Check if valid package name
		pkg = sender.text.lower()
		
		response = s.get(uri.format(package=pkg))

		if response.status_code == 200:
			pypi_info = response.json()
			if pkg in python2packages.keys():
				latest_release = select_build(pypi_info, build=python2packages[pkg])
			else: 
				latest_release = select_latest(pypi_info, version='2.7')
				# Check package type
				package_type = latest_release.get('packagetype', None)
				# Binary distribution - C-bindings compiled
				if package_type == 'bdist_wheel': 
					console.alert('Wheel - I don\'t know what to do with this')
				# Source distribution - C-bindings not compiled yet
				elif package_type == 'sdist': 
					package_uri = latest_release.get('url', None) 
					filename = os.path.basename(package_uri)
					extension = os.path.splitext(package_uri)[1]
					download = s.get(package_uri, allow_redirects=True)
					download_object = io.BytesIO(download.content)
					# Decompress archive
					if '.tar.gz' in filename:
						with tarfile.open(fileobj=download_object, mode='r') as archive:
							package_folder = re.compile(r'[^/]*?/'+re.escape(pkg)+r'[/$]')
							selection = [tarinfo for tarinfo in archive.getmembers() if package_folder.match(tarinfo.name)]
							base_path = selection[0].name.split('/')[0]
							for tarinfo in selection:
								tarinfo.name = tarinfo.name[len(base_path) + 1:]
							archive.extractall(members=selection, path=os.path.expanduser('~/Documents/site-packages'))
						console.hud_alert('Package installed!')
						download_object.close()
						self.close()
						workflow.stop()
					elif extension == '.zip':
						with zipfile.ZipFile(file=download_object, mode='r') as archive:
							package_folder = re.compile(r'.*?/('+re.escape(pkg)+r'(?:/.*$|$))')
							selection = [name for name in archive.namelist() if package_folder.match(name)]
							for member in selection:
								filename = package_folder.match(member).group(1)
								path = os.path.join(os.path.expanduser('~/Documents/site-packages'), filename)
								source = archive.open(member)
								# Check if path exists
								if not os.path.exists(os.path.dirname(path)):
									os.makedirs(os.path.dirname(path))
								target = open(path, 'wb')
								with source, target:
									shutil.copyfileobj(source, target)
						console.hud_alert('Package installed!')
						download_object.close()
						self.close()
						workflow.stop()
		else:
			sender.text_color = '#c7180c'
			console.hud_alert('Package not found')		

input_view = InputView()
input_view.present('sheet', hide_title_bar=True)