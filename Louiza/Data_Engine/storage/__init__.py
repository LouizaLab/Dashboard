"""
Storage layer with abstract interfaces
"""

from .interfaces import StorageBackend, VectorStore, MetadataStore
from .local_storage import LocalStorageBackend, LocalVectorStore, LocalMetadataStore

__all__ = [
    'StorageBackend',
    'VectorStore',
    'MetadataStore',
    'LocalStorageBackend',
    'LocalVectorStore',
    'LocalMetadataStore',
]

