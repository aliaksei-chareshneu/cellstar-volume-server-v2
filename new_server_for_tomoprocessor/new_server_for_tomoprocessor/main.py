from cellstar_db.file_system.db import FileSystemVolumeServerDB
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

import new_server_for_tomoprocessor.app.api.v1 as api_v1
import new_server_for_tomoprocessor.app.api.v2 as api_v2
from cellstar_query.core.service import VolumeServerService
from new_server_for_tomoprocessor.app.settings import settings

print("Server Settings: ", settings.dict())

description = f'''
GIT TAG: {settings.GIT_TAG}
GIT SHA: {settings.GIT_SHA}
'''

app = FastAPI(description=description)

# origins = [
#     "http://localhost",
#     "http://localhost:9000",
# ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000, compresslevel=3)  # Default compresslevel=9 is veeery slow

# initialize dependencies
db = FileSystemVolumeServerDB(folder=settings.DB_PATH)

# initialize server
volume_server = VolumeServerService(db)

api_v1.configure_endpoints(app, volume_server)
api_v2.configure_endpoints(app, volume_server)
