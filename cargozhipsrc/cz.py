#!/usr/bin/env python3
import os, re
from wcmatch import glob as wcg
from .log import deb, inf, war, Indent, Unindent, WHITEBOLD, YELLOW, LIGHT_BLUE, GREEN, RESET

default_config = 'cargozhip.json'
depth = 0


class Filters:
    def __init__(self):
        self.include_files = []
        self.include_dirs = []
        self.exclude_files = []
        self.exclude_dirs = []


class ScanResult:
    def __init__(self):
        self.nof_files = 0
        self.pattern_length = 0
        self.file_list = {}

    def add(self, hit):
        key, filename, pattern_length = hit
        if not self.file_list.get(key):
            self.file_list[key] = []
        self.file_list[key].append(filename)
        self.nof_files += 1
        self.pattern_length = pattern_length

    def sort(self):
        for key in self.file_list.keys():
            self.file_list[key] = sorted(self.file_list[key])

    def all_destinations(self):
        result = []
        for key, file_list in self.file_list.items():
            for filename in file_list:
                if key:
                    if key.startswith('@@@'):
                        fn = os.path.join(key[3:], filename[self.pattern_length:])
                        result.append(fn)
                    elif key.startswith('@@'):
                        fn = os.path.join(key[2:], filename)
                        result.append(fn)
                    else:
                        fn = os.path.join(key[1:], os.path.basename(filename))
                        result.append(fn)
                else:
                    result.append(filename)
        return result

    def as_source_and_dest(self):
        sourcefiles = []
        for file_list in self.file_list.values():
            for filename in file_list:
                sourcefiles.append(filename)
        return zip(sourcefiles, self.all_destinations())

    def target_file_exist(self, target):
        target = os.path.normpath(target)
        for _src, dest in self.as_source_and_dest():
            if target == dest:
                return True
        return False


def get_sections(configuration):
    """
    Return all sections as a list regardless of how they might be inherited or not.
    """
    sections = list(configuration.keys())
    try:
        # the config entry is actually the configuration setup used by cargozhipsrc so get rid of that.
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
        for key in config.keys():
            if key != 'config':
                inf(f' found section "{key}"')
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
                    # detect a relocation destination ('@...', '@@...' or '@@@...')
                    if entry.startswith('@'):
                        dest = entry
                        continue

                    filters.include_files.append((dest, entry))

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
    for root, dirs, files in os.walk(directory, followlinks=True):
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
                war(f'ignoring "{fqn}" (broken symlink?)')
                continue


def get_processed():
    return files_processed, dirs_processed


def check_for_exclude_file(name, exclude_files):
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


def check_for_exclude_dir(name, exclude_dirs):
    for exclude_dir in exclude_dirs:
        if exclude_dir[0] == '!':
            if re.search(exclude_dir[1:], name):
                deb(f'exclude dir  "{name}" {GREEN}match{RESET} with regex "{exclude_dir}"')
                return True
        elif wcg.globmatch(name, exclude_dir, flags=wcg.GLOBSTAR):
            deb(f'exclude dir  "{name}" {GREEN}match{RESET} with "{exclude_dir}"')
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


def check_for_include_file(name, include_files):
    for dest, pattern in include_files:
        if pattern[0] == '!':
            if re.search(pattern[1:], name):
                deb(f'include file "{name}" {GREEN}match{RESET} with regex "{pattern}"')
                return (dest, name, 0)
        elif wcg.globmatch(name, pattern, flags=wcg.GLOBSTAR):
            deb(f'include file "{name}" {GREEN}match{RESET} with "{pattern}"')
            # for now support for @@@ operator works for .../** format only.
            pattern_length = len(os.path.commonprefix([name, pattern]))
            return (dest, name, pattern_length)
        else:
            deb(f'include file "{name}" unmatched with "{pattern}"')
    return False


def check_for_include_dir(directory, name, include_dirs):
    for include_dir in include_dirs:
        if include_dir[0] == '!':
            if re.search(include_dir[1:], directory):
                deb(f'include dir  "{name}" {GREEN}match{RESET} with regex "{include_dir}"')
                return (None, name, 0)
        elif wcg.globmatch(directory, include_dir, flags=wcg.GLOBSTAR):
            deb(f'include dir  "{name}" {GREEN}match{RESET} with "{include_dir}"')
            pattern_length = len(os.path.commonprefix([name, include_dir]))
            return (None, name, pattern_length)
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
        Indent()
        fqn = os.path.join(root_path, name)
        symlink = os.path.islink(fqn)

        # directories are not explicitly checked, only implicitly based on actual files found
        if not is_dir or symlink:
            deb(f'{LIGHT_BLUE}Checking "{name}"')

            Indent()
            hit = check_for_include_file(name, filters.include_files)
            _dir = os.path.dirname(name)

            if not hit:
                hit = check_for_include_dir(_dir, name, filters.include_dirs)

            if hit:
                if not check_for_exclude_dir(_dir, filters.exclude_dirs) and not check_for_exclude_file(name, filters.exclude_files):
                    deb(f'{YELLOW}Adding file "{name}"')
                    scan_result.add(hit)
            Unindent()
        Unindent()

    scan_result.sort()

    return scan_result
