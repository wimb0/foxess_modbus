"""The client used to talk Modbus, backed by modbus-connection (tmodbus backend)."""

import logging
from typing import Any

from homeassistant.core import HomeAssistant
from modbus_connection import (
    ModbusError,
    ModbusSerialParams,
    ModbusTcpParams,
    ModbusUdpParams,
    ModbusUnit,
)
from modbus_connection import (
    ModbusConnectionError,
    ModbusTimeoutError,
)
from modbus_connection.tmodbus import ModbusConnection

from ..common.types import ConnectionType
from ..common.types import RegisterType
from ..const import RTU_OVER_TCP
from ..const import SERIAL
from ..const import TCP
from ..const import UDP
from ..inverter_adapters import InverterAdapter

_LOGGER = logging.getLogger(__name__)

_NUM_RETRIES = 3
# The previous client used a ~3s default; modbus-connection lets
# the device set the floor. 5s matches the proven nextenergy_battery setup
# against the same hardware.
_TIMEOUT = 5


def _build_params(protocol: str, config: dict[str, Any]) -> Any:
    """Map the integration's protocol + config dict to backend-neutral params."""
    if protocol == TCP:
        return ModbusTcpParams(host=config["host"], port=config["port"])
    if protocol == UDP:
        # Default framing is native Modbus (socket), as with the old client
        return ModbusUdpParams(host=config["host"], port=config["port"])
    if protocol == SERIAL:
        return ModbusSerialParams(
            device=config["port"],
            baudrate=config.get("baudrate", 9600),
            framer="rtu",
        )
    if protocol == RTU_OVER_TCP:
        # A serial server forwards the line byte-for-byte, so this is a serial
        # link on a socket transport with RTU framing
        return ModbusSerialParams(
            device=f"socket://{config['host']}:{config['port']}",
            baudrate=config.get("baudrate", 9600),
            framer="rtu",
        )
    raise AssertionError(f"Unknown protocol {protocol}")


class ModbusClient:
    """Modbus"""

    def __init__(self, hass: HomeAssistant, protocol: str, adapter: InverterAdapter, config: dict[str, Any]) -> None:
        """Init"""
        # hass is unused now that calls run natively async (previously everything
        # went through hass.async_add_executor_job). Kept so callers don't change.
        self._hass = hass
        self._config = config
        self._protocol = protocol
        self._connection = ModbusConnection(
            _build_params(protocol, config),
            timeout=_TIMEOUT,
            # Delaying for a second after establishing a connection seems to help the inverter stability,
            # see https://github.com/nathanmarlor/foxess_modbus/discussions/132
            connect_delay=1 if adapter.connection_type == ConnectionType.LAN else 0.0,
            # Some serial devices need a short delay after polling. Also do this for the inverter, just
            # in case it helps.
            message_spacing=(
                30 / 1000 if protocol == SERIAL or adapter.connection_type == ConnectionType.LAN else 0.0
            ),
        )

    def _unit(self, slave: int) -> ModbusUnit:
        """Unit handle for the given slave."""
        return self._connection.for_unit(slave)

    async def close(self) -> None:
        """Close connection"""
        _LOGGER.debug("Closing connection to modbus on %s", self)
        await self._connection.close()

    async def read_registers(
        self,
        start_address: int,
        num_registers: int,
        register_type: RegisterType,
        slave: int,
    ) -> list[int]:
        """Read registers"""
        if register_type == RegisterType.HOLDING:
            op = "holding"
        elif register_type == RegisterType.INPUT:
            op = "input"
        else:
            raise AssertionError()

        message = (
            f"Error reading registers. Type: {register_type}; start: {start_address}; count: {num_registers}; "
            f"slave: {slave}"
        )

        # The backend serializes requests per connection, so a response can no
        # longer be matched to the wrong request (the old client had to check
        # response types explicitly for this). Only transient link failures are
        # retried; exception responses (e.g. illegal address, which marks
        # invalid register ranges) fail fast.
        last_error: ModbusError | None = None
        for _ in range(_NUM_RETRIES):
            try:
                unit = self._unit(slave)
                if op == "holding":
                    return list(await unit.read_holding_registers(start_address, num_registers))
                return list(await unit.read_input_registers(start_address, num_registers))
            except (ModbusTimeoutError, ModbusConnectionError) as ex:
                last_error = ex
                _LOGGER.debug("Retrying %s after %s", message, ex)
            except ModbusError as ex:
                raise ModbusClientFailedError(message, self, ex) from ex

        assert last_error is not None
        raise ModbusClientFailedError(message, self, last_error) from last_error

    async def write_registers(self, register_address: int, register_values: list[int], slave: int) -> None:
        """Write registers"""
        message = f"Error writing registers. Start: {register_address}; values: {register_values}; slave: {slave}"

        last_error: ModbusError | None = None
        for _ in range(_NUM_RETRIES):
            try:
                unit = self._unit(slave)
                if len(register_values) > 1:
                    await unit.write_registers(register_address, [int(i) for i in register_values])
                else:
                    await unit.write_register(register_address, int(register_values[0]))
                return
            except (ModbusTimeoutError, ModbusConnectionError) as ex:
                last_error = ex
                _LOGGER.debug("Retrying %s after %s", message, ex)
            except ModbusError as ex:
                raise ModbusClientFailedError(message, self, ex) from ex

        assert last_error is not None
        raise ModbusClientFailedError(message, self, last_error) from last_error

    def __str__(self) -> str:
        if self._protocol == SERIAL:
            return f"{self._config['port']}"
        return f"{self._protocol}://{self._config['host']}:{self._config['port']}"


class ModbusClientFailedError(Exception):
    """Raised when the ModbusClient fails to read/write"""

    def __init__(self, message: str, client: ModbusClient, response: ModbusError | Exception) -> None:
        super().__init__(f"{message} from {client}: {response}")
        self.message = message
        self.client = client
        self.response = response

    def __str__(self) -> str:
        return f"{self.message} from {self.client}: {self.response}"
