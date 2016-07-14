# -*- coding: utf-8 -*-
"""
Created on Sun Feb  7 10:15:34 2016

This module contains the various classes and functions that run the tk windows
for the GCReaderTK program.

@author:
T. Andrew Mobley
Department of Chemistry
Noyce Science Center
Grinnell College
Grinnell, IA 50112
mobleyt@grinnell.edu
"""
import matplotlib
from matplotlib.backends.backend_tkagg \
    import FigureCanvasTkAgg, NavigationToolbar2TkAgg
import numpy as np
import gaschromatogram as gc
import matplotlib.animation as animation
import tkinter as tk
from tkinter import ttk
import gcafileio as gcafio
import gcaglobals as gcaGlobals
from livegctrace import LiveGCTrace
import time
import sys


def _quit(wind):
    """Procedure to close out mainloop and window.
    """
    if tk.messagebox.askokcancel("Quit", "Do you want to quit?"):
        gcaGlobals.runRWgc = False
        time.sleep(0.5)
        closeArduino()
        wind.quit()     # stops mainloop
        wind.destroy()  # this is necessary on Windows to prevent
        # Fatal Python Error: PyEval_RestoreThread: NULL tstate


def startMainLoop(wind):
    """Starts mainloop for root window.
    """
    wind.root.mainloop()


def resetArduino():
    """Function to call routine in gcaserial to:
        reset Arduino by closing and reopening the connection.
    """
    if gcaGlobals.arduinoFile != "Not Connected":
        gcaGlobals.ard.closeArduino()
    connectToArduino()


def closeArduino():
    """Function to call routine in gcaserial to:
        Close serial connection to Arduino
    """
    if gcaGlobals.arduinoFile != "Not Connected":
        gcaGlobals.ard.closeArduino()


def connectToArduino():
    """Function to call routine in gcaserial to:
        Open serial connection to Arduino
    Also calls funciton to start communication queues
    """
    mw = gcaGlobals.mainwind

    mw.bottomRightFrame.stationNameVar.set("Arduino Connection")
    mw.bottomRightFrame.portNameVar.set(gcaGlobals.arduinoCom)
    mw.bottomRightFrame.ardStatusVar.set("Connecting")
    mw.bottomRightFrame.ardStatus['foreground'] = 'blue'
    mw.root.update()
    if not gcaGlobals.ard.openArduino():
        mw.bottomRightFrame.ardStatusVar.set(gcaGlobals.arduinoFile)
        mw.bottomRightFrame.ardStatus['foreground'] = 'red'
        mw.root.update()
    else:
        mw.bottomRightFrame.ardStatusVar.set("Connected")
        mw.bottomRightFrame.ardStatus['foreground'] = 'green'
        mw.root.update()
        gcaGlobals.ard.startCommunicationQueues()


def selectLiveTab():
    """Function that is periodically called (callback) that looks at
    global variable changeChannel. If changeChannel is different than the
    default value, that means that a new experiment has been queued and the
    program should change focus to that new live data. Since this cannot be
    done from inside another thread (readwriteGC is started as another thread),
    it instead sets the global variable and this function (started from within
    the mainloop) constantly checks the variable. This is to handle the fact
    that tkinter is fully threadsafe.
    """
    mw = gcaGlobals.mainwind
    if gcaGlobals.changeChannel != 999:
        mw.dataNB.startAnimation(gcaGlobals.changeChannel)
        mw.dataNB.datanb.select(gcaGlobals.changeChannel-1)
        gcaGlobals.changeChannel = 999
    mw.root.after(1000, selectLiveTab)


class gcArduinoWindow():
    """Class for window to display GC-Arduino interface program.

    This is the main window for the program. It has three main areas currently:
        1) Left hand large frame that contains notebook of data tabs
        2) Right narrow tall frame that contains all of the various settings
            and controls.
        3) Bottom Right frame contains information about connection to Arduino
        4) Bottom frame currently contains nothing, eventually could contain
            information about signal coming from GC, or possibly peak
            information instead of it being directly on gc trace

    Future Development:
        There are some severe shortcomings in the GUI at this point.

        1) Needs to have the various channels separated so that two different
            windows of data could be open for multiple channels. I think that
            this should probably be done by having multiple instances of the
            gcArduinoWindow, but in all likelihood this will mean that
            quite a bit needs to be refactored in the main controls
            (gcaserial).
        2) Currently the numerical data for two channels is not displayed
        3) Need the ability to sort data
        4) Better if save was done by marking tabs of notebook (rather than
            by having a checklist to look at and click)
    """
    def __init__(self,
                 title=gcaGlobals.mainwindTit,
                 size=gcaGlobals.mainwindSize,
                 location=gcaGlobals.mainwindPos):

        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry(size)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        self.root.resizable(True, True)
        self.root.protocol("WM_DELETE_WINDOW", lambda: _quit(self.root))

        self.mainframe = ttk.Frame(self.root)
        self.mainframe.grid(column=0, row=0, sticky=(tk.N, tk.S, tk.E, tk.W))
        self.mainframe.columnconfigure(0, weight=1)
        self.mainframe.rowconfigure(0, weight=1)

        self.dataNB = dataNotebook(self.mainframe)
        self.rightFrame = rightFrame(self.mainframe)
        self.bottomRightFrame = bottomRightFrame(self.mainframe)
        self.bottomFrame = bottomFrame(self.mainframe)

        self.menuBar = menuBar(self.root)
        self.root.config(menu=self.menuBar.menubar)

        self.dataList = []

    def resetMenus(self):
        self.menuBar = menuBar(self.root)
        self.root.config(menu=self.menuBar.menubar)

    def sendMessage(self, tit, msg):
        """Routine to open messagebox without calling function needing access
        to tkinter.
        """
        tk.messagebox.showinfo(tit, msg)

    def printError(self, errorInfo):
        """Routine to print debug information to console

        Future Dvelopment:
            Eventually will write to a log file to allow trouble shooting for
            remote users. Users could send in the log file with error messages.
            When this is implemented, it should also have some standard
            messages that are written at various parts of the program
            (opening serial connection, starting queues, writing to GC)
        """
        if gcaGlobals.debug:
            print(errorInfo)
        else:
            pass


