# Copyright (C) 2018  Chris Lalancette <clalancette@gmail.com>

# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation;
# version 2.1 of the License.

# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

'''
Classes to support UDF.
'''

from __future__ import absolute_import

import random
import struct
import time

import pycdlib.pycdlibexception as pycdlibexception
import pycdlib.utils as utils

POLYNOMIAL = 0x11021


def _initial(c):
    '''
    An internal function to generate the initial table for the CRC CCITT
    algorithm.

    Parameters:
     c - The value of this entry in the table, which also happens to be the
         offset into the table.
    Returns:
     The crc value for this entry in the table.
    '''
    crc = 0
    c = c << 8
    for j_unused in range(8):
        if (crc ^ c) & 0x8000:
            crc = (crc << 1) ^ POLYNOMIAL
        else:
            crc = crc << 1
        c = c << 1
    return crc


_tab = [_initial(i) for i in range(256)]


def _update_crc(crc, c):
    '''
    An internal function to update the CRC passed in 'crc' with the additional
    byte 'c' passed in.

    Parameters:
     crc - The original CRC value.
     c - The additional value to add to the CRC.
    Returns:
     The new value of the the CRC.
    '''
    cc = 0xff & c

    tmp = (crc >> 8) ^ cc
    crc = (crc << 8) ^ _tab[tmp & 0xff]
    crc = crc & 0xffff

    return crc


def crc_ccitt(data):
    '''
    Calculate the CRC over a range of bytes using the CCITT polynomial.

    Parameters:
     data - The array of bytes to calculate the CRC over.
    Returns:
     The CCITT CRC of the data.
    '''
    def identity(x):
        '''
        The identity function so we can use a function for python2/3
        compatibility.
        '''
        return x

    if isinstance(data, str):
        myord = ord
    elif isinstance(data, bytes):
        myord = identity
    crc = 0
    for c in data:
        crc = _update_crc(crc, myord(c))
    return crc


class BEAVolumeStructure(object):
    '''
    A class representing a UDF Beginning Extended Area Volume Structure.
    '''
    __slots__ = ['_initialized', 'orig_extent_loc', 'new_extent_loc']

    FMT = "=B5sB2041s"

    def __init__(self):
        self._initialized = False

    def parse(self, data, extent):
        '''
        Parse the passed in data into a UDF BEA Volume Structure.

        Parameters:
         data - The data to parse.
         extent - The extent that this descriptor currently lives at.
        Returns:
         Nothing.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("BEA Volume Structure already initialized")

        (structure_type, standard_ident, structure_version,
         reserved_unused) = struct.unpack_from(self.FMT, data, 0)

        if structure_type != 0:
            raise pycdlibexception.PyCdlibInvalidISO("Invalid structure type")

        if standard_ident != b'BEA01':
            raise pycdlibexception.PyCdlibInvalidISO("Invalid standard identifier")

        if structure_version != 1:
            raise pycdlibexception.PyCdlibInvalidISO("Invalid structure version")

        self.orig_extent_loc = extent
        self.new_extent_loc = None

        self._initialized = True

    def record(self):
        '''
        A method to generate the string representing this UDF BEA Volume
        Structure.

        Parameters:
         None.
        Returns:
         A string representing this UDF BEA Volume Strucutre.
        '''
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("BEA Volume Structure not initialized")
        return struct.pack(self.FMT, 0, b'BEA01', 1, b'\x00' * 2041)

    def new(self):
        '''
        A method to create a new UDF BEA Volume Structure.

        Parameters:
         None.
        Returns:
         Nothing.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("BEA Volume Structure already initialized")

        self._initialized = True

    def extent_location(self):
        '''
        A method to get the extent location of this UDF BEA Volume Structure.

        Parameters:
         None.
        Returns:
         Integer extent location of this UDF BEA Volume Structure.
        '''
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF BEA Volume Structure not yet initialized")

        if self.new_extent_loc is None:
            return self.orig_extent_loc
        return self.new_extent_loc


class NSRVolumeStructure(object):
    '''
    A class representing a UDF NSR Volume Structure.
    '''
    __slots__ = ['_initialized', 'orig_extent_loc', 'new_extent_loc']

    FMT = "=B5sB2041s"

    def __init__(self):
        self._initialized = False

    def parse(self, data, extent):
        '''
        Parse the passed in data into a UDF NSR Volume Structure.

        Parameters:
         data - The data to parse.
         extent - The extent that this descriptor currently lives at.
        Returns:
         Nothing.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF NSR Volume Structure already initialized")

        (structure_type, standard_ident, structure_version,
         reserved_unused) = struct.unpack_from(self.FMT, data, 0)

        if structure_type != 0:
            raise pycdlibexception.PyCdlibInvalidISO("Invalid structure type")

        if standard_ident != b'NSR02':
            raise pycdlibexception.PyCdlibInvalidISO("Invalid standard identifier")

        if structure_version != 1:
            raise pycdlibexception.PyCdlibInvalidISO("Invalid structure version")

        self.orig_extent_loc = extent
        self.new_extent_loc = None

        self._initialized = True

    def record(self):
        '''
        A method to generate the string representing this UDF NSR Volume
        Structure.

        Parameters:
         None.
        Returns:
         A string representing this UDF BEA Volume Strucutre.
        '''
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF NSR Volume Structure not initialized")
        return struct.pack(self.FMT, 0, b'NSR02', 1, b'\x00' * 2041)

    def new(self):
        '''
        A method to create a new UDF NSR Volume Structure.

        Parameters:
         None.
        Returns:
         Nothing.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF NSR Volume Structure already initialized")

        self._initialized = True

    def extent_location(self):
        '''
        A method to get the extent location of this UDF NSR Volume Structure.

        Parameters:
         None.
        Returns:
         Integer extent location of this UDF NSR Volume Structure.
        '''
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF NSR Volume Structure not yet initialized")

        if self.new_extent_loc is None:
            return self.orig_extent_loc
        return self.new_extent_loc


class TEAVolumeStructure(object):
    '''
    A class representing a UDF Terminating Extended Area Volume Structure.
    '''
    __slots__ = ['_initialized', 'orig_extent_loc', 'new_extent_loc']

    FMT = "=B5sB2041s"

    def __init__(self):
        self._initialized = False

    def parse(self, data, extent):
        '''
        Parse the passed in data into a UDF TEA Volume Structure.

        Parameters:
         data - The data to parse.
         extent - The extent that this descriptor currently lives at.
        Returns:
         Nothing.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("TEA Volume Structure already initialized")

        (structure_type, standard_ident, structure_version,
         reserved_unused) = struct.unpack_from(self.FMT, data, 0)

        if structure_type != 0:
            raise pycdlibexception.PyCdlibInvalidISO("Invalid structure type")

        if standard_ident != b'TEA01':
            raise pycdlibexception.PyCdlibInvalidISO("Invalid standard identifier")

        if structure_version != 1:
            raise pycdlibexception.PyCdlibInvalidISO("Invalid structure version")

        self.orig_extent_loc = extent
        self.new_extent_loc = None

        self._initialized = True

    def record(self):
        '''
        A method to generate the string representing this UDF TEA Volume
        Structure.

        Parameters:
         None.
        Returns:
         A string representing this UDF TEA Volume Strucutre.
        '''
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF TEA Volume Structure not initialized")
        return struct.pack(self.FMT, 0, b'TEA01', 1, b'\x00' * 2041)

    def new(self):
        '''
        A method to create a new UDF TEA Volume Structure.

        Parameters:
         None.
        Returns:
         Nothing.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF TEA Volume Structure already initialized")

        self._initialized = True

    def extent_location(self):
        '''
        A method to get the extent location of this UDF TEA Volume Structure.

        Parameters:
         None.
        Returns:
         Integer extent location of this UDF TEA Volume Structure.
        '''
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF TEA Volume Structure not yet initialized")

        if self.new_extent_loc is None:
            return self.orig_extent_loc
        return self.new_extent_loc


def _compute_csum(data):
    '''
    A method to compute a simple checksum over the given data.
    '''
    def identity(x):
        '''
        The identity function so we can use a function for python2/3
        compatibility.
        '''
        return x

    if isinstance(data, str):
        myord = ord
    elif isinstance(data, bytes):
        myord = identity
    elif isinstance(data, bytearray):
        myord = identity
    csum = 0
    for byte in data:
        csum += myord(byte)
    csum -= myord(data[4])
    csum %= 256

    return csum


