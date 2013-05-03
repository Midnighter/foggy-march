# -*- coding: utf-8 -*-


"""
==========================
Random Walkers on Networks
==========================

:Author:
    Moritz Emanuel Beber
:Date:
    2012-10-23
:Copyright:
    Copyright |c| 2013, Jacobs University Bremen gGmbH, all rights reserved.
:File:
    walkers.py

.. |c| unicode:: U+A9
"""


import sys
import itertools
import bisect
import numpy
import networkx as nx

from IPython.parallel import interactive, require, LoadBalancedView


class UniformInterval(object):

    def __init__(self, mid_point, variation=0, **kw_args):
        super(UniformInterval, self).__init__(**kw_args)
        self.rand_int = numpy.random.random_integers
        self.mid_point = int(mid_point)
        self.variation = int(variation)
        self.mini = max(self.mid_point - self.variation, 0)
        self.maxi = self.mid_point + self.variation

    def __call__(self):
        if self.variation > 0:
            self.__call__ = self.variable
        else:
            self.__call__ = self.constant
        return self.__call__()

    def constant(self):
        return self.mid_point

    def variable(self):
        return self.rand_int(self.mini, self.maxi)


class ConstantValue(object):

    def __init__(self, constant=1.0, **kw_args):
        super(ConstantValue, self).__init__(**kw_args)
        self.value = constant

    def __call__(self, *args):
        return self.value


class DegreeDependentValue(object):

    def __init__(self, graph, indices, weight=None, mu=1.0, **kw_args):
        super(DegreeDependentValue, self).__init__(**kw_args)
        self.values = dict()
        mu = float(mu)
        for (node, deg) in graph.degree_iter(weight=weight):
            self.values[indices[node]] = numpy.power(float(deg), mu)

    def __call__(self, node, *args):
        return self.values[node]

def compute_mu(alpha, nu=1.0):
    """
    Mathematica on real domain:
    \begin{align}
        \alpha &= \dfrac{1}{2} \left( 1 + \dfrac{\dfrac{\mu}{\nu}}{\dfrac{\mu}{\nu} + 1} \right) \\
        \mu &= \dfrac{\nu - 2 \alpha \nu}{2 \left( \alpha - 1 \right)}
    \end{align}
    """
    alpha = float(alpha)
    nu = float(nu)
    return (nu - (2.0 * alpha * nu)) / (2 * (alpha - 1.0))

def prepare_uniform_walk(graph, weight=None):
    """
    Prepare data structures for a uniform random walk.

    Works for undirected as well as directed graphs. For multi-graphs simply
    provide a suitable edge weight.

    Arguments
    ---------
    graph: nx.(Di)Graph
        The underlying network.
    weight: hashable
        The keyword for edge data that should be used to weigh the propagation
        probability.
    """
    nodes = sorted(graph.nodes())
    if len(nodes) < 2:
        raise nx.NetworkXError("network is too small")
    indices = dict(itertools.izip(nodes, itertools.count()))
    probabilities = list()
    neighbours = list()
    for (i, node) in enumerate(nodes):
        adj = graph[node]
        out_deg = len(adj)
        if out_deg == 0:
            probabilities.append([])
            neighbours.append([])
            continue
        prob = 0.0
        probabilities.append(numpy.zeros(out_deg, dtype=float))
        neighbours.append(numpy.zeros(out_deg, dtype=int))
        for (j, (nhbr, data)) in enumerate(adj.iteritems()):
            neighbours[i][j] = indices[nhbr]
            prob += data.get(weight, 1.0)
            probabilities[i][j] = prob
        # prob is now the sum of all edge weights, normalise to unity
        probabilities[i] /= prob
    return (probabilities, neighbours, indices)

@require(numpy, bisect)
@interactive
def uniform_random_walker(node):
    """
    Perform a single random walk on a network with a uniform probability of a
    next step.

    Arguments
    ---------
    """
    # accessing globals `probabilities`, `neighbours`, and `steps that were pushed before
    local_probs = probabilities
    local_nbrs = neighbours
    smpl = numpy.random.random_sample
    choose = bisect.bisect_left
    path = [node]
    for s in xrange(steps):
        nbrs = local_nbrs[node]
        if len(nbrs) == 0:
            break
        draw = smpl()
        # the nbrs list and probs list correspond to each other
        # we use a binary search to find the index to the left of the
        # probability and take that node
        node = nbrs[choose(local_probs[node], draw)]
        path.append(node)
    return path

def parallel_march(d_view, neighbours, probabilities, sources, num_walkers, time_points,
        steps, assessor=ConstantValue(), lb_view=None):
    """
    Start a number of random walkers on the given network for given time points.
    """
    time_points = int(time_points)
    steps = int(steps)
    length = len(sources)
    rand_int = numpy.random.randint
    # compute a running mean and sd as per:
    # http://en.wikipedia.org/wiki/Standard_deviation#Rapid_calculation_methods
    visits = numpy.zeros(len(neighbours))
    mean_fluxes = numpy.zeros(len(neighbours))
    subtraction = numpy.zeros(len(neighbours))
    std_fluxes = numpy.zeros(len(neighbours))
    # make available on remote kernels
    d_view.push(dict(neighbours=neighbours, probabilities=probabilities,
        steps=steps), block=True)
    view = isinstance(lb_view, LoadBalancedView)
    if view:
        num_krnl = len(lb_view)
    sys.stdout.write("\r{0:.2%} complete".format(0.0))
    sys.stdout.flush()
    for time in xrange(1, time_points + 1):
        visits.fill(0)
        curr_num = num_walkers()
        if view:
            size = max((curr_num - 1) // (num_krnl * 2), 1)
            results = lb_view.map(uniform_random_walker,
                    [sources[rand_int(length)] for i in xrange(curr_num)],
                    block=False, ordered=False, chunksize=size)
        else:
            results = d_view.map(uniform_random_walker,
                    [sources[rand_int(length)] for i in xrange(curr_num)],
                    block=False)
        for path in results:
            for node in path:
                visits[node] += assessor(node)
        # compute running average and variation
        subtraction = visits - mean_fluxes
        mean_fluxes += subtraction / time
        std_fluxes += subtraction * (visits - mean_fluxes)
        sys.stdout.write("\r{0:.2%} complete".format(time / float(time_points)))
        sys.stdout.flush()
    std_fluxes /= float(time - 1)
    std_fluxes = numpy.sqrt(std_fluxes)
    sys.stdout.write("\n")
    return (mean_fluxes, std_fluxes)

