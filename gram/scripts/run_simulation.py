from time import time
from gram.simulation.environment import ConditionSimulation
from gram.execution.arguments import RunArguments


# ======================== PARSE SCRIPT ARGUMENTS =============================

args = RunArguments(description='Simulation arguments.')
skwargs = dict(N=args['number_of_trajectories'])
ckwargs = dict(deviations=args['use_deviations'])
path = args['path']

# ============================= RUN SCRIPT ====================================

start_time = time()

# load simulation
simulation = ConditionSimulation.load(path)

# run simulation and comparison
simulation.run(skwargs=skwargs, ckwargs=ckwargs)

# save simulation
simulation.save(path, saveall=args['save_all'])

# print runtime to standard out
runtime = time() - start_time
print('\nSIMULATION COMPLETE.')
print('RUNTIME: {:0.2f}\n\n'.format(runtime))