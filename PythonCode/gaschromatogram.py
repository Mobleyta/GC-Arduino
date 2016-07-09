"""
Module for various aspects of holding and interpreting GC data

Major structure is GasChromatogram class which is used to make a
GasChromatogram object for every GC trace acquired.

This object consists of:
    the actual trace
    information about the acquisition
        time
        instrument
        user comment
    information about the storage file
        filename (actually full path with filename)
        shortfile (just the actual filename)
        title for tab in notebook
    information about processed data
        threshold and gradient threshold levels used to process
        points identified as baseline points in the trace
        calculated baseline points
        a list of peaks (each a Peak object)

Known Issue:
    Need to think about backwards compatibility in opening and saving files
    to allow for future modifications of this class.
    Partially handled currently in fixBkwdCompat() of openFile() in
    gcarduinowindow.py

Future Development:
    If other GC Instruments are added, this could be a root Class that other
    individual classes (e.g. HP5989) would inherit and then modify.

Created on Sun Jan 31 19:22:19 2016

@author:
T. Andrew Mobley
Department of Chemistry
Noyce Science Center
Grinnell College
Grinnell, IA 50112
mobleyt@grinnell.edu
"""

import numpy as np
import gcardglobals as gcaGlobals


class GasChromatogram():
    """
    Class for gas chromatography data.
    """

    def __init__(self, trace, timeStamp, thresh, gradThresh,
                 comment="", instrName=""):

        self.trace = trace

        self.timeStamp = timeStamp
        self.instrName = instrName
        self.comment = comment

        self.saved = False
        self.filename = None
        self.shortfile = None
        self.tabTitle = None

        self.thresh = thresh
        self.gradThresh = gradThresh
        self.baselineIndex = []
        self.baseline = []
        self.baselineCalc = []
        self.peaks = []

    def findPeaks(self):
        """Routine to automatically find peaks.  First looks for start of peak.
        Once found, the end of peak is searched for. When the peak end
        is found, the peakMax is determined, the peakArea is
        determined and then the peak is appended to the list of peaks.
        The routine then moves back to finding a peak start (if the peak end
        was a valley, peakStart is set to the previous peakEnd).  When all
        points in the trace have been searched and all peaks found, the
        normalized area is calculated and set for each of the peaks.
        For automatic routine, baseline is simply calculated as average of
        points immediately preceding peakStart.

        Shortcoming: peaks that are riding on larger peaks are not dealt
        with in a reasonable way. Future development could include
        recalculating baseline for riding peaks to better emulate curve of
        underlying peak.
        """
        timePoints = self.trace[0]
        yPoints = self.trace[1]
        self.baselineCalc = {}

        if len(yPoints) > gcaGlobals.inBaseCt:       # Minimum 10 pts. for data
            yGradients = np.gradient(yPoints).tolist()
            self.baselineIndex = [0]
            self.baseline = yPoints[0:gcaGlobals.inBaseCt-1]
            # define the 1st 10 pts as baseline
            currentIndex = 0                # define start point for analysis
            currentBaseline = (sum(yPoints[0:gcaGlobals.inBaseCt-1]) /
                               gcaGlobals.inBaseCt)  # 1st 10 pts init baseline
            valley = False
            peakEnd = None

            while currentIndex < len(yPoints) - 1:
                peakStart = None
                if valley:
                    if peakEnd:
                        peakStart = peakEnd
                        valley = False
                else:
                    peakStart, currentBaseline = self.findStart(yPoints,
                                                            yGradients,
                                                            currentBaseline,
                                                            currentIndex)

                if peakStart:
                    peakEnd, valley = self.findEnd(yPoints, yGradients,
                                                   currentBaseline, peakStart)
                    if peakEnd:
                        currentIndex = peakEnd
                        peakMax = self.findPeakMax(yPoints, peakStart, peakEnd)
                        peakArea = 100*self.findPeakArea(yPoints, timePoints,
                                                         peakStart, peakEnd,
                                                         currentBaseline,
                                                         gcaGlobals.areaChoice)
                        self.peaks.append(Peak(peakStart, peakEnd,
                                               peakMax, peakArea,
                                               currentBaseline, 0))
                    else:       # If no peak end, must be at end of dataset
                        currentIndex = len(yPoints) - 1
                        peakEnd = currentIndex  # set pk end to last data point
                        peakMax = self.findPeakMax(yPoints, peakStart, peakEnd)
                        peakArea = 100*self.findPeakArea(yPoints, timePoints,
                                                         peakStart, peakEnd,
                                                         currentBaseline,
                                                         gcaGlobals.areaChoice)
                        self.peaks.append(Peak(peakStart, peakEnd,
                                               peakMax, peakArea,
                                               currentBaseline, 0))
                else:
                    currentIndex = len(yPoints)
                    self.baselineCalc[currentIndex] = currentBaseline
        else:   # Data set has less than 15 (default) points
            self.peaks = []

        pkBases = {}
        pkIndex = []        # List to contain all pts. incl. in peaks
        for pk in self.peaks:
            pkStart = pk.peakStart
            pkEnd = pk.peakEnd
            if pkEnd < len(yPoints):
                pkEnd = pkEnd + 1
            for i in list(range(pkStart, pkEnd)):
                pkIndex.append(i)
                pkBases[i] = pk.peakBaseline
