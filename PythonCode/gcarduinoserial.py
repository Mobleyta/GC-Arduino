# -*- coding: utf-8 -*-
"""
This module provides functions for serial connection between computer
and Arduino GC interface

Created on Sat Feb  6 10:48:53 2016

@author:
T. Andrew Mobley
Department of Chemistry
Noyce Science Center
Grinnell College
Grinnell, IA 50112
mobleyt@grinnell.edu
"""
import gcardglobals as gcaGlobals
import gaschromatogram as gc
import sys
import threading
import queue


class GCArduinoSerial():
    """Class for handling arduino communications for GC transfer application
    """
    def __init__(self, arduinoCom=gcaGlobals.arduinoCom, openMode='r+'):
        self.arduinoCom = arduinoCom
        self.openMode = openMode
        self.queue1 = None
        self.queue2 = None
        self.exp = None

    def openArduino(self):
        """Opens serial connection to Arduino.
        """
        # Open serial port to arduino box
        import serial

        try:
            gcaGlobals.arduinoFile = serial.Serial(gcaGlobals.arduinoCom,
                                               timeout=gcaGlobals.timeout,
                                               baudrate=gcaGlobals.baudrate)
            return True
        except:
            gcaGlobals.mainwind.sendMessage("Error opening Arduino",
                                            "There was an error opening the \
connection to the Arduino. Please see help file for instructions on\
troubleshooting")
            return False

    def startCommunicationQueues(self):
        """Starts thread to run communication between Arduino and mainprogram.
        Three queues are started.

        queue1 for channel 1 (GC 1)
        queue2 for channel 2 (GC 2)
        queue3 for sending information to the Arduino

        Future development:  This could probably be refactored in two ways:
            1)  The queues for incoming data should be set up as a list so that
                it could be open-ended how many queues there are. This would
                allow easier expansion to include more than two channels at
                once.
            2)  The write to GC queue should be separated out from the read
                from GC queues.  This should be a separate thread that reads
                the queue constantly and writes to the Arduino asynchronously
                from the reads.  That would make the programming much simpler
                to understand, and possibly more robust.
        """
        self.queue1 = queue.Queue()
        self.queue2 = queue.Queue()
        self.queue3 = queue.Queue()
        self.exp = threading.Thread(target=self.readwriteGC, args=(self.queue1,
                                                                  self.queue2,
                                                                  self.queue3))
        try:
            self.exp.start()
        except:
            gcaGlobals.mainwind.printError(sys.exc_info())

    def helpArduinoOpen(self):
        """
        mw = gcaGlobals.mainwind
        frame = tk.Frame(mw.dataNB.datanb, name='ardcomm')
        self.textboxVar = tk.StringVar()
        self.textboxVar.set("")
        self.textbox = ttk.Label(frame, textvariable=self.textboxVar,
                                 justify=tk.LEFT, wraplength=400)
        self.textbox.grid(row=0, column=0, sticky=tk.W)
        mw.dataNB.datanb.insert('end', frame, text='Arduino communications')
        mw.dataNB.datanb.select(1)
        mw.root.update_idletasks()

        try:
            mw.bottomRightFrame.portNameVar.set(gcaGlobals.arduinoCom)
            self.tbvStr = "Attempting to open " + gcaGlobals.arduinoCom + \
            " \n\n"
            self.textboxVar.set(self.tbvStr)
            mw.root.update_idletasks()
            gcaGlobals.arduinoFile = open(gcaGlobals.arduinoCom, self.openMode)
            mw.dataNB.datanb.forget(frame)
        except FileNotFoundError:
            self.tbvStr += "The arduino box was not found, several things "\
            " could be wrong. \n For instance, \n (1) Check to make "\
            "sure that the usb cable is plugged in.\n (2) Check that the "\
            "correct serial port has been selected, and then reconnect.\n\n"\
            "The following serial ports are available\n\n"
            for key in gcaGlobals.portDict:
                self.tbvStr += (str(key)+" : "+ gcaGlobals.portDict[key]+"\n")
            self.textboxVar.set(self.tbvStr)
            mw.root.update_idletasks()
            gcaGlobals.arduinoFile = "Failed to Connect"  """
        pass

    def closeArduino(self):
        """Close serial connection to Arduino
        """
        if gcaGlobals.arduinoFile != "Not Connected":
            try:
                gcaGlobals.arduinoFile.close()
            except:
                gcaGlobals.mainwind.printError(sys.exc_info())

    def resetArduino(self):
        """Reset serial connection to Arduino by closing and opening.
        """
        if gcaGlobals.arduinoFile != "Not Connected":
            try:
                gcaGlobals.arduinoFile.close()
            except:
                gcaGlobals.mainwind.printError(sys.exc_info())
        return self.openArduino()

    def queueExperiment(self):
        """This function serves as the go-between for the threaded
        function readwriteGC that reads from the GC and posts to queues 1 & 2.
        It reads the data from the queues and then yields the messages to the
        animation that plots the data.

        Future work:

        Currently queueExperiment reads the channel it is supposed to be
        using from the global variable that is set by a radio button in the
        main window. However, eventually it would be better for this to get
        passed to it from the calling routine. This will make it easier to
        understand.

        When the queues are eventually set up to be a list of queues (allowing
        for easier expansion, then this routine will need to be written to
        allow for the looping through the list.)

        This is a spot that seems to get hung up occasionally after the end
        of an experiment. Need to have escape sequence that allows for
        user to manually get out of it. Possibly differentiate between the
        various channels by having user type ctrl-1 and ctrl-2 to shut down
        channel 1 and channel 2 respectively. This sounds like needing to
        attach a keyboard interrupt that raises an exception that is caught by
        the try/except inside while loop.
        """
        mw = gcaGlobals.mainwind

        isDone = False
        channel = int(gcaGlobals.channel)
        if channel == 1:
            timeStamp = gcaGlobals.startString1
        elif channel == 2:
            timeStamp = gcaGlobals.startString2

        if gcaGlobals.ard.exp.ident is None:
            try:
                gcaGlobals.ard.exp.start()
            except:
                mw.printError(sys.exc_info())

        while not isDone:
            try:
                if channel == 1:
                    msg = self.queue1.get(0)
                elif channel == 2:
                    msg = self.queue2.get(0)
                if msg != "quit":
                    yield msg
                else:
                    noExper = len(mw.dataList)
                    if channel == 1:
                        [timeVals, yVals] = self.queue1.get(0)
                        instrName = gcaGlobals.instrName[0]
                    else:
                        [timeVals, yVals] = self.queue2.get(0)
                        instrName = gcaGlobals.instrName[1]
                    gc.gcProcessing([timeVals,  # exp finished, process
                                     yVals],
                                    timeStamp,
                                    instrName)
                    mw.rightFrame.checkAddNewData(noExper, channel)
                    isDone = True
            except queue.Empty:         # Whenever queue is empty, avoid error
                pass
            except:
                mw.printError(sys.exc_info())

        if gcaGlobals.multRuns:         # if multiple runs allowed, restart
            mw.rightFrame.startCollect(channel)

    def readwriteGC(self, q1, q2, q3):
        """Function to read and write data between main program and Arduino.

        This function is called to run in an asynchronous thread.

        Future work:

        Should refactor to split read and write functions
            (see startCommunicationQueues for that idea.)
            If this was done, probably more error checking could be implemented
            in write routine at the same time. Essentially none now.

        It would be much more readable if the various operations were
            refactored into individual functions.

        Need to think about necessary loop structure if queues and channels
            are described as lists (expansion to more channels)
        """
        import time

        def writeStringToGC(strToSend):
            """Function to actually write to Arduino.
            """
            try:
                gcaGlobals.arduinoFile.write(bytearray(strToSend, 'utf-8'))
                gcaGlobals.arduinoFile.flush()
            except:
                gcaGlobals.mainwind.printError(sys.exc_info())

        timeVals = []
        timeVals2 = []
        yVals = []
        yVals2 = []

        self.inline = ""

        while gcaGlobals.runRWgc:       # If False, user is exiting program
            try:
                msg = q3.get(0)         # Message on q3 is a message to send
                writeStringToGC(msg)
            except queue.Empty:
                time.sleep(0.5)         # This will be repeated only if user
