from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from typing import Optional


class Type(Enum):
    str = str
    int = int
    float = float
    bool = bool


@dataclass
class KeyValuePair:

    @classmethod
    def from_dict(cls, d: dict) -> KeyValuePair:
        obj = cls()

        for key, val in d.items():
            # i am losing my mind
            annotation = obj.__annotations__[key].removeprefix("Optional[").removesuffix("]")

            if annotation == "bool":
                val = int(val)

            convertion_type = Type[annotation]
            setattr(obj, key, convertion_type.value(val))

        return obj


@dataclass
class General(KeyValuePair):
    AudioFilename: Optional[str] = None
    AudioLeadIn: Optional[int] = None
    AudioHash: Optional[str] = None
    PreviewTime: Optional[int] = None
    Countdown: Optional[int] = None
    SampleSet: Optional[str] = None
    StackLeniency: Optional[float] = None
    Mode: Optional[int] = None
    LetterboxInBreaks: Optional[bool] = None
    StoryFireInFront: Optional[bool] = None
    UseSkinSprite: Optional[bool] = None
    AlwayShowPlayfield: Optional[bool] = None
    OverlayPosition: Optional[str] = None
    SkinPreference: Optional[str] = None
    EpilepsyWarning: Optional[bool] = None
    CountdownOffset: Optional[int] = None
    SpecialStyle: Optional[bool] = None
    WidescreenStoryboard: Optional[bool] = None
    SampleMatchPlaybackRate: Optional[bool] = None

@dataclass
class Editor(KeyValuePair):
    Bookmarks: Optional[str] = None # comma separated list of ints
    DistanceSpacing: Optional[float] = None
    BeatDivisor: Optional[int] = None
    GridSize: Optional[int] = None
    TimelineZoom: Optional[float] = None

@dataclass
class Metadata(KeyValuePair):
    Title: Optional[str] = None
    TitleUnicode: Optional[str] = None
    Artist: Optional[str] = None
    ArtistUnicode: Optional[str] = None
    Creator: Optional[str] = None
    Version: Optional[str] = None
    Source: Optional[str] = None
    Tags: Optional[str] = None # space separated list of strings
    BeatmapID: Optional[int] = None
    BeatmapSetID: Optional[int] = None

@dataclass
class Difficulty(KeyValuePair):
    HPDrainRate: Optional[float] = None
    CircleSize: Optional[float] = None
    OverallDifficulty: Optional[float] = None
    ApproachRate: Optional[float] = None
    SliderMultiplier: Optional[float] = None
    SliderTickRate: Optional[float] = None

@dataclass
class TimingPoint:
    time: Optional[int] = None
    beatLength: Optional[float] = None
    meter: Optional[int] = None
    sampleSet: Optional[int] = None
    sampleIndex: Optional[int] = None
    volume: Optional[int] = None
    uninherited: Optional[bool] = None
    effects: Optional[int] = None

    @classmethod
    def from_line(cls, line: str) -> TimingPoint:
        time,beatLength,meter,sampleSet,sampleIndex,volume,uninherited,effects = line.split(",")
        return cls(int(time), float(beatLength),
        int(meter), int(sampleSet), int(sampleIndex),
        int(volume), bool(int(uninherited)), int(effects))

@dataclass
class HitObject:
    x: int
    y: int
    time: int
    type: int

@dataclass
class Beatmap:
    general: General
    editor: Editor
    metadata: Metadata
    difficulty: Difficulty
    timingpoints: list[TimingPoint]
    hitobjects: list[HitObject]

    @staticmethod
    def _parse_pair(lines: list[str], section_name: str, obj: KeyValuePair) -> KeyValuePair:
        d = {}

        for line in lines[lines.index(section_name) + 1:]:
            if line[0] + line[-1] == "[]":
                break

            key, val = line.split(":")
            key, val = key.strip(), val.strip()
            d[key] = val

        return obj.from_dict(d)

    @staticmethod
    def _parse_timingpoints(lines: list[str]) -> list[TimingPoint]:
        timingpoints = []

        for line in lines[lines.index("[TimingPoints]") + 1:]:
            if line[0] + line[-1] == "[]":
                break

            timingpoints.append(TimingPoint.from_line(line))
        return timingpoints

    def _parse_hitobjects(lines: list[str]) -> list[HitObject]:
        hitobjects = []

        for line in lines[lines.index("[HitObjects]") + 1:]:
            if line[0] + line[-1] == "[]":
                break

            s = line.split(",")
            x, y, time, type = int(s[0]), int(s[1]), int(s[2]), int(s[3])
            hitobjects.append(HitObject(x, y, time, type))
        return hitobjects

    @staticmethod
    def _get_lines(path: Path) -> list[str]:
        lines = []

        with open(path, "r", errors="ignore") as f:
            for line in f.readlines():
                line = line.strip()

                if not line:
                    continue
                if line[0] + line[1] == "//":
                    continue

                lines.append(line)
        return lines

    @classmethod
    def from_path(cls, path: Path) -> Beatmap:
        lines = cls._get_lines(path)

        general = cls._parse_pair(lines, "[General]", General)
        editor = cls._parse_pair(lines, "[Editor]", Editor)
        metadata = cls._parse_pair(lines, "[Metadata]", Metadata)
        difficulty = cls._parse_pair(lines, "[Difficulty]", Difficulty)
        timingpoints = cls._parse_timingpoints(lines)
        hitobjects = cls._parse_hitobjects(lines)

        return cls(general, editor, metadata,
        difficulty, timingpoints, hitobjects)
