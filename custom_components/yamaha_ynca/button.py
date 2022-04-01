import ynca

from homeassistant.components.button import ButtonEntity

from .const import DOMAIN
from .debounce import debounce


async def async_setup_entry(hass, config_entry, async_add_entities):

    receiver = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    for zone in ynca.ZONE_SUBUNIT_IDS:
        if zone_subunit := getattr(receiver, zone):
            for scene_id in zone_subunit.scenes.keys():
                entities.append(
                    YamahaYncaSceneButton(config_entry.entry_id, zone_subunit, scene_id)
                )

    async_add_entities(entities)


class YamahaYncaSceneButton(ButtonEntity):
    """Representation of a scene button on a Yamaha Ynca device."""

    def __init__(self, receiver_unique_id, zone, scene_id):
        self._zone = zone
        self._scene_id = scene_id

        self._attr_icon = "mdi:palette"
        self._attr_unique_id = (
            f"{receiver_unique_id}_{self._zone.id}_scene_{self._scene_id}"
        )
        self._attr_device_info = {
            "identifiers": {(DOMAIN, receiver_unique_id)},
        }

    @debounce(0.200)
    def debounced_update(self):
        # Debounced update because lots of updates come in when switching sources
        # and I don't want to spam HA with all those updates
        # as it causes unneeded load and glitches in the UI.
        self.schedule_update_ha_state()

    async def async_added_to_hass(self):
        self._zone.register_update_callback(self.debounced_update)

    async def async_will_remove_from_hass(self):
        self._zone.unregister_update_callback(self.debounced_update)

    @property
    def name(self):
        """Return the name of the entity."""
        return f"{self._zone.name}: {self._zone.scenes[self._scene_id]}"

    def press(self) -> None:
        """Activate scene."""
        self._zone.activate_scene(self._scene_id)
