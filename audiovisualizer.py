from PyQt5 import QtWidgets
import sys

import numpy

import audioanalyzer
import audiostreamer as ast
import mplcanvas


class AudioManager:
    def __init__(self):
        self.audiobuffer = None
        self.streamer = None
        self.analyzer = None

    def set_play_wav_file(self, filename):

        self.audiobuffer = ast.WavBuffer(filename, daemon=True)

        self.samplerate = self.audiobuffer.samplerate
        self.channel = self.audiobuffer.channel
        self.dtype = ast.dic_datawidth_to_numpy_dtype[self.audiobuffer.width]

        self.streamer = ast.AudioStreamer(samplerate=self.samplerate,
                                          channel=self.channel,
                                          datatype=self.dtype,
                                          input_flag=False,
                                          daemon=True)

        self.analyzer = audioanalyzer.AudioAnalyzer(daemon=True)

        self.audiobuffer.register_queue(self.streamer.in_queue)
        self.streamer.register_queue(self.analyzer.in_queue)

    def set_play_audiodata(self, datablock, samplerate, channel, dtype):

        self.dtype = dtype
        self.samplerate = samplerate
        self.channel = channel
        self.audiobuffer = ast.AudioBuffer(datablock, daemon=True)
        self.streamer = ast.AudioStreamer(samplerate=self.samplerate,
                                          channel=self.channel,
                                          datatype=self.dtype,
                                          input_flag=False,
                                          daemon=True)

        self.analyzer = audioanalyzer.AudioAnalyzer(daemon=True)

        self.audiobuffer.register_queue(self.streamer.in_queue)
        self.streamer.register_queue(self.analyzer.in_queue)

    def set_record(self, samplerate, channel, dtype, filename):

        self.dtype = dtype
        self.audiobuffer = None
        self.samplerate = samplerate
        self.channel = channel
        self.streamer = ast.AudioStreamer(samplerate=self.samplerate,
                                          channel=self.channel,
                                          datatype=self.dtype,
                                          input_flag=True,
                                          filename=filename,
                                          daemon=True)

        self.analyzer = audioanalyzer.AudioAnalyzer(daemon=True)
        self.streamer.register_queue(self.analyzer.in_queue)

    def start(self):
        if(self.streamer is not None):
            self.streamer.start()
        if(self.audiobuffer is not None):
            self.audiobuffer.start()
        if(self.analyzer is not None):
            self.analyzer.start()

    def stop(self):
        if((self.audiobuffer is not None) and (self.audiobuffer.is_running)):
            self.audiobuffer.immediate_join()
        if((self.streamer is not None) and (self.streamer.is_running)):
            self.streamer.immediate_join()
        if((self.analyzer is not None) and (self.streamer.is_running)):
            self.analyzer.immediate_join()

    def is_running(self):
        result_flag = False
        if(self.audiobuffer is not None):
            result_flag = self.audiobuffer.is_running()
        if(self.streamer is not None):
            result_flag = result_flag or self.streamer.is_running()
        if(self.analyzer is not None):
            result_flag = result_flag or self.analyzer.is_running()

        return result_flag


class ApplicationWindow (QtWidgets.QMainWindow):
    current_col = 0
    current_row = 0
    canvas_list = []

    def __init__(self, maxcol=3):
        super(ApplicationWindow, self).__init__()
        self.setWindowTitle("Audio visualizer")
        self.audio_mgr = AudioManager()
        self.maxcol = maxcol
        self.accumulated_plot = mplcanvas.AccumulateMplCanvas(parent=self,
                                                              daemon=True)
        self.freq_plot = mplcanvas.FreqMplCanvasMP(parent=self, daemon=True)

        self.set_ui()

    def btn_play_clicked(self):
        self.audio_mgr.set_play_wav_file(self.le_file_address.text())

        self.audio_mgr.streamer.register_queue(self.accumulated_plot.in_queue)
        self.audio_mgr.analyzer.register_queue(self.freq_plot.in_queue)
        self.accumulated_plot.set_lim(self.audio_mgr.dtype)
        self.freq_plot.set_lim(self.audio_mgr.dtype)
        self.accumulated_plot.set_channel(self.audio_mgr.channel)
        self.freq_plot.set_channel(self.audio_mgr.channel)

        self.audio_mgr.start()

        self.btn_stop.setEnabled(True)
        self.btn_play.setEnabled(False)
        self.btn_record.setEnabled(False)

    def btn_record_clicked(self):
        self.audio_mgr.set_record(samplerate=11025, channel=1,
                                  dtype=numpy.uint8,
                                  filename=self.le_file_address.text())

        self.audio_mgr.streamer.register_queue(self.accumulated_plot.in_queue)
        self.audio_mgr.analyzer.register_queue(self.freq_plot.in_queue)
        self.accumulated_plot.set_lim(self.audio_mgr.dtype)
        self.freq_plot.set_lim(self.audio_mgr.dtype)
        self.accumulated_plot.set_channel(self.audio_mgr.channel)
        self.freq_plot.set_channel(self.audio_mgr.channel)

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
