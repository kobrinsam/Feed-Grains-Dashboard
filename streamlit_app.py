import altair as alt
import pandas as pd
import streamlit as st
import numpy as np
import requests, zipfile, io
from streamlit_lottie import st_lottie  # pip install streamlit-lottie
import json
st.title("USDA Economic Reseach Service Feed Grains Dashboard")
st.caption("This dashboard contains statistics on four feed grains (corn, grain sorghum, barley, and oats), foreign coarse grains (feed grains plus rye, millet, and mixed grains), hay, and related items. This includes data published in the monthly Feed Outlook and previously annual Feed Yearbook. Data are monthly, quarterly, and/or annual depending upon the data series. Latest data may be preliminary or projected. Missing values indicate unreported values, discontinued series, or not yet released data.")

zip_file_url = "https://www.ers.usda.gov/webdocs/DataFiles/50048/FeedGrains.zip?v=7455.2"

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


#import data
@st.experimental_memo
def get_data():
    r = requests.get(zip_file_url, stream=True)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    z.extractall()
    df = pd.read_csv(z.open('FeedGrains.csv'))
    #format dates
    df['Year_ID'] = df['Year_ID'].apply(lambda x: str(x))
    df['Date'] = df.apply(lambda x: date_format(x["SC_Frequency_ID"], x["Year_ID"], x["Timeperiod_Desc"], x["Timeperiod_ID"]), axis=1)
    df['Date'] = pd.to_datetime(df['Date'])
    return df
df = get_data()


### sidebar
with st.sidebar:
    df = df[df.SC_GeographyIndented_Desc == "United States"]
    group = st.multiselect('Group', list(df.SC_Group_Desc.unique()), default='Prices')
    df_group = df[df.SC_Group_Desc.isin(group)]
    comm = st.multiselect('Commodity', list(df_group.SC_GroupCommod_Desc.unique()))
    comm_group = df_group[df_group.SC_GroupCommod_Desc.isin(comm)]
    attr = st.multiselect('Data Attribute', list(comm_group.SC_Attribute_Desc.unique()))
    attr_df = comm_group[comm_group.SC_Attribute_Desc.isin(attr)]
    dateFreq = st.radio('Frequency', list(attr_df.SC_Frequency_Desc.unique()))
  
    freq_df = attr_df[attr_df.SC_Frequency_Desc == dateFreq]
#filters
unit = np.where(len(freq_df.SC_Unit_Desc.unique())<1,"", freq_df.SC_Unit_Desc.min())
if len(attr) <1:
    chart_title =  "<<< Select Data of Interest From the Sidebar To Get Started"
    st.subheader(chart_title)
    ###lottefile
    # GitHub: https://github.com/andfanilo/streamlit-lottie
    # Lottie Files: https://lottiefiles.com/

    def load_lottiefile(filepath: str):
        with open(filepath, "r") as f:
            return json.load(f)


    def load_lottieurl(url: str):
        r = requests.get(url)
        if r.status_code != 200:
            return None
        return r.json()
    

    #lottie_coding = load_lottiefile("lottiefile.json")  # replace link to local lottie file
    lottie_wheat = load_lottieurl("https://assets10.lottiefiles.com/private_files/lf30_fogqgdsk.json")
   
    st_lottie(
        lottie_wheat,
        speed=1,
        reverse=False,
        loop=True,
        quality="low", # medium ; high
         # canvas
        height=None,
        width=None,
        key=None,
    )

else:
    chart_title =  "{} {}, {}".format(comm[0], attr[0], unit)
    st.subheader(chart_title)
    chart = alt.Chart(freq_df).mark_line().encode(
    x='Date',
    y= alt.Y('Amount', title = "{}".format(unit)),
    color='SC_Commodity_Desc')
    st.altair_chart(chart, use_container_width=True)
if len(attr) <1:
    table_title =  ""
else:
    @st.cache
    def convert_df(df):
         # IMPORTANT: Cache the conversion to prevent computation on every rerun
         return df.to_csv().encode('utf-8')

    csv = convert_df(freq_df)

    st.download_button(
         label="Download The Data as CSV",
         data=csv,
         file_name='feed_grains.csv',
         mime='text/csv',
     )
    table_title = "Data Table: {} {}".format(comm[0], attr[0])
    st.text(table_title)
    st.dataframe(freq_df[['Date', "Amount"]].set_index('Date'))

##footer
st.text('Data Sources: Feed Grains: Yearbook Table, USDA Economic Reseach Service')
st.text('By Sam Kobrin')


