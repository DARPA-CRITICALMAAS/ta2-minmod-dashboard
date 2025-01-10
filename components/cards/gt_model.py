import pandas as pd
import numpy as np
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import dcc

import numpy as np
import plotly.graph_objects as go


def extract_lat_lon(wkt_point):
    if pd.isnull(wkt_point):
        return pd.Series([np.nan, np.nan])  # Return NaN if the value is null
    # Remove 'POINT(' and ')' and split by space
    wkt_point = wkt_point.replace("POINT (", "").replace(")", "")
    lon, lat = map(float, wkt_point.split())
    return pd.Series([lat, lon])


# Function to calculate the min and max distances between points (cached)
def calculate_min_max_distance(distances):
    min_distance = min(distances.values())
    max_distance = max(distances.values())
    return min_distance, max_distance


def greedy_weighted_avg_aggregation(df, distances, proximity_threshold):
    # Create an empty list to store aggregated data
    aggregated_data = []
    processed_indices = set()

    valid_indices = set(df.index)

    # Sort the distances and extract sorted row pairs
    sorted_distances = sorted(distances.items(), key=lambda x: x[1])

    # Flatten the sorted row pairs into a list of valid row indices
    sorted_row_indices = [
        index
        for pair, _ in sorted_distances
        for index in pair
        if index in valid_indices
    ]

    # Loop through all points by sorted row index
    for i in sorted_row_indices:
        if i in processed_indices:
            continue  # Skip already processed points

        # Start with the current point as the center
        group = [i]
        processed_indices.add(i)

        # Find all nearby points within the proximity threshold
        for j in sorted_row_indices:
            if i != j and j not in processed_indices:
                # Ensure that the distance is valid and is not None
                distance = distances.get((i, j))
                if (
                    distance is not None
                    and distance < proximity_threshold
                    and j in valid_indices
                ):
                    group.append(j)
                    processed_indices.add(j)

        # Validate the group indices exist in the DataFrame
        group = [idx for idx in group if idx in valid_indices]

        # Proceed only if the group is valid
        if not group:
            continue

        # Calculate the weighted average of the grade using tonnage as weights
        total_tonnage = df.loc[group, "total_tonnage"].sum()
        weighted_grade = np.average(
            df.loc[group, "total_grade"], weights=df.loc[group, "total_tonnage"]
        )

        # Combine ms_name values from the group
        combined_ms_name = ":: ".join(df.loc[group, "ms_name"])

        # Combine ms_name values from the group
        if len(df.loc[group, "ms_name"]) > 1:
            combined_ms_name = ":: " + ":: ".join(df.loc[group, "ms_name"])
        else:
            combined_ms_name = ":: ".join(df.loc[group, "ms_name"])

        # Combine ms values from the group
        if len(df.loc[group, "ms"]) > 1:
            combined_ms = ":: " + ":: ".join(df.loc[group, "ms"])
        else:
            combined_ms = ":: ".join(df.loc[group, "ms"])

        # Retrieve consistent values for other columns
        ms_value = df.loc[group[0], "ms"]
        commodity_value = df.loc[group[0], "commodity"]
        top1_deposit_name_value = df.loc[group[0], "top1_deposit_name"]
        lat = df.loc[group[0], "lat"]
        lon = df.loc[group[0], "lon"]

        aggregated_data.append(
            {
                "total_grade": weighted_grade,
                "total_tonnage": total_tonnage,
                "ms_name": combined_ms_name,
                "ms": combined_ms,
                "commodity": commodity_value,
                "top1_deposit_name": top1_deposit_name_value,
                "lat": lat,
                "lon": lon,
            }
        )

    return pd.DataFrame(aggregated_data)


