
import pandas as pd
import os
from pathlib import Path
from sys import exit
import holidays 
import calendar
import numpy as np
import matplotlib.pyplot as plt
import copy

type_load = 'residential'
calendar = calendar.TextCalendar().formatyear(2021, 2, 1, 1, 3)

data_file = 'Consumer_Typical_Load_Profiles_for_the_year_EAC_2021.xlsx'

#Define the sheet name
typical_load =  pd.read_excel(data_file, sheet_name = 6, header=0, index_col=0)

max_load = 10 # max load in kVA (assume equal to kW), different for each load_type

## Construct year profile 
date_range = pd.date_range(start='2021-01-01', end='2021-12-31 23:30:00', freq='30min')
date_range_series = date_range.to_series()


# Get columns with monthly data
col0=0
coln=24

typical_load_month = typical_load.iloc[:, col0:coln]
typical_load_month.reset_index(drop=True, inplace=True)
typical_load_month_rev = typical_load_month.drop(typical_load_month.index[[0, 1]])
typical_load_month_rev.reset_index(drop=True, inplace=True)
typical_load_month_rev = typical_load_month_rev.iloc[:48]

# Filter  business days and weekends

holidayscy = holidays.Cyprus(years=[2021])
holidayscy_df = pd.DataFrame.from_dict(holidayscy, orient='index')
holidayscy_df_index = holidayscy_df.index.to_series()
holidayscy_df_index_dt = pd.to_datetime(holidayscy_df_index)

holidays_series =  date_range_series[date_range_series.dt.date.isin(holidayscy_df_index_dt.dt.date)]

days_per_month = {month: dates for month, dates in date_range.to_series().groupby(date_range.month)}
keys = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
days_per_month_dic = dict(zip(keys, list(days_per_month.values())))


business_days = []
weekends_holidays = []
for i in days_per_month_dic:
    business = days_per_month_dic[i][(days_per_month_dic[i].dt.weekday.isin([0,1,2,3,4]))
                                          & (~days_per_month_dic[i].dt.date.isin(holidayscy_df_index_dt.dt.date))]
    business_days.append(business)
    holidays_month = days_per_month_dic[i][date_range_series.dt.date.isin(holidayscy_df_index_dt.dt.date)]
    weekends = days_per_month_dic[i][(days_per_month_dic[i].dt.weekday.isin([5,6]))
                                        | (days_per_month_dic[i].isin(holidays_month))]
    weekends_holidays.append(weekends)

business_days_dic = dict(zip(keys, business_days))
weekends_holidays_dic = dict(zip(keys, weekends_holidays))

time_index = pd.date_range(start = '00:00', end='23:30', freq='30min').to_series()
time_index = time_index.dt.time
typical_load_month_rev.set_index(time_index, inplace=True)

business_days_data = []
for i in range(0,23,2):
    business_data = typical_load_month_rev.iloc[:, i]
    business_data.rename("Working days [p.u]", inplace=True)
    business_days_data.append(business_data)

weekends_holidays_data = []
for i in range(1,24,2):
    holidays_data = typical_load_month_rev.iloc[:, i]
    holidays_data.rename("Non-working days [p.u]", inplace=True)
    weekends_holidays_data.append(holidays_data)
    
business_days_data_dic = dict(zip(keys, business_days_data))
weekends_holidays_data_dic = dict(zip(keys, weekends_holidays_data))

business_days_data_datetime_list = []
weekends_holidays_data_datetime_list = []
for k in keys:
    business_days_data_datetime = pd.concat([business_days_data_dic[k]] * business_days_dic[k].dt.day.value_counts().shape[0], ignore_index=True).to_frame()
    business_days_data_datetime.index = business_days_dic[k]
    business_days_data_datetime_list.append(business_days_data_datetime)
    weekends_holidays_data_datetime = pd.concat([weekends_holidays_data_dic[k]] * weekends_holidays_dic[k].dt.day.value_counts().shape[0], ignore_index=True).to_frame()
    weekends_holidays_data_datetime.index = weekends_holidays_dic[k]
    weekends_holidays_data_datetime_list.append(weekends_holidays_data_datetime)   

business_days_data_datetime_dic =  dict(zip(keys, business_days_data_datetime_list))
weekends_holidays_data_datetime_dic  =  dict(zip(keys, weekends_holidays_data_datetime_list))

# Combine the dataframes
business_days_data_datetime_total_df = pd.concat(business_days_data_datetime_dic)
weekends_holidays_data_datetime_total_df  = pd.concat(weekends_holidays_data_datetime_dic)

business_days_data_datetime_total_df.columns = ['Power [p.u]']
weekends_holidays_data_datetime_total_df.columns = ['Power [p.u]']

business_days_data_datetime_total_index = business_days_data_datetime_total_df.index.to_frame().reset_index(drop=True).drop(columns=[0])
weekends_holidays_data_datetime_total_index = weekends_holidays_data_datetime_total_df.index.to_frame().reset_index(drop=True).drop(columns=[0])

typical_load_year = pd.concat([business_days_data_datetime_total_df, weekends_holidays_data_datetime_total_df])
typical_load_year_final = typical_load_year.droplevel(level=0)
typical_load_year_final.sort_index(inplace=True)

typical_load_year_final_kw = typical_load_year_final * max_load
typical_load_year_final_kw.columns = ['Power [kW]']


typical_load_year_final_kw = typical_load_year_final_kw.astype(float).round(3)

# Create ressampled df in 1h interval
resample_typical_load_year_final_kw = typical_load_year_final_kw.resample('1h').mean().astype(float).round(3)
annual = resample_typical_load_year_final_kw.sum()

# Export in CSV and plot charts
date_range = pd.date_range(start='2021-01-01', end='2021-12-31 23:30:00', freq='1h')
resample_typical_load_year_final_kw.set_index(date_range, inplace=True)

resample_typical_load_year_final_kw.to_csv('Typical Energy Load ' + '-' + type_load + '.csv')

fig, ax = plt.subplots(figsize=(20,15))
resample_typical_load_year_final_kw.plot(ax = ax)
ax.set(ylabel = 'Electricity load (kW)', xlabel = 'Timestep', title = 'Typical Energy Load' + '-' + type_load + '.png')
fig.tight_layout()
plt.savefig('Typical Energy Load' + '-' + type_load + '.png')    
    

