import os
import numpy as np
from datetime import datetime
from .state import *
from .result import Result
from .log import logger


class Forest:
    def __init__(self, N, p, f, coverage=0.9):
        '''
        2D cellular automation implemtation of forest-fire model.
        N: int, scale of the forest
        p: float, probability of empty block turning into tree
        f: float, probability of tree turning into burning tree (lightning)
        coverage: float, probability of initializing a block to be a tree
        '''
        self.N = N
        self.p = p
        self.f = f
        self._initialize_state(coverage)

    def _initialize_state(self, coverage):
        self.state = np.random.choice([TREE, EMPTY], size=(
            self.N, self.N), p=[coverage, 1-coverage])
        self.history = [self.state]

    def _save_evolution(self):
        self.history = np.vstack((self.history, [self.state]))

    def _mark_around_burning(self):
        '''
        returns a NxN bool array 'mark', mark[i, j] is True if any block around (i, j) is burning
        if (i, j) is burning, mark[i, j] is also True, which is not always right, but won't affect result of simulation. 
        '''
        mark = np.zeros((self.N, self.N)).astype(bool)

        # blocks on corner
        if self.state[0, 0] == BURNING:
            mark[0:2, 0:2] = True
        if self.state[0, -1] == BURNING:
            mark[0:2, -2:self.N] = True
        if self.state[-1, 0] == BURNING:
            mark[-2:self.N, 0:2] = True
        if self.state[-1, -1] == BURNING:
            mark[-2:self.N, -2:self.N] = True

        # blocks on side
        for i in range(1, self.N-1):
            if self.state[0, i] == BURNING:
                mark[0:2, i-1:i+2] = True
            if self.state[i, 0] == BURNING:
                mark[i-1:i+2, 0:2] = True
            if self.state[-1, i] == BURNING:
                mark[-2:self.N, i-1:i+2] = True
            if self.state[i, -1] == BURNING:
                mark[i-1:i+2, -2:self.N] = True

        for i in range(1, self.N-1):
            for j in range(1, self.N-1):
                if self.state[i, j] == BURNING:
                    mark[i-1:i+2, j-1:j+2] = True

        return mark

    def evolve(self):
        newstate = np.zeros((self.N, self.N))
        mark = self._mark_around_burning()
        for i in range(self.N):
            for j in range(self.N):
                if self.state[i, j] == BURNING:
                    newstate[i, j] = EMPTY
                elif self.state[i, j] == EMPTY:
                    newstate[i, j] = TREE if np.random.random() < self.p else EMPTY
                elif mark[i, j]:
                    newstate[i, j] = BURNING
                else:
                    newstate[i, j] = BURNING if np.random.random() < self.f else TREE
        self.state = newstate
        self._save_evolution()
    
    def run_simulation(self, Nrounds, outdir, save_to_file='simulation_result.h5'):
        start_time = datetime.now()
        logger.info('start simulation')

        for _ in range(Nrounds):
            self.evolve()

        end_time = datetime.now()
        tmp = datetime(2000, 1, 1, 0, 0, 0)+(end_time-start_time)
        logger.info('end simulation')
        logger.info('{:d} turns of simulation done in {}'.format(
            Nrounds, tmp.strftime('%Hh%Mm%Ss')))

        result = Result(self.N, Nrounds, self.history)
        if not os.path.exists(outdir):
            os.mkdir(outdir)
        result.save_to_h5f(os.path.join(outdir, save_to_file))
        return result
