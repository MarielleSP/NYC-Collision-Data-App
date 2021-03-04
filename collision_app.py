import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import plotly.express as px


# DATA_URL = ("/home/cicada/Downloads/rhyme/streamlit/Motor_Vehicle_Collisions_-_Crashes.csv")
DATA_URL = './Data/reduced_Motor_Vehicle_Collisions_-_Crashes.csv'

st.title("Motor Vehicle Collisions in New York City")
st.markdown("This application is a Streamlit dashboard that can be used "
            "to analyze motor vehicle collisions in NYC 🗽💥🚗")
# The emojis are simply copy-paste from the internet


@st.cache(persist=True)    # This will load data once and cache it
def load_data(nrows):
    data = pd.read_csv(DATA_URL, nrows=nrows, parse_dates=[['CRASH_DATE', 'CRASH_TIME']])
    # cannot have missing longitude and latitude for plotting
    data.dropna(subset=['LATITUDE', 'LONGITUDE'], inplace=True)
    # convert column names to lower case
    lowercase = lambda x: str(x).lower()
    data.rename(lowercase, axis="columns", inplace=True)
    data.rename(columns={"crash_date_crash_time": "date/time"}, inplace=True)
    return data

data = load_data(100000)    # load only a given number of rows
original_data = data


# Display an interactive map
st.header("Where are the most people injured in NYC?")
# insert a slider to make hte map interactive
# previous calculation showed that max number was 19
injured_people = st.slider("Number of persons injured in vehicle collisions", 0, 19)
# query the dataframe where column injured_persons has value >= value of injured_people
# returns a location (lat, long)
st.map(data.query("injured_persons >= @injured_people")[["latitude", "longitude"]].dropna(how="any"))

# the slider can be placed in a sidebar instead
#    injured_people = st.sidebar.slider("Number of persons injured in vehicle collisions", 0, 19)
# an arrow at top left of page toggles sidebar on/off


# Display an interactive plot of collisions vs time of day
st.header("How many collisions occur during a given time of day?")
hour = st.slider("Hour to look at", 0, 23)
data = data[data['date/time'].dt.hour == hour]
st.markdown("Vehicle collisions between %i:00 and %i:00" % (hour, (hour + 1) % 24))
# to initialize map a view of NYC (instead of global view)
# calculate avg lat and long from the data set
midpoint = (np.average(data["latitude"]), np.average(data["longitude"]))
st.write(pdk.Deck(
    map_style="mapbox://styles/mapbox/light-v9",
    initial_view_state={
        "latitude": midpoint[0],
        "longitude": midpoint[1],
        "zoom": 11,
        "pitch": 50,
    },
    # add layer to the map to display data
    layers=[
        pdk.Layer(
        "HexagonLayer",
        data=data[['date/time', 'latitude', 'longitude']],
        get_position=["longitude", "latitude"],    # Note the order : long before lat
        auto_highlight=True,
        radius=100,
        extruded=True,    # need for 3D
        pickable=True,
        elevation_scale=4,
        elevation_range=[0, 1000],
        ),
    ],
))


# Diplay interactive plot of collisions vs time of day
# plotly.express allows us to plot interactively from a simple dataframe
st.subheader("Breakdown by minute between %i:00 and %i:00" % (hour, (hour + 1) % 24))
filtered = data[
    (data['date/time'].dt.hour >= hour) & (data['date/time'].dt.hour < (hour + 1))
]
hist = np.histogram(filtered['date/time'].dt.minute, bins=60, range=(0, 60))[0]
chart_data = pd.DataFrame({"minute": range(60), "crashes": hist})
fig = px.bar(chart_data, x='minute', y='crashes', hover_data=['minute', 'crashes'], height=400)
st.write(fig)


# Find the most dangerous streets for different classes of injured_persons
st.header("Top 5 dangerous streets by affected class")
# insert a dropdown menu; the first option displayed is the default
select = st.selectbox('Affected class', ['Pedestrians', 'Cyclists', 'Motorists'])
if select == 'Pedestrians':
    st.write(original_data.query("injured_pedestrians >= 1")[["on_street_name", "injured_pedestrians"]].sort_values(by=['injured_pedestrians'], ascending=False).dropna(how="any")[:5])
elif select == 'Cyclists':
    st.write(original_data.query("injured_cyclists >= 1")[["on_street_name", "injured_cyclists"]].sort_values(by=['injured_cyclists'], ascending=False).dropna(how="any")[:5])
else:
    st.write(original_data.query("injured_motorists >= 1")[["on_street_name", "injured_motorists"]].sort_values(by=['injured_motorists'], ascending=False).dropna(how="any")[:5])


# a checkbox to toggle on/off a data table
if st.checkbox("Show Raw Data", False):
    st.subheader('Raw Data')
    st.write(data)
