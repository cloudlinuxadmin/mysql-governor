#coding:utf-8
import os
import re
import subprocess
import sys
import urllib
from distutils.version import StrictVersion
from glob import glob


__all__ = ["mysql_version", "clean_whitespaces", "is_package_installed",
           "download_packages", "remove_packages", "install_packages", "grep",
           "new_lve_ctl", "num_proc", "service", "bcolors",
           "check_file", "exec_command", "exec_command_out", "get_cl_num",
           "remove_lines", "write_file", "read_file", "rewrite_file", "touch",
           "add_line", "replace_lines", "getItem", "verCompare", "query_yes_no",
           "confirm_packages_installation", "is_file_owned_by_package", "create_mysqld_link",
           "correct_mysqld_service_for_cl7", "set_debug", "parse_rpm_name"]


RPM_TEMP_PATH = "/usr/share/lve/dbgovernor/tmp/governor-tmp"
WHITESPACES_REGEX = re.compile("\s+")
fDEBUG_FLAG = False

def set_debug():
    """
    Enable echo of all exec_command
    """
    global fDEBUG_FLAG
    fDEBUG_FLAG = True

def mysql_version():
    """
    Detect current installed MySQL version
    """
    # path = exec_command("which mysqld", True, silent=True)
    path = exec_command("which mysqld_safe", True, silent=True)
    if not path:
        return None

    output = exec_command("""rpm -qf --qf="%%{name} %%{version}" %s""" % path,
                          True, silent=True, return_code=True)
    if output==False:
        return None

    output = exec_command("""rpm -qf --qf="%%{name} %%{version}" %s""" % path,
                          True, silent=True)

    name, version = output.lower().split(" ")
    if name.startswith("cl-mariadb"):
        name = "mariadb"
    elif name.startswith("cl-mysql"):
        name = "mysql"
    else:
        # non-CL sql package
        return "auto"

    return "%s%s" % (name, "".join(version.split(".")[:2]))


def clean_whitespaces(data):
    """
    Remove whitespaces duplicates
    """
    return WHITESPACES_REGEX.sub(" ", data)


def is_package_installed(name):
    """
    Check is package installed
    """
    out = exec_command("rpm -q %s" % name, True, silent=True, return_code=True)
    return out=="yes"

def is_file_owned_by_package(file_path):
    """
    Check is file owned by package
    """
    out = exec_command("rpm -qf %s" % file_path, True, silent=True, return_code=True)
    return out=="yes"

def download_packages(names, dest, beta, custom_download = False):
    """
    Download rpm packages to destination directory
    @param `names` list: list of packages for download
    @param `dest` str: destination folder. concatenate with RPM_TEMP_PATH
    @param `beta` bool: use update-testings repo
    """
    path = "%s/%s" % (RPM_TEMP_PATH, dest)
    if not os.path.exists(path):
        os.makedirs(path, 0755)

    if custom_download!=False and custom_download("+")=="yes":
        for pkg_name in names:
            pkg_url = custom_download(pkg_name)
            if pkg_url!="":
                file_name = ("%s/%s.rpm") % (path, pkg_name)
                status  = 200
                try:
                    response = urllib.urlopen(pkg_url)
                    CHUNK = 16 * 1024
                    with open(file_name, 'wb') as f:
                        while True:
                            chunk = response.read(CHUNK)
                            if not chunk: break
                            f.write(chunk)
                except IOError:
                    status = 404

                print("Downloaded file %s from %s with status %d" % (file_name, pkg_url, status) )
    else:
        repo = "" if not beta else "--enablerepo=cloudlinux-updates-testing"
        if exec_command("yum repolist|grep mysql -c", True, True) != "0":
            repo = "%s --enablerepo=mysqclient" % repo

        exec_command(("yumdownloader --destdir=%s --disableexcludes=all %s %s")
                  % (path, repo, " ".join(names)), True, silent=True)
    pkg_not_found = False
    for pkg_name in names:
        pkg_name_split = pkg_name.split('.',1)[0]
        list_of_rpm = glob(("%s/%s*.rpm") % (path, pkg_name_split))
        for i in list_of_rpm:
            print("Package %s was loaded" % i)
        if len(list_of_rpm)==0:
            pkg_not_found = True
            print("WARNING!!!! Package %s was not downloaded" % pkg_name)
    if pkg_not_found == True:
        return False
    else:
        return True

