# re-use existing models and population data easily
from agent_torch.examples.models import movement
from agent_torch.populations import astoria
from agent_torch.core.environment import envs

runner = envs.create(model=movement, population=astoria) # create simulation and init runner

sim_steps = runner.config["simulation_metadata"]["num_steps_per_episode"]
num_episodes = runner.config["simulation_metadata"]["num_episodes"]

for epi in range(num_episodes):
  runner.step(sim_steps)

  runner.reset() # re-initializes the sim parameters for new episode

runner.plot()
runner.reset()