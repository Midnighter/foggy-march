# -*- coding: utf-8 -*-


import time
import os
import logging
import argparse
import json
import codecs
import cPickle as pickle

import numpy
import beanstalkc

import foggy
import jobq

from itertools import izip
from uuid import uuid4
from glob import glob

from IPython.parallel import Client, interactive


logging.basicConfig()
LOGGER = logging.getLogger()
#LOGGER.setLevel(logging.INFO)
LOGGER.setLevel(logging.DEBUG)
#LOGGER.addHandler(logging.StreamHandler())


###############################################################################
# Supply
###############################################################################


class JSONBeanShooter(object):
    _shooter = {
        "parallel": "_shot",
        "deletory": "_capacity_shot",
        "buffered": "_capacity_shot"
    }

    def __init__(self, bean_queue, encoding="utf-8", **kw_args):
        """
        Warning
        -------
        bean_queue must be using the right tube!
        """
        super(JSONBeanShooter, self).__init__(**kw_args)
        self.queue = bean_queue
        self.encoding = encoding

    def __call__(self, filename):
        config = json.load(codecs.open(filename, encoding=self.encoding,
            mode="rb"))
        LOGGER.debug(str(config))
        for path in config["graphs_dir"]:
            assert os.path.exists(path), "directory does not exist '%s'" % path
        shoot = getattr(self, self._shooter[config["walk_type"]])
        description = config.copy()
        del description["graphs_dir"]
        del description["graphs_type"]
        del description["walker_factors"]
        del description["steps_factors"]
        del description["variation_factors"]
        del description["capacity_factors"]
        del description["repetition"]
        for (path, net_type) in izip(config["graphs_dir"], config["graphs_type"]):
            graphs = glob(os.path.join(path, "*.pkl"))
            LOGGER.debug("%d graphs found", len(graphs))
            for net in graphs:
                description["graph_file"] = net
                description["graph_type"] = net_type
                for kw in config["walker_factors"]:
                    description["walker_factor"] = kw
                    for var in config["variation_factors"]:
                        description["variation_factor"] = var
                        for ks in config["steps_factors"]:
                            description["steps_factor"] = ks
                            for _ in range(config["repetition"]):
                                shoot(config, description)

    def _shot(self, config, description):
        description["sim_id"] = str(uuid4()).replace("-", "")
        LOGGER.debug("firing")
        self.queue.put(pickle.dumps(description))

    def _capacity_shot(self, config, description):
        description["sim_id"] = str(uuid4()).replace("-", "")
        for k in config["capacity_factors"]:
            description["capcity_factor"] = k
            LOGGER.debug("firing")
            self.queue.put(pickle.dumps(description))


###############################################################################
# Consumption
###############################################################################


def remote_consumer(worker, host, port):
    queue = beanstalkc.Connection(host=host, port=port)
    queue.watch("input")
    queue.use("output")
    jobq.generic_consumer(queue, worker, "STOP")

def dummy_worker(**kw_args):
#    LOGGER.debug(str(kw_args))
    return "success"


