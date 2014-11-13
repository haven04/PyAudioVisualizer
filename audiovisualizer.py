import collections
import numpy as np
import time
import audiomanager as am
import mplot as mp

max_deque_size = 44100 * 20 
acc_deque = collections.deque(maxlen=max_deque_size)
analyzer_blocksize = 1024 
audio_mgr = am.AudioManager(analyzer_blocksize)

if __name__ == '__main__':

    try:
        audio_mgr.set_play_wav_file("./samples/pavement22050.wav")
        dtypeinfo = np.iinfo(audio_mgr.dtype)
        channel = audio_mgr.channel

        acc_plot = mp.DequeMPlot(xlim=(0, max_deque_size),
                                 ylim=(dtypeinfo.min, dtypeinfo.max),
                                 redraw_interval = 0.2,
                                 max_size = max_deque_size,
                                 channel=channel,
                                 daemon=True)

        freq_y_lim = (0, np.log10(analyzer_blocksize * dtypeinfo.max))
        # freq_y_lim = (0, analyzer_blocksize * dtypeinfo.max)
        freq_x_step = audio_mgr.samplerate / analyzer_blocksize
        freq_x_lim = (-freq_x_step * analyzer_blocksize / 2,
                      freq_x_step * analyzer_blocksize / 2)
        freq_x_range = np.arange(freq_x_lim[0], freq_x_lim[1], freq_x_step)


        freq_plot = mp.DequeMPlot(xlim=freq_x_lim,
                                  ylim=freq_y_lim,
                                  x_range=freq_x_range,
                                  max_size=analyzer_blocksize,
                                  post_process=lambda d: np.log10(np.absolute(d)),
                                  channel=channel,
                                  daemon=True)

        # spectro_ystep = audio_mgr.samplerate / analyzer_blocksize
        # spectro_ylim = np.arange(-audio_mgr.samplerate/2, audio_mgr.samplerate/2, spectro_ystep)
        data_max = np.log10(dtypeinfo.max * np.sqrt(analyzer_blocksize * 2))

        freq_plot2 = mp.SpectroMPlot(xlim=(0, 100),
                                     # ylim=(0, analyzer_blocksize * dtypeinfo.max),
                                     ylim = (0, data_max),
                                     block_size=analyzer_blocksize,
                                     post_process=lambda d: np.log10(d),
                                     channel=channel,
                                     daemon=True)

        # freq_plot2 = mp.SpectroMPlot(block_size=4096)

        audio_mgr.streamer.register_queue(acc_plot.in_queue)
        audio_mgr.analyzer.register_queue(freq_plot.in_queue)
        audio_mgr.analyzer.register_queue(freq_plot2.in_queue)

        acc_plot.start()
        freq_plot.start()
        freq_plot2.start()
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
