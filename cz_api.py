import os, json, time, zipfile, tarfile, logging, pathlib, shutil
from log import inf, war, err, cri, logger as log
import cz


def load_config(config_name):
    """
    Load the configuration file and return it as a native dict
    """
    try:
        with open(config_name) as f:
            return json.loads(f.read())
    except Exception as e:
        cri(f'{str(e)}')


def minimal_config():
    config = {
        'config':
            {'compression': 'lzma'},
        'default':
            {'include_files': ['**']}
    }
    return config


def scan(root, config, section):
    """
    Load the section from the configuration and return the file list matching files and
    directories to include and exclude.
    """
    include_files, include_dirs, exclude_files, exclude_dirs = cz.parse_section(config, section)

    inf(f'Parsing package list for section "{section}"')
    inf(f'  Include files: {include_files}')
    inf(f'  Exclude files: {exclude_files}')
    inf(f'  Include dirs: {include_dirs}')
    inf(f'  Exclude dirs: {exclude_dirs}')

    inf('Scanning ...')
    now = time.time()
    file_list = cz.find_files(root, include_files, include_dirs, exclude_files, exclude_dirs)

    inf(f'Matched {len(file_list)} files')
    if log.level == logging.INFO:
        max_debug_lines = 20
        for fqn in sorted(file_list):
            if max_debug_lines:
                inf(f'  {fqn}')
                max_debug_lines -= 1
                if not max_debug_lines:
                    inf(' -- not listing additional files --')
    elif log.level == logging.DEBUG:
        for fqn in sorted(file_list):
            inf(f'  {fqn}')

    nof_files_processed, nof_dirs_processed = cz.get_processed()

    inf(f'Scanned {nof_files_processed} files and {nof_dirs_processed} '
        f'directories in {time.time()-now:0.3f} secs')

    return file_list


def write_archive(root, file_list, archive, compress_method):
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

    inf(f'Compressing {len(file_list)} files to {archive}')
    now = time.time()

    zip_compression = compress_method in (zipfile.ZIP_LZMA, zipfile.ZIP_BZIP2, zipfile.ZIP_DEFLATED)

    pwd = os.getcwd()
    os.chdir(root)

    if zip_compression:
        with zipfile.ZipFile(rel_archive, 'w', compress_method) as _zipfile:
            for _file in file_list:
                if os.path.islink(_file):
                    # First go at supporting symlinks
                    zipInfo = zipfile.ZipInfo(_file)
                    zipInfo.create_system = 3  # unix
                    mode = os.lstat(_file).st_mode
                    zipInfo.external_attr |= mode << 16

                    link = os.readlink(_file)
                    if os.path.isabs(link):
                        if not link.startswith(root):
                            war(f'symlink {_file} -> {link} has reference outside root, ignored')
                            continue

                    _zipfile.writestr(zipInfo, link)
                else:
                    _zipfile.write(_file)
    else:
        with tarfile.open(rel_archive, compress_method) as _tarfile:
            for _file in file_list:
                _tarfile.add(_file)

    os.chdir(pwd)

    return time.time() - now


def compress(root, config_or_file, section, archive, dry_run=False, compression=None):
    """
    The all in one cargozhip operation.
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

    file_list = scan(root, config, section)

    if not file_list:
        raise Exception('Found no files ?')

    if archive in file_list:
        raise Exception(f'Can\'t append archive {archive} to itself (fix the rules or delete the archive first)')

    if dry_run:
        inf('Dry run, not writing archive')
    else:
        elapsed = write_archive(root, file_list, archive, compress_method)

        inf(f'Generated archive {archive} '
            f'in {elapsed:0.3f} secs ({os.path.getsize(archive)} bytes)')


def decompress(archive, destpath):
    """
    Not really part of the core business, but its an odd thing to miss support
    for unpacking an archive right after having packed one.
    """
    extension = os.path.splitext(archive)[1]
    if extension in ('.lzma', '.bz2', '.zip'):
        with zipfile.ZipFile(archive, 'r') as _zipfile:
            _zipfile.extractall(destpath)

            # zipfile as of current doesn't support symlinks so manually rewrite those
            for element in _zipfile.namelist():
                zipinfo = _zipfile.getinfo(element)
                if zipinfo.external_attr & 0x20000000:
                    symlink = os.path.join(destpath, element)
                    with open(symlink) as f:
                        symlink_dest = f.read()
                    try:
                        os.remove(symlink)
                    except:
                        os.rmdir(symlink)
                    os.symlink(symlink_dest, symlink)

    elif extension in ('.tar.gz', '.tar.bz2', '.xz'):
        with tarfile.ZipFile(archive, 'r') as _tarfile:
            _tarfile.extractall(destpath)
    else:
        raise Exception(f'Don\'t understand the compression {extension} ?')


def copy(root, config_or_file, section, dest_root):
    """
    Also not part of the core business, but support a copy operation using
    a cargozhip configuration file (or a configuration dictionary).
    The result hopefully matches the result of a compress() followed by a decompress().
    """

    if isinstance(config_or_file, str):
        config = load_config(config_or_file)
        inf(f'Loading configuration file "{config_or_file}" section "{section}"')
    else:
        config = config_or_file

    file_list = scan(root, config, section)

    symlinks = []

    for _file in file_list:
        src_file = os.path.join(root, _file)
        dst_file = os.path.join(dest_root, _file)

        if not os.path.islink(src_file):
            try:
                shutil.copy(src_file, dst_file)
            except FileNotFoundError:
                dst_file_path = os.path.dirname(dst_file)
                inf(f'Constructing destination path {dst_file_path}')
                pathlib.Path(dst_file_path).mkdir(parents=True, exist_ok=True)
                shutil.copy(src_file, dst_file)
        else:
            # if it is a symlink (to a file or directory) then just save the link for
            # now in case the destination does not yet exist.
            abs_src_file = os.path.abspath(src_file)
            abs_link_target = os.path.realpath(src_file)
            link = os.path.relpath(abs_link_target, abs_src_file)[3:]
            is_dir = not os.path.isfile(src_file)
            symlinks.append((link, dst_file, is_dir))

    # all files and directories in scope are now made, then make the symlinks
    for link, dst, is_dir in symlinks:
        try:
            os.symlink(src=link, dst=dst, target_is_directory=is_dir)
        except:
            err(f'failed making symlink {link} to {dst}')