class UDFTag(object):
    '''
    A class representing a UDF 167 7.2 Descriptor Tag.
    '''
    __slots__ = ['_initialized', 'tag_ident', 'desc_version', 'tag_serial_number', 'tag_location']

    FMT = "=HHBBHHHL"

    def __init__(self):
        self._initialized = False

    def parse(self, data, extent, crc_bytes):
        '''
        Parse the passed in data into a UDF Descriptor tag.

        Parameters:
         data - The data to parse.
         extent - The extent to compare against for the tag location.
         crc_bytes - The bytes to compute the CRC over.
        Returns:
         Nothing.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Tag already initialized")

        (self.tag_ident, self.desc_version, tag_checksum, reserved,
         self.tag_serial_number, desc_crc, desc_crc_length,
         self.tag_location) = struct.unpack_from(self.FMT, data, 0)

        if reserved != 0:
            raise pycdlibexception.PyCdlibInvalidISO("Reserved data not 0!")

        if _compute_csum(data) != tag_checksum:
            raise pycdlibexception.PyCdlibInvalidISO("Tag checksum does not match!")

        if self.tag_location != extent:
            raise pycdlibexception.PyCdlibInvalidISO("Tag location 0x%x does not match actual location 0x%x" % (self.tag_location, extent))

        if self.desc_version not in [2, 3]:
            raise pycdlibexception.PyCdlibInvalidISO("Tag version not 2 or 3")

        if len(crc_bytes) < desc_crc_length:
            raise pycdlibexception.PyCdlibInternalError("Not enough CRC bytes to compute (expected at least %d, got %d)" % (desc_crc_length, len(crc_bytes)))
        calc = crc_ccitt(crc_bytes[:desc_crc_length])
        if desc_crc != calc:
            raise pycdlibexception.PyCdlibInvalidISO("Tag CRC does not match!")

        self._initialized = True

    def record(self, crc_bytes):
        '''
        A method to generate the string representing this UDF Descriptor Tag.

        Parameters:
         crc_bytes - The string to compute the CRC over.
        Returns:
         A string representing this UDF Descriptor Tag.
        '''
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Descriptor Tag not initialized")

        # We need to compute the checksum, but we'll do that by first creating
        # the output buffer with the csum field set to 0, computing the csum,
        # and then setting that record back as usual.
        rec = bytearray(struct.pack(self.FMT, self.tag_ident, self.desc_version,
                                    0, 0, self.tag_serial_number,
                                    crc_ccitt(crc_bytes), len(crc_bytes),
                                    self.tag_location))

        csum = _compute_csum(rec)

        rec[4] = struct.pack("=B", csum)

        return str(rec)

    def new(self, tag_ident, tag_serial=0):
        '''
        A method to create a new UDF Descriptor Tag.

        Parameters:
         tag_ident - The tag identifier number for this tag.
         tag_serial - The tag serial number for this tag.
        Returns:
         Nothing
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Tag already initialized")

        self.tag_ident = tag_ident
        self.desc_version = 2
        self.tag_serial_number = tag_serial
        self.tag_location = 0  # This will be set later.

        self._initialized = True


class UDFAnchorVolumeStructure(object):
    '''
    A class representing a UDF Anchor Volume Structure.
    '''
    __slots__ = ['_initialized', 'orig_extent_loc', 'new_extent_loc', 'main_vd_length', 'main_vd_extent', 'reserve_vd_length', 'reserve_vd_extent', 'udf_tag']

    FMT = "=16sLLLL"

    def __init__(self):
        self._initialized = False

    def parse(self, data, extent):
        '''
        Parse the passed in data into a UDF Anchor Volume Structure.

        Parameters:
         data - The data to parse.
         extent - The extent that this descriptor currently lives at.
        Returns:
         Nothing.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("Anchor Volume Structure already initialized")

        (desc_tag, self.main_vd_length, self.main_vd_extent,
         self.reserve_vd_length,
         self.reserve_vd_extent) = struct.unpack_from(self.FMT, data, 0)

        self.udf_tag = UDFTag()
        self.udf_tag.parse(desc_tag, extent, data[16:])

        if self.udf_tag.tag_ident != 2:
            raise pycdlibexception.PyCdlibInvalidISO("Anchor Tag identifier not 2")

        self.orig_extent_loc = extent
        self.new_extent_loc = None

        self._initialized = True

    def record(self):
        '''
        A method to generate the string representing this UDF Anchor Volume
        Structure.

        Parameters:
         None.
        Returns:
         A string representing this UDF Anchor Volume Structure.
        '''
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Anchor Volume Descriptor not initialized")
        rec = struct.pack(self.FMT, b'\x00' * 16, self.main_vd_length,
                          self.main_vd_extent, self.reserve_vd_length,
                          self.reserve_vd_extent)[16:] + '\x00' * 480
        return self.udf_tag.record(rec) + rec

    def extent_location(self):
        '''
        A method to get the extent location of this UDF Anchor Volume Structure.

        Parameters:
         None.
        Returns:
         Integer extent location of this UDF Anchor Volume Structure.
        '''
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Anchor Volume Structure not yet initialized")

        if self.new_extent_loc is None:
            return self.orig_extent_loc
        return self.new_extent_loc

    def new(self):
        '''
        A method to create a new UDF Anchor Volume Structure.

        Parameters:
         None.
        Returns:
         Nothing.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Anchor Volume Structure already initialized")

        self.udf_tag = UDFTag()
        self.udf_tag.new(2)  # FIXME: we should let the user set serial_number
        self.main_vd_length = 32768
        self.main_vd_extent = 0  # This will get set later.
        self.reserve_vd_length = 32768
        self.reserve_vd_extent = 0  # This will get set later.

        self._initialized = True

    def set_location(self, new_location, main_vd_extent, reserve_vd_extent):
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Anchor Volume Structure not yet initialized")

        self.new_extent_loc = new_location
        self.udf_tag.tag_location = new_location
        self.main_vd_extent = main_vd_extent
        self.reserve_vd_extent = reserve_vd_extent


class UDFTimestamp(object):
    '''
    A class representing a UDF timestamp.
    '''
    __slots__ = ['_initialized', 'year', 'month', 'day', 'hour', 'minute', 'second', 'centiseconds', 'hundreds_microseconds', 'microseconds', 'timetype', 'tz']

    FMT = "=BBHBBBBBBBB"

    def __init__(self):
        self._initialized = False

    def parse(self, data):
        '''
        Parse the passed in data into a UDF Timestamp.

        Parameters:
         data - The data to parse.
        Returns:
         Nothing.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Timestamp already initialized")

        (tz, timetype, self.year, self.month, self.day, self.hour, self.minute,
         self.second, self.centiseconds, self.hundreds_microseconds,
         self.microseconds) = struct.unpack_from(self.FMT, data, 0)

        self.timetype = timetype >> 4

        def twos_comp(val, bits):
            '''
            Compute the 2's complement of int value val
            '''
            if (val & (1 << (bits - 1))) != 0:  # if sign bit is set e.g., 8bit: 128-255
                val = val - (1 << bits)         # compute negative value
            return val                          # return positive value as is
        self.tz = twos_comp(((timetype & 0xf) << 8) | tz, 12)
        if self.tz < -1440 or self.tz > 1440:
            if self.tz != -2047:
                raise pycdlibexception.PyCdlibInvalidISO("Invalid UDF timezone")

        if self.year < 1 or self.year > 9999:
            raise pycdlibexception.PyCdlibInvalidISO("Invalid UDF year")
        if self.month < 1 or self.month > 12:
            raise pycdlibexception.PyCdlibInvalidISO("Invalid UDF month")
        if self.day < 1 or self.day > 31:
            raise pycdlibexception.PyCdlibInvalidISO("Invalid UDF day")
        if self.hour < 0 or self.hour > 23:
            raise pycdlibexception.PyCdlibInvalidISO("Invalid UDF hour")
        if self.minute < 0 or self.minute > 59:
            raise pycdlibexception.PyCdlibInvalidISO("Invalid UDF minute")
        if self.second < 0 or self.second > 59:
            raise pycdlibexception.PyCdlibInvalidISO("Invalid UDF second")

        self._initialized = True

    def record(self):
        '''
        A method to generate the string representing this UDF Timestamp.

        Parameters:
         None.
        Returns:
         A string representing this UDF Timestamp.
        '''
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Timestamp not initialized")

        tmp = ((1 << 16) - 1) & self.tz
        newtz = tmp & 0xff
        newtimetype = ((tmp >> 8) & 0x0f) | (self.timetype << 4)

        return struct.pack(self.FMT, newtz, newtimetype, self.year, self.month,
                           self.day, self.hour, self.minute, self.second,
                           self.centiseconds, self.hundreds_microseconds,
                           self.microseconds)

    def new(self):
        '''
        A method to create a new UDF Timestamp.

        Parameters:
         None.
        Returns:
         Nothing.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Timestamp already initialized")

        tm = time.time()
        local = time.localtime(tm)

        self.tz = utils.gmtoffset_from_tm(tm, local)
        # FIXME: for the timetype, 0 is UTC, 1 is local, 2 is 'agreement'.
        # We should let the user set this.
        self.timetype = 1
        self.year = local.tm_year
        self.month = local.tm_mon
        self.day = local.tm_mon
        self.hour = local.tm_hour
        self.minute = local.tm_min
        self.second = local.tm_sec
        self.centiseconds = 0
        self.hundreds_microseconds = 0
        self.microseconds = 0

        self._initialized = True


class UDFEntityID(object):
    '''
    A class representing a UDF Entity ID.
    '''
    __slots__ = ['_initialized', 'flags', 'identifier', 'suffix']

    FMT = "=B23s8s"

    def __init__(self):
        self._initialized = False

    def parse(self, data):
        '''
        Parse the passed in data into a UDF Entity ID.

        Parameters:
         data - The data to parse.
        Returns:
         Nothing.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Entity ID already initialized")

        (self.flags, self.identifier, self.suffix) = struct.unpack_from(self.FMT, data, 0)

        self._initialized = True

    def record(self):
        '''
        A method to generate the string representing this UDF Entity ID.

        Parameters:
         None.
        Returns:
         A string representing this UDF Entity ID.
        '''
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Entity ID not initialized")

        return struct.pack(self.FMT, self.flags, self.identifier, self.suffix)

    def new(self, flags=0, identifier=None, suffix=None):
        '''
        A method to create a new UDF Entity ID.

        Parameters:
         None.
        Returns:
         Nothing.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Entity ID already initialized")

        self.flags = flags
        if identifier is None:
            self.identifier = b'\x00' * 23
        else:
            if len(identifier) > 23:
                raise pycdlibexception.PyCdlibInvalidInput("UDF Entity ID identifer must be less than 23 characters")
            self.identifier = b"{:\x00<23}".format(identifier)

        if suffix is None:
            self.suffix = b'\x00' * 8
        else:
            if len(suffix) > 8:
                raise pycdlibexception.PyCdlibInvalidInput("UDF Entity ID suffix must be less than 8 characters")
            self.suffix = b'{:\x00<8}'.format(suffix)

        self._initialized = True


