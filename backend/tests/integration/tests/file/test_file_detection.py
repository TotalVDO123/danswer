# from danswer.file_store.models import FileOrigin
# from danswer.file_store.models import FileDescriptor
# from danswer.file_store.models import ChatFileType
from tests.integration.common_utils.managers.file import FileManager
from tests.integration.common_utils.managers.user import UserManager
from tests.integration.common_utils.test_models import DATestUser

# from danswer.file_store.models import FileType


def test_file_detection() -> None:
    import tempfile

    from reportlab.pdfgen import canvas

    admin_user: DATestUser = UserManager.create(name="aadmasadaasfasdfin_uqser")

    # Create a temporary PDF file
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
        pdf_path = temp_file.name
        c = canvas.Canvas(pdf_path)
        c.drawString(100, 750, "This is a test PDF file.")
        c.save()

    with open(pdf_path, "rb") as pdf_file:
        test_files = FileManager.upload_files([("test.pdf", pdf_file)], admin_user)

    # assert test_file[0].file_type == FileType.PDF
    print(test_files[0])
    print(type(test_files[0]))
    FileManager.fetch_query_file(test_files[0].id)
    # assert recieved_file.file_type == FileType.PDF
