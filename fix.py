"""
A hacky module that tries to fix some shortcomings of py2app.

In particular, the .app bundle is re-scanned for external references
to resources that are not present in an OSX base install. These references
are fixed by moving resources inside the bundle and/or re-pointing
references.
"""
import os
import subprocess
import shutil
import logging

logging.basicConfig(level=logging.DEBUG)


# set of the files included on a base OSX Lion install
with open('osx_base_system.txt') as infile:
    BASE_SYSTEM = set(l.strip() for l in infile.readlines())


def otool(pth, exec_pth):
    """
    Return a dict of shared libraries that an object file uses.
    Wrapper around otool -L

    Parameters
    ----------
    pth : Path to a file to inspect
    exec_pth : The executable path to expand @executable_path into

    Returns
    -------
    a dict that maps install_name -> resolved_name, for each shared
    library reference in pth.

    install_name is what actually appears in the file, and
    includes wildcards like @loader_path. resolved_name is a fully-expanded
    file path
    """
    #XXX This also returns the id of pth, which should be handled better
    loader_pth = os.path.dirname(pth)

    p = subprocess.Popen(['otool', '-L', pth], stdout=subprocess.PIPE)
    p.wait()
    deps = p.stdout.readlines()
    deps = [d for d in deps if d.startswith('\t')]
    if len(deps) == 0:
        return {}

    deps = [d.split('(')[0].strip() for d in deps]

    def resolve(d):
        result = d.replace('@loader_path', loader_pth)
        result = result.replace('@executable_path', exec_pth)
        if not result.startswith('/'):
            result = os.path.join(loader_pth, result)
        return result

    deps = {d: resolve(d) for d in deps}
    return deps


def check_exists(pth, app_base):
    """Test whether a path will exist on an install to a base OSX system

    Checks whether pth is nested inside an application bundle,
    or present in a base OSX install

    Parameters
    ----------
    pth : str
      Fully-resolved reference to a shared library
    app_base : str
      The top-level-directory of an application bundle

    Returns
    -------
    True if pth exists within app_base, or is present on an OSX base system
    """
    if pth.startswith(app_base) and os.path.exists(pth):
        return True
    return pth in BASE_SYSTEM


def change_install_name(pth, frm, to):
    """
    Rename a library reference within a mach-o binary

    Parameters
    ----------
    pth : str
      Path to a Mach-O binary
    frm : str
      Library reference to rename
    to : str
      New name
    """
    #XXX better way to disambiguate this: check if this
    #    chould be changed via -id or -change
    if os.path.split(pth)[1] == os.path.split(to)[1]:
        logging.info("Change install name id:\t %s", to)
        subprocess.check_call(['install_name_tool', '-id', to, pth])
        return

    logging.info("install_name change: %s\n\told: %s\n\tnew: %s", pth, frm, to)
    try:
        subprocess.check_call(['install_name_tool', '-change', frm, to, pth])
    except subprocess.CalledProcessError:
        # not sure if this catches all invalid renames
        logging.error("install_name_tool unsuccessful (name too long?)")


def _find(pth, tld):
    # search a directory `tld` for a file `pth`
    for root, _, files in os.walk(tld):
        if pth in files:
            result = os.path.join(root, pth)
            assert os.path.exists(result)
            return result


def find_sys(pth):
    """ Search some standard shared library locations for a file """
    if '/usr/lib/' + pth not in BASE_SYSTEM:
        return None
    return _find(pth, '/usr/lib')


def find_miniconda(pth):
    """ Search $HOME/miniconda/lib for a file """
    return _find(pth, os.path.join(os.environ['HOME'], 'miniconda', 'lib'))


def find_app(pth, app):
    """ Search the app bundle for a file """
    result = _find(pth, app)
    if result is None:
        return None
    return result.replace(os.path.join(app, 'Contents'),
                          '@executable_path/..')


def iter_references(app):
    """Walk the application yield tuples of file, refname, refpath"""
    exec_path = os.path.join(app, 'Contents', 'MacOS')
    for root, _, filenames in os.walk(app):
        for fname in filenames:
            fname = os.path.join(root, fname)
            for ref, refpath in otool(fname, exec_path).items():
                yield fname, ref, refpath


def fix_references(app):
    """
    Scan an application directory for shared library references,
    and edit as necessary so that the application runs on a base OSX install

    This modifies the application directory in the following ways:
    - Invalid shared library references are changed to system-references,
      if possible
    - If not, but the reference is found elsewhere, it is copied into
      the application bundle and the reference is repointed

    Returns True if the directory was modified, false otherwise
    """

    print("FIX REFERENCES")
    changed = False
    for fname, ref, refpath in iter_references(app):

        print(fname, ref, refpath)

        # reference ok
        if check_exists(refpath, app):
            continue

        print ref, refpath

        _, refname = os.path.split(refpath)

        # reference exists in base OSX
        sys = find_sys(refname)
        if sys:
            change_install_name(fname, ref, sys)
            continue

        # reference exists elsewhere in application bundle
        bun = find_app(refname, app)
        if bun:
            change_install_name(fname, ref, bun)
            continue

        # reference exists in miniconda
        ana = find_miniconda(refname)
        if ana:
            dest = os.path.join(app, 'Contents', 'Resources', refname)
            if os.path.exists(dest):
                continue
            changed = True
            dest_name = '@executable_path/../Resources/' + refname
            shutil.copyfile(ana, dest)
            change_install_name(fname, ref, dest_name)
            continue

        logging.warn('Could not fix bad reference: %s'
                     '\n\t referenced from %s', ref, fname)
    return changed


def copy_nib_file(tld):
    """ Copy the qt nib file into the application bundle"""
    shutil.rmtree(os.path.join(tld, 'Contents', 'Resources', 'qt_menu.nib'),
                  ignore_errors=True)
    shutil.copytree(os.path.join(os.environ['HOME'], 'miniconda',
                                 'python.app', 'Contents',
                                 'Resources', 'qt_menu.nib'),
                    os.path.join(tld, 'Contents', 'Resources', 'qt_menu.nib'))


def main(app):
    if not app.endswith('.app'):
        raise ValueError("Input must be the full path to Glue.app")
    app = os.path.abspath(app)
    copy_nib_file(app)

    # this requires multiple passes, until nothing changes
    do = True
    while do:
        do = fix_references(app)
