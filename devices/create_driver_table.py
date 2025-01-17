#!/usr/bin/env python3

#############################################################################
#
#  Copyright (C) 2007-2023  Bjarne von Horn, Ingenieurgemeinschaft IgH
#
#  This file is part of the IgH EtherCAT Master.
#
#  The IgH EtherCAT Master is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License version 2, as
#  published by the Free Software Foundation.
#
#  The IgH EtherCAT Master is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
#  Public License for more details.
#
#  You should have received a copy of the GNU General Public License along
#  with the IgH EtherCAT Master; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
#
############################################################################

from os import walk
from os.path import join
from re import compile

DRIVER_MAP=(
    # (subdir, driver name, file prefix)
    (".", "8139too", "8139too"),
    ("stmmac", "dwmac-intel", "dwmac-intel"),
    (".", "e100", "e100"),
    ("e1000", "e1000", "e1000_main"),
    ("e1000e", "e1000e", "netdev"),
    ("genet", "bcmgenet", "bcmgenet"),
    ("igb", "igb", "igb_main"),
    ("igc", "igc", "igc_main"),
    (".", "r8169", "r8169"),
    ("r8169", "r8169", "r8169_main"),
    ("stmmac", "stmmac-pci", "stmmac_pci"),
)


DRIVERS = sorted(set([x[1] for x in DRIVER_MAP]))


def compile_regex(prefix, file_extension):
    """
    :return: Compiled regex to extract Kernel version
    """
    return compile("^" + prefix + "-([\d]+)\.([\d]+)-ethercat\."+file_extension+"$")

def filter_versions(file_list, prefix, file_extension):
    """
    :return: Set of tuples with (major, minor) kernel versions.
    """
    rex = compile_regex(prefix, file_extension)
    ans = set()
    for file in file_list:
        match = rex.match(file)
        if match is None:
            continue
        maj, min = match.group(1, 2)
        ans.add((int(maj), int(min)))
    return ans

def get_all_drivers(drivers_dir):
    """
    Walk through "devices" dir and collect all drivers.

    :return: Dict with (major, minor) kernel version key and set of driver
             names as values.
    """
    files = next(walk(drivers_dir))[2]
    driver_table = {}
    def add_driver(versions, driver):
        for version in versions:
            if not version in driver_table:
                driver_table[version] = set()
            driver_table[version].add(driver)
    for subdir, driver_name, file_prefix in DRIVER_MAP:
        if subdir == ".":
            add_driver(filter_versions(files, file_prefix, "c"), driver_name)
        else:
            tmp_files = next(walk(join(drivers_dir, subdir)))[2]
            add_driver(filter_versions(tmp_files, file_prefix, "c"), driver_name)
    return driver_table

def compute_table(dict_data):
    """
    Create a table based on data generated by get_all_drivers().

    :return: List of rows with "X" or "-", including column and row captions
    (driver name / kernel version).
    """
    keys = sorted(dict_data.keys(), reverse=True)
    ans = [("Kernel", *DRIVERS),]

    def parse_row(key):
        row_set = dict_data[key]
        row = []
        for driver in DRIVERS:
            if driver in row_set:
                row.append("X")
            else:
                row.append("-")
        return row

    for key in keys:
        c = "{}.{: <2}".format(*key)
        ans.append([c] + parse_row(key))

    return ans

def get_max_width(row):
    ans = 0
    for cell in row:
        if len(cell) > ans:
            ans = len(cell)
    return ans

def dump_markdown(table_data):
    """
    Create a markdown table based on data from compute_table().
    """
    width = get_max_width(table_data[0])
    cell_fmt_center = "| {: ^" + str(width) + "} "
    cell_fmt_left = "| {: <" + str(width) + "} "
    cell_fmt_right = "| {: >" + str(width) + "} "
    ans = cell_fmt_left.format(table_data[0][0])
    for cell in table_data[0][1:]:
        ans += cell_fmt_center.format(cell)
    ans += '|\n|-' + "-" * width + ":|"
    for i in range(len(table_data[0]) - 1):
        ans += ':' + "-" * width + ':|'
    for row in table_data[1:]:
        ans += '\n' + cell_fmt_right.format(row[0])
        for cell in row[1:]:
            ans += cell_fmt_center.format(cell)
        ans += '|'
    return ans


if __name__ == "__main__":
    from sys import argv
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(
            "--markdown",
            nargs=1,
            help="Markdown output file",
            type=argparse.FileType("w")
    )
    parser.add_argument(
            "devices_dir",
            nargs=1,
            help="Devices driver source dir"
    )
    args = parser.parse_args(argv[1:])
    table = compute_table(get_all_drivers(args.devices_dir[0]))
    if args.markdown is not None:
        with args.markdown[0] as f:
            f.write(dump_markdown(table))
            f.write('\n')
