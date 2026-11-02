# -*- coding: utf-8 -*-
"""
Created on Sat Oct 31 08:20:18 2026

CheckedUp Case Study

@author: Ron
"""


###############################################################################
# Specify directory
import os
os.chdir(r'C:\Users\Ron\OneDrive\Desktop\CheckedUp')

# Load dataset
import pandas as pd

# Convert Patients into number 
rsv = pd.read_csv('RSV Sample data.csv',
                  thousands = ',',          # "246,101" -> 246101 
                  dtype = {'NPI': str})     # keep NPI as text


# Re-add leading 0's to be 10 digit standard
rsv["NPI"] = rsv["NPI"].astype(str).str.zfill(10)

# Remove the 10 rows with no specialty or state information
rsv = rsv.dropna(subset=["Specialty Group", "Specialty", "State"])
# Drop the invalid states
rsv = rsv[rsv.State != "RHEINLAND-PFALZ"]
rsv = rsv[rsv.State != "ONTARIO"]

# Unique values per field
print("Unique brands:", rsv["Brand"].nunique())
print("Unique NPIs:", rsv["NPI"].nunique())
print("Unique Specialty Groups:", rsv["Specialty Group"].nunique())
print("Unique Specialties:", rsv["Specialty"].nunique())
print("Total rows:", len(rsv))


###############################################################################
# 10 most common values per field, by rows

import matplotlib.pyplot as plt

fields = ["Brand", "Specialty Group", "Specialty", "State"]

for field in fields:
    counts = rsv[field].value_counts().head(10).sort_values()  

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(counts.index, counts.values, color="Teal")

    # Label each bar with its count
    ax.bar_label(bars, labels=[f"{v:,}" for v in counts.values], padding=4)

    ax.set_title(f"Top 10 {field} by Number of Rows")
    ax.set_xlabel("Count")
    ax.spines[["top", "right"]].set_visible(False)
    # leave room for the labels
    ax.set_xlim(0, counts.max() * 1.12)  
    plt.tight_layout()
    plt.show()
    
    
    

# 10 most common values per field, by patients, percantage of patients, and number of NPI's
fields = ["Brand", "Specialty Group", "Specialty", "State"]

# Grand total of patients, used for the % share in every chart
total_patients = rsv["Patients"].sum()

for field in fields:
    # Patients and unique NPIs per value, keep the top 10, largest on top
    summary = (rsv.groupby(field)
               .agg(Patients=("Patients", "sum"),
                    NPIs=("NPI", "nunique"))
               .nlargest(10, "Patients")
               .sort_values("Patients"))

    # Each value's share of all patients in the dataset
    summary["Share"] = (summary["Patients"] / total_patients * 100).round(1)

    fig, ax = plt.subplots(figsize=(11, 6))
    bars = ax.barh(summary.index, summary["Patients"], color="Teal")

    # Label each bar with patients, share of total, and number of NPIs
    labels = [f"{p:,}  ({s}%)  |  {n:,} NPIs"
              for p, s, n in zip(summary["Patients"], summary["Share"], summary["NPIs"])]
    ax.bar_label(bars, labels=labels, padding=4, fontsize=9)

    # Titles, plain-number axis, extra room for the labels, cleaner styling
    ax.set_title(f"Top 10 {field} by Total Patients", fontweight="bold")
    ax.set_xlabel("Patients")
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.set_xlim(0, summary["Patients"].max() * 1.35)
    ax.spines[["top", "right"]].set_visible(False)

    plt.tight_layout()
    plt.show()
    
    
    
###############################################################################
# Most common specialtys per State

import math
n_states = 9      # how many states
n_spec = 5        # specialties per state

# Pick states with the most patients
top_states = rsv.groupby("State")["Patients"].sum().nlargest(n_states).index

# Count specialties in each state
spec_by_state = (rsv[rsv["State"].isin(top_states)]
                 .groupby(["State", "Specialty"])["Patients"]
                 .sum()
                 .rename("Count")
                 .reset_index())

# Set a grid of subplots and flatten it so I can loop
ncols = 3
nrows = math.ceil(n_states / ncols)
fig, axes = plt.subplots(nrows, ncols, figsize=(16, 4 * nrows))
axes = axes.flatten()

# Draw one bar chart per state
for ax, state in zip(axes, top_states):
    # Keep this state's top specialties, sorted so the largest bar is on top
    d = (spec_by_state[spec_by_state["State"] == state]
         .nlargest(n_spec, "Count")
         .sort_values("Count"))
    # Horizontal bars with a comma-formatted label at the end of each bar
    bars = ax.barh(d["Specialty"], d["Count"], color="Teal")
    ax.bar_label(bars, labels=[f"{v:,}" for v in d["Count"]], padding=3, fontsize=9)
    
    # Title, extra space for labels, and cleaner styling
    ax.set_title(state, fontweight="bold")
    ax.set_xlim(0, d["Count"].max() * 1.2)
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(axis="y", labelsize=9)

# Hide any empty panels
for ax in axes[len(top_states):]:
    ax.set_visible(False)

fig.suptitle(f"Top {n_spec} Specialties in the Top {n_states} States (by Patients)",
             fontsize=15, fontweight="bold")
