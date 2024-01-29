import numpy as np

from openpilot.common.numpy_fast import interp
from openpilot.common.params import Params

params = Params()
params_memory = Params("/dev/shm/params")

class FrogPilotFunctions:
  # Acceleration profiles - Credit goes to the DragonPilot team!
                   # MPH = [0.,  35,   35,  40,    40,  45,    45,  67,    67,   67, 123]
  A_CRUISE_MIN_BP_CUSTOM = [0., 2.0, 2.01, 11., 11.01, 18., 18.01, 28., 28.01,  33., 55.]
                   # MPH = [0., 6.71, 13.4, 17.9, 24.6, 33.6, 44.7, 55.9, 67.1, 123]
  A_CRUISE_MAX_BP_CUSTOM = [0.,    3,   6.,   8.,  11.,  15.,  20.,  25.,  30., 55.]

  A_CRUISE_MIN_VALS_ECO = [-0.480, -0.480, -0.40, -0.40, -0.40, -0.36, -0.32, -0.28, -0.28, -0.25, -0.25]
  A_CRUISE_MAX_VALS_ECO = [3.5, 3.3, 1.7, 1.1, .76, .62, .47, .36, .28, .09]

  A_CRUISE_MIN_VALS_SPORT = [-0.500, -0.500, -0.42, -0.42, -0.42, -0.42, -0.40, -0.35, -0.35, -0.30, -0.30]
  A_CRUISE_MAX_VALS_SPORT = [3.5, 3.5, 3.0, 2.6, 1.4, 1.0, 0.7, 0.6, .38, .2]

  @staticmethod
  def get_min_accel_eco(v_ego):
    return interp(v_ego, FrogPilotFunctions.A_CRUISE_MIN_BP_CUSTOM, FrogPilotFunctions.A_CRUISE_MIN_VALS_ECO)

  @staticmethod
  def get_max_accel_eco(v_ego):
    return interp(v_ego, FrogPilotFunctions.A_CRUISE_MAX_BP_CUSTOM, FrogPilotFunctions.A_CRUISE_MAX_VALS_ECO)

  @staticmethod
  def get_min_accel_sport(v_ego):
    return interp(v_ego, FrogPilotFunctions.A_CRUISE_MIN_BP_CUSTOM, FrogPilotFunctions.A_CRUISE_MIN_VALS_SPORT)

  @staticmethod
  def get_max_accel_sport(v_ego):
    return interp(v_ego, FrogPilotFunctions.A_CRUISE_MAX_BP_CUSTOM, FrogPilotFunctions.A_CRUISE_MAX_VALS_SPORT)