# Instead of db store etc. there should be 
# a number of methods to store the data

# QUESTION: what is the role of db (FileSystemVolumeServerDB) then?
# What methods should be left there?
# only those that provide access to data?

from argparse import ArgumentError
from pathlib import Path
from typing import Literal
from cellstar_db.file_system.constants import LATTICE_SEGMENTATION_DATA_GROUPNAME, MESH_SEGMENTATION_DATA_GROUPNAME
from cellstar_db.protocol import VolumeServerDB
import zarr

class VolumeAndSegmentationContext:
    def __init__(self, db: VolumeServerDB, namespace: str, key: str, intermediate_zarr_structure: Path):
        self.intermediate_zarr_structure = intermediate_zarr_structure
        self.db = db
        self.path = db.path_to_zarr_root_data(namespace=namespace, key=key)
        assert self.path.exists(), f"Path {self.path} does not exist"
        self.key = key
        self.namespace = namespace
        # if self.db.store_type == "directory":
        #     self.store = zarr.DirectoryStore(path=self.path)
        # elif self.db.store_type == "zip":
        #     self.store = zarr.ZipStore(
        #         path=self.path, compression=0, allowZip64=True, mode="w"
        #     )

        if self.db.store_type == "directory":
            perm_store = zarr.DirectoryStore(str(self.db._path_to_object(namespace, key)))
            self.store = perm_store
        elif self.db.store_type == "zip":
            entry_dir_path = self.db._path_to_object(namespace, key)
            entry_dir_path.mkdir(parents=True, exist_ok=True)
            perm_store = zarr.ZipStore(
                path=str(self.db.path_to_zarr_root_data(namespace, key)),
                compression=0,
                allowZip64=True,
                mode="w",
            )
            self.store = perm_store
        else:
            raise ArgumentError("store type is wrong: {self.store_type}")

    # possibly async?
    # add* methods do something like db.store()
    # TODO: get temp store path from somewhere
    def add_volume():
        pass

    def add_segmentation(self, id: str, kind: Literal["lattice", "mesh", "primitive"]):
        temp_store = zarr.DirectoryStore(
                str(self.intermediate_zarr_structure)
            )
        perm_root = zarr.group(self.store)
        if kind == 'lattice':
            source_path = f'{LATTICE_SEGMENTATION_DATA_GROUPNAME}/{id}'
            
            if LATTICE_SEGMENTATION_DATA_GROUPNAME not in perm_root:
                perm_root.create_group(LATTICE_SEGMENTATION_DATA_GROUPNAME)
            
            zarr.copy_store(source=temp_store, dest=self.store, source_path=source_path, dest_path=source_path)    
            
        elif kind == 'mesh':
            source_path = f'{MESH_SEGMENTATION_DATA_GROUPNAME}/{id}'
            
            if MESH_SEGMENTATION_DATA_GROUPNAME not in perm_root:
                perm_root.create_group(MESH_SEGMENTATION_DATA_GROUPNAME)
            
            zarr.copy_store(source=temp_store, dest=self.store, source_path=source_path, dest_path=source_path)    
            
        elif kind == 'primitive':
            pass
            # add to JSON
        
        # close if zip
        if self.db.store_type == "zip":
            self.store.close()
            

        print('Segmentation added')
            

    def remove_volume():
        pass

    def remove_segmentation():
        pass
    

    def close(self):
        if hasattr(self.store, "close"):
            self.store.close()
        else:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if hasattr(self.store, "close"):
            self.store.close()
        else:
            pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args, **kwargs):
        if hasattr(self.store, "aclose"):
            await self.store.aclose()
        if hasattr(self.store, "close"):
            self.store.close()
        else:
            pass

    # TODO: at the end remove temp store
                # can be atexit
        # temp_store.rmdir()