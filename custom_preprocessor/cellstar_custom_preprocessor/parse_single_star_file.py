# PLAN
# get x y z coordinates
# read to json with list of objects like:
# { kind: 'sphere', center: [0, 0, 0], radius: 1, color: 0xff0000, label: 'S1' }


import json
from typing import TypedDict
import starfile
from pathlib import Path

from custom_preprocessor.cellstar_custom_preprocessor.models import Sphere

# from custom_preprocessor.models import Sphere

STAR_FILE_PATH = Path('preprocessor/temp/pdbe_dataset_scripts/80S_bin1_cryoDRGN-ET_clean_tomo_9.star')
JSON_PATH = Path('preprocessor/temp/shape_primitives/shape_primitives_9rec_input.json')

RATIO = 4
# RATIO = 400 * 5

def parse_single_star_file(path: Path, sphere_radius: float, sphere_color: int) -> list[Sphere]:
    lst = []
    df = starfile.read(str(path.resolve()))
    for index, row in df.iterrows():
        micrograph_name = row['rlnTomoName'].split('_')
        label = micrograph_name[3] + '-' + micrograph_name[4].split('.')[0]
        # radius = 0.08 * 200
        radius = sphere_radius

        #     # yellow
        # color = '0xffff00'
        # TODO: convert color to string
        # 16776960 int
        # color = hex(sphere_color)
        color = sphere_color

        lst.append(
            Sphere(
                id=index,
                center=(row['rlnCoordinateX']/RATIO, row['rlnCoordinateY']/RATIO, row['rlnCoordinateZ']/RATIO),
                color=color,
                radius=radius,
                label=label
            )
            # {
            #     "kind": "sphere",
            #     "parameters": {
            #         "segment_id": index,
            #         "center": (row['rlnCoordinateX']/RATIO, row['rlnCoordinateY']/RATIO, row['rlnCoordinateZ']/RATIO),
            #         "color": color,
            #         "radius": radius
            #     }
            # }
        )
    return {
        'shape_primitive_list': lst
        }


# if __name__ == '__main__':
#     lst = parse_star_file(STAR_FILE_PATH)

#     with (JSON_PATH).open('w') as fp:
#         json.dump(lst, fp, indent=4)