# to run the app : streamlit run app.py
# to have the correct version  : pipreqs --encoding=utf8 --force


import base64
import pandas as pd  # pip install pandas openpyxl
import plotly.express as px  # pip install plotly-express
import plotly.graph_objects as go
import datetime as dt
import streamlit as st  # pip install streamlit
import folium
from streamlit_folium import folium_static
from geopy.geocoders import Nominatim



# emojis: https://www.webfx.com/tools/emoji-cheat-sheet/
st.set_page_config(page_title="Kickstarter Dashboard", page_icon=":bar_chart:", layout="wide")

# ---- READ EXCEL ----

def completion_percentage_creation(row):
    if row['goal'] == 0:
        return 0
    else:
        return min(100, row['pledged'] / row['goal'] * 100)

@st.cache_data
def get_data_from_csv():
    df=pd.read_csv('Study Case Data Intern (Léo) - data.csv')
    df.dropna(thresh=4, inplace=True)
    df.dropna(subset=['goal', 'pledged', 'state'], inplace=True)



    
    # Replace commas with periods in 'usd pledged' column
    df['goal'] = df['goal'].str.replace(',', '.')
    df['pledged'] = df['pledged'].str.replace(',', '.')
    df['usd pledged'] = df['usd pledged'].str.replace(',', '.')
    df['usd_pledged_real'] = df['usd_pledged_real'].str.replace(',', '.')
    df['usd_goal_real'] = df['usd_goal_real'].str.replace(',', '.')


    # Replace dashes with spaces in 'deadline' and 'launched' columns
    df['deadline'] = df['deadline'].str.replace('-', ' ')
    df['launched'] = df['launched'].str.replace('-', ' ')

    # Convert columns to appropriate data types
    df['deadline'] = pd.to_datetime(df['deadline'], format='%Y %m %d')# %H:%M:%S')
    df['launched'] = pd.to_datetime(df['launched'], format='%Y %m %d')# %H:%M:%S')
    df[['goal', 'pledged', 'usd pledged', 'usd_pledged_real', 'usd_goal_real']] = df[['goal', 'pledged', 'usd pledged', 'usd_pledged_real', 'usd_goal_real']].astype(float)
    df[['ID', 'backers']] = df[['ID', 'backers']].astype(int)

    # Appliquer la fonction pour créer une nouvelle colonne 'completion_percentage'
    df['completion_percentage'] = df.apply(completion_percentage_creation, axis=1)

    return df

df = get_data_from_csv()


# ---- SIDEBAR ----
st.sidebar.header("Please Filter Here:")
Category = st.sidebar.multiselect(
    "Select the category:",
    options=df["category"].unique(),
    default=["Music","Product Design","Film & Video","Nonfiction"],
)

Currency = st.sidebar.multiselect(
    "Select the currency:",
    options=df["currency"].unique(),
    default=["USD","EUR"],
)

randge_goal=st.sidebar.slider("Select the goal amount:",
                  value=[int(df["goal"].min()),int(df["goal"].max())])


list_launched = df["launched"].dt.strftime('%Y-%m-%d').sort_values().unique().astype(str)

start_range_launched, end_range_launched= st.sidebar.select_slider("Select the launch date:",
                options=list_launched,
                value=(list_launched[0], list_launched[-1]))

Country= st.sidebar.multiselect(
    "Select the country:",
    options=df["country"].unique(),
    default=["FR","US","IT"],
)

State = st.sidebar.multiselect(
    "Select the state:",
    options=df["state"].unique(),
    default=["failed","canceled","successful","live"],
)

df_selection = df.query(
    "category == @Category & currency ==@Currency & state == @State & country==@Country"
)



df_selection=df_selection[(df_selection["goal"]>=randge_goal[0]) & (df_selection["goal"]<=randge_goal[1])
                        & (df_selection["launched"]>=dt.datetime.strptime(start_range_launched, '%Y-%m-%d'))
                        & (df_selection["launched"]<=dt.datetime.strptime(end_range_launched, '%Y-%m-%d'))]

# ---- MAINPAGE ----
st.title(":bar_chart: Kickstarter Dashboard")
st.markdown("##")

# ----TOP KPI's
total_backers = df_selection.backers.sum()


avg_completion = round(df_selection["completion_percentage"].mean(),1)
average_pledge = round(df_selection["usd pledged"].mean(),1)
number_of_projetcs=df_selection.shape[0]

c_1, c_2, c_3,c_4 = st.columns(4)
with c_1:
    st.subheader("Total Backers:")
    st.subheader(f" {total_backers:,}")
with c_2:
    st.subheader("Average Completion:")
    st.subheader(f"{avg_completion} %")
with c_3:
    st.subheader("Average plegde:")
    st.subheader(f"$ {average_pledge:,}")
with c_4:
    st.subheader("Number of project:")
    st.subheader(f"{number_of_projetcs}")

st.markdown("""---""")

# ---MAIN GRAPH