class BeanMuncher(object):
    _setup = {
        "uniform": foggy.prepare_uniform_walk,
        "directed": foggy.prepare_directed_walk
    }
    _type = {
        "deletory": foggy.deletory_march,
        "buffered": foggy.buffered_march,
        "parallel": foggy.march
    }
    _distribution = {
        "uniform": foggy.UniformInterval
    }
    _visit = {
        "constant": foggy.ConstantValue,
        "degree": foggy.DegreeDependentValue
    }

    def graph_info(graph):
        LOGGER.info("%s graph:", "directed" if graph.is_directed() else "undirected")
        LOGGER.info("    %d nodes", len(graph))
        LOGGER.info("    %d edges", graph.size())
        LOGGER.info("    %d component(s)", nx.number_connected_components(graph))

    def uniform_capacity(graph, indices, walkers, num_steps):
        capacity = numpy.zeros(len(graph), dtype=float)
        capacity += float(walkers.mid_point * num_steps) / float(len(graph))
        return capacity

    def degree_capacity(graph, indices, walkers, num_steps):
        capacity = numpy.zeros(len(graph), dtype=float)
        total_degree = sum(deg for (node, deg) in graph.degree_iter())
        for (node, deg) in graph.degree_iter():
            capacity[indices[node]] = float(deg * walkers.mid_point * num_steps) /\
                     total_degree
        return capacity

    _capacity = {
            "uniform" : uniform_capacity,
            "degree" : degree_capacity
    }

    def _run(self, config, description, net, nbrs, probs, indices, walkers,
            num_steps, visits, seed=None):
        job_descr = dict()
        job_descr["parameters"] = description
        job_descr["worker"] = dummy_worker
        job_descr["simulation"] = self._type[config["walk_type"]]
        job_descr["neighbours"] = nbrs
        job_descr["probabilities"] = probs
        job_descr["sources"] = indices.values()
        job_descr["num_walkers"] = walkers
        job_descr["time_points"] = config["time_points"]
        job_descr["steps"] = num_steps
        job_descr["assessor"] = visits
        job_descr["transient"] = config["transient"]
        job_descr["seed"] = seed
        job_descr["capacity"] = None

    def _capacity_run(self, config, description, net, nbrs, probs, indices, walkers,
            num_steps, visits, seed=None):
        description["sim_id"] = str(uuid4()).replace("-", "")
        job_descr = dict()
        job_descr["parameters"] = description
        job_descr["worker"] = dummy_worker
        job_descr["simulation"] = self._type[config["walk_type"]]
        job_descr["neighbours"] = nbrs
        job_descr["probabilities"] = probs
        job_descr["sources"] = indices.values()
        job_descr["num_walkers"] = walkers
        job_descr["time_points"] = config["time_points"]
        job_descr["steps"] = num_steps
        job_descr["assessor"] = visits
        job_descr["transient"] = config["transient"]
        job_descr["seed"] = seed
        capacity = self._capacity[config["capacity"]](net, indices, walkers, num_steps)

    _dispatch = {
        "parallel": "_run",
        "deletory": "_capacity_run",
        "buffered": "_capacity_run"
    }

    def __init__(self, bean_queue, encoding="utf-8", **kw_args):
        """
        Warning
        -------
        bean_queue must be using the right tube!
        """
        super(JSONBeanShooter, self).__init__(**kw_args)
        self.queue = bean_queue
        self.encoding = encoding

    def __call__(self, filename):
        config = json.load(codecs.open(filename, encoding=self.encoding,
            mode="rb"))
        LOGGER.debug(str(config))
        for path in config["graphs_dir"]:
            assert os.path.exists(path), "directory does not exist '%s'" % path
        setup = self._setup[config["walk_setup"]]
        distribution = self._distribution[config["walker_dist"]]
        visits = self._visit[config["visit_value"]]
        simulation = getattr(self, self._dispatch[config["walk_type"]])
        description = dict()
        description["walk_setup"] = config["walk_setup"]
        description["walk_type"] = config["walk_type"]
        description["walker_dist"] = config["walker_dist"]
        description["visit_value"] = config["visit_value"]
        description["capacity"] = config["capacity"]
        description["transient"] = config["transient"]
        for (path, net_type) in izip(config["graphs_dir"], config["graphs_type"]):
            graphs = [nx.read_gpickle(net_file) for net_file in glob(os.path.join(path, "*.pkl"))]
            LOGGER.debug("%d graphs found", len(graphs))
            for net in graphs:
                description["graph_name"] = net.name
                description["graph_type"] = net_type
                graph_info(net)
                (probs, nbrs, indices) = setup(net)
                for kw in config["walker_factors"]:
                    description["walker_factor"] = kw
                    num_walkers = len(net) * kw
                    for var in config["variation_factors"]:
                        description["variation_factor"] = var
                        walkers = distribution(num_walkers, num_walkers * var)
                        for ks in config["steps_factors"]:
                            description["steps_factor"] = ks
                            num_steps = len(net) * ks
                            for _ in range(config["repetition"]):
                                simulation(config, description, net, nbrs, probs, indices,
                                    walkers, num_steps, visits, seed=None)


###############################################################################
# Results
###############################################################################


def dummy_handler(result):
    LOGGER.debug(str(result))

