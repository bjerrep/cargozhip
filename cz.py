#!/usr/bin/env python3
from log import deb, inf
import os, re
from wcmatch import glob as wcg


default_config = 'cargozhip.json'
RED = '\033[1;31m'
LIGHT_BLUE = '\033[1;34m'
depth = 0


def parse_section(config, section, include_files=None, include_dirs=None, exclude_files=None, exclude_dirs=None):
    """
    Load the specified section and recursively load upstream sections if found listed in 'inherit'.
    """
    global depth
    if include_files is None and include_dirs is None and exclude_files is None and exclude_dirs is None:
        include_files = []
        include_dirs = []
        exclude_files = []
        exclude_dirs = []
        depth = 0

    # try to catch circular recursions before Python does.
    depth += 1
    if depth > 10:
        raise Exception("Too many recursions")

    try:
        _section = config[section]
    except KeyError:
        raise Exception(f'Section "{section}" not found')

    try:
        include_files += _section['include_files']
    except:
        pass
    try:
        include_dirs += _section['include_dirs']
    except:
        pass
    try:
        exclude_files += _section['exclude_files']
    except:
        pass
    try:
        exclude_dirs += _section['exclude_dirs']
    except:
        pass

    try:
        inherit_list = _section['inherit']
        for inherit in inherit_list:
            deb(f'adding inherited "{inherit}"')
            parse_section(config, inherit, include_files, include_dirs, exclude_files, exclude_dirs)
    except KeyError:
        pass
    depth -= 1
    return include_files, include_dirs, exclude_files, exclude_dirs


files_processed = 0
dirs_processed = 0


def file_scan(directory):
    global files_processed, dirs_processed
    for root, dirs, files in os.walk(directory):
        root = os.path.relpath(root, directory)
        if root == '.':
            root = ''
        deb(f'scan: cwd:"{root}" dirs:"{dirs}" files:"{files}"')

        dirs_processed += len(dirs)
        for _dir in dirs:
            yield os.path.join(root, _dir), True

        files_processed += len(files)
        for filename in files:
            fqn = os.path.join(root, filename)
            ffqn = os.path.join(directory, fqn)
            if os.path.exists(ffqn):
                yield fqn, False
            else:
                inf(f'ignoring "{fqn}" (broken symlink?)')
                continue


def get_processed():
    return files_processed, dirs_processed


def exclude_file_hit(name, exclude_files):
    for exclude_file in exclude_files:
        if exclude_file[0] == '!':
            if re.search(exclude_file[1:], name):
                deb(f'exclude file "{name}" match with regex "{exclude_file}"')
                return True
        elif wcg.globmatch(name, exclude_file, flags=wcg.GLOBSTAR):
            deb(f'exclude file "{name}"" match with "{exclude_file}"')
            return True
        else:
            deb(f'exclude file "{name}" unmatched with "{exclude_file}"')
    return False


def exclude_dir_hit(name, exclude_dirs):
    for exclude_dir in exclude_dirs:
        if exclude_dir[0] == '!':
            if re.search(exclude_dir[1:], name):
                deb(f'exclude dir  "{name}" match with regex "{exclude_dir}"')
                return True
        elif wcg.globmatch(name, exclude_dir, flags=wcg.GLOBSTAR):
            deb(f'exclude dir  "{name}" match with "{exclude_dir}"')
            return True
        else:
            dir = os.path.dirname(name)
            if exclude_dir[0] == '!':
                if re.search(exclude_dir[1:], dir):
                    deb(f'exclude dir  "{name}" match with regex "{exclude_dir}"')
                    return True
            elif wcg.globmatch(dir, exclude_dir, flags=wcg.GLOBSTAR):
                deb(f'exclude dir  "{name}" match with "{exclude_dir}"')
                return True
            else:
                deb(f'exclude dir  "{name}" unmatched with "{exclude_dir}"')
    return False


def include_file_hit(name, include_files):
    for include_file in include_files:
        if include_file[0] == '!':
            if re.search(include_file[1:], name):
                deb(f'include file "{name}" match with regex "{include_file}"')
                return True
        elif wcg.globmatch(name, include_file, flags=wcg.GLOBSTAR):
            deb(f'include file "{name}" match with "{include_file}"')
            return True
        else:
            deb(f'include file "{name}" unmatched with "{include_file}"')
    return False


def include_dir_hit(name, include_dirs):
    for include_dir in include_dirs:
        if include_dir[0] == '!':
            if re.search(include_dir[1:], name):
                deb(f'include dir  "{name}" match with regex "{include_dir}"')
                return True
        elif wcg.globmatch(name, include_dir, flags=wcg.GLOBSTAR):
            deb(f'include dir  "{name}" match with "{include_dir}"')
            return True
        else:
            deb(f'include dir  "{name}" unmatched with "{include_dir}"')
    return False


def find_files(root_path, include_files, include_dirs, exclude_files, exclude_dirs):
    """
    The include_... and exclude_... functions above and this function were made before starting
    using the wcmatch library. It should be possible to replace it all with wcmatch but that
    will be another day.
    :return: sorted list of files found
    """
    file_list = set()

    for name, is_dir in file_scan(root_path):
        if not is_dir:
            deb(f'{LIGHT_BLUE}Checking "{name}"')
            _dir = os.path.dirname(name)
            if include_dir_hit(_dir, include_dirs) or include_file_hit(name, include_files):
                if not exclude_dir_hit(_dir, exclude_dirs) and not exclude_file_hit(name, exclude_files):
                    deb(f'{RED}Adding file "{name}"')
                    file_list.add(name)

    return sorted(file_list)
