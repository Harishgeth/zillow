import dash as dash
import numpy as np
from dash import dcc
from dash import html
from dash.dependencies import Input, Output
import pandas as pd
import gc
import plotly.express as px
from urllib.request import urlopen
import json

with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
    counties = json.load(response)

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css', 'assets/custom.css']
# external_stylesheets = [dbc.themes.BOOTSTRAP]
external_scripts = ["https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.5/MathJax.js?config=TeX-MML-AM_CHTML"]

outer_div_style = {}
tab_style = {
    "color": "white",
    "background-color": "#006AFF"
}

### Data loading and preproc
df = pd.read_pickle("../processed/sold_houses_no_outlier.pkl")

xls = pd.ExcelFile('../zillow_data_dictionary.xlsx')
type_resolve_dictionary = {}
HeatingOrSystemTypeID = pd.read_excel(xls, 'HeatingOrSystemTypeID')
HeatingOrSystemTypeIDdict = dict(
    zip(HeatingOrSystemTypeID.HeatingOrSystemTypeID, HeatingOrSystemTypeID.HeatingOrSystemDesc))
type_resolve_dictionary['heatingorsystemtypeid'] = HeatingOrSystemTypeIDdict

PropertyLandUseTypeID = pd.read_excel(xls, 'PropertyLandUseTypeID')
PropertyLandUseTypeIDdict = dict(
    zip(PropertyLandUseTypeID.PropertyLandUseTypeID, PropertyLandUseTypeID.PropertyLandUseDesc))
type_resolve_dictionary['propertylandusetypeid'] = PropertyLandUseTypeIDdict

StoryTypeID = pd.read_excel(xls, 'StoryTypeID')
StoryTypeIDdict = dict(zip(StoryTypeID.StoryTypeID, StoryTypeID.StoryDesc))
type_resolve_dictionary['storytypeid'] = StoryTypeIDdict

AirConditioningTypeID = pd.read_excel(xls, 'AirConditioningTypeID')
AirConditioningTypeIDdict = dict(
    zip(AirConditioningTypeID.AirConditioningTypeID, AirConditioningTypeID.AirConditioningDesc))
type_resolve_dictionary['airconditioningtypeid'] = AirConditioningTypeIDdict

ArchitecturalStyleTypeID = pd.read_excel(xls, 'ArchitecturalStyleTypeID')
ArchitecturalStyleTypeIDdict = dict(
    zip(ArchitecturalStyleTypeID.ArchitecturalStyleTypeID, ArchitecturalStyleTypeID.ArchitecturalStyleDesc))
type_resolve_dictionary['architecturalstyletypeid'] = ArchitecturalStyleTypeIDdict

TypeConstructionTypeID = pd.read_excel(xls, 'TypeConstructionTypeID')
TypeConstructionTypeIDdict = dict(
    zip(TypeConstructionTypeID.TypeConstructionTypeID, TypeConstructionTypeID.TypeConstructionDesc))
type_resolve_dictionary['typeconstructiontypeid'] = TypeConstructionTypeIDdict

BuildingClassTypeID = pd.read_excel(xls, 'BuildingClassTypeID')
BuildingClassTypeIDdict = dict(zip(BuildingClassTypeID.BuildingClassTypeID, BuildingClassTypeID.BuildingClassDesc))
type_resolve_dictionary['buildingclasstypeid'] = BuildingClassTypeIDdict

categorical_cols = ['heatingorsystemtypeid', 'propertylandusetypeid', 'storytypeid', 'airconditioningtypeid',
                    'architecturalstyletypeid', 'typeconstructiontypeid', 'buildingclasstypeid']
years_of_relevance = ['yearbuilt']
binary_cols = ['fireplaceflag', 'taxdelinquencyflag', 'hashottuborspa']
count_cols = ['numberofstories', 'unitcnt', 'roomcnt', 'poolcnt', 'bathroomcnt', 'bedroomcnt', 'fireplacecnt']
rating_cols = ['buildingqualitytypeid']
location_cols = ['fips']
metric_cols = ['calculatedfinishedsquarefeet', 'taxvaluedollarcnt']
luxury_metrics_cols = ['poolsizesum']
id_col = ['parcelid']

