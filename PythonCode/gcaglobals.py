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
import datetime
import shutil
import subprocess

def getPortDict():
    import serial_ports

    portList = serial_ports.serial_ports()
    portDict = dict(zip(range(len(portList)), portList))
    return portDict

def writeLogFile(message):
    import datetime
    
    msgtime = datetime.datetime.strftime(datetime.datetime.now(),
                                         '%Y-%m-%d %H:%M:%S')
    with open("/Users/mobleyt/Desktop/outfile", "a") as logfile:
        logfile.write(msgtime + ":  ")        
        for line in message:
            logfile.write(line)
        logfile.write("\n")
            
writeLogFile(["\n\nLogfile start"])
writeLogFile(["Starting GasChromino"])


if getattr(sys, 'frozen', False):
        # we are running in a bundle
        execDir = sys._MEIPASS
        frozen = True
        writeLogFile(["Path to executable: ", execDir])
else:
        # we are running in a normal Python environment
        execDir = os.path.dirname(os.path.abspath(__file__))
        frozen = False
        writeLogFile(["Path to executable: ", execDir])
        
if sys.platform.startswith('win'):
    platform = 'win'
    print("Still need to assign GasChrominoHome")
elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
    platform = 'linux'
    gasChrominoHome = expanduser("~") + \
                      "$GasChrominoHome"
elif sys.platform.startswith('darwin'):
    platform = 'mac'
    writeLogFile(["Platform = " + platform + "\n",
                  "Importing Global Variables"])

    gasChrominoHome = expandvars("$GASCHROMINOHOME")
    if gasChrominoHome == "$GASCHROMINOHOME":    
        writeLogFile(["Environment variable $GASCHROMINOHOME not set\n"])        
        gasChrominoHome = expanduser("~") + \
                              "/Documents/GasChrominoData"

    if len(gasChrominoHome.split('/')[0]) > 0:
        if gasChrominoHome.split('/')[0][0] == "$":
            gchtemp = gasChrominoHome.split('/')
            gchtemp[0] = expandvars(gchtemp[0])
            gasChrominoHome = "/".join(gchtemp)
    writeLogFile(["Environment variable $GASCHROMINOHOME set to " + 
                 gasChrominoHome])

    gasChrominoSupport = expandvars("$GASCHROMINOSUPPORT")
    if gasChrominoSupport == "$GASCHROMINOSUPPORT":
        writeLogFile(["Environment variable $GASCHROMINOSUPPORT not set\n"])        
        gasChrominoSupport = expanduser("~") + \
                          "/Library/Application Support/GasChromino"
    else:
        pass
    if len(gasChrominoSupport.split('/')[0]) > 0:
        if gasChrominoSupport.split('/')[0][0] == "$":
            gcstemp = gasChrominoSupport.split('/')
            gcstemp[0] = expandvars(gcstemp[0])
            gasChrominoSupport = "/".join(gcstemp)
    writeLogFile(["Environment variable $GASCHROMINOSUPPORT set to " + 
                 gasChrominoSupport])
    
    if not os.path.isfile(gasChrominoSupport + "/GasChromino.cfg"):
        if frozen:
            writeLogFile(["Copying " + execDir +
                         "/Resources/GasChromino.cfg to " +
                         gasChrominoSupport + "/GasChromino.cfg"])
            shutil.copy2(execDir + "/Resources/GasChromino.cfg",
                         gasChrominoSupport + "/GasChromino.cfg")
        else:
            writeLogFile(["Copying " + execDir + "/GasChromino.cfg to " +
                         gasChrominoSupport + "/GasChromino.cfg"])
            shutil.copy2(execDir + "/GasChromino.cfg",
                         gasChrominoSupport + "/GasChromino.cfg")
        subprocess.run(['open', gasChrominoSupport + "/GasChromino.cfg"])
        subprocess.run(['open', gasChrominoSupport + "/Instructions.pdf"])
else:
    writeLogFile('Unsupported platform')
    raise EnvironmentError('Unsupported platform')

config = configparser.ConfigParser()
config.optionxform=str

if platform == 'mac':
    try:
        config.read(gasChrominoSupport + "/GasChromino.cfg")
        for key in config['globalVars']:
            strToExec = str(key) + "=" + str(config['globalVars'][key])
            exec(str(strToExec))
        noGlobals = False
    except:
        writeLogFile("Error opening config file")
        writeLogFile(str(sys.exc_info()))
        noGlobals = True

if not noGlobals:
    portDict = getPortDict()
    helpfile = gasChrominoSupport + '/' + helpfile
