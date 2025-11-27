import vdss_types_pb2 as _vdss_types_pb2
from google.protobuf.internal import containers as _containers
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable, Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class CreateCollectionRequest(_message.Message):
    __slots__ = ("collection_name", "config")
    COLLECTION_NAME_FIELD_NUMBER: _ClassVar[int]
    CONFIG_FIELD_NUMBER: _ClassVar[int]
    collection_name: str
    config: _vdss_types_pb2.CollectionConfig
    def __init__(self, collection_name: _Optional[str] = ..., config: _Optional[_Union[_vdss_types_pb2.CollectionConfig, _Mapping]] = ...) -> None: ...

class CreateCollectionResponse(_message.Message):
    __slots__ = ("status",)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: _vdss_types_pb2.Status
    def __init__(self, status: _Optional[_Union[_vdss_types_pb2.Status, _Mapping]] = ...) -> None: ...

class OpenCollectionRequest(_message.Message):
    __slots__ = ("collection_name",)
    COLLECTION_NAME_FIELD_NUMBER: _ClassVar[int]
    collection_name: str
    def __init__(self, collection_name: _Optional[str] = ...) -> None: ...

class OpenCollectionResponse(_message.Message):
    __slots__ = ("status",)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: _vdss_types_pb2.Status
    def __init__(self, status: _Optional[_Union[_vdss_types_pb2.Status, _Mapping]] = ...) -> None: ...

class CloseCollectionRequest(_message.Message):
    __slots__ = ("collection_name",)
    COLLECTION_NAME_FIELD_NUMBER: _ClassVar[int]
    collection_name: str
    def __init__(self, collection_name: _Optional[str] = ...) -> None: ...

class CloseCollectionResponse(_message.Message):
    __slots__ = ("status",)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: _vdss_types_pb2.Status
    def __init__(self, status: _Optional[_Union[_vdss_types_pb2.Status, _Mapping]] = ...) -> None: ...

class DeleteCollectionRequest(_message.Message):
    __slots__ = ("collection_name",)
    COLLECTION_NAME_FIELD_NUMBER: _ClassVar[int]
    collection_name: str
    def __init__(self, collection_name: _Optional[str] = ...) -> None: ...

class DeleteCollectionResponse(_message.Message):
    __slots__ = ("status",)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: _vdss_types_pb2.Status
    def __init__(self, status: _Optional[_Union[_vdss_types_pb2.Status, _Mapping]] = ...) -> None: ...

class UpsertVectorRequest(_message.Message):
    __slots__ = ("collection_name", "offset", "vector", "payload")
    COLLECTION_NAME_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    VECTOR_FIELD_NUMBER: _ClassVar[int]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    collection_name: str
    offset: int
    vector: _vdss_types_pb2.Vector
    payload: _vdss_types_pb2.Payload
    def __init__(self, collection_name: _Optional[str] = ..., offset: _Optional[int] = ..., vector: _Optional[_Union[_vdss_types_pb2.Vector, _Mapping]] = ..., payload: _Optional[_Union[_vdss_types_pb2.Payload, _Mapping]] = ...) -> None: ...

class UpsertVectorResponse(_message.Message):
    __slots__ = ("status",)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: _vdss_types_pb2.Status
    def __init__(self, status: _Optional[_Union[_vdss_types_pb2.Status, _Mapping]] = ...) -> None: ...

class DeleteVectorRequest(_message.Message):
    __slots__ = ("collection_name", "offset")
    COLLECTION_NAME_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    collection_name: str
    offset: int
    def __init__(self, collection_name: _Optional[str] = ..., offset: _Optional[int] = ...) -> None: ...

class DeleteVectorResponse(_message.Message):
    __slots__ = ("status",)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: _vdss_types_pb2.Status
    def __init__(self, status: _Optional[_Union[_vdss_types_pb2.Status, _Mapping]] = ...) -> None: ...

class GetVectorRequest(_message.Message):
    __slots__ = ("collection_name", "offset")
    COLLECTION_NAME_FIELD_NUMBER: _ClassVar[int]
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    collection_name: str
    offset: int
    def __init__(self, collection_name: _Optional[str] = ..., offset: _Optional[int] = ...) -> None: ...

