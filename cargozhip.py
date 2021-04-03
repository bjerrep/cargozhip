#!/usr/bin/env python3
import os, time, argparse, json, glob, zipfile
from cz import *

folderfrag_manifest = 'cargozhip.json'


parser = argparse.ArgumentParser('cargozhip', description='''
    The slow, configurable and buggy as a complex number asset compressor.
    ''')
parser.add_argument('--root', default='.',
                    help='the root folder to work in, default current directory.')
parser.add_argument('--section', required=True,
                    help='the package configuration section to use')
parser.add_argument('--config',
                    help=f'the package configuration to load. Default "root"/{folderfrag_manifest}')
parser.add_argument('--archive',
                    help='archive name without extension. Default the project root directory name')

args = parser.parse_args()

# step 1/5, process commandline arguments

root = args.root
if not os.path.exists(root):
    fat(f'Root folder {root} not found, "{os.path.join(os.getcwd(), root)}"')
if not os.path.exists(os.path.join(root, folderfrag_manifest)):
    fat(f'Root folder {root} does not contain a {folderfrag_manifest} file (see --root)')
if args.root == '.':
    directory_name = os.path.basename(os.getcwd())
else:
    directory_name = os.path.basename(os.path.normpath(args.root))

inf(f'Packaging project {root}')

if not args.config:
    args.config = os.path.join(root, folderfrag_manifest)
with open(args.config) as f:
    packaging_config = json.loads(f.read())
section_name = args.section
section = packaging_config[section_name]
config = packaging_config['config']

if not args.archive:
    archive = os.path.join(os.getcwd(), directory_name)
else:
    archive = args.archive

try:
    if config['compression'] == 'lzma':
        zipfile_compression = zipfile.ZIP_LZMA
        archive = archive + '.lzma'
    elif config['compression'] == 'bz2':
        zipfile_compression = zipfile.ZIP_BZIP2
        archive = archive + '.bz2'
    else:
        zipfile_compression = zipfile.ZIP_DEFLATED
        archive = archive + '.zip'
except:
    zipfile_compression = zipfile.ZIP_DEFLATED
    archive = archive + '.zip'

inf(f'Destination archive: {archive}')

# step 2/5, parse the package configuration to figure out what gets to be included or excluded

include_files, include_dirs, exclude_files, exclude_dirs = recursive_find_files(packaging_config, section_name)

inf(f'Parsing package list for section "{section_name}"')
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
with zipfile.ZipFile(archive, 'w', zipfile_compression) as _zipfile:
    for _file in file_list:
        _zipfile.write(_file)
    for _dir in dir_list:
        files = glob.glob(_dir + '/**', recursive=True)
        for _file in files:
            _zipfile.write(_file)

# step 5/5, we are done

inf(f'Generated archive {os.path.basename(archive)} in {time.time()-now:0.3f} secs ({os.path.getsize(archive)} bytes)')
