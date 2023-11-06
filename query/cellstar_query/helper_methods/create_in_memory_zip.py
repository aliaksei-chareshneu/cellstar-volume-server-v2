import io
import json
from typing import Union
from zipfile import ZIP_DEFLATED, ZipFile


# zip with bytes in memory
def create_in_memory_zip(files_data: list[tuple[str, Union[bytes, dict]]]) -> bytes:

    file = io.BytesIO()
    with ZipFile(file, 'w', ZIP_DEFLATED) as zip_file:
        # for name, content in [
        #     ('file.dat', b'data'), ('another_file.dat', b'more data')
        # ]:
        for name, content in files_data:
            if isinstance(content, bytes):
                zip_file.writestr(name, content)
            elif isinstance(content, dict):
                dumped_JSON: str = json.dumps(content, ensure_ascii=False, indent=4)
                zip_file.writestr(name, data=dumped_JSON)

    zip_data = file.getvalue()
    # print(zip_data)
    return zip_data


# write to file
# def write_zip_bytes_to_zip_file(zip_data: bytes):
#     with open("my_zip.zip", "wb") as f: # use `wb` mode
#         f.write(zip_data)