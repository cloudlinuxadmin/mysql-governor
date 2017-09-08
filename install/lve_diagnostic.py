#!/usr/bin/python

import os
import pprint
from distutils import version
import rpm

def myExec(str):
    handle = os.popen(str)
    return handle.read()

class LiteSpeed:
    exist = False
    version = 'Unknown'
    suexec = False
    lve = False
    correctArch = False
    def __init__(self):
        self.exist = os.path.isfile('/usr/local/lsws')
        if (os.path.isfile('/usr/local/lsws/bin/litespeed') and len(myExec('ps aux|grep litespeed').split('\n')) > 1):
            self.exist = True
            self.lve = '1' in myExec('grep enableLVE /usr/local/lsws/conf/httpd_config.xml')
            self.suexec = not ('0' in myExec('grep -i phpSuexec\> httpd_config.xml'))
            arch = myExec('file -L /usr/local/lsws/bin/litespeed')
            
    
class ApacheInfo:
    exist = False
    version = 'Unknown'
    mpm = 'Unknown'
    hostinglimits = 'Unknown'
    fcgid = 'Unknown'
    cgi = 'Unknown'
    php_dso = 'Unknown'
    cgid = 'Unknown'
    suPHP = 'Unknown'
    fastcgi = 'Unknown'
    disable_suexec = 'Unknown'
    suexec = 'Unknown'
    moduleInfo = False
    modules = 'Unknown'

    def __init__(self, path):
        self.detect(path)

    def check_version(self):
        if version.LooseVersion(self.version) >= version.LooseVersion("2.2.0"):
            return True
        else:
            print_warning(3001, "Unable to determine list of loaded modules, apache version %s", (self.apache.version))
            return False

    def isModule(self, name):
        return str(self.modules.find(" "+name+"_module") != -1)

    def parseModules(self):
        if self.moduleInfo:
            self.hostinglimits = self.isModule('hostinglimits')
            self.fcgid = self.isModule('fcgid')
            self.php_dso = self.isModule('php5')
            self.cgi = self.isModule('cgi')
            self.cgid = self.isModule('cgid')
            self.suPHP = self.isModule('suPHP')
            self.fastcgi = self.isModule('fastcgi')
            self.disable_suexec = self.isModule('disable_suexec')
            self.suexec = self.isModule('suexec')

    def detect(self, path):
        self.exist = os.path.isfile(path)
        if self.exist:
            tmp = myExec(path + " -V")
            lines = tmp.split('\n')
            for line in lines:
                if line.find('Server version:') != -1:
                    self.version = line[line.find('/')+1:]
                if line.find('Server MPM:') != -1:
                    self.mpm = line[line.rfind(' ')+1:]
            if version.LooseVersion(self.version) > version.LooseVersion('2.2'):
                self.moduleInfo = True
                self.modules = myExec(path + " -M 2>&1")
                self.parseModules()

    def str(self):
        if self.exist:
            str = "Apache verion: "+self.version+", mpm="+self.mpm+\
                ", hostinglimits="+self.hostinglimits+\
                ", cgi="+self.cgi+", cgid="+self.cgid+\
                ", fcgi="+self.fcgid+ ", fastcgi="+self.fastcgi+\
                ", php DSO="+self.php_dso+", suphp="+self.suPHP+\
                ", suexec="+self.suexec+", disable_suexec="+self.disable_suexec

            return str
        
        else:
            return None

def print_error(code, error_str, error_list, solution):
    print "CODE: ", code
    print error_str % error_list
    print "Solution: ", solution

def print_warning(code, error_str, error_list, solution):
    print "WARNING: ", code
    print error_str % error_list