class dataNotebook():
    """Class for data frame of GC-Arduino interface program

    Currently set up with two liveframes for two channels of data.
        This needs to be refactored to allow for either one channel, or two
        channels or possibly more channels. This will come with setting
        channels and queues to be lists.

    Two main variables in the class are datanb, which is the structure
        that actually holds the tabs (frames), and dataframelist (which holds
        a list of the same data frames.)  It is possible that this could be
        reworked to only have the datanb, but right now both are necessary.
        One thing to note:  datanb starts its indexing at 1
                            dataframelist starts its indexing at 0

    Future Development:
        1) Main body needs to be refactored into individual functions
            considerably
    """
    def __init__(self, parent):
        self.parent = parent
        self.datanb = ttk.Notebook(self.parent)
        self.liveframe1 = ttk.Frame(self.datanb)
        self.liveframe1.config(height=gcaGlobals.liveframeHeight,
                               width=gcaGlobals.liveframeWidth)
        self.liveframe2 = ttk.Frame(self.datanb)
        self.liveframe2.config(height=gcaGlobals.liveframeHeight,
                               width=gcaGlobals.liveframeWidth)
        self.dataframelist = [self.liveframe1, self.liveframe2]
        self.datanb.add(self.dataframelist[0], text='Live Data 1')
        self.datanb.add(self.dataframelist[1], text='Live Data 2')
        self.datanb.grid(row=0, column=0,
                         sticky=(tk.N, tk.E, tk.S, tk.W),
                         padx=10, pady=10)

    def startAnimation(self, channel):
        """Routine to actually start the animation of GC data coming in from
        the Arduino.

        Future development:
            Will need to change structure when channels and queues are
            refactored to lists, but will be much easier to read when that
            happens.
        """
        mw = gcaGlobals.mainwind

        if channel == 1:
            self.fig1 = matplotlib.figure.Figure()
            self.canvas1 = FigureCanvasTkAgg(self.fig1,
                                        master=mw.dataNB.dataframelist[0])
            self.canvas1.get_tk_widget().grid(column=0, row=1)
            self.toolbar1 = NavigationToolbar2TkAgg(self.canvas1,
                                               mw.dataNB.dataframelist[0])
            self.toolbar1.update()
            self.canvas1._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
            self.ax1 = self.fig1.add_subplot(111)
            self.liveGC1 = LiveGCTrace(self.ax1, float(gcaGlobals.timeExper))

            self.ani1 = animation.FuncAnimation(self.fig1,
                                   self.liveGC1.update,
                                   gcaGlobals.ard.queueExperiment(),
                                   interval=50, blit=False,
                                   repeat=False)
        elif channel == 2:
            self.fig2 = matplotlib.figure.Figure()
            self.canvas2 = FigureCanvasTkAgg(self.fig2,
                                        master=mw.dataNB.dataframelist[1])
            self.canvas2.get_tk_widget().grid(column=0, row=1)
            self.toolbar2 = NavigationToolbar2TkAgg(self.canvas2,
                                               mw.dataNB.dataframelist[1])
            self.toolbar2.update()
            self.canvas2._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
            self.ax2 = self.fig2.add_subplot(111)
            self.liveGC2 = LiveGCTrace(self.ax2, float(gcaGlobals.timeExper))
            self.ani2 = animation.FuncAnimation(self.fig2,
                                   self.liveGC2.update,
                                   gcaGlobals.ard.queueExperiment(),
                                   interval=50, blit=False,
                                   repeat=False)

    def addDataFrame(self, frameTitle='Newest Data', index=-1, listindex=-1):
        """Function that adds a new data frame after acquisition.
        Called by: checkAddNewData

        Has several functions that allow for user to define manually peaks
        and to delete peaks that have already been picked.

        Future Development:
            1) Need to work on display of peaks; currently on trace but when
                there are long lists of peaks this does not work.
                Need way to turn off, but also need to have another place to
                put it so that they can all be seen. This could be a text box
                that was put in the currently unused bottom frame.
        """
        def getClosestXValue(xPt):
            """After user clicks, returns closest x-point (time point) that
            corresponds to the click.
            """
            index = (np.abs(xArray - xPt)).argmin()
            return index

        def onpress(event):
            """On mouse button control-click, get x-value and then call
            getClosestXValue to get closest time value, mark with arrow.
            This gets starting point of manually picked peak.
            """
            if event.key == 'control':
                xvalue = event.xdata
                startPt = getClosestXValue(xvalue)
                gcaGlobals.manPeakList.append(startPt)
                a.plot(xArray[startPt],
                       yArray[startPt], color='red', linewidth=3, marker='>')
                fig.canvas.draw()
            elif event.key == 'ctrl+b':
                xvalue = event.xdata
                startPt = getClosestXValue(xvalue)
                gcaGlobals.baseSelect = [startPt]
                a.plot(xArray[startPt],
                       yArray[startPt], color='blue', linewidth=5, marker='>')
                fig.canvas.draw()

        def onrelease(event):
            """On mouse button control-click, get x-value and then call
            getClosestXValue to get closest time value.  If
            there is a matching starting point, then add the end point and
            mark with arrow.

            On mouse button shift-click, call deletepeak with closest x-value.
            """
            if event.key == 'control':
                xvalue = event.xdata
                endPt = getClosestXValue(xvalue)
                if len(gcaGlobals.manPeakList) % 2 == 1:
                    gcaGlobals.manPeakList.append(endPt)
                    a.plot(xArray[endPt],
                           yArray[endPt], color='red', linewidth=3, marker='<')
                    fig.canvas.draw()
            if event.key == 'ctrl+b':
                xvalue = event.xdata
                endPt = getClosestXValue(xvalue)
                if len(gcaGlobals.baseSelect) % 2 == 1:
                    gcaGlobals.baseSelect.append(endPt)
                    a.plot(xArray[endPt],
                           yArray[endPt],
                           color='blue',
                           linewidth=5,
                           marker='<')
                    fig.canvas.draw()
            elif event.key == 'shift':
                xvalue = event.xdata
                deletePeak(getClosestXValue(xvalue))

        def deletePeak(xIndex):
            """Called by onrelease.
            Deletes a peak given an x-value. Checks all peaks to see if x-value
            is in the peak range, if so, it deletes it. Once peak is deleted
            it renormalizes the area for all of the remaining peaks. Finally,
            it adds the data frame again to refresh the data.
            """
            for i in range(len(gc.peaks)):
                if ((xIndex >= gc.peaks[i].peakStart) and
                        (xIndex <= gc.peaks[i].peakEnd)):
                    del gc.peaks[i]
                    break
            gc.findNormalizedArea()
            currTab = gcaGlobals.mainwind.dataNB.datanb.select()
            currIndex = gcaGlobals.mainwind.dataNB.datanb.index(currTab)
            if currIndex == 0:
                tk.messagebox.showwarning("Analysis Error",
                                          "Cannot analyze Live Data Tab")

            dataListIndex = currIndex - gcaGlobals.noChannels
            if gcaGlobals.mainwind.dataList[dataListIndex].filename is None:
                gcaGlobals.mainwind.dataNB.addDataFrame(
                    gcaGlobals.mainwind.dataList[dataListIndex].tabTitle,
                    currIndex, dataListIndex)
            else:
                gcaGlobals.mainwind.dataNB.addDataFrame(
                    gcaGlobals.mainwind.dataList[dataListIndex].tabTitle,
                    currIndex, dataListIndex)
            gcaGlobals.mainwind.dataNB.datanb.select(currIndex)

        mw = gcaGlobals.mainwind
        gc = mw.dataList[listindex]

        if index == -1:
            newframe = ttk.Frame(self.datanb)
            newframe.config(height=gcaGlobals.dataframeHeight,
                            width=gcaGlobals.dataframeWidth)
            self.dataframelist.append(newframe)
            self.datanb.add(self.dataframelist[listindex], text=frameTitle)
        elif index != -1:
            self.datanb.forget(index)
            newframe = ttk.Frame(self.datanb)
            newframe.config(height=gcaGlobals.dataframeHeight,
                            width=gcaGlobals.dataframeWidth)
            self.dataframelist[listindex] = newframe
            if index + 1 < len(self.dataframelist):
                self.datanb.insert(index, newframe, text=frameTitle)
            else:
                self.datanb.add(newframe, text=frameTitle)

        colorlist = 20 * gcaGlobals.colorList

        fig = matplotlib.figure.Figure()
        a = fig.add_subplot(211)
        xArray = np.array(gc.trace[0])
        yArray = np.array(gc.trace[1])
        if gc.baselineCalc != [] and gcaGlobals.showBaseline:
            yBaseArray = np.array(gc.baselineCalc)
            a.plot(xArray, yBaseArray, color=gcaGlobals.baselineColor)
        a.plot(xArray, yArray, color=gcaGlobals.traceColor)

        baseline = gc.baselineCalc

        for peak, color in zip(gc.peaks, colorlist):
            a.fill_between(xArray, yArray, baseline, facecolor=color,
                           where=(xArray > xArray[peak.peakStart - 1]) &
                           (xArray < xArray[peak.peakEnd + 1]))

        table = ""
        for peak in gc.peaks:
            table += "{0:.3f}".format(xArray[peak.peakMax]) + \
                "                     " + "{0:.5f}".format(peak.peakArea) + \
                "                {0:.5f}".format(peak.relativePeakArea) + "\n"
        fig.text(0.3, 0.02, gc.comment + "\n" +
                 gc.timeStamp + "\nInstrument: " + gc.instrName + "\n\n"
                 "Ret. Time (min)         Area          Relative Area\n" +
                 table.expandtabs(),
                 fontsize=12)

        canvas = FigureCanvasTkAgg(fig, mw.dataNB.dataframelist[listindex])

        canvas.show()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        toolbar = NavigationToolbar2TkAgg(canvas,
                                          mw.dataNB.dataframelist[listindex])
        toolbar.update()
        canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        canvas.mpl_connect('button_press_event', onpress)
        canvas.mpl_connect('button_release_event', onrelease)
        self.datanb.select(len(mw.dataList)-1)


