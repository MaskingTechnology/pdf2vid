
from dataclasses import dataclass

@dataclass(frozen=True)
class VoiceOptions:
    text: str
    speed: float
    delay: float

@dataclass(frozen=True)
class FrameOptions:
    source: str
    start: int
    end: int
    duplications: str
    rate: int

@dataclass(frozen=True)
class FolderPaths:
    config: str
    chapter: str
    scene: str
    frames: str
    duplications: str

@dataclass(frozen=True)
class FilePaths:
    config: str
    voice: str
    video: str
    result: str

@dataclass(frozen=True)
class Config:
    chapter: str
    scene: str
    voice: VoiceOptions
    frames: FrameOptions
    folders: FolderPaths
    files: FilePaths
