import os, json, time, zipfile, tarfile, logging, pathlib, shutil, warnings
from .log import inf, war, err, deb, logger as log
from . import cz

# force file collisions in zipfile to be fatal rather than a "UserWarning" log message
warnings.filterwarnings("error")


def load_config(config_name):
    """
    Load the configuration file and return it as a native dict
    """
    try:
        with open(config_name) as f:
            return json.loads(f.read())
    except FileNotFoundError as e:
        raise Exception(f'{str(e)}') from e


def get_config_sections(config_name):
    config = load_config(config_name)
    cz.get_sections(config)


def minimal_config():
    config = {
        'config':
            {'compression': 'zip'},
        'everything':
            {'include_files': ['**']}
    }
    return config


def scan(root, config, section):
    """
    Load the section from the configuration and return the file list matching files and
    directories to include and exclude.
    """
    filters = cz.parse_section(config, section)

    inf(f'Parsing package list for section "{section}"')
    inf(f'  Include files dest: {filters.include_files}')
    inf(f'  Exclude files: {filters.exclude_files}')
    inf(f'  Include dirs: {filters.include_dirs}')
    inf(f'  Exclude dirs: {filters.exclude_dirs}')

    inf('Scanning ...')
    now = time.time()
    scan_result = cz.find_files(root, filters)

    inf(f'Matched {scan_result.nof_files} files')

    if log.level <= logging.INFO:
        max_info_lines = 20
        for src, dest in scan_result.as_source_and_dest():
            if src != dest:
                inf(f'  {src} -as- {dest}')
            else:
                inf(f'  {src}')
            if log.level == logging.INFO:
                max_info_lines -= 1
                if not max_info_lines:
                    inf(' -- not listing additional files --')
                    break

    nof_files_processed, nof_dirs_processed = cz.get_processed()

    inf(f'Scanned {nof_files_processed} files and {nof_dirs_processed} '
        f'directories in {time.time() - now:0.3f} secs')

    return scan_result


def write_archive(root, scan_result, archive, compress_method):
    """
    Compress the file list. This is insanely slow, all files are added individually.
    """
    # Since the zip thing is done when located in the source root then figure out the
    # relative path 'rel_archive' to where the archive should be written accordingly.
    abs_root = os.path.abspath(root)
    abs_archive = os.path.abspath(archive)
    rel_archive = os.path.relpath(abs_archive, abs_root)

    archive_path = os.path.dirname(archive)

    if archive_path and not os.path.exists(archive_path):
        inf(f'Constructing the path {archive_path}')
        pathlib.Path(archive_path).mkdir(parents=True)

    inf(f'Compressing {scan_result.nof_files} files to {archive}')
    now = time.time()

    zip_compression = compress_method in (zipfile.ZIP_LZMA, zipfile.ZIP_BZIP2, zipfile.ZIP_DEFLATED)

    pwd = os.getcwd()
    os.chdir(root)

    if zip_compression:
        with zipfile.ZipFile(rel_archive, 'w', compress_method) as _zipfile:
            for _file, _dest in scan_result.as_source_and_dest():
                if os.path.islink(_file):
                    # First go at supporting symlinks
                    zip_info = zipfile.ZipInfo(_dest)
                    zip_info.create_system = 3  # unix
                    mode = os.lstat(_file).st_mode
                    zip_info.external_attr |= mode << 16

                    link = os.readlink(_file)

                    deb(f'archive symlink "{_file}" pointing to "{link}" as "{_dest}" ')

                    if link != '.':
                        # For symlinks pointing out of the current directory check that the destination is present.
                        # The occasional incorrect assumption is that the destination is always present for same directory symlinks.
                        if not scan_result.target_file_exist(_dest):
                            war(f'skipping symlink {_file} since {_dest} is not included')
                            continue
                    if os.path.isabs(link):
                        if not link.startswith(root):
                            war(f'symlink {_file} -> {link} has reference outside root, ignored')
                            continue
                    try:
                        _zipfile.writestr(zip_info, link)
                    except UserWarning:
                        raise Exception(f'Name collision in zip archive when writing symlink {_file} as {_dest}')
                else:
                    try:
                        _zipfile.write(_file, arcname=_dest)
                    except UserWarning:
                        raise Exception(f'Name collision in zip archive when writing file {_file} as {_dest}')
    else:
        with tarfile.open(rel_archive, compress_method) as _tarfile:
            for _file, _dest in scan_result.as_source_and_dest():
                _tarfile.add(_file, arcname=_dest)

    os.chdir(pwd)

    return time.time() - now


