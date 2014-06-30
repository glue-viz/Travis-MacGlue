"""
The AstropyLogger introspects imported modules. This sometimes
triggers ImportErrors for the lazily-loaded email module (which
py2app doesn't support well).

We circumvent this by removing problematic entries from sys.modules
"""

from cStringIO import StringIO

patch = """
import astropy.logger
astropy.logger.log.disable_warnings_logging()
"""

def check(cmd, mg):
    return dict(prescripts=[StringIO(patch)])
