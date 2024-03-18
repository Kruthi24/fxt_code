#lc_lmfit.py

import numpy as np
import swift_scrape
import os
import lmfit as lm
import scipy as sp
import emcee
import math
import pandas as pd


def get_individual_curves_log(filename,unpack=True):
    """ Extract light curve from .txt file
        obtained using swift_scrape.py   
    Args:
        filename : path+name
    Returns:
        tuple : (time,time_perr,time_nerr,flux,flux_perr,flux_nerr). Here 
                time_perr = time_upper_limit - time; 
                time_nerr = time - time_lower_limit.
    """
    time,time_high,time_low, flux, flux_high,flux_low = np.genfromtxt(filename, delimiter='\t', unpack=unpack, skip_header=1)
    return time,time_high,time_low,flux,flux_high,flux_low

def get_y(res, n, x):
    '''
    Pass the result object from lmfit
    '''
    bfit = res.params
    tbreaks = [bfit["tb"+str(i)].value for i in range(n-1)]
    alphas = [bfit["alpha_"+str(i)].value for i in range(n)]
    y = nbroken_law(x,tbreaks, alphas, bfit["amplitude"].value)
    return y


def power_law(x,alpha_1,amplitude):
    '''
    Calculate the power law function.
    '''
    return amplitude * x ** (-alpha_1)

def broken_power_law(x,t_break,alpha_1,alpha_2,amplitude):
    '''
    Calculate the broken power law function.
    '''
    alpha = np.where(x< t_break, alpha_1, alpha_2)
    tt = x / t_break
    return amplitude * tt ** (-alpha)

def double_broken_law(x, tb0, tb1, alpha_0, alpha_1, alpha_2, amplitude):
    '''
    Calculate the double broken power law function.
    '''
    x0 = x[np.where(x<tb0)]
    x1 = x[np.where((x>tb0)&(x<tb1))]
    x2 = x[np.where(x>tb1)]
    x0 = (x0/tb0)**(-alpha_0)
    x1 = (x1/tb0)**(-alpha_1)
    x2 = (tb1/tb0)**(-alpha_1)*(x2/tb1)**(-alpha_2)
    x_return = np.concatenate((x0, x1, x2))
    return amplitude * x_return

def triple_broken_law(x, tb0, tb1, tb2, alpha_0, alpha_1, alpha_2, alpha_3, amplitude):
    '''
    Calculate the triple broken power law function.
    '''
    x0 = x[np.where(x<tb0)]
    x1 = x[np.where((x>tb0)&(x<tb1))]
    x2 = x[np.where((x>tb1)&(x<tb2))]
    x3 = x[np.where(x>tb2)]
    x0 = (x0/tb0)**(-alpha_0)
    x1 = (x1/tb0)**(-alpha_1)
    x2 = (tb1/tb0)**(-alpha_1)*(x2/tb1)**(-alpha_2)
    x3 = (tb1/tb0)**(-alpha_1)*(tb2/tb1)**(-alpha_2)*(x3/tb2)**(-alpha_3)
    x_return = np.concatenate((x0, x1, x2, x3))
    return amplitude * x_return

def nbroken_law(x, breaks, alphas, amplitude):
    '''
    Calculate the n-broken power law function.
    '''
    breaks.append(np.max(x))
    n_seg = len(alphas)
    x_seg = x[np.where(x<=breaks[0])]**(-alphas[0])
    scaling_factors = 1
    for i in range(1,n_seg):
        x_chunk = x[np.where((x>=breaks[i-1])&(x<=breaks[i]))]
        scaling_factors = scaling_factors * breaks[i-1]**(alphas[i]-alphas[i-1])
        x_seg = np.append(x_seg,scaling_factors * x_chunk**(-alphas[i]))
    return amplitude * (breaks[0])**(alphas[0]) * x_seg


def lnlikehood(x, y, yerr, theta,BPL):
    '''
    Calculate the log-likelihood of the data given the model parameters.
    '''
    yerr=np.array(yerr)
    if(BPL==True):
        t_break,alpha_1,alpha_2,amplitude = theta
        model = broken_power_law(x,t_break,alpha_1,alpha_2,amplitude)
    else:
        alpha_1,amplitude = theta
        model = power_law(x,alpha_1,amplitude)
    return -0.5*(np.sum((y-model)**2/(yerr**2) + np.log(np.sqrt(yerr**2)*2*np.pi)))

def information_criteria(ln_like,y,theta):
    '''
    Calculate the AIC, BIC, and degrees of freedom.
    '''
    AIC=-2*ln_like+(2*len(theta))+(2*len(theta)*len(theta))
    BIC=-2*ln_like+(len(theta)*np.log(len(y)))
    dof=len(y)-len(theta)
    return AIC,BIC,dof

def lnlike(theta, x, y, yerr):
    '''
    Calculate the log-likelihood of the data given the model parameters.
    '''
    t_break,alpha_1,alpha_2,amplitude = theta
    model = broken_power_law(x,t_break,alpha_1,alpha_2,amplitude)
    inv_sigma2 = 1.0/(yerr**2)
    return -0.5*(np.sum((y-model)**2*inv_sigma2 - np.log(inv_sigma2)))

def lnprior(theta):
    '''
    Calculate the log-prior of the model parameters.
    '''
    t_break,alpha_1,alpha_2,amplitude = theta
    if 1e1<t_break<1e4 and -1.0<alpha_1<0.2 and 0.0<alpha_2<4.0 and 1e-15<amplitude<1e-11:
        return 0.0
    return -np.inf

def lnprob(theta, x, y, yerr):
    '''
    Calculate the log-posterior of the model parameters.
    '''
    lp = lnprior(theta)
    if not np.isfinite(lp):
        return -np.inf
    return lp + lnlike(theta, x, y, yerr)


#objective functions
def cost_func_pl(params,x,y,x_err,y_err, orth=False):
    '''
    Calculate the cost function for the power law model.
    '''
    v = params.valuesdict()
    y_model = power_law(x,v["alpha_1"],v["amplitude"])
    if orth == True:
        cost_fn = (y_model - y)/y_err + 1/x_err
    cost_fn = (y_model - y)/y_err
    return cost_fn

def cost_func_bpl(params,x,y,x_err,y_err, orth=False):
    '''
    Calculate the cost function for the broken power law model.
    '''
    v = params.valuesdict()
    y_model = broken_power_law(x,v["t_break"],v["alpha_1"],v["alpha_2"],v["amplitude"])
    if orth == True:
        cost_fn = (y_model - y)/y_err + 1/x_err
    cost_fn = (y_model - y)/y_err
    return cost_fn

def cost_func_dbl(params, x, y, x_err, y_err, orth=False):
    '''
    Calculate the cost function for the double broken power law model.
    '''
    v = params.valuesdict()
    y_model = double_broken_law(x,v["tb0"],v["tb1"],v["alpha_0"],v["alpha_1"],v["alpha_2"],v["amplitude"])
    if orth == True:
        cost_fn = (y_model - y)/y_err + 1/x_err
    cost_fn = (y_model - y)/y_err
    return cost_fn

def cost_func_nbpl(params, x, y, x_err, y_err, n, orth=False):
    '''
    Calculate the cost function for the n-broken power law model.
    '''
    v = params.valuesdict()
    tbreaks = [v["tb"+str(i)] for i in range(n-1)]
    alphas = [v["alpha_"+str(i)] for i in range(n)]
    y_model = nbroken_law(x,tbreaks, alphas,v["amplitude"])
    if orth == True:
        cost_fn = (y_model - y)/y_err + 1/x_err
    cost_fn = (y_model - y)/y_err
    return cost_fn