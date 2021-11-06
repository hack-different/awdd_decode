import io
import struct
from typing import *
from enum import IntFlag

BYTE_PARSE_STRUCT = b'B'


class TagType(IntFlag):
    NONE = 0b000
    LENGTH_PREFIX = 0b010
    REPEATED = 0b100


class Tag(NamedTuple):
    index: int
    tag_type: TagType
    length: int
    value: any


class VariableLengthInteger(NamedTuple):
    value: int
    size: int


def decode_variable_length_int(reader: Union[BinaryIO, io.BytesIO]) -> Optional[VariableLengthInteger]:
    def read_bytes() -> Generator[int, None, None]:
        data = reader.read(struct.calcsize(BYTE_PARSE_STRUCT))
        if data is None:
            return

        byte, *_ = struct.unpack(BYTE_PARSE_STRUCT, data)

        while byte & 0b1000_0000 != 0:
            yield byte & 0b0111_1111
            byte, *_ = struct.unpack(BYTE_PARSE_STRUCT, reader.read(struct.calcsize(BYTE_PARSE_STRUCT)))

        yield byte

    result = 0

    result_bytes = list(read_bytes())
    if len(result_bytes) == 0:
        return None

    for single_byte in reversed(result_bytes):
        result <<= 7
        result |= single_byte

    return VariableLengthInteger(value=result, size=len(result_bytes))


"""
Reads in a single tag and it's associated data.  If the low order bits indicate that there is a length
prefix (as is in the case of strings and constructed object types).  For scalar primitives, the high order
bit of the value indicates if there are more bytes to be read.  Finally the remaining 7 bits are 7 to 8 bit
encoded as in email 7bit encoding (MIME)  
"""


def decode_tag(reader: io.IOBase) -> Optional[Tag]:
    result = decode_variable_length_int(reader)
    if result is None:
        return None

    encoded_tag, length = result

    type_bits = encoded_tag & 0b111
    index_bits = encoded_tag >> 3

    if type_bits == TagType.STRING:
        string_length, length_length = decode_variable_length_int(reader)
        value = reader.read(string_length)
        return Tag(index=index_bits, tag_type=TagType(type_bits), length=length + length_length + string_length,
                   value=value)

    elif type_bits == TagType.INTEGER:
        value, value_length = decode_variable_length_int(reader)

        return Tag(index=index_bits, tag_type=TagType(type_bits), length=length + value_length, value=value)

    else:
        Exception('Unknown tag type')


class Parser:
    def __init__(self):
        pass

    def parse(self) -> Generator[Tag, None, None]:
        pass