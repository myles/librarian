import datetime
import typing as t
from copy import deepcopy
from dataclasses import dataclass, field

TEXT_FORMAT_LITERAL = t.Literal["dom", "plain", "html"]


@dataclass
class GeniusReferent:
    id: int

    data: t.Dict[str, t.Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_data(cls, data: t.Dict[str, t.Any]):
        defaults = deepcopy(data)

        safe_keys = ("id",)
        to_remove = [k for k in defaults.keys() if k not in safe_keys]
        for key in to_remove:
            del defaults[key]

        return cls(**defaults, data=data)


@dataclass
class GeniusSearchHit:
    id: int
    full_title: str
    type: str

    data: t.Dict[str, t.Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_data(cls, data: t.Dict[str, t.Any]):
        defaults = deepcopy(data)
        defaults_type = defaults.pop("type")
        defaults_result = defaults.pop("result")

        safe_keys = ("id", "full_title", "type")
        to_remove = [k for k in defaults_result.keys() if k not in safe_keys]
        for key in to_remove:
            del defaults_result[key]

        return cls(type=defaults_type, **defaults_result, data=data)


@dataclass
class GeniusSong:
    id: int
    title: str
    artist_names: str
    release_date: t.Optional[datetime.date] = None

    description_dom: t.Optional[t.Dict[str, t.Any]] = None
    description_html: t.Optional[str] = None
    description_plain: t.Optional[str] = None

    data: t.Dict[str, t.Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_data(cls, data: t.Dict[str, t.Any]):
        try:
            song_data = data["response"]["song"]
        except KeyError:
            raise ValueError("Provided data is not a song response.")

        defaults = deepcopy(song_data)

        safe_keys = (
            "id",
            "title",
            "artist_names",
            "release_date",
            "description",
        )
        to_remove = [k for k in defaults.keys() if k not in safe_keys]
        for key in to_remove:
            del defaults[key]

        if "release_date" in defaults:
            defaults["release_date"] = datetime.date.fromisoformat(
                defaults["release_date"]
            )

        description = defaults.pop("description", {})
        if "dom" in description:
            defaults["description_dom"] = description["dom"]
        elif "html" in description:
            defaults["description_html"] = description["html"]
        elif "plain" in description:
            defaults["description_plain"] = description["plain"]

        return cls(**defaults, data=song_data)
