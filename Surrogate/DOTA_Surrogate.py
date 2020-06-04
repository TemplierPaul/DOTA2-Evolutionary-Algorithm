import Surrogate.preprocessing as prep
from Surrogate.constant_features import *
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

        # Remove constants
        if prep.remove_constant_features:
            state_transformed = remove_constants(self.state)
        else:
            state_transformed = self.state

        # Transform state : remove features and scale
        state_transformed = self.scaler.transform(state_transformed.reshape(1, -1))

        # Transform action into vector
        action_vect = prep.actions_to_vect(action).reshape(1, -1)

        # Create input for surrogate
        x = np.concatenate([state_transformed, action_vect], axis=1)

        # Predict next state
        y = self.model.predict(x)

        # Revert scaling
        y = self.scaler.inverse_transform(y)[0]

        # Add constant features back
        if prep.remove_constant_features:
            y = add_constants(y)

        self.state = y

        # Increment step count
        self.step_nb += 1
        return self.state

    def render(self, mode='human'):
        t = self.state[56]
        x, y = self.state[26:28]
        print("%d > Time: %d | (%d , %d)" % (self.step_nb, t, x, y))
        return self.state