def get_gt_model(gt, proximity_value=0):
    """A function to generate grade-tonnage plot."""

    if not gt:
        return None

    # Sorting the deposit types based on group count, avg (total_contained_metal/total_tonnage)
    gt.df["avg_metal_per_tonnage"] = (
        gt.df["total_contained_metal"] / gt.df["total_tonnage"]
    )

    grouped = (
        gt.df.groupby("top1_deposit_name")
        .agg({"top1_deposit_name": "count", "avg_metal_per_tonnage": "mean"})
        .rename(columns={"top1_deposit_name": "count"})
    )

    # Sort first by count (number of records) and then by avg_metal_per_tonnage, both in descending order
    unique_labels = grouped.sort_values(
        by=["count", "avg_metal_per_tonnage"], ascending=[False, False]
    ).index.tolist()

    # Ensure "Unknown" is at the bottom
    if "Unknown" in unique_labels:
        unique_labels.remove("Unknown")
        unique_labels.append("Unknown")

    # Define color for each unique category in 'dtnorm_labels'
    colors = np.linspace(0, 1, len(unique_labels))
    color_map = {label: color for label, color in zip(unique_labels, colors)}

    gt_model = go.Figure()

    gt.aggregated_df = []

    for d_type in unique_labels:
        df_filtered = gt.df[gt.df["top1_deposit_name"] == d_type]

        aggregated_df = df_filtered
        if proximity_value != 0:
            aggregated_df = greedy_weighted_avg_aggregation(
                df_filtered, gt.distance_caches, proximity_value
            )
        gt.aggregated_df.append(aggregated_df)

        hover_template = (
            "<b>MS Name:</b> %{text}<br>"
            + "<b>Commodity:</b> %{customdata[0]}<br>"
            + "<b>Grade:</b> %{y}<br>"
            + "<b>Tonnage:</b> %{x}<br>"
            + "<extra></extra>"
        )

        # Get the count of deposits for this type
        deposit_count = grouped.loc[d_type, "count"]

        gt_model.add_trace(
            go.Scatter(
                x=aggregated_df["total_tonnage"],
                y=aggregated_df["total_grade"],
                mode="markers",
                text=aggregated_df["ms_name"].apply(
                    lambda x: x.replace("::", "<br>")
                ),  # Use truncated names for the labels on the plot
                hovertemplate=hover_template,  # Use full names for the hover text
                customdata=pd.DataFrame(
                    {
                        "commodity": aggregated_df["commodity"].apply(
                            lambda x: gt.data_cache["commodities"][x]["name"]
                        )
                    }
                ),
                name=f"{d_type} ({deposit_count})",  # Add the count of deposits to the legend name
                marker=dict(color=color_map[d_type], size=10, symbol="circle"),
                textposition="top center",
                visible=True,
            )
        )

    y_min = gt.df["total_grade"].min()
    y_max = gt.df["total_grade"].max()
    x_min = gt.df["total_tonnage"].min()
    x_max = gt.df["total_tonnage"].max()

    # Add slant lines representing constant metal content
    metal_contents = np.logspace(-9, 10, num=20)
    for metal_content in metal_contents:
        # Tonnage values range for plotting the line
        tonnage_range = np.logspace(-8, 8, 100)
        grade_values = metal_content / tonnage_range  # Grade = Metal Content / Tonnage
        hover_text = f"<span style='color: white;'><b>Contained Metal:</b> {metal_content} Mt</span>"

        gt_model.add_trace(
            go.Scatter(
                y=tonnage_range,
                x=grade_values,
                mode="lines",
                line=dict(color="grey", dash="dash"),
                showlegend=False,
                text=hover_text,
                hoverinfo="text",
            )
        )

    # Logarithmic scale and layout adjustments
    gt_model.update_layout(
        xaxis=dict(
            type="log",
            title="Tonnage, in million tonnes",
            title_font=dict(size=23, family="Arial Bold, sans-serif"),
            range=[np.log10(x_min / 5), np.log10(x_max * 5)],
        ),
        yaxis=dict(
            type="log",
            title="Grade, in percent",
            title_font=dict(size=23, family="Arial Bold, sans-serif"),
            range=[np.log10(y_min / 5), np.log10(y_max * 5)],
        ),
        title=f"Grade-Tonnage Model of Mineral Deposits ({' & '.join([', '.join(gt.commodities[:-1]), gt.commodities[-1]]) if len(gt.commodities) > 1 else gt.commodities[0]})",
        hovermode="closest",
        autosize=True,
        height=750,
        template="plotly_white",
        dragmode="pan",
    )

    if len(gt.visible_traces) > 0:
        for trace in gt_model["data"]:
            if trace.hovertemplate:
                trace_name = " ".join(trace["name"].split()[:-1])
                if trace_name in gt.visible_traces:
                    trace.visible = True
                else:
                    trace.visible = "legendonly"

    return gt, gt_model
