# cargozhip



Create compressed archives of assets according to manifest files. A manifest file specifies which files and directories to include and optionally which to exclude. Multiple inherited sections can be listed in the manifest file matching use cases such as packaging an asset for developers or packaging it for a runtime from e.g. a compiled project. 

Cargozhip tries to fit in where just compressing a folder, or specific subfolders, brings in too much and where there are perhaps so many different buildsystems in use that it just becomes unattractive to embed the asset/release thinking into each and everyone of their idiosyncrasies. 



```
./cargozhip.py -h
usage: cargozhip [-h] [--root ROOT] --section SECTION [--config CONFIG] [--archive ARCHIVE] [--dryrun] [--quiet] [--verbose]

The slow, configurable and buggy as a complex number asset compressor.

optional arguments:
  -h, --help         show this help message and exit
  --root ROOT        the root folder to work in, default current directory.
  --section SECTION  the package configuration section name to use
  --config CONFIG    the package configuration to load. Default "root"/cargozhip.json
  --archive ARCHIVE  archive name without extension. Default name is the project root directory name and default location is current directory
  --dryrun           don't actually make an archive
  --quiet            no logging, default is informational logging
  --verbose          verbose logging
```



## Dependencies

Cargozhip uses [wcmatch](https://github.com/facelessuser/wcmatch/) rather than the native python fnmatch for filename and directory name matching. 

It can be installed via pip.



## Compression formats

By using the native python compression modules the supported formats are:

- zip
- bz2
- lzma
- tar.gz
- tar.bz2
- tar.xz


## Config 

A config file is a json file intended to reside in each asset cargozhip should work with.

As advertised it contains separate entries for files and directories to include and/or exclude for the given asset. The full feature set can be seen in **testlib/cargozhip.json**.

Files and directories can be specified in two flavors, either default as "unix filename pattern matching" as used by the python [wcmatch](https://github.com/facelessuser/wcmatch/) module or if starting with a "!", as a regex.

Expect the outcome of a lot of intertwined including and excluding to be at least unpredictable. Either make more explicit rules or, well, fix the code.



## Compressing the demo asset.

```
./cargozhip.py --section dev --root demo --info
INF Loading configuration file demo/cargozhip.json
INF Packaging project "demo" section "dev"
INF Destination archive: /home/user/src/cargozhip/demo.lzma
INF Parsing package list for section "dev"
INF   Include files: ['**/*.h', '**/*.a', '*CMakeLists.txt', '!(?i)license\\.txt', 'version.txt', 'cargozhip.json']
INF   Exclude files: ['**/secret_key.h']
INF   Include dirs: ['art']
INF   Exclude dirs: ['test']
INF Scanning ...
INF Matched 6 files
INF   CMakeLists.txt
INF   LICENSE.txt
INF   art/pop.song
INF   cargozhip.json
INF   inc/testlib.h
INF   lib/libtest.a
INF Scanned 17 files and 8 directories in 0.004 secs
INF Compressing 6 files ...
INF Generated archive demo.lzma in 0.026 secs (1012 bytes)
```



Using the zipinfo utility to check what we got. Note that the content is stripped of references to the original root folder:

```
zipinfo demo.lzma
Archive:  demo.lzma
Zip file size: 1012 bytes, number of entries: 6
-rw-r--r--  6.3 unx        0 b- lzma 21-Apr-01 14:30 CMakeLists.txt
-rw-r--r--  6.3 unx        0 b- lzma 21-Apr-05 01:48 LICENSE.txt
-rw-r--r--  6.3 unx        0 b- lzma 21-Apr-01 16:23 art/pop.song
-rw-r--r--  6.3 unx      747 b- lzma 21-Apr-29 22:50 cargozhip.json
-rw-r--r--  6.3 unx        0 b- lzma 21-Mar-31 00:21 inc/testlib.h
-rw-r--r--  6.3 unx        0 b- lzma 21-Mar-31 00:22 lib/libtest.a
6 files, 747 bytes uncompressed, 380 bytes compressed:  49.1%
```



## Native python

The work is done by the method compress in the cz_api.py. This is what is used by the cargozhip.py executable script which is just a thin command line argument parser. 

```
def compress(root, config_or_file, section, archive, dry_run=False):
```



As a practical example then compressing a directory could look like the following (keeping in mind that this is exactly the usecase where Cargozhip makes very little sense):

```
import cz_api
config = cz_api.minimal_config()
cz_api.compress('test', config, 'default', 'myarchive')
```



The cz_api also have a decompress method which is straightforward and a copy method which runs in cargozhip style except it doesn't make an archive but just copies files to a destination directory as they are matched.

