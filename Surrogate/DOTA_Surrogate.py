import Surrogate.preprocessing as prep
import numpy as np
import pandas as pd


class DOTA2_surrogate:
    def __init__(self, model, scaler):
        self.state = None
        self.agent = None
        self.model = model
        self.scaler = scaler
        self.step_nb = 0

    def reset(self):
        # Reset env
        self.state = np.array(pd.read_csv("Init_state.csv", index_col=0, names=['init'])['init'])
        self.step_nb = 0
        print("Env Reset")
        return self.state

    def step(self, action):
        if self.state is None:
            self.reset()

        state_scaled = self.scaler.transform(self.state.reshape(1, -1))

        action_vect = prep.actions_to_vect(action).reshape(1, -1)

        x = np.concatenate([state_scaled, action_vect], axis=1)

        y = self.model.predict(x)
        self.state = self.scaler.inverse_transform(y)[0]
        self.step_nb += 1
        return self.state

    def render(self, mode='human'):
        t = self.state[56]
        x, y = self.state[26:28]
        print("%d > Time: %d | (%d , %d)" % (self.step_nb, t, x, y))
        return self.state
