from enum import Enum
from typing import Dict, List, Optional, Protocol, TypedDict, Union

import numpy as np

class Sphere(TypedDict):
    id: int
    center: tuple[float, float, float]
    # in grid pofloats
    radius: float
    label: str
    color: int