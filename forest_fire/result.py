import os
import h5py
import numpy as np

import imageio
import matplotlib.pyplot as plt
import multiprocessing

from datetime import datetime
from .log import logger

from .state import *


def read_result_from_h5f(filename):
    logger.info('read result from {}'.format(filename))
    with h5py.File(filename, 'r') as h5f:
        history = h5f['history'][()]
        N = h5f['N'][()]
        Nrounds = h5f['Nrounds'][()]
    return Result(N, Nrounds, history)


def plot_frames(frames_dir, N, states, nums):
    '''
    plot and save l figures corresponding to l states
    frames_dir: str, path to the directory to save the figures
    N: int, size of forest
    states: array-like, lxNxN array, l states to be plotted
    nums: array-like, length l, serial numbers of states
    '''
    fig = plt.figure(figsize=(10, 10))
    ax = fig.add_subplot(111)
    ax.set_xlim((0, 1))
    ax.set_ylim((0, 1))
    ax.set_xticks([])
    ax.set_yticks([])

    for i in range(N):
        ax.axhline(i/N, c='black')
        ax.axvline(i/N, c='black')
    text = ax.text(0.95, 1.03, '', fontsize=20)

    colormap = {EMPTY: 'white', TREE: 'green', BURNING: 'red'}
    width = 1/N
    height = 1/N
    for state, n in zip(states, nums):
        for i in range(N):
            for j in range(N):
                x = [width*j, width*(j+1)]
                y1 = [(N-i)*height]*2
                y2 = [(N-1-i)*height]*2
                ax.fill_between(x, y1, y2, color=colormap[state[i, j]])
        text.set_text('N={:d}'.format(n))
        fig.savefig(os.path.join(frames_dir, '{:d}.png'.format(n)))
    plt.close(fig)


class Result:
    def __init__(self, N, Nrounds, history):
        self.N = N
        self.Nrounds = Nrounds
        self.history = history

    def save_to_h5f(self, filename):
        logger.info('save result file to {}'.format(filename))
        with h5py.File(filename, 'w') as h5f:
            h5f.create_dataset('history', data=self.history)
            h5f.create_dataset('N', data=self.N)
            h5f.create_dataset('Nrounds', data=self.Nrounds)

    def generate_gif(self, outdir, njobs=1,
                     gif_duration=0.1, gif_name='simulation_result.gif', plot_i=None):
        '''
        visualize simulation result as a GIF file
        outdir: str, directory to save the GIF file
        njobs: int, number of processes to be used while plotting states
        gif_duration: float, duration of each frame (in second)
        gif_name: str, name of GIF file
        plot_i: None or iterable, indexes of states that are to be plotted in self.history,
            default to be None, meaning all of the states should be plotted if plot_i is not been specified
        '''
        frames_dir = os.path.join(outdir, 'frames')
        if not os.path.exists(frames_dir):
            os.mkdir(frames_dir)

        logger.info(
            'begin plotting frames, using {:d} processes'.format(njobs))
        processes = []
        if plot_i is None:
            plot_i = np.arange(self.Nrounds)
        else:
            plot_i = np.array(plot_i)
        for i in range(njobs):
            nums_i = range((i*len(plot_i))//njobs, ((i+1)*len(plot_i))//njobs)
            nums = plot_i[nums_i]
            p = multiprocessing.Process(
                target=plot_frames, args=(frames_dir, self.N, self.history[nums], nums))
            processes.append(p)
            p.start()
        for p in processes:
            p.join()

        logger.info('completed plotting frames, generating gif')
        images = [imageio.imread(image) for image in [os.path.join(
            frames_dir, '{:d}.png'.format(i)) for i in range(self.Nrounds)]]
        gif_path = os.path.join(outdir, gif_name)
        imageio.mimsave(gif_path, images, duration=gif_duration)
        logger.info('save gif file to path: {}'.format(gif_path))
