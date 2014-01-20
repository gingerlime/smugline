#!/usr/bin/env python
"""smugsync

Usage:
  smugsync.py upload <album_name> --api-key=<apy_key>
                                  [--from=folder_name]
                                  [--email=email_address]
                                  [--password=password]
  smugsync.py list --api-key=apy_key
                   [--email=email_address]
                   [--password=password]
  smugsync.py create <album_name> --api-key=apy_key
                                  [--privacy=(unlisted | public)]
                                  [--email=email_address]
                                  [--password=password]
  smugsync.py (-h | --help)

Arguments:
  upload        uploads files to a smugmug album
  list          list album names on smugmug
  create        create a new album

Options:
  --api-key=api_key       your smugmug api key
  --from=folder_name      folder to upload from [default: .]
  --privacy=(unlisted | public)
                          album privacy settings [default: unlisted]
  --email=email_address   email address of your smugmug account
  --passwod=password      smugmug password

"""

from docopt import docopt
from smugpy import SmugMug
import getpass
import hashlib
import os
import re

__version__ = '0.2.1'

IMG_FILTER = re.compile(r'.+\.(jpg|png|jpeg|tif|tiff)$', re.IGNORECASE)


class SmugSync(object):
    def __init__(self, api_key, email=None, password=None):
        self.api_key = api_key
        self.email = email
        self.password = password
        self.smugmug = SmugMug(
            api_key=api_key,
            api_version="1.2.2",
            app_name="SmugSync")
        self.login()
        self.md5_sums = {}

    def upload_file(self, source_file, album):
        album_id = album['id']
        self.smugmug.images_upload(File=source_file, AlbumID=album_id)

    def upload(self, source_folder, album_name):
        album = self.get_or_create_album(album_name)
        images = self.get_images_from_folder(source_folder)
        images = self._remove_duplicates(images, album)
        for image in images:
            print('uploading {0} -> {1}'.format(image, album_name))
            self.upload_file(image, album)

    def _get_md5_hashes_for_album(self, album):
        remote_images = self.smugmug.images_get(
            AlbumID=album['id'],
            AlbumKey=album['Key'],
            Extras='MD5Sum')
        md5_sums = [x['MD5Sum'] for x in remote_images['Album']['Images']]
        self.md5_sums[album['id']] = md5_sums
        return md5_sums

    def _file_md5(self, filename, block_size=2**20):
        md5 = hashlib.md5()
        f = open(filename)
        while True:
            data = f.read(block_size)
            if not data:
                break
            md5.update(data)
        return md5.hexdigest()

    def _include_file(self, f, md5_sums):
        if self._file_md5(f) in md5_sums:
            print('skipping image {0} (duplicate)'.format(f))
            return False
        return True

    def _remove_duplicates(self, images, album):
        md5_sums = self._get_md5_hashes_for_album(album)
        return [x for x in images if self._include_file(x, md5_sums)]

    def get_albums(self):
        albums = self.smugmug.albums_get(NickName=self.nickname)
        return albums

    def list_albums(self):
        print('available albums:')
        for album in self.get_albums()['Albums']:
            if album['Title']:
                print(album['Title'])

    def get_or_create_album(self, album_name):
        album = self.get_album_by_name(album_name)
        if album:
            return album
        return self.create_album(album_name)

    def get_album_by_name(self, album_name):
        albums = self.get_albums()
        try:
            matches = [x for x in albums['Albums'] \
                       if x.get('Title') == album_name]
            return matches[0]
        except:
            return None

    def _format_album_name(self, album_name):
        return album_name[0].upper() + album_name[1:]

    def get_album_info(self, album):
        return self.smugmug.albums_getInfo(AlbumID=album['id'], AlbumKey=album['Key'])

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
                os.path.join(root, name) for name in filenames \
                if img_filter.match(name))
        return matches

    def _set_email_and_password(self):
        if self.email is None:
            self.email = raw_input('Email address: ')
        if self.password is None:
            self.password = getpass.getpass()

    def login(self):
        self._set_email_and_password()
        self.user_info = self.smugmug.login_withPassword(
            EmailAddress=self.email,
            Password=self.password)
        self.nickname = self.user_info['Login']['User']['NickName']
        return self.user_info

if __name__ == '__main__':
    arguments = docopt(__doc__, version='SmugSync 0.2.1')
    smugsync = SmugSync(
        arguments['--api-key'],
        email=arguments['--email'],
        password=arguments['--password'])
    if arguments['upload']:
        smugsync.upload(arguments['--from'], arguments['<album_name>'])
    if arguments['list']:
        smugsync.list_albums()
    if arguments['create']:
        smugsync.create_album(arguments['<album_name>'], arguments['--privacy'])
