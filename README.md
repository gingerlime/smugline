# smugline [![Build Status](https://secure.travis-ci.org/gingerlime/smugline.png?branch=master)](http://travis-ci.org/gingerlime/smugline)

a simple command line tool for smugmug (using [smugpy](https://github.com/chrishoffman/smugpy)).
Written in python 2.x/3.x

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
* uploading images, videos or both (default: images)
* clearing duplicate images or video from an album

## Usage

print usage info

```shell
$ python smugline.py -h

Usage:
  smugline.py upload <album_name> --api-key=<apy_key>
                                  [--from=folder_name]
                                  [--media=(videos | images | all)]
                                  [--email=email_address]
                                  [--password=password]
  smugline.py process <json_file> --api-key=<apy_key>
                                  [--from=folder_name]
                                  [--email=email_address]
                                  [--password=password]
  smugline.py list --api-key=apy_key
                   [--email=email_address]
                   [--password=password]
  smugline.py create <album_name> --api-key=apy_key
                                  [--privacy=(unlisted | public)]
                                  [--email=email_address]
                                  [--password=password]
  smugline.py clear_duplicates <album_name> --api-key=<apy_key>
                                            [--email=email_address]
                                            [--password=password]
  smugline.py (-h | --help)

Arguments:
  upload            uploads files to a smugmug album
  process           processes a json file with upload directives
  list              list album names on smugmug
  create            create a new album
  clear_duplicates  finds duplicate images in album and deletes them

Options:
  --api-key=api_key       your smugmug api key
  --from=folder_name      folder to upload from [default: .]
  --media=(videos | images | all)
                          upload videos, images, or both [default: images]
  --privacy=(unlisted | public)
                          album privacy settings [default: unlisted]
  --email=email_address   email address of your smugmug account
  --passwod=password      smugmug password
```

list albums

```shell
$ ./smugline.py list --api-key=... --email=your@email.com
Password:
available albums:
My Album
Another Album
Sample Gallery
```

upload from current folder to 'My Album'

```shell
$ ./smugline.py upload 'My Album' --api-key=... --email=your@email.com --password=yourpassword
uploading ./IMG_123.jpg -> My Album
uploading ./IMG_124.jpg -> My Album
...
uploading ./IMG_999.jpg -> My Album
```

uploading again, this time specifying a source folder

```shell
$ ./smugline.py upload 'My Album' --folder=/my_pics/ --api-key=... --email=your@email.com --password=yourpassword
skipping image /my_pics/IMG_123.jpg (duplicate)
skipping image /my_pics/IMG_124.jpg (duplicate)
...
```

uploading files described in a json file

```shell
$ ./smugline.py process images.json --folder=/my_pics/ --api-key=... --email=your@email.com --password=yourpassword
```

where images.json (utf8 encoding) contain

```json
[
{
"AlbumName": "Birds",
"Caption": "Toco Toucan",
"File": "birds/toco_toucan.jpg",
"Keywords": "birds; animals",
"Title": "Toucan"
},
...
]
```

creating a new album (will create under 'Other' category)

```shell
$ ./smugline.py create 'New Album' --api-key=... --email=your@email.com --password=yourpassword
unlisted album New Album created. URL: http://<your smugmug nickname>.smugmug.com/Other/New-Album/n-vH4ZF
```

uploading videos only
```shell
$ ./smugline.py upload 'My Album' --api-key=... --email=your@email.com --password=yourpassword --media=videos
uploading ./MOV_123.MOV -> My Album
uploading ./MOV_124.mp4 -> My Album
...
uploading ./MOV_999.avi -> My Album
```

clearing duplicate images or videos in 'My Album'
```shell
$ ./smugline.py clear_duplicates 'My Album' --api-key=... --email=your@email.com --password=yourpassword
deleting image IMG_1234.JPG (md5: d429a9d0bf0829082985cb6941f6a547)
...
```

## Duplicates

smugline tries to avoid uploading images that were already uploaded to smugmug. To do so, it relies on the MD5 signature, based on the actual content of the image. This is the most reliable way to detect two identical copies of any file. However, Smugmug appears to auto-rotate images once they are uploaded. In such cases, the MD5 signature will mismatch and duplicate images might still get created.

A workaround for this problem, is to rotate all images *before* uploading. [More information about image rotation tools](http://how-to.wikia.com/wiki/How_to_auto-rotate_digital_photos_to_their_proper_orientation).

On Linux, the best way to achieve this is using the `exifautotran` utility (on ubuntu run `sudo apt-get install libjpeg-turbo-progs`).

### Clearing duplicates

the `clear_duplicates` command will search for items in an album with identical MD5 signature, and will keep only one
copy. It won't detect any changes to metadata (caption, comments etc), so use with care!


## Issues / Questions

smugline is still young and experimental. Feel free to open an issue on github to report any problems.
Code contributions are most welcome to extend and improve smugline

## License

smugline is distributed under the MIT license. All 3rd party libraries and components are distributed under their
respective license terms.


```
Copyright (C) 2014 Yoav Aner

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
```
