# -*- coding: utf-8 -*-
"""
Module to hold various global variables for the GCReader project.

Created on Sun Feb 14 07:09:18 2016

@author:
T. Andrew Mobley
Department of Chemistry
Noyce Science Center
Grinnell College
Grinnell, IA 50112
mobleyt@grinnell.edu
"""
import sys
import configparser
from os.path import expanduser
from os.path import expandvars
import os

def getPortDict():
    import serial_ports

    portList = serial_ports.serial_ports()
    portDict = dict(zip(range(len(portList)), portList))
    return portDict
  
config = configparser.ConfigParser()
config.optionxform=str

if sys.platform.startswith('win'):
    platform = 'win'
    print("Still need to assign GasChrominoHome")
elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
    platform = 'linux'
    gasChrominoHome = expanduser("~") + \
                      "$GasChrominoHome"
elif sys.platform.startswith('darwin'):
    platform = 'mac'
    gasChrominoHome = expandvars("$GASCHROMINOHOME")
    print("Home is "+gasChrominoHome)
#    if gasChrominoHome == "$GASCHROMINOHOME":    
#        gasChrominoHome = expanduser("~") + \
#                              "/Documents/GasChrominoData"
    gasChrominoSupport = expandvars("$GASCHROMINOSUPPORT")
    print("Support is "+gasChrominoSupport)
#    if gasChrominoSupport == "$GASCHROMINOSUPPORT":
#        gasChrominoSupport = expanduser("~") + \
#                          "/Library/Application Support/GasChromino"
#    else:
#        pass	
else:
    raise EnvironmentError('Unsupported platform')

if platform == 'mac':
    try:
        config.read(gasChrominoSupport + "/GasChromino.cfg")
    except:
        print("Error opening config file")

    for key in config['globalVars']:
        strToExec = str(key) + "=" + str(config['globalVars'][key])
        exec(str(strToExec))

portDict = getPortDict()
helpfile = gasChrominoSupport + '/' + helpfile
