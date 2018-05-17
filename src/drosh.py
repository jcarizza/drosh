"""
Listen to new files and create a shared link on Dropbox
"""

import sys
import logging
import os
import time
import subprocess
import pyperclip

import inotify.adapters
import dropbox


DROSH_DROPBOX_TOKEN = os.getenv('DROSH_DROPBOX_TOKEN')
DROSH_DROPBOX_FOLDER = os.getenv('DROSH_DROPBOX_FOLDER')
DROSH_SCREENSHOT_FOLDER = os.getenv('DROSH_SCREENSHOT_FOLDER')
DEFAULT_LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
logger = logging.getLogger(__name__)


class Screenshot(object):
    def __init__(self, path):
        url = self.create_shared_link(path)
        if url is None:
            self.notify('Drosh', 'Error al crear link compartido')
        else:
            self.notify('Drosh', url)
            

    def notify(self, title, body):
        """
        Send a desktop message
        """
        try:
            subprocess.call(['notify-send', title, body])
        except FileNotFoundError:
            # Try with kdialog
            subprocess.run(['kdialog', '--title', title, '--passivepopup', body, '5'])

    def create_shared_link(self, path):
        """
        Create shared link using dropbox client
        """

        dbox = Drosh()
        path = os.path.join(DROSH_DROPBOX_FOLDER, os.path.basename(path.decode('utf8'))) 
        result = dbox.create_shared_link(path)
        if result is not None:
            logger.debug('Shared link created %r for %r file', result.url, path)
            pyperclip.copy(result.url)
            return result.url
        else:
            logger.debug('Error in create shared link for %r file', path)


class Drosh(object):

    def __init__(self, folder=DROSH_DROPBOX_FOLDER):
        self.client = dropbox.dropbox.Dropbox(DROSH_DROPBOX_TOKEN, timeout=30.0)

    def create_shared_link(self, path):
        for i in range(6): 
            try:
                success = self.client.sharing_create_shared_link_with_settings(
                    path=path,
                    settings=None
                )
                return success
            except Exception as e:
                logger.error('Trying %s time: Error to create shared link %r', i, e)
                time.sleep(i * 1.5)
        

def main():
    """
    Watch for new files where screenshots are saved and create the shared link
    once the file is uploaded by Dropbox client
    """

    i = inotify.adapters.Inotify()
    i.add_watch(bytes(DROSH_SCREENSHOT_FOLDER.encode('utf8')))

    try:
        for event in i.event_gen():
            if event is not None:
                (header, type_names, watch_path, filename) = event
                if 'IN_CREATE' in type_names:
                    logger.debug("WD=(%d) MASK=(%d) COOKIE=(%d) LEN=(%d) MASK->NAMES=%s "
                                 "WATCH-PATH=[%s] FILENAME=[%s]",
                                 header.wd, header.mask, header.cookie, header.len, type_names,
                                 watch_path.decode('utf-8'), filename.decode('utf-8'))
                    logger.info('Create shared link for: %r', filename)
                    Screenshot(filename)
    finally:
        i.remove_watch(bytes(DROSH_SCREENSHOT_FOLDER.encode('utf8')))


if __name__ == "__main__":

    # Setup loggin
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    formatter = logging.Formatter(DEFAULT_LOG_FORMAT)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    main()