# concatenate this peak's pts. to pkIndex list
# get baseline for each peak, associate with indices within peaks

        self.baselineIndex = list(set(range(len(yPoints))) - set(pkIndex))
# baseline index is all other points
        self.baseline = []
        self.baselineCalc.update(pkBases)
        baselineList = []

        for i in list(self.baselineCalc.keys()):
            baselineList.append(self.baselineCalc[i])
        self.baselineCalc = baselineList
        self.findNormalizedArea()

    def manualPeaks(self, manualPeakList=[], baseStEnd=[]):
        """Routine to process peaks manually after they have been identified
        by user peak picking. First it merges and sorts the existing peaks with
        those manually picked, if necessary. It then collects all points
        in the peaks, and finds the baseline points by set difference.
        A baseline is then calculated. Individual peaks are then processed
        to find peakMax and peakArea (using the calculated baseline).
        Finally peak areas are normalized.

        Shortcoming: The baseline calculation takes into account the fact that
        the timepoints might not be evenly spaced; HOWEVER, the calculation
        for the baseline underneath an individual peak does not!
        """
        peaks = self.peaks

        if manualPeakList == []:
            gcaGlobals.mainwind.sendMessage("No Peaks",
                                            "No manual peaks to process")
            return
        if peaks == []:     # There are no pre-existing peaks to contend with
            manualPeakList = list(zip(manualPeakList[::2],
                                      manualPeakList[1::2]))  # [(start, end)]
        else:
            oldpeaks = []
            for peak in peaks:      # Move existing peaks into list
                oldpeaks.append((peak.peakStart, peak.peakEnd))
            manualPeakList = list(zip(manualPeakList[::2],
                                      manualPeakList[1::2]))  # [(start, end)]
            manualPeakList = manualPeakList + oldpeaks
            manualPeakList.sort()

        timePoints = self.trace[0]
        yPoints = self.trace[1]

        pkIndex = []        # List to contain all pts. incl. in peaks
        for pk in manualPeakList:
            pkStart = pk[0]
            pkEnd = pk[1]
            if pkEnd != len(yPoints) + 1:
                pkEnd = pkEnd + 1
            pkIndex = pkIndex + list(range(pkStart, pkEnd))

# concatenate this peak's pts. to pkIndex list
        if baseStEnd == []:
            self.baselineIndex = list(set(range(len(yPoints))) - set(pkIndex))
        else:
            self.baselineIndex = list(set(range(baseStEnd[0], baseStEnd[1])) -
                                      set(pkIndex))

# baseline pts are all points not included in pks
        self.baseline = []
        baselineTimes = []
        for i in self.baselineIndex:
            self.baseline.append(yPoints[i])
            baselineTimes.append(timePoints[i])

        baselineCalc = self.calculateBaseline(self.baseline,
                                              baselineTimes,
                                              timePoints)

        newpeaks = []
        for pk in manualPeakList:
            pkStart = pk[0]
            pkEnd = pk[1]
            pkMax = self.findPeakMax(yPoints, pkStart, pkEnd)

# This calculation for current baseline assumes equal spacing of timepoints.
            currentBaseline = sum(baselineCalc[pkStart:pkEnd])/(pkEnd-pkStart)

            pkArea = 100 * self.findPeakArea(yPoints, timePoints, pkStart,
                                             pkEnd, currentBaseline,
                                             gcaGlobals.areaChoice)
            newpeaks.append(Peak(pkStart,
                                 pkEnd, pkMax, pkArea, currentBaseline, 0))
        self.peaks = newpeaks
        self.baselineCalc = baselineCalc
        self.findNormalizedArea()
        gcaGlobals.manPeakList = []
        gcaGlobals.baseSelect = []

    def calculateBaseline(self,
                          baseline, baselineTimes, timePoints, func="5th"):
        """Calculate the baseline for entire GC trace.  Currently this is a
        tenth order polynomial. This function seemed to work well with very
        small peaks on a pretty flat baseline. The accuracy of this baseline
        calculation has not been tested on multiple data sets. This routine
        could be upgraded to allow other functions to be utilized to calculate
        the baseline.
        """
        x = np.array(baselineTimes)
        y = np.array(baseline)
        if func == "5th":
            fit = np.polyfit(x, y, 5)
            ycalc = np.poly1d(fit)
            baselineCalc = []
            for i in timePoints:
                baselineCalc.append(ycalc(i))
        return baselineCalc

    def findNormalizedArea(self):
        """Returns normalized area for peaks that are held in the
        GasChromatograph object that called it.
        """
        import tkinter as tk
        import warnings

# To help catch mathematics calculation warnings to show users
        warnings.filterwarnings('error', category=RuntimeWarning)

        totalPeakArea = 0
        msgStr = ""

        for peak in self.peaks:
            totalPeakArea += peak.peakArea
        for i in range(len(self.peaks)):
            try:
                self.peaks[i].relativePeakArea = \
                    100 * self.peaks[i].peakArea/totalPeakArea
            except RuntimeWarning as msg:
                msgStr = "There was an error in normalizing the peaks: \n\n" +\
                    str(msg)

        if msgStr != "":
            tk.messagebox.showerror("Error in Normalizing Peaks", msgStr)

    def findStart(self, yPts, yGrads, currBase, currIndex):
        """Find beginning of a peak using gradient method. The gradient
        threshold (gradThresh) and the height threshold (thresh) are held in
        the GasChromatograph object that called it.

        Algorithm:

        [An initial baseline value is provided by the calling
        routine (currBase).]

        1) For each point (i) in the remaining yGradients
           a peakStart is found
            IF the gradient at i is higher than the gradThresh
            and IF the next gradient point (i+1) is higher than gradThresh
            and IF the yValue of the next point (i+1) is higher than thresh
            [If a peakStart is found, the actually peakStart is placed at the
            point before the point i]
          if no peakStart is found at point i
            IF point i is < 2 * thresh above current baseline
                add it to the baseline list
                   [This conditional is to prevent climb of baseline at
                   beginning of peak, thus preventing detection of slow
                   rising peaks.]
            Recalculate the new baseline value on the last 15 (default) pts. of
            baseline
        2) When a peakStart has been found, return it with the current baseline
        3) If no peakStart is found in remaining points, return None as pkStart
        """
        found = False

        for i in range(len(yGrads) - currIndex - 1):
            if (yGrads[currIndex + i] > self.gradThresh) and \
                    (yGrads[currIndex + i + 1] > self.gradThresh) and \
                    (yPts[currIndex + i + 1] > (self.thresh + currBase)):
                pkStart = currIndex + i - 1
                found = True
                break
            else:
                if (yPts[currIndex + i] < (2 * self.thresh + currBase)):
                    self.baselineIndex.append(currIndex + i)
                self.baselineCalc[currIndex + i] = currBase
                if len(self.baselineIndex) < gcaGlobals.inBaseCt:
                    currBase = 0
                    for i in self.baselineIndex:
                        currBase += yPts[i]
                    currBase = currBase/len(self.baselineIndex)
                else:
                    currBase = 0
                    for i in self.baselineIndex[-gcaGlobals.inBaseCt:]:
                        currBase += yPts[i]
                    currBase = currBase/gcaGlobals.inBaseCt
        if found:
            return pkStart, currBase
        else:
            return None, currBase

    def findEnd(self, yPts, yGrads, currBase, pkStart):
        """Find end of a peak. The gradient
        threshold (gradThresh) and the height threshold (thresh) are held in
        the GasChromatograph object that called it.

        Algorithm:

        1) Assume that we are initially on upward slope
        2) From the pkStart that is passed by calling procedure, for each
            point i
            IF gradient point i is negative, assume we are now on downslope

            Once we are on downslope:
                IF gradient at point i is < gradThresh/5
                and IF yValue of point i < current baseline + thresh
                THEN we have found the end of the peak,
                    return peakEnd at pt i with valley set to false
            However,
                IF the gradient at point i > 0 and a peakEnd has not been found
                    THEN we have found a valley,
                        return peakEnd at pt i with valley set to true
         3) If no peakEnd found, return None and valley set to False
        """
        downslope = False
        for i in range(len(yGrads) - pkStart - 1):
            if (not downslope) and (yGrads[pkStart + i] < 0):
                downslope = True
            elif ((downslope) and
                  ((abs(yGrads[pkStart + i]) < self.gradThresh/5) and
                  (yPts[pkStart + i] < (currBase + self.thresh)))):
                return pkStart + i, False        # Found peak end
            elif (downslope) and (yGrads[pkStart + i] > 0):
                if (yGrads[pkStart + i + 1] > 0):
                    return pkStart + i, True     # Found peak valley
        return None, False           # Found no end

    def findPeakMax(self, yPts, pkStart, pkEnd):
        """Find top of a peak. Finds peakMax by comparing successive points.
        If there are multiple consecutive points with some max value, takes
        average of all of the time points. Returns index of peakMax.
        """
        pkMax = 0
        multiple = 1
        pkMaxPoint = 0

        for point in range(pkStart, pkEnd):
            if yPts[point] == pkMax:
                multiple += 1
                pkMaxPoint += point
            elif yPts[point] > pkMax:
                pkMaxPoint = point
                pkMax = yPts[point]
                multiple = 1
        return int(pkMaxPoint/multiple)

    def findPeakArea(self, yPts, tPts, pkStart,
                     pkEnd, currBase, method="addition"):
        """Finds area of a given peak as defined by pkStart and pkEnd passed
        by calling routine. Two methods are implemented:

        Addition: simply adds y-Values subtracting out current baseline value
            that was passed by the calling routine
        Trapezoidal: utilizies numpy routine to estimate area, the yPoints that
            are passed are corrected by substracting out current baseline at
            each point.
        """
        pkArea = 0
        yPtsCorr = list(yPts)
        if method == "addition":
            for point in range(pkStart, pkEnd):
                pkArea += yPts[point] - currBase
            pkArea = pkArea/(tPts[pkEnd]-tPts[pkStart])
        elif method == "trapezoidal":
            for point in range(pkStart, pkEnd):
                yPtsCorr[point] = yPts[point] - currBase
            pkArea = np.trapz(yPtsCorr[pkStart:pkEnd], tPts[pkStart:pkEnd])
        return pkArea


