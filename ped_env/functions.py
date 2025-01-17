import math
import random
import timeit
from typing import List

import numpy as np
import pyglet

from numba import njit

from ped_env.settings import ACTION_DIM


def calculate_groups_person_num(env, person_num_sum) -> List:
    reminder = person_num_sum % len(env.terrain.start_points)
    person_num_in_every_spawn = person_num_sum // len(env.terrain.start_points) \
        if person_num_sum >= len(env.terrain.start_points) else 1
    person_num = [person_num_in_every_spawn
                  for _ in range(len(env.terrain.start_points))]
    person_num[-1] += reminder
    return person_num


@njit
def transfer_to_render(x, y, X, Y, scale=30):
    '''
    该函数将物理坐标转化为渲染坐标来进行输出
    :param x: 物体中心点坐标x
    :param y: 物体中心点坐标y
    :param X: 物体的宽度X
    :param Y: 物体的高度Y
    :param scale: 物理坐标与像素坐标的放大比例
    :return:
    '''
    x_, y_ = x - X / 2, y - Y / 2
    return x_ * scale, y_ * scale, X * scale, Y * scale


def calculate_nij(i, j):
    pos_i = i.pos
    pos_j = j.pos
    return normalize_vector(pos_i - pos_j)


from math import sqrt, acos


@njit
def angle_of_vector(v1, v2):
    pi = 3.1415
    vector_prod = v1[0] * v2[0] + v1[1] * v2[1]
    length_prod = sqrt(pow(v1[0], 2) + pow(v1[1], 2)) * sqrt(pow(v2[0], 2) + pow(v2[1], 2))
    cos = vector_prod * 1.0 / (length_prod * 1.0 + 1e-6)
    return (acos(cos) / pi) * 180


def parse_discrete_action_one_hot(type: np.ndarray):
    from ped_env.settings import actions
    return actions[np.argmax(type).item()]


def parse_discrete_action(type: np.ndarray):
    from ped_env.settings import actions
    return actions[type]


@njit
def inner(v):
    v = v.astype(np.float64)
    norm = np.linalg.norm(v)
    if norm == 0:
        return v
    return v / norm


def normalize_vector(v: np.ndarray):
    if not isinstance(v, np.ndarray):
        v = np.array(v)
    return inner(v)


def calculate_each_group_num(group_size, person_num):
    '''
    根据人数随机计算每组人数的多少
    :param group_size:一个元组，代表一个组的范围
    :param person_num:需要分配的人总数
    :return:
    '''
    group_avg = int(sum(group_size) / 2)
    leader_num = int(person_num / group_avg)
    if leader_num == 0:
        raise Exception("Person_num must be bigger than group_avg_num!")
    else:
        group_num = []
        left_num = person_num
        for i in range(0, leader_num):
            num_in_one_group = random.randint(group_size[0], group_size[1])
            group_num.append(num_in_one_group)
            left_num -= num_in_one_group
        group_num[-1] += left_num
    return group_num


def random_pick(some_list, probabilities):
    x = random.uniform(0, 1)
    cumulative_probability = 0.0
    for item, item_probability in zip(some_list, probabilities):
        cumulative_probability += item_probability
        if x < cumulative_probability:
            break
    return item


@njit
def ij_power(r, A=0.01610612736, B=3.93216):
    ij_group_f = (A / (pow(r, 12)) - B / (pow(r, 6)))
    return ij_group_f


@njit
# 定义函数，将角度转换为弧度
def deg_to_rad(degrees):
    return degrees * math.pi / 180


@njit
# 定义函数，计算三角形的顶点坐标
def calc_triangle_points(pos, length, angle):
    # 将角度转换为弧度
    angle_rad = deg_to_rad(angle)

    # 计算三角形的顶点坐标
    x1 = pos[0] + length * math.cos(angle_rad)
    y1 = pos[1] - length * math.sin(angle_rad)

    x2 = pos[0] + length * math.cos(angle_rad + deg_to_rad(120))
    y2 = pos[1] - length * math.sin(angle_rad + deg_to_rad(120))

    x3 = pos[0] + length * math.cos(angle_rad + deg_to_rad(240))
    y3 = pos[1] - length * math.sin(angle_rad + deg_to_rad(240))

    return [(x1, y1), (x2, y2), (x3, y3)]


def gray_scale_image(frame: np.ndarray) -> np.ndarray:
    # 将输入数组的最后一个维度（即A通道）丢弃，得到一个形状为（3, height, width）的RGB图像数组。
    frame = frame[:, :, :]

    # 将输入数组缩放到 [0, 1] 范围内
    frame = frame / 255.0

    weights = np.array([0.2989, 0.5870, 0.1140])

    # 沿着第一个轴对数组进行加权平均，得到形状为 [height, width] 的灰度图像
    gray_frame = np.average(frame, axis=2, weights=weights)

    # 将堆叠后的灰度图像数组作为输出返回
    return gray_frame



def angle_between(v1, v2):
    """ Returns the angle in radians between vectors 'v1' and 'v2'::

            >>> angle_between((1, 0, 0), (0, 1, 0))
            1.5707963267948966
            >>> angle_between((1, 0, 0), (1, 0, 0))
            0.0
            >>> angle_between((1, 0, 0), (-1, 0, 0))
            3.141592653589793
    """
    v1_u = normalize_vector(v1)
    v2_u = normalize_vector(v2)
    radian = np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))
    clockwise = np.cross(v1_u, v2_u) <= 0
    return radian if not clockwise else 2 * np.pi - radian


if __name__ == '__main__':
    print(normalize_vector(np.array([1, 2, 3])))

    import time


    def normalize_vector_raw(v: np.ndarray):
        v = v.astype(np.float64)
        norm = np.linalg.norm(v)
        if norm == 0:
            return v
        return v / norm


    N = 100000
    raw = np.array([1, 2, 3])

    t1 = time.time()
    for i in range(N):
        normalize_vector_raw(raw)

    t2 = time.time()
    for i in range(N):
        normalize_vector(raw)
    t3 = time.time()
    print("{},{}".format(t2 - t1, t3 - t2))
    # for i in range(10):
    #     group_size = (5, 5)
    #     person_num = 10
    #     ret = calculate_each_group_num(group_size, person_num)
    #     print(ret)
    # Af, Bf = 0.4, 240
    # A = 4 * pow(Af, 12) * Bf
    # B = 4 * pow(Af, 6_map11_use) * Bf
    # sigma = pow(A / B, 1/6_map11_use)
    # mu = pow(B, 2)/(4*A)
    # print("Af={},Bf={},A={},B={},mu={},sigma={}".format(Af, Bf, A, B, mu, sigma))

    # delta, counter = 0.01, 0
    # start = 0.37
    # x, y = [], []
    # while counter <= 150:
    #     counter += 1
    #     r = (delta * counter) + start
    #     force = ij_power(r)
    #     x.append(counter / 100 + start)
    #     y.append(force)
    # import matplotlib.pyplot as plt
    #
    # plt.plot(x, y)
    # plt.show()
    pass



