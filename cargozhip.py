#!/usr/bin/env python3
import argparse, logging, os, traceback
from cargozhip import cz
from cargozhip import cz_api
from cargozhip.log import err, cri, set_log_colors, logger as log

set_log_colors()

parser = argparse.ArgumentParser('cargozhip', description='''
    The slow, configurable and buggy as a complex number asset compressor.
    ''')
parser.add_argument('--root', default='.',
                    help='the root folder to work in, default current directory.')
parser.add_argument('--section',
                    help='the package configuration section name to use')
parser.add_argument('--config',
                    help=f'the package configuration to load. Default "root"/{cz.default_config}')
parser.add_argument('--archive',
                    help='archive name without extension. Default name is the project root directory name '
                         'and default location is current directory')
parser.add_argument('--dryrun', action='store_true',
                    help='don\'t actually make the archive')
parser.add_argument('--compression',
                    help='overrule compressor listed in configuration [lzma|bz2|zip|tar.gz|tar.bz2|tar.xz]')
parser.add_argument('--decompress', action='store_true',
                    help='decompress the archive in the given root')
parser.add_argument('--copyroot',
                    help='implies that only the copy part is executed with files copied to copyroot and left there. '
                         'The actual compression part is skipped.')
parser.add_argument('--quiet', action='store_true',
                    help='no logging, default is informational logging')
parser.add_argument('--verbose', action='store_true',
                    help='verbose logging')

args = parser.parse_args()

try:
    if args.verbose:
        log.setLevel(logging.DEBUG)
    elif args.quiet:
        log.setLevel(logging.WARNING)
    else:
        log.setLevel(logging.INFO)

    if not os.path.exists(args.root):
        cri(f'Root folder {args.root} not found, "{os.path.join(os.getcwd(), args.root)}"')

    if args.root == '.' or not args.root:
        root = os.getcwd()
    else:
        root = os.path.abspath(args.root)

    if not args.config:
        config_file = os.path.join(root, cz.default_config)
    else:
        config_file = os.path.abspath(args.config)

    if not args.archive:
        archive = os.path.normpath(os.path.join(os.getcwd(), root))
    else:
        archive = args.archive

    if args.decompress:
        cz_api.decompress(archive, root)
    elif args.copyroot:
        cz_api.copy(root, config_file, args.section, args.copyroot)
    else:
        cz_api.compress(root, config_file, args.section, archive, args.dryrun, args.compression)

except Exception as e:
    err(f'{e.__str__()}')
    if args.verbose:
        print(traceback.format_exc())
    exit(1)

exit(0)