class UDFPrimaryVolumeDescriptor(object):
    '''
    A class representing a UDF Primary Volume Descriptor.
    '''
    __slots__ = ['_initialized', 'orig_extent_loc', 'new_extent_loc', 'vol_desc_seqnum', 'desc_num', 'volume_identifier', 'vol_set_ident', 'desc_char_set', 'explanatory_char_set', 'vol_abstract_length', 'vol_abstract_extent', 'vol_copyright_length', 'vol_copyright_extent', 'implementation_use', 'predecessor_vol_desc_location', 'desc_tag', 'recording_date', 'app_ident', 'impl_ident']

    FMT = "=16sLL32sHHHHLL128s64s64sLLLL32s12s32s64sLH22s"

    def __init__(self):
        self._initialized = False

    def parse(self, data, extent):
        '''
        Parse the passed in data into a UDF Primary Volume Descriptor.

        Parameters:
         data - The data to parse.
         extent - The extent that this descriptor currently lives at.
        Returns:
         Nothing.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Primary Volume Descriptor already initialized")

        (desc_tag, self.vol_desc_seqnum, self.desc_num, self.volume_identifier,
         vol_seqnum, max_vol_seqnum, interchange_level,
         max_interchange_level, character_set_list,
         max_character_set_list, self.vol_set_ident, self.desc_char_set,
         self.explanatory_char_set, self.vol_abstract_length, self.vol_abstract_extent,
         self.vol_copyright_length, self.vol_copyright_extent, app_ident,
         recording_date, impl_ident, self.implementation_use,
         self.predecessor_vol_desc_location, flags,
         reserved) = struct.unpack_from(self.FMT, data, 0)

        self.desc_tag = UDFTag()
        self.desc_tag.parse(desc_tag, extent, data[16:])

        if self.desc_tag.tag_ident != 1:
            raise pycdlibexception.PyCdlibInvalidISO("UDF Primary Descriptor Tag identifier not 1")

        if vol_seqnum != 1:
            raise pycdlibexception.PyCdlibInvalidISO("Only DVD Read-Only disks are supported")
        if max_vol_seqnum != 1:
            raise pycdlibexception.PyCdlibInvalidISO("Only DVD Read-Only disks are supported")
        if interchange_level != 2:
            raise pycdlibexception.PyCdlibInvalidISO("Only DVD Read-Only disks are supported")
        if max_interchange_level != 2:
            raise pycdlibexception.PyCdlibInvalidISO("Only DVD Read-Only disks are supported")
        if character_set_list != 1:
            raise pycdlibexception.PyCdlibInvalidISO("Only DVD Read-Only disks are supported")
        if max_character_set_list != 1:
            raise pycdlibexception.PyCdlibInvalidISO("Only DVD Read-Only disks are supported")
        if flags != 0:
            raise pycdlibexception.PyCdlibInvalidISO("Only DVD Read-Only disks are supported")

        if reserved != b'\x00' * 22:
            raise pycdlibexception.PyCdlibInvalidISO("UDF Primary Volume Descriptor reserved data not 0")

        self.recording_date = UDFTimestamp()
        self.recording_date.parse(recording_date)

        self.app_ident = UDFEntityID()
        self.app_ident.parse(app_ident)

        self.impl_ident = UDFEntityID()
        self.impl_ident.parse(impl_ident)

        self.orig_extent_loc = extent
        self.new_extent_loc = None

        self._initialized = True

    def record(self):
        '''
        A method to generate the string representing this UDF Primary Volume
        Descriptor.

        Parameters:
         None.
        Returns:
         A string representing this UDF Primary Volume Descriptor.
        '''
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Primary Volume Descriptor not initialized")

        rec = struct.pack(self.FMT, b'\x00' * 16,
                          self.vol_desc_seqnum, self.desc_num,
                          self.volume_identifier, 1, 1, 2, 2, 1, 1,
                          self.vol_set_ident,
                          self.desc_char_set, self.explanatory_char_set,
                          self.vol_abstract_length, self.vol_abstract_extent,
                          self.vol_copyright_length, self.vol_copyright_extent,
                          self.app_ident.record(), self.recording_date.record(),
                          self.impl_ident.record(), self.implementation_use,
                          self.predecessor_vol_desc_location, 0, b'\x00' * 22)[16:]
        return self.desc_tag.record(rec) + rec

    def extent_location(self):
        '''
        A method to get the extent location of this UDF Primary Volume Descriptor.

        Parameters:
         None.
        Returns:
         Integer extent location of this UDF Primary Volume Descriptor.
        '''
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Primary Volume Descriptor not yet initialized")

        if self.new_extent_loc is None:
            return self.orig_extent_loc
        return self.new_extent_loc

    def new(self):
        '''
        A method to create a new UDF Primary Volume Descriptor.

        Parameters:
         None.
        Returns:
         Nothing.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Primary Volume Descriptor already initialized")

        self.desc_tag = UDFTag()
        self.desc_tag.new(1)  # FIXME: we should let the user set serial_number

        self.vol_desc_seqnum = 0  # FIXME: we should let the user set this
        self.desc_num = 0  # FIXME: we should let the user set this
        self.volume_identifier = "{:\x00<31}".format(b'\x08CDROM') + b'\x06'  # FIXME: we should let the user set this
        self.vol_set_ident = b'\x08' + struct.pack("=Q", random.getrandbits(64))
        self.desc_char_set = "{:\x00<64}".format(b'\x00OSTA Compressed Unicode')
        self.explanatory_char_set = "{:\x00<64}".format(b'\x00OSTA Compressed Unicode')
        self.vol_abstract_length = 0  # FIXME: we should let the user set this
        self.vol_abstract_extent = 0  # FIXME: we should let the user set this
        self.vol_copyright_length = 0  # FIXME: we should let the user set this
        self.vol_copyright_extent = 0  # FIXME: we should let the user set this
        self.app_ident = UDFEntityID()
        self.app_ident.new()
        self.recording_date = UDFTimestamp()
        self.recording_date.new()
        self.impl_ident = UDFEntityID()
        self.impl_ident.new(0, b'*genisoimage')
        self.implementation_use = b'\x00' * 64  # FIXME: we should let the user set this
        self.predecessor_vol_desc_location = 0  # FIXME: we should let the user set this

        self._initialized = True

    def set_location(self, new_location):
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Primary Volume Descriptor not yet initialized")

        self.new_extent_loc = new_location
        self.desc_tag.tag_location = new_location

class UDFImplementationUseVolumeDescriptorImplementationUse(object):
    '''
    A class representing the Implementation Use field of the Implementation Use Volume Descriptor.
    '''
    __slots__ = ['_initialized', 'charset', 'log_vol_ident', 'lv_info1', 'lv_info2', 'lv_info3', 'impl_ident', 'impl_use']

    FMT = "=64s128s36s36s36s32s128s"

    def __init__(self):
        self._initialized = False

    def parse(self, data):
        '''
        Parse the passed in data into a UDF Implementation Use Volume
        Descriptor Implementation Use field.

        Parameters:
         data - The data to parse.
        Returns:
         Nothing.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Implementation Use Volume Descriptor Implementation Use field already initialized")

        (self.charset, self.log_vol_ident, self.lv_info1, self.lv_info2,
         self.lv_info3, impl_ident,
         self.impl_use) = struct.unpack_from(self.FMT, data, 0)

        self.impl_ident = UDFEntityID()
        self.impl_ident.parse(impl_ident)

        self._initialized = True

    def record(self):
        '''
        A method to generate the string representing this UDF Implementation Use
        Volume Descriptor Implementation Use field.

        Parameters:
         None.
        Returns:
         A string representing this UDF Implementation Use Volume Descriptor.
        '''
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Implementation Use Volume Descriptor Implementation Use field not initialized")

        return struct.pack(self.FMT, self.charset, self.log_vol_ident,
                           self.lv_info1, self.lv_info2, self.lv_info3,
                           self.impl_ident.record(), self.impl_use)

    def new(self):
        '''
        A method to create a new UDF Implementation Use Volume Descriptor Implementation Use field.

        Parameters:
         None:
        Returns:
         Nothing.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Implementation Use Volume Descriptor Implementation Use field already initialized")

        self.charset = b'{:\x00<64}'.format(b'\x00OSTA Compressed Unicode')
        self.log_vol_ident = b'{:\x00<127}'.format(b'\x08CDROM') + b'\x06'
        self.lv_info1 = b'\x00' * 36
        self.lv_info2 = b'\x00' * 36
        self.lv_info3 = b'\x00' * 36
        self.impl_ident = UDFEntityID()
        self.impl_ident.new(0, b'*UDF LV Info', b'\x02\x01')
        self.impl_use = b'\x00' * 128

        self._initialized = True

