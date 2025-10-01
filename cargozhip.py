#!/usr/bin/env python3
import argparse, logging, os, traceback

# In case this script is separated from the default source folder
# then one option is to specify where to find the 'cargozhipsrc' folder here:
# import sys
# sys.path.append('location_hosting_cargozhipsrc')

from cargozhipsrc import cz
from cargozhipsrc import cz_api
from cargozhipsrc.log import err, set_log_colors, logger as log

set_log_colors()

parser = argparse.ArgumentParser('cargozhipsrc', description='''
    The slow, configurable and buggy as a complex number asset compressor.
    ''')
parser.add_argument('--compress', metavar='source',
                    help='Operation: Compress source directory to archive given by --archive')
parser.add_argument('--decompress', metavar='destination',
                    help='Operation: decompress the given archive in the given destination (--archive need to be full filename)')
parser.add_argument('--copy', metavar='source',
                    help='Operation: implies that only the copy part is executed with files copied to destination and left there. '
                         'The actual compression part is skipped. Requires --destination')

parser.add_argument('--archive',
                    help='archive name without extension. Default name is the project source directory name '
                         'and default location is current directory. Used for --compress and --decompress')

parser.add_argument('--destination',
                    help='the destination path for the --copy command')

parser.add_argument('--section',
                    help='the package configuration section name to use')
parser.add_argument('--config',
                    help=f'the cargozhipsrc configuration file to load. Default ./{cz.default_config}')
parser.add_argument('--dryrun', action='store_true',
                    help='don\'t actually make the archive')
parser.add_argument('--compression',
                    help='overrule compressor listed in configuration [lzma|bz2|zip|tar.gz|tar.bz2|tar.xz]')
parser.add_argument('--quiet', action='store_true',
                    help='no logging, default is informational logging')
parser.add_argument('--force', action='store_true',
                    help='allow --copy and --decompress to write into the destination root if its not empty. They will default '
                         'bail out if the destination has any files in it. Note that any old cruft will be left untouched')
parser.add_argument('--verbose', action='store_true',
                    help='verbose logging with exception stacktraces')

args = parser.parse_args()

try:
    if args.verbose:
        log.setLevel(logging.DEBUG)
    elif args.quiet:
        log.setLevel(logging.WARNING)
    else:
        log.setLevel(logging.INFO)

    if args.compress:
        if not args.config:
            config_file = os.path.join(args.compress, cz.default_config)
        else:
            config_file = os.path.abspath(args.config)
        cz_api.compress(args.compress, config_file, args.section, args.archive, args.dryrun, args.compression)
    elif args.decompress:
        cz_api.decompress(args.archive, args.decompress, args.force)
    elif args.copy:
        if not args.config:
            config_file = os.path.join(args.copy, cz.default_config)
        else:
            config_file = os.path.abspath(args.config)
        cz_api.copy(args.copy, config_file, args.section, args.destination)
    else:
        err('Need an --compress, --decompress or --copy argument')

except Exception as e:
    print(f'Terminated with exception: \'{e.__str__()}\'')
    if args.verbose:
        print(traceback.format_exc())
    exit(1)

exit(0)
