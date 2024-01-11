from uuid import uuid4
from cellstar_db.file_system.constants import ANNOTATION_METADATA_FILENAME
from cellstar_db.protocol import VolumeServerDB
from cellstar_db.models import DescriptionData, EntryId, SegmentAnnotationData
from cellstar_preprocessor.flows.common import save_dict_to_json_file

class AnnnotationsEditContext:
    async def remove_descriptions(self, ids: list[str]):
        # 1. read annotations.json file using existing read_annotations function to AnnotationsMetadata TypedDict in d variable
        d = await self.db.read_annotations(namespace=self.namespace, key=self.key)
        # 2. for id in ids, if id exists in annotations.description.keys()
        for id in ids:
            if id in d["descriptions"].keys():
        # 3. remove that key from d variable
                del d["descriptions"][id]
        # 4. write d back to annotations.json
        path = self.db._path_to_object(namespace=self.namespace, key=self.key)
        save_dict_to_json_file(d, ANNOTATION_METADATA_FILENAME, path)
        
        
    async def add_or_modify_descriptions(self, xs: list[DescriptionData]):
        # 1. read annotations.json file using existing read_annotations function to AnnotationsMetadata TypedDict in d variable
        d = await self.db.read_annotations(namespace=self.namespace, key=self.key)
        # 2. loop over xs:
        for x in xs:
        # 2. if 'id' in x:    
            if 'id' in x.keys():
                descr_id = x['id']
            else:
                descr_id = str(uuid4())

            if descr_id in d['description'].keys():
                # loop over each field in x except external_references and replace the fields with the same name in d['description'][descr_id]
                for field_name in x.keys():
                    if field_name != 'external_references':
                        d['description'][descr_id][field_name] = x[field_name]
                    else:
                    # or add if id does not exist
                        for ref in x['external_references']:
                            if 'id' not in ref:
                                ref['id'] = str(uuid4())

                            for index, existing_ref in enumerate(d['description'][descr_id][field_name]):
                                if existing_ref['id'] == ref['id']:
                                    d['description'][descr_id][field_name].pop(index)
                                # does not exist or exists - push anyway
                                d['description'][descr_id][field_name].append(ref)

            # id does not exist, add description
            else:
                d['description'][descr_id] = x
        # 4. write d back to annotations.json
        path = self.db._path_to_object(namespace=self.namespace, key=self.key)
        save_dict_to_json_file(d, ANNOTATION_METADATA_FILENAME, path)

    async def remove_segment_annotations(self, ids: list[str]):
        '''
        Removes (segment) annotations by annotation ids.
        '''
         # 1. read annotations.json file using existing read_annotations function to AnnotationsMetadata TypedDict in d variable
        d = await self.db.read_annotations(namespace=self.namespace, key=self.key)
        # filter annotations list to leave only those which id is not in ids
        old_annotations_list: list[SegmentAnnotationData] = d['annotations']
        new_annotations_list = list(filter(lambda a: a['id'] not in ids, old_annotations_list))
        d['annotations'] = new_annotations_list
        path = self.db._path_to_object(namespace=self.namespace, key=self.key)
        save_dict_to_json_file(d, ANNOTATION_METADATA_FILENAME, path)

    async def add_or_modify_segment_annotations(self, xs: list[SegmentAnnotationData]):
        # 1. read annotations.json file using existing read_annotations function to AnnotationsMetadata TypedDict in d variable
        d = await self.db.read_annotations(namespace=self.namespace, key=self.key)
        # 2. loop over xs:
        for x in xs:
        # 2. if 'id' in x:    
            if 'id' in x.keys():
                annotation_id = x['id']
            else:
                annotation_id = str(uuid4())
            # id exists, replacing annotation    
            if any(a['id'] == annotation_id for a in d['annotations']):
                for idx, item in enumerate(d['annotations']):
                    if item['id'] == annotation_id:
                        # do stuff on item
                        for field_name in x.keys():
                            item[field_name] = x[field_name]

                        d['annotations'][idx] = item

                    
                # # for each field in x, replace that field in existing_annotation
 
                # # loop over each field in x and replace the fields with the same name in d['description'][descr_id]
                # for field_name in x.keys():
                #     target_annotation_item[field_name] = x[field_name]





                #     # filter_results = [(index, g) for index, g in enumerate(d) if g["segmentation_id"] == id]
                #     # # filter_results = list(filter(lambda g: g["segmentation_id"] == id, d))
                #     # assert len(filter_results) == 1
                #     # target_index = filter_results[0][0]
                #     # # instead of append, remove it
                #     # # d.append(target_geometric_segmentation)
                #     # d.pop(target_index)


                #     # d['annotations'][annotation_id][field_name] = x[field_name]
                
                print(f'Annotation with id {annotation_id} was modified')
            # id does not exist, add annotation
            else:
                d['annotations'].append(x)
                print(f'Annotation with id {annotation_id} was added')

                    # if field_name != 'external_references':
                    #     d['description'][annotation_id][field_name] = x[field_name]
                    # else:
                    # # or add if id does not exist
                    #     for ref in x['external_references']:
                    #         if 'id' not in ref:
                    #             ref['id'] = str(uuid4())

                    #         for index, existing_ref in enumerate(d['description'][annotation_id][field_name]):
                    #             if existing_ref['id'] == ref['id']:
                    #                 d['description'][annotation_id][field_name].pop(index)
                    #             # does not exist or exists - push anyway
                    #             d['description'][annotation_id][field_name].append(ref)
        path = self.db._path_to_object(namespace=self.namespace, key=self.key)
        save_dict_to_json_file(d, ANNOTATION_METADATA_FILENAME, path)
    
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # if hasattr(self.store, "close"):
        #     self.store.close()
        # else:
        #     pass
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args, **kwargs):
        # if hasattr(self.store, "aclose"):
        #     await self.store.aclose()
        # if hasattr(self.store, "close"):
        #     self.store.close()
        # else:
        #     pass
        pass

    def __init__(self, db: VolumeServerDB, namespace: str, key: str):
        self.db = db
        self.namespace = namespace
        self.key = key
        self.path = db.path_to_zarr_root_data(namespace=self.namespace, key=self.key)
        assert self.path.exists(), f"Path {self.path} does not exist"
        # if self.db.store_type == "directory":
        #     self.store = zarr.DirectoryStore(path=self.path)
        # elif self.db.store_type == "zip":
        #     self.store = zarr.ZipStore(
        #         path=self.path, compression=0, allowZip64=True, mode="r"
        #     )