from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd


MatrixEnsemble = Dict[str, np.ndarray]


def _coerce_rng(rng: Optional[np.random.Generator] = None) -> np.random.Generator:
    if rng is None:
        return np.random.default_rng()
    return rng


def _clone_ensemble(ensemble: MatrixEnsemble) -> MatrixEnsemble:
    return {key: value.copy() for key, value in ensemble.items()}


class HITLSystemSimulation:
    def __init__(
        self,
        n_components: int = 6,
        n_users: int = 100,
        seed: Optional[int] = None,
        rng: Optional[np.random.Generator] = None,
        pr: float = 1.0,
        component_success_range: Tuple[float, float] = (0.5, 0.8),
        p_accept_correct_range: Tuple[float, float] = (1.0, 1.0),
        p_accept_incorrect_range: Tuple[float, float] = (0.0, 0.0),
    ) -> None:
        if rng is not None and seed is not None:
            raise ValueError("Pass either seed or rng, not both.")
        if not 0.0 <= pr <= 1.0:
            raise ValueError("pr must be between 0 and 1.")

        self.seed = seed
        self.rng = rng if rng is not None else np.random.default_rng(seed)
        self.pr = float(pr)
        self.request_validity_vector = np.array([[self.pr], [1.0 - self.pr]], dtype=float)

        self.n_components = n_components
        self.n_users = n_users
        self.component_success_range = component_success_range
        self.p_accept_correct_range = p_accept_correct_range
        self.p_accept_incorrect_range = p_accept_incorrect_range

        self.components = self._create_component_ensemble(
            n_components=n_components,
            low=component_success_range[0],
            high=component_success_range[1],
        )
        self.users = self._create_user_ensemble(
            n_users=n_users,
            p_accept_correct_range=p_accept_correct_range,
            p_accept_incorrect_range=p_accept_incorrect_range,
        )

        self.initial_components = _clone_ensemble(self.components)
        self.initial_users = _clone_ensemble(self.users)
        self.final_components: Optional[MatrixEnsemble] = None
        self.raw_telemetry: Optional[pd.DataFrame] = None
        self.telemetry: Optional[pd.DataFrame] = None
        self.request_type_categories: Dict[str, str] = {}

    @staticmethod
    def _build_component_matrix(p_success: float) -> np.ndarray:
        return np.array([[p_success, 0.0], [1.0 - p_success, 1.0]], dtype=float)

    @staticmethod
    def _build_human_matrix(
        p_accept_correct: float,
        p_accept_incorrect: float,
    ) -> np.ndarray:
        return np.array(
            [
                [p_accept_correct, p_accept_incorrect],
                [1.0 - p_accept_correct, 1.0 - p_accept_incorrect],
            ],
            dtype=float,
        )

    def _create_component_ensemble(
        self,
        n_components: int,
        low: float,
        high: float,
    ) -> MatrixEnsemble:
        ensemble: MatrixEnsemble = {}

        for index in range(n_components):
            component_id = f"C{index + 1}"
            p_success = float(self.rng.uniform(low=low, high=high))
            ensemble[component_id] = self._build_component_matrix(p_success)

        return ensemble

    def _create_user_ensemble(
        self,
        n_users: int,
        p_accept_correct_range: Tuple[float, float],
        p_accept_incorrect_range: Tuple[float, float],
    ) -> MatrixEnsemble:
        ensemble: MatrixEnsemble = {}

        for index in range(n_users):
            user_id = f"u{index + 1}"
            p_accept_correct = float(
                self.rng.uniform(
                    low=p_accept_correct_range[0],
                    high=p_accept_correct_range[1],
                )
            )
            p_accept_incorrect = float(
                self.rng.uniform(
                    low=p_accept_incorrect_range[0],
                    high=p_accept_incorrect_range[1],
                )
            )
            ensemble[user_id] = self._build_human_matrix(
                p_accept_correct,
                p_accept_incorrect,
            )

        return ensemble

    def _link_system_components(
        self,
        ensemble: MatrixEnsemble,
        component_list: Sequence[str],
    ) -> Tuple[np.ndarray, Dict[str, bool]]:
        feature_dict: Dict[str, bool] = {}
        result = np.eye(2, dtype=float)

        for key in component_list:
            is_success = bool(self.rng.random() < float(ensemble[key][0][0]))
            feature_dict[key] = is_success
            result = result @ self._build_component_matrix(float(is_success))

        return result, feature_dict

    def _simulate_daily_activity(
        self,
        day: int,
        n_items: int,
        component_ensemble: MatrixEnsemble,
        min_path_length: int,
        max_path_length: Optional[int],
    ) -> pd.DataFrame:
        telemetry: List[List[object]] = []
        user_ids = list(self.users.keys())
        component_ids = list(component_ensemble.keys())

        if not component_ids:
            raise ValueError("component_ensemble must contain at least one component")

        path_min = max(1, min_path_length)
        path_max = len(component_ids) if max_path_length is None else min(max_path_length, len(component_ids))

        if path_min > path_max:
            raise ValueError("min_path_length cannot be greater than max_path_length")

        for _ in range(n_items):
            user = str(self.rng.choice(user_ids))
            path_length = int(self.rng.integers(path_min, path_max + 1))
            system_inference_path = list(
                self.rng.choice(component_ids, size=path_length, replace=False)
            )
            composite_system_performance, feature_dict = self._link_system_components(
                component_ensemble,
                system_inference_path,
            )
            accept_prob = float(
                (
                    self.users[user]
                    @ composite_system_performance
                    @ self.request_validity_vector
                )[0, 0]
            )
            is_accepted = bool(self.rng.random() < accept_prob)
            telemetry.append(
                [day, user, is_accepted, system_inference_path, feature_dict]
            )

        return pd.DataFrame(
            telemetry,
            columns=[
                "Date",
                "User",
                "isAccepted",
                "systemInferencePath",
                "featuresDict",
            ],
        )

    @staticmethod
    def _component_improvement_sprint(
        component_ensemble: MatrixEnsemble,
        component_list: Sequence[str],
        improvement_rate: float,
    ) -> MatrixEnsemble:
        for key in component_list:
            improvement = (1.0 - float(component_ensemble[key][0][0])) * improvement_rate
            component_ensemble[key][0][0] += improvement
            component_ensemble[key][1][0] -= improvement
        return component_ensemble

    def _format_telemetry(self, telemetry_df: pd.DataFrame) -> pd.DataFrame:
        formatted_df = telemetry_df.copy()

        formatted_df["systemInferencePath"] = formatted_df["systemInferencePath"].apply(
            lambda values: sorted(values)
        )

        expanded_df = pd.json_normalize(formatted_df["featuresDict"])
        feature_columns = list(expanded_df.columns)
        formatted_df[feature_columns] = expanded_df

        categories: Dict[str, str] = {}
        counter = 1
        for inference_path in formatted_df["systemInferencePath"].astype(str).unique():
            categories[inference_path] = f"Type_{counter}"
            counter += 1

        self.request_type_categories = categories
        formatted_df["request_type"] = formatted_df["systemInferencePath"].apply(
            lambda value: categories[str(value)]
        )
        formatted_df.drop(columns=["featuresDict"], inplace=True)

        ordered_columns = [
            "Date",
            "User",
            "systemInferencePath",
            *feature_columns,
            "request_type",
            "isAccepted",
        ]
        return formatted_df[ordered_columns]

    def run_simulation(
        self,
        n_items_per_day: int = 1000,
        simulation_duration: int = 455,
        sprint_every_days: int = 7,
        sprint_stop_day: int = 425,
        components_per_sprint: int = 1,
        improvement_rate: float = 0.4,
        min_path_length: int = 2,
        max_path_length: Optional[int] = None,
    ) -> pd.DataFrame:
        working_component_ensemble = _clone_ensemble(self.components)
        historical_telemetry: List[pd.DataFrame] = []
        component_ids = list(working_component_ensemble.keys())

        for day in range(1, simulation_duration + 1):
            historical_telemetry.append(
                self._simulate_daily_activity(
                    day=day,
                    n_items=n_items_per_day,
                    component_ensemble=working_component_ensemble,
                    min_path_length=min_path_length,
                    max_path_length=max_path_length,
                )
            )

            if (
                sprint_every_days > 0
                and day % sprint_every_days == 0
                and day <= sprint_stop_day
                and component_ids
            ):
                sprint_size = min(components_per_sprint, len(component_ids))
                selected_components = list(
                    self.rng.choice(component_ids, size=sprint_size, replace=False)
                )
                self._component_improvement_sprint(
                    working_component_ensemble,
                    selected_components,
                    improvement_rate,
                )

        self.final_components = working_component_ensemble
        self.raw_telemetry = pd.concat(historical_telemetry, ignore_index=True)
        self.telemetry = self._format_telemetry(self.raw_telemetry)
        return self.telemetry


hitl_system_simulation = HITLSystemSimulation
