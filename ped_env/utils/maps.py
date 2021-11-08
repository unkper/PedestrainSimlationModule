import numpy as np
from numpy import flipud


class Map():
    def __init__(self, map: np.ndarray, exits: list, start_points: list, name, radius):
        # 对地图进行翻转操作
        map = flipud(map)
        self.map = map.T
        self.exits = exits
        self.start_points = start_points
        self.create_radius = radius
        self.name = name

    def get_render_scale(self, window_size: int = 500):
        '''
        得到缩放比例，500*500的窗口大小
        :return:
        '''
        size = self.map.shape[0]
        return window_size / size

    def __str__(self):
        return self.name


exits_1 = [(49.5, 17.5), (49.5, 34.5)]
exits_2 = [(10, 3), (10, 7)]
# (生成点中心x,生成点中心y)
start_points_1 = [(5, 20), (5, 30)]
start_points_2 = [(1, 3), (1, 7)]

# 0代表空地,1代表障碍物,2代表外部墙,3-9代表终点

map3 = np.array([
    [2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 2],
    [2, 0, 0, 1, 1, 0, 0, 0, 0, 3],
    [2, 0, 0, 1, 1, 0, 0, 0, 0, 3],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 2],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 2],
    [2, 0, 0, 0, 0, 0, 1, 1, 0, 3],
    [2, 0, 0, 0, 0, 0, 1, 1, 0, 3],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 2],
    [2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
])

map4 = np.array([
    [2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
    [2, 0, 0, 1, 1, 0, 0, 0, 0, 2],
    [2, 0, 0, 1, 1, 0, 0, 0, 0, 3],
    [2, 0, 0, 1, 1, 0, 0, 0, 0, 3],
    [2, 0, 0, 1, 1, 0, 0, 0, 0, 2],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 2],
    [2, 0, 0, 1, 1, 0, 0, 0, 0, 3],
    [2, 0, 0, 1, 1, 0, 0, 0, 0, 3],
    [2, 0, 0, 1, 1, 0, 0, 0, 0, 2],
    [2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
])

start_points_map5 = [(1.5, 3), (1.5, 8)]
exit_map5 = [(11.5, 9), (11.5, 2)]
radius_map5 = 1

map5 = np.array([
    [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3],
    [2, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 3],
    [2, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 2],
    [2, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 2],
    [2, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 2],
    [2, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 2],
    [2, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0, 4],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4],
    [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
])

start_points_map6 = [(1.5, 3), (1.5, 8)]
exit_map6 = [(11.5, 9), (11.5, 2)]
radius_map6 = 1

map6 = np.array([
    [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3],
    [2, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 3],
    [2, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 2],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2],
    [2, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 2],
    [2, 0, 0, 1, 1, 0, 0, 1, 1, 0, 0, 4],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4],
    [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
])

start_points_map7 = [(6.5, 2), (9, 6.5), (6.5, 9), (2, 6.5)]
exit_map7 = [(6.5, 11.5), (0.5, 6.5), (6.5, 0.5), (11.5, 6.5)]
radius_map7 = 1.5

map7 = np.array([
    [2, 2, 2, 2, 2, 3, 3, 3, 2, 2, 2, 2],
    [2, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 2],
    [2, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 2],
    [2, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 2],
    [4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 6],
    [4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 6],
    [4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 6],
    [2, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 2],
    [2, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 2],
    [2, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 2],
    [2, 1, 1, 1, 1, 0, 0, 0, 1, 1, 1, 2],
    [2, 2, 2, 2, 2, 5, 5, 5, 2, 2, 2, 2],
])

start_points_map8 = [(9, 2)]
exit_map8 = [(1.5, 11.5)]
radius_map8 = 1.5

map8 = np.array([
    [2, 3, 3, 3, 2, 2, 2, 2, 2, 2, 2, 2],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2],
    [2, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1, 2],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2],
    [2, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 2],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2],
    [2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
])

exit_test_map = [(10, 3), (10, 7)]
start_points_test_map = [(4, 7),(4.5, 1),(2.125, 7),(4.5, 7),(6.0125, 7)]
radius_test_map = 0
test_map = np.array([
    [2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 2],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 3],
    [2, 0, 0, 1, 1, 1, 1, 0, 0, 3],
    [2, 0, 0, 0, 0, 1, 0, 0, 0, 2],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 2],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 3],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 3],
    [2, 0, 0, 0, 0, 0, 0, 0, 0, 2],
    [2, 2, 2, 2, 2, 2, 2, 2, 2, 2],
])

map_05 = Map(map5, exit_map5, start_points_map5, "map_05", radius_map5)
map_06 = Map(map6, exit_map6, start_points_map6, "map_06", radius_map6)
map_07 = Map(map7, exit_map7, start_points_map7, "map_07", radius_map7)
map_08 = Map(map8, exit_map8, start_points_map8, "map_08", radius_map8)
map_test = Map(test_map, exit_test_map, start_points_test_map, "map_test", radius_test_map)