#!/usr/bin/env python

import os
import re
import stat


class Path(object):
    mapping = {}

    # this is what i used on my mac
    blocked_full_paths = {
        r'/Volumes',  # recurses
        r'/dev',  # full of not files
        r'/var',  # in /private
        r'/tmp',  # in /private
        r'/Users/[^/]*/Library/Containers/.*',  # links to home dir mess up
    }

    def __init__(self, path):
        path = os.path.abspath(os.path.expanduser(path))

        cached = self.get_path(path, False)
        if cached:
            self = cached
        else:
            self.path = path
            self.add_path(self)

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return '<Path "{}">'.format(self.path)

    @property
    def parent_path(self):
        if not hasattr(self, '_parent_path'):
            self._parent_path = os.path.split(self.path)[0]
            if self._parent_path == '':
                self._parent_path = '/'
        return self._parent_path

    @property
    def parent(self):
        if not hasattr(self, '_parent'):
            self._parent = self.get_path(self.parent_path)
        return self._parent

    def delete(self):
        print os.remove(self.path)
        self._delete(self.path)

    @classmethod
    def _delete(cls, path):
        del cls.mapping[path]

    @property
    def children(self):
        if not hasattr(self, '_children'):
            self._children = []
            if self.is_dir:
                for path, file_names, dir_names in os.walk(self.path):
                    for file_name in file_names:
                        full_path = os.path.join(self.path, file_name)
                        if any(re.match(pattern, full_path) for pattern in self.blocked_full_paths):
                            print 'skipping', full_path
                            continue
                        self._children.append(Path(full_path))
                    for dir_name in dir_names:
                        full_path = os.path.join(self.path, dir_name)
                        if any(re.match(pattern, full_path) for pattern in self.blocked_full_paths):
                            print 'skipping', full_path
                            continue
                        self._children.append(Path(full_path))
                    break
        return self._children

    @property
    def stats(self):
        if not hasattr(self, '_stats'):
            try:
                self._stats = os.stat(self.path)
            except OSError:
                self._stats = None
        return self._stats

    @property
    def list(self):
        for child in sorted(self.children, key=lambda x: x.size):
            print child.listing
        print
        print self.listing

    @property
    def size(self):
        if not hasattr(self, '_size'):
            if self.is_dir:
                self._size = sum(child.size for child in self.children)
            else:
                if self.stats:
                    self._size = self.stats.st_size
                else:
                    self._size = 0
        return self._size

    @property
    def human_size(self):
        return self.human(self.size)

    @property
    def listing(self):
        return '{:<64}{:>10}'.format(self.path, self.human_size)

    @property
    def is_dir(self):
        try:
            return stat.S_ISDIR(self.stats.st_mode)
        except AttributeError:
            return False

    @classmethod
    def add_path(cls, path):
        if os.path.exists(path.path):
            cls.mapping[path.path] = path

    @classmethod
    def get_path(cls, path, create=True):
        if path == '':
            return cls.mapping['/']
        if create:
            return cls.mapping.get(path, Path(path))
        return cls.mapping.get(path, None)

    @staticmethod
    def human(size):
        names = [' B', 'kB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB']

        output = None
        name = None

        if size == 0:
            return '0  B'

        for i, n in zip(range(len(names)), names)[::-1]:
            v = size / 1024 ** i
            if v and not output:
                name = n
                size -= v * 1024 ** i
                output = v
            elif output:
                output += v / 1000.
                break
        return '{} {}'.format(output, name)

