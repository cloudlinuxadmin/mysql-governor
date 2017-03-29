# coding:utf-8
"""
This module contains helpful utilities to perform common actions
"""
import errno
import os
import re
import shutil
import subprocess
import sys
import urllib
import time
import ConfigParser
from datetime import datetime
from distutils.version import StrictVersion
from glob import glob

__all__ = [
    "mysql_version", "clean_whitespaces", "is_package_installed",
    "download_packages", "remove_packages", "install_packages", "grep",
    "new_lve_ctl", "num_proc", "service", "bcolors", "parse_rpm_name",
    "check_file", "exec_command", "exec_command_out", "get_cl_num",
    "remove_lines", "write_file", "read_file", "rewrite_file", "touch",
    "add_line", "replace_lines", "query_yes_no", "create_mysqld_link",
    "confirm_packages_installation", "is_file_owned_by_package",
    "correct_mysqld_service_for_cl7", "set_debug", "debug_log",
    "shadow_tracing", "add_line_rw_owner", "set_path_environ",
    "correct_remove_notowned_mysql_service_names_cl7",
    "correct_remove_notowned_mysql_service_names_not_symlynks_cl7",
    "disable_and_remove_service",
    "disable_and_remove_service_if_notsymlynk", "check_mysqld_is_alive",
    "get_mysql_log_file", "get_mysql_cnf_value", "makedir_recursive"
]

RPM_TEMP_PATH = "/usr/share/lve/dbgovernor/tmp/governor-tmp"
WHITESPACES_REGEX = re.compile(r"\s+")
TRACE_LOG_FILE = "/usr/share/lve/dbgovernor/install_trace.log"
fDEBUG_FLAG = False


def set_path_environ():
    """
    Set PATH variable
    """
    os.environ[
        "PATH"] += os.pathsep + "/bin" + os.pathsep + "/sbin" + os.pathsep + \
                   "/usr/bin" + os.pathsep + "/usr/sbin" + os.pathsep + \
                   "/usr/local/bin" + os.pathsep + "/usr/local/sbin"


def _trace_calls(frame, event, arg):
    """
    Functions calls tracer (logger)
    """
    if event != "call" or frame.f_back is None:
        return

    func_name = frame.f_code.co_name
    if func_name == "write":
        # Ignore write() calls from print statements
        return

    filename = frame.f_code.co_filename
    if filename.startswith("/opt/alt/python27/"):
        # ignore system functions
        return

    f, level = frame, -1
    while f.f_back is not None:
        level += 1
        f = f.f_back

    def _call_string(f):
        """
        Make trace message
        :param f:
        """
        func_name = f.f_code.co_name
        line_no = f.f_lineno
        filename = f.f_code.co_filename
        i = f.f_locals if func_name != "<module>" else {}
        args_str = ", ".join(["%s=%s" % x for x in i.iteritems()])
        return "%s(%s)|%s:%s" % (func_name, args_str, filename, line_no)

    date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = "[%s] %s%s <- %s\n" % (date, "====" * level, _call_string(frame),
                                  _call_string(frame.f_back))
    add_line_rw_owner(TRACE_LOG_FILE, line)

    return


def shadow_tracing(status=True):
    """
    Enable tracing
    :param status:
    """
    sys.settrace(_trace_calls if status else None)


def set_debug(status=True):
    """
    Enable echo of all exec_command
    """
    global fDEBUG_FLAG
    if status:
        with open(TRACE_LOG_FILE, "w") as f:
            f.write("")

    fDEBUG_FLAG = status


def debug_log(line):
    """
    Debug output log
    """
    global fDEBUG_FLAG
    if fDEBUG_FLAG:
        print line
    else:
        sys.stdout.write_extended(line)


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
    if output == "no":
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
    return out == "yes"


def is_file_owned_by_package(file_path):
    """
    Check is file owned by package
    """
    out = exec_command("rpm -qf %s" % file_path, True, silent=True,
                       return_code=True)
    return out == "yes"


