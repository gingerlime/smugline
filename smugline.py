#!/usr/bin/env python
"""smugline - command line tool for SmugMug

Usage:
  smugline.py upload <album_name> --api-key=<apy_key>
                                  [--from=folder_name]
                                  [--media=(videos | images | all)]
                                  [--email=email_address]
                                  [--password=password]
  smugline.py download <album_name> --api-key=<apy_key>
                                    [--to=folder_name]
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
  download          downloads an entire album into a folder
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

"""

# pylint: disable=print-statement
from docopt import docopt
from smugpy import SmugMug
import getpass
import hashlib
import os
import re
import json
import requests
import time
from itertools import groupby

# Python 3 vs 2
try:
    from urllib.error import HTTPError
except:
    from urllib2 import HTTPError

__version__ = '0.6.0'

IMG_FILTER = re.compile(r'.+\.(jpg|png|jpeg|tif|tiff|gif)$', re.IGNORECASE)
VIDEO_FILTER = re.compile(r'.+\.(mov|mp4|avi|mts)$', re.IGNORECASE)
ALL_FILTER = re.compile('|'.join([IMG_FILTER.pattern, VIDEO_FILTER.pattern]),
                        re.IGNORECASE)


class SmugLine(object):
    def __init__(self, api_key, email=None, password=None):
        self.api_key = api_key
        self.email = email
        self.password = password
        self.smugmug = SmugMug(
            api_key=api_key,
            api_version="1.2.2",
            app_name="SmugLine")
        self.login()
        self.md5_sums = {}

    def get_filter(self, media_type='images'):
        if media_type == 'videos':
            return VIDEO_FILTER
        if media_type == 'images':
            return IMG_FILTER
        if media_type == 'all':
            return ALL_FILTER

    def upload_file(self, album, image):
        retries = 5
        while retries:
            try:
                self.smugmug.images_upload(AlbumID=album['id'], **image)
                return
            except HTTPError:
                print("retry ", image)
                retries -= 1

    # source: http://stackoverflow.com/a/16696317/305019
    def download_file(self, url, folder, filename=None):
        local_filename = os.path.join(folder, filename or url.split('/')[-1])
        if os.path.exists(local_filename):
            print('{0} already exists...skipping'.format(local_filename))
            return
        r = requests.get(url, stream=True)
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=1024):
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)
                    f.flush()

        return local_filename

    def set_file_timestamp(self, filename, image):
        if filename is None:
            return
        # apply the image date
        image_info = self.get_image_info(image)
        timestamp = time.strptime(image_info['Image']['Date'], '%Y-%m-%d %H:%M:%S')
        t = time.mktime(timestamp)
        os.utime(filename, (t, t))

    def upload_json(self, source_folder, json_file):
        images = json.load(open(json_file))

        # prepend folder
        for image in images:
            image['File'] = source_folder + image['File']

        # group by album
        groups = []
        images.sort(key=lambda x: x['AlbumName'])
        for k, g in groupby(images, key=lambda x: x['AlbumName']):
            groups.append(list(g))

        for group in groups:
            album_name = group[0]['AlbumName']
            album = self.get_or_create_album(album_name)
            self._upload(group, album_name, album)

    def upload_folder(self, source_folder, album_name, file_filter=IMG_FILTER):
        album = self.get_or_create_album(album_name)
        images = self.get_images_from_folder(source_folder, file_filter)
        self._upload(images, album_name, album)

    def download_album(self, album_name, dest_folder, file_filter=IMG_FILTER):
        album = self.get_album_by_name(album_name)
        if album is None:
            print('Album {0} not found'.format(album_name))
            return
        images = self._get_images_for_album(album, file_filter)
        self._download(images, dest_folder)

    def _upload(self, images, album_name, album):
        images = self._remove_duplicates(images, album)
        for image in images:
            print('uploading {0} -> {1}'.format(image, album_name))
            self.upload_file(album, image)

    def _download(self, images, dest_folder):
        for img in images:
            print('downloading {0} -> {1}'.format(img['FileName'], dest_folder))
            if 'OriginalURL' not in img:
                print('no permission to download {0}...skipping'.format(img['FileName']))
                continue
            filename = self.download_file(img['OriginalURL'], dest_folder, img['FileName'])
            self.set_file_timestamp(filename, img)

    def _get_remote_images(self, album, extras=None):
        remote_images = self.smugmug.images_get(
            AlbumID=album['id'],
            AlbumKey=album['Key'],
            Extras=extras)
        return remote_images

    def _get_md5_hashes_for_album(self, album):
        remote_images = self._get_remote_images(album, 'MD5Sum')
        md5_sums = [x['MD5Sum'] for x in remote_images['Album']['Images']]
        self.md5_sums[album['id']] = md5_sums
        return md5_sums

    def _get_images_for_album(self, album, file_filter=IMG_FILTER):
        extras = 'FileName,OriginalURL'
        images = self._get_remote_images(album, extras)['Album']['Images']

        for image in [img for img in images \
                    if file_filter.match(img['FileName'])]:
            yield image

    def _file_md5(self, filename, block_size=2**20):
        md5 = hashlib.md5()
        f = open(filename, 'rb')
        while True:
            data = f.read(block_size)
            if not data:
                break
            md5.update(data)
        return md5.hexdigest()

    def _include_file(self, f, md5_sums):
        try:
            if self._file_md5(f) in md5_sums:
                print('skipping {0} (duplicate)'.format(f))
                return False
            return True
        except IOError as err:
            # see https://github.com/PyCQA/pylint/issues/165
            # pylint: disable=unpacking-non-sequence
            errno, strerror = err
            print('I/O Error({0}): {1}...skipping'.format(errno, strerror))
            return False

    def _remove_duplicates(self, images, album):
        md5_sums = self._get_md5_hashes_for_album(album)
        return [x for x in images if self._include_file(x.get('File'), md5_sums)]

    def get_albums(self):
        albums = self.smugmug.albums_get(NickName=self.nickname)
        return albums

    def list_albums(self):
        print('available albums:')
        for album in self.get_albums()['Albums']:
            if album['Title']:
                print(album['Title'].encode('utf-8'))

    def get_or_create_album(self, album_name):
        album = self.get_album_by_name(album_name)
        if album:
            return album
        return self.create_album(album_name)

    def get_album_by_name(self, album_name):
        albums = self.get_albums()
        try:
            matches = [x for x in albums['Albums'] \
                       if x.get('Title').lower() == album_name.lower()]
            return matches[0]
        except:
            return None

    def _format_album_name(self, album_name):
        return album_name[0].upper() + album_name[1:]

    def get_album_info(self, album):
        return self.smugmug.albums_getInfo(AlbumID=album['id'], AlbumKey=album['Key'])

    def get_image_info(self, image):
        return self.smugmug.images_getInfo(ImageKey=image['Key'])

    def create_album(self, album_name, privacy='unlisted'):
        public = (privacy == 'public')
        album_name = self._format_album_name(album_name)
        album = self.smugmug.albums_create(Title=album_name, Public=public)
        album_info = self.get_album_info(album['Album'])
        print('{0} album {1} created. URL: {2}'.format(
            privacy,
            album_name,
            album_info['Album']['URL']))
        return album_info['Album']

    def get_images_from_folder(self, folder, img_filter=IMG_FILTER):
        matches = []
        for root, dirnames, filenames in os.walk(folder):
            matches.extend(
                {'File': os.path.join(root, name)} for name in filenames \
                if img_filter.match(name))
        return matches

    def _set_email_and_password(self):
        # for python2
        try:
            input = raw_input
        except NameError:
            pass

        if self.email is None:
            self.email = input('Email address: ')
        if self.password is None:
            self.password = getpass.getpass()

    def login(self):
        self._set_email_and_password()
        self.user_info = self.smugmug.login_withPassword(
            EmailAddress=self.email,
            Password=self.password)
        self.nickname = self.user_info['Login']['User']['NickName']
        return self.user_info

    def _delete_image(self, image):
        print('deleting image {0} (md5: {1})'.format(image['FileName'],
                                                    image['MD5Sum']))
        self.smugmug.images_delete(ImageID=image['id'])

    def clear_duplicates(self, album_name):
        album = self.get_album_by_name(album_name)
        remote_images = self._get_remote_images(album, 'MD5Sum,FileName')
        md5_sums = []
        for image in remote_images['Album']['Images']:
            if image['MD5Sum'] in md5_sums:
                self._delete_image(image)
            md5_sums.append(image['MD5Sum'])


if __name__ == '__main__':
    arguments = docopt(__doc__, version='SmugLine 0.4')
    smugline = SmugLine(
        arguments['--api-key'],
        email=arguments['--email'],
        password=arguments['--password'])
    if arguments['upload']:
        file_filter = smugline.get_filter(arguments['--media'])
        smugline.upload_folder(arguments['--from'],
                        arguments['<album_name>'],
                        file_filter)
    if arguments['download']:
        file_filter = smugline.get_filter(arguments['--media'])
        smugline.download_album(arguments['<album_name>'],
                        arguments['--to'],
                        file_filter)
    if arguments['process']:
        smugline.upload_json(arguments['--from'],
                        arguments['<json_file>'])
    if arguments['list']:
        smugline.list_albums()
    if arguments['create']:
        smugline.create_album(arguments['<album_name>'], arguments['--privacy'])
    if arguments['clear_duplicates']:
        smugline.clear_duplicates(arguments['<album_name>'])