class UDFImplementationUseVolumeDescriptor(object):
    '''
    A class representing a UDF Implementation Use Volume Structure.
    '''
    __slots__ = ['_initialized', 'orig_extent_loc', 'new_extent_loc', 'vol_desc_seqnum', 'impl_use', 'desc_tag', 'impl_ident']

    FMT = "=16sL32s460s"

    def __init__(self):
        self._initialized = False

    def parse(self, data, extent):
        '''
        Parse the passed in data into a UDF Implementation Use Volume
        Descriptor.

        Parameters:
         data - The data to parse.
         extent - The extent that this descriptor currently lives at.
        Returns:
         Nothing.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Implementation Use Volume Descriptor already initialized")

        (desc_tag, self.vol_desc_seqnum, impl_ident,
         impl_use) = struct.unpack_from(self.FMT, data, 0)

        self.desc_tag = UDFTag()
        self.desc_tag.parse(desc_tag, extent, data[16:])
        if self.desc_tag.tag_ident != 4:
            raise pycdlibexception.PyCdlibInvalidISO("Implementation Use Descriptor Tag identifier not 4")

        self.impl_ident = UDFEntityID()
        self.impl_ident.parse(impl_ident)
        if self.impl_ident.identifier[:12] != b"*UDF LV Info":
            raise pycdlibexception.PyCdlibInvalidISO("Implementation Use Identifier not '*UDF LV Info'")

        self.impl_use = UDFImplementationUseVolumeDescriptorImplementationUse()
        self.impl_use.parse(impl_use)

        self.orig_extent_loc = extent
        self.new_extent_loc = None

        self._initialized = True

    def record(self):
        '''
        A method to generate the string representing this UDF Implementation Use
        Volume Descriptor.

        Parameters:
         None.
        Returns:
         A string representing this UDF Implementation Use Volume Descriptor.
        '''
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Implementation Use Volume Descriptor not initialized")

        rec = struct.pack(self.FMT, b'\x00' * 16,
                          self.vol_desc_seqnum, self.impl_ident.record(),
                          self.impl_use.record())[16:]
        return self.desc_tag.record(rec) + rec

    def extent_location(self):
        '''
        A method to get the extent location of this UDF Implementation Use
        Volume Descriptor.

        Parameters:
         None.
        Returns:
         Integer extent location of this UDF Implementation Use Volume
         Descriptor.
        '''
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Implementation Use Volume Descriptor not initialized")

        if self.new_extent_loc is None:
            return self.orig_extent_loc
        return self.new_extent_loc

    def new(self):
        '''
        A method to create a new UDF Implementation Use Volume Descriptor.

        Parameters:
         None:
        Returns:
         Nothing.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Implementation Use Volume Descriptor already initialized")

        self.desc_tag = UDFTag()
        self.desc_tag.new(4)  # FIXME: we should let the user set serial_number

        self.vol_desc_seqnum = 1

        self.impl_ident = UDFEntityID()
        self.impl_ident.new(0, b"*UDF LV Info", b'\x02\x01')

        self.impl_use = UDFImplementationUseVolumeDescriptorImplementationUse()
        self.impl_use.new()

        self._initialized = True

    def set_location(self, new_location):
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Implementation Use Volume Descriptor not initialized")

        self.new_extent_loc = new_location
        self.desc_tag.tag_location = new_location


class UDFPartitionHeaderDescriptor(object):
    '''
    A class representing a UDF Partition Header Descriptor.
    '''
    __slots__ = ['_initialized']

    FMT = "=LLLLLLLLLL88s"

    def __init__(self):
        self._initialized = False

    def parse(self, data):
        '''
        Parse the passed in data into a UDF Partition Header Descriptor.

        Parameters:
         data - The data to parse.
        Returns:
         Nothing.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Partition Header Descriptor already initialized")
        (unalloc_table_length, unalloc_table_pos, unalloc_bitmap_length,
         unalloc_bitmap_pos, part_integrity_table_length,
         part_integrity_table_pos, freed_table_length, freed_table_pos,
         freed_bitmap_length, freed_bitmap_pos,
         reserved_unused) = struct.unpack_from(self.FMT, data, 0)

        if unalloc_table_length != 0:
            raise pycdlibexception.PyCdlibInvalidISO("Partition Header unallocated table length not 0")
        if unalloc_table_pos != 0:
            raise pycdlibexception.PyCdlibInvalidISO("Partition Header unallocated table position not 0")
        if unalloc_bitmap_length != 0:
            raise pycdlibexception.PyCdlibInvalidISO("Partition Header unallocated bitmap length not 0")
        if unalloc_bitmap_pos != 0:
            raise pycdlibexception.PyCdlibInvalidISO("Partition Header unallocated bitmap position not 0")
        if part_integrity_table_length != 0:
            raise pycdlibexception.PyCdlibInvalidISO("Partition Header partition integrity length not 0")
        if part_integrity_table_pos != 0:
            raise pycdlibexception.PyCdlibInvalidISO("Partition Header partition integrity position not 0")
        if freed_table_length != 0:
            raise pycdlibexception.PyCdlibInvalidISO("Partition Header freed table length not 0")
        if freed_table_pos != 0:
            raise pycdlibexception.PyCdlibInvalidISO("Partition Header freed table position not 0")
        if freed_bitmap_length != 0:
            raise pycdlibexception.PyCdlibInvalidISO("Partition Header freed bitmap length not 0")
        if freed_bitmap_pos != 0:
            raise pycdlibexception.PyCdlibInvalidISO("Partition Header freed bitmap position not 0")

        self._initialized = True

    def record(self):
        '''
        A method to generate the string representing this UDF Partition Header
        Descriptor.

        Parameters:
         None.
        Returns:
         A string representing this UDF Partition Header Descriptor.
        '''
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Partition Header Descriptor not initialized")

        return struct.pack(self.FMT, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, b'\x00' * 88)

    def new(self):
        '''
        A method to create a new UDF Partition Header Descriptor.

        Parameters:
         None.
        Returns:
         Nothing.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Partition Header Descriptor already initialized")

        self._initialized = True


class UDFPartitionVolumeDescriptor(object):
    '''
    A class representing a UDF Partition Volume Structure.
    '''
    __slots__ = ['_initialized', 'orig_extent_loc', 'new_extent_loc', 'vol_desc_seqnum', 'part_flags', 'part_num', 'access_type', 'part_start_location', 'part_length', 'implementation_use', 'desc_tag', 'part_contents', 'impl_ident', 'part_contents_use']

    FMT = "=16sLHH32s128sLLL32s128s156s"

    def __init__(self):
        self._initialized = False

    def parse(self, data, extent):
        '''
        Parse the passed in data into a UDF Partition Volume Descriptor.

        Parameters:
         data - The data to parse.
         extent - The extent that this descriptor currently lives at.
        Returns:
         Nothing.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Partition Volume Descriptor already initialized")

        (desc_tag, self.vol_desc_seqnum, self.part_flags, self.part_num,
         part_contents, part_contents_use, self.access_type,
         self.part_start_location, self.part_length, impl_ident,
         self.implementation_use, reserved_unused) = struct.unpack_from(self.FMT, data, 0)

        self.desc_tag = UDFTag()
        self.desc_tag.parse(desc_tag, extent, data[16:])
        if self.desc_tag.tag_ident != 5:
            raise pycdlibexception.PyCdlibInvalidISO("Implementation Use Descriptor Tag identifier not 5")

        self.part_contents = UDFEntityID()
        self.part_contents.parse(part_contents)
        if self.part_contents.flags != 2:
            raise pycdlibexception.PyCdlibInvalidISO("Partition Contents Flags not 2")
        if self.part_contents.identifier[:6] != "+NSR02":
            raise pycdlibexception.PyCdlibInvalidISO("Partition Contents Identifier not '+NSR02'")

        self.impl_ident = UDFEntityID()
        self.impl_ident.parse(impl_ident)

        self.part_contents_use = UDFPartitionHeaderDescriptor()
        self.part_contents_use.parse(part_contents_use)

        self.orig_extent_loc = extent
        self.new_extent_loc = None

        self._initialized = True

    def record(self):
        '''
        A method to generate the string representing this UDF Partition Volume
        Descriptor.

        Parameters:
         None.
        Returns:
         A string representing this UDF Partition Volume Descriptor.
        '''
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Partition Volume Descriptor not initialized")

        rec = struct.pack(self.FMT, b'\x00' * 16,
                          self.vol_desc_seqnum, self.part_flags,
                          self.part_num, self.part_contents.record(),
                          self.part_contents_use.record(), self.access_type,
                          self.part_start_location, self.part_length,
                          self.impl_ident.record(), self.implementation_use,
                          b'\x00' * 156)[16:]
        return self.desc_tag.record(rec) + rec

    def extent_location(self):
        '''
        A method to get the extent location of this UDF Partition Volume
        Descriptor.

        Parameters:
         None.
        Returns:
         Integer extent location of this UDF Partition Volume Descriptor.
        '''
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Partition Volume Descriptor not initialized")

        if self.new_extent_loc is None:
            return self.orig_extent_loc
        return self.new_extent_loc

    def new(self):
        '''
        A method to create a new UDF Partition Volume Descriptor.

        Parameters:
         None.
        Returns:
         Nothing.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Partition Volume Descriptor already initialized")

        self.desc_tag = UDFTag()
        self.desc_tag.new(5)  # FIXME: we should let the user set serial_number

        self.vol_desc_seqnum = 2
        self.part_flags = 1  # FIXME: how should we set this?
        self.part_num = 0  # FIXME: how should we set this?

        self.part_contents = UDFEntityID()
        self.part_contents.new(2, "+NSR02")

        self.part_contents_use = UDFPartitionHeaderDescriptor()
        self.part_contents_use.new()

        self.access_type = 1
        self.part_start_location = 0  # This will get set later
        self.part_length = 9  # This will get set later

        self.impl_ident = UDFEntityID()
        self.impl_ident.new()  # FIXME: we should let the user set this

        self.implementation_use = b'\x00' * 128  # FIXME: we should let the user set this

        self._initialized = True

    def set_location(self, new_location):
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Partition Volume Descriptor not initialized")
        self.new_extent_loc = new_location
        self.desc_tag.tag_location = new_location

    def set_start_location(self, new_location):
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Partition Volume Descriptor not initialized")
        self.part_start_location = new_location