class Kernel:
    version = None
    isLVEKernel = False
    isVZKernel = False
    isLVEEnabled = False
    def __init__(self):
        self.kernelName = myExec('/bin/uname -r').rstrip('\n')
        self.isLVEKernel =  self.kernelName.find('lve')
        if (self.isLVEKernel != -1):
            self.version = self.kernelName[self.isLVEKernel+3:]
            self.isLVEEnabled = os.path.isfile('/proc/lve/list')
        else:
            self.isVZKernel =  'stab' in self.kernelName
    
    def check(self):
        if self.isLVEEnabled:
            if self.isLVEEnabled:
                if version.LooseVersion(self.version) > version.LooseVersion('0.8.28'):
                    return True
                elif version.LooseVersion(self.version) > version.LooseVersion('0.8.0'):
                    print_error(1001, "You are running bugy kernel LVE version %s", (self.version), \
                                    "Upgrade Kernel")
                elif version.LooseVersion(self.version) > version.LooseVersion('0.7.0'):
                    print_error(1002, "You are running old kernel LVE version %s\n That version doesn't support multiple cores per LVE or memory limits", (self.version), "Upgrade Kernel")
                else:
                    print_error(1003, "You are running very old, bugy kernel, LVE version %s", \
                                    (self.version), "Upgrade Kernel")
            else:
                print_error(1004, "LVE is not enabled", (), \
                                "Check /etc/sysconfig/lve file, and make sure lve rpm is installed")
        elif self.isVZKernel:
            print_error(1101, "You are running VZ or OpenVZ", (), \
                            "CloudLinux is not compatible, see http://www.cloudlinux.com/vz-compat.php for more info")
        else:
            print_error(1201, "You are not running CloudLinux kernel. Your kernel is: %s", \
                            (self.version), "Check /boot/grub/grub.conf")

                
    def str(self):
        result = "Kernel: ";
        if self.isLVEEnabled:
            result+="OK ("+self.version+")"
        elif self.isVZKernel:
            result+="VZ ("+self.kernelName+")"
        else:
            result+="Unknown ("+self.kernelName+")"
        return result
  
class CP(object):
    name = "Unknown CP"
    version = "Unknown"
    rpms = None
    kernel = None
    
    def __init__(self, lite):
        if lite!=True:
            self.apache = ApacheInfo('/usr/sbin/apachectl')
            self.rpms = RPMChecker()
            self.kernel = Kernel()

    def str(self):
        return self.name + " " + self.version +" "+self.kernel.str()

    def check(self):
        self.kernel.check()
        self.rpms.check()

    def check_defaults(self):
        print "lve=", str(self.rpms.check_version('lve', '0.8'))
        print 'liblve=', str(self.rpms.check_version('liblve', '0.8'))
        print 'cpanel-lve=', str(self.rpms.check_version('cpanel-lve','0.6'))


        

class CPanel(CP):
    def __init__(self, lite):
        super(CPanel, self).__init__(lite)
        self.name = "cPanel"
        self.version = myExec('/usr/local/cpanel/cpanel -V')
        if lite!=True:
            self.apache = ApacheInfo('/usr/local/bin/apachectl')

    def check_11_30(self):
        self.rpms.check_version('lve-stats', '0.5-17')
        if self.apache.check_version():
            if not self.apache.isModule('hostinglimits'):
                print_error(3011, "hostinglimits module not installed", (), \
                                "Recompile Apache via EasyApache. You can do it either through WHM, or by running /scripts/easyapache --build")

    def check_11_28(self):
        self.check_version('cpanel-lve', '0.2')
        self.check_version('cpanel-lvemanager', '0.2')
        self.check_version('lve-cpanel-plugin', '0.1')
        if self.apache.check_version():
            if not self.apache.isModule('hostinglimits'):
                print_error(3011, "hostinglimits module not installed", (), \
                                "Recompile Apache via EasyApache. You can do it either through WHM, or by running /scripts/easyapache --build")

            
    def check(self):
        super(CPanel, self).check()
        self.rpms.check_err("lve-stats", "0.5-17")
        self.rpms.check_err("liblve-devel", "0.8-20")
        if version.LooseVersion(self.version) >= version.LooseVersion("11.30"):
            self.check_11_30()
        else:
            self.check_11_28()

            
class Plesk(CP):
    def __init__(self, lite):
        super(Plesk, self).__init__(lite)
        self.name = "Plesk"
        tmp = myExec('/bin/cat /usr/local/psa/version')
        self.version = tmp.split(' ')[0]
        if lite!=True:
            self.apache = ApacheInfo('/usr/sbin/apachectl')

