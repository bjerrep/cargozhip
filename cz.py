#!/usr/bin/env python3
import os, fnmatch, re

GREY = '\033[0;37m'
RESET = '\033[0m'
WHITE = '\033[1;37m'


def ver(message):
    # print(f'{WHITE}{message}{RESET}')
    pass


def deb(message):
    # print(f'{GREY}{message}{RESET}')
    pass


def inf(message):
    print(message)


def err(message):
    print(message)


default_config = 'cargozhip.json'


def recursive_find_files(package_config, section, include_files=None, include_dirs=None, exclude_files=None, exclude_dirs=None):
    if not include_files and not include_dirs and not exclude_files and not exclude_dirs:
        include_files = []
        include_dirs = []
        exclude_files = []
        exclude_dirs = []

    _section = package_config[section]
    try:
        include_files += _section["include_files"]
    except:
        pass
    try:
        include_dirs += _section["include_dirs"]
    except:
        pass
    try:
        exclude_files += _section["exclude_files"]
    except:
        pass
    try:
        exclude_dirs += _section["exclude_dirs"]
    except:
        pass

    try:
        for include in _section["inherit"]:
            recursive_find_files(package_config, include, include_files, include_dirs, exclude_files, exclude_dirs)
    except:
        pass
    return include_files, include_dirs, exclude_files, exclude_dirs


files_processed = 0
dirs_processed = 0


def find_files(directory):
    global files_processed, dirs_processed
    for root, dirs, files in os.walk(directory):
        root = os.path.relpath(root, directory)
        if root == '.':
            root = ''
        deb(f'find_files: "{root}" "{dirs}" "{files}"')

        dirs_processed += len(dirs)
        for _dir in dirs:
            yield os.path.join(root, _dir), True

        files_processed += len(files)
        for filename in files:
            fqn = os.path.join(root, filename)
            yield fqn, False


def get_processed():
    return files_processed, dirs_processed


def exclude_file_hit(name, exclude_files):
    for exclude_file in exclude_files:
        if exclude_file[0] == '!':
            if re.search(name, exclude_file[1:]):
                ver(f'exclude file {name} match with regex {exclude_file}')
                return True
        elif fnmatch.fnmatch(name, exclude_file):
            ver(f'exclude file {name} match with {exclude_file}')
            return True
        else:
            ver(f'exclude file {name} unmatched with {exclude_file}')
    return False


def exclude_dir_hit(name, exclude_dirs):
    for exclude_dir in exclude_dirs:
        for path_component in name.split('/'):
            if exclude_dir[0] == '!':
                if re.search(path_component, exclude_dir[1:]):
                    ver(f'exclude dir {name} match with regex {exclude_dir}')
                    return True
            elif fnmatch.fnmatch(path_component, exclude_dir):
                ver(f'exclude dir {name} match with {exclude_dir}')
                return True
            else:
                ver(f'exclude dir {name} unmatched with {exclude_dir}')
    return False


def find_files_and_dirs(rootpath, include_files, include_dirs, exclude_files, exclude_dirs):
    file_list = set()
    dir_list = set()

    for name, is_dir in find_files(rootpath):
        if is_dir:
            if not exclude_dir_hit(name, exclude_dirs):
                for pattern in include_dirs:
                    for element in name.split('/'):
                        if pattern[0] == '!':
                            if re.search(pattern[1:], element):
                                dir_list.add(element)
                        else:
                            if fnmatch.fnmatch(name, pattern):
                                dir_list.add(element)
        else:
            if not exclude_file_hit(name, exclude_files) and not exclude_dir_hit(name, exclude_dirs):
                for pattern in include_files:
                    if pattern[0] == '!':
                        if re.search(pattern[1:], name):
                            file_list.add(name)
                    else:
                        if fnmatch.fnmatch(name, pattern):
                            file_list.add(name)

    return file_list, dir_list
