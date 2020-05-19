import numpy as np

"""
Dict {dota_time: minimum value for max_dist to continue the game
"""
MIN_DIST = {
    60: 300,
    120: 400
}

class FitnessEvaluator():
    def __init__(self):
        self.fitness = 0
        self.last_features = []
        self.variables = {
            'max_dist': 0
        }
        print("FitnessEvaluator created")
        print("Max dist", self.variables['max_dist'])

    """
    Evaluate fitness at each frame
    """
    def frame_evaluation(self, features):
        x = features[26] + 6700
        y = features[27] + 6700
        dist = np.sqrt(x ** 2 + y ** 2)
        dota_time = features[56]
        print("%ds | %d | %d" % (dota_time, dist, self.variables['max_dist']))

        self.variables['max_dist'] = max(self.variables['max_dist'], dist)
        self.last_features = features
        return self.fitness

    """
    Returns True if the game is to be stopped before the end
    """
    @property
    def early_stop(self):
        dota_time = self.last_features[56]
        for time, dist in MIN_DIST.items():
            if dota_time > time and self.variables['max_dist'] <= dist:
                return True
        return False

    """
    Finale fitness evaluation on the last features set
    """

    def final_evaluation(self):
        print("MAX DISTANCE", self.variables['max_dist'])
        self.fitness = self.variables['max_dist']
        return self.fitness