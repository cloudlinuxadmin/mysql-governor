#!/usr/bin/env python2
# -*- coding: utf-8 -*-

# Copyright © Cloud Linux GmbH & Cloud Linux Software, Inc 2010-2019 All Rights Reserved
#
# Licensed under CLOUD LINUX LICENSE AGREEMENT
# http://cloudlinux.com/docs/LICENSE.TXT

import os
import sys
import argparse
import fnmatch
import re
import io


COPYRIGHT_IGNORE_FILE = "copyright_ignore"
EXTENSIONS_GROUP1 = (".js", ".ts", ".php")
EXTENSIONS_GROUP2 = (".c", ".cpp", ".java", ".h")
EXTENSIONS_GROUP3 = (".sh", ".py")
EXTENSIONS_GROUP4 = (".html",)
SUPPORTED_EXTENSIONS = EXTENSIONS_GROUP1 + EXTENSIONS_GROUP2 + EXTENSIONS_GROUP3 + EXTENSIONS_GROUP4
COPYRIGHT_CONTENT = u"""Copyright © Cloud Linux GmbH & Cloud Linux Software, Inc 2010-2019 All Rights Reserved

Licensed under CLOUD LINUX LICENSE AGREEMENT
http://cloudlinux.com/docs/LICENSE.TXT

AUTHOR--"""