class rightFrame():
    """Class for right frame of GC-Arduino interface program.

    This frame contains most of the control functions for use of the program.

    Categories:
        1) Deletion of notebook tabs
        2) Experimental Parameters
            a) Length of experiment
            b) Comment
        3) Start of experiment
        4) Processing
            a) Method for area calculation (trapezoidal, simple addition)
            b) Automatic Processing
                1. Peak threshold: Amount above baseline before changes
                     in signal will be recognized as the start of a peak
                2. Gradient threshold:  Amount that slope must be above
                     before changes in signal will be recognized as the start
                     of a peak
                3. Find an integrate peaks based upon thresholds provided
            c) Manual Processing
                1. Integrate manually marked peaks
                2. Clear all peaks
                3. Set comment for current data tab (after acquisition)
                4. Copy peak table to clipboard for transfer to another program
    """
    def __init__(self, parent):
        self.parent = parent
        self.rightframe = ttk.Frame(self.parent)
        self.rightframe.grid(column=1, row=0,
                             sticky=(tk.N, tk.S, tk.E, tk.W), padx=20)
        self.rightframe.columnconfigure(0, weight=0)
        self.rightframe.rowconfigure(0, weight=1)

        self.delTabButton = ttk.Button(self.rightframe,
                                       text="Close Data Tab",
                                       command=self.deleteTab)
        self.delTabButton.pack(pady=10)

        self.experframe = ttk.Frame(self.rightframe, relief=tk.SUNKEN)
        self.experframe.pack(fill=tk.BOTH, pady=5, padx=5)

        ttk.Label(self.experframe, text="Experimental parameters",
                  font=('Helvetica', 16, 'bold')).pack(padx=5,
                                                       pady=10,
                                                       fill=tk.X)

        ttk.Label(self.experframe,
                  text="Length of GC experiment in minutes",
                  font=('Helvetica', 14, 'bold italic')).pack(padx=5,
                                                              fill=tk.X)
        self.timeExperVar = tk.StringVar()
        self.timeExperVar.set(gcaGlobals.timeExper)
        self.timeExperEntry = ttk.Entry(self.experframe,
                                        textvariable=self.timeExperVar)
        self.timeExperEntry.pack(padx=5, fill=tk.X)

        ttk.Label(self.experframe).pack()

        ttk.Label(self.experframe,
                  text="Comment for Experiment",
                  font=('Helvetica', 14, 'bold italic')).pack(padx=5,
                                                              fill=tk.X)
        self.commentVar = tk.StringVar()
        self.commentVar.set("")
        self.commentEntry = ttk.Entry(self.experframe,
                                      textvariable=self.commentVar)
        self.commentEntry.pack(padx=5, fill=tk.X)

        self.gcVal = tk.StringVar()
        self.gcValLabel = ttk.Label(self.experframe,
                                    textvariable=self.gcVal)
        self.gcValLabel.pack(padx=5, fill=tk.X)

        if gcaGlobals.noChannels > 1:
            buttString = "Prepare " + gcaGlobals.instrName[0]
        else:
            buttString = "Prepare Arduino"

        self.startGC1 = ttk.Button(self.experframe,
                                   text=buttString,
                                   command=lambda chan=1:
                                   self.startCollect(chan))

        self.startGC1.pack(padx=5, pady=2, fill=tk.X)

        if gcaGlobals.noChannels == 2:
            buttString = "Prepare " + gcaGlobals.instrName[1]
            self.startGC2 = ttk.Button(self.experframe,
                                       text=buttString,
                                       command=lambda chan=2:
                                           self.startCollect(chan))
            self.startGC2.pack(padx=5, pady=2, fill=tk.X)

        ttk.Label(self.rightframe).pack()

        self.procframe = ttk.Frame(self.rightframe, relief=tk.SUNKEN)
        self.procframe.pack(fill=tk.BOTH, pady=5, padx=5)

        ttk.Label(self.procframe, text="Processing",
                  font=('Helvetica', 16, 'bold')).pack(padx=5,
                                                       pady=10,
                                                       fill=tk.X)

        ttk.Label(self.procframe, text="Method for Area Calculation",
                  font=('Helvetica', 14, 'bold italic')).pack(padx=5,
                                                              fill=tk.X)
        self.areaChooseVar = tk.StringVar()
        self.areaChooseVar.set(gcaGlobals.areaChoice)
        self.areaChoose1 = ttk.Radiobutton(self.procframe,
                                           var=self.areaChooseVar,
                                           text="addition",
                                           value="addition",
                                           command=self.areaChooseChange)
        self.areaChoose2 = ttk.Radiobutton(self.procframe,
                                           var=self.areaChooseVar,
                                           text="trapezoidal",
                                           value="trapezoidal",
                                           command=self.areaChooseChange)
        self.areaChoose1.pack(padx=25, fill=tk.X)
        self.areaChoose2.pack(padx=25, fill=tk.X)

        ttk.Label(self.experframe).pack()

        ttk.Label(self.procframe,
                  text="Automatic Reprocessing",
                  font=('Helvetica', 14, 'bold italic')).pack(padx=5,
                                                              fill=tk.X)

        self.threshVarLabel = ttk.Label(self.procframe,
                                        text="Peak start threshhold")
        self.threshVarLabel.pack(padx=5, fill=tk.X)
        self.threshVar = tk.StringVar()
        self.threshVar.set(gcaGlobals.thresh)
        self.threshVarEntry = ttk.Entry(self.procframe,
                                        textvariable=self.threshVar)
        self.threshVarEntry.pack(padx=5, fill=tk.X)

        self.gradThreshVarLabel = ttk.Label(self.procframe,
                                            text="Peak start gradient \
threshhold")
        self.gradThreshVarLabel.pack(padx=5, fill=tk.X)
        self.gradThreshVar = tk.StringVar()
        self.gradThreshVar.set(gcaGlobals.gradThresh)
        self.gradThreshVarEntry = ttk.Entry(self.procframe,
                                            textvariable=self.gradThreshVar)
        self.gradThreshVarEntry.pack(padx=5, fill=tk.X)

        ttk.Label(self.procframe).pack()

        self.repAnalysisButton = ttk.Button(self.procframe,
                                            text="Find and Integrate Peaks",
                                            command=self.repeatAnalysis)
        self.repAnalysisButton.pack(padx=5, fill=tk.X)

        ttk.Label(self.procframe).pack()

        ttk.Label(self.procframe,
                  text="Manual Processing",
                  font=('Helvetica', 14, 'bold italic')).pack(padx=5,
                                                              fill=tk.X)

        self.manualPeaksButton = ttk.Button(self.procframe,
                                            text="Integrate Picked Peaks",
                                            command=self.manualPeaks)
        self.manualPeaksButton.pack(padx=5, fill=tk.X)

        self.clearPeaksButton = ttk.Button(self.procframe,
                                           text="Clear All Peaks",
                                           command=self.clearPeaks)
        self.clearPeaksButton.pack(padx=5, fill=tk.X)

        self.showBaselineVar = tk.BooleanVar()
        self.showBaselineVar.set(gcaGlobals.showBaseline)
        self.showBaseCheck = tk.Checkbutton(self.procframe,
                                            text="Show Calculated Baseline",
                                            variable=self.showBaselineVar,
                                            onvalue=True, offvalue=False,
                                            command=self.showBaseChange)
        self.showBaseCheck.pack()

        ttk.Label(self.procframe).pack()

        self.setCommentButton = ttk.Button(self.procframe,
                                           text="Set Comment for Experiment",
                                           command=self.setComment)
        self.setCommentButton.pack(padx=5, fill=tk.X)

        self.copyPeaksButton = ttk.Button(self.procframe,
                                          text="Copy Peaks to Clipboard",
                                          command=self.copyPeaks)
        self.copyPeaksButton.pack(padx=5, fill=tk.X)

    def checkSetup(self):
        """Function to grab current comment and set time for experiment.

        Checks validity of time value (must be positive number)
        """
        gcaGlobals.comment = self.commentEntry.get()
        timeExper = self.timeExperVar.get()
        try:
            if float(timeExper) < 0:
                raise ValueError
        except ValueError:
                tk.messagebox.showwarning("Time Value Problem",
                                          "Invalid value given for experiment \
                                          time")
                return False
        except:
            tk.messagebox.showwarning("Time Value Problem",
                                      "Problem with Time Value: \n\n" +
                                      str(sys.exc_info()))
        else:
            gcaGlobals.timeExper = timeExper
            return True

    def startCollect(self, channel):
        """
        Procedure to look for the beginning of data from the arduino.

        Upon start button being pushed (or being invoked from the end of a
        previous experiment at the end of queueExperiment in gcaserial),
        this procedure checks the setup of the experiment, getting the time
        of the experiment and the current comment, and then sends the
        parameters to the arduino.
        """
        def lookForData(root, searchString1, searchString2):
            import sys

            line = ""

            try:
                line = gcaGlobals.arduinoFile.readline().decode('utf-8')
            except IOError:
                print(sys.exc_info()[0])
            except:
                print(sys.exc_info()[0])

            if line != "":
                line = line.rstrip().split(' ')
                if (line[0] == searchString1):
                    gcaGlobals.ch1Running = True
                    root.after_cancel(gcaGlobals.afterid)
                    mw.dataNB.datanb.select(0)
                    mw.dataNB.startAnimation(1)
                    return
                elif (line[1] == searchString2):
                    gcaGlobals.ch2Running = True
                    root.after_cancel(gcaGlobals.afterid)
                    mw.dataNB.datanb.select(1)
                    mw.dataNB.startAnimation(2)
                    return
                else:
                    gcaGlobals.afterid = root.after(1000, lambda:
                                                    lookForData(root,
                                                                searchString1,
                                                                searchString2))
            else:
                gcaGlobals.afterid = root.after(1000, lambda:
                                                lookForData(root,
                                                            searchString1,
                                                            searchString2))

        mw = gcaGlobals.mainwind
        gcaGlobals.channel = str(channel)

        if not gcaGlobals.ch1Running and not gcaGlobals.ch2Running:
            if self.checkSetup():
                gcaGlobals.ard.setupExperiments(channel)
                lookForData(mw.root,
                            gcaGlobals.startString1,
                            gcaGlobals.startString2)
            else:
                tk.messagebox.showinfo("Experiment Aborted",
                                       "Experiment not started")
        elif gcaGlobals.ch1Running and gcaGlobals.ch2Running:
            tk.messagebox.showwarning("Experiments already started", "It \
appears that both channels are already collecting data.")
        elif channel == 1 and not gcaGlobals.ch1Running:
            if self.checkSetup():
                gcaGlobals.ard.setupExperiments(1)
        elif channel == 2 and not gcaGlobals.ch2Running:
            if self.checkSetup():
                gcaGlobals.ard.setupExperiments(2)
        else:
            mw.sendMessage("Channel Start Error",
                           "Neither channel 1 nor 2 started. Some error has\
occurred")

    def checkAddNewData(self, noExper, channel):
        """Function to check and see if data needs to be added into a new tab

        Checks to see if the length of the datalist is longer than the number
        of experiments passed to it. If so, this means that a dataset has been
        added to the list and therefore a new tab needs to be opened and
        displayed.
        """
        mw = gcaGlobals.mainwind

        if len(mw.dataList) > noExper:
            newframe = ttk.Frame(mw.dataNB.datanb)
            newframe.config(height=gcaGlobals.dataframeHeight,
                            width=gcaGlobals.dataframeWidth)
            mw.dataNB.datanb.insert(channel-1, newframe,
                                    text="Live Data " + str(channel))
            mw.dataNB.datanb.forget(channel)
            mw.dataNB.dataframelist[channel-1] = newframe

            mw.dataList[-1].tabTitle = "GC " + str(channel) + ": " + \
                mw.dataList[-1].timeStamp.split('-')[3]
            mw.dataList[-1].filename = mw.dataList[-1].tabTitle
            mw.dataNB.addDataFrame(mw.dataList[-1].tabTitle)
            mw.dataNB.datanb.select(len(mw.dataNB.dataframelist)-1)

    def deleteTab(self):
        """Function to delete currently selected tab.

        Checks to make sure that it is not one of the tabs for live data.
        """
        mw = gcaGlobals.mainwind

        currTab = mw.dataNB.datanb.select()
        currIndex = mw.dataNB.datanb.index(currTab)
        if currIndex < gcaGlobals.noChannels:
            tk.messagebox.showwarning("Close Tab Error",
                                      "Cannot close Live Data Tab")
        elif currIndex > 1:
            mw.dataNB.datanb.forget(currIndex)
            del mw.dataList[currIndex - gcaGlobals.noChannels]
            del mw.dataNB.dataframelist[currIndex]
        else:
            mw.dataNB.datanb.forget(currIndex)

    def areaChooseChange(self):
        """Function updates global variable for method to integrate area upon
        change of radiobuttons.

        Future Development:
            Move this function to menu
        """
        gcaGlobals.areaChoice = self.areaChooseVar.get()

    def repeatAnalysis(self):
        """Function called to repeat automatic analysis of data (presumably
        with new values for threshold and gradient threshold.)
        """
        mw = gcaGlobals.mainwind

        currTab = mw.dataNB.datanb.select()
        currIndex = mw.dataNB.datanb.index(currTab)
        if currIndex < gcaGlobals.noChannels:
            tk.messagebox.showwarning("Analysis Error",
                                      "Cannot analyze Live Data Tab")
        else:
            dataListIndex = currIndex - gcaGlobals.noChannels
        gT = float(self.gradThreshVar.get())
        thr = float(self.threshVar.get())
        gc.gcReProcessing(dataListIndex, thr, gT)
        if mw.dataList[dataListIndex].filename is None:
            mw.dataNB.addDataFrame(mw.dataList[dataListIndex].tabTitle,
                                   currIndex, dataListIndex)
        else:
            mw.dataNB.addDataFrame(
                mw.dataList[dataListIndex].tabTitle,
                currIndex, dataListIndex)
        mw.dataNB.datanb.select(currIndex)

    def clearPeaks(self):
        """Function removes all peaks from current data selected and replots
        data.
        """
        mw = gcaGlobals.mainwind
        currTab = mw.dataNB.datanb.select()
        currIndex = mw.dataNB.datanb.index(currTab)
        if currIndex < gcaGlobals.noChannels:
            tk.messagebox.showwarning("Analysis Error",
                                      "Cannot analyze Live Data Tab")
        else:
            dataListIndex = currIndex - gcaGlobals.noChannels
        gc.gcClearPeaks(dataListIndex)

        if mw.dataList[dataListIndex].filename is None:
            mw.dataNB.addDataFrame(mw.dataList[dataListIndex].tabTitle,
                                   currIndex, dataListIndex)
        else:
            mw.dataNB.addDataFrame(
                mw.dataList[dataListIndex].tabTitle,
                currIndex, dataListIndex)
        mw.dataNB.datanb.select(currIndex)

    def manualPeaks(self):
        """Function integrates peaks that have been manually picked by user
        and replots data.
        """
        mw = gcaGlobals.mainwind
        currTab = mw.dataNB.datanb.select()
        currIndex = mw.dataNB.datanb.index(currTab)
        if currIndex < gcaGlobals.noChannels:
            tk.messagebox.showwarning("Analysis Error",
                                      "Cannot analyze Live Data Tab")
        else:
            dataListIndex = currIndex - gcaGlobals.noChannels

        mw.dataList[dataListIndex].manualPeaks(gcaGlobals.manPeakList,
                                               gcaGlobals.baseSelect)
        if mw.dataList[dataListIndex].filename is None:
            mw.dataNB.addDataFrame(mw.dataList[dataListIndex].tabTitle,
                                   currIndex, dataListIndex)
        else:
            mw.dataNB.addDataFrame(mw.dataList[dataListIndex].tabTitle,
                                   currIndex, dataListIndex)
        mw.dataNB.datanb.select(currIndex)

    def showBaseChange(self):
        """Function to set global boolean to show calculated baseline or not
        """
        gcaGlobals.showBaseline = self.showBaselineVar.get()

        currTab = gcaGlobals.mainwind.dataNB.datanb.select()
        currIndex = gcaGlobals.mainwind.dataNB.datanb.index(currTab)
        if currIndex == 0:
            tk.messagebox.showwarning("Analysis Error",
                                      "Live Data Tab does not have baseline")

        dataListIndex = currIndex - gcaGlobals.noChannels
        if gcaGlobals.mainwind.dataList[dataListIndex].filename is None:
            gcaGlobals.mainwind.dataNB.addDataFrame(
                gcaGlobals.mainwind.dataList[dataListIndex].tabTitle,
                currIndex, dataListIndex)
        else:
            gcaGlobals.mainwind.dataNB.addDataFrame(
                gcaGlobals.mainwind.dataList[dataListIndex].tabTitle,
                currIndex, dataListIndex)
        gcaGlobals.mainwind.dataNB.datanb.select(currIndex)

    def setComment(self):
        """Function sets comment for selected data set and replots data with
        new comment in peak pick block.
        """
        mw = gcaGlobals.mainwind

        currTab = mw.dataNB.datanb.select()
        currIndex = mw.dataNB.datanb.index(currTab)

        if currIndex < gcaGlobals.noChannels:
            tk.messagebox.showwarning("Analysis Error",
                                      "Cannot analyze Live Data Tab")
            return
        else:
            dataListIndex = currIndex - gcaGlobals.noChannels

        gcaGlobals.comment = self.commentEntry.get()
        mw.dataList[dataListIndex].comment = gcaGlobals.comment

        if mw.dataList[dataListIndex].filename is None:
            mw.dataNB.addDataFrame(mw.dataList[dataListIndex].tabTitle,
                                   currIndex, dataListIndex)
        else:
            mw.dataNB.addDataFrame(mw.dataList[dataListIndex].tabTitle,
                                   currIndex, dataListIndex)
        mw.dataNB.datanb.select(currIndex)

    def copyPeaks(self):
        """Function copies space delimited table of peaks and peak areas to
        clipboard.
        """
        currTab = gcaGlobals.mainwind.dataNB.datanb.select()
        currIndex = gcaGlobals.mainwind.dataNB.datanb.index(currTab)
        if currIndex < gcaGlobals.noChannels:
            tk.messagebox.showwarning("Analysis Error",
                                      "Cannot analyze Live Data Tab")
        else:
            dataListIndex = currIndex - gcaGlobals.noChannels

        table = "Retention Time,Area,Relative Area\n"
        gc = gcaGlobals.mainwind.dataList[dataListIndex]
        for peak in gc.peaks:
            table += "{0:.3f}".format(gc.trace[0][peak.peakMax]) + "," + \
                "{0:.3f}".format(peak.peakArea) + "," + \
                "{0:.3f}".format(peak.relativePeakArea)+"\n"

        gcaGlobals.mainwind.root.clipboard_clear()
        gcaGlobals.mainwind.root.clipboard_append(table)


