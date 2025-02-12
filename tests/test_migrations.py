"""Test the Yamaha (YNCA) config flow migration."""
from __future__ import annotations

from unittest.mock import patch
import pytest

from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    mock_registry,
    mock_device_registry,
)

import custom_components.yamaha_ynca as yamaha_ynca
from custom_components.yamaha_ynca.const import CONF_HIDDEN_SOUND_MODES, DOMAIN
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant


@pytest.fixture
def device_reg(hass):
    """Return an empty, loaded, registry."""
    return mock_device_registry(hass)


async def test_async_migration_entry(hass: HomeAssistant):
    """Full chain of migrations should result in last version"""

    old_entry = MockConfigEntry(
        domain=yamaha_ynca.DOMAIN,
        entry_id="entry_id",
        title="ModelName",
        data={"serial_port": "SerialPort"},
        version=1,
    )
    old_entry.add_to_hass(hass)

    migration_success = await yamaha_ynca.async_migrate_entry(hass, old_entry)
    await hass.async_block_till_done()

    assert migration_success == True

    new_entry = hass.config_entries.async_get_entry(old_entry.entry_id)
    assert new_entry.version == 7


async def test_async_migration_entry_version_v1_to_v2(hass: HomeAssistant):

    old_entry = MockConfigEntry(
        domain=yamaha_ynca.DOMAIN,
        entry_id="entry_id",
        title="ModelName",
        data={"serial_port": "SerialPort"},
        version=1,
    )
    old_entry.add_to_hass(hass)

    mock_entity_registry = mock_registry(hass)
    mock_button_entity_entry = mock_entity_registry.async_get_or_create(
        Platform.BUTTON,
        yamaha_ynca.DOMAIN,
        "button.scene_button",
        config_entry=old_entry,
        device_id="device_id",
    )
    assert len(mock_entity_registry.entities) == 1  # Make sure entities were added

    # Migrate
    with patch(
        "homeassistant.helpers.entity_registry.async_get",
        return_value=mock_entity_registry,
    ):
        yamaha_ynca.migrations.migrate_v1_to_v2(hass, old_entry)
    await hass.async_block_till_done()

    # Button entities removed
    assert len(mock_entity_registry.entities) == 0

    # Serial_port renamed to serial_url
    new_entry = hass.config_entries.async_get_entry(old_entry.entry_id)
    assert new_entry.version == 2
    assert new_entry.data["serial_url"] == "SerialPort"


async def test_async_migration_entry_version_v2_to_v3(hass: HomeAssistant):

    old_entry = MockConfigEntry(
        domain=yamaha_ynca.DOMAIN,
        entry_id="entry_id",
        title="ModelName",
        data={"serial_url": "SerialUrl"},
        version=2,
    )
    old_entry.add_to_hass(hass)

    mock_entity_registry = mock_registry(hass)
    mock_scene_entity_entry = mock_entity_registry.async_get_or_create(
        Platform.SCENE,
        yamaha_ynca.DOMAIN,
        "scene.scene_button",
        config_entry=old_entry,
        device_id="device_id",
    )
    assert len(mock_entity_registry.entities) == 1  # Make sure entities were added

    # Migrate
    with patch(
        "homeassistant.helpers.entity_registry.async_get",
        return_value=mock_entity_registry,
    ):
        yamaha_ynca.migrations.migrate_v2_to_v3(hass, old_entry)
    await hass.async_block_till_done()

    # Scene entities removed
    assert len(mock_entity_registry.entities) == 0

    new_entry = hass.config_entries.async_get_entry(old_entry.entry_id)
    assert new_entry.version == 3


async def test_async_migration_entry_version_v3_to_v4_hidden_soundmodes(
    hass: HomeAssistant,
):

    old_entry = MockConfigEntry(
        domain=yamaha_ynca.DOMAIN,
        entry_id="entry_id",
        title="ModelName",
        data={"serial_url": "SerialUrl"},
        options={CONF_HIDDEN_SOUND_MODES: ["CHURCH_IN_ROYAUMONT", "UNSUPPORTED"]},
        version=3,
    )
    old_entry.add_to_hass(hass)

    # Migrate
    yamaha_ynca.migrations.migrate_v3_to_v4(hass, old_entry)
    await hass.async_block_till_done()

    # Hidden soundmodes are translated from enum name to value
    new_entry = hass.config_entries.async_get_entry(old_entry.entry_id)
    assert new_entry.version == 4
    assert new_entry.options[CONF_HIDDEN_SOUND_MODES] == ["Church in Royaumont"]


async def test_async_migration_entry_version_v3_to_v4_no_hidden_soundmodes(
    hass: HomeAssistant,
):

    old_entry = MockConfigEntry(
        domain=yamaha_ynca.DOMAIN,
        entry_id="entry_id",
        title="ModelName",
        data={"serial_url": "SerialUrl"},
        version=3,
    )
    old_entry.add_to_hass(hass)

    # Migrate
    yamaha_ynca.migrations.migrate_v3_to_v4(hass, old_entry)
    await hass.async_block_till_done()

    # Hidden soundmodes are translated from enum name to value
    new_entry = hass.config_entries.async_get_entry(old_entry.entry_id)
    assert new_entry.version == 4
    assert new_entry.options.get(CONF_HIDDEN_SOUND_MODES, None) is None


