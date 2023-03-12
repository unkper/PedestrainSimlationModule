import torch

from rl_platform.tianshou_case.third_party import episodic_memory
from rl_platform.tianshou_case.third_party import oracle

import gym
import numpy as np
import cv2

from rl_platform.tianshou_case.third_party.episodic_memory import EpisodicMemory
from rl_platform.tianshou_case.third_party.r_network_training import RNetworkTrainer


def resize_observation(frame, image_shape, reward=None):
    """Resize an observation according to the target image shape."""
    # Shapes already match, nothing to be done
    height, width, target_depth = image_shape
    if frame.shape == (height, width, target_depth):
        return frame
    if frame.shape[-1] != 3 and frame.shape[-1] != 1:
        raise ValueError(
            'Expecting color or grayscale images, got shape {}: {}'.format(
                frame.shape, frame))

    if frame.shape[-1] == 3 and target_depth == 1:
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY)

    frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_AREA)

    # OpenCV operations removes the last axis for grayscale images.
    # Restore the last axis.
    if len(frame.shape) != 3:
        frame = frame[:, :, np.newaxis]

    if reward is None:
        return frame

    return np.concatenate([frame, np.full([height, width, 1], reward)], axis=-1)


class MovingAverage(object):
    """Computes the moving average of a variable."""

    def __init__(self, capacity):
        self._capacity = capacity
        self._history = np.array([0.0] * capacity)
        self._size = 0

    def add(self, value):
        index = self._size % self._capacity
        self._history[index] = value
        self._size += 1

    def mean(self):
        if not self._size:
            return None
        if self._size < self._capacity:
            return np.mean(self._history[0:self._size])
        return np.mean(self._history)


def to_numpy_and_squeeze_batch(observation):
    if isinstance(observation, torch.Tensor):
        observation = observation.detach().cpu()
        observation = observation.numpy()
    return np.squeeze(observation, 0) if observation.shape[0] == 1 else observation


