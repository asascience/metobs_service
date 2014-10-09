"""
Plotting tools for USACE FRF Oceanographic data
"""

import numpy as np
import prettyplotlib as ppl
from prettyplotlib import plt
from windrose import WindroseAxes


axis_font_default = {'fontname': 'Arial',
                     'size': '14',
                     'color': 'black',
                     'weight': 'normal',
                     'verticalalignment': 'bottom'}

title_font_default = {'fontname': 'Arial',
                      'size': '18',
                      'color': 'black',
                      'weight': 'bold',
                      'verticalalignment': 'bottom'}


class OceanPlots(object):

    def get_log_tick_labels(self, leftlim, rightlim):
        tick_num = []
        tick_lab = []
        eps = np.spacing(1)
        tol = np.floor(np.log10(leftlim))
        factors = 10 ** (np.fix(-tol))
        tick_num.append(np.round(leftlim * factors) / factors)
        tickindex = 0
        tick_lab.append(str(leftlim))
        while tick_num[tickindex] < rightlim:
            while (((10 ** (tol+1)) - tick_num[tickindex]) > eps) and (tick_num[tickindex] < rightlim):
    #             tick_lab += '| '
                tickindex += 1
                tick_num.append(tick_num[-1] + 10 ** tol)
                if (((10 ** (tol + 1)) - tick_num[tickindex]) < eps):
                    tick_lab.append(str(tick_num[tickindex]))
                else:
                    tick_lab.append('')
            tol += 1
        tick_num[-1] = rightlim
        tick_num[0] = leftlim
        tick_lab[-1] = str(rightlim)
        return tick_lab, tick_num

    def plot_time_series(self, fig, ax, x, y, title='', ylabel='',
                         title_font={}, axis_font={}, **kwargs):

        if not title_font:
            title_font = title_font_default
        if not axis_font:
            axis_font = axis_font_default

        ppl.plot(ax, x, y, **kwargs)
        if ylabel:
            ax.set_ylabel(ylabel, **axis_font)
        if title:
            ax.set_title(title, **title_font)
        if 'degree' in ylabel:
            ax.set_ylim([0, 360])
        fig.autofmt_xdate()
        ax.grid(True)

    def plot_stacked_time_series(self, fig, ax, x, y, z, title='', ylabel='',
                                 cbar_title='', title_font={}, axis_font={},
                                 **kwargs):

        if not title_font:
            title_font = title_font_default
        if not axis_font:
            axis_font = axis_font_default
        z = np.ma.array(z, mask=np.isnan(z))
        h = plt.pcolormesh(x, y, z, **kwargs)
        if ylabel:
            ax.set_ylabel(ylabel, **axis_font)
        if title:
            ax.set_title(title, **title_font)
        plt.axis([x.min(), x.max(), y.min(), y.max()])
        ax.xaxis_date()
        fig.autofmt_xdate()
        ax.invert_yaxis()
        cbar = plt.colorbar(h)
        if cbar_title:
            cbar.ax.set_ylabel(cbar_title)
        ax.grid(True)

    def plot_profile(self, ax, x, y, xlabel='', ylabel='',
                     axis_font={}, **kwargs):

        if not axis_font:
            axis_font = axis_font_default

        ppl.plot(ax, x, y, **kwargs)
        if xlabel:
            ax.set_xlabel(xlabel, **axis_font)
        if ylabel:
            ax.set_ylabel(ylabel, **axis_font)
        ax.invert_yaxis()
        ax.xaxis.set_label_position('top')  # this moves the label to the top
        ax.xaxis.set_ticks_position('top')
        ax.grid(True)
        # ax.set_title(title, **title_font)

    def plot_histogram(self, ax, x, bins, title='', xlabel='', title_font={},
                       axis_font={}, **kwargs):

        if not title_font:
            title_font = title_font_default
        if not axis_font:
            axis_font = axis_font_default
        x = x[~np.isnan(x)]
        ppl.hist(ax, x, bins, **kwargs)
        if xlabel:
            ax.set_xlabel(xlabel, labelpad=10, **axis_font)
        ax.set_ylabel('No. of Occurrences', **axis_font)
        ax.set_title(title, **title_font)
        ax.grid(True)

    def plot_scatter(self, fig, ax, x, y, title='', xlabel='', ylabel='',
                     title_font={}, axis_font={}, **kwargs):

        if not title_font:
            title_font = title_font_default
        if not axis_font:
            axis_font = axis_font_default

        ppl.scatter(ax, x, y, **kwargs)
        if xlabel:
            ax.set_xlabel(xlabel, labelpad=10, **axis_font)
        if ylabel:
            ax.set_ylabel(ylabel, labelpad=10, **axis_font)
        ax.set_title(title, **title_font)
        ax.grid(True)

    #A quick way to create new windrose axes...
    def new_axes(self):
        fig = plt.figure(figsize=(8, 8), dpi=80, facecolor='w', edgecolor='w')
        rect = [0.1, 0.1, 0.8, 0.8]
        ax = WindroseAxes(fig, rect, axisbg='w')
        fig.add_axes(ax)
        return fig, ax

    def set_legend(self, ax, label=''):
        """Adjust the legend box."""
        l = ax.legend(title=label)
        plt.setp(l.get_texts(), fontsize=8)

    def plot_rose(self, magnitude, direction, bins=15, nsector=16,
                  title='', title_font={}, legend_title='', normed=True,
                  opening=0.8, edgecolor='white'):

        if not title_font:
            title_font = title_font_default

        fig, ax = self.new_axes()
        ax.bar(direction, magnitude, bins=bins, normed=normed,
               opening=opening, edgecolor=edgecolor, nsector=nsector)

        self.set_legend(ax, legend_title)
        ax.set_title(title, **title_font)
        return fig

    def plot_1d_quiver(self, fig, ax, time, u, v, title='', ylabel='',
                       title_font={}, axis_font={},
                       legend_title="Current magnitude [m/s]", **kwargs):

        if not title_font:
            title_font = title_font_default
        if not axis_font:
            axis_font = axis_font_default
        # Plot quiver
        magnitude = (u**2 + v**2)**0.5
        maxmag = max(magnitude)
        ax.set_ylim(-maxmag, maxmag)
        dx = time[-1] - time[0]
        ax.set_xlim(time[0] - 0.05 * dx, time[-1] + 0.05 * dx)
        ax.fill_between(time, magnitude, 0, color='k', alpha=0.1)

        # Fake 'box' to be able to insert a legend for 'Magnitude'
        p = ax.add_patch(plt.Rectangle((1, 1), 1, 1, fc='k', alpha=0.1))
        leg1 = ax.legend([p], [legend_title], loc='lower right')
        leg1._drawFrame = False

        # # 1D Quiver plot
        q = ax.quiver(time, 0, u, v, **kwargs)
        plt.quiverkey(q, 0.2, 0.05, 0.2,
                      r'$0.2 \frac{m}{s}$',
                      labelpos='W',
                      fontproperties={'weight': 'bold'})

        ax.xaxis_date()
        fig.autofmt_xdate()

        if ylabel:
            ax.set_ylabel(ylabel, labelpad=20, **axis_font)
        ax.set_title(title, **title_font)

    def plot_2d_wave_spectrum_contour(self, ax, freq, deg, spectrum,
                                      title='Contour 2D Spectrum',
                                      title_font={},
                                      cbar_title='',
                                      axis_font={}, log=True, **kwargs):

        if not title_font:
            title_font = title_font_default
        if not axis_font:
            axis_font = axis_font_default
        if not cbar_title:
            cbar_title = ('LOG' + r'$_{10}$' +
                          ' Energy Density (m' + r'$^2$' + '/Hz/Deg)')
        contour_levels = np.log10(spectrum)
        if len(set(contour_levels.flat)) < 7:
            nlines = len(set(contour_levels.flat))
        else:
            nlines = 12
        # nlines = len(set(contour_levels.flat)) if len(set(contour_levels.flat)) < 7 else 12

        cmap = plt.cm.jet
        h = plt.contourf(freq, deg, contour_levels, nlines, cmap=cmap)
        cbar = plt.colorbar(h, orientation='horizontal', aspect=30, shrink=0.8)

        cbar.solids.set_edgecolor("face")
        for line in cbar.lines:
            line.set_linewidth(3)
        if cbar_title:
            cbar.ax.set_xlabel(cbar_title)

        ax.set_ylabel('Direction (deg)', **axis_font)
        ax.set_ylim([0, 360])
        ax.set_xlabel('Frequency (Hz)', **axis_font)
        ax.set_title(title, **title_font)
        if log:
            ax.set_xscale('log')
            ticklab, ticknum = self.get_log_tick_labels(freq.min(), freq.max())
            ax.set_xticks(ticknum)
            ax.set_xticklabels(ticklab)

    def plot_2d_wave_spectrum_polar(self, freq, deg, spectrum,
                                    title='Polar 2D Spectrum', title_font={},
                                    cbar_title=''):

        if not title_font:
            title_font = title_font_default
        if not cbar_title:
            cbar_title = ('LOG' + r'$_{10}$' +
                          ' Energy Density (m' + r'$^2$' + '/Hz/Deg)')

        fig, ax = plt.subplots(figsize=(12, 8), subplot_kw=dict(projection='polar'))

        ax.set_theta_zero_location("N")
        ax.set_theta_direction(-1)
        theta_angles = np.arange(0, 360, 45)
        theta_labels = ['N', 'N-E', 'E', 'S-E', 'S', 'S-W', 'W', 'N-W']
        ax.set_thetagrids(angles=theta_angles, labels=theta_labels)

        spectrum = np.log10(spectrum)
        # radius is log of freq
        if max(freq) < 0:
            ymin = np.log10(0.05)
            zeniths = freq - ymin
        else:
            ymin = 0.0
            zeniths = freq

        # Add angles to wrap contours around 360 deg
        deg = np.append(deg[0]-(deg[-1]-deg[-2])/2.0, deg)
        # deg = np.append(0, deg)
        deg = np.append(deg, deg[-1]+(deg[-1]-deg[-2])/2.0)

        if max(deg) < 7.0:  # Radians
            azimuths = deg
        else:
            azimuths = np.radians(deg)

        theta, r = np.meshgrid(azimuths, zeniths)

        # Add 2 columns to spectrum now
        new_col = np.array((spectrum[:, 0] + spectrum[:, -1]) / 2.0)
        z = np.concatenate((np.mat(new_col).T, spectrum), axis=1)
        z = np.concatenate((z, np.mat(new_col).T), axis=1)

        contour_levels = np.log10(z)
        nlevels = len((contour_levels)) if len((contour_levels)) < 7 else 12
        values = np.array(z)
        h = plt.contourf(theta, r, values, nlevels)
        ax.set_title(title, **title_font)

        cbar = plt.colorbar(h, orientation='horizontal',
                            aspect=20, shrink=0.45)
        if cbar_title:
            cbar.ax.set_xlabel(cbar_title)

        return fig

    def plot_spectrograph(self, fig, ax, time, freq, spectrum,
                          ylabel='Period (s)',
                          title='Wave Energy Spectrograph',
                          cbar_title='',
                          title_font={}, axis_font={}, **kwargs):

        if not title_font:
            title_font = title_font_default
        if not axis_font:
            axis_font = axis_font_default
        if not cbar_title:
            cbar_title = 'LOG' + r'$_{10}$' + ' (m' + r'$^2$' + '/Hz)'

        h = plt.pcolormesh(time, freq, np.log10(spectrum))

        ax.set_ylabel(ylabel, **axis_font)
        ax.set_title(title, **title_font)
        # plt.axis([time.min(), time.max(), freq.min(), freq.max()])

        ax.xaxis_date()
        fig.autofmt_xdate()
        ax.set_xlim([time.min(), time.max()])
        ax.set_ylim([freq.min(), freq.max()])

        labels = ax.get_yticks().tolist()
        new_labels = []
        for label in labels:
            if float(label) > 0:
                new_labels.append(str(np.floor( 1/float(label) * 10 )/10))
            else:
                new_labels.append('')
        ax.set_yticklabels(new_labels)
        cbar = plt.colorbar(h, orientation='horizontal',
                            aspect=20, shrink=0.85, pad=0.2)
        if cbar_title:
            cbar.ax.set_xlabel(cbar_title)

    def plot_frequency_spectrum(self, ax, freq, spectrum_1d,
                                title='Frequency Spectrum', title_font={},
                                axis_font={}, log=False, **kwargs):

        if not title_font:
            title_font = title_font_default
        if not axis_font:
            axis_font = axis_font_default

        if log:
            plt.loglog(freq, spectrum_1d, basex=10, basey=10, **kwargs)
            ax.set_xlim([freq.min(), freq.max()])
            ticklab, ticknum = self.get_log_tick_labels(freq.min(), freq.max())
            ax.set_xticks(ticknum)
            ax.set_xticklabels(ticklab)
        else:
            ppl.plot(ax, freq, spectrum_1d, **kwargs)
            ax.set_xlim([freq.min(), freq.max()])
            # ppl.fill_between(ax, freq, spectrum_1d, **kwargs)

        # # Now plot the Pierson Moskowitz spectra
        # alpha = 0.0081
        # beta = -0.74
        # g = 9.81
        # wo = -g/

        ax.grid(True)
        ax.set_xlabel('Frequency (Hz)', **axis_font)
        ax.set_ylabel('Wave Energy (' + r'$m^2$' + '/Hz)', **axis_font)
        ax.set_title(title, **title_font)

    def plot_2d_wave_spectrum_cartesian(self, ax, freq, deg, spectrum,
                                        title='Cartesian 2D Spectrum',
                                        title_font={}, axis_font={}, **kwargs):

        if not title_font:
            title_font = title_font_default
        if not axis_font:
            axis_font = axis_font_default

        X, Y = np.meshgrid(freq, deg)
        if np.shape(X) != np.shape(spectrum):
            spectrum = spectrum.T
            if np.shape(X) != np.shape(spectrum):
                raise Exception('Dimension mismatch!')
        ax.plot_surface(X, Y, spectrum, cmap=plt.cm.jet, rstride=1, cstride=1,
                        linewidth=0, antialiased=False)
        ax.set_ylim([0, 360])
        ax.set_ylabel('Direction (deg)', **axis_font)
        ax.set_xlim([freq.min(), freq.max()])
        ax.set_xlabel('Frequency (Hz)', **axis_font)
        ax.set_zlabel('Energy Density (m' + r'$^2$' + '/Hz/deg)', **axis_font)
        ax.set_title(title, **title_font)

    def make_patch_spines_invisible(self, ax):
        ax.set_frame_on(True)
        ax.patch.set_visible(False)
        for sp in ax.spines.itervalues():
            sp.set_visible(False)

    def set_spine_direction(self, ax, direction):
        if direction in ["right", "left"]:
            ax.yaxis.set_ticks_position(direction)
            ax.yaxis.set_label_position(direction)
        elif direction in ["top", "bottom"]:
            ax.xaxis.set_ticks_position(direction)
            ax.xaxis.set_label_position(direction)
        else:
            raise ValueError("Unknown Direction: %s" % (direction,))

        ax.spines[direction].set_visible(True)

    def plot_4_xaxes(self, ax, xdata, ydata, colors, ylabel='Depth (m)',
                     axis_font={}, **kwargs):
        # Acknowledgment: This program is based on code written by Jae-Joon Lee,
        # URL= http://matplotlib.svn.sourceforge.net/viewvc/matplotlib/trunk/matplotlib/
        # examples/pylab_examples/multiple_yaxis_with_spines.py?revision=7908&view=markup
        if not axis_font:
            axis_font = axis_font_default

        n_vars = len(xdata)
        if n_vars > 4:
            raise Exception('This code currently handles a maximum of four independent variables.')

        spine_directions = ["top", "bottom", "bottom", "top"]

        # Generate the plot.
        # Use twiny() to create extra axes for all dependent variables except the first
        # (we get the first as part of the ax axes).
        x_axis = n_vars * [0]
        x_axis[0] = ax
        for i in range(1, n_vars):
            x_axis[i] = ax.twiny()

        ax.spines["top"].set_visible(False)
        self.make_patch_spines_invisible(x_axis[1])
        self.set_spine_direction(x_axis[1], "top")

        if n_vars >= 3:
           # The following statement positions the third y-axis to the right of the
           # frame, with the space between the frame and the axis controlled by the
           # numerical argument to set_position; this value should be between 1.10 and
           # 1.2.
            x_axis[2].spines["top"].set_position(("axes", 1.15))
            self.make_patch_spines_invisible(x_axis[2])
            self.set_spine_direction(x_axis[2], "top")
            plt.subplots_adjust(bottom=0.0, top=0.8)

        if n_vars >= 4:
            # The following statement positions the fourth y-axis to the left of the
            # frame, with the space between the frame and the axis controlled by the
            # numerical argument to set_position; this value should be between 1.10 and
            # 1.2.
            x_axis[3].spines["bottom"].set_position(("axes", -0.15))
            self.make_patch_spines_invisible(x_axis[3])
            self.set_spine_direction(x_axis[3], "bottom")
            plt.subplots_adjust(bottom=0.2, top=0.8)

        p = n_vars * [0]
        # Plot the curves:
        for ind, key in enumerate(xdata):
            p[ind], = x_axis[ind].plot(xdata[key], ydata, colors[ind], **kwargs)

        # Label the y-axis:
        ax.set_ylabel(ylabel,  **axis_font)
        for ind, key in enumerate(xdata):

            # Label the x-axis and set text color:
            x_axis[ind].set_xlabel(key, **axis_font)
            x_axis[ind].xaxis.label.set_color(colors[ind])
            x_axis[ind].spines[spine_directions[ind]].set_color(colors[ind])

            for obj in x_axis[ind].xaxis.get_ticklines():
                # `obj` is a matplotlib.lines.Line2D instance
                obj.set_color(colors[ind])
                obj.set_markeredgewidth(2)

            for obj in x_axis[ind].xaxis.get_ticklabels():
                obj.set_color(colors[ind])
                obj.set_size(12)
                obj.set_weight(600)

        ax.invert_yaxis()
        ax.grid(True)