class bottomRightFrame():
    """Class for bottom right frame of GC-Arduino interface program for buttons

    This area shows information for connection of program to Arduino.
    """

    def __init__(self, parent):
        self.parent = parent
        self.bottomrightframe = ttk.Frame(self.parent)
        self.bottomrightframe.grid(column=1, row=1,
                                   sticky=(tk.N, tk.S, tk.E, tk.W))
        self.bottomrightframe.columnconfigure(0, weight=0)
        self.bottomrightframe.rowconfigure(0, weight=1)
        self.quitbutton = ttk.Button(self.bottomrightframe,
                                     text='quit',
                                     command=lambda: _quit(self.parent.master))
        self.quitbutton.grid(row=1, column=1, sticky=(tk.S, tk.E),
                             padx=10, pady=10)
        self.arduinoConsole = ttk.Frame(self.bottomrightframe)
        self.arduinoConsole.grid(row=0, column=0, columnspan=2,
                                 sticky=(tk.N, tk.S, tk.E, tk.W),
                                 padx=10, pady=10)

        if gcaGlobals.dataStation:
            self.stationNameVar = tk.StringVar()
            self.stationNameVar.set("Data Station")
            ttk.Label(self.arduinoConsole,
                      textvariable=self.stationNameVar,
                      font=('Helvetica', 14, 'bold')).pack()
            self.portNameVar = tk.StringVar()
            self.portNameVar.set("")
            self.portName = ttk.Label(self.arduinoConsole,
                                      textvariable=self.portNameVar,
                                      foreground='black')
            self.portName.pack()
            self.ardStatusVar = tk.StringVar()
            self.ardStatusVar.set("")
            self.ardStatus = ttk.Label(self.arduinoConsole,
                                       textvariable=self.ardStatusVar,
                                       foreground='blue')
            self.ardStatus.pack()
        else:
            self.stationNameVar = tk.StringVar()
            self.stationNameVar.set("Arduino Connection")
            ttk.Label(self.arduinoConsole,
                      textvariable=self.stationNameVar,
                      font=('Helvetica', 14, 'bold')).pack()
            self.portNameVar = tk.StringVar()
            self.portNameVar.set(gcaGlobals.arduinoCom)
            self.portName = ttk.Label(self.arduinoConsole,
                                      textvariable=self.portNameVar,
                                      foreground='black')
            self.portName.pack()
            self.ardStatusVar = tk.StringVar()
            self.ardStatusVar.set("Not Connected Yet")
            self.ardStatus = ttk.Label(self.arduinoConsole,
                                       textvariable=self.ardStatusVar,
                                       foreground='blue')
            self.ardStatus.pack()

    def updateArdConsole(self, message):
        """Function sets message of Arduino status.
        """
        self.ardStatusVar.set(message)