my_app = dash.Dash('Dashapp')

my_app.layout = html.Div([
                            html.Div([
                                html.Div([
                                    html.Img(src=r'assets/zillow.svg', alt='image', className="site-logo"),
                                    html.Span('Z-Explanatory Data Visualization', className="zexp-header"),
                                    html.Div([
                                        html.Span("Built for Information Visualization Class(VT)"),
                                        html.Span("Harish Ravi"),
                                        html.Span("harishr@vt.edu")
                                    ], className="course-specifics")
                                ], style={'display': 'flex'}),
                                html.Br(),
                                html.Div([
                                    html.Strong("PRELUDE:"),
                                    html.Div(className="hl"),
                                    html.Span(
                                        "This dashboard is an opinionated visualization of Zillow's Zestimate dataset. It serves to explain the valuation of properties when analyzed through the lens of a homeowner. It's to be noted that, the dataset contains data for only three Californian counties, so the applicability of these insights is limited and only the sold houses of 2016-17 were considered here! But considering the richness of the data, and its origin from the real world, so we hope to Z-Explain the data, by slicing-dicing and plotting with and on some opinionated variables."),
                                    html.A(children="DATA SOURCE", href="https://www.kaggle.com/competitions/zillow-prize-1/overview")
                                ], className="intermediate-text"),
                                html.Br(),
                                dcc.Tabs(id='zillow_tabs',
                                         children=[
                                             dcc.Tab(label='Pricepoint/Area by Amenities', value='opt1'),
                                             dcc.Tab(label='Amenities for Pricepoint/Area', value='opt2'),
                                             dcc.Tab(label='Aggregations', value='opt3'),
                                         ], value='opt1'),
                                html.Br(),
                                html.Div(id='layout'),
                            ], style=outer_div_style, className="outer-div"),
                            html.Div([
                                html.Strong("ヽ(•‿•)ノ")
                            ], id="footer")
                           ],

)

fips_map = {
    '06111': 'Ventura County',
    '06037': 'Los Angeles County',
    '06059': 'Orange County'
}
type_resolve_dictionary['fips'] = fips_map