class CuriosityEnvWrapper:
    """Environment wrapper that adds additional curiosity reward."""

    def __init__(self,
                 vec_env,
                 vec_episodic_memory: EpisodicMemory,
                 observation_embedding_fn,
                 target_image_shape,
                 exploration_reward='episodic_curiosity',
                 scale_task_reward: float = 1.0,
                 scale_surrogate_reward: float = 0.0,
                 append_ec_reward_as_channel: bool = False,
                 bonus_reward_additive_term=0,
                 exploration_reward_min_step=0,
                 similarity_threshold: float = 0.5,
                 similarity_aggregation='percentile',
                 r_net_trainer: RNetworkTrainer = None,
                 test_mode: bool=False):
        # 该类中存储的是原有的图像经过缩放后的处理图像，而计算好奇心的时候才通过observation_embedding_fn
        # 进行相应的转换
        if self._should_postprocess_observation(vec_env.observation_space.shape):
            observation_space_shape = target_image_shape[:]
            if append_ec_reward_as_channel:
                observation_space_shape[-1] += 1
            observation_space = gym.spaces.Box(
                low=0, high=255, shape=observation_space_shape, dtype=np.float)
        else:
            observation_space = vec_env.observation_space
            assert not append_ec_reward_as_channel, (
                'append_ec_reward_as_channel not compatible with non-image-like obs.')
        self.venv = vec_env

        self._bonus_reward_additive_term = bonus_reward_additive_term
        self._vec_episodic_memory = vec_episodic_memory
        self._observation_embedding_fn = observation_embedding_fn
        self._target_image_shape = target_image_shape
        self._append_ec_reward_as_channel = append_ec_reward_as_channel

        self._exploration_reward = exploration_reward
        self._scale_task_reward = scale_task_reward
        self._scale_surrogate_reward = scale_surrogate_reward
        self._exploration_reward_min_step = exploration_reward_min_step

        # Oracle reward.
        self._oracle = oracle.OracleExplorationReward()

        # Cumulative task reward over an episode.
        self._episode_task_reward = 0.0
        self._episode_bonus_reward = 0.0

        # Stats on the task and exploration reward.
        self._stats_task_reward = MovingAverage(capacity=100)
        self._stats_bonus_reward = MovingAverage(capacity=100)

        # Total number of steps so far per environment.
        self._step_count = 0

        self._similarity_threshold = similarity_threshold
        self._similarity_aggregation = similarity_aggregation

        # for online training
        self._r_net_trainer: RNetworkTrainer = r_net_trainer

        # Observers are notified each time a new time step is generated by the
        # environment.
        # Observers implement a function "on_new_observation".
        self._observers = []
        self._test_mode = test_mode

    def _should_postprocess_observation(self, obs_shape):
        # Only post-process observations that look like an image.
        return len(obs_shape) >= 3

    def add_observer(self, observer):
        self._observers.append(observer)

    def _postprocess_observation(self, observation, reward=None):
        #print(observation.shape)
        if not self._should_postprocess_observation(observation.shape):
            return observation

        if self._append_ec_reward_as_channel:
            if reward is not None:
                return resize_observation(observation, self._target_image_shape, reward)
            else:
                # When environment is reset there are no rewards, so we explicitly pass
                # 0 in this case.
                return resize_observation(observation, self._target_image_shape, 0)
        else:
            return resize_observation(observation, self._target_image_shape, None)

    def _compute_curiosity_reward(self, observation, info, done):
        # Computes the surrogate reward.
        # This extra reward is set to 0 when the episode is finished.
        if info.get('frame') is not None:
            frames = np.array(info['frame'])
        else:
            frames = observation
        embedded_observation = self._observation_embedding_fn(frames)
        similarity_to_memory = episodic_memory.similarity_to_memory(embedded_observation,
                                                                    self._vec_episodic_memory,
                                                                    similarity_aggregation=self._similarity_aggregation)

        # Updates the episodic memory of environment.
        # If we've reached the end of the episode, resets the memory
        # and always adds the first state of the new episode to the memory.
        if done:
            self._vec_episodic_memory.reset()
            self._vec_episodic_memory.add(embedded_observation, info)

        # Only add the new state to the episodic memory if it is dissimilar
        # enough.
        if similarity_to_memory < self._similarity_threshold:
            self._vec_episodic_memory.add(embedded_observation, info)
        # Augment the reward with the exploration reward.
        # bonus的奖励定义为0.5 - 相似程度，代表的是越相似的奖励值就越小，可能为负值
        bonus_rewards = 0.0 if done else 0.5 - similarity_to_memory + self._bonus_reward_additive_term
        bonus_rewards = float(bonus_rewards)
        return bonus_rewards

    def _compute_oracle_reward(self, info, done):
        bonus_rewards = self._oracle.update_position(info['position'])
        bonus_rewards = np.array(bonus_rewards)

        if done:
            self._oracle.reset()

        return bonus_rewards

    def step(self, action):
        """Overrides VecEnvWrapper.step_wait."""
        # observation, reward, done, truncated, info = self.venv.step(action)
        # observation = observation['screen']

        observation, reward, done, info = self.venv.step(action)
        # observation = np.squeeze(observation)
        # observation = np.expand_dims(observation, 0)  # 为了给单个环境添加一个batch_size维度
        # reward = np.expand_dims(reward, 0)
        # done = np.expand_dims(done, 0)

        for observer in self._observers:
            observer.on_new_observation(observation, reward, done, info)
        if self._r_net_trainer is not None and not self._test_mode:
            self._r_net_trainer.on_new_observation(observation, reward, done, info)

        self._step_count += 1

        # if (self._step_count % 1000) == 0:
        #     print('step={} task_reward={} bonus_reward={} scale_bonus={}'.format(
        #         self._step_count,
        #         self._stats_task_reward.mean(),
        #         self._stats_bonus_reward.mean(),
        #         self._scale_surrogate_reward))

        info['task_reward'] = reward
        info['task_observation'] = observation

        # Exploration bonus.
        reward_for_input = None
        if self._test_mode:
            bonus_reward = 0.0
            reward_for_input = 0.0
        else:
            if self._exploration_reward == 'episodic_curiosity':
                bonus_reward = self._compute_curiosity_reward(observation, info, done)
                reward_for_input = bonus_reward
            elif self._exploration_reward == 'oracle':
                bonus_reward = self._compute_oracle_reward(info, done)
                if self._append_ec_reward_as_channel:
                    reward_for_input = self._compute_curiosity_reward(
                        observation, info, done)
            elif self._exploration_reward == 'none':
                bonus_reward = 0.0
                reward_for_input = 0.0
            else:
                raise ValueError('Unknown exploration reward: {}'.format(
                    self._exploration_reward))

        # Combined rewards.
        scale_surrogate_reward = self._scale_surrogate_reward
        if self._step_count < self._exploration_reward_min_step or self._test_mode:
            # This can be used for online training during the first N steps,
            # the R network is totally random and the surrogate reward has no
            # meaning.
            scale_surrogate_reward = 0.0
        postprocessed_reward = (self._scale_task_reward * reward +
                                scale_surrogate_reward * bonus_reward)

        # Update the statistics.
        self._episode_task_reward += reward
        self._episode_bonus_reward += bonus_reward
        if done:
            self._stats_task_reward.add(self._episode_task_reward)
            self._stats_bonus_reward.add(self._episode_bonus_reward)
            self._episode_task_reward = 0.0
            self._episode_bonus_reward = 0.0

        # Post-processing on the observation. Note that the reward could be used
        # as an input to the agent. For simplicity we add it as a separate channel.
        postprocessed_observation = self._postprocess_observation(observation,
                                                                  reward_for_input)

        return postprocessed_observation, postprocessed_reward, done, info

    def get_episodic_memory(self):
        """Returns the episodic memory for the k-th environment."""
        return self._vec_episodic_memory

    def reset(self, seed=None, options=None):
        """Overrides VecEnvWrapper.reset."""
        # observations, _ = self.venv.reset()
        # observations = observations['screen']

        observations = self.venv.reset()
        #observations = np.expand_dims(observations, 0)  # 为了给单个环境添加一个batch_size维度
        postprocessed_observations = self._postprocess_observation(observations)

        # Clears the episodic memory of every environment.
        if self._vec_episodic_memory is not None:
            self._vec_episodic_memory.reset()

        return postprocessed_observations

    def render(self, mode="human"):
        self.venv.render(mode)

    @property
    def metadata(self) -> dict:
        """Returns the environment metadata."""
        if self._metadata is None:
            return self.venv.metadata
        return self._metadata

    @metadata.setter
    def metadata(self, value):
        self._metadata = value

    def __getattr__(self, name):
        # 如果name是Foo的属性或者方法，就返回它
        if hasattr(self.venv, name):
            return getattr(self.venv, name)
        # 否则抛出异常
        else:
            raise AttributeError(f"{self.__class__.__name__} object has no attribute {name}")
