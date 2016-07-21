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

import gcaglobals as gcaGlobals

if gcaGlobals.noGlobals:
    import tkinter as tk
    import sys
    
    def getout():
        root.destroy()
        root.quit()
        
    root = tk.Tk()
    root.title("Error opening Global Variables")
    msg = "There was an unresolved error opening the \
Global Variables.\n\n This is most likely due to improper setup.\n Please try \
running gcSetup and try again."
    tk.Label(root, text=msg, fg='red').pack()
    tk.Button(root, text="Quit", command=getout).pack()
    root.lift()
    
    root.mainloop()
else:
    import gcaserial as gcaSerial
    import gcawindow as gca    

    gcaGlobals.ard = gcaSerial.GCArduinoSerial()

    gcaGlobals.mainwind = gca.gcArduinoWindow()



    if not gcaGlobals.dataStation:
        gcaGlobals.mainwind.root.after(10, gca.connectToArduino)
        gcaGlobals.mainwind.root.after(50, gca.selectLiveTab)

    gca.startMainLoop(gcaGlobals.mainwind)