class UDFPartitionMap(object):
    '''
    A class representing a UDF Partition Map.
    '''
    __slots__ = ['_initialized', 'part_num']

    FMT = "=BBHH"

    def __init__(self):
        self._initialized = False

    def parse(self, data):
        '''
        Parse the passed in data into a UDF Partition Map.

        Parameters:
         data - The data to parse.
        Returns:
         Nothing.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Partition Map already initialized")

        (map_type, map_length, vol_seqnum,
         self.part_num) = struct.unpack_from(self.FMT, data, 0)

        if map_type != 1:
            raise pycdlibexception.PyCdlibInvalidISO("UDF Partition Map type is not 1")
        if map_length != 6:
            raise pycdlibexception.PyCdlibInvalidISO("UDF Partition Map length is not 6")
        if vol_seqnum != 1:
            raise pycdlibexception.PyCdlibInvalidISO("UDF Partition Volume Sequence Number is not 1")

        self._initialized = True

    def record(self):
        '''
        A method to generate the string representing this UDF Partition Map.

        Parameters:
         None.
        Returns:
         A string representing this UDF Partition Map.
        '''
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Partition Map not initialized")

        return struct.pack(self.FMT, 1, 6, 1, self.part_num)

    def new(self):
        '''
        A method to create a new UDF Partition Map.

        Parameters:
         None.
        Returns:
         Nothing.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Partition Map already initialized")

        self.part_num = 0  # FIXME: we should let the user set this

        self._initialized = True


class UDFLongAD(object):
    '''
    A class representing a UDF Long Allocation Descriptor.
    '''
    __slots__ = ['_initialized', 'extent_length', 'log_block_num', 'part_ref_num', 'impl_use']

    FMT = "=LLH6s"

    def __init__(self):
        self._initialized = False

    def parse(self, data):
        '''
        Parse the passed in data into a UDF Long AD.

        Parameters:
         data - The data to parse.
        Returns:
         Nothing.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Long Allocation descriptor already initialized")
        (self.extent_length, self.log_block_num, self.part_ref_num,
         self.impl_use) = struct.unpack_from(self.FMT, data, 0)

        self._initialized = True

    def record(self):
        '''
        A method to generate the string representing this UDF Long AD.

        Parameters:
         None.
        Returns:
         A string representing this UDF Long AD.
        '''
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Long AD not initialized")

        return struct.pack(self.FMT, self.extent_length, self.log_block_num,
                           self.part_ref_num, self.impl_use)

    def new(self, length, blocknum):
        '''
        A method to create a new UDF Long AD.

        Parameters:
         None.
        Returns:
         Nothing.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Long AD already initialized")

        self.extent_length = length
        self.log_block_num = blocknum
        self.part_ref_num = 0  # FIXME: we should let the user set this
        self.impl_use = b'\x00' * 6  # FIXME: we should let the user set this

        self._initialized = True


class UDFLogicalVolumeDescriptor(object):
    '''
    A class representing a UDF Logical Volume Descriptor.
    '''
    __slots__ = ['_initialized', 'orig_extent_loc', 'new_extent_loc', 'vol_desc_seqnum', 'desc_charset', 'logical_volume_ident', 'implementation_use', 'integrity_sequence_length', 'integrity_sequence_extent', 'desc_tag', 'domain_ident', 'impl_ident', 'partition_map', 'logical_volume_contents_use']

    FMT = "=16sL64s128sL32s16sLL32s128sLL6s"

    def __init__(self):
        self._initialized = False

    def parse(self, data, extent):
        '''
        Parse the passed in data into a UDF Logical Volume Descriptor.

        Parameters:
         data - The data to parse.
         extent - The extent that this descriptor currently lives at.
        Returns:
         Nothing.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Logical Volume Descriptor already initialized")

        (desc_tag, self.vol_desc_seqnum, self.desc_charset, self.logical_volume_ident,
         logical_block_size, domain_ident, logical_volume_contents_use,
         map_table_length, num_partition_maps, impl_ident,
         self.implementation_use, self.integrity_sequence_length,
         self.integrity_sequence_extent, partition_map) = struct.unpack_from(self.FMT, data, 0)

        self.desc_tag = UDFTag()
        self.desc_tag.parse(desc_tag, extent, data[16:])
        if self.desc_tag.tag_ident != 6:
            raise pycdlibexception.PyCdlibInvalidISO("Volume Descriptor Tag identifier not 6")

        if logical_block_size != 2048:
            raise pycdlibexception.PyCdlibInvalidISO("Volume Descriptor block size is not 2048")

        self.domain_ident = UDFEntityID()
        self.domain_ident.parse(domain_ident)
        if self.domain_ident.identifier[:19] != "*OSTA UDF Compliant":
            raise pycdlibexception.PyCdlibInvalidISO("Volume Descriptor Identifier not '*OSTA UDF Compliant'")

        if map_table_length != 6:
            raise pycdlibexception.PyCdlibInvalidISO("Volume Descriptor map table length not 6")

        if num_partition_maps != 1:
            raise pycdlibexception.PyCdlibInvalidISO("Volume Descriptor number of partition maps not 1")

        self.impl_ident = UDFEntityID()
        self.impl_ident.parse(impl_ident)

        self.partition_map = UDFPartitionMap()
        self.partition_map.parse(partition_map)

        self.logical_volume_contents_use = UDFLongAD()
        self.logical_volume_contents_use.parse(logical_volume_contents_use)

        self.orig_extent_loc = extent
        self.new_extent_loc = None

        self._initialized = True

    def record(self):
        '''
        A method to generate the string representing this UDF Logical Volume Descriptor.

        Parameters:
         None.
        Returns:
         A string representing this UDF Logical Volume Descriptor.
        '''
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Logical Volume Descriptor not initialized")

        rec = struct.pack(self.FMT, b'\x00' * 16,
                          self.vol_desc_seqnum, self.desc_charset,
                          self.logical_volume_ident, 2048,
                          self.domain_ident.record(),
                          self.logical_volume_contents_use.record(), 6, 1,
                          self.impl_ident.record(), self.implementation_use,
                          self.integrity_sequence_length,
                          self.integrity_sequence_extent,
                          self.partition_map.record())[16:]
        return self.desc_tag.record(rec) + rec

    def extent_location(self):
        '''
        A method to get the extent location of this UDF Logical Volume
        Descriptor.

        Parameters:
         None.
        Returns:
         Integer extent location of this UDF Logical Volume Descriptor.
        '''
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Logical Volume Descriptor not initialized")

        if self.new_extent_loc is None:
            return self.orig_extent_loc
        return self.new_extent_loc

    def new(self):
        '''
        A method to create a new UDF Logical Volume Descriptor.

        Parameters:
         None.
        Returns:
         Nothing.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Logical Volume Descriptor already initialized")

        self.desc_tag = UDFTag()
        self.desc_tag.new(6)  # FIXME: we should let the user set serial_number

        self.vol_desc_seqnum = 3
        self.desc_charset = "{:\x00<64}".format(b'\x00OSTA Compressed Unicode')

        self.logical_volume_ident = "{:\x00<127}".format(b'\x08CDROM') + b'\x06'  # FIXME: we should let the user set this

        self.domain_ident = UDFEntityID()
        self.domain_ident.new(0, b"*OSTA UDF Compliant", b'\x02\x01\x03')

        self.logical_volume_contents_use = UDFLongAD()
        self.logical_volume_contents_use.new(4096, 0)

        self.impl_ident = UDFEntityID()
        self.impl_ident.new()

        self.implementation_use = b'\x00' * 128  # FIXME: let the user set this
        self.integrity_sequence_length = 4096
        self.integrity_sequence_extent = 0  # This will get set later

        self.partition_map = UDFPartitionMap()
        self.partition_map.new()

        self._initialized = True

    def set_location(self, new_location):
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Logical Volume Descriptor not initialized")

        self.new_extent_loc = new_location
        self.desc_tag.tag_location = new_location

    def set_integrity_location(self, integrity_extent):
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Logical Volume Descriptor not initialized")

        self.integrity_sequence_extent = integrity_extent

class UDFUnallocatedSpaceDescriptor(object):
    '''
    A class representing a UDF Unallocated Space Descriptor.
    '''
    __slots__ = ['_initialized', 'orig_extent_loc', 'new_extent_loc', 'vol_desc_seqnum', 'desc_tag']

    FMT = "=16sLL"

    def __init__(self):
        self._initialized = False

    def parse(self, data, extent):
        '''
        Parse the passed in data into a UDF Unallocated Space Descriptor.

        Parameters:
         data - The data to parse.
         extent - The extent that this descriptor currently lives at.
        Returns:
         Nothing.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Unallocated Space Descriptor already initialized")
        (desc_tag, self.vol_desc_seqnum,
         num_alloc_descriptors) = struct.unpack_from(self.FMT, data, 0)

        self.desc_tag = UDFTag()
        self.desc_tag.parse(desc_tag, extent, data[16:])
        if self.desc_tag.tag_ident != 7:
            raise pycdlibexception.PyCdlibInvalidISO("Unallocated Space Tag identifier not 7")

        if num_alloc_descriptors != 0:
            raise pycdlibexception.PyCdlibInvalidISO("UDF Unallocated Space Descriptor allocated descriptors is not 0")

        self.orig_extent_loc = extent
        self.new_extent_loc = None

        self._initialized = True

    def record(self):
        '''
        A method to generate the string representing this UDF Unallocated Space
        Descriptor.

        Parameters:
         None.
        Returns:
         A string representing this UDF Unallocated Space Descriptor.
        '''
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Unallocated Space Descriptor not initialized")

        rec = struct.pack(self.FMT, b'\x00' * 16,
                          self.vol_desc_seqnum, 0)[16:]
        return self.desc_tag.record(rec) + rec

    def extent_location(self):
        '''
        A method to get the extent location of this UDF Unallocated Space
        Descriptor.

        Parameters:
         None.
        Returns:
         Integer extent location of this UDF Unallocated Space Descriptor.
        '''
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Unallocated Space Descriptor not initialized")

        if self.new_extent_loc is None:
            return self.orig_extent_loc
        return self.new_extent_loc

    def new(self):
        '''
        A method to create a new UDF Unallocated Space Descriptor.

        Parameters:
         None.
        Returns:
         Nothing.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Unallocated Space Descriptor already initialized")

        self.desc_tag = UDFTag()
        self.desc_tag.new(7)  # FIXME: we should let the user set serial_number

        self.vol_desc_seqnum = 4

        self._initialized = True

    def set_location(self, new_location):
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Unallocated Space Descriptor not initialized")

        self.new_extent_loc = new_location
        self.desc_tag.tag_location = new_location


