#!/usr/bin/env python3
import os, time, argparse
from cz import *
import cz_api

parser = argparse.ArgumentParser('cargozhip', description='''
    The slow, configurable and buggy as a complex number asset compressor.
    ''')
parser.add_argument('--root', default='.',
                    help='the root folder to work in, default current directory.')
parser.add_argument('--section', required=True,
                    help='the package configuration section name to use')
parser.add_argument('--config',
                    help=f'the package configuration to load. Default "root"/{default_config}')
parser.add_argument('--archive',
                    help='archive name without extension. Default the project root directory name')

args = parser.parse_args()


success, message = cz_api.compress(args.root, args.config, args.section, args.archive)

if success:
    inf(message)
else:
    err('Packaging failed with error')
    err(message)
    exit(1)

