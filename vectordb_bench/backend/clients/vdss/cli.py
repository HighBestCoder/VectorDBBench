"""VDSS CLI for VectorDBBench"""

from typing import Annotated, Unpack

import click
import os
from pydantic import SecretStr

from vectordb_bench.cli.cli import (
    CommonTypedDict,
    cli,
    click_parameter_decorators_from_typed_dict,
    run,
    get_custom_case_config,
)
from vectordb_bench.backend.clients import DB


class VDSSTypedDict(CommonTypedDict):
    """VDSS CLI parameters"""
    
    grpc_host: Annotated[
        str,
        click.option(
            "--grpc-host",
            type=str,
            help="VDSS gRPC server host",
            default="localhost",
            show_default=True,
        ),
    ]
    grpc_port: Annotated[
        int,
        click.option(
            "--grpc-port",
            type=int,
            help="VDSS gRPC server port",
            default=50051,
            show_default=True,
        ),
    ]
    api_key: Annotated[
        str,
        click.option(
            "--api-key",
            type=str,
            help="VDSS API key (optional)",
            default=lambda: os.environ.get("VDSS_API_KEY", ""),
            show_default="$VDSS_API_KEY",
        ),
    ]
    m: Annotated[
        int,
        click.option(
            "--m",
            type=int,
            help="HNSW M parameter",
            default=16,
            show_default=True,
        ),
    ]
    ef_construction: Annotated[
        int,
        click.option(
            "--ef-construction",
            type=int,
            help="HNSW ef_construction parameter",
            default=200,
            show_default=True,
        ),
    ]
    ef_search: Annotated[
        int,
        click.option(
            "--ef-search",
            type=int,
            help="HNSW ef_search parameter",
            default=100,
            show_default=True,
        ),
    ]
    storage_type: Annotated[
        str,
        click.option(
            "--storage-type",
            type=str,
            help="Storage type (zendb, mem)",
            default="zendb",
            show_default=True,
        ),
    ]


@cli.command()
@click_parameter_decorators_from_typed_dict(VDSSTypedDict)
def VDSSHnsw(**parameters: Unpack[VDSSTypedDict]):
    """Run benchmark for VDSS with HNSW index"""
    from .config import VDSSConfig, VDSSIndexConfig
    from vectordb_bench.backend.clients.api import IndexType

    # Get custom case config if provided
    parameters["custom_case"] = get_custom_case_config(parameters)

    api_key_value = parameters["api_key"]
    
    run(
        db=DB.VDSS,
        db_config=VDSSConfig(
            db_label=parameters["db_label"],
            grpc_host=parameters["grpc_host"],
            grpc_port=parameters["grpc_port"],
            api_key=SecretStr(api_key_value) if api_key_value else None,
        ),
        db_case_config=VDSSIndexConfig(
            index_type=IndexType.HNSW,
            m=parameters["m"],
            ef_construction=parameters["ef_construction"],
            ef_search=parameters["ef_search"],
            storage_type=parameters["storage_type"],
        ),
        **parameters,
    )
