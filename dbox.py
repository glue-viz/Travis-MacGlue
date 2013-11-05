"""
Store collections of files on dropbox, retaining only the
newest items in each collection.
"""

import os
import time

from dropbox import session, client

consumer_key = os.environ['DROPBOX_CONSUMER_KEY']
consumer_secret = os.environ['DROPBOX_CONSUMER_SECRET']
access = 'app_folder'

auth_key = os.environ['DROPBOX_AUTH_KEY']
auth_secret = os.environ['DROPBOX_AUTH_SECRET']


def get_client():
    sess = session.DropboxSession(consumer_key, consumer_secret, access)
    sess.set_token(auth_key, auth_secret)
    return client.DropboxClient(sess)


def ls_timesort(path='/'):
    c = get_client()
    md = c.metadata(path)
    if not md['is_dir']:
        raise ValueError('Must call ls_timesort on a directory: %s' % path)

    files = md['contents']
    fmt = '%a, %d %b %Y %H:%M:%S +0000'
    files = sorted(files, key=lambda x: time.strptime(x['modified'], fmt))
    files = files[::-1]  # newest first
    return files


def purge_old_files(prefix='/', keep=4):
    c = get_client()
    files = ls_timesort(prefix)

    for f in files[keep:]:
        print 'purging:', f['path']
        c.file_delete(f['path'])


def alias_newest_file(prefix, alias_name):
    c = get_client()
    files = ls_timesort(prefix)
    c.file_copy(files[0]['path'], alias_name)


def put(src, target):
    c = get_client()
    c.put_file(target, src, overwrite=True)
    if target[0] == '/':
        target = target[1:]
    if '/' in target:
        prefix = target.split('/')[0]
    else:
        prefix = '/'
    purge_old_files(prefix)


if __name__ == "__main__":
    from cStringIO import StringIO

    put(StringIO('1'), 'test/1.txt')
    put(StringIO('2'), 'test/2.txt')
    put(StringIO('3'), 'test/3.txt')
    put(StringIO('4'), 'test/4.txt')
    put(StringIO('4'), 'test/5.txt')

    put(StringIO('1'), 'test2/3.txt')
    put(StringIO('2'), 'test2/4.txt')
    put(StringIO('3'), 'test2/5.txt')
    put(StringIO('4'), 'test2/6.txt')
    put(StringIO('4'), 'test2/7.txt')
