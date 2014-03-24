# -*- coding: utf-8 -*-


"""
==========================
Input/Output of HDF5 Files
==========================

:Authors:
    Moritz Emanuel Beber
:Date:
    2014-02-06
:Copyright:
    Copyright(c) 2014 Jacobs University of Bremen. All rights reserved.
:File:
    hdf5.py
"""


__all__ = ["ResultManager"]


import os

import numpy
import tables


UUID_LENGTH = 32 # stripped dashes


class NodeData(tables.IsDescription):
    """
    1 row per node per simulation per graph
    """
    sim_id = tables.StringCol(UUID_LENGTH) # simulation id
    graph_id = tables.StringCol(UUID_LENGTH) # graph id
    node_id = tables.UInt32Col() # node id
    directed = tables.BoolCol() # directed or undirected
    degree = tables.Float64Col()
    in_degree = tables.Float64Col()
    out_degree = tables.Float64Col()
    mean_activity = tables.Float64Col()
    std_activity = tables.Float64Col()
    internal = tables.Float64Col()
    external = tables.Float64Col()
    capacity = tables.Float64Col()
    mean_rejected = tables.Float64Col()
    std_rejected = tables.Float64Col()
    total_rejected = tables.Float64Col()


class RandomWalkData(tables.IsDescription):
    """
    """
    sim_id = tables.StringCol(UUID_LENGTH) # simulation id
    walk = tables.StringCol(8) # uniform or directed
    walk_type = tables.StringCol(8) # parallel, deletory, or buffered
    walker_dist = tables.StringCol(8) # uniform
    variation = tables.Float64Col() # variation of the number of walkers
    visit_value = tables.StringCol(8) # constant or degree
    walker_factor = tables.UInt16Col() # number of walkers in relation to graph
    steps_factor = tables.UInt16Col() # number of steps in relation to graph
    time_points = tables.UInt16Col()
    transient = tables.UInt32Col() # cut-off of transient of walk
    graph_id = tables.StringCol(UUID_LENGTH) # graph id
    graph_type = tables.StringCol(12) # ER or BA
    directed = tables.BoolCol() # directed or undirected
    capacity = tables.StringCol(8) # uniform, degree
    capacity_factor = tables.Float64Col()


class ResultManager(object):

    def __init__(self, filename, key="/", **kw_args):
        super(ResultManager, self).__init__(**kw_args)
        self.key = key
        if not os.path.exists(filename):
            self._setup(filename)
        else:
            self.h5_file = tables.open_file(filename, mode="a")
            self.root = self.h5_file._get_node(self.key)
            self.simulations = self.root.simulations
            self.results = self.root.results

    def append_sim(self, sim_id, walk, walk_type, walker_dist, variation,
            visit_value, walker_factor, steps_factor, time_points, transient,
            graph_id, graph_type, directed, capacity=None, capacity_factor=None):
        row = self.simulations.row
        row["sim_id"] = sim_id
        row["walk"] = walk
        row["walk_type"] = walk_type
        row["walker_dist"] = walker_dist
        row["variation"] = variation
        row["visit_value"] = visit_value
        row["walker_factor"] = walker_factor
        row["steps_factor"] = steps_factor
        row["time_points"] = time_points
        row["transient"] = transient
        row["graph_id"] = graph_id
        row["graph_type"] = graph_type
        row["directed"] = directed
        if capacity is not None:
            row["capacity"] = capacity
        if capacity_factor is not None:
            row["capacity_factor"] = capacity_factor
        row.append()
        self.simulations.flush()

    def append(self, sim_id, graph_id, directed, graph, node2ind, activity,
            internal, external, capacity=None, rejected=None):
        row = self.results.row
        for node in graph:
            ind = node2ind[node]
            row["sim_id"] = sim_id
            row["graph_id"] = graph_id
            row["node_id"] = ind
            row["directed"] = directed
            if directed:
                row["in_degree"] = graph.in_degree(node)
                row["out_degree"] = graph.out_degree(node)
                row["degree"] = graph.degree(node)
            else:
                row["degree"] = graph.degree(node)
            view = activity[ind, :]
            mask = numpy.isfinite(view)
            row["mean_activity"] = view[mask].mean()
            row["std_activity"] = view[mask].std(ddof=1)
            row["internal"] = internal[ind]
            row["external"] = external[ind]
            row["capacity"] = capacity[ind]
            if capacity is not None:
                row["capacity"] = capacity[ind]
            if rejected is not None:
                view = rejected[ind, :]
                mask = numpy.isfinite(view)
                row["mean_rejected"] = view[mask].mean()
                row["std_rejected"] = view[mask].std(ddof=1)
                row["total_rejected"] = view[mask].sum()
            row.append()
        self.results.flush()

    def _setup(self, filename):
        self.h5_file = tables.open_file(filename, mode="w",
                title="Random Walk Simulation Data")
        components = self.key.split("/")
        if components[1]:
            self.h5_file.create_group("/", components[1])
            for i in range(2, len(components)):
                self.h5_file.create_group("/".join(components[:i]), components[i])
        self.root = self.h5_file._get_node(self.key)
        self.simulations = self.h5_file.create_table(self.root, "simulations", RandomWalkData,
                title="Summary table for all random walk simulations.")
        self.results = self.h5_file.create_table(self.root, "results", NodeData,
                title="Per node results of simulations.")

    def finalize(self):
        self.h5_file.close()

