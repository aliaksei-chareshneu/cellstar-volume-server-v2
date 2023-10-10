from dataclasses import dataclass
from typing import Union

import numpy as np

from custom_preprocessor.models import Sphere


@dataclass
class SpheresContext(object):
    center_x: np.ndarray
    center_y: np.ndarray
    center_z: np.ndarray
    id: np.ndarray
    radius: np.ndarray
    color: np.ndarray
    label: np.ndarray

    @staticmethod
    def from_list_of_sphere_objects(l: list[Sphere]):
        """Create `SegmentSetTable` from dict where keys are set ids, values are lists of segments ids."""
        # set_ids = []
        # segment_ids = []
        # for k in set_dict.keys():
        #     for v in set_dict[k]:
        #         set_ids.append(int(k))
        #         segment_ids.append(v)
        # return SegmentSetTable(set_ids, segment_ids, len(set_ids))
        # return ParticlesData(id=s['id'], center=s['center'], radius=s['radius'], color=s['color'], label=s['label'])
        centers_x = []
        centers_y = []
        centers_z = []
        ids = []
        radii = []
        colors = []
        labels = []
        for s in l:
            centers_x.append(s['center'][0])
            centers_y.append(s['center'][1])
            centers_z.append(s['center'][2])
            ids.append(s['id'])
            radii.append(s['radius'])
            colors.append(s['color'])
            labels.append(s['label'])

        return SpheresContext(
            center_x=np.asarray(centers_x),
            center_y=np.asarray(centers_y),
            center_z=np.asarray(centers_z),
            id=np.asarray(ids),
            radius=np.asarray(radii),
            color=np.asarray(colors),
            label=np.asarray(labels)
        )