# has not yet started up one of the channels. This is a waiting routine to
# look for a start of data acquisition.

            if gcaGlobals.ch1Running or gcaGlobals.ch2Running:
                self.inline = ""
                msg = ""
                while self.inline == "":
                    try:
                        self.inline = \
                            gcaGlobals.arduinoFile.readline().decode('utf-8')
                    except IOError:
                        gcaGlobals.mainwind.sendMessage("I/O Error",
                                                "An I/O error has occurred")
                    try:
                        msg = q3.get(0)  # Message on q3 is a message to send
                    except:
                        pass
                    if msg != "":
                        writeStringToGC(msg)

                lTimePot = self.inline.rstrip().split(' ')

                while (lTimePot[0] != "stopped" or lTimePot[1] != "stopped"):
                    if len(lTimePot) > 2:
                        if lTimePot[2] != "q":
                            q1.put([float(lTimePot[2]), float(lTimePot[3])])
                            timeVals.append(float(lTimePot[2]))
                            yVals.append(float(lTimePot[3]))
                        elif timeVals != []:
                            q1.put("quit")
                            q1.put([timeVals, yVals])
                            timeVals = []
                            yVals = []
                            gcaGlobals.ch1Running = False
                        if lTimePot[4] != "q":
                            q2.put([float(lTimePot[4]), float(lTimePot[5])])
                            timeVals2.append(float(lTimePot[4]))
                            yVals2.append(float(lTimePot[5]))
                        elif timeVals2 != []:
                            q2.put("quit")
                            q2.put([timeVals2, yVals2])
                            timeVals2 = []
                            yVals2 = []
                            gcaGlobals.ch2Running = False

                    """As the next line is read in, this checks to see if
                    data is now coming in from the other channel.
                    If it is, start putting it on the queue.
                    """
                    try:
                        self.inline = \
                            gcaGlobals.arduinoFile.readline().decode('utf-8')
                    except:
                        pass
                    if self.inline != "":
                        lTimePot = self.inline.rstrip().split(' ')
                        if (not gcaGlobals.ch1Running and lTimePot[0] ==
                                gcaGlobals.startString1):
                            gcaGlobals.ch1Running = True
                            gcaGlobals.changeChannel = 1
                        elif (not gcaGlobals.ch2Running and lTimePot[1] ==
                                gcaGlobals.startString2):
                            gcaGlobals.ch2Running = True
                            gcaGlobals.changeChannel = 2
                    msg = ""
                    try:
                        msg = q3.get(0)
                    except queue.Empty:
                        pass
                    if msg != "":
                        writeStringToGC(msg)
                    if not gcaGlobals.runRWgc:  # Looks for closing of program
                        break
            if timeVals != []:          # If data lists are not empty,
                q1.put("quit")          # put on queue
                q1.put([timeVals, yVals])
                timeVals = []
                yVals = []
                gcaGlobals.ch1Done = True
            if timeVals2 != []:
                q2.put("quit")
                q2.put([timeVals2, yVals2])
                timeVals2 = []
                yVals2 = []
                gcaGlobals.ch2Done = True
            gcaGlobals.ch1Running = False   # If all the way here, no channel
            gcaGlobals.ch2Running = False   # is running

    def setupExperiments(self, channel):
        """
        Procedure to send instructions to Arduino.

        Which ADC (Arduino's native or ADS1115) will be used is sent.

        Sends a string based upon time to identify beginning of data set. This
        is needed to rid buffer of old data if a false start is somehow done
        on arduino side.

        Sends whether channel 1 or channel 2 is being used.

        Sends length of time of experiment.
        """

        import datetime

        timeString = datetime.datetime.strftime(
            datetime.datetime.now(), '%Y-%m-%d-%H:%M:%S')

        if channel == 1:
            gcaGlobals.startString1 = timeString
        if channel == 2:
            gcaGlobals.startString2 = timeString

        preString = "single" + " " + gcaGlobals.adcChoice + " " + \
            timeString + " " + str(channel) + " "

        strToSend = preString + gcaGlobals.timeExper + "\n"
        self.queue3.put(strToSend)
