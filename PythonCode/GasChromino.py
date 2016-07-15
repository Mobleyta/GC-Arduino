# -*- coding: utf-8 -*-
"""
GCReader with a windows (tk) interface
Created on Sun Feb  7 09:50:02 2016

@author:
T. Andrew Mobley
Department of Chemistry
Noyce Science Center
Grinnell College
Grinnell, IA 50112
mobleyt@grinnell.edu
"""

import sys


import gcaserial as gcaSerial
import gcawindow as gca
import gcaglobals as gcaGlobals

gcaGlobals.ard = gcaSerial.GCArduinoSerial()

gcaGlobals.mainwind = gca.gcArduinoWindow()

if not gcaGlobals.dataStation:
    gcaGlobals.mainwind.root.after(10, gca.connectToArduino)
    gcaGlobals.mainwind.root.after(50, gca.selectLiveTab)

gca.startMainLoop(gcaGlobals.mainwind)