def compress(root, config_or_file, section, archive, dry_run=False, compression=None):
    """
    The all in one cargozhipsrc operation.
    Scans for files according to a configuration file or dictionary and then writes the archive.

    'config_or_file' can be either a filename to a json configuration file or it can be a
    dictionary with the configuration directly.
    """

    inf(f'Packaging root "{root}"')

    if isinstance(config_or_file, str):
        config = load_config(config_or_file)
        inf(f'Loading configuration file "{config_or_file}" section "{section}"')
    else:
        config = config_or_file

    settings_config = config['config']

    if not archive:
        archive = os.path.join(os.getcwd(), root)

    if compression:
        _compression = compression
    else:
        _compression = settings_config['compression']

    if _compression == 'lzma':
        compress_method = zipfile.ZIP_LZMA
        archive = archive + '.lzma'
    elif _compression == 'bz2':
        compress_method = zipfile.ZIP_BZIP2
        archive = archive + '.bz2'
    elif _compression == 'zip':
        compress_method = zipfile.ZIP_DEFLATED
        archive = archive + '.zip'
    elif _compression == 'tar.gz':
        compress_method = 'w:gz'
        archive = archive + '.tar.gz'
    elif _compression == 'tar.bz2':
        compress_method = 'w:bz2'
        archive = archive + '.tar.bz2'
    elif _compression == 'tar.xz':
        compress_method = 'w:xz'
        archive = archive + '.tar.xz'
    else:
        raise Exception(f'Don\'t understand the compression {compression} ?')

    inf(f'Destination archive: {archive}')

    scan_result = scan(root, config, section)

    if not scan_result.nof_files:
        raise Exception('Found no files ?')

    if archive in scan_result.all_destinations():
        raise Exception(f'Can\'t append archive {archive} to itself (fix the rules or delete the archive first)')

    if dry_run:
        inf('Dry run, not writing archive')
    else:
        elapsed = write_archive(root, scan_result, archive, compress_method)

        inf(f'Generated archive {archive} '
            f'in {elapsed:0.3f} secs ({os.path.getsize(archive)} bytes)')


def decompress(archive, destpath, force=False):
    """
    Not really part of the core business, but its an odd thing to miss support
    for unpacking an archive right after having packed one.
    """
    try:
        os.makedirs(destpath, exist_ok=force)
    except:
        err(f'destination {destpath} already exist ?')

    extension = os.path.splitext(archive)[1]

    if extension in ('.lzma', '.bz2', '.zip'):
        with zipfile.ZipFile(archive, mode='r') as _zipfile:
            for info in _zipfile.infolist():
                if force:
                    try:
                        os.remove(os.path.join(destpath, info.filename))
                    except:
                        pass
                is_symlink = bool(info.external_attr & 0x20000000)
                deb(f'decompressing {info.filename}  {"symlink" if is_symlink else ""}')
                _zipfile.extract(info.filename, path=destpath)

                if is_symlink:
                    symlink = os.path.join(destpath, info.filename)
                    with open(symlink) as f:
                        symlink_dest = f.read()
                        try:
                            os.remove(symlink)
                        except:
                            os.rmdir(symlink)
                        deb(f'symlink destination "{symlink_dest}"')
                        os.symlink(symlink_dest, symlink)

    elif extension in ('.tar.gz', '.tar.bz2', '.xz'):
        with tarfile.ZipFile(archive, 'r') as _tarfile:
            _tarfile.extractall(destpath)
    else:
        raise Exception(f'Cannot decompress from filename extension "{extension}" ?')


def copy(root, config_or_file, section, destination, require_empty_destination=True):
    """
    Also not part of the core business, but support a copy operation using a cargozhipsrc configuration
    file (or a configuration dictionary).
    This allows for a faster/different/otherwise better compression tool to be used rather than the
    native python compressors in case cargozhipsrc is still useful for just extracting files.
    The result hopefully matches the result of a compress() followed by a decompress().
    """
    if not destination:
        err('missing a destination')
    if not section:
        err('missing a section (from config file)')

    try:
        # require the destination to be empty or non-existent
        if require_empty_destination:
            if os.listdir(os.path.abspath(destination)):
                err(f'destination directory {destination} is not empty (see --force)')
    except FileNotFoundError:
        pass

    if isinstance(config_or_file, str):
        config = load_config(config_or_file)
        get_config_sections(config_or_file)
        inf(f'Loading configuration file "{config_or_file}" section "{section}"')
    else:
        config = config_or_file

    scan_result = scan(root, config, section)
    symlinked_paths = []

    for _source, _dest in scan_result.as_source_and_dest():
        src_file = os.path.join(root, _source)
        dst_file = os.path.join(destination, _dest)

        duplicate = False
        for sl_path in symlinked_paths:
            if dst_file == sl_path:
                duplicate = True
                break

        if duplicate:
            continue

        if not os.path.islink(src_file):
            try:
                shutil.copy(src_file, dst_file)
            except FileNotFoundError:
                dst_file_path = os.path.dirname(dst_file)
                inf(f'Constructing destination path {dst_file_path}')
                pathlib.Path(dst_file_path).mkdir(parents=True, exist_ok=True)
                shutil.copy(src_file, dst_file)
        else:
            abs_src_file = os.path.abspath(src_file)
            abs_link_target = os.path.realpath(src_file)
            link = os.path.relpath(abs_link_target, abs_src_file)[3:]
            is_dir = not os.path.isfile(src_file)

            try:
                os.symlink(src=link, dst=dst_file, target_is_directory=is_dir)
                symlinked_paths.append(dst_file)
            except FileExistsError:
                if require_empty_destination:
                    err(f'got FileExists error making symlink {link} to {dst_file}')
            except FileNotFoundError:
                try:
                    # and the destination path is still missing in case this was also a move
                    dst_path = os.path.dirname(dst_file)
                    pathlib.Path(dst_path).mkdir(parents=True, exist_ok=True)
                    os.symlink(src=link, dst=dst_file, target_is_directory=is_dir)
                    symlinked_paths.append(dst_file)
                except:
                    err(f'failed making symlink {link} to {dst_file} after making {dst_path}')
            except NotADirectoryError:
                err(f'failed making symlink {link} to {dst_file} (perhaps a name clash?)')
            except:
                err(f'failed making symlink {link} to {dst_file}')

    inf(f'copy complete to {destination}')
