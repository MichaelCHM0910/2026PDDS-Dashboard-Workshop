# Library Setup
from dash import Dash, html, dcc, Input, Output
import plotly.express as px
import pandas as pd

# Import functions from db_service.py
from services.db_service import get_rush_hours_data, get_day_counts

# Initialize Dash Application
app = Dash(__name__)
server = app.server  # Required for deployment (gunicorn app:server)

# Fetching data via db_service
# df: one row per hour_of_day x channel x day_type, with total_order
# day_counts: how many calendar days of each day_type are in the data
df = get_rush_hours_data()
day_counts = get_day_counts().set_index("day_type")["n_days"]


# Create Plotly Visualization
# Builds the grouped bar chart for one day filter and one metric.
def build_figure(day_type: str, metric: str):
    # 1. Keep only the rows for the chosen day type ("All" keeps everything)
    dff = df if day_type == "All" else df[df["day_type"] == day_type]

    # 2. Add Weekday + Weekend rows together, so each hour x channel is one bar
    dff = dff.groupby(["hour_of_day", "channel"], as_index=False)["total_order"].sum()

    # 3. Denominator: number of days covered by this filter
    n_days = int(day_counts.sum() if day_type == "All" else day_counts[day_type])

    # 4. Choose the metric shown on the y-axis
    if metric == "avg":
        dff["value"] = (dff["total_order"] / n_days).round(2)
        y_label = "Average Orders per Day"
    else:
        dff["value"] = dff["total_order"]
        y_label = "Total Orders (All Recorded Days)"

    fig = px.bar(
        dff,
        x="hour_of_day",
        y="value",
        color="channel",
        barmode="group",
        title=f"Orders by Hour & Channel · {day_type} · {n_days} days (21 Sep–1 Nov 2026)",
        labels={
            "hour_of_day": "Clock Hour of Day",
            "value": y_label,
            "channel": "Sales Channel",
        },
        hover_data={"total_order": True},
    )
    return fig, dff, n_days


# App Layout
app.layout = html.Div(
    style={"padding": "30px", "fontFamily": "Arial, sans-serif"},
    children=[
        html.H1("Bubble Tea Store Analytics", style={"textAlign": "center"}),
        html.P(
            "Peak rush hours across Walk-in and Foodpanda channels (21 Sep–1 Nov 2026).",
            style={"textAlign": "center", "color": "#666"},
        ),

        # Controls: these are the Inputs of the callback below
        html.Div(
            style={"display": "flex", "gap": "40px", "flexWrap": "wrap",
                   "justifyContent": "center", "marginBottom": "10px"},
            children=[
                html.Div(
                    style={"minWidth": "220px"},
                    children=[
                        html.Label("Days to include"),
                        dcc.Dropdown(
                            id="day-filter",
                            options=["All", "Weekday", "Weekend"],
                            value="All",
                            clearable=False,
                        ),
                    ],
                ),
                html.Div(
                    children=[
                        html.Label("Metric"),
                        dcc.RadioItems(
                            id="metric-choice",
                            options=[
                                {"label": " Total orders", "value": "total"},
                                {"label": " Average orders per day", "value": "avg"},
                            ],
                            value="total",
                            inline=True,
                            inputStyle={"marginLeft": "12px"},
                        ),
                    ],
                ),
            ],
        ),

        # Outputs of the callback: the summary line and the chart
        html.P(id="summary", style={"textAlign": "center", "color": "#444"}),
        dcc.Graph(id="rush-hour-chart"),
    ],
)


# Callback: whenever the dropdown or the radio button changes, Dash calls
# update_chart with their new values and puts the return values into the Outputs.
@app.callback(
    Output("rush-hour-chart", "figure"),
    Output("summary", "children"),
    Input("day-filter", "value"),
    Input("metric-choice", "value"),
)
def update_chart(day_type, metric):
    fig, dff, n_days = build_figure(day_type, metric)
    total = int(dff["total_order"].sum())
    summary = f"{day_type}: {total} orders over {n_days} days ({total / n_days:.1f} orders per day)"
    return fig, summary


if __name__ == "__main__":
    app.run(debug=True)
