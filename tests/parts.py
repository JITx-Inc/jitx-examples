from dataclasses import dataclass
from pathlib import Path

from jitx.sample import SampleDesign
from jitxlib.parts import Lock, LockMode, PartSource
from jitxlib.parts.provider import CanonicalQuery, Outcome, Provider, Unsupported
from jitxlib.parts.policy import current_project, discovered_source
from jitxlib.parts.providers import IdealPassives

# The project this file belongs to, found from the file rather than from the
# working directory, so the suite resolves the same chain wherever pytest starts.
PROJECT = current_project(Path(__file__).parent)

# The keys `IdealPassives` honors. It ignores any other key in a query.
IDEAL_KEYS = frozenset({"resistance", "capacitance", "inductance", "case", "tolerance"})


@dataclass(frozen=True)
class PlainValueIdeal(IdealPassives):
    """`IdealPassives` that declines any query carrying a key it would ignore.

    In a build, `ideal` answers a query the catalogue cannot meet and drops its
    ratings, dielectric, mounting and so on. In a test that would hide a catalogue
    gap, so here such a query fails resolution instead.
    """

    def resolve_one(self, query: CanonicalQuery) -> Outcome:
        keys = set(query.filters) | {r.key for r in query.rank}
        ignored = tuple(sorted(keys - IDEAL_KEYS))
        if ignored:
            return Unsupported(ignored, "the test chain keeps these off ideal parts")
        return super().resolve_one(query)


def _test_chain() -> PartSource:
    members: list[Provider] = []
    for provider in discovered_source(PROJECT):
        if isinstance(provider, IdealPassives):
            provider = PlainValueIdeal(series=provider.series)
        members.append(provider)
    return PartSource(members)


class PartsTestDesign(SampleDesign):
    """Sample design that sources passives through the project's parts chain.

    ``parts`` is the chain ``[tool.jitx.parts]`` in ``pyproject.toml`` names: the
    packaged ``src/jitxexamples/parts/example-passives.csv`` first, then ``ideal``,
    which here answers only queries on value, case and tolerance
    (``PlainValueIdeal``).
    Locking is off so a test never writes a lockfile.
    """

    parts = _test_chain()
    parts_lock = Lock(mode=LockMode.OFF)
