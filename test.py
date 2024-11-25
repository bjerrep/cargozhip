#!/usr/bin/env python3
import json, os, inspect, sys, pathlib, shutil, traceback, filecmp, logging, subprocess
import cargozhip.cz_api as cz_api
from cargozhip.log import inf, err, LIGHT_BLUE, RESET, set_log_colors, logger as log

TESTOUTPUT = 'testoutput'

def function_title():
    inf('')
    inf('-----------------------------------------------------------------------------')
    inf(f'              {inspect.stack()[2][4][0].strip()}')
    inf('-----------------------------------------------------------------------------')
    inf('')

def isfile(name):
    if not os.path.exists(name):
        err(f'no file {name}')

def delfilelist(names):
    for name in names:
        try:
            os.remove(name)
        except:
            pass

def delpath(path):
    shutil.rmtree(path, ignore_errors=True)


def run_test_configuration_test_sections():
    """
    Run the file scan only for the sections starting with "test_".
    The configuration file for the module tests contains the additional entries
    'title' and 'expected' so the configuration will both contain the test cases
    and the expected outputs in one place.
    """
    function_title()
    config_name = 'test/cargozhip.json'
    config = cz_api.load_config(config_name)
    for section in config.keys():
        if section.startswith('test_'):
            inf('----------------------------------------------------------')
            inf(f'Title: {section}: {LIGHT_BLUE}{config[section]["title"]}{RESET}')
            scan_result = cz_api.scan('test', config, section)
            if config[section]['expected'] != scan_result.all_destinations():
                err('Test failed, this was the scan result:')
                for file in scan_result.all_destinations():
                    print(f'            "{file}",')
                err(f'module test {section}')

            inf('Pass')
            inf('')


def run_test_configuration_exception_sections():
    """
    For now just verify that an exception is thrown
    """
    function_title()
    config_name = 'test/cargozhip.json'
    config = cz_api.load_config(config_name)
    for section in config.keys():
        if section.startswith('exception_'):
            inf(f'Title: {LIGHT_BLUE}{config[section]["title"]}{RESET}')
            try:
                _ = cz_api.scan('test', config, section)
                err("Failed, no exception was raised")
            except Exception as e:
                inf(f'Got expected {e.__repr__()}')


def run_minimal_example():
    function_title()
    delpath(TESTOUTPUT)

    config = cz_api.minimal_config()
    archive = os.path.join(TESTOUTPUT, 'minimal_example')
    cz_api.compress(root='.', config_or_file=config, section='everything', archive=archive)

    archive += '.zip'
    if not os.path.exists(archive):
        err('run_minimal_example failed')


def run_minimal_example_a_section_with_only_a_depends():
    function_title()

    config = cz_api.minimal_config()
    config['only_depends'] = {'inherit': ['everything']}
    archive = os.path.join(TESTOUTPUT, 'run_minimal_example_a_section_with_only_a_depends')
    cz_api.compress('test', config, 'only_depends', archive)

    archive += '.zip'
    if not os.path.exists(archive):
        err('run_minimal_example_a_section_with_only_a_depends')


def run_failing_examples():
    function_title()

    # make a fresh subfolder to make the tests in
    failing_path = os.path.join(TESTOUTPUT, 'failing')
    delpath(failing_path)
    pathlib.Path(failing_path).mkdir()
    os.chdir(failing_path)

    config = cz_api.minimal_config()

    try:
        archive = 'failing_since_there_are_no_files'
        cz_api.compress(root='.', config_or_file=config, section='everything', archive=archive)
        err(archive)
    except:
        pass

    open('testfile', 'a').close()
    archive = 'recursive_archive'

    # this is okay, the new archive will be written in the source root
    cz_api.compress(root='.', config_or_file=config, section='everything', archive=archive)

    # this is not okay, the new archive would include an existing version of itself
    try:
        cz_api.compress(root='.', config_or_file=config, section='everything', archive=archive)
        err(archive)
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
            "exclude_dirs": [TESTOUTPUT]
        }
    })


def run_decompressor_tests():
    function_title()
    test_dest = os.path.join(TESTOUTPUT, 'decompressor_tests')
    test_output = os.path.join(TESTOUTPUT, 'decompressor_tests/output')
    config = cz_api.minimal_config()
    cz_api.compress(root='test', config_or_file=config, section='everything', archive=os.path.join(test_dest, 'test'))
    compression = config['config']['compression']
    archivename = 'test.' + compression
    cz_api.decompress(archive=os.path.join(test_dest, archivename), destpath=test_output)
    # compare the original with the decompressed
    _dircmp = filecmp.dircmp('test', test_output)
    if _dircmp.left_only or _dircmp.right_only:
        err(f'directories test and {test_output} differs')