class UDFTerminatingDescriptor(object):
    '''
    A class representing a UDF Unallocated Space Descriptor.
    '''
    __slots__ = ['_initialized', 'orig_extent_loc', 'new_extent_loc', 'desc_tag']

    FMT = "=16s496s"

    def __init__(self):
        self._initialized = False

    def parse(self, data, extent, start_extent):
        '''
        Parse the passed in data into a UDF Terminating Descriptor.

        Parameters:
         data - The data to parse.
         extent - The extent that this descriptor currently lives at.
         start_extent - The extent that this logical block starts at.
        Returns:
         Nothing.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Terminating Descriptor already initialized")

        (desc_tag, reserved_unused) = struct.unpack_from(self.FMT, data, 0)

        self.desc_tag = UDFTag()
        self.desc_tag.parse(desc_tag, extent - start_extent, data[16:])
        if self.desc_tag.tag_ident != 8:
            raise pycdlibexception.PyCdlibInvalidISO("Terminating Tag identifier not 8")

        self.orig_extent_loc = extent
        self.new_extent_loc = None

        self._initialized = True

    def record(self):
        '''
        A method to generate the string representing this UDF Terminating
        Descriptor.

        Parameters:
         None.
        Returns:
         A string representing this UDF Terminating Descriptor.
        '''
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Terminating Descriptor not initialized")

        rec = struct.pack(self.FMT, b'\x00' * 16, b'\x00' * 496)[16:]
        return self.desc_tag.record(rec) + rec

    def extent_location(self):
        '''
        A method to get the extent location of this UDF Terminating Descriptor.

        Parameters:
         None.
        Returns:
         Integer extent location of this UDF Terminating Descriptor.
        '''
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Terminating Descriptor not initialized")

        if self.new_extent_loc is None:
            return self.orig_extent_loc
        return self.new_extent_loc

    def new(self):
        '''
        A method to create a new UDF Terminating Descriptor.

        Parameters:
         None.
        Returns:
         Nothing.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Terminating Descriptor already initialized")

        self.desc_tag = UDFTag()
        self.desc_tag.new(8)  # FIXME: we should let the user set serial_number

        self._initialized = True

    def set_location(self, new_location, tag_location=None):
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Terminating Descriptor not initialized")

        self.new_extent_loc = new_location
        if tag_location is None:
            tag_location = new_location
        self.desc_tag.tag_location = tag_location


class UDFLogicalVolumeHeaderDescriptor(object):
    '''
    A class representing a UDF Logical Volume Header Descriptor.
    '''
    __slots__ = ['_initialized', 'unique_id']

    FMT = "=Q24s"

    def __init__(self):
        self._initialized = False

    def parse(self, data):
        '''
        Parse the passed in data into a UDF Logical Volume Header Descriptor.

        Parameters:
         data - The data to parse.
        Returns:
         Nothing.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Logical Volume Header Descriptor already initialized")
        (self.unique_id, reserved_unused) = struct.unpack_from(self.FMT, data, 0)

        self._initialized = True

    def record(self):
        '''
        A method to generate the string representing this UDF Logical Volume
        Header Descriptor.

        Parameters:
         None.
        Returns:
         A string representing this UDF Logical Volume Header Descriptor.
        '''
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Logical Volume Header Descriptor not initialized")

        return struct.pack(self.FMT, self.unique_id, b'\x00' * 24)

    def new(self):
        '''
        A method to create a new UDF Logical Volume Header Descriptor.

        Parameters:
         None.
        Returns:
         Nothing.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Logical Volume Header Descriptor already initialized")

        self.unique_id = 261

        self._initialized = True


class UDFLogicalVolumeImplementationUse(object):
    '''
    A class representing a UDF Logical Volume Implementation Use.
    '''
    __slots__ = ['_initialized', 'num_files', 'num_dirs', 'min_udf_read_revision', 'min_udf_write_revision', 'max_udf_write_revision', 'impl_id', 'impl_use']

    FMT = "=32sLLHHH"

    def __init__(self):
        self._initialized = False

    def parse(self, data):
        '''
        Parse the passed in data into a UDF Logical Volume Implementation Use.

        Parameters:
         data - The data to parse.
        Returns:
         Nothing.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Logical Volume Implementation Use already initialized")

        (impl_id, self.num_files, self.num_dirs, self.min_udf_read_revision,
         self.min_udf_write_revision,
         self.max_udf_write_revision) = struct.unpack_from(self.FMT, data, 0)

        self.impl_id = UDFEntityID()
        self.impl_id.parse(impl_id)

        self.impl_use = data[46:]

        self._initialized = True

    def record(self):
        '''
        A method to generate the string representing this UDF Logical Volume
        Implementation Use.

        Parameters:
         None.
        Returns:
         A string representing this UDF Logical Volume Implementation Use.
        '''
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Logical Volume Implementation Use not initialized")

        return struct.pack(self.FMT, self.impl_id.record(),
                           self.num_files, self.num_dirs,
                           self.min_udf_read_revision,
                           self.min_udf_write_revision,
                           self.max_udf_write_revision) + self.impl_use

    def new(self):
        '''
        A method to create a new UDF Logical Volume Implementation Use.

        Parameters:
         None.
        Returns:
         Nothing.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Logical Volume Implementation Use already initialized")

        self.impl_id = UDFEntityID()
        self.impl_id.new()

        self.num_files = 0  # FIXME: let the user set this
        self.num_dirs = 1
        self.min_udf_read_revision = 258
        self.min_udf_write_revision = 258
        self.max_udf_write_revision = 258

        self.impl_use = b'\x00' * 378

        self._initialized = True


class UDFLogicalVolumeIntegrityDescriptor(object):
    '''
    A class representing a UDF Logical Volume Integrity Descriptor.
    '''
    __slots__ = ['_initialized', 'orig_extent_loc', 'new_extent_loc', 'length_impl_use', 'free_space_table', 'size_table', 'desc_tag', 'recording_date', 'logical_volume_contents_use', 'logical_volume_impl_use']

    FMT = "=16s12sLLL32sLLLL424s"

    def __init__(self):
        self._initialized = False

    def parse(self, data, extent):
        '''
        Parse the passed in data into a UDF Logical Volume Integrity Descriptor.

        Parameters:
         data - The data to parse.
         extent - The extent that this descriptor currently lives at.
        Returns:
         Nothing.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Logical Volume Integrity Descriptor already initialized")

        (desc_tag, recording_date, integrity_type,
         next_integrity_extent_length, next_integrity_extent_extent,
         logical_volume_contents_use, num_partitions,
         self.length_impl_use, self.free_space_table,
         self.size_table, impl_use) = struct.unpack_from(self.FMT, data, 0)

        self.desc_tag = UDFTag()
        self.desc_tag.parse(desc_tag, extent, data[16:16 + 118])
        if self.desc_tag.tag_ident != 9:
            raise pycdlibexception.PyCdlibInvalidISO("Logical Volume Integrity Tag identifier not 9")

        self.recording_date = UDFTimestamp()
        self.recording_date.parse(recording_date)

        if integrity_type != 1:
            raise pycdlibexception.PyCdlibInvalidISO("Logical Volume Integrity Type not 1")
        if next_integrity_extent_length != 0:
            raise pycdlibexception.PyCdlibInvalidISO("Logical Volume Integrity Extent length not 1")
        if next_integrity_extent_extent != 0:
            raise pycdlibexception.PyCdlibInvalidISO("Logical Volume Integrity Extent extent not 1")
        if num_partitions != 1:
            raise pycdlibexception.PyCdlibInvalidISO("Logical Volume Integrity number partitions not 1")
        # For now, we only support an implementation use field of up to 424
        # bytes (the "rest" of the 512 byte sector we get here).  If we run
        # across ones that are larger, we can go up to 2048, but anything
        # larger than that is invalid (I'm not quite sure why UDF defines
        # this as a 32-bit quantity, since there are no situations in which
        # this can be larger than 2048 minus 88).
        if self.length_impl_use > 424:
            raise pycdlibexception.PyCdlibInvalidISO("Logical Volume Integrity implementation use length too large")
        if self.free_space_table != 0:
            raise pycdlibexception.PyCdlibInvalidISO("Logical Volume Integrity free space table not 0")

        self.logical_volume_contents_use = UDFLogicalVolumeHeaderDescriptor()
        self.logical_volume_contents_use.parse(logical_volume_contents_use)

        self.logical_volume_impl_use = UDFLogicalVolumeImplementationUse()
        self.logical_volume_impl_use.parse(impl_use)

        self.orig_extent_loc = extent
        self.new_extent_loc = None

        self._initialized = True

    def record(self):
        '''
        A method to generate the string representing this UDF Logical Volume
        Integrity Descriptor.

        Parameters:
         None.
        Returns:
         A string representing this UDF Logical Volume Integrity Descriptor.
        '''
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Logical Volume Integrity Descriptor not initialized")

        rec = struct.pack(self.FMT, b'\x00' * 16,
                          self.recording_date.record(), 1, 0, 0,
                          self.logical_volume_contents_use.record(), 1,
                          self.length_impl_use, self.free_space_table,
                          self.size_table,
                          self.logical_volume_impl_use.record())[16:]
        return self.desc_tag.record(rec[:118]) + rec

    def extent_location(self):
        '''
        A method to get the extent location of this UDF Logical Volume Integrity
        Descriptor.

        Parameters:
         None.
        Returns:
         Integer extent location of this UDF Logical Volume Integrity Descriptor.
        '''
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Logical Volume Integrity Descriptor not initialized")

        if self.new_extent_loc is None:
            return self.orig_extent_loc
        return self.new_extent_loc

    def new(self):
        '''
        A method to create a new UDF Logical Volume Integrity Descriptor.

        Parameters:
         None.
        Returns:
         Nothing.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Logical Volume Integrity Descriptor already initialized")

        self.desc_tag = UDFTag()
        self.desc_tag.new(9)  # FIXME: we should let the user set serial_number

        self.recording_date = UDFTimestamp()
        self.recording_date.new()

        self.length_impl_use = 46
        self.free_space_table = 0  # FIXME: let the user set this
        self.size_table = 9

        self.logical_volume_contents_use = UDFLogicalVolumeHeaderDescriptor()
        self.logical_volume_contents_use.new()

        self.logical_volume_impl_use = UDFLogicalVolumeImplementationUse()
        self.logical_volume_impl_use.new()

        self._initialized = True

    def set_location(self, new_location):
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF Logical Volume Integrity Descriptor not initialized")

        self.new_extent_loc = new_location
        self.desc_tag.tag_location = new_location

