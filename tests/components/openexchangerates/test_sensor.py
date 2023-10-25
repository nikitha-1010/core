# test cases
import pytest
from unittest.mock import Mock, patch
from homeassistant.components.openexchangerates.sensor import (
    async_setup_entry,
    OpenexchangeratesSensor,
    ConvertedAmountSensor,
    CONF_QUOTE,
    DOMAIN,
    API_KEY,
)


# Sample data for tests
SAMPLE_RATES = {"USD": 1, "EUR": 0.84, "GBP": 0.74}


@pytest.fixture
def mock_coordinator():
    """Return a mock OpenexchangeratesCoordinator."""
    coordinator = Mock()
    coordinator.data.rates = SAMPLE_RATES
    return coordinator


def test_openexchangerates_sensor_init_and_properties(mock_coordinator):
    """Test the initialization and property methods of the sensor."""
    config_entry = Mock()
    config_entry.entry_id = "test_entry_id"
    sensor = OpenexchangeratesSensor(config_entry, mock_coordinator, "EUR", True)

    assert sensor.native_value == 0.84


def test_converted_amount_sensor_conversion(mock_coordinator):
    """Test the currency conversion in ConvertedAmountSensor."""
    sensor = ConvertedAmountSensor(mock_coordinator)
    sensor.hass = Mock()

    # Mocking the required states
    with patch.object(
        sensor.hass.states,
        "get",
        side_effect=[
            Mock(state="100"),  # amount
            Mock(state="USD"),  # from_currency
            Mock(state="EUR"),  # to_currency
        ],
    ):
        converted = sensor.convert_currency(100, "USD", "EUR", SAMPLE_RATES)
        assert converted == 84.0


def test_converted_amount_sensor_invalid_conversion(mock_coordinator):
    """Test invalid conversion scenario in ConvertedAmountSensor."""
    sensor = ConvertedAmountSensor(mock_coordinator)

    with pytest.raises(ValueError, match="Invalid conversion: USD to INVALID_CURRENCY"):
        sensor.convert_currency(100, "USD", "INVALID_CURRENCY", SAMPLE_RATES)


@pytest.mark.asyncio
async def test_async_setup_entry(mock_coordinator):
    """Test async_setup_entry function."""
    hass = Mock()
    config_entry = Mock()
    config_entry.data = {CONF_QUOTE: "EUR"}
    hass.data = {DOMAIN: {config_entry.entry_id: mock_coordinator}}
    async_add_entities = Mock()

    await async_setup_entry(hass, config_entry, async_add_entities)

    # Validate the async_add_entities has been called
    async_add_entities.assert_called()
