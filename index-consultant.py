#!/usr/bin/env python
# coding: utf-8

# ### Library

# In[3]:


import pandas as pd
import numpy as np
import re
import os
#import difflib
# ### Parse Excel 

# ##### Get list of consultants from Excel

# In[19]:

df = pd.read_excel('C:/Users/yazdsous/Documents/GitHub/index-consultant-or-companyname/list_of_consultants.xlsx')  
list_cons = list(df.Consultant)


# #### Find unique words

# In[44]:
a = set()
unique = [x for x in list_cons if x not in a and (a.add(x) or True) and type(x) is not float]


#ref_list = ['TriAlta', 'Trace Associates','Métis Nation of Alberta (MNA) Region 3', 'TreaTy, Lands & resources department Tsleil-Waututh Nation','Stantec', 'ENVIRONMENTAL DEFENCE, EQUITERRE, SIERRA CLUB B.C.','Tera - CH2M','Hydro-Québec TransÉnergie','Dillon Consulting Limited - CH2M HILL Energy Canada','Action Land & Environmental Services','Matrix Solutions','Golder Associates','Ghostpine Environmental Services','NGTL','Enbridge','Integrated Environments','TERA Environmental Consultants','Jacques Whitford','AXYS Environmental Consulting','Montana-Alberta Tie','EnCana Corporation','AMEC','SNC-Lavalin','PanCanadian Energy','Driftpile','EDI Environmental Dynamics','Wood.','TransMountain','Amec Foster Wheeler','CH2M HILL','Trans Northern','Landsong Heritage Consulting','B.A. Blackwell & Associates','Applied Aquatic Research']




path_txt = "F:/Environmental Baseline Data/Version 2/Data/Text/"


# In[37]:


cnt = 0
files = []
fname = []
# r=root, d=directories, f = files
for r, d, f in os.walk(path_txt):
    for file in f:
        if '.txt' in file:
            files.append(os.path.join(r, file))
            fname.append(file)


# In[52]:


data = {'FilePath':files,'FileName':fname,'Consultants':None} 
  
# Create DataFrame 
df = pd.DataFrame(data) 
  


#Parse text files one at a time and search for the consultant names in the list and add that name to the column "Consultants" in the dataframe
# In[ ]:
lst = []
cnt = 0
for f in files:
    txt_file = open(f , encoding="utf8")
    f_lst = txt_file.readlines()
    s = " ".join([x.strip() for x in f_lst])
    lst_ov = []
    for x in unique:
        if(re.search((x.lower()), s.lower())):
            lst_ov.append(x)
        else:
            lst_ov.append(None)
    lst.append(lst_ov)
    if all(x is None for x in lst_ov):
        cnt = cnt+1
        print(f)
        df.loc[df['FilePath'] == f , 'Consultants'] = "Not Found"
    else:
        df.loc[df['FilePath'] == f , 'Consultants'] = [[x for x in lst_ov if x != None]]










