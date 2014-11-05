from PyQt5 import QtWidgets

import matplotlib
matplotlib.use('Qt5Agg')
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

import threading
import multiprocessing
import customthreads
import queue
import collections
import numpy


class MplCanvas(FigureCanvasQTAgg, customthreads.StoppableThread):

    def __init__(self, parent=None, width=5, height=4, channel=1,
                 dpi=100, *args, **kwargs):

        customthreads.StoppableThread.__init__(self, *args, **kwargs)
        self.in_queue = queue.Queue()

        self.fig = Figure(figsize=(width, height), dpi=dpi)
        FigureCanvasQTAgg.__init__(self, self.fig)
        FigureCanvasQTAgg.setSizePolicy(self,
                                        QtWidgets.QSizePolicy.Expanding,
                                        QtWidgets.QSizePolicy.Expanding)
        FigureCanvasQTAgg.updateGeometry(self)

        self.axes_list = []
        self.ylim = None

        self.setParent(parent)
        self.set_channel(channel)

        # self.axes = self.fig.add_subplot(111)
        # self.axes.hold(False)

    def set_channel(self, channel):
        self.channel = channel

        '''clear subplots'''
        if(self.axes_list is not []):
            for ax in self.axes_list:
                self.fig.delaxes(ax)
        self.axes_list = []

        for i in range(1, self.channel+1):
            self.axes_list.append(self.fig.add_subplot(self.channel, 1, i))
        for ax in self.axes_list:
            ax.hold(False)

    def set_lim(self, dtype):
        self.typeinfo = numpy.iinfo(dtype)
        self.ylim = [self.typeinfo.min, self.typeinfo.max]

    def split_channel(self, data):
        return numpy.transpose(numpy.reshape(data, (len(data)/self.channel, self.channel)))

    def run(self):
        '''Thread Loop'''
        while(self.is_stopped() is False):
            try:
                data = self.in_queue.get_nowait()
                split_data = self.split_channel(data)
                for i in range(self.channel):
                    # print(split_data[i], len(split_data[i]))
                    self.axes_list[i].plot(range(len(split_data[i])), split_data[i], 'b')
                    self.axes_list[i].set_ylim(self.ylim)
                self.draw()

            except queue.Empty:
                '''do nothing'''
                pass


class AccumulateMplCanvas(MplCanvas):

    def __init__(self, deque_size=44100, redraw_interval=0.2,
                 *args, **kwargs):
        self.deque_list = []
        self.deque_size = deque_size
        self.x_range = range(self.deque_size)
        self.redraw_interval = redraw_interval
        super(AccumulateMplCanvas, self).__init__(*args, **kwargs)

    def set_channel(self, channel):
        super(AccumulateMplCanvas, self).set_channel(channel)
        # print("CHANNEL!:", channel)
        self.deque_list = []
        for i in range(channel):
            self.deque_list.append(collections.deque(maxlen=self.deque_size))
        for dq in self.deque_list:
            dq.extend([0] * self.deque_size)

    def redraw(self):
        '''redraw graph every 'redraw_interval' seconds'''
        for i in range(self.channel):
            self.axes_list[i].plot(self.x_range, self.deque_list[i], 'b')
            self.axes_list[i].set_ylim(self.ylim)
        self.draw()
        threading.Timer(self.redraw_interval, self.redraw).start()

    def run(self):
        self.redraw()
        while(self.is_stopped() is False):
            try:
                data = self.in_queue.get_nowait()
                split_data = self.split_channel(data)
                for i in range(self.channel):
                    self.deque_list[i].extend(split_data[i])
            except queue.Empty:
                pass


class MplCanvasMP(MplCanvas):
    def __init__(self, *args, **kwargs):
        super(MplCanvasMP, self).__init__(*args, **kwargs)
        self.in_queue = multiprocessing.Queue()


class FreqMplCanvasMP(MplCanvasMP):
    def __init__(self, *args, **kwargs):
        super(FreqMplCanvasMP, self).__init__(*args, **kwargs)

    def run(self):
        '''Process Loop'''
        while(self.is_stopped() is False):
            try:
                data = self.in_queue.get_nowait()
                split_data = self.split_channel(data)
                datalength = len(split_data[0])
                x_range = range(datalength)
                scaled_ylim = numpy.log10(datalength * self.ylim[1])
                for i in range(self.channel):
                    scaled = numpy.log10(split_data[i])
                    self.axes_list[i].plot(x_range, scaled.real, 'b')
                    self.axes_list[i].set_ylim(0, scaled_ylim)
                self.draw()

            except queue.Empty:
                '''do nothing'''
                pass


    # def run(self):
    #     '''Thread Loop'''
    #     while(self.is_stopped() is False):
    #         try:
    #             data = self.in_queue.get_nowait()
    #             for ax in self.axes_list:
    #                 ax.plot(range(len(data)), data, 'b')
    #                 ax.set_ylim(self.ylim)
    #             # self.axes.plot(range(len(data)), data, 'b')
    #             # self.axes.set_ylim(self.ylim)
    #             self.draw()

    #         except queue.Empty:
    #             '''do nothing'''
    #             pass