class bottomFrame():
    """Class for bottom frame of GC-Arduino interface program for buttons

    Currently, no information is printed in this area.
    Future Development:
        This area could be used for text area to hold longer lists of peaks
        This area could also be used for realtime signal from GC.
            This could be from a constant update from the Arduino about the GC
            signal
    """
    def __init__(self, parent):
        self.parent = parent
        self.bottomframe = ttk.Frame(self.parent)
        self.bottomframe.grid(column=0, row=1, sticky=(tk.N, tk.S, tk.E, tk.W))
        self.bottomframe.columnconfigure(0, weight=1)


class menuBar():
    """Class for the menubar
    """
    def __init__(self, parent):
        self.parent = parent
        self.menubar = tk.Menu(self.parent)
        self.filemenu = fileMenu(self.menubar)
        self.ardconfmenu = ardConnectMenu(self.menubar)
        self.confmenu = configMenu(self.menubar)
        self.helpmenu = helpMenu(self.menubar)
        self.menubar.add_cascade(label="File", menu=self.filemenu.fm)
        self.menubar.add_cascade(label="Arduino Communications",
                                 menu=self.ardconfmenu.acm)
        self.menubar.add_cascade(label="Configuration",
                                 menu=self.confmenu.conf)
        self.menubar.add_cascade(label="Help", menu=self.helpmenu.hm)