class UDFFileSetDescriptor(object):
    '''
    A class representing a UDF File Set Descriptor.
    '''
    __slots__ = ['_initialized', 'orig_extent_loc', 'new_extent_loc', 'log_vol_charset', 'log_vol_ident', 'file_set_charset', 'file_set_ident', 'copyright_file_ident', 'abstract_file_ident', 'desc_tag', 'recording_date', 'domain_ident', 'root_dir_icb']

    FMT = "=16s12sHHLLLL64s128s64s32s32s32s16s32s16s48s"

    def __init__(self):
        self._initialized = False

    def parse(self, data, extent, start_extent):
        '''
        Parse the passed in data into a UDF File Set Descriptor.

        Parameters:
         data - The data to parse.
         extent - The extent that this descriptor currently lives at.
         start_extent - The extent that this logical block starts at.
        Returns:
         Nothing.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF File Set Descriptor already initialized")

        (desc_tag, recording_date, interchange_level, max_interchange_level,
         charset_list, max_charset_list, file_set_num, file_set_desc_num,
         self.log_vol_charset, self.log_vol_ident,
         self.file_set_charset, self.file_set_ident, self.copyright_file_ident,
         self.abstract_file_ident, root_dir_icb, domain_ident, next_extent,
         reserved_unused) = struct.unpack_from(self.FMT, data, 0)

        self.desc_tag = UDFTag()
        self.desc_tag.parse(desc_tag, extent - start_extent, data[16:])
        if self.desc_tag.tag_ident != 256:
            raise pycdlibexception.PyCdlibInvalidISO("File Set Descriptor Tag identifier not 9")

        self.recording_date = UDFTimestamp()
        self.recording_date.parse(recording_date)

        if interchange_level != 3:
            raise pycdlibexception.PyCdlibInvalidISO("Only DVD Read-Only disks are supported")
        if max_interchange_level != 3:
            raise pycdlibexception.PyCdlibInvalidISO("Only DVD Read-Only disks are supported")
        if charset_list != 1:
            raise pycdlibexception.PyCdlibInvalidISO("Only DVD Read-Only disks are supported")
        if max_charset_list != 1:
            raise pycdlibexception.PyCdlibInvalidISO("Only DVD Read-Only disks are supported")
        if file_set_num != 0:
            raise pycdlibexception.PyCdlibInvalidISO("Only DVD Read-Only disks are supported")
        if file_set_desc_num != 0:
            raise pycdlibexception.PyCdlibInvalidISO("Only DVD Read-Only disks are supported")

        self.domain_ident = UDFEntityID()
        self.domain_ident.parse(domain_ident)
        if self.domain_ident.identifier[:19] != "*OSTA UDF Compliant":
            raise pycdlibexception.PyCdlibInvalidISO("File Set Descriptor Identifier not '*OSTA UDF Compliant'")

        self.root_dir_icb = UDFLongAD()
        self.root_dir_icb.parse(root_dir_icb)

        if next_extent != b'\x00' * 16:
            raise pycdlibexception.PyCdlibInvalidISO("Only DVD Read-Only disks are supported")

        self.orig_extent_loc = extent
        self.new_extent_loc = None

        self._initialized = True

    def record(self):
        '''
        A method to generate the string representing this UDF File Set
        Descriptor.

        Parameters:
         None.
        Returns:
         A string representing this UDF File Set Descriptor.
        '''
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF File Set Descriptor not initialized")

        rec = struct.pack(self.FMT, b'\x00' * 16,
                          self.recording_date.record(), 3, 3, 1, 1, 0, 0,
                          self.log_vol_charset, self.log_vol_ident,
                          self.file_set_charset, self.file_set_ident,
                          self.copyright_file_ident,
                          self.abstract_file_ident, self.root_dir_icb.record(),
                          self.domain_ident.record(), b'\x00' * 16,
                          b'\x00' * 48)[16:]
        return self.desc_tag.record(rec) + rec

    def extent_location(self):
        '''
        A method to get the extent location of this UDF File Set Descriptor.

        Parameters:
         None.
        Returns:
         Integer extent location of this UDF File Set Descriptor.
        '''
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF File Set Descriptor not initialized")

        if self.new_extent_loc is None:
            return self.orig_extent_loc
        return self.new_extent_loc

    def new(self):
        '''
        A method to create a new UDF File Set Descriptor.

        Parameters:
         None.
        Returns:
         Nothing.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF File Set Descriptor already initialized")

        self.desc_tag = UDFTag()
        self.desc_tag.new(256)  # FIXME: we should let the user set serial_number

        self.recording_date = UDFTimestamp()
        self.recording_date.new()

        self.domain_ident = UDFEntityID()
        self.domain_ident.new(0, "*OSTA UDF Compliant", b'\x02\x01\x03')

        self.root_dir_icb = UDFLongAD()
        self.root_dir_icb.new(2048, 2)

        self.log_vol_charset = b'\x00' * 64  # FIXME: let the user set this
        self.log_vol_ident = b'\x00' * 128  # FIXME: let the user set this
        self.file_set_charset = b'\x00' * 64  # FIXME: let the user set this
        self.file_set_ident = b'\x00' * 32  # FIXME: let the user set this
        self.copyright_file_ident = b'\x00' * 32  # FIXME: let the user set this
        self.abstract_file_ident = b'\x00' * 32  # FIXME: let the user set this

        self._initialized = True


class UDFICBTag(object):
    '''
    A class representing a UDF ICB Tag.
    '''
    __slots__ = ['_initialized', 'prior_num_direct_entries', 'strategy_type', 'strategy_param', 'max_num_entries', 'file_type', 'parent_icb_log_block_num', 'parent_icb_part_ref_num', 'flags']

    FMT = "=LHHHBBLHH"

    def __init__(self):
        self._initialized = False

    def parse(self, data):
        '''
        Parse the passed in data into a UDF ICB Tag.

        Parameters:
         data - The data to parse.
        Returns:
         Nothing.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF ICB Tag already initialized")

        (self.prior_num_direct_entries, self.strategy_type, self.strategy_param,
         self.max_num_entries, reserved, self.file_type,
         self.parent_icb_log_block_num, self.parent_icb_part_ref_num,
         self.flags) = struct.unpack_from(self.FMT, data, 0)

        if self.strategy_type not in [4, 4096]:
            raise pycdlibexception.PyCdlibInvalidISO("UDF ICB Tag invalid strategy type")

        if reserved != 0:
            raise pycdlibexception.PyCdlibInvalidISO("UDF ICB Tag reserved not 0")

        self._initialized = True

    def record(self):
        '''
        A method to generate the string representing this UDF ICB Tag.

        Parameters:
         None.
        Returns:
         A string representing this UDF ICB Tag.
        '''
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF ICB Tag not initialized")

        return struct.pack(self.FMT, self.prior_num_direct_entries,
                           self.strategy_type, self.strategy_param,
                           self.max_num_entries, 0, self.file_type,
                           self.parent_icb_log_block_num,
                           self.parent_icb_part_ref_num, self.flags)

    def new(self):
        '''
        A method to create a new UDF ICB Tag.

        Parameters:
         None.
        Returns:
         Nothing.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF ICB Tag already initialized")

        self.prior_num_direct_entries = 0  # FIXME: let the user set this
        self.strategy_type = 4
        self.strategy_param = 0  # FIXME: let the user set this
        self.max_num_entries = 1
        self.file_type = 4
        self.parent_icb_log_block_num = 0  # FIXME: let the user set this
        self.parent_icb_part_ref_num = 0  # FIXME: let the user set this
        self.flags = 560

        self._initialized = True


