from setuptools import setup, Command
from subprocess import check_call, Popen, PIPE
from glob import glob
import time
import shutil
import os

import py2app.recipes
import PIL_RECIPE
import ipython_recipe
import glue_recipe

py2app.recipes.PIL.check = PIL_RECIPE.check
py2app.recipes.IPython = ipython_recipe
py2app.recipes.glue = glue_recipe

APP = ['Glue.py']
DATA_FILES = []
cmdclass = {}

OPTIONS = {
    'matplotlib_backends' : ['qt4agg'],
    'argv_emulation': True,
    'emulate_shell_environment': True,
    'packages': ['zmq', 'glue', 'astropy', 'matplotlib', 'pygments','scipy',
                 'numpy', 'IPython', 'skimage', 'pyavm', 'h5py', 'pytest'],
    'includes': ['PySide.QtCore', 'PySide.QtGui', 'PySide.QtScript',
                 'PySide.QtUiTools', 'PySide.QtXml', 'PySide.QtSvg'],
    'excludes': ['PyQt4', 'sip', 'TKinter', 'OpenGL'],
    'iconfile' : 'glue_icon.icns',
    'resources': ['glue_file_icon.icns'],
    'plist': dict(
        CFBundleDocumentTypes=[
            dict(
                CFBundleTypeRole='Viewer',
                CFBundleTypeName='Glue Session',
                CFBundleTypeExtensions=['glu'],
                CFBundleTypeIconFile='glue_file_icon.icns',
                LSHandlerRank='Owner'),
            dict(
                CFBundleTypeRole='Viewer',
                CFBundleTypeName='Flexible Image Transport System',
                CFBundleTypeIconFile='glue_file_icon.icns',
                CFBundleTypeExtensions=['fits', 'fit', 'fts'],
                ),
            dict(
                CFBundleTypeRole='Viewer',
                CFBundleTypeName='VO Table',
                CFBundleTypeIconFile='glue_file_icon.icns',
                CFBundleTypeExtensions=['vot'],
                ),
            dict(
                CFBundleTypeRole='Viewer',
                CFBundleTypeName='Comma Separated Value File',
                CFBundleTypeIconFile='glue_file_icon.icns',
                CFBundleTypeExtensions=['csv']
                ),
            ]
        ),
    }


class Fix(Command):
    user_options = []
    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def trim_packages(self):
        """Remove big files in external dependencies that Glue doesn't need"""

        shutil.rmtree('dist/Glue.app/Contents/Resources/'
                      'lib/python2.7/matplotlib/tests/'
                      'baseline_images', ignore_errors=True)
        shutil.rmtree('dist/Glue.app/Contents/Resources/'
                      'lib/python2.7/scipy/weave', ignore_errors=True)

    def run(self):
        from fix_dylib import repair
        repair('dist/Glue.app')
        self.trim_packages()

cmdclass['fix'] = Fix

class Upload(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def glue_git_hash(self):
        p = Popen('git rev-parse HEAD'.split(), stdout=PIPE, cwd='glue')
        p.wait()
        return p.stdout.read().strip()[:10]

    def file_name(self):
        timestamp = time.strftime('%Y-%m-%d_%H%M%S', time.gmtime())
        hash = self.glue_git_hash()
        path = '{timestamp}_{hash}.dmg'.format(hash=hash, timestamp=timestamp)
        return path

    def run(self):
        cwd = os.path.abspath('dist')
        check_call('macdeployqt Glue.app -dmg'.split(), cwd=cwd)
        print "created DMG"
        self.upload()
        print "Uploaded"

    def upload(self):
        from dbox import put
        with open('dist/Glue.dmg') as infile:
            put(infile, self.file_name())

cmdclass['upload'] = Upload


class BuildGlue(Command):
    user_options = [
        ('ref=', 'r', 'Glue git reference to build')
        ]

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def clone(self):
        check_call('rm -rf glue'.split())
        check_call('git clone git://github.com/glue-viz/glue.git'.split())

    def checkout(self, ref):
        check_call(('git checkout %s' % ref).split(), cwd='glue')

    def run(self):
        self.clone()
        check_call('python setup.py install'.split(), cwd='glue')

cmdclass['glue'] = BuildGlue

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    cmdclass=cmdclass
)
