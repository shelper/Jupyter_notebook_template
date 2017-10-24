
# coding: utf-8

# In[11]:


import os
import glob
import cv2
import numpy as  np
from scipy.signal import savgol_filter, medfilt
import matplotlib.pyplot as plt

get_ipython().run_line_magic('matplotlib', 'notebook')
# configurations that used in the treads detection algorithm
# raw image params
reverse, thresh, bg_level = True, 20.0, 130.0
# system params
baseline, sensor2baseline_offset, d0 = 10.067, 1.25, 5.549
row_num, pix_num, pix_size = 1000, 1500, 0.0055
# tread params
win_size, edge_size, edge_expand = 30, 10, 15
min_tread_width, max_tread_width, max_treads_num, treads_num = 20, 80, 8, 4
min_treads_score = 0.5
# profile smoothing params for Savitzky–Golay smoothing 
spike_size, filt_size, fit_order = 2, 11, 3

img_file = r'C:\Users\MPNV38\ZDevelop\tiretread\data\SE655POC\from_Neeharika\07.bmp'


# In[12]:


def get_img(img_file, row_num, pix_num, reverse, thresh):
    if img_file[-3:] == 'raw':
        image = np.fromfile(img_file, dtype='uint8')
        image = np.reshape(image, (row_num, pix_num))
    elif img_file[-3:] == 'bmp':
        image = cv2.imread(img_file, cv2.IMREAD_GRAYSCALE)
    # offset and threshold to remove bg noise
#     image = image[1:-1, 1:-1]
    if reverse:
        image = bg_level - image
    image[image < thresh] = 0
    image -= image.min()
    image *= 255 / image.max()
    
    return image

img = get_img(img_file, row_num, pix_num, reverse, thresh)
plt.imshow(img, vmin=0, vmax=130, cmap='gray')


# In[30]:


def get_profile(image, spike_size, filt_size, fit_order):
    profile = (image) * np.arange(image.shape[1])
    profile = profile.sum(axis=1) / (image).sum(axis=1)
    plt.figure(); plt.plot(profile); plt.title('raw profile')
    # fill in missing points of the profile
    nans = np.isnan(profile)
    if len(nans.nonzero()[0]):
        profile[nans]= np.interp(nans.nonzero()[0], (~nans).nonzero()[0], profile[~nans])
    plt.figure(); plt.plot(profile);plt.title('broken line interpolated')
    # smooth the profile
    if spike_size: 
        profile = medfilt(profile, spike_size * 2 + 1)
        plt.figure(); plt.plot(profile); plt.title('spikes removed')
    if filt_size:
        profile = savgol_filter(profile, filt_size, fit_order)
        plt.figure(); plt.plot(profile); plt.title('smoothed using savgol filter')
    return profile

profile = get_profile(img, spike_size, filt_size, fit_order)
profile_diff = profile[:-edge_size] - profile[edge_size:]
plt.figure();plt.plot(np.diff(profile_diff));plt.plot(profile_diff)


# In[35]:


def find_treads(profile_diff, edge_size,  win_size, max_treads_num, min_tread_width):
    n_sects = len(profile_diff) // win_size
    idx4mins = []
    idx4maxs = []
    for i in range(len(profile_diff) // win_size):
        s = i * win_size 
        e = (i + 1) * win_size
        idx4mins.append(s + profile_diff[s : e].argmin())
        idx4maxs.append(s + profile_diff[s : e].argmax())
    plt.figure(); plt.plot(profile_diff) 
    for (s, e) in zip(idx4maxs, idx4mins):
        plt.axvline(x=s, color='r')
        plt.axvline(x=e, color='g')
    plt.title('local max(red) and min(green)')

    max2pop = []
    for i in range(len(idx4maxs) - 1):
        if idx4maxs[i+1] - idx4maxs[i] < win_size:
            if (profile_diff[idx4maxs[i]] <= profile_diff[idx4maxs[i+1]]) and (i not in max2pop):
                max2pop.append(i)
            elif i+1 not in max2pop:
                max2pop.append(i + 1)
    plt.figure(); plt.plot(profile_diff) 
    for i in max2pop:
        plt.axvline(x=idx4maxs[i], color='r')
    plt.title('fake local max to be removed')
        
    min2pop = []
    for i in range(len(idx4mins) - 1):
        if idx4mins[i+1] - idx4mins[i] < win_size:
            if profile_diff[idx4mins[i]] >= profile_diff[idx4mins[i+1]] and (i not in min2pop):
                min2pop.append(i)
            elif i+1 not in min2pop:
                min2pop.append(i + 1)
    plt.figure(); plt.plot(profile_diff) 
    for i in min2pop:
        plt.axvline(x=idx4mins[i], color='g')
    plt.title('fake local min to be removed')
        
    for i in reversed(max2pop):
        idx4maxs.pop(i)
    for i in reversed(min2pop):
        idx4mins.pop(i)
    plt.figure(); plt.plot(profile_diff) 
    for s, e in zip(idx4maxs, idx4mins):
        plt.axvline(x=s, color='r')
        plt.axvline(x=e, color='g')
    plt.title('after removing fake local min and max')

    idx4mins = np.array(idx4mins)
    idx4maxs = np.array(idx4maxs)
    edge_starts = np.sort(idx4maxs[profile_diff[idx4maxs].argsort()[-max_treads_num:]])
    edge_ends = np.sort(idx4mins[profile_diff[idx4mins].argsort()[:max_treads_num]])
    
    plt.figure(); plt.plot(profile_diff) 
    for s, e in zip(edge_starts, edge_ends):
        plt.axvline(x=s, color='r')
        plt.axvline(x=e, color='g')
    plt.title('the top candidates of tread starts(red) and tread ends(green)')
    
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
#                 # remove treads overlapping
#                 elif start < end0:
#                     treads_edge.pop()
#                     treads_edge.append([max(start, start0), min(end, end0)])
                else:
                    treads_edge.append([start, end])

    plt.figure(); plt.plot(profile_diff) 
    for s, e in treads_edge:
        plt.axvline(x=s, color='r')
        plt.axvline(x=e, color='g')
    plt.title('treads start(red) and end(green) location on profile diff')
    
    treads_edge = np.array(treads_edge)
    treads_edge[:, 1] += edge_size 
    
    plt.figure(); plt.plot(profile) 
    for s, e in treads_edge:
        plt.axvline(x=s, color='r')
        plt.axvline(x=e, color='g')
    plt.title('treads start(red) and end(green) location on profile')

    treads_width = np.squeeze(np.diff(treads_edge, axis=1))
    treads_edge = treads_edge[(treads_width>min_tread_width) & (treads_width<max_tread_width)]
    
    plt.figure(); plt.plot(profile) 
    for s, e in treads_edge:
        plt.axvline(x=s, color='r')
        plt.axvline(x=e, color='g')
    plt.title('remove treads that is too wide or too narrow')
    
    return treads_edge

treads_edge = find_treads(profile_diff, edge_size,  win_size, max_treads_num, min_tread_width)

# treads = np.zeros((treads_edge.shape[0], np.diff(treads_edge).max() + edge_expand * 2))
# for i, (s, e) in enumerate(treads_edge):
#     ss = s - edge_expand
#     ee = e + edge_expand
#     tread = profile[ss:ee]
#     pad_before = (treads.shape[1] - len(tread)) // 2
#     pad_after = treads.shape[1] - len(tread) - pad_before
#     treads[i] = np.pad(tread, (pad_before, pad_after), 'edge')
    
plt.figure();plt.plot(treads.T); plt.title('raw treads')


# In[32]:


def calibrate_treads(profile, treads_edge, pix_size, edge_expand):
    treads_num = treads_edge.shape[0]
    treads = np.zeros((treads_num, np.diff(treads_edge).max() + edge_expand * 2))
    abs_depth = lambda x : - x * d0 / (x - baseline) 
    for i, (s, e) in enumerate(treads_edge):
        # remove the baseline of the tread, baseline is fitted using beginning and ending points
        ss = s - edge_expand
        ee = e + edge_expand
        tread = abs_depth(profile[ss:ee] * pix_size + baseline + sensor2baseline_offset)
        x = np.concatenate((np.arange(edge_expand), np.arange(len(tread) - edge_expand, len(tread))))
        linear_fit_params = np.polyfit(x, tread[x], 1)
        tread -= np.polyval(linear_fit_params, np.arange(len(tread)))
        pad_before = (treads.shape[1] - len(tread)) // 2
        pad_after = treads.shape[1] - len(tread) - pad_before
        treads[i] = np.pad(tread, (pad_before, pad_after), 'constant')
    return treads

treads = calibrate_treads(profile, treads_edge, pix_size, edge_expand)
plt.figure();plt.plot(treads.T); plt.title('after calibration of treads')


# In[33]:


def get_treads_score(profile_diff, treads_depth, treads_edge, edge_size):
    w1, w2, w3 = 1, -1, -1
    norm_treads_depth = treads_depth / treads_depth.max()
    treads_unflatness = []
    idx_peaks_dips = treads_edge - [0, edge_size]
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
   
treads_depth = - treads.min(axis=1)
treads_score = get_treads_score(profile_diff, treads_depth, treads_edge, edge_size)
plt.figure();plt.plot(treads.T); plt.title('treads score as shown in figure legend'); plt.legend(treads_score)

picked_treads_idx = (treads_score.argsort())[-treads_num:]
picked_treads_idx = picked_treads_idx[treads_score[picked_treads_idx] > min_treads_score]
picked_treads = treads[picked_treads_idx[-treads_num:]]
picked_treads_depth = treads_depth[picked_treads_idx]
picked_treads_score = treads_score[picked_treads_idx]
picked_treads_edge = treads_edge[picked_treads_idx]
plt.figure();plt.plot(picked_treads.T); plt.title('top picked treads'); plt.legend(picked_treads_score)


# In[34]:


resized_img = np.flipud(img[:, int(profile.min()):int(profile.max())].T)
plt.figure()
plt.subplot(311)
plt.imshow(resized_img, aspect=0.1 * resized_img.shape[1]/resized_img.shape[0])

plt.subplot(312)
plt.plot(profile)
for (s, e) in treads_edge:
    plt.axvline(x=s, color='r')
    plt.axvline(x=e, color='r')
for (s, e) in picked_treads_edge:
    plt.axvline(x=s, color='g')
    plt.axvline(x=e, color='g')
    plt.xlim(0, len(profile))

plt.subplot(313)
if len(treads):
    plt.plot(picked_treads.T)
    plt.legend(picked_treads_score)

# plt.savefig(os.path.join(os.path.split(img_file)[0], 'profile', os.path.basename(img_file) + '.png'))

