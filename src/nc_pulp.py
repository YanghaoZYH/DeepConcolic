from typing import *
from pulp import *
from utils import *
from pulp_encoding import *
import numpy as np

# ---

from engine import LayerLocalAnalyzer
from nc import NcAnalyzer, NcTarget
from lp import PulpLinearMetric, PulpSolver4DNN


class NcPulpAnalyzer (NcAnalyzer, LayerLocalAnalyzer, PulpSolver4DNN):

  def __init__(self, input_metric: PulpLinearMetric = None, **kwds):
    assert isinstance (input_metric, PulpLinearMetric)
    super().__init__(**kwds)
    self.metric = input_metric


  def finalize_setup(self, clayers):
    super().build_lp (self.dnn, self.metric,
                      upto = deepest_tested_layer (self.dnn, clayers))


  def input_metric(self):
    return self.metric


  def search_input_close_to(self, x, target: NcTarget):
    problem = self.for_layer (target.layer)
    activations = eval_batch (self.dnn, np.array([x]))
    cstrs = []

    # Augment problem with activation constraints up to layer of
    # target:
    target_neuron = target.position[0]
    prev = self.input_layer_encoder
    for lc in self.layer_encoders:
      if lc.layer_index < target.layer.layer_index:
        cstrs.extend(lc.pulp_replicate_activations (activations, prev))
        prev = lc
      else:
        cstrs.extend(lc.pulp_replicate_activations (activations, prev,
                                                    exclude = (lambda nidx: nidx == target_neuron)))
        cstrs.extend(lc.pulp_negate_activation (activations, target_neuron, prev))
        break

    res = self.find_constrained_input (problem, self.metric, x,
                                       extra_constrs = cstrs)

    if not res:
      return None
    else:
      dist = self.metric.distance (x, res[1])
      return dist, res[1]


# ---
