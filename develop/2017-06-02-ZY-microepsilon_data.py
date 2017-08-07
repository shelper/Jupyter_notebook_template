
# coding: utf-8

# In[1]:

get_ipython().magic('version_information numpy, scipy, matplotlib, pandas')


# In[138]:

import csv
import numpy as np
from glob import iglob
data_folder = r"C:\Users\MPNV38\ZDevelop\tiretread\data\232/" 
for data_file in iglob(data_folder + '*.csv'):
    data = []
    with open(data_file) as f:
        for i, line in enumerate(csv.reader(f, delimiter=';')):
            if i > 9 and line:
                data.append(float(line[1].replace(',', '.')))
#                 new_line = [float(s.replace(',', '.')) for s in line[:2]] 
    #             new_line = ','.join(line).split(',')
    #             new_line = [float(s) for s in  new_line[:8]]
#                 data.append(new_line)
    data = np.array(data)
    new_data_file = data_file[:-4] + '_tread.csv'
    np.savetxt(new_data_file, data, fmt='%.3f')
    print(new_data_file)


# In[ ]:



