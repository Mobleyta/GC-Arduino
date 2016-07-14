# -*- coding: utf-8 -*-
"""
Module for functions to handle file input/output for GCReaderTK program.

Created on Mon Feb  8 19:18:55 2016

@author:
T. Andrew Mobley
Department of Chemistry
Noyce Science Center
Grinnell College
Grinnell, IA 50112
mobleyt@grinnell.edu
"""
import gcaglobals as gcaGlobals
import tkinter.filedialog as filedialog
import os
from tkinter import messagebox
import pickle


def openFile():
    """Opens file for further processing.
    Current Limitations: The only file type that currently can be opened is the
    native .gcard datatype. Maybe should extend to be able to open simple csv
    files of time, intensity.
    """
    filename = filedialog.askopenfilename()
    waste, ext = os.path.splitext(filename)
    waste, shortfilename = os.path.split(filename)
    if ext != ".gcard":
        messagebox.showinfo("Invalid filetype", "This program can currently \
only open the gcard file type (native to this program).")
        return None
    else:
        with open(filename, 'rb') as inputf:
            try:
                return pickle.load(inputf), filename, shortfilename
            except:
                messagebox.showinfo("File open error", "Trouble reading file")
                return None


def saveFile(gcExp, extension=".gcard"):
    """Saves file.
    Saves two types of file:
        .gcard native format (with pickle to save GasChromatogram object)
        .csv or any other ext (space separated time intensity line feed)
    """
    if (gcExp.filename is None):
        filename = getFilename(extension)
    else:
        filename = gcExp.filename
    waste, ext = os.path.splitext(filename)
    waste, shortfilename = os.path.split(filename)
    if ext == ".gcard":
        try:
            gcExp.shortfile, waste = os.path.splitext(shortfilename)
            gcExp.filename = filename
            gcExp.tabTitle = gcExp.shortfile
            with open(filename, 'wb') as outf:
                pickle.dump([gcExp], outf, pickle.HIGHEST_PROTOCOL)
            return filename
        except:
            messagebox.showinfo("File write error", "There was a problem \
writing to the " + ext + " file.")
            return None
    else:
        try:
            with open(filename, 'w') as outf:
                timePoints = gcExp.trace[0]
                yPoints = gcExp.trace[1]
                for i in len(timePoints):
                    outf.write(timePoints[i] + " " +
                               yPoints[i] + "\r\n")
                outf.write("\r\n")
            return filename
        except:
            messagebox.showinfo("File write error", "There was a problem \
writing to the " + ext + " file.")
            return None


def saveFileAs(gcExp, extension=".gcard"):
    """Saves file with new name or in different format with different extension
    Saves two types of file:
        .gcard native format (with pickle to save GasChromatogram object)
        .csv or any other ext (space separated time intensity line feed)
    """
    filename = getFilename(extension)
    waste, ext = os.path.splitext(filename)
    waste, shortfilename = os.path.split(filename)
    if ext == ".gcard":
        try:
            gcExp.shortfile, waste = os.path.splitext(shortfilename)
            gcExp.filename = filename
            gcExp.tabTitle = gcExp.shortfile
            with open(filename, 'wb') as outf:
                pickle.dump([gcExp], outf, pickle.HIGHEST_PROTOCOL)
            return filename
        except:
            messagebox.showinfo("File write error", "There was a problem \
writing to the " + ext + " file.")
            return None
    else:
        try:
            with open(filename, 'w') as outf:
                timePoints = gcExp.trace[0]
                yPoints = gcExp.trace[1]
                for i in range(len(timePoints)):
                    outf.write(str(timePoints[i]) + " " +
                               str(yPoints[i]) + "\r\n")
                outf.write("\r\n")
            return filename
        except:
            messagebox.showinfo("File write error", "There was a problem \
writing to the " + ext + " file.")
            return None


def saveMultipleFileAs(listOfGCExp, extension=".gcard"):
    """Stub for future development.
    Should take list of GasChromatogram objects and save them.
    To develop, need to implement method to choose list from current
    experiments, and then save the list, possibly to a different extension
    (lgcard?) or to the same extension. If the former (easier), openFile then
    recognizes new extension and executes opening of a list rather than
    individual GasChromatogram object. If the latter, then it is necessary
    for openFile to recognize the difference in the format (that it is a list)
    and open the file appropriately.
    """
    import sys

    filename = getFilename(extension)
    waste, ext = os.path.splitext(filename)
    waste, shortfilename = os.path.split(filename)
    if ext == ".gcard":
        try:
            counter = 1
            for exp in listOfGCExp:
                if counter > 1:
                    exp.shortfile, waste = os.path.splitext(shortfilename)
                    exp.shortfile = exp.shortfile + " " + str(counter)
                    exp.filename = filename + " " + str(counter)
                    exp.tabTitle = exp.shortfile
                else:
                    exp.shortfile, waste = os.path.splitext(shortfilename)
                    exp.filename = filename
                    exp.tabTitle = exp.shortfile
                counter += 1
            with open(filename, 'wb') as outf:
                pickle.dump(listOfGCExp, outf, pickle.HIGHEST_PROTOCOL)
            return filename
        except:
            messagebox.showinfo("File write error", "There was a problem \
writing to the " + ext + " file.")
            print(sys.exc_info())
            return None
    else:
        try:
            with open(filename, 'w') as outf:
                for gcExp in listOfGCExp:
                    timePoints = gcExp.trace[0]
                    yPoints = gcExp.trace[1]
                    for i in range(len(timePoints)):
                        outf.write(str(timePoints[i]) + " " +
                                   str(yPoints[i]) + "\r\n")
                    outf.write("\r\n")
            return filename
        except:
            messagebox.showinfo("File write error", "There was a problem \
writing to the " + ext + " file.")
            return None


def getFilename(extension):
    """Routine to return a filename using OS filedialog request.
    """
    filename = filedialog.asksaveasfilename(initialdir=gcaGlobals.outDirectory,
                                            defaultextension=extension,
                                            filetypes=[("gcard file",
                                                        "*.gcard"),
                                                       ("txt file", "*.txt")])
    gcaGlobals.outDirectory = os.path.dirname(filename)
    return filename
