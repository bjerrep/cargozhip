# cargozhip



Create compressed archives of assets according to manifest files. A manifest file specifies which files and directories to include and optionally which to exclude. Multiple inherited sections can be listed in the manifest file matching use cases such as packaging an asset for developers or packaging it for a runtime from e.g. a compiled project. 

Cargozhip tries to fit in where just compressing a folder, or specific subfolders, brings in too much and where there are perhaps so many different buildsystems in use that it just becomes unattractive to embed the asset/release thinking into each and everyone of their idiosyncrasies. 



```
./cargozhip.py -h
usage: cargozhip [-h] [--compress source] [--decompress destination] [--copy source] [--archive ARCHIVE] [--destination DESTINATION] [--section SECTION] [--config CONFIG] [--dryrun] [--compression COMPRESSION] [--quiet] [--force] [--verbose]

The slow, configurable and buggy as a complex number asset compressor.

options:
  -h, --help            show this help message and exit
  --compress source     Operation: Compress source directory to archive given by
  						--archive
  --decompress destination
                        Operation: decompress the given archive in the given 
                        destination (--archive need to be full filename)
  --copy source         Operation: implies that only the copy part is executed with
						files copied to destination and left there. The actual
                        compression part is skipped. Requires --destination
  --archive ARCHIVE     archive name without extension. Default name is the project
  						source directory name and default location is current directory.
                        Used for --compress and --decompress
  --destination DESTINATION
                        the destination path for the --copy command
  --section SECTION     the package configuration section name to use
  --config CONFIG       the cargozhip configuration file to load.
  						Default ./cargozhip.json
  --dryrun              don't actually make the archive
  --compression COMPRESSION
                        overrule compressor listed in configuration
                        [lzma|bz2|zip|tar.gz|tar.bz2|tar.xz]
  --quiet               no logging, default is informational logging
  --force               allow --copy and --decompress to write into the destination
  						root if its not empty. They will default bail out if the
                        destination has any files in it. Note that any old
                        cruft will be left untouched
  --verbose             verbose logging


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



### Symlinks

Support for symlinks to both files and folders is implemented for the zip style compressions zip, bz2 and lzma, and seems to work for at least the plain zip compression. Currently symlinks pointing outside the given root are simply skipped.

Be aware that some archivers fails to make proper symlinks when decompressing, at least when given the zip file made by Cargozhip. Using *unzip* on the commandline or Cargozhip native decompression and copy (see further down) should produce valid symlinks.




## Configuration 

The configuration file is a json file intended to reside in each asset cargozhip should work with.

As advertised it contains separate entries for files and directories to include and/or exclude for the given asset. A simple configuration file could look like this (the --config argument):

```
{
    "config": {
        "compression": "zip"
    },
    "runtime": {
        "include_dirs": ["lib", "bin"]
    }
}
```

The full feature set can be seen in [test/cargozhip.json](test/cargozhip.json).

Files and directories can be specified in two flavors, either default as "unix filename pattern matching" as used by the python [wcmatch](https://github.com/facelessuser/wcmatch/) module or if starting with a "!", as a regex.

Expect the outcome of a lot of intertwined including and excluding to be at least unpredictable. Either make more explicit rules or, well, fix the code.



## Relocating

Cargozhip can relocate, or move, files to a new location in the compressed archive. It could be documentation from all over the place that it would be nice to present to users of the archive as a single  ./doc directory or it could be binaries that should be in a single ./bin directory. 

#### Operator @

```
["@[destination]", "filter1" [, "filter2", ...] ]
```

Any files found from the filter list will be relocated to the destination root or ./destination if specified. The "@" sign should be interpreted as the destination root "./" so any destination path beyond that is optional. The original path is not preserved, only the actual files

Example:

```
include_files:	["just/as/is", "@inc", "lib1/inc/foo.h", "lib2/inc/bar.h", "@bin", "build/program"]
```

Which will result in something like

```
./just/as/is
./inc/foo.h
./inc/bar.h
./bin/program
```

#### Operator @@

It is also possible to have relocated files preserve their original path below the given search root by using leading @@ rather than @ as in the example above. The output will now be

```
./just/as/is
./inc/lib1/inc/foo.h
./inc/lib2/inc/bar.h
./bin/build/program
```

#### Operator @@@

Now the relocated files will preserve the path below the path found in the filter (so far wcmatch ../** only). Remember that the "library/" filter path below might hit somewhere deep inside the source tree, then it might make more sense as to why to have the @@@ operator in the first place.

```
include_files:	["@@@", "library/**"]
```

So if there was a "somewhere/library/lib/lib.so" and an "somewhere/library/inc/header.h" this will end up as 

```
./lib/lib.so
./inc/header.h
```



## Cheat sheet

A consequence of the current file matching is that it can be slightly baffling to get the include and exclude patterns to work as intended. Rather than risk to add to the confusion by "improving" the current matching some typical tasks and a way to do them are listed here:

```
root
	file
	subdir1
		file1
		subdir2
			file2	
```

Include all files in a given directory:

```
include_dirs:	["**/subdir1"]
Finds:			file1
```

Include everything in all sub directories recursively below a given directory (ignoring files in subdir1 itself):

```
include_dirs:	["**/subdir1/**"]
Finds:			subdir2, file2
```

Include everything below a given directory:

```
wcmatch
include_files:	["subdir1/**"]
or regex
include_files:	["!/subdir1/"]
Finds: 			file1, subdir2, file2
```

Exclude a specific filename:

```
include_files:	["!/subdir1/"]
exclude_files:	["!file1"]         (or wnmatch "**/file1")
Finds: 			subdir2, file2
```



## Compressing the demo asset.

```
./cargozhip.py --section dev --compress demo
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



## Around the world

First make a zip of the demo directory (again), then unzip it and finally make a copy operation. Then it will be interesting to see how the original demo directory compares to the content in the final copy destination. The copy operation is like a compress where the target archive is replaced by straight copies to a directory in the filesystem.

```
# 1/3 compress to zip archive
./cargozhip.py --section dev --compress demo --archive testoutput/around_1_compress

# 2/3 decompress to testoutput/around_2_decompress
./cargozhip.py --section dev --decompress testoutput/around_2_decompress --archive testoutput/around_1_compress.zip

# 3/3 copy the decompressed from
./cargozhip.py --section dev --copy testoutput/around_2_decompress --destination testoutput/around_3_copy
```

Now the final around_3_copy directory should be equal to the content of the zip which should be the parts from the demo set given the section "dev".



There is a test.py which test cargozhip for regressions through both the native python api and also the command line interface as done above. 



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



The cz_api also have a decompress method and a copy method.

