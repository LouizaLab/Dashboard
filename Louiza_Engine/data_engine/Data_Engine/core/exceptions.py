"""
Custom exceptions for the Data Engine
"""


class DataEngineException(Exception):
    """Base exception for all data engine errors"""
    pass


class IngestionError(DataEngineException):
    """Error during data ingestion"""
    pass


class NormalizationError(DataEngineException):
    """Error during data normalization"""
    pass


class IndexingError(DataEngineException):
    """Error during indexing"""
    pass


class RetrievalError(DataEngineException):
    """Error during retrieval"""
    pass


class StorageError(DataEngineException):
    """Error with storage operations"""
    pass

