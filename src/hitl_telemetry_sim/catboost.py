from __future__ import annotations

import os
from typing import Any, Dict, Sequence, Tuple

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from joblib import Parallel, delayed
from sklearn.model_selection import train_test_split


DateSlice = Tuple[Any, Any]


def _validate_catboost_inputs(
    telemetry_df: pd.DataFrame,
    date_slice: DateSlice,
    feature_columns: Sequence[str],
) -> None:
    required_columns = {"Date", "isAccepted", *feature_columns}
    missing_columns = sorted(required_columns.difference(telemetry_df.columns))
    if missing_columns:
        raise ValueError(
            f"telemetry_df is missing required columns: {', '.join(missing_columns)}"
        )

    if len(date_slice) != 2:
        raise ValueError("date_slice must contain exactly two values: (start, end).")

    if not feature_columns:
        raise ValueError("feature_columns must contain at least one column name.")


def _run_single_experiment(
    seed: int,
    selected_telemetry: pd.DataFrame,
    feature_columns: Sequence[str],
    test_size: float,
    loss_function: str,
    eval_metric: str,
    auto_class_weights: str,
    depth: int,
    learning_rate: float,
    iterations: int,
    early_stopping_rounds: int,
    task_type: str,
    thread_count: int,
    verbose: bool | int,
) -> float:
    y = selected_telemetry["isAccepted"].astype(int)
    X = selected_telemetry[list(feature_columns)].copy().fillna(-1)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=test_size,
        stratify=y,
        random_state=seed,
    )

    cat_cols = X_train.select_dtypes(include=["object", "category"]).columns.tolist()

    model = CatBoostClassifier(
        loss_function=loss_function,
        eval_metric=eval_metric,
        auto_class_weights=auto_class_weights,
        depth=depth,
        learning_rate=learning_rate,
        iterations=iterations,
        early_stopping_rounds=early_stopping_rounds,
        random_seed=seed,
        verbose=verbose,
        task_type=task_type,
        thread_count=thread_count,
    )

    model.fit(
        X_train,
        y_train,
        cat_features=cat_cols,
        eval_set=(X_test, y_test),
        use_best_model=True,
    )

    return float(model.get_best_score()["validation"]["AUC"])


def run_catboost_auc_slice(
    telemetry_df: pd.DataFrame,
    date_slice: DateSlice,
    feature_columns: Sequence[str],
    num_runs: int = 10,
    test_size: float = 0.25,
    loss_function: str = "Logloss",
    eval_metric: str = "AUC",
    auto_class_weights: str = "Balanced",
    depth: int = 6,
    learning_rate: float = 0.05,
    iterations: int = 1000,
    early_stopping_rounds: int = 50,
    task_type: str = "CPU",
    thread_count: int = 1,
    n_jobs: int | None = None,
    verbose: bool | int = False,
) -> Dict[str, Any]:
    _validate_catboost_inputs(telemetry_df, date_slice, feature_columns)

    date_start, date_end = date_slice
    selected_telemetry = telemetry_df.loc[
        (telemetry_df["Date"] >= date_start) & (telemetry_df["Date"] <= date_end)
    ].copy()

    if selected_telemetry.empty:
        raise ValueError("No telemetry rows found for the requested date_slice.")

    y = selected_telemetry["isAccepted"].astype(int)
    if y.nunique() < 2:
        raise ValueError(
            "Selected telemetry must contain at least two target classes for AUC."
        )

    job_count = n_jobs if n_jobs is not None else min(6, os.cpu_count() or 1)
    auc_scores = Parallel(n_jobs=job_count)(
        delayed(_run_single_experiment)(
            seed=seed,
            selected_telemetry=selected_telemetry,
            feature_columns=feature_columns,
            test_size=test_size,
            loss_function=loss_function,
            eval_metric=eval_metric,
            auto_class_weights=auto_class_weights,
            depth=depth,
            learning_rate=learning_rate,
            iterations=iterations,
            early_stopping_rounds=early_stopping_rounds,
            task_type=task_type,
            thread_count=thread_count,
            verbose=verbose,
        )
        for seed in range(num_runs)
    )

    auc_array = np.asarray(auc_scores, dtype=float)
    return {
        "selected_telemetry": selected_telemetry,
        "feature_columns": list(feature_columns),
        "date_slice": date_slice,
        "auc_scores": auc_scores,
        "mean_auc": float(np.mean(auc_array)),
        "std_auc": float(np.std(auc_array)),
        "num_runs": num_runs,
        "n_jobs": job_count,
    }
