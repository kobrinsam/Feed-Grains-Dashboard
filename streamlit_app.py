from collections import namedtuple
import altair as alt
import math
import pandas as pd
import streamlit as st
import yfinance as yf
from sklearn import preprocessing
import numpy as np
import requests
st.title("American Agricultural Economy Barometer")
st.subheader("Surveying the state of the agriculture industry on a monthly basis")
st.caption("Data sources include Ag Economy Barometer Indices produced by Perdue Univeristy and key Agricultural input and output prices.")
### format ag barometer data
df = pd.read_html("https://ag.purdue.edu/commercialag/ageconomybarometer/tables/")[0]
df['Month/Year.1'] = df['Month/Year.1'].apply(lambda x: str(x))
df['Date'] = df['Month/Year'] +'-'+ df['Month/Year.1']
df['Date'] = pd.to_datetime(df['Date'])
df = df.drop(['Month/Year', 'Month/Year.1'], axis=1)
#######
### get yahoo finance data
data = yf.download(
        # tickers list or string as well
        tickers = "UFV=F ZC=F ZS=F LE=F DC=F HE=F NG=F",

        #LE=F is live cattle futures
        # DC=F is milk futures
        # HE=F is lean hog futures
        period = "max",
        interval = "1mo",
        group_by = 'column',
        auto_adjust = True,
        prepost = True,
    )
data = data['Close'].rename(columns={"DC=F":"Milk Futures (DC-F)", "HE=F" :"Lean Hog Futures (HE=F)",
                              "LE=F": "Live Cattle Futures (LE=F)",
                              "UFV=F":"Urea (Granular) FOB US Gulf Fut (UFV=F)",
                              "ZS=F":"Soybean Futures,Nov-2022 (ZS=F)",
                              "NG=F": "Natural Gas Oct 22 (NG=F)",
                              "ZC=F":"Corn Futures,Dec-2022 (ZC=F)"})


#### get drought data
r = requests.get("https://usdmdataservices.unl.edu/api/USStatistics/GetDroughtSeverityStatisticsByArea?aoi=conus&startdate=1/1/2000&enddate=8/1/2022&statisticsType=1")
json = r.json()
drought = pd.DataFrame.from_dict(json)
drought[['D0', 'D1', 'D2', 'D3','D4']] = drought[['D0', 'D1', 'D2', 'D3','D4']].applymap(lambda x: float(str.replace(x,',', '')))
drought['Date'] = pd.to_datetime(drought['MapDate'])
drought = drought.set_index('Date').resample("M").mean()
drought = drought.reset_index()
drought['Date'] = drought['Date'].apply(lambda x: x.replace(day=1))
drought['CONUS Area in Drought (D1 - D4)'] = drought['D1'] + drought['D2'] + drought['D3'] + drought['D4']
drought = drought.rename(columns = {'D0' : 'CONUS Area at Risk of Drought - D0',
 'D1':'CONUS Area in Moderate Drought - D1',
  'D2': 'CONUS Area in Severe Drought - D2',
   'D3': 'CONUS Area in Extreme Drought - D3',
    'D4':'CONUS Area in Exceptional Drought - D4'})
#merge dataframes
total_data = data.reset_index().merge(df, how='left').merge(drought, how='left')
# normalize data
#create scaled dataframe
total_data = total_data.set_index('Date')
scaled_df = preprocessing.normalize(total_data.fillna(0), axis=0)
scaled_df = pd.DataFrame(scaled_df, columns=total_data.columns, index =total_data.index).replace({0:np.NaN}).reset_index()
total_data = total_data.reset_index()
barometer_list = ['Purdue/CME Ag Economy Barometer',
 'Index of Current Conditions',
 'Index of Future Expectations',
 'Farm Capital Investment Index']
drought_list =  ['CONUS Area at Risk of Drought - D0',
'CONUS Area in Moderate Drought - D1',
  'CONUS Area in Severe Drought - D2',
   'CONUS Area in Extreme Drought - D3',
    'CONUS Area in Exceptional Drought - D4',
    'CONUS Area in Drought (D1 - D4)']
####
# correlations df
corr_df = scaled_df[scaled_df['Date']>'2010-10-01'].rename(columns={"DC=F":"Milk Futures (DC-F)", "HE=F" :"Lean Hog Futures (HE=F)",
                              "LE=F": "Live Cattle Futures (LE=F)",
                              "UFV=F":"Urea (Granular) FOB US Gulf Fut (UFV=F)",
                              "ZS=F":"Soybean Futures,Nov-2022 (ZS=F)",
                              "NG=F": "Natural Gas Oct 22 (NG=F)",
                              "ZC=F":"Corn Futures,Dec-2022 (ZC=F)"}).corr().drop(barometer_list, axis=0)

## drought df
drought_df = corr_df['CONUS Area in Drought (D1 - D4)'].drop(drought_list, axis=0)


###functions
def display_data(norm):
    if norm:
        return scaled_df
    else :
        return total_data
#frontend

indicators = st.multiselect('Agricultural Economic Indicators', list(total_data.drop('Date', axis=1).columns))
norm = st.checkbox('Normalize Economic Indicators')
st.text("Ag Economy Indicators, by month")
st.line_chart(data = display_data(norm), x= 'Date' , y = indicators)
st.text("Ag Economy Indicator Data Table")
st.dataframe(display_data(norm).set_index('Date'))
st.subheader('Farmer Sentiment is Associated with Key Agricultural Commodity Prices')
st.text('Correlation Between Ag Economy Barometer Indices and Key Ag Commodity Prices')
radio = st.radio('Ag Barometer Index', ['Purdue/CME Ag Economy Barometer',
 'Index of Current Conditions',
 'Index of Future Expectations',
 'Farm Capital Investment Index'], index=0, horizontal=True)
bar_df = corr_df[radio].sort_values()
st.bar_chart(data=bar_df)
st.subheader('There is a Strong Relationship Between Drought and Ag Commodity Futures Prices')
st.text('Correlation Between CONUS Area in drought and Key Ag Commodity Prices')
st.bar_chart(data= drought_df.sort_values())
col1, col2 = st.columns([4, 1])
st.text('Data Sources: Purdue Ag Barometer, The U.S. Drought Monitor, and Yahoo Finance')
st.text('By Sam Kobrin')


