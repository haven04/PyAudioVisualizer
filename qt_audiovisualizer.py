from PyQt5 import QtWidgets
import sys

import numpy
import audiomanager as am
import qt_mplcanvas as mp


class ApplicationWindow (QtWidgets.QMainWindow):
    current_col = 0
    current_row = 0
    canvas_list = []
    analyzer_blocksize = 4096
    max_deque_size = 44100

    def __init__(self, maxcol=3):
        super(ApplicationWindow, self).__init__()
        self.setWindowTitle("Audio visualizer")
        self.audio_mgr = am.AudioManager(self.analyzer_blocksize)
        self.maxcol = maxcol

        self.accumulated_plot = mp.DequeMplCanvas(xlim=(0, self.max_deque_size),
                                                  ylim=None,
                                                  redraw_interval=0.2,
                                                  parent=self,
                                                  daemon=True)

        self.freq_plot = mp.DequeMplCanvasWithMpQueue(xlim=(0, self.analyzer_blocksize), 
                                                      ylim=None, x_range=None,
                                                      max_size=self.analyzer_blocksize,
                                                      post_process=lambda d: numpy.log10(numpy.absolute(d)),
                                                      daemon=True)

        # self.freq_plot = mp.FreqMplCanvasMP(parent=self, daemon=True)

        self.set_ui()

    def btn_play_clicked(self):
        self.audio_mgr.set_play_wav_file(self.le_file_address.text())

        dtypeinfo = numpy.iinfo(self.audio_mgr.dtype)
        self.accumulated_plot.ylim = (dtypeinfo.min, dtypeinfo.max)
        self.accumulated_plot.set_channel(self.audio_mgr.channel)

        freq_y_lim = (0, numpy.log10(self.analyzer_blocksize * dtypeinfo.max))
        freq_x_step = self.audio_mgr.samplerate / self.analyzer_blocksize
        freq_x_lim = (-freq_x_step * self.analyzer_blocksize / 2,
                      freq_x_step * self.analyzer_blocksize / 2)
        freq_x_range = numpy.arange(freq_x_lim[0], freq_x_lim[1], freq_x_step)

        self.freq_plot.xlim = freq_x_lim
        self.freq_plot.ylim = freq_y_lim
        self.freq_plot.x_range = freq_x_range
        self.freq_plot.set_channel(self.audio_mgr.channel)

        self.audio_mgr.streamer.register_queue(self.accumulated_plot.in_queue)
        self.audio_mgr.analyzer.register_queue(self.freq_plot.in_queue)

        self.audio_mgr.start()

        self.btn_stop.setEnabled(True)
        self.btn_play.setEnabled(False)
        self.btn_record.setEnabled(False)

    def btn_record_clicked(self):
        rec_channel = 1
        rec_dtypeinfo = numpy.iinfo(numpy.uint8)
        self.audio_mgr.set_record(samplerate=11025, channel=rec_channel,
                                  dtype=rec_dtypeinfo,
                                  filename=self.le_file_address.text())

        self.audio_mgr.streamer.register_queue(self.accumulated_plot.in_queue)
        self.accumulated_plot.set_channel(self.audio_mgr.channel)
        self.accumulated_plot.ylim = (rec_dtypeinfo.min, rec_dtypeinfo.max)

        # self.audio_mgr.analyzer.register_queue(self.freq_plot.in_queue)
        # self.freq_plot.set_lim(self.audio_mgr.dtype)
        # self.freq_plot.set_channel(self.audio_mgr.channel)

        self.audio_mgr.start()

        self.btn_stop.setEnabled(True)
        self.btn_play.setEnabled(False)
        self.btn_record.setEnabled(False)

    def btn_stop_clicked(self):
        self.audio_mgr.stop()

        self.btn_stop.setEnabled(False)
        self.btn_play.setEnabled(True)
        self.btn_record.setEnabled(True)

    def set_ui(self):
        self.main_widget = QtWidgets.QWidget(self)
        self.setCentralWidget(self.main_widget)

        self.main_layout = QtWidgets.QHBoxLayout(self.main_widget)
        self.btn_layout = QtWidgets.QVBoxLayout()
        self.grid_layout = QtWidgets.QGridLayout()

        # self.add_mplcanvas(mplcanvas.MplCanvas(parent=self, daemon=True))
        self.add_mplcanvas(self.accumulated_plot)
        self.add_mplcanvas(self.freq_plot)

        self.le_file_address = QtWidgets.QLineEdit(self)
        self.btn_play = QtWidgets.QPushButton('Play File', self)
        self.btn_stop = QtWidgets.QPushButton('Stop', self)
        self.btn_record = QtWidgets.QPushButton('Record', self)

        self.btn_layout.addWidget(self.le_file_address)
        self.btn_layout.addWidget(self.btn_play)
        self.btn_layout.addWidget(self.btn_record)
        self.btn_layout.addWidget(self.btn_stop)
        self.btn_layout.addStretch()

        self.main_layout.addLayout(self.grid_layout)
        self.main_layout.addLayout(self.btn_layout)

        self.btn_play.clicked.connect(self.btn_play_clicked)
        self.btn_stop.clicked.connect(self.btn_stop_clicked)
        self.btn_record.clicked.connect(self.btn_record_clicked)
        self.btn_stop.setEnabled(False)

    def add_mplcanvas(self, widget):
        self.grid_layout.addWidget(widget, self.current_row, self.current_col)
        self.canvas_list.append(widget)
        widget.start()

        self.current_col += 1
        if(self.current_col is self.maxcol):
            self.current_row += 1
            self.current_col = 0


if __name__ == '__main__':
    try:
        qApp = QtWidgets.QApplication(sys.argv)
        aw = ApplicationWindow(maxcol=3)
        aw.show()

        sys.exit(qApp.exec_())

    except KeyboardInterrupt:
        pass

    finally:
        while(aw.audio_mgr.is_running()):
            aw.audio_mgr.stop()
        for c in aw.canvas_list:
            c.immediate_join()
        print("bye!")
