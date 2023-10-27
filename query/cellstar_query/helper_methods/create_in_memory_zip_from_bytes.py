import io
from zipfile import ZIP_DEFLATED, ZipFile


# zip with bytes in memory
def create_in_memory_zip_from_bytes(files_data: list[tuple[str, bytes]]) -> bytes:

    file = io.BytesIO()
    with ZipFile(file, 'w', ZIP_DEFLATED) as zip_file:
        # for name, content in [
        #     ('file.dat', b'data'), ('another_file.dat', b'more data')
        # ]:
        for name, content in files_data:
            zip_file.writestr(name, content)

    zip_data = file.getvalue()
    # print(zip_data)
    return zip_data


# write to file
# def write_zip_bytes_to_zip_file(zip_data: bytes):
#     with open("my_zip.zip", "wb") as f: # use `wb` mode
#         f.write(zip_data)