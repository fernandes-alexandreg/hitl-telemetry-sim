from __future__ import annotations

from typing import Optional

import pandas as pd
import plotly.express as px
from plotly.graph_objects import Figure


def _validate_telemetry_columns(telemetry_df: pd.DataFrame, group_column: Optional[str] = None) -> None:
    required_columns = {"Date", "isAccepted"}
    if group_column is not None:
        required_columns.add(group_column)

    missing_columns = sorted(required_columns.difference(telemetry_df.columns))
    if missing_columns:
        raise ValueError(
            f"telemetry_df is missing required columns: {', '.join(missing_columns)}"
        )


def _build_date_index(date_series: pd.Series) -> pd.Index:
    if pd.api.types.is_datetime64_any_dtype(date_series):
        return pd.date_range(
            date_series.min(),
            date_series.max(),
            freq="D",
            name="Date",
        )

    return pd.Index(
        range(int(date_series.min()), int(date_series.max()) + 1),
        name="Date",
    )


def _rolling_acceptance_rate_by_group(
    telemetry_df: pd.DataFrame,
    group_column: str,
    window: int,
) -> pd.DataFrame:
    _validate_telemetry_columns(telemetry_df, group_column=group_column)

    if window < 1:
        raise ValueError("window must be at least 1.")

    grouped_daily_stats = (
        telemetry_df.groupby(["Date", group_column], as_index=False)
        .agg(
            accepted_sum=("isAccepted", "sum"),
            n_obs=("isAccepted", "size"),
        )
    )

    if grouped_daily_stats.empty:
        return grouped_daily_stats.assign(isAccepted=pd.Series(dtype=float))

    all_dates = _build_date_index(grouped_daily_stats["Date"])
    group_values = telemetry_df[group_column].drop_duplicates()

    acceptance_df = (
        grouped_daily_stats.set_index([group_column, "Date"])
        .reindex(
            pd.MultiIndex.from_product(
                [group_values, all_dates],
                names=[group_column, "Date"],
            ),
            fill_value=0,
        )
        .reset_index()
        .sort_values([group_column, "Date"])
    )

    rolling_columns = [f"accepted_sum_{window}d", f"n_obs_{window}d"]
    acceptance_df[rolling_columns] = (
        acceptance_df.groupby(group_column)[["accepted_sum", "n_obs"]]
        .transform(lambda series: series.rolling(window=window, min_periods=1).sum())
    )

    acceptance_df["isAccepted"] = (
        acceptance_df[rolling_columns[0]] / acceptance_df[rolling_columns[1]]
    )
    return acceptance_df[acceptance_df["n_obs"] > 0]


def plot_daily_acceptance(
    telemetry_df: pd.DataFrame,
    title: str = "Daily Acceptance Rate",
) -> Figure:
    _validate_telemetry_columns(telemetry_df)

    observed_daily_accepts = (
        telemetry_df.groupby(["Date"], as_index=False)["isAccepted"].mean()
    )

    fig = px.scatter(
        observed_daily_accepts,
        x="Date",
        y="isAccepted",
        title=title,
        labels={"isAccepted": "Acceptance Rate", "Date": "Day"},
    )
    fig.update_traces(marker={"size": 5})
    fig.update_layout(yaxis_tickformat=".0%")
    return fig


def plot_acceptance_rate_by_request_type(
    telemetry_df: pd.DataFrame,
    window: int = 7,
    title: Optional[str] = None,
) -> Figure:
    observed_daily_accepts = _rolling_acceptance_rate_by_group(
        telemetry_df,
        group_column="request_type",
        window=window,
    )

    plot_title = title or f"{window}-Day Trailing Acceptance Rate by Request Type"
    fig = px.scatter(
        observed_daily_accepts,
        x="Date",
        y="isAccepted",
        color="request_type",
        hover_name="request_type",
        opacity=0.45,
        title=plot_title,
        labels={"isAccepted": "Acceptance Rate", "Date": "Day"},
    )
    fig.update_traces(marker={"size": 5})
    fig.update_layout(yaxis_tickformat=".0%")
    return fig


def plot_acceptance_rate_by_user(
    telemetry_df: pd.DataFrame,
    window: int = 7,
    title: Optional[str] = None,
) -> Figure:
    observed_daily_accepts = _rolling_acceptance_rate_by_group(
        telemetry_df,
        group_column="User",
        window=window,
    )

    plot_title = title or f"{window}-Day Trailing Acceptance Rate by User"
    fig = px.scatter(
        observed_daily_accepts,
        x="Date",
        y="isAccepted",
        color="User",
        hover_name="User",
        opacity=0.45,
        title=plot_title,
        labels={"isAccepted": "Acceptance Rate", "Date": "Day"},
    )
    fig.update_traces(marker={"size": 5})
    fig.update_layout(yaxis_tickformat=".0%")
    return fig