class fileMenu():
    """Class for the file menu items
    """
    def __init__(self, parent):
        self.parent = parent
        self.fm = tk.Menu(self.parent, tearoff=0)
        self.fm.add_command(label="Open", accelerator="Ctrl-O",
                            command=self.openFile)
        self.fm.add_command(label="Save", accelerator="Ctrl-S",
                            command=lambda: self.saveFile())
        self.fm.add_command(label="Save As",
                            command=lambda: self.saveFileAs())
        self.fm.add_command(label="Save Multiple As",
                            command=lambda: self.saveMultipleFileAs())

    def saveFile(self):
        """Save previously saved file.
        """
        mw = gcaGlobals.mainwind

        currentExpSelect = mw.dataNB.datanb.select()
        currentExpIndex = mw.dataNB.datanb.index(currentExpSelect) - 1
        gcafio.saveFile(mw.dataList[currentExpIndex])
        tabtitle = mw.dataList[currentExpIndex].shortfile
        mw.dataNB.datanb.tab(currentExpIndex + 1,
                             text=tabtitle)

    def saveFileAs(self):
        """Save with changed name or with different extension.
        """
        mw = gcaGlobals.mainwind

        currentExpSelect = mw.dataNB.datanb.select()
        currentExpIndex = mw.dataNB.datanb.index(currentExpSelect) - \
            gcaGlobals.noChannels
        gcafio.saveFileAs(mw.dataList[currentExpIndex])
        tabtitle = mw.dataList[currentExpIndex].shortfile
        mw.dataList[currentExpIndex].tabTitle = tabtitle
        mw.dataNB.datanb.tab(currentExpIndex + gcaGlobals.noChannels,
                             text=tabtitle)

    def saveMultipleFileAs(self):
        """Function saves multiple tabs of data in one file.

        Currently operates by generating dictionary of names and
            GasChromatogram objects that are then displayed with radiobuttons
            for selection. The user then selects those data tabs desired and
            clicks on choose button. This data is then passed to function from
            gcafileio to actually save the data.

        Future Development:
            This routine needs to be changed to have check marks on the data
            tabs themselves that can be selected to mark for saving. Would also
            need a clear all function.
        """
        def states(chosen, dataDict):
            """Gets states of radiobuttons and actually passes them to
            gcafileio routine.
            """
            l = []
            for item in chosen:
                if item[0].get():
                    l.append(dataDict[item[1]])
            gcafio.saveMultipleFileAs(l)
            fileChoose.destroy()

        mw = gcaGlobals.mainwind

        dataDict = {gc.tabTitle: gc for gc in mw.dataList}
        fileChoose = tk.Toplevel()

        tk.Label(fileChoose, text="Select data to save to a single file.",
                 font="bold").pack()
        tk.Label(fileChoose).pack()

        chosen = []
        for tab in list(dataDict.keys()):
            var = tk.IntVar()
            check = tk.Checkbutton(fileChoose, text=tab, variable=var)
            check.pack()
            chosen.append([var, tab])

        button = tk.Button(fileChoose, text="Choose", command=lambda:
                           states(chosen, dataDict))
        button.pack(side=tk.BOTTOM, padx=5, pady=5)

    def openFile(self):
        """Function to open file. Calls gcafileio function.
        """
        def fixBkwdCompat(dataset):
            """Function to deal with backwards compatibility of datasets.

            This function is likely to be constantly in flux with each revision
            of the program. Anytime that there is a change in the format of the
            GasChromatogram object, these changes would need to be reflected
            here so that old data could still be read.
            """
            try:
                if dataset.tabTitle == "":
                    dataset.tabTitle = sfn
            except AttributeError:
                dataset.tabTitle = sfn
            try:
                if dataset.instrName == "":
                    dataset.instrName = ""
            except AttributeError:
                dataset.instrName = ""
            try:
                if dataset.baselineCalc != []:
                    pass
                else:
                    dataset.baselineCalc = 0
            except:
                dataset.baselineCalc = 0
                
            return dataset

        mw = gcaGlobals.mainwind

        newData, fn, sfn = gcafio.openFile()
        if newData is not None:
            existList = []
            for data in mw.dataList:
                existList.append(data.filename)
            for indivNewData in newData:
                newFilename = indivNewData.filename
                if newFilename in existList:
                    msg = "File "+newFilename+" already exists.  \n\n Do you \
want to reopen the data (this will overwrite the existing data)?"
                    if tk.messagebox.askokcancel("File Exists", msg):
                        frameNo = existList.index(newFilename) + \
                            gcaGlobals.noChannels
                    else:
                        frameNo = 999        # user cancelled, don't open file
                else:
                    frameNo = -1        # no files match, append to end of list
                if frameNo == -1:
                    indivNewData = fixBkwdCompat(indivNewData)
                    mw.dataList.append(indivNewData)
                    mw.dataNB.addDataFrame(indivNewData.tabTitle)
                    mw.dataNB.datanb.select(len(mw.dataList)+1)
                    mw.root.update_idletasks()
                elif frameNo != 999:
                    mw.dataList.append(indivNewData)
                    mw.dataNB.addDataFrame(indivNewData.tabTitle,
                                           frameNo,
                                           frameNo-gcaGlobals.noChannels+1)
                    mw.dataNB.datanb.select(frameNo)
                    mw.root.update_idletasks()
                elif frameNo == 999:
                    pass                    # Did not open file
        else:
            mw.sendMessage("File Open Failed", "Some sort of error occurred.\n\
\nThe file was not opened.")


