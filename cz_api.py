import os, json, time, zipfile, tarfile, logging, pathlib
from log import inf, logger as log
import cz


def load_config(config_name):
    """
    Load the configuration file and return it as a native dict
    """
    inf(f'Loading configuration file {config_name}')
    with open(config_name) as f:
        return json.loads(f.read())


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
    archive_path = os.path.dirname(archive)

    if not os.path.exists(archive_path):
        inf(f'Constructing the path {archive_path}')
        pathlib.Path(archive_path).mkdir(parents=True)

    inf(f'Compressing {len(file_list)} files to {archive}')
    now = time.time()

    zip_compression = compress_method in (zipfile.ZIP_LZMA, zipfile.ZIP_BZIP2, zipfile.ZIP_DEFLATED)

    if zip_compression:
        with zipfile.ZipFile(archive, 'w', compress_method) as _zipfile:
            for _file in file_list:
                _zipfile.write(os.path.join(root, _file))
    else:
        with tarfile.open(archive, compress_method) as _tarfile:
            for _file in file_list:
                _tarfile.add(os.path.join(root, _file))

    return time.time() - now


def compress(root, config_or_file, section, archive, dry_run=False):
    """
    The all in one cargozhip operation.
    Scans for files according to a configuration file or dictionary and then writes the archive.

    'config_or_file' can be either a filename to a json configuration file or it can be a
    dictionary with the configuration directly.
    """

    inf(f'Packaging project "{root}" section "{section}"')

    try:
        config = load_config(config_or_file)
    except:
        config = config_or_file

    settings_config = config['config']

    if not archive:
        archive = os.path.join(os.getcwd(), root)

    compression = settings_config['compression']
    if compression == 'lzma':
        compress_method = zipfile.ZIP_LZMA
        archive = archive + '.lzma'
    elif compression == 'bz2':
        compress_method = zipfile.ZIP_BZIP2
        archive = archive + '.bz2'
    elif compression == 'zip':
        compress_method = zipfile.ZIP_DEFLATED
        archive = archive + '.zip'
    elif compression == 'tar.gz':
        compress_method = 'w:gz'
        archive = archive + '.tar.gz'
    elif compression == 'tar.bz2':
        compress_method = 'w:bz2'
        archive = archive + '.tar.bz2'
    elif compression == 'tar.xz':
        compress_method = 'w:xz'
        archive = archive + '.tar.xz'
    else:
        raise Exception(f'Don\'t understand the compression {compression} ?')

    inf(f'Destination archive: {archive}')

    file_list = scan(root, config, section)

    if not file_list:
        raise Exception('Found no files ?')

    if dry_run:
        inf('Dry run, not writing archive')
    else:
        elapsed = write_archive(root, file_list, archive, compress_method)

        inf(f'Generated archive {archive} '
            f'in {elapsed:0.3f} secs ({os.path.getsize(archive)} bytes)')
