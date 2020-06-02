import numpy as np

"""
Distance from the center it must have reached
"""
MIN_DIST = {
    60: 6500,
    120: 6000,
    180: 5000,
    240: 4000,
    200: 2000
}

class FitnessEvaluator():
    def __init__(self):
        self.fitness = 0
        self.last_features = []
        self.variables = {
            'min_dist': np.inf
        }

    """
    Evaluate fitness at each call
    """
    def frame_evaluation(self, features):
        x = features[26]
        y = features[27]
        dist = np.sqrt(x ** 2 + y ** 2)  # Distance from the center
        dota_time = features[56]

        self.variables['min_dist'] = min(self.variables['min_dist'], dist)

        net_worth = features[23]
        passive_gold = 1.3 * dota_time + 598  # 598 = start gold
        self.fitness = net_worth - passive_gold

        # print("%ds | %d | %d" % (dota_time, dist, self.variables['max_dist']))
        print("%ds | %dg | %d" % (dota_time, self.fitness, self.variables['min_dist']))
        self.last_features = features
        return self.fitness

    """
    Returns True if the game is to be stopped before the end
    """
    @property
    def early_stop(self):
        dota_time = self.last_features[56]
        for time, dist in MIN_DIST.items():
            if dota_time > time and self.variables['min_dist'] >= dist:
                return True
        return False

    """
    Finale fitness evaluation on the last features set
    """

    def final_evaluation(self):
        print("MIN DISTANCE", self.variables['min_dist'])
        print("NET WORTH", self.fitness)
        # self.fitness = self.variables['max_dist']
        return self.fitness

    def reset(self):
        self.fitness = 0
        self.last_features = []
        self.variables = {
            'min_dist': np.inf
        }
        print("FitnessEvaluator reset")