class ardConnectMenu():
    """Class for arduino connection menu
    """

    def __init__(self, parent):
        def convToInstr():
            gcaGlobals.dataStation = False
            self.__init__(self.parent)
            gcaGlobals.mainwind.resetMenus()
            connectToArduino()
            selectLiveTab()

        def convToData():
            gcaGlobals.dataStation = True
            closeArduino()
            gcaGlobals.runRWgc = False
            self.__init__(self.parent)
            gcaGlobals.mainwind.resetMenus()

        self.parent = parent
        self.acm = tk.Menu(self.parent, tearoff=0)
        if gcaGlobals.dataStation:
            self.acm.add_command(label="Convert to Instrument Station",
                                 command=convToInstr)
        else:
            self.acm.add_command(label="Connect to Arduino",
                                 command=connectToArduino)
            self.acm.add_command(label="Reset Arduino",
                                 command=resetArduino)
            self.acm.add_command(label="Close Arduino",
                                 command=closeArduino)
            self.portmenu = portMenu(self.acm)
            self.acm.add_cascade(label="Set Arduino Port",
                                 menu=self.portmenu.ports)
            self.acm.add_separator()
            self.acm.add_command(label="Convert to DataStation",
                                 command=convToData)


class portMenu():
    """Class for list of ports available menu

    Newly implemented: getPortDict allows rechecking of ports list. Needs to be
    debugged using a serial port.
    """
    def __init__(self, parent):
        self.parent = parent
        self.ports = tk.Menu(self.parent, tearoff=0)
        self.portchosen = tk.StringVar()
        self.portchosen.set(gcaGlobals.arduinoCom)
        for key in gcaGlobals.portDict:
            self.ports.add_radiobutton(label=gcaGlobals.portDict[key],
                                       variable=self.portchosen,
                                       value=gcaGlobals.portDict[key],
                                       command=self.setArduinoCom)
        self.ports.add_command(label="Recheck Port List",
                               command=self.getPortDict)

    def setArduinoCom(self):
        gcaGlobals.arduinoCom = self.portchosen.get()

    def getPortDict(self):
        gcaGlobals.portDict = gcaGlobals.getPortDict()