#  - Number of Projects Launched over Time
launch_counts = df_selection["launched"].sort_values().reset_index()
fig_Number_Projects_over_Time = px.line(launch_counts, x='launched', title='Evolution of the cumulated Number of Projects')
fig_Number_Projects_over_Time['data'][0]['showlegend'] = True
fig_Number_Projects_over_Time['data'][0]['name'] = 'Cumulated number of projects'
fig_Number_Projects_over_Time.update_xaxes(title='Time')
fig_Number_Projects_over_Time.update_yaxes(title='Number of Projects launched')
fig_Number_Projects_over_Time.update_layout(
    legend=dict(
        x=0,
        y=1,
    )
)



fig_states = go.Figure(data=[go.Pie(labels=df_selection["state"], textinfo='label+percent',
                             insidetextorientation='radial'
                            )])
fig_states.update_traces(hole=.5)
fig_states.update_layout(title='State of the projets')

#  - Distribution of Goal vs Pledged (USD)

fig_distribution_goal_vs_pledge = px.scatter(df_selection, x='goal', y='pledged', color='state', hover_data=['name'], title='Distribution of Goal vs Pledged (USD)')

left_column, right_column = st.columns(2)
with left_column:
    st.plotly_chart(fig_Number_Projects_over_Time, use_container_width=True)
with right_column:
    st.plotly_chart(fig_states, use_container_width=True)



# - Create stacked bar chart with number of values

#trie des données
df_goupe=df_selection.groupby(by=['category', 'state'])['ID'].count().reset_index()
grouped_sorted_columns = df_goupe.groupby(['category'])['ID'].sum().sort_values().index

df_goupe['category'] = pd.Categorical(df_goupe['category'], categories=grouped_sorted_columns, ordered=True)

sorted_df = df_goupe.sort_values(by=['category', 'state'])


fig_number_values = px.bar(sorted_df, x='category', y='ID', color='state', barmode='stack',text_auto=True)

fig_number_values.update_layout(title='Number of projects by category and status', xaxis_title='Category', yaxis_title='Number of projects')
fig_number_values.update_layout(
    legend=dict(
        x=0,
        y=1,
    )
)


# - Create stacked bar chart with the average pledge amount with the ratio 

#trie des données

df_goupe=df_selection.groupby(by=['category', 'state'])["pledged"].mean().reset_index()

grouped_sorted_columns = df_goupe.groupby(['category'])['pledged'].sum().sort_values().index

df_goupe['category'] = pd.Categorical(df_goupe['category'], categories=grouped_sorted_columns, ordered=True)

sorted_df = df_goupe.sort_values(by=['category', 'state'])


fig_avg_values = px.bar(sorted_df, x='category', y='pledged', color='state', barmode='stack',text_auto=True)

fig_avg_values.update_layout(title='Mean of the pledged by projects and status', xaxis_title='Category', yaxis_title='US $')
fig_avg_values.update_layout(
    legend=dict(
        x=0,
        y=1,
    )
)

# display the graph

c_1, c_2 = st.columns(2)
with c_1:
    st.plotly_chart(fig_number_values,use_container_width=True)
with c_2:
    st.plotly_chart(fig_avg_values,use_container_width=True)



# - Affichage de la carte

def get_country_lat_lon(country):
    geolocator = Nominatim(user_agent="my_app")
    location = geolocator.geocode(country, exactly_one=True)
    if location:
        return (location.latitude, location.longitude)
    return None


# Create a dataframe with the number of projects by country
df_countries = df_selection.groupby('country').count()['ID'].reset_index()

# Create a map centered on the world
world_map = folium.Map(location=[0, 0], zoom_start=2)

# Add markers for each country with at least one project
for index, row in df_countries.iterrows():
    if row['country'] != 'N,0"':
        marker = folium.Marker(
            location=get_country_lat_lon(row['country']),
            popup=f"{row['country']}: {row['ID']} projects"
        )
        marker.add_to(world_map)



folium_static(world_map,height=325)#width=725

# - Affichage des données

st.write(df_selection)
st.markdown("""---""")


# - LIENS

LIEN = {
    "Léo Dujourd'hui": "https://leo-dujourd-hui-digital-cv.streamlit.app",
}
SOURCES ={
    "Github": "https://github.com/le-cmyk/Kickstarter-Dashboard"
}



# - Téléchargement des données 

def download_button(data, file_name, button_text):
    csv = data.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    href = f'<a href="data:file/csv;base64,{b64}" download="{file_name}">{button_text}</a>'
    st.markdown(href, unsafe_allow_html=True)

c_1, c_2,c_3 = st.columns(3)
with c_1:
    for clé, link in LIEN.items():
        st.write(f"Made by : [{clé}]({link})")
with c_2:
    for clé, link in SOURCES.items():
        st.write(f"[{clé}]({link})")
with c_3:
    download_button(df, 'data.csv', '📄 Download Sorted Data')



# ---- HIDE STREAMLIT STYLE ----
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)
