import os, json, time, glob, zipfile, tarfile
from cz import *


def compress(root, config, section, archive):
    """
    :param root: the root dir to compress. Will not be included in archive.
    :param config: the configuration json file. Will default be root/'default_config'
    :param section: the section to start from in config file
    :param archive: the name (and optionally path) of the archive. Will default be
                    named after the root dir
    :return: (bool, message). True for success, False on failure.
    """

    # step 1/5, process arguments
    if not os.path.exists(root):
        return False, f'Root folder {root} not found, "{os.path.join(os.getcwd(), root)}"'
    if root == '.':
        directory_name = os.path.basename(os.getcwd())
    else:
        directory_name = os.path.basename(os.path.normpath(root))

    inf(f'Packaging project {root}')

    if not config:
        config = os.path.join(root, default_config)
    with open(config) as f:
        packaging_config = json.loads(f.read())
    config = packaging_config['config']

    if not archive:
        archive = os.path.join(os.getcwd(), directory_name)
    else:
        archive = archive

    zipfile_compression = None
    tarfile_compression = None

    try:
        if config['compression'] == 'lzma':
            zipfile_compression = zipfile.ZIP_LZMA
            archive = archive + '.lzma'
        elif config['compression'] == 'bz2':
            zipfile_compression = zipfile.ZIP_BZIP2
            archive = archive + '.bz2'
        elif config['compression'] == 'zip':
            zipfile_compression = zipfile.ZIP_DEFLATED
            archive = archive + '.zip'
        elif config['compression'] == 'tar.gz':
            tarfile_compression = 'w:gz'
            archive = archive + '.tar.gz'
        elif config['compression'] == 'tar.bz2':
            tarfile_compression = 'w:bz2'
            archive = archive + '.tar.bz2'
        else:
            return False, f'Dont understand the compression {config["compression"]} ?'
    except:
        inf('Defaulting to zip compression')
        zipfile_compression = zipfile.ZIP_DEFLATED
        archive = archive + '.zip'

    inf(f'Destination archive: {archive}')

    # step 2/5, parse the package configuration to figure out what gets to be included or excluded

    include_files, include_dirs, exclude_files, exclude_dirs = recursive_find_files(packaging_config, section)

    inf(f'Parsing package list for section "{section}"')
    inf(f'  Include files: {include_files}')
    inf(f'  Exclude files: {exclude_files}')
    inf(f'  Include dirs: {include_dirs}')
    inf(f'  Exclude dirs: {exclude_dirs}')

    # step 3/5, scan the project aka root

    inf('Scanning ...')
    now = time.time()
    file_list, dir_list = find_files_and_dirs(root, include_files, include_dirs, exclude_files, exclude_dirs)

    inf(f'Matched {len(file_list)} files')
    for fqn in sorted(file_list):
        print(f'  {fqn}')
    inf(f'Matched {len(dir_list)} directories')
    for _dir in sorted(dir_list):
        print(f'  {_dir}')

    nof_files_processed, nof_dirs_processed = get_processed()

    inf(f'Scanned {nof_files_processed} files and {nof_dirs_processed} directories in {time.time()-now:0.3f} secs')

    # step 4/5, compress the file and dir lists. This is insanely slow

    inf(f'Compressing {len(file_list)} files and {len(dir_list)} directories ...')
    now = time.time()
    os.chdir(root)

    if zipfile_compression:
        with zipfile.ZipFile(archive, 'w', zipfile_compression) as _zipfile:
            for _file in file_list:
                _zipfile.write(_file)
            for _dir in dir_list:
                files = glob.glob(_dir + '/**', recursive=True)
                for _file in files:
                    _zipfile.write(_file)
    elif tarfile_compression:
        with tarfile.open(archive, tarfile_compression) as _tarfile:
            for _file in file_list:
                _tarfile.add(_file)
            for _dir in dir_list:
                _tarfile.add(_dir)
    else:
        return False, 'internal error, bailing out'

    # step 5/5, we are done

    return True, f'Generated archive {os.path.basename(archive)} in {time.time()-now:0.3f} secs ({os.path.getsize(archive)} bytes)'