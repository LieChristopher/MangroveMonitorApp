import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from calculate_mangrove_data import Mangrove_data
# from calculate_mangrove_data import Mangrove_data

import ee
import geemap.foliumap as gee
import geemap
import google.oauth2 as service_account

st.set_page_config(page_title="Mangrove Monitor App")

# ee.Authenticate()
# ee.Authenticate(project='dogwood-outcome-388110')
# ee.Initialize()
# geemap.ee_initialize()

geemap.ee_initialize()

# def initialize_ee():
#     service_account_info = st.secrets["gee_service_account"]
#     credentials = service_account.Credentials.from_service_account_info(service_account_info)
#     ee.Initialize(credentials)
# initialize_ee()

# st.set_page_config(layout="wide")

# select dropdown
location_codes = [
    'mamberamo_raya','biak_numfor12','sarmi', #Lagoon
    'mappi','asmat', #Delta
    'intersection_MamberamoRaya_Waropen','supiori', #OpenCoast
    'mamberamo_raya1','teluk_bintuni' #Estuary
]

location_names = {
    'mamberamo_raya':'Teba, Kab. Mamberamo Raya',
    'asmat':'Hellwig River, Kab. Asmat',
    'biak_numfor12':'Numfor Island, Kab. Biak Numfor',
    'intersection_MamberamoRaya_Waropen':'Border of Kab. Mamberamo Raya and Kab. Waropen',
    'mamberamo_raya1':'Mamberamo River, Kab. Mamberamo Raya',
    'mappi':'Taroea Anim, Kab. Mappi',
    'sarmi':'Kaptiau, Kab. Sarmi',
    'supiori':'Ineki Island, Kab. Supiori',
    'teluk_bintuni':'Bintuni, Kab. Teluk Bintuni'
}

year_list = ['2016','2017','2018','2019','2020','2021']
model_list = ['01-10']
location_code, year, model = 'mamberamo_raya', '2016', '01-10'
image_name = location_code+'_'+year+'_'+model
user_prefix = 'users/liechristopher7/'

IDR_per_MgC = 75000
USD_to_IDR = 15000
USD_per_MgC = IDR_per_MgC/USD_to_IDR

C_to_CO2 = 44/12

@st.cache_data
def getMangroveData(location, model):
    return Mangrove_data(user_prefix,location,model,year_list)

# Main
st.title ("Web-Based Mangrove Monitoring System for Estimating Carbon Stock in Papua")

col_map, col_info = st.columns([0.6,0.4])
data_area, history_area = st.tabs([':calendar: Current Year',':book: All Years'])
about_area = st.container()

with col_info:
    st.markdown('Control Panel')
    location_name = st.selectbox('Location', list(location_names.values()), index = 0)
    location_code = list(location_names.keys())[list(location_names.values()).index(location_name)]
    year = st.selectbox('Year', year_list, index = 0)
    opacity = st.slider('Opacity', 0.0, 1.0, 0.75)
    view_legend = st.checkbox('View Legend',value = True)
    view_worthington_data = st.checkbox('View 2016 Global Topology of Mangroves (May be slow)')
    if view_worthington_data:
        human_data_opacity = st.slider('Opacity', 0.0, 1.0, 0.4)
    image_name = location_code+'_'+year+'_'+model
    image = ee.Image(user_prefix+image_name)
    mangrove_data_per_year = getMangroveData(location_code,model)

    
