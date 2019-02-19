### About "copyright.py" script
Script "copyright.py" we can use to:
 - check files for presence copyright block;
 - update copyright block in files;
 - add copyright block to files;

This script we also use in job for checking copyright block in projects
"http://jenkins.cloudlinux.com:8080/view/WebDev_LVE/job/copyright-test/"
All available options of using script see bellow.

```
usage: copyright.py [-h] [--base-dir BASE_DIR] [--check] [--update] [--add]
                    [--files-extensions FILES_EXTENSIONS]
                    [--ignore-list IGNORE_LIST]

CHECK COPYRIGHT: Check files for copyright.

optional arguments:
  -h, --help            show this help message and exit
  --base-dir BASE_DIR, -d BASE_DIR
                        Directory from which start working, default is current
  --check, -c           Check files for presence copyright
  --update, -u          Update copyright in files
  --add, -a             Add missed or update existing copyright
  --files-extensions FILES_EXTENSIONS, -f FILES_EXTENSIONS
                        A list of file extensions to work with. Example: ".py,
                        .js"
  --ignore-list IGNORE_LIST, -i IGNORE_LIST
                        Unix filename patterns to ignore. Like "somefile.py,
                        somedir/*.js" Attention: this option has high priority
                        so it means that list from file "copyright_ignore"
                        will not be included
```

### Examples of using script
**Example 1:**
This example require file ***"copyright_ignore"***.
***"--base-dir"*** parameter should contain the path to file ***"copyright_ignore"***
```
python copyright.py --check --base-dir="../../../"
```
or
```
python copyright.py --update --base-dir="cpanel-lvemanager/spa"
```
**Example 2:**
In this example ***"copyright_ignore"*** file is NOT required.
```
 python copyright.py --add --base-dir="../../../" --ignore-list="tests/*, *.html"
```
### How to add new project to Job "copyright_test"?
To integrate your project with Job "http://jenkins.cloudlinux.com:8080/view/WebDev_LVE/job/copyright-test/" you need to:
 - add new item to ***"Gerrit Trigger"*** section in Job Configuration (project name should be the  same as in Gerrit)
 - create ***"copyright_ignore"*** file in the project root.
 File example:
```
[root@~]# cat copyright_ignore
protractor-tests/*
katalon-tests/*
tests/*
*bootstrap*
*__init__.py
*jquery*
directadmin/*.html
```