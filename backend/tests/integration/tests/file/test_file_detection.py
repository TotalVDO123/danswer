import tempfile

from tests.integration.common_utils.managers.file import FileManager
from tests.integration.common_utils.managers.user import UserManager
from tests.integration.common_utils.test_models import DATestUser


def test_file_detection(reset: None) -> None:
    admin_user: DATestUser = UserManager.create(name="admin_user")

    test_content = "This is a test text file."
    with tempfile.NamedTemporaryFile(
        suffix=".txt", delete=False, mode="w"
    ) as temp_file:
        temp_file.write(test_content)
        txt_path = temp_file.name

    with open(txt_path, "rb") as txt_file:
        test_files = FileManager.upload_files([("test.txt", txt_file)], admin_user)

    uploaded_file = test_files[0][0]
    assert uploaded_file["name"] == "test.txt"
    assert uploaded_file["type"] == "plain_text"

    file_content = FileManager.fetch_uploaded_file(uploaded_file["id"], admin_user)
    assert file_content == test_content.encode()

    import os

    os.unlink(txt_path)