def download_packages(names, dest, beta, custom_download=None):
    """
    Download rpm packages to destination directory
    @param `names` list: list of packages for download
    @param `dest` str: destination folder. concatenate with RPM_TEMP_PATH
    @param `beta` bool: use update-testings repo
    """
    path = "%s/%s" % (RPM_TEMP_PATH, dest)
    if not os.path.exists(path):
        os.makedirs(path, 0755)

    if custom_download is not None and callable(custom_download) \
            and custom_download("+") == "yes":
        names = _custom_download_packages(names, path, custom_download)
    else:
        repo = "" if not beta else "--enablerepo=cloudlinux-updates-testing"
        if exec_command(
                "yum repolist --enablerepo=* --setopt=cl-mysql.skip_if_unavailable=true --setopt=cl-mysql-debuginfo.skip_if_unavailable=true --setopt=cl-mysql-testing.skip_if_unavailable=true |grep mysql -c",
                True, True) != "0":
            repo = "%s --enablerepo=mysqclient" % repo

        exec_command("yumdownloader --destdir=%s --disableexcludes=all %s %s"
                     % (path, repo, " ".join(names)), True, silent=True)

    pkg_not_found = False
    for pkg_name in names:
        pkg_name_split = pkg_name.split('.', 1)[0]
        list_of_rpm = glob("%s/%s*.rpm" % (path, pkg_name_split))
        for i in list_of_rpm:
            print "Package %s was loaded" % i

        if len(list_of_rpm) == 0:
            pkg_not_found = True
            print "WARNING!!!! Package %s was not downloaded" % pkg_name

    return not pkg_not_found


def _custom_download_packages(names, path, downloader):
    """
    Custom download packages logic
    """
    result = []
    for pkg_name in names:
        pkg_url = downloader(pkg_name)
        print "URL %s" % pkg_url
        if pkg_url:
            file_name = "%s/%s.rpm" % (path, pkg_name)
            status = 200
            if len(pkg_url) > 5 and pkg_url[:5] == "file:":
                result.append(os.path.basename(pkg_url[5:]))
                pkg_url = pkg_url[5:]
                if os.path.exists(pkg_url):
                    shutil.copy(pkg_url, path)
                else:
                    status = 404
            else:
                result.append(pkg_name)
                try:
                    response = urllib.urlopen(pkg_url)
                    CHUNK = 16 * 1024
                    with open(file_name, 'wb') as f:
                        while True:
                            chunk = response.read(CHUNK)
                            if not chunk:
                                break
                            f.write(chunk)
                except IOError:
                    status = 404

            print "Downloaded file %s from %s with status %d" % \
                  (file_name, pkg_url, status)
        else:
            result.append(pkg_name)

    return list(set(result))


def remove_packages(packages_list):
    """
    Remove packages from system without dependencies
    """
    # don`t do anything if no packages
    if not packages_list:
        return
    # Try to find server package, because it should be removed first
    new_pkg = []
    for pkg in packages_list:
        if "-server" in pkg:
            print exec_command("rpm -e --nodeps %s" % pkg, True,
                               cmd_on_error="rpm -e --nodeps --noscripts %s" % pkg)
        else:
            new_pkg.append(pkg)
    if len(new_pkg) > 0:
        packages = " ".join(new_pkg)
        print exec_command("rpm -e --nodeps %s" % packages, True,
                           cmd_on_error="rpm -e --nodeps --noscripts %s" % packages)


def confirm_packages_installation(rpm_dir, no_confirm=None):
    """
    Confirm install new packages from rpm files in directory
    @param `no_confirm` bool|None: bool - show info about packages for install
                                   if True - show confirm message.
                                   None - no additional info
    """
    if no_confirm is not None:
        pkg_path = "%s/" % os.path.join(RPM_TEMP_PATH, rpm_dir.strip("/"))
        packages_list = sorted(
            [x.replace(pkg_path, "") for x in glob("%s*.rpm" % pkg_path)])
        print "New packages will be installed: \n    %s" % "\n    ".join(
            packages_list)
        if not no_confirm:
            if not query_yes_no("Continue?"):
                return False

    return True


