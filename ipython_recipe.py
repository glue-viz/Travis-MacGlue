"""
IPythons Qt introspection breaks with py2app's packaging style.
Since we know PySide is provided, we monkey-patch the test
"""
from cStringIO import StringIO

s = StringIO("import IPython.external.qt_loaders; IPython.external.qt_loaders.has_binding = lambda x: x == 'pyside'")
def check(cmd, mg):
    return dict(prescripts=[s])
