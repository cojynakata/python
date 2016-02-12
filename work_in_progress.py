#!/usr/bin/python

import subprocess
import os
import platform
import math
import sys
import re

class colour:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def sudo_check():
    euid = os.geteuid()
    if euid != 0:
        args = ['sudo - ', sys.executable] + sys.argv + [os.environ]
        os.execlpe('sudo', *args)

    if euid != 0:
        print "Sorry, you need to have root privileges to run this script"
        sys.exit()
    else:
        os.system('cls' if os.name == 'nt' else 'clear')
        print colour.OKGREEN + "You are running this script as root" + colour.ENDC

def print_header():
    print " ------------------------------------------------------------- "                                                  
    print "  _____ _____    _____ _____    _____ _____ _____ _____ ____"
    print " |_   _|     |  | __  |   __|  |   | |  _  |     |   __|    \\"
    print "   | | |  |  |  | __ -|   __|  | | | |     | | | |   __|  |  |"
    print "   |_| |_____|  |_____|_____|  |_|___|__|__|_|_|_|_____|____/ "
    print ""
    print " ------------------------------------------------------------- "  
def python_version_check():
    min_ver = (2, 6, 0)
    if sys.version_info < min_ver:
        print colour.FAIL + ("Python version: %s" % sys.version.split('\n')[0])
        print "You need Python 2.6 or greater in order to run this script" + colour.ENDC
        sys.exit()
    else:
        print colour.OKGREEN + ("Python version: %s" % sys.version.split('\n')[0]) + colour.ENDC


def check_if_running(process):
    if sys.version_info < (2,7,0):
        command = 'pidof ' + process
        pid_output = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        pid = pid_output.stdout.read().splitlines()
    elif sys.version_info >= (2,7,0):
        from subprocess import check_output
        try:
            pid = check_output(["pidof", process]).split()
        except:
            pid = []

    if len(pid) > 0:
        return 1
    else:
        return 0


def os_check():
    global os_platform, os_distro, os_version
    supported_os_platform = ['Linux']
    supported_os_dist_debian = ['LinuxMint', 'debian', 'Ubuntu']
    supported_os_dist_fedora = ['fedora', 'redhat', 'centos', 'Red Hat Enterprise Linux Server', 'CentOS']
    supported_os_version_debian = [7, 8, 12, 14, 15, 17]
    supported_os_version_fedora = [6, 7]
    # getting the running OS details
    os_platform = platform.system()
    os_distro = platform.linux_distribution()[0]
    os_version = int(float(platform.linux_distribution()[1]))

    # checking the OS type
    if os_platform not in supported_os_platform:
        print colour.FAIL + ("Sorry, you are running on the %s platform which is NOT supported." % (os_platform)) + colour.ENDC
        sys.exit()
    
    # checking the OS distro
    if platform.linux_distribution()[0] in supported_os_dist_fedora:
        if os_version not in supported_os_version_fedora:
            print colour.FAIL + ("Sorry, you are running an OS based on %s with the major version %d which is NOT supported." % (os_distro, os_version)) + colour.ENDC
            sys.exit()
    elif platform.linux_distribution()[0] in supported_os_dist_debian:
        if os_version not in supported_os_version_debian:
            print colour.FAIL + ("Sorry, you are running an OS based on %s with the major version %d which is NOT supported." % (os_distro, os_version)) + colour.ENDC
            sys.exit()
    else:
        print colour.FAIL + ("Sorry, you are running an OS based on %s which is NOT supported." % (os_distro)) + colour.ENDC
        sys.exit()

    print colour.OKGREEN + "You are running a supported %s based OS with the major version %d." % (os_distro, os_version) + colour.ENDC


def check_running_port(service):
    listening_ports = []

    netstat_command = 'netstat -ntlp | egrep ' + service + ' | egrep tcp | grep -v 127.0.0.1 | grep -v localhost | awk {\'print $4\'}'
    netstat_exec = subprocess.Popen(netstat_command, stdout=subprocess.PIPE, shell=True)
    netstat_output = netstat_exec.stdout.read()
    portRegex = re.compile(r'\:+(\d+)')
    for line in netstat_output.split():
        port = portRegex.search(line)
        if port.group(1) is not None and int(port.group(1)) not in listening_ports:
            listening_ports.append(int(port.group(1)))
    return listening_ports


def check_if_installed(service):
    try:
        null = open("/dev/null", "w")
        subprocess.check_call(['which', service], stdout=null, stderr=null)
        null.close()
    except:
        return 0

def services_check():
    global webservice_type, webservice_version

    if os_platform in ['Linux']:
        if os_distro in ['LinuxMint', 'debian', 'Ubuntu']:
            webservice_type = "apache2"
        elif os_distro in ['fedora', 'redhat', 'centos', 'Red Hat Enterprise Linux Server', 'CentOS']:
            webservice_type = "httpd"
        else:
            print colour.FAIL + "Could not determine the default webservice for your OS distribution" + colour.ENDC
            sys.exit()           
    else:
        print colour.FAIL + "Linux OS platform supported only" + colour.ENDC
        sys.exit()

    # remove any services not installed on the server
    global services_running
    services_running = []
    services_installed = ["httpd", "apache2", "nginx", "varnishd", "memcached", "mysqld_safe"]
    
    for service in services_installed:
        if check_if_installed(service) is not 0:
            # service name renaming
            if service is "mysqld_safe":
                service = "mysqld"

            if check_if_running(service) is 1:
                services_running.append(service)
            else:
                # if the process name of apache is not named httpd
                if service == "httpd":
                    if check_if_installed("httpd.worker") is 0:
                        print colour.WARNING + "Service %s is installed but the process is not running" % "httpd" + colour.ENDC
                    else:
                        services_running.append(service)
                else:
                    print colour.WARNING + "Service %s is installed but the process is not running" % service + colour.ENDC

    for service in services_running:
        if len(check_running_port(service)) > 1:
            print colour.BOLD + colour.OKBLUE + "*** Service %s is installed and the process is running on the ports " % service + ' and '.join(map(str,check_running_port(service))) + colour.ENDC
        else:
            print colour.BOLD + colour.OKBLUE + "*** Service %s is installed and the process is running on the port " % service + ' and '.join(map(str,check_running_port(service))) + colour.ENDC
                
    return services_running

def webservices_check():
    webservices_running = []
    for service in services_running:
        if service == "httpd":
            if check_if_installed("httpd.worker") is 0:
                webservices_running.append("httpd.worker")
            else:
                webservices_running.append(service)
        if service == "apache2":
            webservices_running.append(service)
        if service == "nginx":
            webservices_running.append(service)

    print webservices_running

# Preflight checks and gathering system information
sudo_check()
print_header()
python_version_check()
os_check()
services_check()
webservices_check()