with col_map:
    Map = gee.Map(center=[-1.05, 134.95], zoom=0)
    def maskS2clouds(s2_image):
        qa = s2_image.select('QA60')
        cloudBitMask = 1 << 10
        cirrusBitMask = 1 << 11
        mask = qa.bitwiseAnd(cloudBitMask).eq(0).And(qa.bitwiseAnd(cirrusBitMask).eq(0))
        return s2_image.updateMask(mask).divide(10000).copyProperties(s2_image, ["system:time_start"])
    ROI = ee.FeatureCollection('users/liechristopher7/Pulau_Papua')
    ROI = ROI.geometry().convexHull()
    
    year_of_interest = int(year)
    start_date = ee.Date.fromYMD(year_of_interest, 1, 1)
    end_date = ee.Date.fromYMD(year_of_interest, 12, 31)
    image_collection = ee.ImageCollection('COPERNICUS/S2') \
        .filterDate(start_date, end_date) \
        .filterBounds(ROI)
    filtered_image_collection = image_collection \
    .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30)).map(maskS2clouds)
    median_image = filtered_image_collection.median()
    rgb_image = median_image.select(['B2', 'B3', 'B4'])

    if view_legend:
        Map.add_legend(legend_dict=mangrove_data_per_year.legend_dict)

    Map.addLayer(rgb_image, {
        'min': 0.0,
        'max': 1.0/3,
        'bands': ['B4', 'B3', 'B2']}, 'RGB Image')
    Map.addLayer(image, {
        'min': 0,
        'max': len(mangrove_data_per_year.class_list)-1,
        'palette': [mangrove_data_per_year.legend_dict.get(c) for c in mangrove_data_per_year.class_list]}, opacity = opacity, name=image_name)
    
    if view_worthington_data:
        papua_mangrove = ee.FeatureCollection('users/davidelomeo/lomeo_and_singh_2022/mangrove_typology_2016').filterBounds(image.geometry())
        
        legend_dict = {}
        for class_name, color in mangrove_data_per_year.legend_dict.items():
            legend_dict[class_name] = {'color': color, 'width':3}
        mangrove_styles = ee.Dictionary(legend_dict)
        papua_mangrove = papua_mangrove.map(
            lambda feature: feature.set('style', mangrove_styles.get(feature.get('Class')))
        )
        papua_mangrove = papua_mangrove.style(styleProperty='style',)
        Map.addLayer(papua_mangrove, 
        opacity = human_data_opacity, name='Mangrove Typology 2016')
        

    Map.center_object(image)
    Map.to_streamlit(height = 400)
    latlon = image.geometry().centroid().coordinates().getInfo()
    st.caption(f'{latlon[0]}, {latlon[1]}')
    st.caption(f'{mangrove_data_per_year.pixel_dimensions[0]}px x {mangrove_data_per_year.pixel_dimensions[1]}px')

year_idx = year_list.index(year)





with data_area:
    st.header("Mangrove Carbon Stock Information for " + location_name + " in " + year)
    st.markdown(f"In {year}, the approximated amount of carbon stock found in mangroves at the selected area in {location_name} is")
    current_year_mean = mangrove_data_per_year.total_mean_carbon_per_year[year_idx]
    current_year_stddev = mangrove_data_per_year.total_stddev_carbon_per_year[year_idx]
    st.latex(f"{current_year_mean:,.4f} ± {current_year_stddev:,.4f} MgC")
    valuation_USD_mean = current_year_mean*(C_to_CO2)*USD_per_MgC
    valuation_USD_stddev = current_year_stddev*(C_to_CO2)*USD_per_MgC
    valuation_IDR_mean = valuation_USD_mean*IDR_per_MgC
    valuation_IDR_stddev = valuation_USD_stddev*IDR_per_MgC
    
    st.markdown(f" which, at a rate of USD {USD_per_MgC:.2f} / MgC and a conversion factor from C to CO2e of (44/12), there is approximately a CO2 valuation in USD of")
    st.latex(f"USD {valuation_USD_mean:,.2f} ± {valuation_USD_stddev:,.2f}")
    st.markdown(f"Assuming a USD/IDR exchange rate of {USD_to_IDR}, there is approximately a CO2 valuation in IDR of")
    st.latex(f"IDR {valuation_IDR_mean:,.2f} ± {valuation_IDR_stddev:,.2f}")
    
    st.subheader("Predicted Carbon Stock by Class")
    fig_carbon_per_class_year = go.Figure(data=go.Bar(
        x = mangrove_data_per_year.class_list[:mangrove_data_per_year.size_mangroves],
        y = list(map(lambda x: mangrove_data_per_year.mean_carbon_per_class_year[x][year_idx],
                mangrove_data_per_year.class_list[:mangrove_data_per_year.size_mangroves])) ,
        error_y = dict(
            type = 'data',
            array = list(map(lambda x: mangrove_data_per_year.stddev_carbon_per_class_year[x][year_idx],
                mangrove_data_per_year.class_list[:mangrove_data_per_year.size_mangroves])),
            visible = True)
    ))
    fig_carbon_per_class_year.update_layout(
        xaxis_title = "Mangrove Category",
        yaxis_title = "Amount of Carbon (Megagrams of Carbon)"
    )
    st.plotly_chart(fig_carbon_per_class_year)

    st.dataframe(pd.DataFrame({
        'Category': mangrove_data_per_year.class_list[:mangrove_data_per_year.size_mangroves],
        'Mean': [mangrove_data_per_year.mean_carbon_per_class_year[class_name][year_idx] for class_name in mangrove_data_per_year.class_list[:mangrove_data_per_year.size_mangroves]],
        'Standard Deviation': [mangrove_data_per_year.stddev_carbon_per_class_year[class_name][year_idx] for class_name in mangrove_data_per_year.class_list[:mangrove_data_per_year.size_mangroves]]
        }))

    st.subheader("Predicted Area Coverage by Land Cover Type")
    fig_lct_per_class_year = go.Figure(data = [ go.Pie(
            labels = [f'{name}: {mangrove_data_per_year.areaSqM_per_class_year[name][year_idx]:.4f} m^2'
                      for name in mangrove_data_per_year.class_list],
            values = [mangrove_data_per_year.areaSqM_per_class_year[name][year_idx]
                      for name in mangrove_data_per_year.class_list]
        )])
    fig_lct_per_class_year.update_traces(
        hoverinfo = 'label+value',
        textinfo = 'percent',
        textfont_size = 18,
        marker = dict(
            colors = list(map(lambda x: mangrove_data_per_year.legend_dict[x], mangrove_data_per_year.class_list))
        ))
    fig_lct_per_class_year.update_layout(
        xaxis_title = "Mangrove Category",
        yaxis_title = "Mg C (Megagram of Carbon)"
    )

    data_area.plotly_chart(fig_lct_per_class_year)





