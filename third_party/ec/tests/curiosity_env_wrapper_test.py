# coding=utf-8
# Copyright 2019 Google LLC.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Test of curiosity_env_wrapper.py."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import unittest
from collections import OrderedDict

from gym.vector.utils import spaces

from rl_platform.tianshou_case.net.r_network import RNetwork
from third_party.ec import episodic_memory, single_curiosity_env_wrapper as curiosity_env_wrapper
from third_party.ec import r_network_training

import gym
import numpy as np

from third_party.ec.vec_env import VecEnv
from third_party.ec.single_curiosity_env_wrapper import CuriosityEnvWrapper


class DummyVecEnv(VecEnv):
    def __init__(self, env_fns):
        self.envs = [fn() for fn in env_fns]
        env = self.envs[0]
        VecEnv.__init__(self, len(env_fns), env.observation_space, env.action_space)
        shapes, dtypes = {}, {}
        self.keys = []
        obs_space = env.observation_space

        if isinstance(obs_space, spaces.Dict):
            assert isinstance(obs_space.spaces, OrderedDict)
            subspaces = obs_space.spaces
        else:
            subspaces = {None: obs_space}

        for key, box in subspaces.items():
            shapes[key] = box.shape
            dtypes[key] = box.dtype
            self.keys.append(key)

        self.buf_obs = { k: np.zeros((self.num_envs,) + tuple(shapes[k]), dtype=dtypes[k]) for k in self.keys }
        self.buf_dones = np.zeros((self.num_envs,), dtype=np.bool)
        self.buf_rews  = np.zeros((self.num_envs,), dtype=np.float32)
        self.buf_infos = [{} for _ in range(self.num_envs)]
        self.actions = None

    def step_async(self, actions):
        self.actions = actions

    def step_wait(self):
        for e in range(self.num_envs):
            obs, self.buf_rews[e], self.buf_dones[e], self.buf_infos[e] = self.envs[e].step(self.actions[e])
            if self.buf_dones[e]:
                obs = self.envs[e].reset()
            self._save_obs(e, obs)
        return (self._obs_from_buf(), np.copy(self.buf_rews), np.copy(self.buf_dones),
                self.buf_infos.copy())

    def reset(self):
        for e in range(self.num_envs):
            obs = self.envs[e].reset()
            self._save_obs(e, obs)
        return self._obs_from_buf()

    def close(self):
        return

    def render(self, mode='human'):
        return [e.render(mode=mode) for e in self.envs]

    def _save_obs(self, e, obs):
        for k in self.keys:
            if k is None:
                self.buf_obs[k][e] = obs
            else:
                self.buf_obs[k][e] = obs[k]

    def _obs_from_buf(self):
        if self.keys==[None]:
            return self.buf_obs[None]
        else:
            return self.buf_obs



class DummyImageEnv(gym.Env):

    def __init__(self):
        self._num_actions = 4
        self._image_shape = (28, 28, 3)
        self._done_prob = 0.01

        self.action_space = gym.spaces.Discrete(self._num_actions)
        self.observation_space = gym.spaces.Box(
            0, 255, self._image_shape, dtype=np.float32)

    def seed(self, seed=None):
        pass

    def step(self, action):
        observation = np.random.randint(0, 255, size=self._image_shape, dtype=np.uint8)
        reward = 0.0
        done = (np.random.rand() < self._done_prob)
        info = {}
        return observation, reward, done, info

    def reset(self):
        return np.random.randint(0, 255, size=self._image_shape, dtype=np.uint8)

    def render(self, mode='human'):
        raise NotImplementedError('Rendering not implemented')


# TODO(damienv): To be removed once the code in ec
# is compatible with python 2.
class HackDummyVecEnv(DummyVecEnv):

    def step_wait(self):
        for e in range(self.num_envs):
            action = self.actions[e]
            if isinstance(self.envs[e].action_space, gym.spaces.Discrete):
                action = int(action)

            obs, self.buf_rews[e], self.buf_dones[e], self.buf_infos[e] = (
                self.envs[e].step(action))
            if self.buf_dones[e]:
                obs = self.envs[e].reset()
            self._save_obs(e, obs)
        return (np.copy(self._obs_from_buf()),
                np.copy(self.buf_rews),
                np.copy(self.buf_dones),
                list(self.buf_infos))


def embedding_similarity(x1, x2):
    assert x1.shape[0] == x2.shape[0]
    epsilon = 1e-6

    # Inner product between the embeddings in x1
    # and the embeddings in x2.
    s = np.sum(x1 * x2, axis=-1)

    s /= np.linalg.norm(x1, axis=-1) * np.linalg.norm(x2, axis=-1) + epsilon
    return 0.5 * (s + 1.0)


def linear_embedding(m, x):
    # Flatten all but the batch dimension if needed.
    if len(x.shape) > 2:
        x = np.reshape(x, [x.shape[0], -1])
    return np.matmul(x, m)


class EpisodicEnvWrapperTest(unittest.TestCase):

    def EnvFactory(self):
        return DummyImageEnv()

    def testResizeObservation(self):
        img_grayscale = np.random.randint(low=0, high=256, size=[64, 48, 1])
        img_grayscale = img_grayscale.astype(np.uint8)
        resized_img = curiosity_env_wrapper.resize_observation(img_grayscale,
                                                               [16, 12, 1])
        self.assertEqual([16, 12, 1], list(resized_img.shape))

        img_color = np.random.randint(low=0, high=256, size=[64, 48, 3])
        img_color = img_color.astype(np.uint8)
        resized_img = curiosity_env_wrapper.resize_observation(img_color,
                                                               [16, 12, 1])
        self.assertEqual([16, 12, 1], list(resized_img.shape))
        resized_img = curiosity_env_wrapper.resize_observation(img_color,
                                                               [16, 12, 3])
        self.assertEqual([16, 12, 3], list(resized_img.shape))

    def testEpisodicEnvWrapperSimple(self):
        vec_env = self.EnvFactory()

        embedding_size = 16
        vec_episodic_memory = episodic_memory.EpisodicMemory(
            capacity=1000,
            observation_shape=[embedding_size],
            observation_compare_fn=embedding_similarity)

        mat = np.random.normal(size=[28 * 28 * 3, embedding_size])
        observation_embedding = lambda x, m=mat: linear_embedding(m, x)

        target_image_shape = [14, 14, 1]

        set_device = 'cuda'
        r_model = RNetwork([28, 28, 3], set_device)
        r_trainer = r_network_training.RNetworkTrainer(
            r_model,
            observation_history_size=10000,
            training_interval=500,
            num_train_epochs=1,
            checkpoint_dir="../",
            device=set_device)
        env_wrapper = CuriosityEnvWrapper(
            vec_env, vec_episodic_memory,
            observation_embedding,
            target_image_shape,
            r_net_trainer=r_trainer,
            scale_surrogate_reward=1.0,
            exploration_reward_min_step=300)

        observations = env_wrapper.reset()
        self.assertEqual(target_image_shape, list(observations.shape))

        dummy_actions = [1]
        for _ in range(2000):
            previous_mem_length = len(vec_episodic_memory)
            observation, unused_reward, done, unused_info = (env_wrapper.step(dummy_actions))
            current_mem_length = len(vec_episodic_memory)
            print(unused_reward)
            #pprint.pprint(unused_info)

            self.assertEqual(target_image_shape, list(observation.shape))
            if done:
                self.assertEqual(1, current_mem_length)
            else:
                self.assertGreaterEqual(current_mem_length, previous_mem_length)


