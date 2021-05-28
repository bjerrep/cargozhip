#!/usr/bin/env python3
import cz_api, log
from log import inf, err
import json, os, pathlib, shutil


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


def run_failing_examples():
    inf('')
    inf(' --------- run_failing_examples() ----------')
    inf('')

    # make a fresh subfolder to make the tests in
    failing_path = 'compresstest/failing'
    shutil.rmtree(failing_path)
    pathlib.Path(failing_path).mkdir()
    os.chdir(failing_path)

    config = cz_api.minimal_config()

    try:
        archive = 'failing_since_there_are_no_files'
        cz_api.compress('.', config, 'default', archive)
        raise Exception(archive)
    except:
        pass

    open('testfile', 'a').close()
    archive = 'recursive_archive'

    # this is okay, the new archive will be written in the source root
    cz_api.compress('.', config, 'default', archive)

    # this is not okay, the new archive would include an existing version of itself
    try:
        cz_api.compress('.', config, 'default', archive)
        raise Exception(archive)
    except:
        pass

    os.chdir('../..')


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


def run_copy_without_archiving():
    config = cz_api.minimal_config()
    cz_api.copy('test', config, 'default', 'compresstest/copy_test')


try:
    run_minimal_example()
    run_failing_examples()
    run_compressor_tests()
    module_test()
    run_copy_without_archiving()

    print('\nNote that compresstest directory isn\'t deleted automatically')

    print('\n---------------')
    print(' Test pass')
    print('---------------\n')
    exit(0)

except Exception as e:
    print('\n---------------')
    print(f' Test fail, {e.__repr__()}')
    print('---------------\n')
    exit(1)
