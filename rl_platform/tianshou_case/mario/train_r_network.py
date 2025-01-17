import os.path
import pprint
from datetime import datetime

from tianshou.data import VectorReplayBuffer
from tianshou.env import SubprocVectorEnv
from vizdoom import gym_wrapper  # noqa
from tianshou.data.collector import Collector

from rl_platform.tianshou_case.standard_gym.wrapper import RewardType
from third_party.ec import train_r_network_with_collector
from rl_platform.tianshou_case.utils.dummy_policy import DummyPolicy
from wrapper import create_mario_env

env_name = "Mario_v3"
set_device = "cuda"
task = "{}".format(env_name)
file_name = os.path.abspath(os.path.join("r_network", task + "_PPO_" + datetime.now().strftime("%Y_%m_%d_%H_%M_%S")))
total_feed_step = 650000
observation_history_size = 20000
num_train_epochs = 50
batch_size = 128
training_interval = 20000
target_image_shape = [42, 42, 4]
step_interval = 500
train_env_num = 10


def make_env():
    env = create_mario_env(reward_type=RewardType.RAW_REWARD)
    # env = create_walker_env()
    return env


debug = False

if debug:
    batch_size = 16
    train_env_num = 2
    training_interval = 100


def test_collector():
    policy = DummyPolicy(make_env().action_space)
    train_envs = SubprocVectorEnv([make_env for _ in range(1)])
    buffer = VectorReplayBuffer(100, len(train_envs))
    collector = Collector(policy, train_envs, buffer=buffer)
    collector.collect(n_episode=6, render=1 / 36)
    pprint.pprint(buffer.sample(2))


from easydict import EasyDict

if __name__ == '__main__':
    # test_collector()
    load_file = r"D:\Projects\python\PedestrainSimlationModule\rl_platform\tianshou_case\mario\r_network\Mario_v3_PPO_2023_03_19_23_44_44\r_network_weight_200.pt"
    dic = EasyDict(globals())
    train_r_network_with_collector(make_env, file_name, dic, load_file=load_file)

    # path = r"/rl_platform/tianshou_case/vizdoom/checkpoints/VizdoomMyWayHome-v0_PPO_2023_03_11_01_35_53\r_network_weight_500.pt"
    # train()
    # train(r"D:\Projects\python\PedestrainSimlationModule\rl_platform\tianshou_case\standard_gym\r_network\CarRacing_v3_PPO_2023_03_16_00_07_57\r_network_weight_150.pt")
