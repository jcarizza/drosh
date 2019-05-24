"""
Listen to new files and create a shared link on Dropbox
"""


import sys
import argparse
import logging
import os
import time
import subprocess

import pyperclip
import inotify.adapters
import dropbox
from dropbox.files import WriteMode
from dropbox.exceptions import ApiError


DROSH_DROPBOX_TOKEN = os.getenv("DROSH_DROPBOX_TOKEN")
DROSH_DROPBOX_FOLDER = os.getenv("DROSH_DROPBOX_FOLDER")
DROSH_SCREENSHOT_FOLDER = os.getenv("DROSH_SCREENSHOT_FOLDER")
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
logger = logging.getLogger(__name__)


class ScreenshotHandler(object):
    def __init__(self, path):
        self.uploader = DropboxUploader()
        file_on_dropbox = self.upload_file(path)
        url = self.create_shared_link(file_on_dropbox)
        if url is None:
            self.notify("Drosh", "Error in create shared link")
        else:
            self.notify("Drosh", url)
            self.url = url

    def get_url(self):
        return self.url

    def notify(self, title, body):
        """
        Send a desktop message
        """
        try:
            subprocess.call(["notify-send", title, body])
        except FileNotFoundError:
            # Try with kdialog
            subprocess.run(["kdialog", "--title", title, "--passivepopup", body, "5"])

    def upload_file(self, path):
        """
        Upload file
        """

        path_local = os.path.join(DROSH_SCREENSHOT_FOLDER, os.path.basename(path))
        path_remote = os.path.join(DROSH_DROPBOX_FOLDER, os.path.basename(path))

        logger.debug("*** DROSH ***: upload %s file to %s", path_local, path_remote)
        if not os.path.exists(path_local):
            logger.error("*** DROSH ***: %s file do not exists", path_local)
            sys.exit(1)

        result = self.uploader.files_upload(path_local, path_remote)
        if result is not None:
            logger.debug("File %r uploaded successfully", result.path_display)

            return result.path_display
        else:
            logger.debug("Error in upload %r file", path_remote)

    def create_shared_link(self, path):
        """
        Create shared link
        """

        result = self.uploader.create_shared_link(path)
        if result is not None:
            logger.debug("Shared link created %r for %r file", result.url, path)
            try:
                pyperclip.copy(result.url)
            except pyperclip.PyperclipException:
                pass
            return result.url
        else:
            logger.debug("Error in create shared link for %r file", path)


class DropboxUploader(object):

    def __init__(self):
        self.client = dropbox.dropbox.Dropbox(DROSH_DROPBOX_TOKEN, timeout=30.0)

    def get_file_size(self, filename):
        if os.path.isfile(filename):
            st = os.stat(filename)
            return st.st_size
        else:
            return -1

    def get_local_file(self, filename, i):
        if i > 6:
            return -1

        file_size = self.get_file_size(filename)

        if file_size > 0:
            return open(filename, "rb")
        else:
            time.sleep(1)  # sometimes file is empty when we try to upload it
            i = i + 1
            return self.get_local_file(filename, i)

    def files_upload(self, path_local, path_remote):
        file_local = self.get_local_file(path_local, 0)
        logger.debug("Uploading %s to Dropbox as %s", path_local, path_remote)

        # We use WriteMode=overwrite to make sure that the settings
        # in the file are changed on upload
        try:
            success = self.client.files_upload(
                file_local.read(),
                path_remote,
                mode=WriteMode("overwrite"),
                autorename=True
            )

            return success
        except ApiError as err:
            if (err.error.is_path() and err.error.get_path().error.is_insufficient_space()):
                sys.exit("ERROR: Cannot back up; insufficient space.")
            elif err.user_message_text:
                logger.error("User messare error %s", err.user_message_text)
                sys.exit()
            else:
                logger.error("Error %r", err)
                sys.exit()

    def check_if_link_is_created(self, path):
        result = self.client.sharing_list_shared_links(path, None, True)

        if not result.links:
            return 0
        else:
            return result.links[0]

    def create_shared_link(self, path):
        for i in range(6):
            try:
                link = self.check_if_link_is_created(path)
                if (link == 0):
                    success = self.client.sharing_create_shared_link_with_settings(
                        path=path, settings=None
                    )
                else:
                    success = link

                return success
            except Exception as e:
                logger.error("Trying %s time: Error to create shared link %r", i, e)
                time.sleep(i * 1.5)


def main():
    """
    Watch for new files where screenshots are saved and create the shared link
    once the file is uploaded by Dropbox client
    """

    i = inotify.adapters.Inotify()
    i.add_watch(DROSH_SCREENSHOT_FOLDER)

    try:
        for event in i.event_gen():
            if event is not None:
                (header, type_names, watch_path, filename) = event

                if "IN_CLOSE_WRITE" in type_names:
                    logger.debug("WD=(%d) MASK=(%d) COOKIE=(%d) LEN=(%d) MASK->NAMES=%s "
                                 "WATCH-PATH=[%s] FILENAME=[%s]",
                                 header.wd, header.mask, header.cookie, header.len, type_names,
                                 watch_path, filename)
                    logger.info("Upload and create shared link for: %r", filename)
                    ScreenshotHandler(filename)

    except Exception as e:
        logger.error('*** DROSH ***: %s', e)
        logger.error('*** DROSH ***: command stop running')
        sys.exit(1)
    finally:
        i.remove_watch(DROSH_SCREENSHOT_FOLDER)


if __name__ == "__main__":

    args = sys.argv
    parser = argparse.ArgumentParser()
    command_group = parser.add_mutually_exclusive_group(required=True)
    command_group.add_argument("--upload",
                               type=str,
                               help="File to upload and create shared link")
    command_group.add_argument("--watch",
                               action="store_true",
                               help="Start to watch directory for files")
    args = parser.parse_args()

    # Setup loggin
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    formatter = logging.Formatter(DEFAULT_LOG_FORMAT)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Upload one time image
    if not args.watch:
        logger.warning("*** DROSH ***: Overwriting DROSH_SCREENSHOT_FOLDER env variable")
        DROSH_SCREENSHOT_FOLDER = ""
        logger.info("*** DROSH ****: Upload file %s", args.upload)
        url = ScreenshotHandler(args.upload).get_url()
        print('\n\nShare this link! \n', url)
        sys.exit(0)

    # Watch for new files on dir
    logger.info("*** DROSH ***: Listen for new files")
    main()
