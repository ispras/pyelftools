#-------------------------------------------------------------------------------
# elftools: dwarf/abbrevtable.py
#
# DWARF abbreviation table
#
# Eli Bendersky (eliben@gmail.com)
# This code is in the public domain
#-------------------------------------------------------------------------------
from ..common.utils import struct_parse, dwarf_assert


class AbbrevTable(object):
    """ Represents a DWARF abbreviation table.
    """
    def __init__(self, structs, stream, offset):
        """ Create new abbreviation table. Parses the actual table from the
            stream and stores it internally.

            structs:
                A DWARFStructs instance for parsing the data

            stream, offset:
                The stream and offset into the stream where this abbreviation
                table lives.
        """
        self.structs = structs
        self.stream = stream
        self.offset = offset

        # A lazy parsing is involved. When an unknown code is requested, the
        # parser is being adjusted until the code is met.
        self._parser_state = self._abbrev_table_parser()
        self._abbrev_map = {}

    def get_abbrev(self, code):
        """ Get the AbbrevDecl for a given code. Raise KeyError if no
            declaration for this code exists.
        """
        _map = self._abbrev_map
        # check if the code has been already parsed
        if code in _map:
            return _map[code]

        # look for the code in the rest of the table
        for decl in self._parser_state:
            _map[decl.code] = decl
            if decl.code == code:
                return decl

        # parsing ended, no such code found
        raise KeyError(code)

    def _abbrev_table_parser(self):
        """ Parse the abbrev table from the stream
        """
        stream = self.stream
        offset = self.offset
        while True:
            stream.seek(offset)
            decl_code = struct_parse(
                struct=self.structs.Dwarf_uleb128(''),
                stream=self.stream)
            if decl_code == 0:
                break
            declaration = struct_parse(
                struct=self.structs.Dwarf_abbrev_declaration,
                stream=self.stream)
            # Stream offset can be adjusted between yields. So, preserve last
            # offset locally.
            offset = stream.tell()
            yield AbbrevDecl(decl_code, declaration)


class AbbrevDecl(object):
    """ Wraps a parsed abbreviation declaration, exposing its fields with
        dict-like access, and adding some convenience methods.

        The abbreviation declaration represents an "entry" that points to it.
    """
    def __init__(self, code, decl):
        self.code = code
        self.decl = decl

    def has_children(self):
        """ Does the entry have children?
        """
        return self['children_flag'] == 'DW_CHILDREN_yes'

    def iter_attr_specs(self):
        """ Iterate over the attribute specifications for the entry. Yield
            (name, form) pairs.
        """
        for attr_spec in self['attr_spec']:
            yield attr_spec.name, attr_spec.form

    def __getitem__(self, entry):
        return self.decl[entry]
