"""
A hacky module that copies over @loader_path references
that py2app misses.

The libraries are pulled from $HOME/anaconda
"""
import fnmatch
import os
import subprocess
import shutil

def loader_paths(obj_file):
    """
    Return absolute paths to all shared_library references
    within an object file that begin with @loader_path

    Parameters
    ----------
    obj_file : Path to the object file to inspect
    """
    loader_path = os.path.abspath(os.path.split(obj_file)[0])

    p = subprocess.Popen(['otool', '-L', obj_file], stdout=subprocess.PIPE)
    p.wait()
    deps = p.stdout.readlines()[1:]

    deps = [d.strip().split()[0] for d in deps]
    deps = [os.path.join(loader_path, d[13:])
            for d in deps if d.startswith('@loader')]
    return deps


def find_in_anaconda(path):
    """Given an absolute path to a dylib file, return
    the path to the equivalent file in $HOME/anaconda/lib, if present.
    Otherwise, returns None
    """

    libdir = os.path.join(os.environ['HOME'], 'anaconda', 'lib')
    base, file = os.path.split(path)
    target = os.path.join(libdir, file)
    if os.path.exists(target):
        return target


def copy_from_anaconda(path, tld):
    """
    Given the path to a missing dylib file,
    try to copy the file over from anaconda

    Parameters
    ----------
    path : string
        Path to a dynamic library that is missing
    tld : Top level directory. Do not copy files above this directory

    Raises
    -------
    ValueError, if the library is not found in anaconda,
    or the target path is above the top-level directory
    """
    if not path.startswith(tld):
        raise ValueError("Attempting to copy a file above outside"
                         "of the top level directory\n"
                         "\tTop Level Directory: %s\n"
                         "\tTarget destination:  %s" % (path, tld))
    src = find_in_anaconda(path)
    if src is None:
        raise ValueError("Library not found in Anaconda: %s" % path)
    print 'copy %s to %s' % (src, path)
    shutil.copyfile(src, path)


def repair_missing_libraries(path, tld):
    """
    Given a path to an object file,
    detect and repair references to any missing shared librarires
    referenced within the file.

    Parameters
    ----------
    path : str
         path to an object file
    tld : str
        path of top level directory. No files will be copied above this
        directory
    """
    for lp in loader_paths(path):
        if os.path.exists(lp):
            continue
        try:
            copy_from_anaconda(lp, tld)
        except Exception as e:
            print 'Error fixing dependencies for %s' % path
            print e
            continue


def repair(tld):
    """Fix missing shared library references for object files in a directory

    The top level directory is scanned for .so and .dylib files.
    Each one is inspected for library references begging with @loader_path,
    that are not contained within tld. These missing libraries
    are then copied into the correct location from $HOME/anaconda/lib
    """
    for root, dirnames, filenames in os.walk(tld):
        for filename in fnmatch.filter(filenames, '*.so'):
            path = os.path.join(root, filename)
            repair_missing_libraries(path, tld)

        for filename in fnmatch.filter(filenames, '*.dylib'):
            path = os.path.join(root, filename)
            repair_missing_libraries(path, tld)

    shutil.rmtree(os.path.join(tld, 'Contents', 'Resources', 'qt_menu.nib'),
                  ignore_errors=True)
    shutil.copytree(os.path.join(os.environ['HOME'], 'anaconda',
                                 'python.app', 'Contents',
                                 'Resources', 'qt_menu.nib'),
                    os.path.join(tld, 'Contents', 'Resources', 'qt_menu.nib'))
