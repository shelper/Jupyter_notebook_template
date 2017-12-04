import numpy as np
from math import factorial
# from scipy.signal import savgol_filter, medfilt
# from scipy.signal import savgol_filter

def medfilt(data, window_size):
    if window_size % 2 != 1 or window_size < 1:
        raise TypeError("window_size size must be a positive odd number")
    
    # strided_app(a, L, S ):  # Window len = L, Stride len/stepsize = S
    half_window = (window_size-1) //2
    nrows = data.size - window_size + 1
    n = data.strides[0]
    filted_data = np.lib.stride_tricks.as_strided(data, shape=(nrows,window_size), strides=(n, n))
    filted_data = np.median(filted_data, axis=1)
    firstvals = data[0:half_window]
    lastvals = data[-half_window:]
    filted_data = np.concatenate((firstvals, filted_data, lastvals))
    return filted_data 


def savitzky_golay(y, window_size, order, deriv=0, rate=1):
    """
    Parameters
    ----------
    y : array_like, shape (N,)
        the values of the time history of the signal.
    window_size : int
        the length of the window. Must be an odd integer number.
    order : int
        the order of the polynomial used in the filtering.
        Must be less then `window_size` - 1.
    deriv: int
        the order of the derivative to compute (default = 0 means only smoothing)
    Returns
    -------
    ys : ndarray, shape (N)
        the smoothed signal (or it's n-th derivative).
    """

    if window_size % 2 != 1 or window_size < 1:
        raise TypeError("window_size size must be a positive odd number")
    if window_size < order + 2:
        raise TypeError("window_size is too small for the polynomials order")
    order_range = range(order+1)
    half_window = (window_size -1) // 2
    # precompute coefficients
    b = np.mat([[k**i for i in order_range] for k in range(-half_window, half_window+1)])
    m = np.linalg.pinv(b).A[deriv] * rate**deriv * factorial(deriv)
    # pad the signal at the extremes with
    # values taken from the signal itself
    firstvals = y[0] - np.abs( y[1:half_window+1][::-1] - y[0] )
    lastvals = y[-1] + np.abs(y[-half_window-1:-1][::-1] - y[-1])
    y = np.concatenate((firstvals, y, lastvals))
    return np.convolve(m[::-1], y, mode='valid')


def get_profile(image, spike_size, filt_size, fit_order):
    img_sum = image.sum(axis = 1)
    img_peak = (image > 10).sum(axis = 1)
    # print(image.max(), image.min())
    # image[image < thresh] = 0
    profile = image * np.arange(image.shape[1])
    profile = profile.sum(axis=1)
    profile = profile / img_sum
    profile[img_peak < 5] = np.nan
    # fill in missing points of the profile
    nans = np.isnan(profile)

    if all(nans):
        profile = np.zeros(len(profile))
    else:
        profile[nans]= np.interp(nans.nonzero()[0], (~nans).nonzero()[0], profile[~nans])

    # smooth the profile
    if spike_size: 
        profile = medfilt(profile, spike_size * 2 + 1)
    if filt_size:
        # profile = savgol_filter(profile, filt_size, fit_order)
        profile = savitzky_golay(profile, filt_size, fit_order)
        
    return profile