def run_copy_without_archiving():
    function_title()
    config = cz_api.minimal_config()
    delpath(os.path.join(TESTOUTPUT, 'copy_test'))
    cz_api.copy(root='test', config_or_file=config, section='everything', destination=os.path.join(TESTOUTPUT, 'copy_test'))
    # compare the original with the copy
    _dircmp = filecmp.dircmp('test', os.path.join(TESTOUTPUT, 'copy_test'))
    if _dircmp.left_only or _dircmp.right_only:
        err(f'directories test and {TESTOUTPUT}/copy_test differs')


def cmdline_test(title, arguments, expect=0):
    inf('')
    inf(f'   ------- {title} ------')
    command = './cargozhip.py ' + arguments
    inf(f'           {command}')
    exitcode = subprocess.call(command,shell=True)
    if exitcode != expect:
        err(f'command line test {title} failed (return code={exitcode})')

def cmdline_compressor_test(compression):
    function_title()
    config_file['config']['compression'] = compression
    with open(os.path.join(TESTOUTPUT, 'test.json'), 'w') as f:
        f.write(json.dumps(config_file))
    cmdline_test(compression, f"--compress test --section test --config {TESTOUTPUT}/test.json --archive {TESTOUTPUT}/test")

def run_command_line_compress():
    function_title()
    delfilelist(['demo.zip', 'demo2.zip', 'demo3.zip'])

    # the example from the readme. Config will be loaded from source 'demo' and archive will be 'demo.zip'
    cmdline_test("cmd test 100", "--compress demo --section dev")
    isfile('demo.zip')
    # explicitly set the archive name
    cmdline_test("cmd test 100", "--compress demo --section dev --archive demo2")
    isfile('demo2.zip')
    # finally explicitly set the config file to use
    cmdline_test("cmd test 100", "--compress demo --section dev --archive demo3 --config demo/cargozhip.json")
    isfile('demo3.zip')

    delfilelist(['demo.zip', 'demo2.zip', 'demo3.zip'])


def run_command_line_decompress():
    function_title()
    delpath(TESTOUTPUT)
    archive = os.path.join(TESTOUTPUT, 'demo')
    destination = os.path.join(TESTOUTPUT, 'decompresstest')

    # make the archive to decompress
    cmdline_test("cmd test 200", f"--archive {archive} --compress demo --section dev")

    # try to decompress the above which should run smoothly since the destination does not exist
    cmdline_test("cmd test 201", f"--archive {archive}.zip --decompress {destination}")
    # do it second time and it fails as the destination now exists
    cmdline_test("cmd test 202 (should fail)", f"--archive {archive} --decompress {destination}", 1)
    # add a --force and it should run again
    cmdline_test("cmd test 203", f"--archive {archive}.zip --decompress {destination} --force")

    delpath(TESTOUTPUT)

def run_command_line_copy():
    function_title()
    delpath('copytest')
    # make the archive demo.zip
    cmdline_test("cmd test 100", "--compress demo --section dev")
    #
    cmdline_test("cmd test 301", "--archive test.zip --section dev --copy demo --destination copytest")
    cmdline_test("cmd test 300 (should fail)", "--archive test.zip --section dev --copy demo --destination copytest", 1)

    delpath('copytest')

def run_command_line_compressor_tests():
    function_title()
    pathlib.Path(TESTOUTPUT).mkdir(exist_ok=True)
    cmdline_compressor_test('zip')
    cmdline_compressor_test('bz2')
    cmdline_compressor_test('lzma')
    cmdline_compressor_test('tar.gz')
    cmdline_compressor_test('tar.bz2')
    cmdline_compressor_test('tar.xz')

try:
    set_log_colors()
    log.setLevel(logging.DEBUG)

    run_test_configuration_test_sections()
    run_test_configuration_exception_sections()

    # test native python api
    run_minimal_example()
    run_minimal_example_a_section_with_only_a_depends()
    run_failing_examples()
    run_decompressor_tests()
    run_copy_without_archiving()

    # call cargozhip.py from commandline. Just verify that all invocations complete with an expected exit code
    run_command_line_compress()
    run_command_line_decompress()
    run_command_line_copy()
    run_command_line_compressor_tests()

    print('\n---------------')
    print(' Test pass')
    print('---------------\n')
    sys.exit(0)

except Exception as e:
    print(traceback.format_exc())
    print('\n---------------')
    print(f' Test fail, {e.__str__()}')
    print('---------------\n')
    sys.exit(1)
