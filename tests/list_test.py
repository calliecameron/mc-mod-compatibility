import requests_mock

from mrpack_utils.commands.list import (
    _empty_row,
    _headers,
    _modpack_data,
    _mods,
    _other_files,
    _unknown_mods,
    run,
)
from mrpack_utils.mods import (
    Env,
    GameVersion,
    Mod,
    Modpack,
    Requirement,
)
from mrpack_utils.output import IncompatibleMods, MissingMods, Table


class TestList:
    def test_headers(self) -> None:
        assert _headers(set(), False) == [
            "Name",
            "Link",
            "Installed version",
            "On client",
            "On server",
            "Latest game version",
        ]

        assert _headers({GameVersion("1.20"), GameVersion("1.19")}, False) == [
            "Name",
            "Link",
            "Installed version",
            "On client",
            "On server",
            "Latest game version",
            "1.19",
            "1.20",
        ]

        assert _headers(set(), True) == [
            "Name",
            "Link",
            "Installed version",
            "On client",
            "On server",
            "Latest game version",
            "License",
            "Modrinth client",
            "Modrinth server",
            "Source",
            "Issues",
        ]

        assert _headers({GameVersion("1.20"), GameVersion("1.19")}, True) == [
            "Name",
            "Link",
            "Installed version",
            "On client",
            "On server",
            "Latest game version",
            "1.19",
            "1.20",
            "License",
            "Modrinth client",
            "Modrinth server",
            "Source",
            "Issues",
        ]

    def test_empty_row(self) -> None:
        assert _empty_row(["a", "b", "c"]) == ["", "", ""]

    def test_modpack_data(self) -> None:
        modpack = Modpack(
            name="Test Modpack",
            version="1",
            game_version=GameVersion("1.19.4"),
            dependencies={"Foo": "1", "fabric-loader": "0.16"},
            mods={},
            missing_mods=set(),
            unknown_mods={},
            other_files={},
        )
        assert _modpack_data(modpack, _headers({GameVersion("1.19.2")}, False)) == [
            ["modpack: Test Modpack", "", "1", "", "", "", ""],
            ["minecraft", "", "1.19.4", "", "", "", ""],
            ["fabric-loader", "", "0.16", "", "", "", ""],
            ["Foo", "", "1", "", "", "", ""],
        ]

    def test_mods(self) -> None:
        foo = Mod(
            name="Foo",
            slug="foo",
            version="1.2.3",
            original_env=Env(client=Requirement.OPTIONAL, server=Requirement.OPTIONAL),
            overridden_env=Env(client=Requirement.REQUIRED, server=Requirement.OPTIONAL),
            mod_license="MIT",
            source_url="example.com",
            issues_url="example2.com",
            game_versions=frozenset([GameVersion("1.20"), GameVersion("1.19.4")]),
        )
        bar = Mod(
            name="Bar",
            slug="bar",
            version="4.5.6",
            original_env=Env(client=Requirement.REQUIRED, server=Requirement.REQUIRED),
            overridden_env=Env(client=Requirement.REQUIRED, server=Requirement.OPTIONAL),
            mod_license="GPL",
            source_url="",
            issues_url="",
            game_versions=frozenset([GameVersion("1.19.4"), GameVersion("1.19.2")]),
        )
        modpack = Modpack(
            name="Test Modpack",
            version="1",
            game_version=GameVersion("1.19.4"),
            dependencies={"foo": "1", "fabric-loader": "0.16"},
            mods={"abcd": foo, "fedc": bar},
            missing_mods=frozenset(),
            unknown_mods={},
            other_files={},
        )

        mods, incompatible = _mods(
            modpack,
            frozenset([GameVersion("1.19.4"), GameVersion("1.20")]),
            False,
        )
        assert mods == [
            [
                "Bar",
                "https://modrinth.com/mod/bar",
                "4.5.6",
                "required",
                "optional",
                "1.19.4",
                "yes",
                "no",
            ],
            [
                "Foo",
                "https://modrinth.com/mod/foo",
                "1.2.3",
                "required",
                "optional",
                "1.20",
                "yes",
                "yes",
            ],
        ]
        assert incompatible == {
            GameVersion("1.19.4"): frozenset(),
            GameVersion("1.20"): frozenset([bar]),
        }

        mods, incompatible = _mods(
            modpack,
            frozenset([GameVersion("1.19.4"), GameVersion("1.20")]),
            True,
        )
        assert mods == [
            [
                "Bar",
                "https://modrinth.com/mod/bar",
                "4.5.6",
                "required",
                "optional",
                "1.19.4",
                "yes",
                "no",
                "GPL",
                "required",
                "required",
                "",
                "",
            ],
            [
                "Foo",
                "https://modrinth.com/mod/foo",
                "1.2.3",
                "required",
                "optional",
                "1.20",
                "yes",
                "yes",
                "MIT",
                "optional",
                "optional",
                "example.com",
                "example2.com",
            ],
        ]
        assert incompatible == {
            GameVersion("1.19.4"): frozenset(),
            GameVersion("1.20"): frozenset([bar]),
        }

    def test_unknown_mods(self) -> None:
        modpack = Modpack(
            name="Test Modpack",
            version="1",
            game_version=GameVersion("1.19.4"),
            dependencies={},
            mods={},
            missing_mods=set(),
            unknown_mods={"Foo": "a", "bar": "b"},
            other_files={},
        )

        assert _unknown_mods(modpack, {GameVersion("1.19.2")}, False) == [
            [
                "bar",
                "unknown - probably CurseForge",
                "b",
                "unknown",
                "unknown",
                "unknown",
                "check manually",
            ],
            [
                "Foo",
                "unknown - probably CurseForge",
                "a",
                "unknown",
                "unknown",
                "unknown",
                "check manually",
            ],
        ]

        assert _unknown_mods(modpack, {GameVersion("1.19.2")}, True) == [
            [
                "bar",
                "unknown - probably CurseForge",
                "b",
                "unknown",
                "unknown",
                "unknown",
                "check manually",
                "",
                "",
                "",
                "",
                "",
            ],
            [
                "Foo",
                "unknown - probably CurseForge",
                "a",
                "unknown",
                "unknown",
                "unknown",
                "check manually",
                "",
                "",
                "",
                "",
                "",
            ],
        ]

    def test_other_files(self) -> None:
        modpack = Modpack(
            name="Test Modpack",
            version="1",
            game_version=GameVersion("1.19.4"),
            dependencies={},
            mods={},
            missing_mods=set(),
            unknown_mods={},
            other_files={"Foo": "a", "bar": "b"},
        )
        assert _other_files(modpack, _headers({GameVersion("1.19.2")}, False)) == [
            ["bar", "non-mod file", "b", "", "", "", ""],
            ["Foo", "non-mod file", "a", "", "", "", ""],
        ]

    def test_run_normal(self) -> None:
        with requests_mock.Mocker() as m:
            m.post(
                "https://api.modrinth.com/v2/version_files",
                json={
                    "abcd": {
                        "project_id": "baz",
                        "version_number": "1.2.3",
                        "files": [
                            {
                                "hashes": {
                                    "sha512": "abcd",
                                },
                            },
                            {
                                "hashes": {
                                    "sha512": "wxyz",
                                },
                            },
                        ],
                    },
                    "fedc": {
                        "project_id": "quux",
                        "version_number": "4.5.6",
                        "files": [
                            {
                                "hashes": {
                                    "sha512": "fedc",
                                },
                            },
                        ],
                    },
                },
            )
            m.get(
                'https://api.modrinth.com/v2/projects?ids=["baz", "quux"]',
                complete_qs=True,
                json=[
                    {
                        "id": "baz",
                        "title": "Foo",
                        "slug": "foo",
                        "game_versions": ["1.19.2", "1.20"],
                        "client_side": "optional",
                        "server_side": "required",
                        "license": {"id": "MIT"},
                        "source_url": "example.com",
                        "issues_url": "example2.com",
                    },
                    {
                        "id": "quux",
                        "title": "Bar",
                        "slug": "bar",
                        "game_versions": ["1.19.4"],
                    },
                ],
            )
            assert run("testdata/test1.mrpack", frozenset([GameVersion("1.20")]), False) == (
                Table(
                    [
                        [
                            "Name",
                            "Link",
                            "Installed version",
                            "On client",
                            "On server",
                            "Latest game version",
                            "1.19.4",
                            "1.20",
                        ],
                        [
                            "modpack: Test Modpack",
                            "",
                            "1.1",
                            "",
                            "",
                            "",
                            "",
                            "",
                        ],
                        [
                            "minecraft",
                            "",
                            "1.19.4",
                            "",
                            "",
                            "",
                            "",
                            "",
                        ],
                        [
                            "fabric-loader",
                            "",
                            "0.16",
                            "",
                            "",
                            "",
                            "",
                            "",
                        ],
                        [
                            "foo",
                            "",
                            "1",
                            "",
                            "",
                            "",
                            "",
                            "",
                        ],
                        [
                            "Bar",
                            "https://modrinth.com/mod/bar",
                            "4.5.6",
                            "unknown",
                            "unknown",
                            "1.19.4",
                            "yes",
                            "no",
                        ],
                        [
                            "Foo",
                            "https://modrinth.com/mod/foo",
                            "1.2.3",
                            "required",
                            "optional",
                            "1.20",
                            "no",
                            "yes",
                        ],
                        [
                            "client-overrides/mods/baz-1.0.0.jar",
                            "unknown - probably CurseForge",
                            "a2c6f513",
                            "unknown",
                            "unknown",
                            "unknown",
                            "check manually",
                            "check manually",
                        ],
                        [
                            "client-overrides/mods/foo-1.2.3.jar",
                            "unknown - probably CurseForge",
                            "d6902afc",
                            "unknown",
                            "unknown",
                            "unknown",
                            "check manually",
                            "check manually",
                        ],
                        [
                            "overrides/mods/foo-1.2.3.jar",
                            "unknown - probably CurseForge",
                            "d6902afc",
                            "unknown",
                            "unknown",
                            "unknown",
                            "check manually",
                            "check manually",
                        ],
                        [
                            "server-overrides/mods/bar-1.0.0.jar",
                            "unknown - probably CurseForge",
                            "7123eea6",
                            "unknown",
                            "unknown",
                            "unknown",
                            "check manually",
                            "check manually",
                        ],
                        [
                            "overrides/config/foo.txt",
                            "non-mod file",
                            "7e3265a8",
                            "",
                            "",
                            "",
                            "",
                            "",
                        ],
                        [
                            "server-overrides/config/bar.txt",
                            "non-mod file",
                            "04a2b3e9",
                            "",
                            "",
                            "",
                            "",
                            "",
                        ],
                    ],
                ),
                MissingMods(
                    {"baz.jar"},
                ),
                IncompatibleMods(
                    num_mods=2,
                    game_version="1.19.4",
                    mods={"Foo"},
                    curseforge_warning=True,
                ),
                IncompatibleMods(
                    num_mods=2,
                    game_version="1.20",
                    mods={"Bar"},
                    curseforge_warning=True,
                ),
            )

    def test_run_dev(self) -> None:
        with requests_mock.Mocker() as m:
            m.post(
                "https://api.modrinth.com/v2/version_files",
                json={
                    "abcd": {
                        "project_id": "baz",
                        "version_number": "1.2.3",
                        "files": [
                            {
                                "hashes": {
                                    "sha512": "abcd",
                                },
                            },
                            {
                                "hashes": {
                                    "sha512": "wxyz",
                                },
                            },
                        ],
                    },
                    "fedc": {
                        "project_id": "quux",
                        "version_number": "4.5.6",
                        "files": [
                            {
                                "hashes": {
                                    "sha512": "fedc",
                                },
                            },
                        ],
                    },
                },
            )
            m.get(
                'https://api.modrinth.com/v2/projects?ids=["baz", "quux"]',
                complete_qs=True,
                json=[
                    {
                        "id": "baz",
                        "title": "Foo",
                        "slug": "foo",
                        "game_versions": ["1.19.2", "1.20"],
                        "client_side": "optional",
                        "server_side": "required",
                        "license": {"id": "MIT"},
                        "source_url": "example.com",
                        "issues_url": "example2.com",
                    },
                    {
                        "id": "quux",
                        "title": "Bar",
                        "slug": "bar",
                        "game_versions": ["1.19.4"],
                    },
                ],
            )
            assert run("testdata/test1.mrpack", frozenset([GameVersion("1.20")]), True) == (
                Table(
                    [
                        [
                            "Name",
                            "Link",
                            "Installed version",
                            "On client",
                            "On server",
                            "Latest game version",
                            "1.19.4",
                            "1.20",
                            "License",
                            "Modrinth client",
                            "Modrinth server",
                            "Source",
                            "Issues",
                        ],
                        [
                            "modpack: Test Modpack",
                            "",
                            "1.1",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                        ],
                        [
                            "minecraft",
                            "",
                            "1.19.4",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                        ],
                        [
                            "fabric-loader",
                            "",
                            "0.16",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                        ],
                        [
                            "foo",
                            "",
                            "1",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                        ],
                        [
                            "Bar",
                            "https://modrinth.com/mod/bar",
                            "4.5.6",
                            "unknown",
                            "unknown",
                            "1.19.4",
                            "yes",
                            "no",
                            "",
                            "unknown",
                            "unknown",
                            "",
                            "",
                        ],
                        [
                            "Foo",
                            "https://modrinth.com/mod/foo",
                            "1.2.3",
                            "required",
                            "optional",
                            "1.20",
                            "no",
                            "yes",
                            "MIT",
                            "optional",
                            "required",
                            "example.com",
                            "example2.com",
                        ],
                        [
                            "client-overrides/mods/baz-1.0.0.jar",
                            "unknown - probably CurseForge",
                            "a2c6f513",
                            "unknown",
                            "unknown",
                            "unknown",
                            "check manually",
                            "check manually",
                            "",
                            "",
                            "",
                            "",
                            "",
                        ],
                        [
                            "client-overrides/mods/foo-1.2.3.jar",
                            "unknown - probably CurseForge",
                            "d6902afc",
                            "unknown",
                            "unknown",
                            "unknown",
                            "check manually",
                            "check manually",
                            "",
                            "",
                            "",
                            "",
                            "",
                        ],
                        [
                            "overrides/mods/foo-1.2.3.jar",
                            "unknown - probably CurseForge",
                            "d6902afc",
                            "unknown",
                            "unknown",
                            "unknown",
                            "check manually",
                            "check manually",
                            "",
                            "",
                            "",
                            "",
                            "",
                        ],
                        [
                            "server-overrides/mods/bar-1.0.0.jar",
                            "unknown - probably CurseForge",
                            "7123eea6",
                            "unknown",
                            "unknown",
                            "unknown",
                            "check manually",
                            "check manually",
                            "",
                            "",
                            "",
                            "",
                            "",
                        ],
                        [
                            "overrides/config/foo.txt",
                            "non-mod file",
                            "7e3265a8",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                        ],
                        [
                            "server-overrides/config/bar.txt",
                            "non-mod file",
                            "04a2b3e9",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                            "",
                        ],
                    ],
                ),
                MissingMods(
                    {"baz.jar"},
                ),
                IncompatibleMods(
                    num_mods=2,
                    game_version="1.19.4",
                    mods={"Foo"},
                    curseforge_warning=True,
                ),
                IncompatibleMods(
                    num_mods=2,
                    game_version="1.20",
                    mods={"Bar"},
                    curseforge_warning=True,
                ),
            )