def find_treads(profile_diff, edge_size,  win_size, max_treads_num, min_tread_width, max_tread_width):
    n_sects = len(profile_diff) // win_size
    idx4mins = []
    idx4maxs = []
    for i in range(len(profile_diff) // win_size):
        s = i * win_size 
        e = (i + 1) * win_size
        idx4mins.append(s + profile_diff[s : e].argmin())
        idx4maxs.append(s + profile_diff[s : e].argmax())
    
    max2pop = []
    for i in range(len(idx4maxs) - 1):
        if idx4maxs[i+1] - idx4maxs[i] < win_size:
            if (profile_diff[idx4maxs[i]] <= profile_diff[idx4maxs[i+1]]) and (i not in max2pop):
                max2pop.append(i)
            elif i+1 not in max2pop:
                max2pop.append(i + 1)
        
    min2pop = []
    for i in range(len(idx4mins) - 1):
        if idx4mins[i+1] - idx4mins[i] < win_size:
            if profile_diff[idx4mins[i]] >= profile_diff[idx4mins[i+1]] and (i not in min2pop):
                min2pop.append(i)
            elif i+1 not in min2pop:
                min2pop.append(i + 1)
        
    for i in reversed(max2pop):
        idx4maxs.pop(i)
    for i in reversed(min2pop):
        idx4mins.pop(i)

    idx4mins = np.array(idx4mins)
    idx4maxs = np.array(idx4maxs)
    edge_starts = np.sort(idx4maxs[profile_diff[idx4maxs].argsort()[-max_treads_num:]])
    edge_ends = np.sort(idx4mins[profile_diff[idx4mins].argsort()[:max_treads_num]])
    treads_edge = [] 
    for start in edge_starts:
        for end in edge_ends:
            if end <= start:
                continue
            if len(treads_edge) == 0:
                treads_edge.append([start, end])
                continue
            else:
                start0, end0 = treads_edge[-1]
                if start == start0:
                    break
                elif end == end0:
                    treads_edge.pop()
                    treads_edge.append([start, end])
                else:
                    treads_edge.append([start, end])

    treads_edge = np.array(treads_edge)
    treads_edge[:, 1] += edge_size 
    treads_width = np.squeeze(np.diff(treads_edge, axis=1))
    treads_edge = treads_edge[(treads_width>min_tread_width) & (treads_width<max_tread_width)]
    return treads_edge


def calibrate_treads(profile, treads_edge, pix_size, edge_expand, baseline, d0, sensor2baseline_offset):
    treads_num = treads_edge.shape[0]
    if treads_num == 0:
       return None 
    else:
        treads = np.zeros((treads_num, np.diff(treads_edge).max() + edge_expand * 2))
        abs_depth = lambda x : - x * d0 / (x - baseline) 
        for i, (s, e) in enumerate(treads_edge):
            # remove the baseline of the tread, baseline is fitted using beginning and ending points
            ss = s - edge_expand
            ee = e + edge_expand
            # print(ss, ee)
            tread = abs_depth(profile[ss:ee] * pix_size + baseline + sensor2baseline_offset)
            # print(len(tread))
            x = np.concatenate((np.arange(edge_expand), np.arange(len(tread) - edge_expand, len(tread))))
            linear_fit_params = np.polyfit(x, tread[x], 1)
            tread -= np.polyval(linear_fit_params, np.arange(len(tread)))
            pad_before = (treads.shape[1] - len(tread)) // 2
            pad_after = treads.shape[1] - len(tread) - pad_before
            treads[i] = np.pad(tread, (pad_before, pad_after), 'constant')

        return treads


def get_treads_score(profile_diff, treads_depth, idx_peaks_dips):
    w1, w2, w3 = 1, -1, -1
    norm_treads_depth = treads_depth / treads_depth.max()
    treads_unflatness = []
    for (idx_peak, idx_dip) in idx_peaks_dips:
        peak, dip = profile_diff[idx_peak], profile_diff[idx_dip]
        sub_peak = max(profile_diff[(idx_peak + idx_dip) // 2: idx_dip + 1])
        sub_dip = min(profile_diff[idx_peak: (idx_peak + idx_dip) // 2 + 1])
        treads_unflatness.append(abs((sub_peak - sub_dip)/(peak-dip)))
    treads_unflatness = np.array(treads_unflatness)
        
    peaks, dips = profile_diff[idx_peaks_dips].T
    peak_dip_mismatch = abs((peaks + dips)/(peaks - dips))
    treads_score = w1 * norm_treads_depth + w2 * treads_unflatness + w3 * peak_dip_mismatch
    max_score = w1
    min_score = w2 + w3
    treads_score -= min_score
    treads_score /= max_score - min_score
    return treads_score
