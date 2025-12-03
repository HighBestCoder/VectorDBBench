"""FAISS CLI wiring."""

from typing import Annotated, Unpack

import click

from vectordb_bench.backend.clients import DB
from vectordb_bench.backend.clients.api import MetricType
from vectordb_bench.cli.cli import (
    CommonTypedDict,
    HNSWFlavor3,
    click_parameter_decorators_from_typed_dict,
    get_custom_case_config,
    run,
)

from .config import FaissConfig, FaissIndexConfig


class FaissTypedDict(CommonTypedDict, HNSWFlavor3):
    metric_type: Annotated[
        str,
        click.option(
            "--metric-type",
            type=click.Choice([metric.name for metric in MetricType], case_sensitive=False),
            default=MetricType.L2.name,
            show_default=True,
            help="Distance metric used by the dataset",
        ),
    ]
    num_threads: Annotated[
        int,
        click.option(
            "--num-threads",
            type=int,
            default=0,
            show_default=True,
            help="Limit FAISS OpenMP threads (0 keeps FAISS default)",
        ),
    ]
    batch_size: Annotated[
        int,
        click.option(
            "--batch-size",
            type=int,
            default=20000,
            show_default=True,
            help="Maximum number of vectors pushed per native call",
        ),
    ]
    faiss_root: Annotated[
        str | None,
        click.option(
            "--faiss-root",
            type=str,
            help="Override FAISS installation directory (defaults to third-party/faiss/linux-x64)",
        ),
    ]
    client_library: Annotated[
        str | None,
        click.option(
            "--client-library",
            type=str,
            help="Absolute path to libfaissclient.so (auto-detected otherwise)",
        ),
    ]


@click.command(name="faiss")
@click_parameter_decorators_from_typed_dict(FaissTypedDict)
def FaissCli(**parameters: Unpack[FaissTypedDict]):
    """Run benchmarks locally using the embedded FAISS engine."""

    parameters["custom_case"] = get_custom_case_config(parameters)
    metric_type = MetricType[parameters["metric_type"].upper()]

    run(
        db=DB.FAISS,
        db_config=FaissConfig(
            db_label=parameters["db_label"],
            batch_size=parameters["batch_size"],
            num_threads=parameters["num_threads"],
            faiss_root=parameters.get("faiss_root"),
            client_library=parameters.get("client_library"),
        ),
        db_case_config=FaissIndexConfig(
            metric_type=metric_type,
            m=parameters["m"],
            ef_construction=parameters["ef_construction"],
            ef_search=parameters["ef_search"],
        ),
        **parameters,
    )
