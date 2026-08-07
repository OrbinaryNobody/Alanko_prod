from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class UploadMediaPayload:
    message: str
    file_url: str
    uploaded_by: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "message": self.message,
            "file_url": self.file_url,
            "uploaded_by": self.uploaded_by,
        }
