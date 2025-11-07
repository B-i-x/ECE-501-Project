from dataclasses import dataclass

from pathlib import Path
from typing import Dict, List, Union

import yaml

@dataclass(frozen=True)
class ExecutionConfig:
    runs_per_query: int
    timeout_seconds: int
    dataset_partitions_per_query: Dict[str, List[int]]

def _to_int_list(values: List[Union[int, str]]) -> List[int]:
    out: List[int] = []
    for v in values:
        if isinstance(v, int):
            out.append(v)
        elif isinstance(v, str):
            s = v.replace("_", "").replace(",", "").strip()
            if not s.isdigit():
                raise ValueError(f"Partition value is not an integer: {v!r}")
            out.append(int(s))
        else:
            raise TypeError(f"Unsupported partition type: {type(v).__name__}")
    return out
    
@dataclass(frozen=True)
class AppConfig:
    data_dir = "data"
    ny_edu_data = data_dir + "/ny_edu_data" # baseline datasets in accdb/mdb
    baseline_dir = data_dir + "/baseline" # baseline datasets in sqlite
    execution_config_path = "execution_config.yaml" # query configuration file

    @staticmethod
    def load_execution_config() -> ExecutionConfig:
        """Parse execution_config YAML into an ExecutionConfig object."""
        path = Path(AppConfig.execution_config_path)
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        root = data.get("execution_config")
        if not isinstance(root, dict):
            raise ValueError("Missing 'execution_config' mapping in YAML.")

        runs = int(root.get("runs_per_query", 1))
        timeout = int(root.get("timeout_seconds", 0))

        if timeout < 0:
            raise ValueError("'timeout_seconds' must be >= 0.")
        
        parts_raw = root.get("dataset_partitions_per_query", {}) or {}
        if not isinstance(parts_raw, dict):
            raise ValueError("'dataset_partitions_per_query' must be a mapping of query->list of integers.")

        partitions = {k: _to_int_list(v) for k, v in parts_raw.items()}


        if runs <= 0:
            raise ValueError("'runs_per_query' must be > 0.")
        if timeout < 0:
            raise ValueError("'timeout_seconds' must be >= 0.")

        return ExecutionConfig(
            runs_per_query=runs,
            timeout_seconds=timeout,
            dataset_partitions_per_query=partitions,
        )