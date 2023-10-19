from ciftools.models.writer import CIFCategoryDesc
from ciftools.models.writer import CIFFieldDesc as Field

from new_server_for_tomoprocessor.app.serialization.data.volume_info import VolumeInfo
from new_server_for_tomoprocessor.app.serialization.volume_cif_categories import encoders


class VolumeDataTimeAndChannelInfo(CIFCategoryDesc):
    name = "volume_data_time_and_channel_info"

    @staticmethod
    def get_row_count(_) -> int:
        return 1

    @staticmethod
    def get_field_descriptors(ctx: VolumeInfo):
        byte_array = encoders.bytearray_encoder
        return [
            # do we need time_id or actual time (with ms) here?
            Field.numbers(name="time_id", value=lambda d, i: ctx.time, encoder=byte_array, dtype="i4"),
            Field.numbers(name="channel_id", value=lambda d, i: ctx.time, encoder=byte_array, dtype="i4"), 
        ]
