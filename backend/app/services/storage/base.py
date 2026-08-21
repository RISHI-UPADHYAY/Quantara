from abc import ABC, abstractmethod
from pathlib import Path

class StorageService(ABC):

    @abstractmethod
    def save(self, source_path: Path, storage_key: str) -> str:
        """
        Store a file and return its storage URI
        """
        raise NotImplementedError

    @abstractmethod
    def get(self, storage_key: str) -> Path:
        """
        Resolve a storage key to a local readable path
        """
        raise NotImplementedError

    @abstractmethod
    def exists(self, storage_key: str) -> bool:
        """
        Check whether an object exists
        """
        raise NotImplementedError

    @abstractmethod
    def delete(self, storage_key: str) -> None:
        """
        Delete an object
        """

        raise NotImplementedError