def remove_packages(packages_list):
    """
    Remove packages from system without dependencies
    """
    # don`t do anything if no packages
    if not packages_list:
        return

    packages = " ".join(packages_list)
    print exec_command("rpm -e --nodeps %s" % packages, True)

def confirm_packages_installation(rpm_dir,  no_confirm=None):
    """
    Confirm install new packages from rpm files in directory
    @param `no_confirm` bool|None: bool - show info about packages for install
                                   if True - show confirm message. 
                                   None - no additional info
    """

    pkg_path = "%s/" % os.path.join(RPM_TEMP_PATH, rpm_dir.strip("/"))
    if no_confirm is not None:
        packages_list = sorted([x.replace(pkg_path, "") for x in glob("%s*.rpm" % pkg_path)])
        print "New packages will be installed: \n    %s" % "\n    ".join(packages_list)
        if not no_confirm:
            if not query_yes_no("Continue?"):
                return False

    return True

def install_packages(rpm_dir, is_beta, no_confirm=None):
    """
    Install new packages from rpm files in directory
    @param `no_confirm` bool|None: bool - show info about packages for install
                                   if True - show confirm message. 
                                   None - no additional info
    """
    repo = ""
    if is_beta:
        repo = "--enablerepo=cloudlinux-updates-testing"

    pkg_path = "%s/" % os.path.join(RPM_TEMP_PATH, rpm_dir.strip("/"))

    print exec_command("yum install %s --disableexcludes=all --nogpgcheck -y %s*.rpm" % (repo, pkg_path), True)
    return True


def new_lve_ctl(version1):
    return StrictVersion("1.4") <= StrictVersion(version1)
    

def num_proc(s):
    try:
        return int(s)
    except ValueError:
        return 0


def service(action, *names):
    """
    Manage system service
    @param `action` str: action type (start|stop|restart|etc...)
    @param `names` tuple: list with services
    """
    for name in names:
        if os.path.exists("/usr/lib/systemd/system/%s.service" % name):
            exec_command_out("/bin/systemctl %s %s.service" % (action, name))
        else:
            exec_command_out("/sbin/service %s %s" % (name, action))


def check_file(path):
    """
    Check file exists or exit with error
    """
    if not os.path.exists(path):
        print "Installtion error file ---%s---- does not exists" % path
        sys.exit(1)

    return True


def exec_command(command, as_string=False, silent=False, return_code=False):
    """
    """
    global fDEBUG_FLAG
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    out, err = p.communicate()
    if fDEBUG_FLAG==True:
        print("Executed command %s with retcode %d" % (command, p.returncode))
    if return_code==True:
        if p.returncode == 0:
            return "yes"
        else:
            return "no"

    if p.returncode != 0 and not silent:
        print >>sys.stderr, "Execution command: %s error" % command
        raise RuntimeError("%s\n%s" % (out, err))

    if as_string:
        return out.strip()

    return [x.strip() for x in out.split("\n") if x.strip()]

    
def exec_command_out(command):
    global fDEBUG_FLAG
    os.system(command)
    if fDEBUG_FLAG==True:
        print("Executed command %s with retcode NN" % (command))

def get_cl_num():
    """
    Get CL version number
    """
    with open("/etc/redhat-release", "r") as f:
        words = f.read().strip().split(" ")

    for word in words:
        try:
            return int(float(word))
        except ValueError:
            pass

    return None


