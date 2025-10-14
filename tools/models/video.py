
from dataclasses import dataclass

@dataclass(frozen=True)
class FolderPaths:
    config: str
    output: str
    cache: str

@dataclass(frozen=True)
class FilePaths:
    source: str
    cache: str
    result: str

@dataclass(frozen=True)
class Config:
    video: str
    description: str
    chapters: list[str]
    folders: FolderPaths
    files: FilePaths