def result_handler(result):
    results = foggy.ResultManager(h5_file)
    filename = os.path.join(out_path, sim_id)
    numpy.savez(filename, activity=activity)
    numpy.savez(filename, activity=activity, hits=removed, capacity=dynamic)
    results.append(sim_id, graph.name, graph.is_directed(), graph, indices,
            activity, internal, external)
    results.append_sim(sim_id, config["walk"], config["walk_type"],
            config["walker_dist"], config["walker_variation"],
            config["visit_value"], config["walker_factor"],
            config["steps_factor"], config["time_points"],
            config["transient_cutoff"], graph.name, graph_type, graph.is_directed())
    results.finalize()


###############################################################################
# Main
###############################################################################


def supply(args):
    queue = beanstalkc.Connection(host=args.host, port=args.port)
    queue.use("input")
    dispatch = JSONBeanShooter(queue)
    watcher = jobq.DirectoryWatcher(args.watch_dir, dispatch, glob_pattern=args.glob, wait=5.0)
    watcher.start()
    LOGGER.debug("watcher running")
    while watcher.is_alive():
        try:
            time.sleep(0.1)
        except (KeyboardInterrupt, SystemExit):
            LOGGER.info("shutdown signal received")
            watcher.stop()
            break
    watcher.join()
    queue.close()

def consume(args):
    rc = Client(profile=args.profile)
    dv = rc.direct_view()
    LOGGER.debug("remote module import")
    dv.execute("import beanstalkc; import foggy; import jobq", block=True)
    LOGGER.debug("pushing remote variables")
    dv.push({"consumer": remote_consumer, "worker": dummy_worker,
        "host": args.host, "port": args.port}, block=True)
    LOGGER.debug("remote function call")
    dv.execute("consumer(worker, host, port)", block=False)

def handle(args):
    queue = beanstalkc.Connection(host=args.host, port=args.port)
    queue.watch("output")
    jobq.generic_handler(queue, dummy_handler)
    queue.close()
    return

def info(args):

    def queue_info(stats):
        LOGGER.info("All jobs: %d", stats["total-jobs"])
        LOGGER.info("Jobs handled correctly: %d", stats["cmd-delete"])
        LOGGER.info("Jobs in queue: %d", stats["current-jobs-ready"])
        LOGGER.info("Jobs failed: %d", stats["current-jobs-buried"])

    queue = beanstalkc.Connection(host=args.host, port=args.port)
    show_total = False
    try:
        stats = queue.stats_tube("input")
    except beanstalkc.CommandFailed:
        show_total = True
    else:
        LOGGER.info("%s", "".join(["*"] * 58))
        LOGGER.info("Input queue statistics:")
        queue_info(stats)
    try:
        stats = queue.stats_tube("output")
    except beanstalkc.CommandFailed:
        show_total = True
    else:
        LOGGER.info("%s", "".join(["*"] * 58))
        LOGGER.info("Output queue statistics:")
        queue_info(stats)
    if show_total:
        LOGGER.info("%s", "".join(["*"] * 58))
        LOGGER.info("Total queue statistics:")
        queue_info(queue.stats())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=None)
    parser.add_argument("-V", "--version", action="version", version="0.1")
    parser.add_argument("-l", "--host", dest="host", metavar="IP", default="127.0.0.1",
            help="host IP address of beanstalkd queue (default: %(default)s)")
    parser.add_argument("-p", "--port", dest="port", type=int, default=11300,
            help="host port of beanstalkd queue (default: %(default)d)")
    subparsers = parser.add_subparsers(help="sub-command help")
# supply
    parser_s = subparsers.add_parser("supply",
            help="supply the beanstalkd queue with jobs")
    parser_s.add_argument(dest="watch_dir", metavar="watched directory",
            help="directory to watch for job config files")
    parser_s.add_argument("-g", "--glob", dest="glob", default="*",
            help="extension of files that configure jobs (default: %(default)s)")
    parser_s.set_defaults(func=supply)
# consume
    parser_c = subparsers.add_parser("consume", help="consume jobs")
    parser_c.add_argument("--profile", dest="profile", default="default",
            help="IPython profile to connect to cluster (default: %(default)s)")
    parser_c.set_defaults(func=consume)
# handle
    parser_h = subparsers.add_parser("handle", help="handle results")
    parser_h.set_defaults(func=handle)
# info
    parser_i = subparsers.add_parser("info", help="print queue stats")
    parser_i.set_defaults(func=info)
    args = parser.parse_args()
    args.func(args)

