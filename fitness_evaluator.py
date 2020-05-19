import numpy as np

class FitnessEvaluator():
    def __init__(self):
        self.fitness = 0
        self.last_features = []
        self.variables = {
            'max_dist': 0
        }

    """
    Evaluate fitness at each frame
    """
    def frame_evaluation(self, features):
        x = features[26] + 6700
        y = features[27] + 6700
        dist = np.sqrt(x ** 2 + y ** 2)
        dota_time = features[56]
        print("%ds | %d" % (dota_time, dist))

        self.variables['max_dist'] = max(self.variables['max_dist'], dist)
        self.last_features = features
        return self.fitness

    """
    Returns True if the game is to be stopped before the end
    """
    @property
    def early_stop(self):
        dota_time = self.last_features[56]
        if dota_time > 2 * 60 and self.variables['max_dist'] <= 100:
            return True
        return False

    """
    Finale fitness evaluation on the last features set
    """

    def final_evaluation(self):
        print("MAX DISTANCE", self.variables['max_dist'])
        self.fitness = self.variables['max_dist']
        return self.fitness