def install_packages(rpm_dir, is_beta, installer=None, abs_path=False):
    """
    Install new packages from rpm files in directory
    @param `no_confirm` bool|None: bool - show info about packages for install
                                   if True - show confirm message.
                                   None - no additional info
    """
    repo = ""
    if is_beta:
        repo = "--enablerepo=cloudlinux-updates-testing"

    if not abs_path:
        pkg_path = os.path.join(RPM_TEMP_PATH, rpm_dir.strip("/"))
    else:
        pkg_path = rpm_dir.rstrip("/")

    if installer is None:
        list_for_install = []
        is_server_found = []
        list_of_rpm = glob("%s/*.rpm" % pkg_path)
        for found_package in list_of_rpm:
            if "-server" in found_package or "-meta-" in found_package:
                is_server_found.append(found_package)
            else:
                list_for_install.append(found_package)
        exec_command_out(
            "yum install %s --disableexcludes=all --nogpgcheck -y %s" % (
                repo, " ".join(list_for_install)))
        if is_server_found != "":
            exec_command_out(
                "yum clean all --enablerepo=cloudlinux-updates-testing")
            exec_command_out(
                "yum install %s --disableexcludes=all --nogpgcheck -y %s" % (
                    repo, " ".join(is_server_found)))
    else:
        is_server_found = ""
        list_of_rpm = glob("%s/*.rpm" % pkg_path)
        for found_package in list_of_rpm:
            if "-server" in found_package:
                is_server_found = found_package
            else:
                print "Going to install %s" % found_package
                installer(found_package)
        if is_server_found != "":
            print "Going to install %s" % is_server_found
            installer(is_server_found)
    return True


def new_lve_ctl(version1):
    """
    Check version
    :param version1:
    """
    return StrictVersion("1.4") <= StrictVersion(version1)


def num_proc(s):
    """
    Convert to int
    :param s:
    """
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
        end_name = name
        found_path = ""
        if name == "mysql" or name == "mysqld":
            if os.path.exists("/usr/lib/systemd/system/mysqld.service"):
                end_name = "mysqld"
            elif os.path.exists("/usr/lib/systemd/system/mysql.service"):
                end_name = "mysql"
            elif os.path.exists("/etc/systemd/system/mysql.service"):
                end_name = "mysql"
                found_path = "/etc/systemd/system/mysql.service"
            elif os.path.exists("/etc/systemd/system/mysqld.service"):
                end_name = "mysqld"
                found_path = "/etc/systemd/system/mysqld.service"
        if os.path.exists("/usr/lib/systemd/system/%s.service" % end_name) or (
                    found_path != ""):
            exec_command_out(
                "/bin/systemctl %s %s.service" % (action, end_name))
        else:
            if name == "mysql" or name == "mysqld":
                if os.path.exists("/etc/init.d/mysql"):
                    end_name = "mysql"
                elif os.path.exists("/etc/init.d/mysqld"):
                    end_name = "mysqld"
            exec_command_out("/sbin/service %s %s" % (end_name, action))


def check_file(path):
    """
    Check file exists or exit with error
    """
    if not os.path.exists(path):
        print "Installtion error file ---%s---- does not exists" % path
        sys.exit(1)

    return True


def exec_command(command, as_string=False, silent=False, return_code=False,
                 cmd_on_error=""):
    """
    Advanced system exec call
    """
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    out, err = p.communicate()
    debug_log("Executed command %s with retcode %d\n" % (command, p.returncode))

    if return_code:
        if p.returncode == 0:
            return "yes"
        else:
            return "no"

    if p.returncode != 0 and not silent:
        print >> sys.stderr, "Execution command: %s error" % command
        if cmd_on_error != "":
            return exec_command(cmd_on_error, as_string, silent, return_code,
                                "")
        raise RuntimeError("%s\n%s" % (out, err))

    if as_string:
        return out.strip()

    return [x.strip() for x in out.split("\n") if x.strip()]


def exec_command_out(command):
    """
    Simple system exec call
    """
    os.system(command)
    debug_log("Executed command %s with retcode NN\n" % command)


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


def add_line_rw_owner(path, line):
    """
    Add line to file
    """
    with open(path, "a") as f:
        f.write("%s\n" % line.strip())
    os.chmod(path, 0o600)


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
    """
    Unix touch analog
    :param fname:
    :return:
    """
    try:
        os.utime(fname, None)
    except (IOError, OSError):
        open(fname, 'a').close()


class bcolors(object):
    """
    Colorful stdout
    """
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

    def disable(self):
        """
        Set no colors
        """
        self.HEADER = ''
        self.OKBLUE = ''
        self.OKGREEN = ''
        self.WARNING = ''
        self.FAIL = ''
        self.ENDC = ''


