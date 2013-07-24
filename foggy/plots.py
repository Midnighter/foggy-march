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


import numpy
import matplotlib.pyplot as plt

from itertools import izip

from scipy.optimize import curve_fit


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
    for ((x_loc, y_loc), label, colour) in izip(data, labels, BREWER_SET1):
        mask = numpy.isfinite(x_loc) & (x_loc > 0.0) & numpy.isfinite(y_loc) & (y_loc > 0.0)
        x_loc = x_loc[mask]
        y_loc = y_loc[mask]
        if len(x_loc) == 0 or len(y_loc) == 0:
            continue
        plt.scatter(x_loc, y_loc, label=label, color=colour)
    plt.xlabel("$<f_{i}>$")
    plt.ylabel("$\\sigma_{i}$")
    plt.xscale("log")
    plt.yscale("log")
    plt.legend(loc="upper left")
    plt.show()

def _continuous_power_law(x, k, alpha, c):
    return k * numpy.power(x, alpha) + c

def fluctuation_scaling_fit(data, labels):
    glob_x_max = -numpy.inf
    glob_y_max = -numpy.inf
    fits = list()
    for ((x_loc, y_loc), label, colour) in izip(data, labels, BREWER_SET1):
        mask = numpy.isfinite(x_loc) & (x_loc > 0.0) & numpy.isfinite(y_loc) & (y_loc > 0.0)
        x_loc = x_loc[mask]
        y_loc = y_loc[mask]
        if len(x_loc) == 0 or len(y_loc) == 0:
            continue
        x_max = x_loc.max()
        y_max = y_loc.max()
        if x_max > glob_x_max:
            glob_x_max = x_max
        if y_max > glob_y_max:
            glob_y_max = y_max
        plt.scatter(x_loc, y_loc, label=label, color=colour)
        try:
            (popt, pcov) = curve_fit(_continuous_power_law, x_loc, y_loc)
            fit_y = numpy.power(x_loc, popt[1])
#       (slope, intercept, r, p, err) = stats.linregress(x_log, y_log)
#       fit_y = numpy.power(x_loc, slope) * numpy.power(10.0, intercept)
            plt.plot(x_loc, fit_y, color=colour)
            fits.append([popt[1], colour])
        except RuntimeError:
            continue
    for (i, (slope, colour)) in enumerate(fits):
        # need to make text right justified
        plt.text(numpy.power(glob_x_max, 0.7),
                numpy.power(glob_y_max, 0.1 * float(i + 1)),
                "$\\alpha = %.3G$" % slope, color=colour)
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
    plt.xscale("log")
    plt.yscale("log")
    plt.legend(loc="upper left")
    plt.show()

def internal_external_ratio(internal, external, num_bins=50):
    eta = external / internal
    plt.hist(eta[numpy.isfinite(eta)], bins=num_bins)
    plt.xlabel("$\\eta = \\sigma^{(ext)} / \\sigma^{(int)}$")
    plt.ylabel("$f(\\eta)$")
    plt.show()

