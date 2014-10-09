# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <markdowncell>

# ### This notebook retrieves wave spectra and stats from the thredds server and generates plots

# <markdowncell>

# #### import libraries

# <codecell>

import os
import os.path
import netCDF4
from netCDF4 import num2date, date2num
from netcdftime import utime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import rcParams
from mpl_toolkits.mplot3d import Axes3D
import datetime as dt
import folium
import numpy as np
import prettyplotlib as ppl
from ocean_plot_tools import OceanPlots

%matplotlib inline
rcParams['xtick.direction'] = 'out'
rcParams['ytick.direction'] = 'out'

# Create instance of OceanPlots class
ocean_plots = OceanPlots()

# <markdowncell>

# ### Get the spectra data

# <codecell>

# Get the URL of the file on the thredds server
url = 'http://10.90.71.208:9000/thredds/dodsC/frfData/waves/awac/awac03/2013/awac_03_201302_spec.nc'
nc = netCDF4.Dataset(url, 'r')
print nc
nc_time = nc.variables['time']
freq = nc.variables['waveFrequency'][:]
deg = nc.variables['waveDirectionBins'][:]
spectra_2d = nc.variables['directionalWaveEnergyDensity']
spectra_1d = nc.variables['waveEnergyDensity']

dates = num2date(nc_time[:], units=nc_time.units)
noutcdates = []
for date in dates:
    noutcdates.append(date.replace(tzinfo=None))

# <codecell>

# Set the font dictionaries (for plot title and axis titles)
title_font = {'fontname':'Arial', 
              'size':'18', 
              'color':'black', 
              'weight':'bold',
              'verticalalignment':'bottom'} # Bottom vertical alignment for more space
axis_font = {'fontname':'Arial', 
             'size':'14'}

# <markdowncell>

# #### Plot 2d Spectra

# <codecell>

for record_num in range(5):
    fig, ax = plt.subplots(figsize=(12,12))
    spectrum = np.array(spectra_2d[record_num,:,:]).transpose()
    date_str = dates[record_num].strftime("%Y-%m-%d %H:%M")
    ocean_plots.plot_2d_wave_spectrum_contour(ax, freq, deg, spectrum,
                                  title='Contour 2D Spectrum\n' + date_str)

# <markdowncell>

# #### Plot 1D frequency spectrum

# <codecell>

for record_num in range(5):
    fig, ax = plt.subplots(figsize=(12, 6))
    spec1d = np.array(spectra_1d[record_num]).transpose()
    kwargs = dict(linewidth=2.0, color='b')
    date_str = dates[record_num].strftime("%Y-%m-%d %H:%M")
    ocean_plots.plot_frequency_spectrum(ax, freq, spec1d, log=True, 
                                        title='Frequency Spectrum\n' + date_str, 
                                        **kwargs)

# <markdowncell>

# #### Plot 2d wave spectrum in polar coordinates

# <codecell>

# fig, ax = plt.subplots(figsize=(12, 6), subplot_kw=dict(projection='polar'))
for record_num in range(5):
    spectrum = spectra_2d[record_num,:,:]
    date_str = dates[record_num].strftime("%Y-%m-%d %H:%M")
    ocean_plots.plot_2d_wave_spectrum_polar(freq, deg, spectrum,
                                            title='Polar 2D Spectrum\n' + date_str)

# <markdowncell>

# #### Plot Cartesian

# <codecell>

for record_num in range(5):
    fig, ax = plt.subplots(figsize=(12, 10), subplot_kw=dict(projection='3d'))
    date_str = dates[record_num].strftime("%Y-%m-%d %H:%M")
    ocean_plots.plot_2d_wave_spectrum_cartesian(ax, freq, deg, spectra_2d[record_num,:,:].T,
                                                title='Cartesian 2D Spectrum\n' + date_str)

# <markdowncell>

# #### Plot spectrograph

# <codecell>

# Now plot the spectrograph
spec1d = np.array(spectra_1d).transpose()
fig, ax = plt.subplots(figsize=(12, 6))
time = mdates.date2num(dates)
ocean_plots.plot_spectrograph(fig, ax, time, freq, spec1d)

# <markdowncell>

# ### Get the stats data

# <codecell>

# Get the URL of the file on the thredds server
url = 'http://localhost:9000/thredds/dodsC/frfData/waves/awac/awac03/2013/awac_03_201302_stats.nc'
# url = '/Users/bobfratantonio/Documents/Dev/code/usace-fdif-data/FRF/waves/waveriders/wr430/2010/waverdr_430_201001_stats.nc'
nc = netCDF4.Dataset(url, 'r')
print nc
nc_time = nc.variables['time']
hs = nc.variables['waveHs'][:]
fp = nc.variables['waveFp'][:]
dp = nc.variables['waveDp'][:]

dates = num2date(nc_time[:], units=nc_time.units)
noutcdates = []
for date in dates:
    noutcdates.append(date.replace(tzinfo=None))

# <markdowncell>

# #### Plot stats

# <codecell>

# Plot Hs
fig, ax = ppl.subplots(figsize=(12, 6))
kwargs = dict(linewidth=2.0, color='b')
ocean_plots.plot_time_series(fig, ax, noutcdates, hs, 
                             title='Significant Wave Height', 
                             ylabel='Hs (m)',
                             **kwargs)

# Plot Tp
fig, ax = ppl.subplots(figsize=(12, 6))
kwargs = dict(linewidth=2.0, color='r')
ocean_plots.plot_time_series(fig, ax, noutcdates, 1/fp, 
                             title='Peak Period', 
                             ylabel='Tp (s)',
                             **kwargs)

# Plot Dp 
fig, ax = ppl.subplots(figsize=(12, 6))
kwargs = dict(linewidth=2.0, color='g')
ocean_plots.plot_time_series(fig, ax, noutcdates, dp, 
                             title='Peak Wave Direction', 
                             ylabel='Dp (deg)',
                             **kwargs)

# <markdowncell>

# #### Plot Hs Tp Scatter

# <codecell>

fig, ax = ppl.subplots(figsize=(8, 8))
x = hs
y = 1.0/fp
kwargs = dict(color='r', marker='o', s=40)
ocean_plots.plot_scatter(fig, ax, x, y, 
                         title='Height Period Scatter', 
                         ylabel='Wave Period (s)', 
                         xlabel='Wave Height (m)', 
                         **kwargs)

# <markdowncell>

# #### Plot wave height rose

# <codecell>

ocean_plots.plot_rose(hs, dp, bins=5, nsector=16, 
                      title=' Wave Height Rose', 
                      legend_title='Hm0 (m)')

# <markdowncell>

# #### Plot histograms

# <codecell>

fig, ax = ppl.subplots(3, 1, figsize=(12, 18))

x = dp
# the histogram of the data
kwargs = dict(normed=0, facecolor='g', alpha=0.85)
ocean_plots.plot_histogram(ax[0], x, bins=20, 
                           title='Wave Direction Histogram', 
                           xlabel= 'Direction (deg)', 
                           **kwargs)

x = hs
# the histogram of the data
kwargs = dict(normed=0, facecolor='b', alpha=0.85)
ocean_plots.plot_histogram(ax[1], x, bins=20, 
                           title='Wave Height Histogram', 
                           xlabel= 'Height (m)', 
                           **kwargs)

x = 1/fp
# the histogram of the data
kwargs = dict(normed=0, facecolor='r', alpha=0.85)
ocean_plots.plot_histogram(ax[2], x, bins=20, 
                           title='Wave Period Histogram', 
                           xlabel= 'Period (s)', 
                           **kwargs)

