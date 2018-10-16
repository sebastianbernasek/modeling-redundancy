from os import getcwd
from argparse import ArgumentParser

from gram.simulation.environment import ConditionSimulation


# ======================== PARSE SCRIPT ARGUMENTS =============================

parser = ArgumentParser(description='Run a perturbation simulation.')

# simulation directory
parser.add_argument('path',
                    nargs='?',
                    required=True)

# save simulation trajectories
parser.add_argument('-S', '--saveall',
                    help='Save simulation trajectories.',
                    type=bool,
                    default=False,
                    required=False)

# number of trajectories
parser.add_argument('-N', '--trajectories',
                    help='Number of stochastic simulations.',
                    type=int,
                    default=1000,
                    required=False)

# number of trajectories
parser.add_argument('-D', '--use_deviations',
                    help='Use deviation variables.',
                    type=bool,
                    default=False,
                    required=False)

args = vars(parser.parse_args())

# ============================= RUN SCRIPT ====================================

# load simulation
simulation = ConditionSimulation.load(args['path'])

# run simulation and comparison
simulation.simulate(N=args['trajectories'])
simulation.compare(deviations=args['use_deviations'], inplace=True)

# save simulation
simulation.save(path, saveall=args['saveall'])