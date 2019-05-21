import unittest
from tempfile import NamedTemporaryFile
from unittest.mock import patch


from drosh import Screenshot


class TestScreenshot(unittest.TestCase):

    @patch('drosh.Screenshot.notify')
    @patch('drosh.Screenshot.upload_file')
    @patch('drosh.Screenshot.create_shared_link')
    def test_screenshot_calls(self, notify, upload_file, create_shared_link):
        tmp_file = NamedTemporaryFile()
        screenshot = Screenshot(tmp_file)
        upload_file.assert_called_once()
        create_shared_link.assert_called_once()
        notify.assert_called_once()


# TODO:
#  - Esta observando por cambios de archivos en la carpeta
#  - dbox.upload_file retorna archivo
#  - dbox.create_shared_link crea el link
#  - se llama a notify
