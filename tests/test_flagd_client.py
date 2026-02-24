"""Tests for FlagdClient."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from otelfl.core.flagd_client import (
    FlagdClient,
    FlagdError,
    FlagNotFoundError,
    InvalidVariantError,
)


class TestListFlags:
    def test_lists_all_flags(self, flagd_client: FlagdClient) -> None:
        flags = flagd_client.list_flags()
        assert len(flags) == 2
        names = {f.name for f in flags}
        assert names == {"boolFlag", "multiFlag"}

    def test_flag_variant_types(self, flagd_client: FlagdClient) -> None:
        flags = {f.name: f for f in flagd_client.list_flags()}
        assert flags["boolFlag"].variant_type == "boolean"
        assert flags["boolFlag"].is_boolean is True
        assert flags["multiFlag"].variant_type == "multi"
        assert flags["multiFlag"].is_boolean is False


class TestGetFlag:
    def test_get_existing_flag(self, flagd_client: FlagdClient) -> None:
        flag = flagd_client.get_flag("boolFlag")
        assert flag.name == "boolFlag"
        assert flag.default_variant == "off"
        assert flag.current_value is False

    def test_get_nonexistent_flag_raises(self, flagd_client: FlagdClient) -> None:
        with pytest.raises(FlagNotFoundError, match="nosuch"):
            flagd_client.get_flag("nosuch")


class TestSetFlag:
    def test_set_valid_variant(self, flagd_client: FlagdClient) -> None:
        flag = flagd_client.set_flag("boolFlag", "on")
        assert flag.default_variant == "on"
        assert flag.current_value is True
        # Verify persisted
        reloaded = flagd_client.get_flag("boolFlag")
        assert reloaded.default_variant == "on"

    def test_set_multi_variant(self, flagd_client: FlagdClient) -> None:
        flag = flagd_client.set_flag("multiFlag", "high")
        assert flag.default_variant == "high"
        assert flag.current_value == 75

    def test_set_invalid_variant_raises(self, flagd_client: FlagdClient) -> None:
        with pytest.raises(InvalidVariantError, match="invalid"):
            flagd_client.set_flag("boolFlag", "invalid")

    def test_set_nonexistent_flag_raises(self, flagd_client: FlagdClient) -> None:
        with pytest.raises(FlagNotFoundError):
            flagd_client.set_flag("nosuch", "on")


class TestToggleFlag:
    def test_toggle_boolean_flag(self, flagd_client: FlagdClient) -> None:
        flag = flagd_client.toggle_flag("boolFlag")
        assert flag.default_variant == "on"
        flag = flagd_client.toggle_flag("boolFlag")
        assert flag.default_variant == "off"

    def test_toggle_multi_variant_raises(self, flagd_client: FlagdClient) -> None:
        with pytest.raises(FlagdError, match="Cannot toggle"):
            flagd_client.toggle_flag("multiFlag")


class TestResetFlag:
    def test_reset_single_flag(self, flagd_client: FlagdClient) -> None:
        flagd_client.set_flag("boolFlag", "on")
        flag = flagd_client.reset_flag("boolFlag")
        assert flag.default_variant == "off"

    def test_reset_all_flags(self, flagd_client: FlagdClient) -> None:
        flagd_client.set_flag("boolFlag", "on")
        flagd_client.set_flag("multiFlag", "high")
        flags = flagd_client.reset_all()
        for f in flags:
            assert f.default_variant == "off"


class TestFileHandling:
    def test_missing_config_raises(self, tmp_path: Path) -> None:
        client = FlagdClient(tmp_path / "nonexistent.json")
        with pytest.raises(FlagdError, match="not found"):
            client.list_flags()

    def test_preserves_schema_key(self, config_file: Path, flagd_client: FlagdClient) -> None:
        flagd_client.set_flag("boolFlag", "on")
        data = json.loads(config_file.read_text())
        assert "$schema" in data

    def test_preserves_indent(self, config_file: Path, flagd_client: FlagdClient) -> None:
        flagd_client.set_flag("boolFlag", "on")
        text = config_file.read_text()
        # indent=2 means we expect 2-space indentation
        assert '  "flags"' in text


class TestFlagState:
    def test_set_flag_state_disabled(self, flagd_client: FlagdClient) -> None:
        flag = flagd_client.set_flag_state("boolFlag", "DISABLED")
        assert flag.state == "DISABLED"
        reloaded = flagd_client.get_flag("boolFlag")
        assert reloaded.state == "DISABLED"

    def test_set_flag_state_enabled(self, flagd_client: FlagdClient) -> None:
        flagd_client.set_flag_state("boolFlag", "DISABLED")
        flag = flagd_client.set_flag_state("boolFlag", "ENABLED")
        assert flag.state == "ENABLED"

    def test_toggle_flag_state(self, flagd_client: FlagdClient) -> None:
        flag = flagd_client.toggle_flag_state("boolFlag")
        assert flag.state == "DISABLED"
        flag = flagd_client.toggle_flag_state("boolFlag")
        assert flag.state == "ENABLED"

    def test_invalid_state_raises(self, flagd_client: FlagdClient) -> None:
        with pytest.raises(FlagdError, match="Invalid state"):
            flagd_client.set_flag_state("boolFlag", "INVALID")


class TestSnapshot:
    def test_get_snapshot(self, flagd_client: FlagdClient) -> None:
        snapshot = flagd_client.get_snapshot()
        assert snapshot == {"boolFlag": "off", "multiFlag": "off"}

    def test_apply_snapshot(self, flagd_client: FlagdClient) -> None:
        changes = flagd_client.apply_snapshot({"boolFlag": "on", "multiFlag": "high"})
        assert len(changes) == 2
        assert flagd_client.get_flag("boolFlag").default_variant == "on"
        assert flagd_client.get_flag("multiFlag").default_variant == "high"

    def test_apply_snapshot_skips_unknown_flags(self, flagd_client: FlagdClient) -> None:
        changes = flagd_client.apply_snapshot({"boolFlag": "on", "unknownFlag": "on"})
        assert len(changes) == 1

    def test_apply_snapshot_skips_unchanged(self, flagd_client: FlagdClient) -> None:
        changes = flagd_client.apply_snapshot({"boolFlag": "off"})
        assert len(changes) == 0


class TestWithRealConfig:
    def test_lists_14_flags(self, real_config_file: Path) -> None:
        client = FlagdClient(real_config_file)
        flags = client.list_flags()
        assert len(flags) == 14

    def test_real_flag_types(self, real_config_file: Path) -> None:
        client = FlagdClient(real_config_file)
        flags = {f.name: f for f in client.list_flags()}
        # Boolean flags
        assert flags["adHighCpu"].is_boolean is True
        assert flags["cartFailure"].is_boolean is True
        # Multi-variant flags
        assert flags["paymentFailure"].is_boolean is False
        assert len(flags["paymentFailure"].variants) == 7
        assert flags["emailMemoryLeak"].is_boolean is False

    def test_toggle_real_boolean_flag(self, real_config_file: Path) -> None:
        client = FlagdClient(real_config_file)
        flag = client.toggle_flag("adHighCpu")
        assert flag.default_variant == "on"
        flag = client.toggle_flag("adHighCpu")
        assert flag.default_variant == "off"

    def test_set_real_multi_flag(self, real_config_file: Path) -> None:
        client = FlagdClient(real_config_file)
        flag = client.set_flag("paymentFailure", "50%")
        assert flag.default_variant == "50%"
        assert flag.current_value == 0.5
