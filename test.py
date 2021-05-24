#!/usr/bin/env python3
import cz_api, log
from log import inf, err
import json, os, pathlib


def module_test():
    """
    The configuration file for the module tests contains the additional entries
    'title' and 'expected' so the configuration will both contain the test cases
    and the expected outputs in one place.
    """
    config_name = 'test/cargozhip.json'
    config = cz_api.load_config(config_name)
    for section in config.keys():
        if section.startswith('test_'):
            inf(f'Title: {log.LIGHT_BLUE}{config[section]["title"]}{log.RESET}')
            file_list = cz_api.scan('test', config, section)
            if config[section]['expected'] != file_list:
                err('Test failed, this was the scan result:')
                for file in file_list:
                    print(f'            "{file}",')
                raise Exception(f'module test {section}')
            else:
                inf('Pass')
                inf('')


def run_minimal_example():
    inf('')
    inf(' --------- run_minimal_example() ----------')
    inf('')

    config = cz_api.minimal_config()
    archive = 'compresstest/minimal_example'
    cz_api.compress('test', config, 'default', archive)

    archive += '.lzma'
    if not os.path.exists(archive):
        raise Exception('run_minimal_example failed')


# Compressor tests :
# For now its a success if trying out the different compressors dont't crash.
# Whatever is present under the project root is compressed (e.g. including .git/)
#
config_file = (
    {
        "config": {
            "compression": "..."
        },
        "test": {
            "include_files": ["**", ".**"],
            "include_dirs": [".**"],
            "exclude_dirs": ["compresstest"]
        }
    })


def compressor_test(compression):
    inf('')
    inf(f' --------- compressor test with {compression} ----------')
    inf('')
    config_file['config']['compression'] = compression
    with open('compresstest/test.json', 'w') as f:
        f.write(json.dumps(config_file))
    os.system('./cargozhip.py --root . --section test --config compresstest/test.json --archive compresstest/test')


def run_compressor_tests():
    pathlib.Path('compresstest').mkdir(exist_ok=True)
    compressor_test('zip')
    compressor_test('bz2')
    compressor_test('lzma')
    compressor_test('tar.gz')
    compressor_test('tar.bz2')
    compressor_test('tar.xz')
    print('\nNote that compresstest directory isn\'t deleted automatically')


def run_copy_without_archiving():
    config = cz_api.minimal_config()
    cz_api.copy('test', config, 'default', 'compresstest/copy_test')


try:
    run_minimal_example()
    run_compressor_tests()
    module_test()
    run_copy_without_archiving()

    print('\n---------------')
    print(' Test pass')
    print('---------------\n')
    exit(0)

except Exception as e:
    print('\n---------------')
    print(f' Test fail, {e.__repr__()}')
    print('---------------\n')
    exit(1)
