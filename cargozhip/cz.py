#!/usr/bin/env python3
import os, re
from wcmatch import glob as wcg
from cargozhip.log import deb, inf, Indent, WHITEBOLD, RED, LIGHT_BLUE, GREEN, RESET


default_config = 'cargozhip.json'
depth = 0


class Filters:
    def __init__(self):
        self.include_files = []
        self.include_files_dest = []
        self.include_dirs = []
        self.exclude_files = []
        self.exclude_dirs = []

class ScanResult:
    def __init__(self):
        self.nof_files = 0
        self.file_list = {}

    def add(self, key, filename):
        if key:
            key = key[1:]
        if not self.file_list.get(key):
            self.file_list[key] = []
        self.file_list[key].append(filename)
        self.nof_files += 1

    def sort(self):
        for key in self.file_list.keys():
            self.file_list[key] = sorted(self.file_list[key])

    def as_file_list(self):
        result = []
        for key, file_list in self.file_list.items():
            for filename in file_list:
                if key:
                    fn = os.path.join(key, os.path.basename(filename))
                    result.append(fn)
                else:
                    result.append(filename)
        return result

    def as_source_and_dest(self):
        result = []
        for file_list in self.file_list.values():
            for filename in file_list:
                result.append(filename)
        return zip(result, self.as_file_list())

    def target_file_exist(self, target):
        target = os.path.normpath(target)
        for src, dest in self.as_source_and_dest():
            if target == dest:
                return True
        return False


def get_sections(configuration):
    """
    Return all sections as a list regardless of how they might be inherited or not.
    """
    sections = list(configuration.keys())
    try:
        # the config entry is actually the configuration setup used by cargozhip so get rid of that.
        sections.remove('config')
    except:
        pass
    return sections


def parse_section(config, section, filters=None):
    """
    Load the specified section and recursively load upstream sections if found listed in 'inherit'.
    """
    global depth
    if filters is None:
        filters = Filters()
        depth = 0

    # try to catch circular recursions before Python does.
    depth += 1
    if depth > 10:
        raise Exception("Too many recursions")

    try:
        _section = config[section]
    except KeyError:
        raise Exception(f'Section "{section}" not found')

    keys = _section.keys()

    for key in keys:
        if key == 'inherit':
            # try to keep the chronology and process inherits after this filters loop
            continue
        try:
            filterentry = _section[key]

            if key.startswith('include_files'):
                dest = None

                for entry in filterentry:
                    if entry.startswith("@"):
                        dest = entry
                        continue
                    filters.include_files.append(entry)
                    filters.include_files_dest.append(dest)
            elif key.startswith('include_dirs'):
                filters.include_dirs += filterentry
            elif key.startswith('exclude_files'):
                filters.exclude_files += filterentry
            elif key.startswith('exclude_dirs'):
                filters.exclude_dirs += filterentry
        except IndexError:
            pass

    try:
        inherit_list = _section['inherit']
        for inherit_section in inherit_list:
            deb(f'adding inherited "{inherit_section}"')
            parse_section(config, inherit_section, filters)
    except KeyError:
        pass
    depth -= 1
    return filters


files_processed = 0
dirs_processed = 0


def file_scan(directory):
    global files_processed, dirs_processed
    for root, dirs, files in os.walk(directory):
        root = os.path.relpath(root, directory)
        if root == '.':
            root = ''
        deb(f'{WHITEBOLD}scan: cwd:"{root}" dirs:"{dirs}" files:"{files}"{RESET}')

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
                deb(f'exclude file "{name}" {GREEN}match{RESET} with regex "{exclude_file}"')
                return True
        elif wcg.globmatch(name, exclude_file, flags=wcg.GLOBSTAR):
            deb(f'exclude file "{name}"" {GREEN}match{RESET} with "{exclude_file}"')
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
            directory = os.path.dirname(name)
            if exclude_dir[0] == '!':
                if re.search(exclude_dir[1:], directory):
                    deb(f'exclude dir  "{name}" {GREEN}match{RESET} with regex "{exclude_dir}"')
                    return True
            elif wcg.globmatch(directory, exclude_dir, flags=wcg.GLOBSTAR):
                deb(f'exclude dir  "{name}" {GREEN}match{RESET} with "{exclude_dir}"')
                return True
            else:
                deb(f'exclude dir  "{name}" unmatched with "{exclude_dir}"')
    return False


def include_file_hit(name, include_files, include_files_dest):
    for include_file, include_file_dest in zip(include_files, include_files_dest):
        if include_file[0] == '!':
            if re.search(include_file[1:], name):
                deb(f'include file "{name}" {GREEN}match{RESET} with regex "{include_file}"')
                return include_file_dest
        elif wcg.globmatch(name, include_file, flags=wcg.GLOBSTAR):
            deb(f'include file "{name}" {GREEN}match{RESET} with "{include_file}"')
            return include_file_dest
        else:
            deb(f'include file "{name}" unmatched with "{include_file}"')
    return False


def include_dir_hit(name, include_dirs):
    for include_dir in include_dirs:
        if include_dir[0] == '!':
            if re.search(include_dir[1:], name):
                deb(f'include dir  "{name}" {GREEN}match{RESET} with regex "{include_dir}"')
                return True
        elif wcg.globmatch(name, include_dir, flags=wcg.GLOBSTAR):
            deb(f'include dir  "{name}" {GREEN}match{RESET} with "{include_dir}"')
            return True
        else:
            deb(f'include dir  "{name}" unmatched with "{include_dir}"')
    return False


def find_files(root_path, filters):
    """
    The include_... and exclude_... functions above and this function were made before starting
    using the wcmatch library. It should be possible to replace it all with wcmatch but that
    will be another day.
    :return: sorted list of files and symlinks found. Normally directories are ignored but as a
             special case also include directories that are in fact symlinks.
    """
    scan_result = ScanResult()

    for name, is_dir in file_scan(root_path):
        _ = Indent()
        fqn = os.path.join(root_path, name)
        symlink = os.path.islink(fqn)
        if not is_dir or symlink:
            deb(f'{LIGHT_BLUE}Checking "{name}"')
            _dir = os.path.dirname(name)
            inc_file_hit = include_file_hit(name, filters.include_files, filters.include_files_dest)

            if include_dir_hit(_dir, filters.include_dirs) or inc_file_hit is not False:
                if not exclude_dir_hit(_dir, filters.exclude_dirs) and not exclude_file_hit(name, filters.exclude_files):
                    deb(f'{RED}Adding file "{name}"')
                    scan_result.add(inc_file_hit, name)

        del _

    scan_result.sort()

    return scan_result