def tab1Layout():
    pool_map = {
        1: "Available",
        0: "Not-Available"
    }
    min_bed_rooms = df.bedroomcnt.unique().min()
    max_bed_rooms = df.bedroomcnt.unique().max()
    tab1layout = html.Div([
        html.Div([
            html.Span(
                children="This tab allows you to filter houses by key criteria, and visualize the price spread and Square footage spread, It also comes with a handy tool to understand how the filtered distribution pans out by counties",
            ),
        ], className="description-text-t1"),

        html.Div([
            html.Span(children="Select a County:", className="sli-label"),
            dcc.Dropdown(
                id='fips-selection',
                options=[{'label': f"{key} ({item})", 'value': item} for item, key in fips_map.items()],
                className="fips-selector",
                multi=True
            ),

        ], className="selection-line-item"),
        html.Div([
            html.Span(children="Timeline-of-sale", className="sli-label"),
            dcc.DatePickerRange(id="transaction-time-line", min_date_allowed=df.transactiondate.min(),
                                max_date_allowed=df.transactiondate.max(), className="date-picker-ttl"),
        ], className="selection-line-item"),

        html.Div([
            html.Span(children="Has a Pool?", className="sli-label"),
            dcc.Checklist(
                id="pool-checkbox",
                options=[{'label': f"{key}", 'value': item} for item, key in pool_map.items()]
            )

        ], className="selection-line-item"),
        html.Div([
            html.Span(children="Desired Bedrooms Range", className="sli-label"),
            dcc.RangeSlider(id="bedroom-slider", className="slider-range", min=min_bed_rooms, max=max_bed_rooms, step=1,
                            value=[min_bed_rooms, max_bed_rooms]),
        ], className="selection-line-item"),

        html.Div([
            html.Span(children="Toggle the 50 percentile Valuation", className="sli-label"),
            html.Button('Bottom Percentile Price', id='bottom-perc-valuation', n_clicks=0, className="button-59"),
        ], className="selection-line-item"),

        html.Div([
            html.Span(children="Toggle the 50 percentile Area", className="sli-label"),
            html.Button('Bottom Percentile Area', id='bottom-perc-area', n_clicks=0, className="button-59"),

        ], className="selection-line-item"),
        html.Div([
            html.Div([
                html.H2("The Estimated Price of houses sold (with the specified conditions)"),
                dcc.RadioItems(["Histogram", "Boxplot"], "Histogram", inline=True, id="valuation-radio",
                               className="radio-buttons-g"),
                html.Span(id="histogram-err-g1-t1", className="error-message", children=""),
                html.Div([
                    html.Span("Bins:"),
                    dcc.Input(id='histogram-ip-g1-t1', type="number", value=50, className="t1-bins-ip"),
                ], id="histogram-ip-g1-t1-div",className='bins-field'),
                dcc.Graph(id="valuation-graph", className="tab1-graphs"),
            ], className="graph-with-radio-buttons"),
            html.Div([
                html.H2("The Estimated Square Footage of houses sold (with the specified conditions)"),
                dcc.RadioItems(["Histogram", "Boxplot"], "Histogram", inline=True, id="square-radio",
                               className="radio-buttons-g"),
                html.Span(id="histogram-err-g2-t1", className="error-message", children=""),
                html.Div([
                    html.Span("Bins:"),
                    dcc.Input(id='histogram-ip-g2-t1', type="number", value=50, className="t1-bins-ip"),
                ],id="histogram-ip-g2-t1-div",className='bins-field'),
                dcc.Graph(id="square-graph", className="tab1-graphs")
            ], className="graph-with-radio-buttons")
        ], className="plots-tab1"),
        html.H2("Counties with the sale deeds of interest"),
        dcc.Graph(id="chloropleth-t1")
    ])
    return tab1layout


eligible_y = {
    "Valuation": "taxvaluedollarcnt",
    "Footage": "calculatedfinishedsquarefeet",
}
eligible_x = {
    "Building Construction Material": "typeconstructiontypeid",
    "Construction Year": "yearbuilt",
    "Bedroom Count": "bedroomcnt",
    "Room Count": "roomcnt",
    "Counties": "fips",
    "Building Fireproofing Status": "buildingclasstypeid",
    "Architectural Style": "architecturalstyletypeid",
    "FirePlace": "fireplaceflag",
    "Area Zoning": "propertylandusetypeid",
    "Has Hottub": "hashottuborspa",
    "Has Pool": "poolcnt",
    "Heating System": "heatingorsystemtypeid",
    "Story Type": "storytypeid",
    "Air Conditioning": "airconditioningtypeid",
}


