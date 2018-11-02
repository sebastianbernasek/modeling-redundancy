from os.path import join, abspath, relpath, isdir
from os import mkdir, chmod, pardir
import shutil
from glob import glob
import pickle
import numpy as np
from time import time
from datetime import datetime

from ..simulation.environment import ConditionSimulation


class Batch:
    """
    Class defines a collection of batch job submissions for Quest.

    Attributes:

        path (str) - path to batch directory

        parameters (iterable) - parameter sets

        simulation_paths (dict) - relative paths to simulation directories

        sim_kw (dict) - keyword arguments for simulation

    Properties:

        N (int) - number of samples in parameter space

    """
    def __init__(self, parameters):
        """
        Instantiate batch of jobs.

        Args:

            parameters (iterable) - each entry is a parameter set that defines a simulation. Parameter sets are passed to the build_model method.

        """
        self.simulation_paths = {}
        self.parameters = parameters

    def __getitem__(self, index):
        """ Returns simulation instance. """
        return self.load_simulation(index)

    def __iter__(self):
        """ Iterate over serialized simulations. """
        self.count = 0
        return self

    def __next__(self):
        """ Returns next simulation instance. """
        if self.count < len(self.simulation_paths):
            simulation = self.load_simulation(self.count)
            self.count += 1
            return simulation
        else:
            raise StopIteration

    @property
    def N(self):
        """ Number of samples in parameter space. """
        return len(self.parameters)

    @staticmethod
    def load(path):
        """ Load batch from target <path>. """
        with open(join(path, 'batch.pkl'), 'rb') as file:
            batch = pickle.load(file)
        batch.path = path
        return batch

    @staticmethod
    def build_submission_script(path,
                                num_trajectories,
                                saveall,
                                deviations,
                                allocation='p30653'):
        """
        Writes job submission script.

        Args:

            path (str) - path to simulation top directory

            num_trajectories (int) - number of simulation trajectories

            saveall (bool) - if True, save simulation trajectories

            deviations (bool) - if True, use deviation variables

            allocation (str) - project allocation, e.g. p30653 (comp. bio)

        """

        # define paths
        path = abspath(path)
        job_script_path = join(path, 'scripts', 'submit.sh')

        # copy run script to scripts directory
        run_path = join(abspath(__file__)
        run_path = run_path.rsplit('/', maxsplit=1)[0], 'run_batch.py')
        shutil.copy(run_path, join(path, 'scripts'))

        # declare outer script that reads PATH from file
        job_script = open(job_script_path, 'w')
        job_script.write('#!/bin/bash\n')

        # move to batch directory
        job_script.write('cd {:s} \n\n'.format(path))

        # begin outer script for processing batch
        job_script.write('while IFS=$\'\\t\' read P\n')
        job_script.write('do\n')
        job_script.write('   JOB=`msub - << EOJ\n\n')

        # =========== begin submission script for individual job =============
        job_script.write('#! /bin/bash\n')
        job_script.write('#MSUB -A {:s} \n'.format(allocation))
        job_script.write('#MSUB -q short \n')
        job_script.write('#MSUB -l walltime=04:00:00 \n')
        job_script.write('#MSUB -m abe \n')
        #job_script.write('#MSUB -M sebastian@u.northwestern.edu \n')
        job_script.write('#MSUB -o ${P}/outlog \n')
        job_script.write('#MSUB -e ${P}/errlog \n')
        job_script.write('#MSUB -N $(basename ${P}) \n')
        job_script.write('#MSUB -l nodes=1:ppn=1 \n')
        job_script.write('#MSUB -l mem=1gb \n\n')

        # load python module and metabolism virtual environment
        job_script.write('module load python/anaconda3.6\n')
        job_script.write('source activate ~/pythonenvs/metabolism_env\n\n')

        # move to batch directory
        job_script.write('cd {:s} \n\n'.format(batch_path))

        # run script
        job_script.write('python ./scripts/run_batch.py ${P}')
        args = (num_trajectories, saveall, deviations)
        job_script.write(' -N {:d} -S {:d} -D {:d}\n'.format(*args))
        job_script.write('EOJ\n')
        job_script.write('`\n\n')
        # ============= end submission script for individual job =============

        # print job id
        #job_script.write('echo "JobID = ${JOB} submitted on `date`"\n')
        job_script.write('done < ./batches/index.txt \n')
        job_script.write('echo "All batches submitted as of `date`"\n')
        job_script.write('exit\n')

        # close the file
        job_script.close()

        # change the permissions
        chmod(job_path, 0o755)

    def build_path_files(self, batch_size=25):
        """
        Creates directory and writes simulation paths for each batch.

        Args:

            batch_size (int) - number of simulations per batch

        """

        # get directory for all batches
        batches_dir = join(self.path, 'batches')

        # create index file for batches
        batches_index = open(join(batches_dir, 'index.txt', 'w'))

        # write file containing simulation paths for each batch
        for i, simulation_path in self.simulation_paths.items():

            # determine batch ID
            batch_id = i // batch_size

            # open batch file and append to index
            if i % batch_size == 0:
                batch_dir = join(batches_dir, '{:d}.txt'.format(batch_id))
                batch_file = open(batch_dir, 'w')
                batches_index.write('{:s}\n'.format(batch_dir))

            # write paths to batch file
            batch_file.write('{:s}\n'.format(simulation_path))

            # close batch file
            if i % batch_size == (batch_size - 1):
                batch_file.close()

        batches_index.close()

    def make_directory(self, directory='./'):
        """
        Create directory for batch of jobs.

        Args:

            directory (str) - destination path

        """

        # assign name to batch
        timestamp = datetime.fromtimestamp(time()).strftime('%y%m%d_%H%M%S')
        name = '{:s}_{:s}'.format(self.__class__.__name__, timestamp)

        # create directory (overwrite existing one)
        path = join(directory, name)
        if not isdir(path):
            mkdir(path)
        self.path = path

        # make subdirectories for simulations and scripts
        mkdir(join(path, 'scripts'))
        mkdir(join(path, 'simulations'))
        mkdir(join(path, 'batches'))

    def build(self,
              directory='./',
              batch_size=25,
              num_trajectories=5000,
              saveall=False,
              deviations=False,
              allocation='p30653',
              **sim_kw):
        """
        Build directory tree for a batch of jobs. Instantiates and saves a simulation instance for each parameter set, then generates a single shell script to submit each simulation as a separate job.

        Args:

            directory (str) - destination path

            batch_size (int) - number of simulations per batch

            num_trajectories (int) - number of simulation trajectories

            saveall (bool) - if True, save simulation trajectories

            deviations (bool) - if True, use deviation variables

            allocation (str) - project allocation

            sim_kw (dict) - keyword arguments for ConditionSimulation

        """

        # create batch directory
        self.make_directory(directory)

        # store parameters (e.g. pulse conditions)
        self.sim_kw = sim_kw
        self.batch_size = batch_size

        # build simulations
        for i, parameters in enumerate(self.parameters):
            simulation_path = join(self.path, 'simulations', '{:d}'.format(i))
            self.simulation_paths[i] = relpath(simulation_path, self.path)
            self.build_simulation(parameters, simulation_path, **sim_kw)

        # save serialized batch
        with open(join(self.path, 'batch.pkl'), 'wb') as file:
            pickle.dump(self, file, protocol=-1)

        # build parameter file
        self.build_path_files(batch_size=batch_size)

        # build job submission script
        self.build_submission_script(self.path,
                                     num_trajectories,
                                     saveall,
                                     deviations,
                                     allocation=allocation)

    @classmethod
    def build_simulation(cls, parameters, simulation_path, **kwargs):
        """
        Builds and saves a simulation instance for a set of parameters.

        Args:

            parameters (iterable) - parameter sets

            simulation_path (str) - simulation path

            kwargs: keyword arguments for ConditionSimulation

        """

        # build model
        model = cls.build_model(parameters)

        # instantiate simulation
        simulation = ConditionSimulation(model, **kwargs)

        # create simulation directory
        if not isdir(simulation_path):
            mkdir(simulation_path)

        # save simulation
        simulation.save(simulation_path)

    def load_simulation(self, index):
        """
        Load simulation instance from file.

        Args:

            index (int) - simulation index

        Returns:

            simulation (ConditionSimulation)

        """
        simulation_path = join(self.path, self.simulation_paths[index])
        return ConditionSimulation.load(simulation_path)

    def apply(self, func):
        """
        Applies function to entire batch of simulations.

        Args:

            func (function) - function operating on a simulation instance

        Returns:

            output (dict) - {simulation_id: function output} pairs

        """
        f = lambda path: func(ConditionSimulation.load(path))
        return {i: f(p) for i, p in self.simulation_paths.items()}
