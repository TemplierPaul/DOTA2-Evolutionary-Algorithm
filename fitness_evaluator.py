import numpy as np

class FitnessEvaluator():
    def __init__(self):
        self.fitness = 0
        self.last_features = []
        self.variables = {}

    """
    Evaluate fitness at each frame
    """
    def frame_evaluation(self, features):
        x = features[26] + 10000
        y = features[27] + 10000
        dist = np.sqrt(x ** 2 + y ** 2)
        self.fitness = max(self.fitness, dist)
        self.last_features = features
        return self.fitness

    """
    Returns True if the game is to be stopped before the end
    """
    @property
    def early_stop(self):
        dota_time = self.last_features[56]
        if dota_time > 5*60: # Stop at 5min
            return True
        return False

    """
    Finale fitness evaluation on the last features set
    """
    def final_evaluation(self, features):
        if features == self.last_features:
            print("LAST FEATURES EVALUATED TWICE")
        return self.fitness