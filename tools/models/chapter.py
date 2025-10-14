
from dataclasses import dataclass

@dataclass(frozen=True)
class FolderPaths:
    config: str
    output: str
    cache: str
    chapter: str

@dataclass(frozen=True)
class FilePaths:
    source: str
    cache: str
    result: str

@dataclass(frozen=True)
class Config:
    chapter: str
    description: str
    scenes: dict[str, str]
    folders: FolderPaths
    files: FilePaths
