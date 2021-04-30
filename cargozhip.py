#!/usr/bin/env python3
import argparse, logging, os
import cz
import cz_api
from log import err, cri, logger as log


parser = argparse.ArgumentParser('cargozhip', description='''
    The slow, configurable and buggy as a complex number asset compressor.
    ''')
parser.add_argument('--root', default='.',
                    help='the root folder to work in, default current directory.')
parser.add_argument('--section', required=True,
                    help='the package configuration section name to use')
parser.add_argument('--config',
                    help=f'the package configuration to load. Default "root"/{cz.default_config}')
parser.add_argument('--archive',
                    help='archive name without extension. Default name is the project root directory name '\
                         'and default location is current directory')
parser.add_argument('--dryrun', action='store_true',
                    help='don\'t actually make the archive')
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
    if args.root == '.':
        root = os.path.basename(os.getcwd())
    else:
        root = os.path.basename(os.path.normpath(args.root))

    if not args.config:
        config_file = os.path.join(root, cz.default_config)
    else:
        config_file = args.config

    cz_api.compress(args.root, config_file, args.section, args.archive, args.dryrun)

except Exception as e:
    err(f'{e.__repr__()}')
    exit(1)

exit(0)