class Copyright:
    """Copyright Class"""


    def __init__(self, ):
        """Initialize class"""
        self.ignore_list = ""


    def generate_copyright_block(self, file_name):
        """Generate copyright block depend on file extension"""
        copyright_lines = COPYRIGHT_CONTENT.split("\n")
        lines_separator = ""
        prefix = ""
        postfix = ""
        if file_name.endswith(EXTENSIONS_GROUP1):
            lines_separator = " * "
            prefix = "/**\n"
            postfix = " */"
        elif file_name.endswith(EXTENSIONS_GROUP2):
            lines_separator = " * "
            prefix = "/*\n"
            postfix = " */"
        elif file_name.endswith(EXTENSIONS_GROUP3):
            lines_separator = "# "
        elif file_name.endswith(EXTENSIONS_GROUP4):
            lines_separator = " " * 4
            prefix = "<!--\n"
            postfix = "-->"
        else:
            print("Warning: Not supported file format: {}".format(file_name))
        for i in range(len(copyright_lines)):
            copyright_lines[i] = lines_separator + copyright_lines[i] + "\n"
        content = "".join(copyright_lines)
        copyright_block = prefix + content + postfix
        return re.sub("(\n|\*|#)\s+\n", "\\1\n", copyright_block).strip()


    def get_regex_pattern(self, file_name):
        """Get pattern to search copyright in file depend on file extension"""
        if file_name.endswith(EXTENSIONS_GROUP1):
            regex_pattern = u"/\*\*\n.*Copyright.*Cloud.*Linux.+(\n.*\*.*){4,6}/"
        elif file_name.endswith(EXTENSIONS_GROUP2):
            regex_pattern = u"/\*\n.*Copyright.*Cloud.*Linux.+(\n.*\*.*){4,6}/"
        elif file_name.endswith(EXTENSIONS_GROUP3):
            regex_pattern = u"#.*Copyright.*Cloud.*Linux.+(\n#.*){3,5}"
        elif file_name.endswith(EXTENSIONS_GROUP4):
            regex_pattern = u"<!--\n.*Copyright.*Cloud.*Linux.+(\n.*){3,5}\n-->"
        return regex_pattern


    def update_copyright(self, file_name):
        """Update copyright for file with copyright block"""
        try:
            copyright_pattern = self.get_regex_pattern(file_name)
            copyright_block = self.generate_copyright_block(file_name)
            with io.open(file_name, "r", encoding="utf8") as f:
                file_content = f.read()
            if re.search(copyright_pattern, file_content):
                new_file_content = re.sub(copyright_pattern, copyright_block, file_content)
                with io.open(file_name, "w", encoding="utf8") as f:
                    f.write(new_file_content)
        except IOError as e:
            print("Warning: can not update copyright for file:{0}. {1}"
                  .format(file_name, sys.exc_info()[1]))


    def add_copyright(self, file_name):
        """Add copyright for files where it missed or update if present"""
        try:
            copyright_pattern = self.get_regex_pattern(file_name)
            copyright_block = self.generate_copyright_block(file_name)
            with io.open(file_name, "r", encoding="utf8") as f:
                file_lines = f.readlines()
                file_content = "".join(file_lines)
            # Update copyright if it already present in file
            if re.search(copyright_pattern, file_content):
                new_file_content = re.sub(copyright_pattern, copyright_block, file_content)
                with io.open(file_name, 'w', encoding="utf8") as f:
                    f.write(new_file_content)
            else:
                # Add copyright block for files where it missed
                lines_before_copyright = ("#!", "<?php", "coding")
                file_begin_lines = file_lines[:2]
                position_for_copyright = 0
                for line in lines_before_copyright:
                    if re.search(line, "".join(file_begin_lines)):
                        position_for_copyright += 1
                encoding = "# -*- coding: utf-8 -*-"
                if file_name.endswith(".py") and not re.search("coding", "".join(file_begin_lines)):
                    copyright_block = encoding + "\n\n" + copyright_block
                if position_for_copyright != 0:
                    copyright_block = "\n" + copyright_block
                file_lines.insert(position_for_copyright, copyright_block + "\n")
                new_file_content = "".join(file_lines)
                with io.open(file_name, 'w', encoding="utf8") as f:
                    f.write(new_file_content)
        except Exception as e:
            print("Warning: can not add copyright to file:{0}. {1}"
                  .format(file_name, sys.exc_info()[1]))


    def is_copyright_present(self, file_name):
        """Check if copyright present in file"""
        try:
            if file_name.endswith(SUPPORTED_EXTENSIONS):
                copyright_pattern = self.get_regex_pattern(file_name)
            with io.open(file_name, "r", encoding="utf8") as f:
                content = f.read()
            if re.search(copyright_pattern, content):
                return True
            return False
        except Exception as e:
            print("Warning: can not check copyright for file file: {}. "
                  .format(file_name, sys.exc_info()[1]))


    def get_files(self, files_extensions):
        """Get all files with supported extension exclude patterns from ignore_list"""
        for root, dirs, files in os.walk("./"):
            dirs[:] = [d for d in dirs
                       if not self.is_file_ignored(os.path.join(root, d))]
            for file_name in files:
                if file_name.endswith(files_extensions):
                    copyright_pattern = self.get_regex_pattern(file_name)
                    file_location = os.path.join(root, file_name)
                    if not self.is_file_ignored(file_location):
                        yield file_location


    def is_file_ignored(self, file_name):
        """Check if file should be ignored"""
        for pattern in self.ignore_list:
            if fnmatch.fnmatch(file_name, pattern):
                return True
        return False


    def get_ignore_list_from_config(self, ignore_config):
        """Read patterns to ignore from file copyright_ignore"""
        try:
            with io.open(ignore_config, "r", encoding="utf8") as conf:
                return conf.read().splitlines()
        except IOError as e:
            print("Can not get ignore list from 'copyright_ignore', {}".format(e))
            sys.exit(1)


    def make_parser(self):
        parser = argparse.ArgumentParser(description="""CHECK COPYRIGHT:
        Check files for copyright.""")
        parser.add_argument("--base-dir", "-d", action="store",
                            help="Directory from which start working, default is current",
                            dest="base_dir", default="./")
        parser.add_argument("--check", "-c", action="store_true",
                            help="Check files for presence copyright")
        parser.add_argument("--update", "-u", action="store_true",
                            help="Update copyright in files")
        parser.add_argument("--add", "-a", action="store_true",
                            help="Add missed or update existing copyright")
        parser.add_argument("--files-extensions", "-f", action="store",
                            help="A list of file extensions to work with. Example: \".py, .js\"")
        parser.add_argument("--ignore-list", "-i", action="store",
                            default="",
                            help="Unix filename patterns to ignore. Like \"somefile.py, somedir/*.js\"\
                            Attention: this option has high priority so it means that \
                            list from file \"copyright_ignore\" will not be included")
        return parser


    def main(self):
        parser = self.make_parser()
        args = parser.parse_args()
        # Check if user give as args
        if not args:
            parser.print_help()
            sys.exit(1)
        # Change base dir to dir from which start walk throw files
        os.chdir(args.base_dir)
        # Get ignore list from file or from arguments
        # Arguments have the highest priority
        if args.ignore_list:
            ignore_list = args.ignore_list.split()
        else:
            ignore_list = self.get_ignore_list_from_config(COPYRIGHT_IGNORE_FILE)
        # Format ignore_list because basic path will always start with "./"
        self.ignore_list = ['./{0}'.format(element) for element in ignore_list]
        # Define files extensions to work with (default is all)
        if args.files_extensions:
            files_extensions = tople(args.files_extensions.split())
        else:
            files_extensions = SUPPORTED_EXTENSIONS
        # Generator
        files_without_copyright = []
        for file_name in self.get_files(files_extensions):
            # Define what to perform depend on parameters
            if args.check:
                if not self.is_copyright_present(file_name):
                    files_without_copyright.append(file_name)
            elif args.update:
                self.update_copyright(file_name)
            elif args.add:
                self.add_copyright(file_name)
            else:
                print("One of the following parameters required: --check, --update, --add")
                sys.exit(1)
        if len(files_without_copyright) > 0:
            print("Copyright was not found for the second files: \n{}"
                  .format("\n".join(files_without_copyright)))
            sys.exit(1)


if __name__ == '__main__':
    Copyright().main()