def tab2Layout():
    tab2layout = html.Div([
        html.Div([
            html.Span(
                children="We understand the distribution of some categorical/count variables at percentiles of interest. The strategy is to make an informed slice and then dice, to understand valuation at interesting/useful regions.",
            ),
        ], className="description-text-t1"),
        html.Div([
            dcc.Graph(id="area-percentile", className="grouped-box-plot-unit"),
            dcc.Graph(id="valuation-percentile", className="grouped-box-plot-unit")
        ],
            className='grouped-box-plots'),
        html.Div([
            html.Span(children="Valuation Percentile Range", className="sli-label"),
            dcc.RangeSlider(id="percentile-slider-valuation", className="slider-range", min=0, max=100, step=1,
                            marks={i: str(i) for i in range(0, 101, 10)},
                            value=[30, 70]),
        ], className="selection-line-item"),
        html.Div([
            html.Span(children="Square footage Percentile Range", className="sli-label"),
            dcc.RangeSlider(id="percentile-slider-area", className="slider-range", min=0, max=100, step=1,
                            marks={i: str(i) for i in range(0, 101, 10)},
                            value=[30, 70]),
        ], className="selection-line-item"),
        html.Div([
            html.Span(id="area_mean",children=""),
            html.Br(),
            html.Span( id="val_mean",children=""),
        ], className="description-text-t1"),
        html.Div([
            html.H2("Diced Visualization by selected variable"),
            html.P("Select the y axis for the visualization"),
            dcc.Dropdown(
                id='diced-y-selection',
                options=[{'label': key, 'value': item} for key, item in eligible_y.items()],
                className="fips-selector",
                value="taxvaluedollarcnt",
                multi=False
            ),
            html.P("Select the x axis for the visualization"),
            dcc.Dropdown(
                id='diced-x-selection',
                options=[{'label': key, 'value': item} for key, item in eligible_x.items()],
                className="fips-selector",
                value="yearbuilt",
                multi=False
            ),
            dcc.RadioItems(["Violin", "Box"], "Box", inline=True, id="diced-graph-radio-valuation",
                           className="radio-buttons-g"),
            html.Div([
                dcc.Graph(id="diced-graph-valuation", className="tab2-graphs"),
                dcc.Markdown(id="exp-area", dangerously_allow_html=True)
            ], className="graph-expl-t2")

        ], className="graph-with-radio-buttons"),
    ])
    return tab2layout


def tab3Layout():
    min_year = df.yearbuilt.min()
    max_year = df.yearbuilt.max()
    tab3layout = html.Div([
        html.Div([
            html.Span(
                children="When filtered by percentiles of valuation (or) area we got to see the spread of data across various regions of the dependent variables. Now let's plot the aggregate measures of the same metrics with bar and pie plots.",
            ),
        ], className="description-text-t1"),
        html.Div([
            html.Span(children="Valuation Percentile Range", className="sli-label"),
            dcc.RangeSlider(id="percentile-slider-valuation-t3", className="slider-range", min=0, max=100, step=1,
                            marks={i: str(i) for i in range(0, 101, 10)},
                            value=[30, 70]),
        ], className="selection-line-item"),
        html.Div([
            html.Span(children="Square footage Percentile Range", className="sli-label"),
            dcc.RangeSlider(id="percentile-slider-area-t3", className="slider-range", min=0, max=100, step=1,
                            marks={i: str(i) for i in range(0, 101, 10)},
                            value=[30, 70]),
        ], className="selection-line-item"),
        html.Div([
            html.Span(children="Year Built", className="sli-label"),
            dcc.RangeSlider(id="year-built-slider", className="slider-range", min=min_year, max=max_year, step=1,
                            marks={i: str(i) for i in range(min_year, max_year + 20, 20)},
                            value=[2010, max_year]),
        ], className="selection-line-item"),
        html.Div([
            html.H2("Diced Visualization by selected variable"),
            html.P("Select the aggregation column"),
            dcc.Dropdown(
                id='aggregator-col',
                options=[{'label': key, 'value': item} for key, item in eligible_x.items()],
                className="fips-selector",
                value="fips",
                multi=False
            ),
            html.Div([
                dcc.Graph(id="aggregated-pie-valuation", className="tab3-graphs"),
                dcc.Graph(id="aggregated-pie-area", className="tab3-graphs"),
            ], className="graph-expl-t2"),
            html.Div([
                dcc.Graph(id="aggregated-bar-valuation", className="tab3-graphs"),
                dcc.Graph(id="aggregated-bar-area", className="tab3-graphs"),
            ], className="graph-expl-t2"),
            dcc.Markdown(id="exp-area-t3", dangerously_allow_html=True),
            html.Div([
                html.Span(
                    children="Now let's plot square footage versus the valuation as a Scatter plot with trendlines, colored by the aggregator variable.",
                ),
            ], className="description-text-t1"),
            dcc.Graph(id="plot-reg")

        ], className="graph-with-radio-buttons"),
    ])
    return tab3layout


