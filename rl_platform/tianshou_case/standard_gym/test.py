import pprint

import gym

import matplotlib.pyplot as plt
from gym.wrappers import TimeLimit
from wrapper import WalkerEnvWrapper, create_walker_env, create_car_racing_env
from matplotlib.animation import FuncAnimation

env = create_car_racing_env()
pprint.pprint(env.observation_space)

# Reset the environment
obs = env.reset()

obs_arr = []

done = False
i = 0
while not done:
    #i += 1
    # Select a random action
    action = env.action_space.sample()

    # Take the selected action and get the new state, reward, and done flag
    obs, reward, done, info = env.step(action)
    pprint.pprint(obs.shape)
    i += reward

    # Render the current state of the environment
    obs_arr.append(obs)
print(i)

