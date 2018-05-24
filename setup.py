import os
import sys
from setuptools import setup, find_packages
from tethys_apps.app_installation import custom_develop_command, custom_install_command

### Apps Definition ###
app_package = 'time_series_script_manager'
release_package = 'tethysapp-' + app_package
app_class = 'time_series_manager.app:TimeSeriesScriptManager'
app_package_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tethysapp', app_package)

### Python Dependencies ###
dependencies = ['hs_restclient', 'lxml', 'ciso8601', 'requests', 'urllib2', 'netCDF4', 'suds', 'cython']

setup(
    name=release_package,
    version='0.0.1',
    tags='&quot;Time Series&quot;, &quot;CUAHSI&quot;, &quot;HydroShare&quot;',
    description='This application is designed to launch Python scripts using Google Colaboratory',
    long_description='',
    keywords='',
    author='Matthew Bayles',
    author_email='',
    url='',
    license='',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    namespace_packages=['tethysapp', 'tethysapp.' + app_package],
    include_package_data=True,
    zip_safe=False,
    install_requires=dependencies,
    cmdclass={
        'install': custom_install_command(app_package, app_package_dir, dependencies),
        'develop': custom_develop_command(app_package, app_package_dir, dependencies)
    }
)
