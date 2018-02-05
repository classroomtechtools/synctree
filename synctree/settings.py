"""
Instructions for use:
> from dss.settings import setup_settings
> setup_settings(module)
# Another file
> import module_settings

(Note: The importable module's name is actually module.__name__ + '_settings')
"""

settings_ini_filename = 'settings.ini'

def setup_settings(package_with_settings_ini):
	"""
	Manipulates sys.modules to give us the ability to import the configparser object from anyway
	"""
	try:
		package_with_settings_ini.__file__
	except AttributeError:
		raise TypeError('Package is a namespace, not a full package; did you forget the __init__.py file?')
	from pathlib import Path
	import pkg_resources
	import inspect, os, sys

	path_to_package_parent = str(Path(inspect.getfile(package_with_settings_ini)))
	path_to_home = os.path.split(os.path.split(path_to_package_parent)[0])[0]
	input(path_to_home)
	path_to_settings = os.path.join(path_to_home, settings_ini_filename)

	import configparser
	settings = configparser.ConfigParser()

	# We'll add settings that we want to be automatic, such as path settings
	settings['DEFAULT']['user_home'] = os.getenv("HOME")
	settings['DEFAULT']['my_home'] = path_to_package_parent
	settings['DEFAULT']['package_home'] = path_to_home
	settings.read(path_to_settings)

	importable_settings_module_name = '{}_settings'.format(package_with_settings_ini.__name__)
	sys.modules[importable_settings_module_name] = settings

	return settings