async def test_async_migration_entry_version_v4_to_v5_is_ipaddress(hass: HomeAssistant):

    old_entry = MockConfigEntry(
        domain=yamaha_ynca.DOMAIN,
        entry_id="entry_id",
        title="ModelName",
        data={"serial_url": "1.2.3.4"},
        version=4,
    )
    old_entry.add_to_hass(hass)

    yamaha_ynca.migrations.migrate_v4_to_v5(hass, old_entry)
    await hass.async_block_till_done()

    # IP address converted to socket:// url
    new_entry = hass.config_entries.async_get_entry(old_entry.entry_id)
    assert new_entry.version == 5
    assert new_entry.data["serial_url"] == "socket://1.2.3.4:50000"


async def test_async_migration_entry_version_v4_to_v5_is_ipaddress_and_port(
    hass: HomeAssistant,
):

    old_entry = MockConfigEntry(
        domain=yamaha_ynca.DOMAIN,
        entry_id="entry_id",
        title="ModelName",
        data={"serial_url": "1.2.3.4:56789"},
        version=4,
    )
    old_entry.add_to_hass(hass)

    yamaha_ynca.migrations.migrate_v4_to_v5(hass, old_entry)
    await hass.async_block_till_done()

    # IP address converted to socket:// url
    new_entry = hass.config_entries.async_get_entry(old_entry.entry_id)
    assert new_entry.version == 5
    assert new_entry.data["serial_url"] == "socket://1.2.3.4:56789"


async def test_async_migration_entry_version_v4_to_v5_is_not_ipaddress(
    hass: HomeAssistant,
):

    old_entry = MockConfigEntry(
        domain=yamaha_ynca.DOMAIN,
        entry_id="entry_id",
        title="ModelName",
        data={"serial_url": "not an ip address"},
        version=4,
    )
    old_entry.add_to_hass(hass)

    yamaha_ynca.migrations.migrate_v4_to_v5(hass, old_entry)
    await hass.async_block_till_done()

    # IP address converted to socket:// url
    new_entry = hass.config_entries.async_get_entry(old_entry.entry_id)
    assert new_entry.version == 5
    assert new_entry.data["serial_url"] == "not an ip address"


async def test_async_migration_entry_version_v5_to_v6(hass: HomeAssistant):

    old_entry = MockConfigEntry(
        domain=yamaha_ynca.DOMAIN,
        entry_id="entry_id",
        title="ModelName",
        data={"serial_url": "SerialUrl"},
        options={
            "hidden_sound_modes": ["Church in Royaumont"],
            "hidden_inputs_MAIN": [],
            "hidden_inputs_ZONE3": ["V-AUX", "USB", "iPod (USB)", "AUDIO2", "AUDIO1"],
        },
        version=5,
    )
    old_entry.add_to_hass(hass)

    # Migrate
    yamaha_ynca.migrations.migrate_v5_to_v6(hass, old_entry)
    await hass.async_block_till_done()

    # Entry is migrated to new structure
    new_entry = hass.config_entries.async_get_entry(old_entry.entry_id)
    assert new_entry.version == 6
    assert new_entry.data["modelname"] == "ModelName"
    assert new_entry.options["hidden_sound_modes"] == ["Church in Royaumont"]
    assert (
        "MAIN" not in new_entry.options
    )  # Main was empty/falsey so does not get migrated
    assert "ZONE2" not in new_entry.options
    assert "ZONE4" not in new_entry.options
    assert new_entry.options["ZONE3"]["hidden_inputs"] == [
        "V-AUX",
        "USB",
        "iPod (USB)",
        "AUDIO2",
        "AUDIO1",
    ]


async def test_async_migration_entry_version_v5_to_v6_no_data(hass: HomeAssistant):

    old_entry = MockConfigEntry(
        domain=yamaha_ynca.DOMAIN,
        entry_id="entry_id",
        title="ModelName",
        data={"serial_url": "SerialUrl"},
        version=5,
    )
    old_entry.add_to_hass(hass)

    # Migrate
    yamaha_ynca.migrations.migrate_v5_to_v6(hass, old_entry)
    await hass.async_block_till_done()

    # Entry is migrated to new structure
    new_entry = hass.config_entries.async_get_entry(old_entry.entry_id)
    assert new_entry.version == 6
    assert new_entry.data["modelname"] == "ModelName"
    assert "general" not in new_entry.options
    assert "MAIN" not in new_entry.options
    assert "ZONE2" not in new_entry.options
    assert "ZONE3" not in new_entry.options
    assert "ZONE4" not in new_entry.options


async def test_async_migration_entry_version_v6_to_v7(device_reg, hass: HomeAssistant):

    config_entry = MockConfigEntry(
        domain=yamaha_ynca.DOMAIN,
        entry_id="entry_id",
        title="ModelName",
        data={"serial_url": "SerialUrl"},
        version=2,
    )
    config_entry.add_to_hass(hass)

    device_entry_before = device_reg.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={(DOMAIN, "entry_id")},
    )
    assert len(device_reg.devices) == 1  # Sanitycheck that setup was ok

    # Migrate
    with patch(
        "homeassistant.helpers.device_registry.async_get",
        return_value=device_reg,
    ):
        yamaha_ynca.migrations.migrate_v6_to_v7(hass, config_entry)
        await hass.async_block_till_done()

    assert len(device_reg.devices) == 1  # Still only 1 device
    device_entry_after = device_reg.async_get_device({(DOMAIN, "entry_id_MAIN")})
    assert device_entry_after is not None
    assert device_entry_after.config_entries == device_entry_before.config_entries

    new_entry = hass.config_entries.async_get_entry(config_entry.entry_id)
    assert new_entry.version == 7
