
from dataclasses import dataclass

@dataclass(frozen=True)
class FolderPaths:
    cache: str
    chapter: str

@dataclass(frozen=True)
class FilePaths:
    result: str

@dataclass(frozen=True)
class Config:
    chapter: str
    description: str
    scenes: list[str]
    folders: FolderPaths
    files: FilePaths