plt.tight_layout()
plt.show()


###############################################################################
# Which specialties overlap across NPIs? Is there any collision?

# Count how many different specialties and specialty groups each NPI has
npi_check = (rsv.groupby("NPI")
             # Aggregate by unique values
             .agg(n_specialty=("Specialty", "nunique"), 
                  n_group=("Specialty Group", "nunique"),
                  n_brands=("Brand", "nunique"),
                  rows=("NPI", "size")))

# How many NPIs have more than one specialty or group
print("NPIs with >1 Specialty:", (npi_check["n_specialty"] > 1).sum())
print("NPIs with >1 Specialty Group:", (npi_check["n_group"] > 1).sum())
print("Total NPIs:", len(npi_check))

# Pull NPIs that have a collision in either field
collision_npis = npi_check[(npi_check["n_specialty"] > 1) |
                           (npi_check["n_group"] > 1)].index

# Show their full rows to see conflicting values side by side
collisions = (rsv[rsv["NPI"].isin(collision_npis)]
              .sort_values(["NPI", "Brand"]))
print(collisions)

# There are no NPI's that have more than 1 Specialty or Specialty Group, so the extra ones come from occuring across multiple Brands/States


###############################################################################
# Total number of patients and Unique Brands per Specialty Group / Specialty


# Totals by Specialty Group: patients, unique brands, and unique NPIs
by_group = (rsv.groupby("Specialty Group")
            .agg(Patients=("Patients", "sum"),
                 Unique_Brands=("Brand", "nunique"),
                 NPIs=("NPI", "nunique"))
            .sort_values("Patients", ascending=False))

# Add each group's share of all patients
by_group["Patient_Share_%"] = (by_group["Patients"] / by_group["Patients"].sum() * 100).round(1)
print(by_group)


###############################################################################
# Same breakdown one level deeper: Specialty within each Specialty Group
by_specialty = (rsv.groupby(["Specialty Group", "Specialty"])
                .agg(Patients=("Patients", "sum"),
                     Unique_Brands=("Brand", "nunique"),
                     NPIs=("NPI", "nunique"))
                .sort_values("Patients", ascending=False))

# Add each specialty's share of all patients
by_specialty["Patient_Share_%"] = (by_specialty["Patients"] / by_specialty["Patients"].sum() * 100).round(1)
print(by_specialty)


###############################################################################
# I want to see top specialties in each specialty group and how many patients they have

import math
import textwrap

# how many groups and specialties to show, and max characters per label line
n_groups = 9      # how many specialty groups
n_spec = 5        # specialties per group
wrap_width = 30   # text wrap labels longer than this many characters

# Turn the by_specialty table back into regular columns
spec_df = by_specialty.reset_index()

# Find the specialty groups with the most total patients
top_groups = spec_df.groupby("Specialty Group")["Patients"].sum().nlargest(n_groups).index

# Set up a grid of subplots (3 per row) and flatten it so we can loop over it
ncols = 3
nrows = math.ceil(n_groups / ncols)
fig, axes = plt.subplots(nrows, ncols, figsize=(16, 4 * nrows))
axes = axes.flatten()

# Draw one bar chart per specialty group
for ax, group in zip(axes, top_groups):
    # Keep this group's top specialties, sorted so the largest bar is on top
    d = (spec_df[spec_df["Specialty Group"] == group]
         .nlargest(n_spec, "Patients")
         .sort_values("Patients"))

    # Wrap long specialty names onto multiple lines
    wrapped = [textwrap.fill(s, wrap_width) for s in d["Specialty"]]

    # Horizontal bars with a comma-formatted patient label at the end of each bar
    bars = ax.barh(wrapped, d["Patients"], color="Teal")
    ax.bar_label(bars, labels=[f"{v:,}" for v in d["Patients"]], padding=3, fontsize=9)

    # Title, extra space for labels, and cleaner styling
    ax.set_title(group, fontweight="bold")
    ax.set_xlim(0, d["Patients"].max() * 1.25)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(axis="y", labelsize=9)
    ax.tick_params(axis="x", labelsize=8)

# Hide any empty panels left over in the grid
for ax in axes[len(top_groups):]:
    ax.set_visible(False)

# Overall title for the figure, then fit everything together and display
fig.suptitle(f"Top {n_spec} Specialties in the Top {n_groups} Specialty Groups (by Patients)",
             fontsize=15, fontweight="bold")
plt.tight_layout()
plt.show()


###############################################################################
# I want to build an interactive geographic map, that will display a few things
# either total number of unique NPI's, or total number of patients in each state
# Including filters for Brands, Specialties, Groups
# I followed the deployment instructions on https://docs.posit.co/shinyapps.io/guide/index.html to publish the shiny app, saved here:
# https://k6clpl-ron-balaban.shinyapps.io/checkedup-rsv-map/




# Potential future analysis, connecting to NPI registry (https://npiregistry.cms.hhs.gov/search)
# Share of NPIs that start with 1 or 2, as real NPIs do
print(rsv["NPI"].str[0].value_counts().sort_index())
print("Look like real NPIs:", rsv["NPI"].str[0].isin(["1", "2"]).mean().round(3))






















# Can I build an SNA of Prescribers, to see the most interactive network?





