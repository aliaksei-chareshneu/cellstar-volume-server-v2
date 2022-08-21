from typing import Callable, Optional, Union

import numpy as np
from src.ciftools.ciftools.binary.encoding.impl.binary_cif_encoder import BinaryCIFEncoder
from src.ciftools.ciftools.cif_format import ValuePresenceEnum
from src.ciftools.ciftools.writer.base import FieldDesc
from src.ciftools.ciftools.writer.fields import number_field


def number_field_volume3d(
    *,
    name: str,
    value: Callable[[np.ndarray, int], Optional[Union[int, float]]],
    dtype: np.dtype,
    encoder: Callable[[np.ndarray], BinaryCIFEncoder],
    presence: Optional[Callable[[np.ndarray, int], Optional[ValuePresenceEnum]]] = None,
) -> FieldDesc:
    return number_field(name=name, value=value, dtype=dtype, encoder=encoder, presence=presence)

class Fields_VolumeData3d:
    def _value(self, volume: np.ndarray, index: int):
        return volume[index]

    def __init__(self, encoder: BinaryCIFEncoder, dtype: np.dtype):
        self.fields: list[FieldDesc] = [
            number_field_volume3d(name="values", value=self._value, encoder=lambda _: encoder, dtype=dtype)
        ]