class configMenu():
    """Class for configuration of arduino/gc
    """
    def __init__(self, parent):
        self.parent = parent
        self.conf = tk.Menu(self.parent, tearoff=0)
        self.multCheckVar = tk.BooleanVar()
        self.multCheckVar.set(gcaGlobals.multRuns)
        self.conf.add_command(label="Multiple Runs")
        self.conf.add_checkbutton(label="   Allow",
                                  variable=self.multCheckVar,
                                  onvalue=True,
                                  offvalue=False,
                                  command=self.multCheckChange)
        self.adcChooseVar = tk.StringVar()
        self.adcChooseVar.set(gcaGlobals.adcChoice)
        self.conf.add_separator()
        self.conf.add_command(label="ADC Choice")
        for key in gcaGlobals.adcChoices:
            self.conf.add_radiobutton(label="   " + gcaGlobals.adcChoices[key],
                                      variable=self.adcChooseVar,
                                      value=gcaGlobals.adcChoices[key],
                                      command=self.adcChooseChange)

    def adcChooseChange(self):
        """Updates global adcChoice upon radiobutton change.
        """
        gcaGlobals.adcChoice = self.adcChooseVar.get()

    def multCheckChange(self):
        """Updates global multRuns upon checkbutton change.
        """
        gcaGlobals.multRuns = self.multCheckVar.get()


class helpMenu():
    """Class for simple help instructions
    """
    def __init__(self, parent):
        self.parent = parent
        self.hm = tk.Menu(self.parent, tearoff=0)
        self.hm.add_command(label="Open Instructions",
                            command=self.openPDFFile)

    def openPDFFile(self):
        """Opens pdf file for help instructions.
        """
        import os
        import subprocess
        if gcaGlobals.platform == 'win':
            cmd = 'start ' + gcaGlobals.helpfile
            os.system(cmd)
        elif gcaGlobals.platform == 'linux':
            subprocess.call(["xdg-open", gcaGlobals.helpfile])
        elif gcaGlobals.platform == 'mac':
            cmd = 'open ' + gcaGlobals.helpfile
            os.system(cmd)