def remove_lines(path, value):
    """
    Remove lines with value string from file
    """
    if not os.path.isfile(path):
        return False

    with open(path, "r+") as f:
        content = []
        for line in f:
            if value not in line:
                content.append(line)
        rewrite_file(f, content)

    return True


def write_file(path, content):
    """
    Write content to path
    """
    with open(path, "w") as f:
        f.write(content)


def read_file(path):
    """
    read file content
    """
    with open(path, "r") as f:
        return f.read()


def rewrite_file(f, content):
    """
    Rewrite file content
    """
    f.seek(0)
    f.truncate()
    f.write("".join(content))


def add_line(path, line):
    """
    Add line to file
    """
    with open(path, "a") as f:
        f.write("%s\n" % line.strip())


def grep(path, pattern, regex=False):
    """
    grep path or list of lines for pattern
    """
    if isinstance(path, basestring):
        if not os.path.isfile(path):
            return False
        iterator = open(path, "r")
    elif isinstance(path, (list, tuple)):
        iterator = path
    else:
        return False

    if regex:
        pattern = re.compile(pattern)

    result = []
    for line in iterator:
        line = line.rstrip()
        if not regex:
            if pattern in line:
                result.append(line)
        else:
            if pattern.match(line):
                result.append(line)

    if isinstance(iterator, file):
        iterator.close()

    return result


def replace_lines(path, pattern, replace):
    """
    Replace file lines with pattern to replace value 
    """
    lines = []
    with open(path, "w+") as f:
        for line in f:
            if pattern in line:
                line.replace(pattern, replace)
            lines.append(line)

        rewrite_file(f, lines)


def touch(fname):
    try:
        os.utime(fname, None)
    except:
        open(fname, 'a').close()


def getItem(txt1, txt2, op):
    try:
        i1 = int(txt1)
    except ValueError:
        i1 = -1
    try:
        i2 = int(txt2)
    except ValueError:
        i2 = -1
    if i1 == -1 or i2 == -1:
        if op == 0:
            return txt1>txt2
        else:
            return txt1<txt2
    else:
        if op == 0:
            return i1>i2
        else:
            return i1<i2

    
#Compare version of types xx.xx.xxx... and yyy.yy.yy.y..
#if xxx and yyy is numbers, than comapre as numbers
#else - comapre as strings
def verCompare (base, test):
    base = base.split(".")
    test = test.split(".")
    if(len(base)>len(test)):
        ln = len(test)
    else:
        ln = len(base)
    for i in range(ln):
        if getItem(base[i],test[i],0):
            return 1
        if getItem(base[i],test[i],1):
            return -1
    if len(base)==len(test):    
        return 0
    elif len(base)>len(test):
        return 1
    else:
        return 0


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

    def disable(self):
        self.HEADER = ''
        self.OKBLUE = ''
        self.OKGREEN = ''
        self.WARNING = ''
        self.FAIL = ''
        self.ENDC = ''


def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")

def create_mysqld_link(link, to_file):
    """
    cl-MySQL packages brings only /etc/init.d/mysql file, mysqld should be created
    """
    cl_ver = get_cl_num()
    if cl_ver<7:
        link_name = "/etc/init.d/" + link
        if not os.path.exists(link_name):
            if not os.path.islink(link_name):
                os.symlink("/etc/init.d/" + to_file, link_name)
                
def correct_mysqld_service_for_cl7(name):
    """
    For cl7 /etc/init.d/mysql should be removed if exists
    """
    cl_ver = get_cl_num()
    if cl_ver==7:
        link_name = "/etc/init.d/" + name
        if os.path.exists(link_name):
            os.unlink(link_name)
        elif os.path.islink(link_name):
            os.unlink(link_name)

def parse_rpm_name(name):
    """
    Split rpm package name
    """
    result = exec_command("/usr/bin/rpm --queryformat \"%%{NAME} %%{VERSION} %%{RELEASE} %%{ARCH}\" -q %s" % name, True).split(' ', 4)
    if len(result)>=4:
        return [result[0], result[1], result[2], result[3]]
    return []
    