## Plot the tabs
@my_app.callback(
    Output(component_id='layout', component_property='children'),
    Input(component_id='zillow_tabs', component_property='value')
)
def rendertheRightTabs(ques):
    if ques == 'opt1':
        return tab1Layout()
    elif ques == 'opt2':
        return tab2Layout()
    elif ques == 'opt3':
        return tab3Layout()
    return "The impaler"


@my_app.callback(
    Output(component_id="valuation-graph", component_property="figure"),
    Output(component_id="histogram-ip-g1-t1-div", component_property="style"),
    Output(component_id="square-graph", component_property="figure"),
    Output(component_id="histogram-ip-g2-t1-div", component_property="style"),
    Output(component_id="chloropleth-t1", component_property="figure"),

    Input(component_id="fips-selection", component_property="value"),
    Input(component_id="valuation-radio", component_property="value"),
    Input(component_id="square-radio", component_property="value"),
    Input(component_id="pool-checkbox", component_property="value"),
    Input(component_id="transaction-time-line", component_property="start_date"),
    Input(component_id="transaction-time-line", component_property="end_date"),
    [Input('bedroom-slider', 'value')],
    Input(component_id="bottom-perc-valuation", component_property="n_clicks"),
    Input(component_id="bottom-perc-area", component_property="n_clicks"),
    Input(component_id="histogram-ip-g1-t1", component_property="value"),
    Input(component_id="histogram-ip-g2-t1", component_property="value")
)
def valuationPieByFilters(fips_selection, valuation_radio_opt, square_radio_opt, pools_selection, start_date, end_date,
                          bed_rooms, bot_perc_val, bot_perc_area, bins_g1, bins_g2):
    query_df = df
    print(bed_rooms)
    fig1 = None
    fig2 = None
    dispblockfig1 = None
    dispblockfig2 = None

    if start_date is not None:
        query_df = query_df.query("transactiondate>=@start_date")
    if end_date is not None:
        query_df = query_df.query("transactiondate<=@end_date")
    if fips_selection is not None:
        if fips_selection != []:
            query_df = query_df.query("fips == @fips_selection")
    if pools_selection is not None:
        if pools_selection != []:
            query_df = query_df.query("poolcnt == @pools_selection")
    if bed_rooms is not None:
        if len(bed_rooms) == 2:
            query_df = query_df.query("bedroomcnt>=@bed_rooms[0]")
            query_df = query_df.query("bedroomcnt<=@bed_rooms[1]")
    if bot_perc_val % 2 != 0:
        bottom_50_percentile_pricepoint = df.taxvaluedollarcnt.quantile(.50)
        query_df = query_df.query("taxvaluedollarcnt<=@bottom_50_percentile_pricepoint")
    if bot_perc_area % 2 != 0:
        bottom_50_percentile_area = df.calculatedfinishedsquarefeet.quantile(.50)
        query_df = query_df.query("calculatedfinishedsquarefeet<=@bottom_50_percentile_area")
    if valuation_radio_opt == "Histogram":
        fig1 = px.histogram(query_df, x="taxvaluedollarcnt", nbins=bins_g1,
                            labels=dict(taxvaluedollarcnt="Price Estimate($)", count="Units Sold"))
        dispblockfig1 = {'display': 'block'}
    else:
        fig1 = px.box(query_df, x="taxvaluedollarcnt", labels=dict(taxvaluedollarcnt="Price Estimate($)"))
        dispblockfig1 = {'display': 'none'}

    if square_radio_opt == "Histogram":
        fig2 = px.histogram(query_df, x="calculatedfinishedsquarefeet", nbins=bins_g2,
                            labels=dict(calculatedfinishedsquarefeet="Square Footage", count="Units Sold"))
        dispblockfig2 = {'display': 'block'}
    else:
        fig2 = px.box(query_df, x="calculatedfinishedsquarefeet",
                      labels=dict(calculatedfinishedsquarefeet="Square Footage"))
        dispblockfig2 = {'display': 'none'}

    fips_summary = query_df.groupby(['fips']).size().reset_index(name='dist')

    fig3 = px.choropleth(fips_summary, geojson=counties, locations='fips', color='dist',
                         color_continuous_scale="Viridis",
                         range_color=(fips_summary.dist.min(), fips_summary.dist.max()),
                         scope="usa",
                         labels={'dist': 'Units sold by county'}
                         )

    return fig1, dispblockfig1, fig2, dispblockfig2, fig3



