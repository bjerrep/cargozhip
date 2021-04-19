# cargozhip



Create compressed archives of assets according to manifest files. A manifest file specifies which files and directories to include and optionally which to exclude. Multiple inherited sections can be listed in the manifest file matching use cases such as packaging an asset for developers or packaging it for a runtime from e.g. a compiled project. 

Cargozhip tries to fit in where just compressing a folder, or specific subfolders, brings in too much and where there are perhaps so many different buildsystems in use that it just becomes unattractive to embed the asset/release thinking into each and everyone of their idiosyncrasies. 



```
./cargozhip.py -h
usage: cargozhip [-h] [--root ROOT] --section SECTION [--config CONFIG] [--archive ARCHIVE]

The slow, configurable and buggy as a complex number asset compressor.

optional arguments:
  -h, --help         show this help message and exit
  --root ROOT        the root folder to work in, default current directory.
  --section SECTION  the package configuration section to use
  --config CONFIG    the package configuration to load. Default "root"/cargozhip.json
  --archive ARCHIVE  archive name without extension. Default the project root directory name

```



## Compression formats

By using the native python compression modules the supported formats are:

- zip

- bz2

- lzma

- tar.gz

- tar.bz2



## Config 

A config file is a json file intended to reside in each asset cargozhip should work with.

As advertised it contains separate entries for files and directories to include and/or exclude for the given asset. The full feature set can be seen in **testlib/cargozhip.json**.

Files and directories can be specified in two flavors, either default as "unix filename pattern matching" as used by the python fnmatch module or if starting with a "!", as a regex.

Expect the outcome of a lot of intertwined including and excluding to be at least unpredictable. Either make more explicit rules or, well, fix the code.



## Compressing the demo 'testlib' asset.

```
./cargozhip.py --section dev --root testlib/
Packaging project testlib/
Destination archive: /home/dizzy/src/cargozhip/testlib.lzma
Parsing package list for section "dev"
  Include files: ['*.h', '*.a', '*CMakeLists.txt', '!(?i)license\\.txt', 'version.txt', 'cargozhip.json']
  Exclude files: ['**/secret_key.h']
  Include dirs: ['art']
  Exclude dirs: ['test']
Scanning ...
Matched 5 files
  CMakeLists.txt
  LICENSE.txt
  cargozhip.json
  inc/testlib.h
  lib/libtest.a
Matched 1 directories
  art
Scanned 15 files and 7 directories in 0.001 secs
Compressing 5 files and 1 directories ...
Generated archive testlib.lzma in 0.020 secs (1056 bytes)

```



Using the zipinfo utility to check what we got. Note that the content is stripped of references to the original root folder:

```
zipinfo testlib.lzma
Archive:  testlib.lzma
Zip file size: 1056 bytes, number of entries: 7
-rw-r--r--  6.3 unx        0 b- lzma 21-Mar-31 00:22 lib/libtest.a
-rw-r--r--  6.3 unx      615 b- lzma 21-Apr-05 01:47 cargozhip.json
-rw-r--r--  6.3 unx        0 b- lzma 21-Mar-31 00:21 inc/testlib.h
-rw-r--r--  6.3 unx        0 b- lzma 21-Apr-01 14:30 CMakeLists.txt
-rw-r--r--  6.3 unx        0 b- lzma 21-Apr-05 01:48 LICENSE.txt
drwxr-xr-x  2.0 unx        0 b- stor 21-Apr-01 16:23 art/
-rw-r--r--  6.3 unx        0 b- lzma 21-Apr-01 16:23 art/pop.song
7 files, 615 bytes uncompressed, 340 bytes compressed:  44.7%

```



## Native python

The work is done by the method compress in the cz_api.py. This is what is used by the cargozhip.py executable script which is just a thin command line argument parser. 

```
def compress(root, config, section, archive):
```



