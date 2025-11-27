from typing import Annotated, Unpack

import click
from pydantic import SecretStr

from vectordb_bench.backend.clients import DB
from vectordb_bench.cli.cli import (
    CommonTypedDict,
    cli,
    click_parameter_decorators_from_typed_dict,
    run,
)

DBTYPE = DB.QdrantLocal


class QdrantLocalTypedDict(CommonTypedDict):
    url: Annotated[
        str,
        click.option("--url", type=str, help="Qdrant url", required=True),
    ]
    grpc_port: Annotated[
        int,
        click.option("--grpc-port", type=int, default=None, help="Qdrant gRPC port (optional, enables gRPC if set)"),
    ]
    prefer_grpc: Annotated[
        bool,
        click.option("--prefer-grpc/--no-prefer-grpc", default=False, help="Prefer gRPC over HTTP (requires grpc-port)"),
    ]
    on_disk: Annotated[
        bool,
        click.option("--on-disk", type=bool, default=False, help="Store the vectors and the HNSW index on disk"),
    ]
    m: Annotated[
        int,
        click.option("--m", type=int, default=16, help="HNSW index parameter m, set 0 to disable the index"),
    ]
    ef_construct: Annotated[
        int,
        click.option("--ef-construct", type=int, default=200, help="HNSW index parameter ef_construct"),
    ]
    hnsw_ef: Annotated[
        int,
        click.option(
            "--hnsw-ef",
            type=int,
            default=0,
            help="HNSW index parameter hnsw_ef, set 0 to use ef_construct for search",
        ),
    ]


@cli.command()
@click_parameter_decorators_from_typed_dict(QdrantLocalTypedDict)
def QdrantLocal(**parameters: Unpack[QdrantLocalTypedDict]):
    from .config import QdrantLocalConfig, QdrantLocalIndexConfig

    run(
        db=DBTYPE,
        db_config=QdrantLocalConfig(
            url=SecretStr(parameters["url"]),
            grpc_port=parameters.get("grpc_port"),
            prefer_grpc=parameters.get("prefer_grpc", False),
        ),
        db_case_config=QdrantLocalIndexConfig(
            on_disk=parameters["on_disk"],
            m=parameters["m"],
            ef_construct=parameters["ef_construct"],
            hnsw_ef=parameters["hnsw_ef"],
        ),
        **parameters,
    )