@my_app.callback(
    Output(component_id="area-percentile", component_property="figure"),
    Output(component_id="valuation-percentile", component_property="figure"),
    Output(component_id="diced-graph-valuation", component_property="figure"),
    Output(component_id="exp-area", component_property="children"),
    Output(component_id="area_mean", component_property="children"),
    Output(component_id="val_mean", component_property="children"),
    Input(component_id="diced-graph-radio-valuation", component_property="value"),
    Input(component_id="diced-x-selection", component_property="value"),
    Input(component_id="diced-y-selection", component_property="value"),
    [Input('percentile-slider-area', 'value')],
    [Input('percentile-slider-valuation', 'value')],

)
def plotQuartileAfterSlicingDicing(graph3_type, x_selection, y_selection, area_percentiles, valuation_percentiles):
    area_percentile_min = 0
    area_percentile_max = 0

    valuation_percentile_min = 0
    valuation_percentile_max = 0
    query_df = df

    if area_percentiles is not None:
        if len(area_percentiles) == 2:
            area_percentile_min = df.calculatedfinishedsquarefeet.quantile(float(area_percentiles[0]) / 100.0)
            area_percentile_max = df.calculatedfinishedsquarefeet.quantile(float(area_percentiles[1]) / 100.0)
            query_df = query_df.query("calculatedfinishedsquarefeet<=@area_percentile_max")
            query_df = query_df.query("calculatedfinishedsquarefeet>=@area_percentile_min")
    if valuation_percentiles is not None:
        if len(valuation_percentiles) == 2:
            valuation_percentile_min = df.taxvaluedollarcnt.quantile(float(valuation_percentiles[0]) / 100.0)
            valuation_percentile_max = df.taxvaluedollarcnt.quantile(float(valuation_percentiles[1]) / 100.0)
            query_df = query_df.query("taxvaluedollarcnt<=@valuation_percentile_max")
            query_df = query_df.query("taxvaluedollarcnt>=@valuation_percentile_min")

    fig1 = px.box(query_df, x='calculatedfinishedsquarefeet')
    fig2 = px.box(query_df, x='taxvaluedollarcnt')
    if graph3_type == "Box":
        fig3 = px.box(query_df, y=y_selection, x=x_selection)
    else:
        fig3 = px.violin(query_df, y=y_selection, x=x_selection)
    explanation_of_vars = ""
    if x_selection in type_resolve_dictionary:
        explanation_of_vars = f"<b>Metadata for the x-axis variable {x_selection}</b> <br/><br/>"
        for key, val in type_resolve_dictionary[x_selection].items():
            explanation_of_vars = explanation_of_vars + str(key) + "\t" + val + "<br/>"
    mean_str_area=f"The Mean Square footage for the filtered data {query_df.calculatedfinishedsquarefeet.mean():.2f}"
    mean_str_val=f"The Mean Valuation for the filtered data is ${query_df.taxvaluedollarcnt.mean():.2f} "
    return fig1, fig2, fig3, explanation_of_vars,mean_str_area,mean_str_val


#     dcc.Graph(id="aggregated-pie-valuation", className="tab3-graphs"),
#     dcc.Graph(id="aggregated-pie-area", className="tab3-graphs"),
#
# ], className = "graph-expl-t2"),
# html.Div([
# dcc.Graph(id="aggregated-bar-footage", className="tab3-graphs"),
# dcc.Graph(id="aggregated-bar-area", className="tab3-graphs"),
# dcc.Graph(id="plot-reg")

