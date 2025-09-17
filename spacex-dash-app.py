# Import required libraries
import pandas as pd
import dash
from dash import html, dcc
from dash.dependencies import Input, Output
import plotly.express as px

# ===== Read the SpaceX launch data =====
spacex_df = pd.read_csv("spacex_launch_dash.csv")

# Handle column-name variants defensively
site_col = 'Launch Site' if 'Launch Site' in spacex_df.columns else 'LaunchSite'
payload_col = (
    'Payload Mass (kg)' if 'Payload Mass (kg)' in spacex_df.columns else
    ('PayloadMass' if 'PayloadMass' in spacex_df.columns else
     ('PayloadMassKg' if 'PayloadMassKg' in spacex_df.columns else None))
)
booster_col = 'Booster Version Category' if 'Booster Version Category' in spacex_df.columns else 'BoosterVersionCategory'

if payload_col is None:
    raise ValueError(
        "Couldn't find a payload column (e.g., 'Payload Mass (kg)') in the CSV. "
        f"Available columns: {list(spacex_df.columns)}"
    )

# Compute payload slider bounds from data
max_payload = spacex_df[payload_col].max()
min_payload = spacex_df[payload_col].min()

# ===== Create a dash application =====
app = dash.Dash(__name__)

# ===== App layout (Tasks 1 & 3 UI components included) =====
app.layout = html.Div(children=[
    html.H1(
        'SpaceX Launch Records Dashboard',
        style={'textAlign': 'center', 'color': '#503D36', 'font-size': 40}
    ),

    # TASK 1: Launch Site dropdown
    dcc.Dropdown(
        id='site-dropdown',
        options=[{'label': 'All Sites', 'value': 'ALL'}] +
                [{'label': s, 'value': s} for s in sorted(spacex_df[site_col].unique())],
        value='ALL',
        placeholder="Select a Launch Site here",
        searchable=True
    ),

    html.Br(),

    # TASK 2: Pie chart (success counts)
    html.Div(dcc.Graph(id='success-pie-chart')),
    html.Br(),

    html.P("Payload range (Kg):"),

    # TASK 3: Payload range slider
    dcc.RangeSlider(
        id='payload-slider',
        min=float(min_payload),
        max=float(max_payload),
        step=1000,
        value=[float(min_payload), float(max_payload)],
        marks={
            int(min_payload): str(int(min_payload)),
            int((min_payload + max_payload) / 2): str(int((min_payload + max_payload) / 2)),
            int(max_payload): str(int(max_payload))
        },
        allowCross=False
    ),

    html.Br(),

    # TASK 4: Scatter chart (payload vs class, colored by booster)
    html.Div(dcc.Graph(id='success-payload-scatter-chart')),
])

# ===== TASK 2: Pie chart callback =====
# - If ALL: show total successful launches by site (class == 1)
# - Else: show Success (1) vs Failure (0) for the selected site
@app.callback(
    Output(component_id='success-pie-chart', component_property='figure'),
    Input(component_id='site-dropdown', component_property='value')
)
def get_pie_chart(entered_site):
    if entered_site == 'ALL':
        df_success = spacex_df[spacex_df['class'] == 1]
        fig = px.pie(
            df_success,
            names=site_col,
            title='Total Successful Launches by Site'
        )
        return fig
    else:
        df_site = spacex_df[spacex_df[site_col] == entered_site]
        outcome_counts = (
            df_site['class']
            .value_counts()
            .rename_axis('Outcome')  # 0/1
            .reset_index(name='Count')
        )
        outcome_counts['Outcome'] = outcome_counts['Outcome'].map({1: 'Success (1)', 0: 'Failure (0)'})
        fig = px.pie(
            outcome_counts,
            names='Outcome',
            values='Count',
            title=f'Launch Outcomes for {entered_site}'
        )
        return fig

# ===== TASK 4: Scatter plot callback =====
# Inputs: site dropdown + payload slider
# Output: scatter of payload vs class, colored by booster version
@app.callback(
    Output(component_id='success-payload-scatter-chart', component_property='figure'),
    [
        Input(component_id='site-dropdown', component_property='value'),
        Input(component_id='payload-slider', component_property='value')
    ]
)
def update_scatter(selected_site, payload_range):
    low, high = payload_range

    # Filter by payload range
    mask = (spacex_df[payload_col] >= low) & (spacex_df[payload_col] <= high)
    dff = spacex_df[mask].copy()

    title_suffix = "All Sites"
    if selected_site != 'ALL':
        dff = dff[dff[site_col] == selected_site]
        title_suffix = selected_site

    fig = px.scatter(
        dff,
        x=payload_col,
        y='class',
        color=booster_col,
        hover_data=[site_col],
        title=f"Payload vs. Launch Outcome (0/1) — {title_suffix}"
    )
    fig.update_yaxes(tickmode="array", tickvals=[0, 1], title="Launch Outcome (class)")
    fig.update_xaxes(title="Payload Mass (kg)")
    return fig

# ===== Run the app =====
if __name__ == '__main__':
    app.run()
