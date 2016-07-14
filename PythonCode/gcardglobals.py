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

def getPortDict():
    import serial_ports

    portList = serial_ports.serial_ports()
    portDict = dict(zip(range(len(portList)), portList))
    return portDict
    
config = configparser.ConfigParser()
config.optionxform=str

try:
    config.read('GasChromino.cfg')
except:
    print("Error opening config file")
    raise Exception

for key in config['globalVars']:
    strToExec = str(key) + "=" + str(config['globalVars'][key])
    exec(str(strToExec))

if sys.platform.startswith('win'):
    platform = 'win'
elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
    platform = 'linux'
elif sys.platform.startswith('darwin'):
    platform = 'mac'
else:
    raise EnvironmentError('Unsupported platform')

portDict = getPortDict()