@my_app.callback(
    Output(component_id="aggregated-pie-valuation", component_property="figure"),
    Output(component_id="aggregated-pie-area", component_property="figure"),
    Output(component_id="aggregated-bar-valuation", component_property="figure"),
    Output(component_id="aggregated-bar-area", component_property="figure"),
    Output(component_id="plot-reg", component_property="figure"),
    Output(component_id="exp-area-t3", component_property="children"),
    Output(component_id="exp-area-t3", component_property="style"),
    Input(component_id="aggregator-col", component_property="value"),
    [Input('percentile-slider-area-t3', 'value')],
    [Input('percentile-slider-valuation-t3', 'value')],
    [Input('year-built-slider', 'value')],
)
def plotAggregatedMetrics(agg_col, area_percentiles, valuation_percentiles, year_built_range):
    query_df = df

    if area_percentiles is not None:
        if len(area_percentiles) == 2:
            area_percentile_min = df.calculatedfinishedsquarefeet.quantile(float(area_percentiles[0]) / 100.0)
            area_percentile_max = df.calculatedfinishedsquarefeet.quantile(float(area_percentiles[1]) / 100.0)
            query_df = query_df.query("calculatedfinishedsquarefeet<=@area_percentile_max")
            query_df = query_df.query("calculatedfinishedsquarefeet>=@area_percentile_min")
    if valuation_percentiles is not None:
        if len(valuation_percentiles) == 2:
            valuation_percentile_min = df.taxvaluedollarcnt.quantile(float(valuation_percentiles[0]) / 100.0)
            valuation_percentile_max = df.taxvaluedollarcnt.quantile(float(valuation_percentiles[1]) / 100.0)
            query_df = query_df.query("taxvaluedollarcnt<=@valuation_percentile_max")
            query_df = query_df.query("taxvaluedollarcnt>=@valuation_percentile_min")

    if year_built_range is not None:
        if len(year_built_range) == 2:
            query_df = query_df.query("yearbuilt<=@year_built_range[1]")
            query_df = query_df.query("yearbuilt>=@year_built_range[0]")

    fig1 = px.pie(query_df, values='taxvaluedollarcnt', names=agg_col,
                  title=f"Pie plot of taxvaluedollarcnt exploded by {agg_col}")
    fig2 = px.pie(query_df, values='calculatedfinishedsquarefeet', names=agg_col,
                  title=f"Pie plot of calculatedfinishedsquarefeet exploded by {agg_col}")
    explanation_of_vars = ""

    agged_data_sqft = query_df.groupby(agg_col).mean()['calculatedfinishedsquarefeet'].reset_index()
    agged_data_val = query_df.groupby(agg_col).mean()['taxvaluedollarcnt'].reset_index()
    fig3 = px.bar(agged_data_sqft, x=agg_col, y='calculatedfinishedsquarefeet',
                  title=f"Bar plot of {agg_col} vs Avg. calculatedfinishedsquarefeet")
    fig4 = px.bar(agged_data_val, x=agg_col, y='taxvaluedollarcnt',
                  title=f"Bar plot of {agg_col} vs Avg. taxvaluedollarcnt")

    style_exp = {"background": "white"}
    if agg_col in type_resolve_dictionary:
        explanation_of_vars = f"<b>Metadata for variable {agg_col}</b> <br/><br/>"
        style_exp = {}
        for key, val in type_resolve_dictionary[agg_col].items():
            explanation_of_vars = explanation_of_vars + str(key) + "\t" + val + "<br/>"

    fig5 = px.scatter(query_df, x='taxvaluedollarcnt', y='calculatedfinishedsquarefeet', color=agg_col, trendline="ols",
                      title=f"Plot of Square footage vs Tax Valuation with ({agg_col} hue)")
    return fig1, fig2, fig3, fig4, fig5, explanation_of_vars, style_exp


my_app.server.run(port=8020, host='0.0.0.0')
