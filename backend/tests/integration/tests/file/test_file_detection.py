# from danswer.file_store.models import FileOrigin
# from danswer.file_store.models import FileDescriptor
# from danswer.file_store.models import ChatFileType
from tests.integration.common_utils.managers.file import FileManager

# from danswer.file_store.models import FileType


def test_file_detection():
    import tempfile
    from reportlab.pdfgen import canvas

    # Create a temporary PDF file
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
        pdf_path = temp_file.name
        c = canvas.Canvas(pdf_path)
        c.drawString(100, 750, "This is a test PDF file.")
        c.save()

    pdf_file = open(pdf_path, "rb")
    test_file = FileManager.upload_files([pdf_file])

    # assert test_file[0].file_type == FileType.PDF

    FileManager.fetch_query_file(test_file[0].id)
    # assert recieved_file.file_type == FileType.PDF
