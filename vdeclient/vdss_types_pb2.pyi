from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Iterable as _Iterable
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class CollectionState(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    READY: _ClassVar[CollectionState]
    REBUILDING: _ClassVar[CollectionState]
    ERROR: _ClassVar[CollectionState]
READY: CollectionState
REBUILDING: CollectionState
ERROR: CollectionState

class Vector(_message.Message):
    __slots__ = ("data", "dimension")
    DATA_FIELD_NUMBER: _ClassVar[int]
    DIMENSION_FIELD_NUMBER: _ClassVar[int]
    data: _containers.RepeatedScalarFieldContainer[float]
    dimension: int
    def __init__(self, data: _Optional[_Iterable[float]] = ..., dimension: _Optional[int] = ...) -> None: ...

class Payload(_message.Message):
    __slots__ = ("json",)
    JSON_FIELD_NUMBER: _ClassVar[int]
    json: str
    def __init__(self, json: _Optional[str] = ...) -> None: ...

class CollectionConfig(_message.Message):
    __slots__ = ("index_type", "storage_type", "dimension", "distance_metric", "config_json")
    INDEX_TYPE_FIELD_NUMBER: _ClassVar[int]
    STORAGE_TYPE_FIELD_NUMBER: _ClassVar[int]
    DIMENSION_FIELD_NUMBER: _ClassVar[int]
    DISTANCE_METRIC_FIELD_NUMBER: _ClassVar[int]
    CONFIG_JSON_FIELD_NUMBER: _ClassVar[int]
    index_type: str
    storage_type: str
    dimension: int
    distance_metric: str
    config_json: str
    def __init__(self, index_type: _Optional[str] = ..., storage_type: _Optional[str] = ..., dimension: _Optional[int] = ..., distance_metric: _Optional[str] = ..., config_json: _Optional[str] = ...) -> None: ...

class SearchResult(_message.Message):
    __slots__ = ("offset", "score")
    OFFSET_FIELD_NUMBER: _ClassVar[int]
    SCORE_FIELD_NUMBER: _ClassVar[int]
    offset: int
    score: float
    def __init__(self, offset: _Optional[int] = ..., score: _Optional[float] = ...) -> None: ...

class CollectionStats(_message.Message):
    __slots__ = ("total_vectors", "indexed_vectors", "deleted_vectors", "storage_bytes", "index_memory_bytes")
    TOTAL_VECTORS_FIELD_NUMBER: _ClassVar[int]
    INDEXED_VECTORS_FIELD_NUMBER: _ClassVar[int]
    DELETED_VECTORS_FIELD_NUMBER: _ClassVar[int]
    STORAGE_BYTES_FIELD_NUMBER: _ClassVar[int]
    INDEX_MEMORY_BYTES_FIELD_NUMBER: _ClassVar[int]
    total_vectors: int
    indexed_vectors: int
    deleted_vectors: int
    storage_bytes: int
    index_memory_bytes: int
    def __init__(self, total_vectors: _Optional[int] = ..., indexed_vectors: _Optional[int] = ..., deleted_vectors: _Optional[int] = ..., storage_bytes: _Optional[int] = ..., index_memory_bytes: _Optional[int] = ...) -> None: ...

class Status(_message.Message):
    __slots__ = ("code", "message")
    CODE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    code: int
    message: str
    def __init__(self, code: _Optional[int] = ..., message: _Optional[str] = ...) -> None: ...
