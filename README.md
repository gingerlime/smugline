# smugsync
a simple command line tool for smugmug (using [smugpy](https://github.com/chrishoffman/smugpy)).
Written in python 2.7

## Installation

* `git clone` the repository from github
* `pip install -r requirements.txt`

## API Key

You must have a smugmug account and [apply for an API key](http://www.smugmug.com/hack/apikeys).
Once you apply, the API key will be visible on your account settings -> Discovery -> API keys.
You only need the `Key` (no need for the `Secret`).

## Features

* listing albums on your smugmug account
* uploading from a folder (recursively) to an album on smugmug
* existing images will be uploaded only once (skipping duplicates)

## Usage

```shell
$ python smugsync.py

Usage:
  smugsync.py upload <album_name> --api-key=<apy_key>
                                  [--from=folder_name]
                                  [--email=email_address]
                                  [--password=password]
  smugsync.py list --api-key=apy_key
                   [--email=email_address]
                   [--password=password]
  smugsync.py (-h | --help)
```

```shell
$ ./smugsync.py list --api-key=... --email=your@email.com
Password:
available albums:
My Album
Another Album
Sample Gallery

$ ./smugsync.py upload 'My Album' --api-key=... --email=your@email.com --password=yourpassword
uploading ./IMG_123.jpg -> My Album
uploading ./IMG_124.jpg -> My Album
...
uploading ./IMG_999.jpg -> My Album

$ ./smugsync.py upload 'My Album' --folder=/my_pics/ --api-key=... --email=your@email.com --password=yourpassword
skipping image /my_pics/IMG_123.jpg (duplicate)
skipping image /my_pics/IMG_124.jpg (duplicate)
...
```

## Duplicates

smugsync tries to avoid uploading images that were already uploaded to smugmug. To do so, it relies on the MD5 signature, based on the actual content of the image. This is the most reliable way to detect two identical copies of any file. However, Smugmug appears to auto-rotate images once they are uploaded. In such cases, the MD5 signature will mismatch and duplicate images might still get created.

A workaround for this problem, is to rotate all images *before* uploading. [More information about image rotation tools](http://how-to.wikia.com/wiki/How_to_auto-rotate_digital_photos_to_their_proper_orientation).

On Linux, the best way to achieve this is using the `exifautotran` utility (on ubuntu run `sudo apt-get install libjpeg-turbo-progs`).

## Issues / Questions

smugsync is still young and experimental. Feel free to open an issue on github to report any problems.
Code contributions are most welcome to extend and improve smugsync

## License

smugsync is released under the MIT license.