class DirectAdmin(CP):
    def __init__(self, lite):
	super(DirectAdmin, self).__init__(lite)
	self.name = "DirectAdmin"
	tmp = myExec('/usr/local/directadmin/directadmin v')
	tmp = tmp.split('\n')
	self.version = 'Unknown'
	if lite!=True:
	    self.apache = ApacheInfo('/usr/sbin/apachectl')
	for item in tmp:
	    if (item.find('Version: DirectAdmin v.')!=-1):
		self.version = item.split('v.')[1].strip()
		break

class HSphere(CP):
    def __init__(self, lite):
	super(HSphere, self).__init__(lite)
	self.name = "H-Sphere"
	tmp = myExec('/bin/cat /hsphere/local/home/cpanel/shiva/psoft_config/HS_VERSION')
	self.version = tmp.split('\n')[1].strip()
	if lite!=True:
	    self.apache = self.get_apache_type()
	
    def get_apache_type(self):
	if os.path.isfile('/hsphere/shared/scripts/scripts.cfg'):
	    f = open('/hsphere/shared/scripts/scripts.cfg')
	    lines = f.readlines()
	    f.close()
	    for item in lines:
		key = item.split('=')[0].strip()
		value = item.split('=')[1].strip()
		if key == 'apache_version':
		    if value == '1':
			return ApacheInfo('/hsphere/shared/apache/bin/httpd')
		    else:
			return ApacheInfo('/hsphere/shared/apache2/bin/apachectl')
	return ApacheInfo('')
	
class iWorx(CP):
    def __init__(self, lite):
        super(iWorx, self).__init__(lite)
        self.name = "InterWorx"
        if lite!=True:
            self.version = self.rpms.find_version("interworx")
            self.apache = ApacheInfo('/usr/sbin/apachectl')

class ISPMgr(CP):
    def __init__(self, lite):
        super(ISPMgr, self).__init__(lite)
        self.name = "ISPManager"
        self.version = "unk"
        if lite!=True:
            self.apache = ApacheInfo('/usr/sbin/apachectl')	

class RPMChecker:
    def __init__(self):
        self.rpmList = myExec('/bin/rpm -qa --qf "%{n} %{v}-%{r}\n"').split('\n')
        # print "Total: "+str(len(self.rpmList))

    def check(self):
        if len(self.rpmList) < 50:
            print_error(2001, "Only %d RPMs detected, RPM database might be corrupted", \
                            (len(self.rpmList)), "Please, contact support")
        self.check_err("lve", "0.8-20")
        self.check_err("lve-utils", "0.6")
        self.check_err("liblve", "0.8-20")

    def check_err(self, name, v):
        res = self.check_version(name, v)
        if res:
            return
        if res is None:
            print_error(2011, "Package %s missing", (name), "Please install the missing package")
        else:
            print_error(2012, "Package %s is older then %s", (name, v), "Please, update the package")

            
    def check_version(self, name, v):
        for line in self.rpmList:
            if line.find(name+' ') == 0:
                pkgVersion = line[len(name) + 1:]
                return version.LooseVersion(pkgVersion) >= version.LooseVersion(v)
        return None
        
    def find_version(self, name):
	ts = rpm.TransactionSet()
	mi = ts.dbMatch('name', str(name))
	for h in mi:
	    return "%s" % (h['version'])        
	return None

        
def get_cp(lite=False):
    if os.path.isfile('/usr/local/cpanel/cpanel'):
        cp = CPanel(lite)
    elif os.path.isfile('/usr/local/psa/version'):
        cp = Plesk(lite)
    elif os.path.isdir('/usr/local/directadmin') and os.path.isfile('/usr/local/directadmin/directadmin'):
	cp = DirectAdmin(lite)
    elif os.path.isfile('/hsphere/local/home/cpanel/shiva/psoft_config/HS_VERSION'):
	cp = HSphere(lite)
    elif os.path.isdir("/usr/local/ispmgr"):
	cp = ISPMgr(lite)
    elif os.path.isdir("/usr/local/mgr5/bin/core"):
	cp = ISPMgr(lite)
    else:
	rpmss = RPMChecker()
	if not (rpmss.find_version("interworx") is None):
	    cp = iWorx(lite)
	else:
    	    cp = CP(lite)  
    return cp


