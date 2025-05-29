import os
import sys
import argparse
import configparser
from datetime import datetime

from fnmatch import fnmatch
import hashlib
import zlib
def repo_path(repo, *path):
    return os.path.join(repo.gitdir, *path)
def repo_dir(repo, *path, mkdir=False):
    path = repo_path(repo, *path)

    if os.path.exists(path):
        if (os.path.isdir(path)):
            return path
        else:
            raise Exception(f"Not a directory {path}")

    if mkdir:
        os.makedirs(path)
        return path
    else:
        return None
def repo_file(repo, *path, mkdir=False):
    if repo_dir(repo, *path[:-1], mkdir=mkdir):
        return repo_path(repo, *path)