import shutil
from pathlib import Path

from app.services.storage.base import StorageService

class LocalStorageService(StorageService):

    def __init__(self, base_path: str | Path):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _resolve(self, storage_key: str) -> Path:
        path = self.base_path / storage_key

        resolved_base = self.base_path.resolve()
        resolved_path = path.resolve()

        if resolved_base not in resolved_path.parents and resolved_path != resolved_base:
            raise ValueError("Invalid storage key")

        return resolved_path

    def save(self, source_path: Path, storage_key: str) -> str:
        destination = self._resolve(storage_key)

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        shutil.copy2(
            source_path,
            destination,
        )

        return f"file://{destination}"

    def get(self, storage_key: str) -> Path:
        path = self._resolve(storage_key)

        if not path.exists():
            raise FileNotFoundError(
                f"Stored object not found: {storage_key}"
            )

        return path

    def exists(self, storage_key: str) -> bool:
        return self._resolve(storage_key).exists()

    def delete(self, storage_key: str) -> None:
        path = self._resolve(storage_key)

        if path.exists():
            path.unlink()