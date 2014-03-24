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
        "correlation", "histogram"]


import numpy
import scipy.stats
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
    for ((x_loc, y_loc), label, colour) in izip(data, labels, BREWER_SET1):
        mask = numpy.isfinite(x_loc) & (x_loc > 0.0) & numpy.isfinite(y_loc) & (y_loc > 0.0)
        x_loc = x_loc[mask]
        y_loc = y_loc[mask]
        if len(x_loc) == 0 or len(y_loc) == 0:
            continue
        try:
            (popt, pcov) = curve_fit(_continuous_power_law, x_loc, y_loc)
            fit_y = numpy.power(x_loc, popt[1])
#            fit_y *= popt[0] # can cause OverflowError
#       (slope, intercept, r, p, err) = stats.linregress(x_log, y_log)
#       fit_y = numpy.power(x_loc, slope) * numpy.power(10.0, intercept)
            plt.plot(x_loc, fit_y, color=colour)
        except RuntimeError:
            plt.scatter(x_loc, y_loc, label=label, color=colour)
        else:
            plt.scatter(x_loc, y_loc, label="%s $\\alpha = %.3G \\pm %.3G$" % (label,
                popt[1], numpy.sqrt(pcov[1, 1])), color=colour)
#       plt.text(lab_xloc, lab_yloc, "$\\alpha = %.3G$\n$R^{2} = %.3G$\n$p = %.3G$\ns.e.$= %.3G$" % (slope, numpy.power(r, 2.0), p, err))
    plt.xlabel("$<f_{i}>$")
    plt.ylabel("$\\sigma_{i}$")
    plt.xscale("log")
    plt.yscale("log")
    plt.legend(loc="upper left")
    plt.show()

def correlation(x, y, x_lbl="Degree $k$", y_lbl="$\\eta$"):
    mask = numpy.isfinite(x) & numpy.isfinite(y)
    x = x[mask]
    y = y[mask]
    pearson = scipy.stats.pearsonr(x, y)
    spearman = scipy.stats.spearmanr(x, y)
    fig = plt.figure()
    plt.plot(x, y, "x", label="$r=%.3g$\n$p=%.3g$\n$\\rho=%.3g$\n$p=%.3g$" % (pearson[0], pearson[1], spearman[0], spearman[1]))
    plt.xlabel(x_lbl)
    plt.ylabel(y_lbl)
    plt.legend(loc="best")
    return fig

def histogram(x, x_lbl="Speed $v$", y_lbl="$f(v)$", num_bins=100):
    mask = numpy.isfinite(x)
    if not mask.any():
        return
    x = x[mask]
    plt.hist(x, bins=num_bins)
    plt.xlabel(x_lbl)
    plt.ylabel(y_lbl)
    plt.show()

