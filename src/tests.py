import unittest
import os
from tempfile import NamedTemporaryFile
from unittest.mock import patch


from drosh import ScreenshotHandler


class TestScreenshotHandler(unittest.TestCase):

    @patch("drosh.ScreenshotHandler.notify")
    @patch("drosh.ScreenshotHandler.upload_file")
    @patch("drosh.ScreenshotHandler.create_shared_link")
    def test_screenshot_calls(self, create_shared_link, upload_file, notify):
        """Test essential methods.

        This class should call three methods one time.
        """
        tmp_file = NamedTemporaryFile()
        ScreenshotHandler(tmp_file)
        upload_file.assert_called_once()
        create_shared_link.assert_called_once()
        notify.assert_called_once()

    @patch("drosh.ScreenshotHandler.notify")
    @patch("drosh.DropboxUploader.files_upload")
    @patch("drosh.DropboxUploader.create_shared_link")
    def test_dropbox_uploader_methods(self, create_shared_link, files_upload, notify):
        """Test uploader.

        When instantiated an screanshot handler should
        use the uploader to create link and upload the file"""

        with NamedTemporaryFile() as f:
            url = "https://example.com/image"
            name = os.path.basename(f.name)
            upload_response = type("result", (object, ), dict(path_display=name))()
            link_response = type("result", (object, ), dict(url=url))()
            files_upload.return_value = upload_response
            create_shared_link.return_value = link_response

            ScreenshotHandler(f.name)
            arg1 = os.path.join(os.getenv("DROSH_SCREENSHOT_FOLDER"), name)
            arg2 = os.path.join(os.getenv("DROSH_DROPBOX_FOLDER"), name)
            files_upload.assert_called_once_with(arg1, arg2)
            create_shared_link.assert_called_once_with(name)
            notify.assert_called_once_with("Drosh", url)