def query_yes_no(question, default=None):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True, "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write("%s%s" % (question, prompt))
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
    cl-MySQL packages brings only /etc/init.d/mysql file,
    mysqld should be created
    """
    cl_ver = get_cl_num()
    if cl_ver < 7:
        link_name = "/etc/init.d/%s" % link
        if not os.path.exists(link_name):
            if not os.path.islink(link_name):
                os.symlink("/etc/init.d/%s" % to_file, link_name)


def correct_mysqld_service_for_cl7(mysql_type):
    """
    For cl7 check symlink pathes
    """
    name = "mysqld"
    if mysql_type in ["mysql50", "mysql51", "mysql55", "mysql56", "mysql57", "auto"]:
        name = "mysqld"
    elif mysql_type in ["mariadb55", "mariadb100", "mariadb101"]:
        name = "mariadb"
    cl_ver = get_cl_num()
    if cl_ver == 7:
        service_name = name + ".service"
        if check_mysqld_is_alive():
            service("stop", name)
            time.sleep(10)
            if os.path.exists("/etc/rc.d/init.d/mysql") and check_mysqld_is_alive():
                exec_command_out("service --skip-redirect mysql stop")
                time.sleep(10)
        if os.path.exists("/usr/lib/systemd/system/" + service_name):
            need_enable = False
            if name == "mysqld" or name == "mariadb":
                if os.path.exists("/etc/systemd/system/mariadb.service"):
                    os.unlink("/etc/systemd/system/mariadb.service")
                    need_enable = True
            if os.path.exists("/etc/systemd/system/mysql.service"):
                if os.path.islink("/etc/systemd/system/mysql.service"):
                    if os.path.realpath("/etc/systemd/system/mysql.service") != "/usr/lib/systemd/system/" + service_name:
                        os.unlink("/etc/systemd/system/mysql.service")
                        need_enable = True
                else:
                    os.unlink("/etc/systemd/system/mysql.service")
                    need_enable = True
            else:
                need_enable = True
            if name == "mysqld":
                if os.path.exists("/etc/systemd/system/mysqld.service"):
                    os.unlink("/etc/systemd/system/mysqld.service")
                    need_enable = True
            else:
                if os.path.exists("/etc/systemd/system/mysql.service"):
                    if os.path.islink("/etc/systemd/system/mysql.service"):
                        if os.path.realpath("/etc/systemd/system/mysql.service") != "/usr/lib/systemd/system/" + service_name:
                            os.unlink("/etc/systemd/system/mysql.service")
                            need_enable = True
                    else:
                        os.unlink("/etc/systemd/system/mysql.service")
                        need_enable = True
                else:
                    need_enable = True
            if need_enable:
                exec_command_out("systemctl enable %s" % service_name)
            if not check_mysqld_is_alive():
                service("start", name)


def disable_and_remove_service(service_path):
    """
    Disable systemd service
    :param service_path:
    :return:
    """
    if os.path.exists(service_path):
        service_name = os.path.basename(service_path)
        if service_name != "" and is_file_owned_by_package(
                service_path) == False:
            disable_service(os.path.splitext(service_name)[0])
            os.unlink(service_path)


def correct_remove_notowned_mysql_service_names_cl7():
    """
    After any MySQL-server removing should not be any mysql
    or mysqld or mariadb service files
    """
    cl_ver = get_cl_num()
    if cl_ver == 7:
        disable_and_remove_service("/usr/lib/systemd/system/mysqld.service")
        disable_and_remove_service("/usr/lib/systemd/system/mysql.service")
        disable_and_remove_service("/usr/lib/systemd/system/mariadb.service")

        exec_command_out("systemctl daemon-reload")


def disable_and_remove_service_if_notsymlynk(service_path):
    """
    Disable not symlinked systemd service
    :param service_path:
    :return:
    """
    if os.path.exists(service_path):
        service_name = os.path.basename(service_path)
        if service_name != "" and is_file_owned_by_package(
                service_path) == False and not os.path.islink(service_path):
            disable_service(os.path.splitext(service_name)[0])
            os.unlink(service_path)


def correct_remove_notowned_mysql_service_names_not_symlynks_cl7():
    """
    After any MySQL-server removing should not be any mysql
    or mysqld or mariadb service files
    """
    cl_ver = get_cl_num()
    if cl_ver == 7:
        disable_and_remove_service_if_notsymlynk(
            "/etc/systemd/system/mysqld.service")
        disable_and_remove_service_if_notsymlynk(
            "/etc/systemd/system/mysql.service")


def parse_rpm_name(name):
    """
    Split rpm package name
    """
    result = exec_command(("rpm --queryformat \"%%{NAME} %%{VERSION}"
                           " %%{RELEASE} %%{ARCH}\" -q %s") % name, True) \
        .split(' ', 4)
    if len(result) >= 4:
        return [result[0], result[1], result[2], result[3]]

    return []


def disable_service(name):
    """
    systemd disabling service, Before disabling MySQL or MariaDB should be stopped.
    """
    cl_ver = get_cl_num()
    if cl_ver == 7:
        service_name = name + ".service"
        if os.path.exists("/usr/lib/systemd/system/" + service_name):
            #Bingo! We found service from one step
            service("stop", name)
            time.sleep(10)
            if check_mysqld_is_alive():
                if os.path.exists("/etc/rc.d/init.d/mysql"):
                    exec_command_out("service --skip-redirect mysql stop")
                    time.sleep(10)
            exec_command_out("systemctl disable %s" % service_name)
        else:
            #We are not so lucky. Looks like name - it is only alias. Try to figure out what is real service name
            service_name = ""
            real_name = ""
            if name == "mysql":
            #It can be mysql.service or mysqld.service or mariadb.service
                if os.path.exists("/usr/lib/systemd/system/mysql.service"):
                    service_name = "mysql.service"
                    real_name = "mysql"
                elif os.path.exists("/usr/lib/systemd/system/mysqld.service"):
                    service_name = "mysqld.service"
                    real_name = "mysqld"
                elif os.path.exists("/usr/lib/systemd/system/mariadb.service"):
                    service_name = "mariadb.service"
                    real_name = "mariadb"
            elif name == "mysqld":
            #It can be mysqld.service or mariadb.service
                if os.path.exists("/usr/lib/systemd/system/mysqld.service"):
                    service_name = "mysqld.service"
                    real_name = "mysqld"
                elif os.path.exists("/usr/lib/systemd/system/mariadb.service"):
                    service_name = "mariadb.service"
                    real_name = "mariadb"
            elif name == "mariadb":
            #It can be mariadb.service
                if os.path.exists("/usr/lib/systemd/system/mariadb.service"):
                    service_name = "mariadb.service"
                    real_name = "mariadb"
            if service_name != "":
                service("stop", real_name)
                time.sleep(10)
                if check_mysqld_is_alive():
                    if os.path.exists("/etc/rc.d/init.d/mysql"):
                        exec_command_out("service --skip-redirect mysql stop")
                        time.sleep(10)
                exec_command_out("systemctl disable %s" % service_name)


def check_mysqld_is_alive():
    """
    Check if mysql process is alive
    """
    check_mysql = exec_command("ps -Af | grep -v grep | grep mysqld | "
                               "egrep -e 'datadir|--daemonize'",
                               True, silent=True)
    check_mysql57_mariadb101 = exec_command("ps -Af | grep -v grep | grep /usr/sbin/mysqld",
                               True, silent=True)
    check_mysqld = exec_command("/usr/bin/mysql -e \"select 1\" "
                                "2>&1 1>/dev/null", True, silent=True,
                                        return_code=True)
    if check_mysql57_mariadb101 or check_mysql or check_mysqld == "yes":
        return True
    return False


def get_mysql_cnf_value(section, name):
    """
    Get value from my.cnf
    """
    if os.path.exists("/etc/my.cnf"):
        configParser = ConfigParser.RawConfigParser(allow_no_value=True)
        configFilePath = r'/etc/my.cnf'
        try:
            configParser.read(configFilePath)
            return configParser.get(section, name)
        except:
            return ""
    return ""


def get_mysql_log_file():
    """
    Get path to mysqld.log file
    """
    file_path = get_mysql_cnf_value("mysqld", "log-error")
    if file_path == "":
        file_path = get_mysql_cnf_value("mysqld_safe", "log-error")
    if file_path == "":
        file_path = "/var/log/mysqld.log"
    return file_path


def makedir_recursive(path):
    """
    Create directory recursively
    :param path:
    :return:
    """
    path = os.path.dirname(os.path.abspath(path))
    try:
        os.makedirs(path)
        return True
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            return True
        else:
            return False


def patch_governor_config(username, password):
    """

    :param username:
    :param password:
    :return:
    """
    with open("/etc/container/mysql-governor.xml", 'rb') as governor_config:
        contents = governor_config.readlines()

    for index, line in enumerate(contents):
        if 'connector' in line and 'login=' not in line:
            contents[index] = '<connector login="{login}" password="{password}" prefix_separator="_"/>\n'.format(login=username, password=password)

    with open("/etc/container/mysql-governor.xml", 'wb') as governor_config:
        governor_config.writelines(contents)
