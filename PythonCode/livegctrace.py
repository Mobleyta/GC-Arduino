# -*- coding: utf-8 -*-
"""
This routine is adapted from the Matplotlib example:
http://matplotlib.org/examples/animation/strip_chart_demo.html

animation example code: strip_chart_demo.py

Original Header:
Emulate an oscilloscope.  Requires the animation API introduced in
matplotlib 1.0 SVN.


Created on Tue Jan 26 16:21:27 2016

@author:
T. Andrew Mobley
Department of Chemistry
Noyce Science Center
Grinnell College
Grinnell, IA 50112
mobleyt@grinnell.edu
"""

from matplotlib.lines import Line2D


class LiveGCTrace(object):
    def __init__(self, ax, maxt=1):
        self.ax = ax
        self.maxt = maxt
        self.tdata = [0]
        self.ydata = [0]
        self.line = Line2D(self.tdata, self.ydata)
        self.ax.add_line(self.line)
        self.ax.set_ylim(0, 1.2)
        self.ax.set_xlim(0, self.maxt)

    def update(self, dataPoint):
        lastt = self.tdata[-1]
        if lastt > self.tdata[0] + self.maxt:  # if at end double the time
            self.ax.set_xlim(self.tdata[0], self.tdata[-1] + self.maxt)
            self.ax.figure.canvas.draw()

        self.tdata.append(dataPoint[0])
        self.ydata.append(dataPoint[1])
        self.line.set_data(self.tdata, self.ydata)
        return self.line,


def emitter():
    """
    random emitter to show how routine works. Only called if this file is
    initiated as __main__

    Future Development for GC-Arduino:
        This could be modified to allow for simulation of GC using datafiles
    """

    import random
    for y in range(100):
        x = random.random()
        print(str(x)+" "+str(y))
        yield [float(x), float(y/100)]

if __name__ == '__main__':
    import matplotlib.pyplot as plt
    import matplotlib.animation as animation
    fig, ax = plt.subplots()

    liveGC = LiveGCTrace(ax)

    # pass a generator in "emitter" to produce data for the update func
    ani = animation.FuncAnimation(fig, liveGC.update, emitter, interval=20,
                                  blit=False)

    plt.show()