class UDFFileEntry(object):
    '''
    A class representing a UDF File Entry.
    '''
    __slots__ = ['_initialized', 'orig_extent_loc', 'new_extent_loc', 'uid', 'gid', 'perms', 'file_link_count', 'info_len', 'log_block_recorded', 'unique_id', 'len_extended_attrs', 'len_alloc_descs', 'desc_tag', 'icb_tag', 'alloc_descs', 'descs', 'access_time', 'mod_time', 'attr_time', 'extended_attr_icb', 'impl_ident', 'extended_attrs']

    FMT = "=16s20sLLLHBBLQQ12s12s12sL16s32sQLL"

    def __init__(self):
        self.alloc_descs = []
        self.descs = []
        self._initialized = False

    def parse(self, data, extent, start_extent):
        '''
        Parse the passed in data into a UDF File Entry.

        Parameters:
         data - The data to parse.
         extent - The extent that this descriptor currently lives at.
         start_extent - The extent that this logical block starts at.
        Returns:
         Nothing.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF File Entry already initialized")

        (desc_tag, icb_tag, self.uid, self.gid, self.perms, self.file_link_count,
         record_format, record_display_attrs, record_len,
         self.info_len, self.log_block_recorded, access_time, mod_time,
         attr_time, checkpoint, extended_attr_icb, impl_ident, self.unique_id,
         self.len_extended_attrs, self.len_alloc_descs) = struct.unpack_from(self.FMT, data, 0)

        self.desc_tag = UDFTag()
        self.desc_tag.parse(desc_tag, extent - start_extent, data[16:16 + 168])
        if self.desc_tag.tag_ident != 261:
            raise pycdlibexception.PyCdlibInvalidISO("File Entry Descriptor Tag identifier not 9")

        self.icb_tag = UDFICBTag()
        self.icb_tag.parse(icb_tag)

        if record_format != 0:
            raise pycdlibexception.PyCdlibInvalidISO("File Entry record format is not 0")

        if record_display_attrs != 0:
            raise pycdlibexception.PyCdlibInvalidISO("File Entry record display attributes is not 0")

        if record_len != 0:
            raise pycdlibexception.PyCdlibInvalidISO("File Entry record length is not 0")

        self.access_time = UDFTimestamp()
        self.access_time.parse(access_time)

        self.mod_time = UDFTimestamp()
        self.mod_time.parse(mod_time)

        self.attr_time = UDFTimestamp()
        self.attr_time.parse(attr_time)

        if checkpoint != 1:
            raise pycdlibexception.PyCdlibInvalidISO("Only DVD Read-only disks supported")

        self.extended_attr_icb = UDFLongAD()
        self.extended_attr_icb.parse(extended_attr_icb)

        self.impl_ident = UDFEntityID()
        self.impl_ident.parse(impl_ident)

        offset = struct.calcsize(self.FMT)
        self.extended_attrs = data[offset:offset + self.len_extended_attrs]

        offset += self.len_extended_attrs
        num_alloc_descs = self.len_alloc_descs / 8  # a short_ad is 8 bytes
        for i_unused in range(0, num_alloc_descs):
            (length, pos) = struct.unpack("=LL", data[offset:offset + 8])
            self.alloc_descs.append((length, pos))
            offset += 8

        self.orig_extent_loc = extent
        self.new_extent_loc = None

        self._initialized = True

    def record(self):
        '''
        A method to generate the string representing this UDF File Entry.

        Parameters:
         None.
        Returns:
         A string representing this UDF File Entry.
        '''
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF File Entry not initialized")

        rec = struct.pack(self.FMT, b'\x00' * 16,
                          self.icb_tag.record(), self.uid, self.gid,
                          self.perms, self.file_link_count, 0, 0, 0,
                          self.info_len, self.log_block_recorded,
                          self.access_time.record(), self.mod_time.record(),
                          self.attr_time.record(), 1,
                          self.extended_attr_icb.record(),
                          self.impl_ident.record(), self.unique_id,
                          self.len_extended_attrs, self.len_alloc_descs)[16:]
        for length, pos in self.alloc_descs:
            rec += struct.pack("=LL", length, pos)

        return self.desc_tag.record(rec) + rec

    def extent_location(self):
        '''
        A method to get the extent location of this UDF File Entry.

        Parameters:
         None.
        Returns:
         Integer extent location of this UDF File Entry.
        '''
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF File Entry not initialized")

        if self.new_extent_loc is None:
            return self.orig_extent_loc
        return self.new_extent_loc

    def new(self):
        '''
        A method to create a new UDF File Entry.

        Parameters:
         None.
        Returns:
         Nothing.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF File Entry already initialized")

        self.desc_tag = UDFTag()
        self.desc_tag.new(261)  # FIXME: we should let the user set serial_number

        self.icb_tag = UDFICBTag()
        self.icb_tag.new()

        self.uid = 4294967295
        self.gid = 4294967295
        self.perms = 5285
        self.file_link_count = 1
        self.info_len = 40
        self.log_block_recorded = 1

        self.access_time = UDFTimestamp()
        self.access_time.new()

        self.mod_time = UDFTimestamp()
        self.mod_time.new()

        self.attr_time = UDFTimestamp()
        self.attr_time.new()

        self.extended_attr_icb = UDFLongAD()
        self.extended_attr_icb.new(0, 0)

        self.impl_ident = UDFEntityID()
        self.impl_ident.new(0, b'*genisoimage')

        self.unique_id = 0  # FIXME: let the user set this
        self.len_extended_attrs = 0  # FIXME: let the user set this
        self.len_alloc_descs = len(self.alloc_descs)

        self.extended_attrs = b''

        self._initialized = True

    def set_location(self, new_location, tag_location):
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF File Entry not initialized")

        self.new_extent_loc = new_location
        self.desc_tag.tag_location = tag_location


class UDFFileIdentifierDescriptor(object):
    '''
    A class representing a UDF File Identifier Descriptor.
    '''
    __slots__ = ['_initialized', 'orig_extent_loc', 'new_extent_loc', 'desc_tag', 'file_characteristics', 'len_fi', 'len_impl_use', 'fi', 'isdir', 'isparent', 'icb', 'impl_use', 'file_entry']

    FMT = "=16sHBB16sH"

    def __init__(self):
        self.file_entry = None
        self._initialized = False

    @staticmethod
    def pad(val):
        return (4 * ((val + 3) // 4)) - val

    def parse(self, data, extent, start_extent):
        '''
        Parse the passed in data into a UDF File Identifier Descriptor.

        Parameters:
         data - The data to parse.
         extent - The extent that this descriptor currently lives at.
         start_extent - The extent that this logical block starts at.
        Returns:
         The number of bytes this descriptor consumed.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF File Identifier Descriptor already initialized")

        (desc_tag, file_version_num, self.file_characteristics,
         self.len_fi, icb, self.len_impl_use) = struct.unpack_from(self.FMT, data, 0)

        self.desc_tag = UDFTag()
        self.desc_tag.parse(desc_tag, extent - start_extent, data[16:])
        if self.desc_tag.tag_ident != 257:
            raise pycdlibexception.PyCdlibInvalidISO("File Identifier Descriptor Tag identifier not 257")

        if file_version_num != 1:
            raise pycdlibexception.PyCdlibInvalidISO("File Identifier Descriptor file version number not 1")

        self.isdir = False
        if self.file_characteristics & 0x2:
            self.isdir = True

        self.isparent = False
        if self.file_characteristics & 0x8:
            self.isparent = True

        self.icb = UDFLongAD()
        self.icb.parse(icb)

        start = 38
        end = 38 + self.len_impl_use
        self.impl_use = data[start:end]

        start = end
        end += self.len_fi
        self.fi = data[start:end]

        self.orig_extent_loc = extent
        self.new_extent_loc = None

        self._initialized = True

        return end + UDFFileIdentifierDescriptor.pad(end)

    def is_dir(self):
        '''
        A method to determine if this File Identifier represents a directory.

        Parameters:
         None.
        Returns:
         True if this File Identifier represents a directory, False otherwise.
        '''
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF File Identifier Descriptor not initialized")
        return self.isdir

    def is_parent(self):
        '''
        A method to determine if this File Identifier is a "parent" (essentially ..).

        Parameters:
         None.
        Returns:
         True if this File Identifier is a parent, False otherwise.
        '''
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF File Identifier Descriptor not initialized")
        return self.isparent

    def record(self):
        '''
        A method to generate the string representing this UDF File Identifier Descriptor.

        Parameters:
         None.
        Returns:
         A string representing this UDF File Identifier Descriptor.
        '''
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF File Identifier Descriptor not initialized")

        rec = struct.pack(self.FMT, b'\x00' * 16, 1,
                          self.file_characteristics, self.len_fi,
                          self.icb.record(),
                          self.len_impl_use) + self.impl_use + self.fi + b'\x00' * UDFFileIdentifierDescriptor.pad(struct.calcsize(self.FMT) + self.len_impl_use + self.len_fi)
        return self.desc_tag.record(rec[16:]) + rec[16:]

    def extent_location(self):
        '''
        A method to get the extent location of this UDF File Identifier.

        Parameters:
         None.
        Returns:
         Integer extent location of this UDF File Identifier.
        '''
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF File Identifier not initialized")

        if self.new_extent_loc is None:
            return self.orig_extent_loc
        return self.new_extent_loc

    def new(self, isdir, isparent):
        '''
        A method to create a new UDF File Identifier.

        Parameters:
         None.
        Returns:
         Nothing.
        '''
        if self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF File Identifier already initialized")

        self.desc_tag = UDFTag()
        self.desc_tag.new(257)  # FIXME: we should let the user set serial_number

        self.icb = UDFLongAD()
        self.icb.new(2048, 2)

        self.isdir = isdir
        self.isparent = isparent
        self.file_characteristics = 0
        if self.isdir:
            self.file_characteristics |= 0x2
        if self.isparent:
            self.file_characteristics |= 0x8
        self.len_fi = 0  # FIXME: need to let the user set this
        self.len_impl_use = 0  # FIXME: need to let the user set this
        self.fi = b''  # FIXME: need to let the user set this

        self.impl_use = b''

        self._initialized = True

    def set_location(self, new_location, tag_location):
        if not self._initialized:
            raise pycdlibexception.PyCdlibInternalError("UDF File Identifier not initialized")

        self.new_extent_loc = new_location
        self.desc_tag.tag_location = tag_location
