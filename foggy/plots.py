# -*- coding: utf-8 -*-


"""
======================
Variance Scaling Plots
======================

:Author:
    Moritz Emanuel Beber
:Date:
    2013-05-03
:Copyright:
    Copyright |c| 2013 Jacobs University Bremen gGmbH, all rights reserved.
:File:
    plots.py


.. |c| unicode:: U+A9
"""


__all__ = ["BREWER_SET1", "fluctuation_scaling", "fluctuation_scaling_fit",
        "internal_external_ratio"]


import logging

import numpy
#import scipy.stats as stats
import matplotlib.pyplot as plt

from itertools import izip
from .miscellaneous import NullHandler


LOGGER = logging.getLogger(__name__)
LOGGER.addHandler(NullHandler())

BREWER_SET1 = ["#E41A1C", "#377EB8", "#4DAF4A", "#984EA3", "#FF7F00", "#FFFF33",
        "#A65628", "#F781BF", "#8DD3C7"]


def fluctuation_scaling(data, labels):
    """
    Plot many curves with labels.

    data: list
        Contains tuples of x-locations and y-locations.
    labels: list
        For each pair in ``data`` one string.
    """
    x_min = numpy.inf
    x_max = -numpy.inf
    y_min = numpy.inf
    plt.xscale("log")
    plt.yscale("log")
    for ((x_loc, y_loc), label, colour) in izip(data, labels, BREWER_SET1):
        mask = numpy.isfinite(x_loc) & (x_loc > 0.0) & numpy.isfinite(y_loc) & (y_loc > 0.0)
        x_loc = x_loc[mask]
        y_loc = y_loc[mask]
        if len(x_loc) == 0 or len(y_loc) == 0:
            continue
        tmp = x_loc.min()
        if tmp < x_min:
            x_min = tmp
        tmp = x_loc.max()
        if tmp > x_max:
            x_max = tmp
        tmp = y_loc.min()
        if tmp < y_min:
            y_min = tmp
        plt.scatter(x_loc, y_loc, label=label, color=colour)
    plt.xlabel("$<f_{i}>$")
    plt.ylabel("$\\sigma_{i}$")
#    if all(num > 0.0 for num in [x_min, x_max, y_min]):
#        plt.plot([x_min, x_max], [y_min, (x_max - x_min) + y_min], color="black")
#    if all(num > 1.0 for num in [x_min, x_max, y_min]):
#        plt.plot([x_min, x_max], [y_min, numpy.sqrt(x_max - x_min) + y_min],
#                color="black", linestyle="dashed")
    plt.legend()
    plt.show()

def fluctuation_scaling_fit(data, labels, loc_modifier=5.0):
    glob_x_min = numpy.inf
    glob_x_max = -numpy.inf
    glob_y_min = numpy.inf
    fits = list()
    plt.xscale("log")
    plt.yscale("log")
    for ((x_loc, y_loc), label, colour) in izip(data, labels, BREWER_SET1):
        mask = numpy.isfinite(x_loc) & (x_loc > 0.0) & numpy.isfinite(y_loc) & (y_loc > 0.0)
        x_loc = x_loc[mask]
        y_loc = y_loc[mask]
        if len(x_loc) == 0 or len(y_loc) == 0:
            continue
        x_min = x_loc.min()
        x_max = x_loc.max()
        y_min = y_loc.min()
        y_max = y_loc.max()
        if x_min < glob_x_min:
            glob_x_min = x_min
        if x_max > glob_x_max:
            glob_x_max = x_max
        if y_min < glob_y_min:
            glob_y_min = y_min
        plt.scatter(x_loc, y_loc, label=label, color=colour)
        x_log = numpy.log10(x_loc)
        y_log = numpy.log10(y_loc)
        (slope, r, rank, s) = numpy.linalg.lstsq(x_log[:, numpy.newaxis], y_log)
        fit_y = numpy.power(x_loc, slope)
#       (slope, intercept, r, p, err) = stats.linregress(x_log, y_log)
#       fit_y = numpy.power(x_loc, slope) * numpy.power(10.0, intercept)
        plt.plot(x_loc, fit_y, color=colour)
        fits.append([x_max / 10.0, y_max / 10.0, slope, colour])
    for i in xrange(1, len(fits)):
        while any((items[1] / fits[i][1]) < loc_modifier for items in fits[0: i]):
            fits[i][1] /= loc_modifier
    for (lab_x_loc, lab_y_loc, slope, colour) in fits:
        plt.text(lab_x_loc, lab_y_loc, "$\\alpha = %.3G$" % slope, color=colour)
#       plt.text(lab_xloc, lab_yloc, "$\\alpha = %.3G$\n$R^{2} = %.3G$\n$p = %.3G$\ns.e.$= %.3G$" % (slope, numpy.power(r, 2.0), p, err))
    plt.xlabel("$<f_{i}>$")
    plt.ylabel("$\\sigma_{i}$")
#    if all(num > 0.0 for num in [glob_x_min, glob_x_max, glob_y_min]):
#        plt.plot([glob_x_min, glob_x_max],
#                [glob_y_min, (glob_x_max - glob_x_min) + glob_y_min],
#                color="black")
#    if all(num > 1.0 for num in [glob_x_min, glob_x_max, glob_y_min]):
#        plt.plot([glob_x_min, glob_x_max],
#                [glob_y_min, numpy.sqrt((glob_x_max - glob_x_min) + glob_y_min)],
#                color="black", linestyle="dashed")
    plt.legend()
    plt.show()

def internal_external_ratio(internal, external, num_bins=50):
    eta = external / internal
    plt.hist(eta[numpy.isfinite(eta)], bins=num_bins)
    plt.xlabel("$\\eta = \\sigma^{(ext)} / \\sigma^{(int)}$")
    plt.ylabel("$f(\\eta)$")
    plt.show()

