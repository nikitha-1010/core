# sensor.py

"""Support for openexchangerates.org exchange rates service."""
from __future__ import annotations

import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_QUOTE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import OpenexchangeratesCoordinator

ATTRIBUTION = "Data provided by openexchangerates.org"
_LOGGER = logging.getLogger(__name__)
SENSOR_ID = "converted_amount"
SENSOR_NAME = "Converted Amount"

API_ENDPOINT = "https://openexchangerates.org/api/latest.json"
API_KEY = "c9879b5708c94d55a82be58a091bd970"  # Replace with your own API key


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Open Exchange Rates sensor."""
    quote: str = config_entry.data.get(CONF_QUOTE, "EUR")
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    async_add_entities(
        [
            OpenexchangeratesSensor(
                config_entry, coordinator, rate_quote, rate_quote == quote
            )
            for rate_quote in coordinator.data.rates
        ]
    )

    sensor = ConvertedAmountSensor(coordinator)
    async_add_entities([sensor])

    async def state_changed_listener(event):
        new_state = event.data.get("new_state")
        if new_state is None:
            return

        if event.data["entity_id"] in [
            "input_number.amount",
            "input_select.from_currency",
            "input_select.to_currency",
        ]:
            sensor.async_schedule_update_ha_state(True)

    async_track_state_change_event(
        hass,
        [
            "input_number.amount",
            "input_select.from_currency",
            "input_select.to_currency",
        ],
        state_changed_listener,
    )


class OpenexchangeratesSensor(
    CoordinatorEntity[OpenexchangeratesCoordinator], SensorEntity
):
    """Representation of an Open Exchange Rates sensor."""

    _attr_has_entity_name = True
    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        config_entry: ConfigEntry,
        coordinator: OpenexchangeratesCoordinator,
        quote: str,
        enabled: bool,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, config_entry.entry_id)},
            manufacturer="Open Exchange Rates",
            name=f"Open Exchange Rates {coordinator.base}",
        )
        self._attr_entity_registry_enabled_default = enabled
        self._attr_name = f"Conversion {coordinator.base} to {quote}"
        self._attr_native_unit_of_measurement = quote
        self._attr_unique_id = f"{config_entry.entry_id}_{quote}"
        self._quote = quote

    @property
    def native_value(self) -> float:
        """Return the state of the sensor."""
        return round(self.coordinator.data.rates[self._quote], 4)


class ConvertedAmountSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator) -> None:
        super().__init__(coordinator)
        self._state = None

    @property
    def name(self) -> None:
        return SENSOR_NAME

    @property
    def unique_id(self) -> None:
        return SENSOR_ID

    @property
    def state(self) -> None:
        return self._state

    async def async_update(self) -> None:
        amount = float(self.hass.states.get("input_number.amount").state)
        from_currency = self.hass.states.get("input_select.from_currency").state
        to_currency = self.hass.states.get("input_select.to_currency").state

        # Perform the conversion using your existing logic
        try:
            self._state = self.convert_currency(
                amount, from_currency, to_currency, self.coordinator.data.rates
            )
        except ValueError as e:
            _LOGGER.error("Error converting currency: %s", e)
            self._state = None

    def convert_currency(self, amount, from_currency, to_currency, rates):
        """Convert currency value."""
        try:
            from_rate = rates[from_currency]
            to_rate = rates[to_currency]
        except KeyError:
            raise ValueError(f"Invalid conversion: {from_currency} to {to_currency}")

        usd_amount = amount / from_rate
        converted_amount = usd_amount * to_rate
        return converted_amount