class GetVectorResponse(_message.Message):
    __slots__ = ("status", "vector", "payload")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    VECTOR_FIELD_NUMBER: _ClassVar[int]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    status: _vdss_types_pb2.Status
    vector: _vdss_types_pb2.Vector
    payload: _vdss_types_pb2.Payload
    def __init__(self, status: _Optional[_Union[_vdss_types_pb2.Status, _Mapping]] = ..., vector: _Optional[_Union[_vdss_types_pb2.Vector, _Mapping]] = ..., payload: _Optional[_Union[_vdss_types_pb2.Payload, _Mapping]] = ...) -> None: ...

class BatchUpsertRequest(_message.Message):
    __slots__ = ("collection_name", "offsets", "vectors", "payloads")
    COLLECTION_NAME_FIELD_NUMBER: _ClassVar[int]
    OFFSETS_FIELD_NUMBER: _ClassVar[int]
    VECTORS_FIELD_NUMBER: _ClassVar[int]
    PAYLOADS_FIELD_NUMBER: _ClassVar[int]
    collection_name: str
    offsets: _containers.RepeatedScalarFieldContainer[int]
    vectors: _containers.RepeatedCompositeFieldContainer[_vdss_types_pb2.Vector]
    payloads: _containers.RepeatedCompositeFieldContainer[_vdss_types_pb2.Payload]
    def __init__(self, collection_name: _Optional[str] = ..., offsets: _Optional[_Iterable[int]] = ..., vectors: _Optional[_Iterable[_Union[_vdss_types_pb2.Vector, _Mapping]]] = ..., payloads: _Optional[_Iterable[_Union[_vdss_types_pb2.Payload, _Mapping]]] = ...) -> None: ...

class BatchUpsertResponse(_message.Message):
    __slots__ = ("status",)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: _vdss_types_pb2.Status
    def __init__(self, status: _Optional[_Union[_vdss_types_pb2.Status, _Mapping]] = ...) -> None: ...

class BatchDeleteRequest(_message.Message):
    __slots__ = ("collection_name", "offsets")
    COLLECTION_NAME_FIELD_NUMBER: _ClassVar[int]
    OFFSETS_FIELD_NUMBER: _ClassVar[int]
    collection_name: str
    offsets: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, collection_name: _Optional[str] = ..., offsets: _Optional[_Iterable[int]] = ...) -> None: ...

class BatchDeleteResponse(_message.Message):
    __slots__ = ("status",)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: _vdss_types_pb2.Status
    def __init__(self, status: _Optional[_Union[_vdss_types_pb2.Status, _Mapping]] = ...) -> None: ...

class SearchRequest(_message.Message):
    __slots__ = ("collection_name", "query", "top_k")
    COLLECTION_NAME_FIELD_NUMBER: _ClassVar[int]
    QUERY_FIELD_NUMBER: _ClassVar[int]
    TOP_K_FIELD_NUMBER: _ClassVar[int]
    collection_name: str
    query: _vdss_types_pb2.Vector
    top_k: int
    def __init__(self, collection_name: _Optional[str] = ..., query: _Optional[_Union[_vdss_types_pb2.Vector, _Mapping]] = ..., top_k: _Optional[int] = ...) -> None: ...

class SearchResponse(_message.Message):
    __slots__ = ("status", "results")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    RESULTS_FIELD_NUMBER: _ClassVar[int]
    status: _vdss_types_pb2.Status
    results: _containers.RepeatedCompositeFieldContainer[_vdss_types_pb2.SearchResult]
    def __init__(self, status: _Optional[_Union[_vdss_types_pb2.Status, _Mapping]] = ..., results: _Optional[_Iterable[_Union[_vdss_types_pb2.SearchResult, _Mapping]]] = ...) -> None: ...

class SearchFilteredRequest(_message.Message):
    __slots__ = ("collection_name", "query", "top_k", "filter_json")
    COLLECTION_NAME_FIELD_NUMBER: _ClassVar[int]
    QUERY_FIELD_NUMBER: _ClassVar[int]
    TOP_K_FIELD_NUMBER: _ClassVar[int]
    FILTER_JSON_FIELD_NUMBER: _ClassVar[int]
    collection_name: str
    query: _vdss_types_pb2.Vector
    top_k: int
    filter_json: str
    def __init__(self, collection_name: _Optional[str] = ..., query: _Optional[_Union[_vdss_types_pb2.Vector, _Mapping]] = ..., top_k: _Optional[int] = ..., filter_json: _Optional[str] = ...) -> None: ...

