import altair as alt
import pandas as pd
import streamlit as st
import numpy as np
import requests, zipfile, io

st.title("USDA Economic Reseach Service Feed Grains Dashboard")
st.caption("This dashboard contains statistics on four feed grains (corn, grain sorghum, barley, and oats), foreign coarse grains (feed grains plus rye, millet, and mixed grains), hay, and related items. This includes data published in the monthly Feed Outlook and previously annual Feed Yearbook. Data are monthly, quarterly, and/or annual depending upon the data series. Latest data may be preliminary or projected. Missing values indicate unreported values, discontinued series, or not yet released data.")

zip_file_url = "https://www.ers.usda.gov/webdocs/DataFiles/50048/FeedGrains.zip?v=7455.2"


#import data
r = requests.get(zip_file_url, stream=True)
z = zipfile.ZipFile(io.BytesIO(r.content))
z.extractall()
df = pd.read_csv(z.open('FeedGrains.csv'))

##function to format date
def date_format(freq, year, time, time_id):
  if freq == 1:
      return time +'-'+ year
  elif freq == 2:
    if str(time_id)[-1] == "1":
     return "Jan" +'-'+ year
    elif str(time_id)[-1] == "2":
      return "Apr" +'-'+ year
    elif str(time_id)[-1] == "3":
      return "July" +'-'+ year
    else:
      return "Oct" +'-'+ year
  elif freq == 3:
    return "Jan" +'-'+ year

#format dates
df['Year_ID'] = df['Year_ID'].apply(lambda x: str(x))
df['Date'] = df.apply(lambda x: date_format(x["SC_Frequency_ID"], x["Year_ID"], x["Timeperiod_Desc"], x["Timeperiod_ID"]), axis=1)
df['Date'] = pd.to_datetime(df['Date'])
### sidebar
with st.sidebar:
    df = df[df.SC_GeographyIndented_Desc == "United States"]
    group = st.multiselect('Group', list(df.SC_Group_Desc.unique()), default='Prices')
    df_group = df[df.SC_Group_Desc.isin(group)]
    comm = st.multiselect('Commodity', list(df_group.SC_GroupCommod_Desc.unique()), default='Hay')
    comm_group = df_group[df_group.SC_GroupCommod_Desc.isin(comm)]
    attr = st.multiselect('Data Attribute', list(comm_group.SC_Attribute_Desc.unique()), default='Prices received by farmers')
    attr_df = comm_group[comm_group.SC_Attribute_Desc.isin(attr)]
    dateFreq = st.radio('Frequency', list(attr_df.SC_Frequency_Desc.unique()))
    freq_df = comm_group[attr_df.SC_Frequency_Desc == dateFreq]
#filters
chart_title = "{} {}, {}".format(comm[0], attr[0], freq_df.SC_Unit_Desc.min())
st.subheader(chart_title)
st.line_chart(data = freq_df, x= 'Date', y='Amount')
table_title = "Data Table: {} {}".format(comm[0], attr[0])
st.text(table_title)
st.dataframe(freq_df[['Date', "Amount"]])

##footer
st.text('Data Sources: Feed Grains: Yearbook Table, USDA Economic Reseach Service')
st.text('By Sam Kobrin')


