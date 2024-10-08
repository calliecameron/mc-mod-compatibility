import csv
import io
from abc import ABC, abstractmethod
from collections.abc import Sequence, Set

import tabulate
from attrs import field, frozen


def _frozenset_converter(data: Set[str]) -> frozenset[str]:
    return frozenset(data)


def _table_converter(data: Sequence[Sequence[str]]) -> tuple[tuple[str, ...], ...]:
    return tuple(tuple(row) for row in data)


class Element(ABC):
    @abstractmethod
    def render(self) -> str:  # pragma nocover
        raise NotImplementedError


@frozen
class Table(Element):
    data: tuple[tuple[str, ...], ...] = field(converter=_table_converter)

    def render(self) -> str:
        return tabulate.tabulate(self.data, headers="firstrow", tablefmt="github")

    def render_csv(self) -> str:
        with io.StringIO() as f:
            csv.writer(f, lineterminator="\n").writerows(self.data)
            return f.getvalue().rstrip()


@frozen
class MissingMods(Element):
    mods: frozenset[str] = field(converter=_frozenset_converter)

    def render(self) -> str:
        out = []
        if self.mods:
            out.append("Mods supposed to be on Modrinth, but not found:")
            out += ["  " + item for item in sorted(self.mods, key=lambda i: i.lower())]
        return "\n".join(out)


@frozen
class IncompatibleMods(Element):
    num_mods: int
    game_version: str
    mods: frozenset[str] = field(converter=_frozenset_converter)
    curseforge_warning: bool

    def render(self) -> str:
        modrinth = ""
        warning = ""
        if self.curseforge_warning:
            modrinth = " Modrinth"
            warning = " (CurseForge mods must be checked manually)"

        out = []
        out.append(f"For version {self.game_version}:")
        if self.mods:
            out.append(
                f"  {len(self.mods)} out of {self.num_mods}{modrinth} mods are incompatible with "
                f"this version{warning}:",
            )
            out += ["    " + mod for mod in sorted(self.mods, key=lambda m: m.lower())]
        else:
            out.append(f"  All{modrinth} mods are compatible with this version{warning}")
        return "\n".join(out)


def render(elements: Sequence[Element]) -> str:
    items = [element.render() for element in elements]
    return "\n\n".join([item for item in items if item])


def render_csv(elements: Sequence[Element]) -> str:
    for element in elements:
        if isinstance(element, Table):
            return element.render_csv()
    return ""
