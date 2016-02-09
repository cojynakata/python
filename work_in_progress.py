#!/usr/bin/python

import errno
import subprocess
import os
import platform
import math
import sys
import re

def prompt_sudo():
    ret = 0
    if os.geteuid() != 0:
        msg = "[sudo] password for %u:"
        ret = subprocess.check_call("sudo -v -p '%s'" % msg, shell=True)
    return ret

if prompt_sudo() != 0:
    exit("Sorry, you need to have root privileges to run this script.")
else:
    print("You are running this script as root.")

#Display the running python version
#print ("Python version: %s" % sys.version.split('\n'))

def get_pid(process):
    from subprocess import check_output
    return check_output(["pidof", process]).split()

def os_check():
    global os_platform, os_distro, os_version
    supported_os_platform = ['Linux']
    supported_os_dist_debian = ['LinuxMint', 'debian', 'Ubuntu']
    supported_os_dist_fedora = ['fedora', 'redhat', 'centos', 'Red Hat Enterprise Linux Server']
    supported_os_version_debian = [7, 8, 12, 14, 15, 17]
    supported_os_version_fedora = [6, 7, 21, 22]
    # getting the running OS details
    os_platform = platform.system()
    os_distro = platform.linux_distribution()[0]
    os_version = int(float(platform.linux_distribution()[1]))

    # checking the OS type
    if os_platform not in supported_os_platform:
        exit("Sorry, you are running on the %s platform which is NOT supported." % (os_platform))
    
    # checking the OS distro
    if platform.linux_distribution()[0] in supported_os_dist_fedora:
        if os_version not in supported_os_version_fedora:
            exit("Sorry, you are running an OS based on %s with the major version %d which is NOT supported." % (os_distro, os_version))
    elif platform.linux_distribution()[0] in supported_os_dist_debian:
        if os_version not in supported_os_version_debian:
            exit("Sorry, you are running an OS based on %s with the major version %d which is NOT supported." % (os_distro, os_version))
    else:
        exit("Sorry, you are running an OS based on %s which is NOT supported." % (os_distro))

    print "You are running a supported %s based OS with the major version %d." % (os_distro, os_version)

def webservice_check():
    #can't detect apache running as fast-cgi yet!!
    global webservice_type, webservice_version
    import subprocess

    def check_running_port(service):
        output = []
        command = 'netstat -ntlp | grep ' + service + ' | grep -v tcp6'
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, shell=True)
        proc_output = proc.stdout.read().splitlines()
        for lines in range(len(proc_output)):
            output.append(proc_output[lines].split()[3].split(':')[1])
        return output

    def webservice_score(service, port):
    # this function will determine which webservice is in use when multiple ones are running on the server
    # or when the one detected is not running on the ususal 80 and/or 443 port
        if "0800" or "4433" in port:
            return 1
        else:
            return 0

    #defining default package name, conf files location
    if os_platform in ['Linux']:
        if os_distro in ['LinuxMint', 'debian', 'Ubuntu']:
            webservice_type = "apache2"
        elif os_distro in ['fedora', 'redhat', 'centos', 'Red Hat Enterprise Linux Server']:
            webservice_type = "httpd"           
    else:
        print "Linux OS platform supported only"

    webservices_list = [webservice_type, "nginx"]
    try:
        null = open("/dev/null", "w")
        subprocess.check_call([webservice_type, "-v"], stdout=null, stderr=null)
        null.close()
    except:
        webservices_list.remove(webservice_type)

    try:
        null = open("/dev/null", "w")
        subprocess.check_call(["nginx", "-v"], stdout=null, stderr=null)
        null.close()
    except:
        webservices_list.remove("nginx")

    if len(webservices_list) == 0:
        print "No webservices installed or detection failed"
        sys.exit()

    current_services = []
    for webservice in webservices_list:
        try:
            null = open("/dev/null", "w")
            pids = get_pid(webservice)
            current_services.append(webservice)
            null.close()
        except:
            print "Webservice package %s is installed but process is NOT running." % webservice

    webservice_score_store = {}
    if len(current_services) == 0:
        print "No webservices running or detection failed"
        sys.exit()
    elif len(current_services) > 1:
        print "Multiple webservices installed and running:"
        for webservice in current_services:
            if len(check_running_port(webservice)) == 0:
                print "*** Webservice package %s is installed and running but is NOT listening on a TCPv4 port" % (webservice)
            elif len(check_running_port(webservice)) > 1:
                print "*** Webservice package %s is installed and running on ports " % webservice + ' and '.join(map(str,check_running_port(webservice)))

            else:
                print "*** Webservice package %s is installed and running on port " % webservice + ' and '.join(map(str,check_running_port(webservice)))

            if len(check_running_port(webservice)) > 0:
                webservice_score_store[webservice] = webservice_score(webservice, check_running_port(webservice))
                #print "Webservice %s has a score of %d" % (webservice, webservice_score_store[webservice])

        
        # validating results (eg. ensuring that max_score is not a duplicate key)
        max_score = max(webservice_score_store, key=webservice_score_store.get)
        
        duplicate = []
        for key, value in webservice_score_store.iteritems():
            if value == webservice_score_store[max_score]:
                duplicate.append(key)

        if len(duplicate) > 1:
            print "Could not determine which is the relevant webservice process"
            sys.exit()
        else:
            webservice_type = duplicate[0]
            return duplicate[0]

    else:
        if len(check_running_port(webservice)) == 0:
            print "*** Webservice package %s is installed and running but is NOT listening on a TCPv4 port" % (webservice)
        elif len(check_running_port(webservice)) > 1:
            print "*** Webservice package %s is installed and running on ports " % webservice + ' and '.join(map(str,check_running_port(webservice)))
        else:
            print "*** Webservice package %s is installed and running on port " % webservice + ' and '.join(map(str,check_running_port(webservice)))

        if len(check_running_port(webservice)) > 0:
            webservice_score_store[webservice] = webservice_score(webservice, check_running_port(webservice))
            print "Webservice %s has a score of %d" % (webservice, webservice_score_store[webservice])

# Main program
os_check()
webservice_check()