with history_area:
    st.header(f"Mangrove Carbon Stock Data for {location_name}")

    st.subheader("Predicted Carbon Valuation by Year")
    valuation_history_IDR_mean = []
    valuation_history_IDR_stddev = []
    valuation_history_USD_mean = []
    valuation_history_USD_stddev = []
    for x in range(len(mangrove_data_per_year.year_list)):
        temp_mean = mangrove_data_per_year.total_mean_carbon_per_year[x]
        temp_stddev = mangrove_data_per_year.total_stddev_carbon_per_year[x]
        valuation_history_IDR_mean.append(temp_mean*IDR_per_MgC*C_to_CO2)
        valuation_history_IDR_stddev.append(temp_stddev*IDR_per_MgC*C_to_CO2)
        valuation_history_USD_mean.append(temp_mean*USD_per_MgC*C_to_CO2)
        valuation_history_USD_stddev.append(temp_stddev*USD_per_MgC*C_to_CO2)
    
    fig_valuation_per_year = make_subplots(specs=[[{"secondary_y": True}]])
    text = [f'{mangrove_data_per_year.year_list[x]}'
        + "<br>"
        + f"IDR {valuation_history_IDR_mean[x]:,.2f} ± {valuation_history_IDR_stddev[x]:,.2f}"
        + "<br>"
        + f"USD {valuation_history_USD_mean[x]:,.2f} ± {valuation_history_USD_stddev[x]:,.2f}"
        for x in range(len(mangrove_data_per_year.year_list))]
    fig_valuation_per_year.add_trace(
        go.Scatter(
            x = mangrove_data_per_year.year_list,
            y = valuation_history_USD_mean,
            error_y = dict(
                type = 'data',
                array = valuation_history_USD_stddev),
            text = text,
            name = "USD",
            visible = True
        ),
        secondary_y = True,
        )
    fig_valuation_per_year.add_trace(go.Scatter(
        x = mangrove_data_per_year.year_list,
        y = valuation_history_IDR_mean,
        error_y = dict(
            type = 'data',
            array = valuation_history_IDR_stddev,
            visible = True),
        text = text,
        name = "IDR",
        hoverinfo="text",
        ),
        secondary_y = False)
    
    fig_valuation_per_year.update_xaxes(
        title_text = "Year"
    )
    fig_valuation_per_year.update_yaxes(
        title_text = "Carbon Valuation (IDR)",
        secondary_y = False
    )
    fig_valuation_per_year.update_yaxes(
        title_text = "Carbon Valuation (USD)",
        secondary_y = True,
    )
    # fig_valuation_per_year.update_traces(visible='legendonly',
    #               selector=dict(name="USD"))

    st.plotly_chart(fig_valuation_per_year)

    df = pd.DataFrame({
        "Year":mangrove_data_per_year.year_list,
        "IDR":[f"IDR {valuation_history_IDR_mean[x]:,.2f}±{valuation_history_IDR_stddev[x]:,.2f}"
               for x in range(len(mangrove_data_per_year.year_list))],
        "USD":[f"USD {valuation_history_USD_mean[x]:,.2f}±{valuation_history_USD_stddev[x]:,.2f}"
               for x in range(len(mangrove_data_per_year.year_list))],
    })
    st.caption("Predicted Carbon Valuation by Year")
    st.dataframe(df)


    st.subheader("Predicted Total Carbon Stock and Contribution by Mangrove Class by Year")
    fig_carbon_bar = go.Figure()
    for i in range(mangrove_data_per_year.size_mangroves):
        class_name = mangrove_data_per_year.class_list[i]
        fig_carbon_bar.add_trace(go.Bar(
            x = mangrove_data_per_year.year_list,
            y = mangrove_data_per_year.mean_carbon_per_class_year[class_name],
            name = class_name,
            marker = dict(
                color = '#'+mangrove_data_per_year.legend_dict[class_name]
            )
            ),
            )
    fig_carbon_bar.update_layout(
        xaxis_title = "Year",
        yaxis_title = "Mg C (Megagram of Carbon)"
    )
    fig_carbon_bar.add_trace(go.Scatter(
        x = mangrove_data_per_year.year_list,
        y = mangrove_data_per_year.total_mean_carbon_per_year,
        name = 'Mean ± Standard Deviation',
        error_y = dict(type = 'data', array = mangrove_data_per_year.total_stddev_carbon_per_year)),
        )
    fig_carbon_bar.update_layout(barmode = 'stack')
    fig_carbon_bar.update_xaxes(categoryorder = 'category ascending')
    st.plotly_chart(fig_carbon_bar)

    df = {}
    for year_temp_idx in range(len(mangrove_data_per_year.year_list)):
        temp = {}
        _total = [0,0]
        for class_name in mangrove_data_per_year.class_list[:mangrove_data_per_year.size_mangroves]:
            temp[class_name] = f'{mangrove_data_per_year.mean_carbon_per_class_year[class_name][year_temp_idx]:.4f} ± {mangrove_data_per_year.stddev_carbon_per_class_year[class_name][year_temp_idx]:.4f}'
            _total[0] = _total[0] + mangrove_data_per_year.mean_carbon_per_class_year[class_name][year_temp_idx]
            _total[1] = _total[1] + mangrove_data_per_year.stddev_carbon_per_class_year[class_name][year_temp_idx]
        temp['Total'] = f'{_total[0]:.4f} ± {_total[1]:.4f}'
        df[mangrove_data_per_year.year_list[year_temp_idx]] = temp
    st.caption("Predicted Carbon Stock in Megagrams of Carbon (MgC) by Mangrove Class by Year")
    st.dataframe(pd.DataFrame(df))


    st.subheader("Predicted Area Coverage by Land Cover Type by Year")
    fig_lct_bar = go.Figure()
    for class_name in mangrove_data_per_year.class_list:
        fig_lct_bar.add_trace(go.Bar(
            x = mangrove_data_per_year.year_list,
            y = mangrove_data_per_year.areaSqM_per_class_year[class_name], name=class_name,
            marker = dict(
                color = '#'+mangrove_data_per_year.legend_dict[class_name]
            )))
    fig_lct_bar.update_layout(
        barmode = 'stack',
        xaxis_title = "Year",
        yaxis_title = "Area (square meters)"
    )
    # fig_lct_bar.update_traces(
    #     # hoverinfo = 'label+value',
    #     text = '',
    #     textfont_size = 18,)
    st.plotly_chart(fig_lct_bar)


    df = {}
    for year_temp_idx in range(len(mangrove_data_per_year.year_list)):
        temp = {}
        for class_name in mangrove_data_per_year.class_list:
            temp[class_name] = mangrove_data_per_year.areaSqM_per_class_year[class_name][year_temp_idx]
        df[mangrove_data_per_year.year_list[year_temp_idx]] = temp
    df = pd.DataFrame(df)
    st.caption("Predicted Area Coverage by Class in Square Meters")
    st.table(df)

    ndf = {}
    for _year in mangrove_data_per_year.year_list:
        ndf[_year] = (df[_year] / df[_year].sum()) * 100
    st.caption("Predicted Area Coverage by Class in Percentage of Total Area")
    st.table(ndf)





about_area.write("About this app")
about_area.caption("This Streamlit App is used to display mangrove carbon stock information in Papua, one of the regions with the largest mangrove carbon stock globally.")
about_area.caption("The carbon stock is approximated using predicted mangrove coverage in an area and the average carbon stock data by Sasmito, et. al.")
about_area.caption("The mangrove coverage is predicted using a Deep Learning U-Net model designed by Lomeo and Singh based on Ronneberger et. al. trained on Sentinel-2 satellite images and mangrove categorization data by Worthington, et. al.")
about_area.caption("The web app is created by Christopher from BINUS University, Indonesia to fulfill his undergraduate program graduation requirements.")
