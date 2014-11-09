import collections
import numpy
import time
import audiomanager as am
import mplot as mp

max_deque_size = 44100
acc_deque = collections.deque(maxlen=max_deque_size)
analyzer_blocksize = 4096
audio_mgr = am.AudioManager(analyzer_blocksize)

if __name__ == '__main__':

    try:
        audio_mgr.set_play_wav_file("./test_stereo.wav")
        dtypeinfo = numpy.iinfo(audio_mgr.dtype)
        channel = audio_mgr.channel

        acc_plot = mp.DequeMPlot(xlim=(0, max_deque_size),
                                 ylim=(dtypeinfo.min, dtypeinfo.max),
                                 redraw_interval = 0.2,
                                 channel=channel,
                                 daemon=True)

        freq_y_lim = (0, numpy.log10(analyzer_blocksize * dtypeinfo.max))
        freq_x_step = audio_mgr.samplerate / analyzer_blocksize
        freq_x_lim = (-freq_x_step * analyzer_blocksize / 2,
                      freq_x_step * analyzer_blocksize / 2)
        freq_x_range = numpy.arange(freq_x_lim[0], freq_x_lim[1], freq_x_step)


        freq_plot = mp.DequeMPlot(xlim=freq_x_lim,
                                  ylim=freq_y_lim,
                                  x_range=freq_x_range,
                                  max_size=analyzer_blocksize,
                                  post_process=lambda d: numpy.log10(numpy.absolute(d)),
                                  channel=channel,
                                  daemon=True)

        audio_mgr.streamer.register_queue(acc_plot.in_queue)
        audio_mgr.analyzer.register_queue(freq_plot.in_queue)

        acc_plot.start()
        freq_plot.start()
        audio_mgr.start()

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        pass

    finally:
        audio_mgr.stop()
        acc_plot.immediate_join()
        freq_plot.immediate_join()
        print("bye!")