class Peak():
    """Class for an individual peak within a gas chromatogram.
    Will hold peakStart, peakEnd, peakMax as (index, maximum value), peakArea
    """

    def __init__(self, peakStart, peakEnd, peakMax, peakArea, peakBaseline,
                 relativePeakArea):
        self.peakStart = peakStart     # index of timePoints, yPoints
        self.peakEnd = peakEnd         # index of timePoints, yPoints
        self.peakMax = peakMax         # index of timePoint, yPoints
        self.peakArea = peakArea       # Area under curve
        self.peakBaseline = peakBaseline
        self.relativePeakArea = relativePeakArea


def gcProcessing(newData, timeStamp, instrName):
    """Procedure for taking initial data from experiment and processing it into
    GasChromatogram class.  Calls individual methods within GasChromatogram
    to do the various processing. It then adds the new instance of
    GasChromatogram to the global list of experiments.
    """

    newGCExp = GasChromatogram(newData, timeStamp,
                               gcaGlobals.thresh, gcaGlobals.gradThresh,
                               gcaGlobals.comment, instrName)
    newGCExp.findPeaks()
    gcaGlobals.mainwind.dataList.append(newGCExp)


def gcReProcessing(dataListIndex, thresh, gradThresh):
    """Procedure for taking existing data from experiment and processing it
    into GasChromatogram class.  Calls individual methods within
    GasChromatogram to do the various processing. It then replaces the existing
    instance of GasChromatogram in the global list of experiments with new one.
    """
    reprocGCExp = gcaGlobals.mainwind.dataList[dataListIndex]
    gcClearPeaks(dataListIndex)
    gcClearBaseline(dataListIndex)
    reprocGCExp.thresh = thresh
    reprocGCExp.gradThresh = gradThresh
    reprocGCExp.findPeaks()
    gcaGlobals.mainwind.dataList[dataListIndex] = reprocGCExp


def gcClearPeaks(dataListIndex):
    """Procedure for removing peaks from a given data set.
    """
    clearPeakGCExp = gcaGlobals.mainwind.dataList[dataListIndex]
    clearPeakGCExp.peaks = []
    gcaGlobals.mainwind.dataList[dataListIndex] = clearPeakGCExp


def gcClearBaseline(dataListIndex):
    """Procedure for removing baseline information from a data set.
    """
    clearBaseGCExp = gcaGlobals.mainwind.dataList[dataListIndex]
    clearBaseGCExp.baselineIndex = []
    clearBaseGCExp.baseline = []
    clearBaseGCExp.baselineCalc = []
    gcaGlobals.mainwind.dataList[dataListIndex] = clearBaseGCExp
