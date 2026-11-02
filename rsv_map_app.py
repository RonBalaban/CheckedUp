# -*- coding: utf-8 -*-
"""
Created on Sat Oct 31 14:24:43 2026

@author: Ron
"""

import pandas as pd
import plotly.express as px
from plotly.offline import get_plotlyjs_version
from shiny import App, reactive, render, ui
from shinywidgets import output_widget, render_plotly
from pathlib import Path

# Load and clean the data from the same folder as this app [Local and Server version]
rsv = pd.read_csv(Path(__file__).parent / "RSV Sample data.csv",
                  thousands=",", dtype={"NPI": str})

# Pad to 10 digits
rsv["NPI"] = rsv["NPI"].str.zfill(10)
# Remove the 10 rows with no specialty or state information
rsv = rsv.dropna(subset=["Specialty Group", "Specialty", "State"])
# Drop the invalid states
rsv = rsv[rsv.State != "RHEINLAND-PFALZ"]
rsv = rsv[rsv.State != "ONTARIO"]



# Keep state as text
rsv["State"] = rsv["State"].str.strip().str.upper()


# Lists of choices for the filters
brands = sorted(rsv["Brand"].unique())
groups = sorted(rsv["Specialty Group"].unique())
specialties = sorted(rsv["Specialty"].unique())
states = sorted(rsv["State"].unique())


# Page layout: filters in a sidebar, map and summary in the main area
app_ui = ui.page_sidebar(
    ui.sidebar(
        # Choose what the map colors by
        ui.input_radio_buttons("metric", "Show on map",
                               {"Patients": "Total patients", "NPIs": "Unique NPIs"}),
        # Brand checkboxes (all checked to start)
        ui.input_checkbox_group("brand", "Brand", brands, selected=brands),
        # Specialty filters (leave empty to include all)
        ui.input_selectize("group", "Specialty Group", groups, multiple=True,
                           options={"placeholder": "All groups"}),
        ui.input_selectize("specialty", "Specialty", specialties, multiple=True,
                           options={"placeholder": "All specialties"}),
        # State filter (all selected to start; remove one to grey it out)
        ui.input_selectize("state", "States", states, selected=states, multiple=True),
        ui.input_action_button("all_states", "Select all states"),
        width=320,
    ),
    ui.output_text("summary"),
    # Load Plotly's JavaScript once (same version as the Python package)
    ui.head_content(ui.tags.script(
        src=f"https://cdn.plot.ly/plotly-{get_plotlyjs_version()}.min.js")),
    ui.output_ui("map"),
    title="RSV Patients and NPIs by State",
)

def server(input, output, session):

    # Button to put every state back into the selection
    @reactive.effect
    @reactive.event(input.all_states)
    def _():
        ui.update_selectize("state", selected=states)

    # Only show specialties that belong to the chosen specialty groups
    @reactive.effect
    def _():
        chosen = input.group()
        opts = sorted(rsv.loc[rsv["Specialty Group"].isin(chosen), "Specialty"].unique()) \
               if chosen else specialties
        keep = [s for s in input.specialty() if s in opts]
        ui.update_selectize("specialty", choices=opts, selected=keep)

    # Apply all filters to the data
    @reactive.calc
    def filtered():
        df = rsv[rsv["Brand"].isin(input.brand()) & rsv["State"].isin(input.state())]
        if input.group():
            df = df[df["Specialty Group"].isin(input.group())]
        if input.specialty():
            df = df[df["Specialty"].isin(input.specialty())]
        return df

    # One-line summary of the current selection
    @render.text
    def summary():
        df = filtered()
        return (f"Showing {df['Patients'].sum():,} patients from "
                f"{df['NPI'].nunique():,} unique NPIs across {df['State'].nunique()} states")

    # Draw the map; states not in the filtered data stay grey
    @render.ui
    
    def map():
        by_state = (filtered().groupby("State", as_index=False)
                    .agg(Patients=("Patients", "sum"), NPIs=("NPI", "nunique")))
        metric = input.metric()

        fig = px.choropleth(by_state, locations="State", locationmode="USA-states",
                            color=metric, scope="usa", color_continuous_scale="Teal",
                            hover_data={"Patients": ":,", "NPIs": ":,"})
        fig.update_geos(landcolor="lightgrey", showlakes=False)
        fig.update_layout(autosize=True, margin=dict(l=0, r=0, t=10, b=0))

        # Render as a normal Plotly chart that fills 85% of the window height and resizes with it
        return ui.HTML(fig.to_html(include_plotlyjs=False, full_html=False,
                                   default_height="85vh", default_width="100%",
                                   config={"responsive": True}))

app = App(app_ui, server)