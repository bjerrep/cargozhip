#!/usr/bin/env python3
import json, os, pathlib, shutil, traceback, logging
import cargozhip.cz_api as cz_api, cargozhip.log as log
from cargozhip.log import inf, err, die, set_log_colors


def module_test():
    """
    Run the file scan only for the test cases starting with "test_".
    The configuration file for the module tests contains the additional entries
    'title' and 'expected' so the configuration will both contain the test cases
    and the expected outputs in one place.
    """
    config_name = 'test/cargozhip.json'
    config = cz_api.load_config(config_name)
    for section in config.keys():
        if section.startswith('test_'):
            inf('----------------------------------------------------------')
            inf(f'Title: {section}: {log.LIGHT_BLUE}{config[section]["title"]}{log.RESET}')
            scan_result = cz_api.scan('test', config, section)
            if config[section]['expected'] != scan_result.as_file_list():
                err('Test failed, this was the scan result:')
                for file in scan_result.as_file_list():
                    print(f'            "{file}",')
                raise Exception(f'module test {section}')
            else:
                inf('Pass')
                inf('')


def module_test_failures():
    """
    For now just verify that an exception is thrown
    """
    config_name = 'test/cargozhip.json'
    config = cz_api.load_config(config_name)
    for section in config.keys():
        if section.startswith('exception_'):
            inf(f'Title: {log.LIGHT_BLUE}{config[section]["title"]}{log.RESET}')
            try:
                _ = cz_api.scan('test', config, section)
                raise Exception("Failed, no exception was raised")
            except Exception as e:
                inf(f'Got expected {e.__repr__()}')


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


def run_minimal_example_a_section_with_only_a_depends():
    inf('')
    inf(' --------- run_minimal_example_a_section_with_only_a_depends() ----------')
    inf('')

    config = cz_api.minimal_config()
    config['only_depends'] = {'inherit': ['default']}
    archive = 'compresstest/run_minimal_example_a_section_with_only_a_depends'
    cz_api.compress('test', config, 'only_depends', archive)

    archive += '.lzma'
    if not os.path.exists(archive):
        raise Exception('run_minimal_example_a_section_with_only_a_depends')


def run_failing_examples():
    inf('')
    inf(' --------- run_failing_examples() ----------')
    inf('')

    # make a fresh subfolder to make the tests in
    failing_path = 'compresstest/failing'
    shutil.rmtree(failing_path, ignore_errors=True)
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
    ret = os.system('./cargozhip.py --root test --section test --config compresstest/test.json --archive compresstest/test')
    if ret:
        die('cargozhip.py failed')


def run_compressor_tests():
    pathlib.Path('compresstest').mkdir(exist_ok=True)
    compressor_test('zip')
    compressor_test('bz2')
    compressor_test('lzma')
    compressor_test('tar.gz')
    compressor_test('tar.bz2')
    compressor_test('tar.xz')


def run_copy_without_archiving():
    inf('')
    inf(' --------- run_copy_without_archiving ----------')
    inf('')
    config = cz_api.minimal_config()
    shutil.rmtree('compresstest/copy_test', ignore_errors=True)
    cz_api.copy('test', config, 'default', 'compresstest/copy_test')


try:
    log.set_log_colors()

    module_test()
    run_minimal_example()
    run_minimal_example_a_section_with_only_a_depends()
    run_failing_examples()
    run_compressor_tests()
    module_test()
    module_test_failures()
    run_copy_without_archiving()

    print('\nNote that compresstest directory isn\'t deleted automatically')

    print('\n---------------')
    print(' Test pass')
    print('---------------\n')
    exit(0)

except Exception as e:
    print(traceback.format_exc())
    print('\n---------------')
    print(f' Test fail, {e.__str__()}')
    print('---------------\n')
    exit(1)
