
# coding: utf-8

# In[7]:

import matplotlib.pyplot as plt
get_ipython().magic('pylab')
get_ipython().magic('matplotlib inline')


# In[5]:

raw_img_file = r"C:\Users\MPNV38\ZDevelop\tiretread\data\SE655POC\parallel.raw"
# raw_img_file = r"C:\Users\MPNV38\ZDevelop\tiretread\data\SE655POC\parallel.raw"
raw_img = np.fromfile(raw_img_file, dtype='uint8')
raw_img = raw_img.reshape(1000, 1500)
plt.imshow(raw_img)


# In[8]:

# reverse the image and remove the background
raw_img = 130.0 - raw_img
raw_img[raw_img < 30] = 0
plt.imshow(raw_img)


# In[9]:

# get weighted centor
profile = raw_img * np.linspace(0, 1499, 1500)
profile = profile.sum(axis=1) / raw_img.sum(axis=1)
plt.plot(profile)


# In[5]:

nans = np.isnan(profile)
if nans.nonzero()[0]:
    profile[nans]= np.interp(nans.nonzero()[0], (~nans).nonzeros()[0], profile[~nans])
plt.figure();plt.plot(profile)

plt.show()


# In[ ]:



