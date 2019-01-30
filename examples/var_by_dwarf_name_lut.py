#-------------------------------------------------------------------------------
# elftools example: var_by_dwarf_name_lut.py
#
# An example of getting DIEs describing a global variable with custom type
# using .debug_pubnames and .debug_pubtupes sections.
#
# Efimov Vasiliy (real@ispras.ru)
# This code is in the public domain
#-------------------------------------------------------------------------------
from __future__ import print_function
import sys

# If pyelftools is not installed, the example can also run from the root or
# examples/ dir of the source distribution.
sys.path[0:0] = ['.', '..']

from elftools.elf.elffile import ELFFile


def process_file(filename):
    print('Processing file:', filename)
    with open(filename, 'rb') as f:
        elffile = ELFFile(f)

        if not elffile.has_dwarf_info():
            print('  file has no DWARF info')
            return

        # get_dwarf_info returns a DWARFInfo context object, which is the
        # starting point for all DWARF-based processing in pyelftools.
        dwarfinfo = elffile.get_dwarf_info()

        if not (dwarfinfo.debug_pubtypes_sec and dwarfinfo.debug_pubnames_sec):
            print('  file has no .debug_pubtypes and/or .debug_pubnames')
            return

        # Using .debug_pubtypes section it's possible to lookup Compile Unit
        # with Debugging Information Entry describing a global variable.

        pubnames = dwarfinfo.get_pubnames()
        cu_offset, die_global_offset = pubnames["global"]

        print('  Variable "global" is described by DIE at offset %u in CU at'
              ' offset %u' % (die_global_offset, cu_offset))

        # It's possible to get CU using `dwarfinfo._parse_CU_at_offset`.
        # But that method is considered private. Hence, we iterate all CUs
        # until required one is found
        for cu in dwarfinfo.iter_CUs():
            if cu.cu_offset == cu_offset:
                # It's CU we looking for.
                break
        else:
            print('  no CU starting at offset %u, is there an error in'
                  ' .debug_pubpubnames' % cu_offset)
            return

        die_cu_offset = die_global_offset - cu_offset

        die = cu.get_DIE_at_offset(die_cu_offset)
        # This DIE describing a variable with name "global".
        # Now, get its type.
        type_offset = die.attributes["DW_AT_type"].value

        # Note that this code assumes that the type defined in same CU with
        # the variable. This case, offset is given relative to that CU.
        # Technically, the attribute "DW_AT_type" has form "DW_FORM_refN"
        # where N in [1, 2, 4, 8].
        type_die = cu.get_DIE_at_offset(type_offset)

        type_name = type_die.attributes["DW_AT_name"].value

        print('  Variable "global" has type "%s"' % type_name.decode("utf-8"))

if __name__ == '__main__':
    if sys.argv[1] == '--test':
        for filename in sys.argv[2:]:
            process_file(filename)