class SearchFilteredResponse(_message.Message):
    __slots__ = ("status", "results")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    RESULTS_FIELD_NUMBER: _ClassVar[int]
    status: _vdss_types_pb2.Status
    results: _containers.RepeatedCompositeFieldContainer[_vdss_types_pb2.SearchResult]
    def __init__(self, status: _Optional[_Union[_vdss_types_pb2.Status, _Mapping]] = ..., results: _Optional[_Iterable[_Union[_vdss_types_pb2.SearchResult, _Mapping]]] = ...) -> None: ...

class SearchWithWhitelistRequest(_message.Message):
    __slots__ = ("collection_name", "query", "top_k", "allowed_offsets")
    COLLECTION_NAME_FIELD_NUMBER: _ClassVar[int]
    QUERY_FIELD_NUMBER: _ClassVar[int]
    TOP_K_FIELD_NUMBER: _ClassVar[int]
    ALLOWED_OFFSETS_FIELD_NUMBER: _ClassVar[int]
    collection_name: str
    query: _vdss_types_pb2.Vector
    top_k: int
    allowed_offsets: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, collection_name: _Optional[str] = ..., query: _Optional[_Union[_vdss_types_pb2.Vector, _Mapping]] = ..., top_k: _Optional[int] = ..., allowed_offsets: _Optional[_Iterable[int]] = ...) -> None: ...

class SearchWithWhitelistResponse(_message.Message):
    __slots__ = ("status", "results")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    RESULTS_FIELD_NUMBER: _ClassVar[int]
    status: _vdss_types_pb2.Status
    results: _containers.RepeatedCompositeFieldContainer[_vdss_types_pb2.SearchResult]
    def __init__(self, status: _Optional[_Union[_vdss_types_pb2.Status, _Mapping]] = ..., results: _Optional[_Iterable[_Union[_vdss_types_pb2.SearchResult, _Mapping]]] = ...) -> None: ...

class FilterByPayloadRequest(_message.Message):
    __slots__ = ("collection_name", "filter_json", "max_count")
    COLLECTION_NAME_FIELD_NUMBER: _ClassVar[int]
    FILTER_JSON_FIELD_NUMBER: _ClassVar[int]
    MAX_COUNT_FIELD_NUMBER: _ClassVar[int]
    collection_name: str
    filter_json: str
    max_count: int
    def __init__(self, collection_name: _Optional[str] = ..., filter_json: _Optional[str] = ..., max_count: _Optional[int] = ...) -> None: ...

class FilterByPayloadResponse(_message.Message):
    __slots__ = ("status", "offsets")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    OFFSETS_FIELD_NUMBER: _ClassVar[int]
    status: _vdss_types_pb2.Status
    offsets: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, status: _Optional[_Union[_vdss_types_pb2.Status, _Mapping]] = ..., offsets: _Optional[_Iterable[int]] = ...) -> None: ...

class SaveSnapshotRequest(_message.Message):
    __slots__ = ("collection_name",)
    COLLECTION_NAME_FIELD_NUMBER: _ClassVar[int]
    collection_name: str
    def __init__(self, collection_name: _Optional[str] = ...) -> None: ...

class SaveSnapshotResponse(_message.Message):
    __slots__ = ("status",)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: _vdss_types_pb2.Status
    def __init__(self, status: _Optional[_Union[_vdss_types_pb2.Status, _Mapping]] = ...) -> None: ...

class LoadSnapshotRequest(_message.Message):
    __slots__ = ("collection_name",)
    COLLECTION_NAME_FIELD_NUMBER: _ClassVar[int]
    collection_name: str
    def __init__(self, collection_name: _Optional[str] = ...) -> None: ...

class LoadSnapshotResponse(_message.Message):
    __slots__ = ("status",)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: _vdss_types_pb2.Status
    def __init__(self, status: _Optional[_Union[_vdss_types_pb2.Status, _Mapping]] = ...) -> None: ...

