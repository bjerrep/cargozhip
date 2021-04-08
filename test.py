#!/usr/bin/env python3
import cz
import json, os, pathlib


def test_exclude_file_hit():
    assert not cz.exclude_file_hit('inc/test.h', ['test'])
    assert not cz.exclude_file_hit('inc/test.h', ['inc'])


def test_exclude_dir_hit():
    assert not cz.exclude_dir_hit('inc/test.h', ['test'])
    assert cz.exclude_dir_hit('inc/test.h', ['inc'])


test_exclude_file_hit()
test_exclude_dir_hit()


#
# livetest : For now its a success if trying out the different compressors dont't crash.
#            Whatever is present under the project root is compressed (e.g. including .git)
#

config_file = (
    {
        "config": {
            "compression": "..."
        },
        "test": {
            "include_files": ["*"],
            "exclude_dirs": ["livetest"]
        }
    })


def live_test(compression):
    print(f'\n --------- livetest with {compression} ----------\n')
    config_file['config']['compression'] = compression
    with open('livetest/livetest.json', 'w') as f:
        f.write(json.dumps(config_file))
    os.system('./cargozhip.py --root . --section test --config livetest/livetest.json --archive livetest/livetest')


pathlib.Path('livetest').mkdir(exist_ok=True)
live_test('zip')
live_test('bz2')
live_test('lzma')
live_test('tar.gz')
live_test('tar.bz2')

print('\nNote that livetest directory isn\'t deleted automatically')


print('\n---------------')
print(' Tests passed')
print('---------------\n')
