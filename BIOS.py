#!/usr/bin/python26

import multiprocessing
import argparse
import paramiko
import getpass
import time
import sys

__author__  = "William Mok"
__version__ = "1.0"

def readConfig(config):
    fileContent = []

    try:
      fh = open(config, "r")
    except Exception as e:
      print "I/O Error: {0} - {1}".format(config, e.strerror)
      sys.exit(1)

    for line in fh.readlines():
      if line.startswith("#"):
        continue
      else:
        fileContent.append(line.rstrip())

    fh.close()
    return fileContent


def biosUpgrade(hostname, user, passwd):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
      client.connect(hostname, username=user, password=passwd, timeout=20)
    except Exception as e:
      print "[-] unable to connect to {0} err: {1}".format(hostname, e)
      return 1

    print "[{0}] Connected".format(hostname)

    stdin, stdout, stderr = client.exec_command('racadm update -f BIOS_VH690_WN64_2.1.3.EXE -l 192.168.1.1:/srv/fai/dell');
    exit_status = stdout.channel.recv_exit_status()

    stdin, stdout, stderr = client.exec_command('racadm update -f LC2.1_Q3FY15_Repair_Package_1.4.2.12_A00.usc -l 192.168.1.1:/srv/fai/dell');
    exit_status = stdout.channel.recv_exit_status()

    stdin, stdout, stderr = client.exec_command('racadm update -f firmimg.d7 -l 192.168.1.1:/srv/fai/dell');
    exit_status = stdout.channel.recv_exit_status()

    stdin, stdout, stderr = client.exec_command('racadm serveraction hardreset');
    exit_status = stdout.channel.recv_exit_status()

    if stdout.readline().rstrip() != "Server power operation successful":
      print "[{0}] unable to powercycle the server".format(hostname)
      return 1 
  
    print "[{0}] has been rebooted".format(hostname)

    client.close()   
    return

if __name__ == '__main__':
    jobs = []
    parser = argparse.ArgumentParser(description="DRAC Upgrade BIOS", prefix_chars="-+")

    parser.add_argument("-H", "--hostfile", required=True, help="Specify a list of servers to update", type=str )
    parser.add_argument("-u", "--user", help="Specify the username to login", type=str )

    opt = parser.parse_args()

    hosts = readConfig(opt.hostfile)

    if opt.user:
      username = opt.user
      password = getpass.getpass("Enter the password for {0}: ".format(opt.user))
    else:
      username = "root"
      password = "calvin"

    for host in hosts:
      print host

    while True:
      uin = raw_input("Would you like to update the servers [yes/no]: ")

      if uin.lower() == "yes":
        break
      elif uin.lower() == "no":
        sys.exit(0)
  

    for host in hosts:
      print "[{0}] Connecting".format(host)

      p = multiprocessing.Process(target=biosUpgrade, args=(host, username, password));
      jobs.append(p)
      p.start()
