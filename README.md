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

## Issues / Questions

smugsync is still young and experimental. Feel free to open an issue on github to report any problems.
Code contributions are most welcome to extend and improve smugsync

## License

smugsync is released under the MIT license.
