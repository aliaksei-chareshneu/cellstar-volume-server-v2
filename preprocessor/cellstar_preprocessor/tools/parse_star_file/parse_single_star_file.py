# PLAN
# get x y z coordinates
# read to json with list of objects like:
# { kind: 'sphere', center: [0, 0, 0], radius: 1, color: 0xff0000, label: 'S1' }


import argparse
import json
from typing import TypedDict
from cellstar_db.models import GeometricSegmentationInputData, ShapePrimitiveInputData, ShapePrimitiveKind, SphereInputParams
import starfile
from pathlib import Path

STAR_FILE_PATH = Path('preprocessor/temp/pdbe_dataset_scripts/80S_bin1_cryoDRGN-ET_clean_tomo_9.star')
JSON_PATH = Path('preprocessor/temp/shape_primitives/shape_primitives_9rec_input.json')

def hex_to_rgba(hex_code):
  """
  Converts a hex color code to a tuple representing RGBA values.

  Args:
      hex_code: A string representing a hex color code (e.g., "#FFFFFF", "FF0000").

  Returns:
      A tuple containing the red, green, blue, and alpha values (0-255) of the hex color.

  Raises:
      ValueError: If the provided hex code is invalid.
  """
  if not isinstance(hex_code, str):
    raise ValueError("Input must be a string")

  # Remove the '#' symbol if present
  hex_code = hex_code.lstrip('#')

  # Check for valid hex code length
  if len(hex_code) not in (3, 6):
    raise ValueError("Invalid hex code length (must be 3 or 6 characters)")

  # Convert each hex digit to integer (0-15)
  rgb_values = tuple(int(hex_code[i:i+2], 16) for i in range(0, len(hex_code), 2))

  # If the hex code has 3 digits, replicate them for each channel (e.g., #FFF becomes #FFFFFF)
  if len(hex_code) == 3:
    rgb_values = rgb_values * 4

  # Add alpha channel (default to 255 for full opacity)
  return rgb_values + (255,)

# TODO: use rln_ribosome_bin1_tomo_649.star

# divisor = 4
def parse_single_star_file(path: Path, sphere_radius: float, sphere_color: list[float], pixel_size: float, star_file_coordinate_divisor: int, segmentation_id: str):
    lst: list[ShapePrimitiveInputData] = []
    df = starfile.read(str(path.resolve()))
    for index, row in df.iterrows():
        # micrograph_name = row['rlnTomoName'].split('_')
        label = row['rlnTomoName']
        # radius = 0.08 * 200
        radius = sphere_radius
        color = sphere_color

        sp_input_data = ShapePrimitiveInputData(
            kind=ShapePrimitiveKind.sphere,
            parameters=SphereInputParams(
                id=index,
                # kind=ShapePrimitiveKind.sphere,
                center=(
                    row['rlnCoordinateX']/star_file_coordinate_divisor * pixel_size,
                    row['rlnCoordinateY']/star_file_coordinate_divisor * pixel_size,
                    row['rlnCoordinateZ']/star_file_coordinate_divisor * pixel_size
                    ),
                color=color,
                radius=radius,
            )
        )
        
        lst.append(sp_input_data)
    d = {
            0: lst
        }
    geometric_segmentation_input = GeometricSegmentationInputData(
        segmentation_id=segmentation_id,
        shape_primitives_input=d
    )
    
    return geometric_segmentation_input

def parse_script_args():
    parser=argparse.ArgumentParser()
    parser.add_argument('--star_file_path', type=str, help='')
    parser.add_argument('--geometric_segmentation_input_file_path', type=str, help='')
    parser.add_argument('--sphere_radius', type=float)
    parser.add_argument('--segmentation_id', type=str)
    # TODO: color as hex? => transform to list float
    parser.add_argument('--sphere_color_hex', type=str)
    parser.add_argument('--pixel_size', type=float)
    parser.add_argument('--star_file_coordinate_divisor', type=int, default=4 )
    args=parser.parse_args()
    return args

def main(args: argparse.Namespace):
    star_file_path = Path(args.star_file_path)
    sphere_radius = args.sphere_radius
    sphere_color_hex: str = args.sphere_color_hex
    pixel_size = args.pixel_size
    star_file_coordinate_divisor = args.star_file_coordinate_divisor
    geometric_segmentation_input_file_path = Path(args.geometric_segmentation_input_file_path)
    
    sphere_color = hex_to_rgba(sphere_color_hex)
    
    lst = parse_single_star_file(
        path=star_file_path,
        sphere_radius=sphere_radius,
        sphere_color=sphere_color,
        pixel_size=pixel_size,
        star_file_coordinate_divisor=star_file_coordinate_divisor,
        segmentation_id=args.segmentation_id
    )  
    with (geometric_segmentation_input_file_path).open('w') as fp:
        json.dump(lst.dict(), fp, indent=4)

if __name__ == '__main__':
    # lst = parse_single_star_file(STAR_FILE_PATH, 16, 16776960, 7.84, 4)
    args = parse_script_args()
    main(args)
    