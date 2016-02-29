# We have to manually get the entry points and patch them in glue because py2app
# doesn't support entry points. We actually implement a solution that doesn't
# use entry points or pkg_resources at all.

import pkg_resources

# List all bundled plugin packages here
PACKAGES = ['glueviz']

# list_plugin_entry_points

patch = """
import importlib

class EntryPoint(object):
    def __init__(self, name, module_name, attrs=None):
        self.name = name
        self.module_name = module_name
        self.attrs = attrs
    def load(self):
        module = importlib.import_module(self.module_name)
        function_name = self.attrs[0]
        return getattr(module, function_name)

def iter_plugin_entry_points():
"""

for package in PACKAGES:
    dist = pkg_resources.working_set.by_key[package]
    entry_map = dist.get_entry_map()
    for key, entry_points in entry_map.items():
        if key == 'glue.plugins':
            for name, entry_point in entry_points.items():
                patch += "    yield EntryPoint('{name}', '{module_name}', attrs={attrs})\n".format(name=name, module_name=entry_point.module_name, attrs=entry_point.attrs)

patch += """
from glue import _plugin_helpers
_plugin_helpers.iter_plugin_entry_points = iter_plugin_entry_points
"""

print("Patching Glue with:")
print(patch)

def check(cmd, mg):
    from cStringIO import StringIO
    return dict(prescripts=[StringIO(patch)])