class GetStateRequest(_message.Message):
    __slots__ = ("collection_name",)
    COLLECTION_NAME_FIELD_NUMBER: _ClassVar[int]
    collection_name: str
    def __init__(self, collection_name: _Optional[str] = ...) -> None: ...

class GetStateResponse(_message.Message):
    __slots__ = ("status", "state")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    STATE_FIELD_NUMBER: _ClassVar[int]
    status: _vdss_types_pb2.Status
    state: _vdss_types_pb2.CollectionState
    def __init__(self, status: _Optional[_Union[_vdss_types_pb2.Status, _Mapping]] = ..., state: _Optional[_Union[_vdss_types_pb2.CollectionState, str]] = ...) -> None: ...

class GetVectorCountRequest(_message.Message):
    __slots__ = ("collection_name",)
    COLLECTION_NAME_FIELD_NUMBER: _ClassVar[int]
    collection_name: str
    def __init__(self, collection_name: _Optional[str] = ...) -> None: ...

class GetVectorCountResponse(_message.Message):
    __slots__ = ("status", "count")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    COUNT_FIELD_NUMBER: _ClassVar[int]
    status: _vdss_types_pb2.Status
    count: int
    def __init__(self, status: _Optional[_Union[_vdss_types_pb2.Status, _Mapping]] = ..., count: _Optional[int] = ...) -> None: ...

class GetStatsRequest(_message.Message):
    __slots__ = ("collection_name",)
    COLLECTION_NAME_FIELD_NUMBER: _ClassVar[int]
    collection_name: str
    def __init__(self, collection_name: _Optional[str] = ...) -> None: ...

class GetStatsResponse(_message.Message):
    __slots__ = ("status", "stats")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    STATS_FIELD_NUMBER: _ClassVar[int]
    status: _vdss_types_pb2.Status
    stats: _vdss_types_pb2.CollectionStats
    def __init__(self, status: _Optional[_Union[_vdss_types_pb2.Status, _Mapping]] = ..., stats: _Optional[_Union[_vdss_types_pb2.CollectionStats, _Mapping]] = ...) -> None: ...

class FlushRequest(_message.Message):
    __slots__ = ("collection_name",)
    COLLECTION_NAME_FIELD_NUMBER: _ClassVar[int]
    collection_name: str
    def __init__(self, collection_name: _Optional[str] = ...) -> None: ...

class FlushResponse(_message.Message):
    __slots__ = ("status",)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: _vdss_types_pb2.Status
    def __init__(self, status: _Optional[_Union[_vdss_types_pb2.Status, _Mapping]] = ...) -> None: ...

class RebuildIndexRequest(_message.Message):
    __slots__ = ("collection_name",)
    COLLECTION_NAME_FIELD_NUMBER: _ClassVar[int]
    collection_name: str
    def __init__(self, collection_name: _Optional[str] = ...) -> None: ...

class RebuildIndexResponse(_message.Message):
    __slots__ = ("status",)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: _vdss_types_pb2.Status
    def __init__(self, status: _Optional[_Union[_vdss_types_pb2.Status, _Mapping]] = ...) -> None: ...

class OptimizeRequest(_message.Message):
    __slots__ = ("collection_name",)
    COLLECTION_NAME_FIELD_NUMBER: _ClassVar[int]
    collection_name: str
    def __init__(self, collection_name: _Optional[str] = ...) -> None: ...

class OptimizeResponse(_message.Message):
    __slots__ = ("status",)
    STATUS_FIELD_NUMBER: _ClassVar[int]
    status: _vdss_types_pb2.Status
    def __init__(self, status: _Optional[_Union[_vdss_types_pb2.Status, _Mapping]] = ...) -> None: ...

class HealthCheckRequest(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class HealthCheckResponse(_message.Message):
    __slots__ = ("status", "version", "uptime_seconds")
    STATUS_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    UPTIME_SECONDS_FIELD_NUMBER: _ClassVar[int]
    status: _vdss_types_pb2.Status
    version: str
    uptime_seconds: int
    def __init__(self, status: _Optional[_Union[_vdss_types_pb2.Status, _Mapping]] = ..., version: _Optional[str] = ..., uptime_seconds: _Optional[int] = ...) -> None: ...
