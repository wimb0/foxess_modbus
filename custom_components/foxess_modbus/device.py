"""Component device model for FoxESS inverters, built on modbus-connection.

Backend-neutral: everything here talks to a ``ModbusUnit`` and works over
any modbus-connection backend. It has no Home Assistant dependency.

Layout follows the V1.05.04 register definition. Components mirror the
spec tables: identity, firmware versions, two BMS packs (each supporting up
to 32 slave modules; fields are modelled for the first five, matching the
largest stack seen in the field), two meters, ratings, status/alarms, PV,
grid/inverter power, EPS, load, batteries, inverter power detail, system
SoC, energy totals, and settings.

Field scales follow the spec gains: voltage/current/power gains divide the
raw value (e.g. gain 1000 on a kW register is a 0.001 scale here).
"""

from __future__ import annotations

from typing import Any

from modbus_connection import ModbusUnit
from modbus_connection.model import (
    Component,
    RegisterField,
    gauge,
    int32,
    integer,
    string,
    uint32,
)


class VersionField(RegisterField[str]):
    """A packed BCD firmware version word: 0xABC -> "A.B.C" (one nibble each)."""

    def decode(
        self, words: list[int], scale_exponent: int | None = None
    ) -> str | None:
        """Decode the packed BCD version word."""
        value = words[0]
        return f"{(value >> 8) & 0xF}.{(value >> 4) & 0xF}.{value & 0xF}"

    def encode(self, value: Any, scale_exponent: int | None = None) -> list[int]:
        """Versions are read-only; encoding is unsupported."""
        raise ValueError("Version registers are read-only")


class Identity(Component):
    """Static device identity: model, serial, and part number."""

    register_ranges = ((30000, 30031),)

    model_name = string(30000, 16)
    serial_number = string(30016, 16)


class FirmwareVersions(Component):
    """Master/slave/manager firmware versions."""

    register_ranges = ((36001, 36003),)

    master_version = VersionField(36001)
    slave_version = VersionField(36002)
    manager_version = VersionField(36003)


class BmsPackStatic(Component):
    """Static identity of one BMS pack and its slave modules (up to five)."""

    register_ranges = (
        (37003, 37020),
        (37032, 37037),
        (37097, 37176),
        (37635, 37636),
    )

    bms_master_version = VersionField(37003)
    bms_master_type = integer(37004, signed=False)
    bms_master_sn = string(37005, 16)
    bms_slave_number = integer(37032, signed=False)
    bms_slave_1_version = VersionField(37033)
    bms_slave_2_version = VersionField(37034)
    bms_slave_3_version = VersionField(37035)
    bms_slave_4_version = VersionField(37036)
    bms_slave_5_version = VersionField(37037)
    bms_slave_1_sn = string(37097, 16)
    bms_slave_2_sn = string(37113, 16)
    bms_slave_3_sn = string(37129, 16)
    bms_slave_4_sn = string(37145, 16)
    bms_slave_5_sn = string(37161, 16)
    bms_design_energy = gauge(37635, 0.01, signed=False)
    battery_flag = integer(37636, signed=False)


class BmsPack2Static(Component):
    """Static identity of the second BMS pack and its slave modules."""

    register_ranges = (
        (37701, 37718),
        (37730, 37735),
        (37795, 37874),
        (38333, 38334),
    )

    bms_master_version = VersionField(37701)
    bms_master_type = integer(37702, signed=False)
    bms_master_sn = string(37703, 16)
    bms_slave_number = integer(37730, signed=False)
    bms_slave_1_version = VersionField(37731)
    bms_slave_2_version = VersionField(37732)
    bms_slave_3_version = VersionField(37733)
    bms_slave_4_version = VersionField(37734)
    bms_slave_5_version = VersionField(37735)
    bms_slave_1_sn = string(37795, 16)
    bms_slave_2_sn = string(37811, 16)
    bms_slave_3_sn = string(37827, 16)
    bms_slave_4_sn = string(37843, 16)
    bms_slave_5_sn = string(37859, 16)
    bms_design_energy = gauge(38333, 0.01, signed=False)
    battery_flag = integer(38334, signed=False)


class BmsPackLive(Component):
    """Live readings of the first BMS pack."""

    register_ranges = ((37002, 37002), (37609, 37633))

    bms_connection_status = integer(37002, signed=False)
    bms_voltage = gauge(37609, 0.1, signed=False)
    bms_current = gauge(37610, 0.1)
    bms_ambient_temp = gauge(37611, 0.1)
    bms_soc = integer(37612, signed=False)
    bms_max_temp = gauge(37617, 0.1)
    bms_min_temp = gauge(37618, 0.1)
    bms_max_cell_voltage = integer(37619, signed=False)
    bms_min_cell_voltage = integer(37620, signed=False)
    bms_soh = integer(37624, signed=False)
    bms_fault_1 = integer(37626, signed=False)
    bms_fault_2 = integer(37627, signed=False)
    bms_fault_3 = integer(37628, signed=False)
    bms_fault_4 = integer(37629, signed=False)
    bms_fault_5 = integer(37630, signed=False)
    bms_fault_6 = integer(37631, signed=False)
    bms_remain_energy = gauge(37632, 0.01, signed=False)
    bms_fcc_capacity = gauge(37633, 0.1, signed=False)


class BmsPack2Live(Component):
    """Live readings of the second BMS pack."""

    register_ranges = ((37700, 37700), (38307, 38331))

    bms_connection_status = integer(37700, signed=False)
    bms_voltage = gauge(38307, 0.1, signed=False)
    bms_current = gauge(38308, 0.1)
    bms_ambient_temp = gauge(38309, 0.1)
    bms_soc = integer(38310, signed=False)
    bms_max_temp = gauge(38315, 0.1)
    bms_min_temp = gauge(38316, 0.1)
    bms_max_cell_voltage = integer(38317, signed=False)
    bms_min_cell_voltage = integer(38318, signed=False)
    bms_soh = integer(38322, signed=False)
    bms_fault_1 = integer(38324, signed=False)
    bms_fault_2 = integer(38325, signed=False)
    bms_fault_3 = integer(38326, signed=False)
    bms_fault_4 = integer(38327, signed=False)
    bms_fault_5 = integer(38328, signed=False)
    bms_fault_6 = integer(38329, signed=False)
    bms_remain_energy = gauge(38330, 0.01, signed=False)
    bms_fcc_capacity = gauge(38331, 0.1, signed=False)


class Meter(Component):
    """External meter (CT1) readings."""

    register_ranges = ((38801, 38815), (38816, 38821), (38822, 38829), (38830, 38846))

    meter_connection_status = integer(38801, signed=False)
    r_phase_voltage = int32(38802, scale=0.1)
    s_phase_voltage = int32(38804, scale=0.1)
    t_phase_voltage = int32(38806, scale=0.1)
    r_phase_current = int32(38808, scale=0.001)
    s_phase_current = int32(38810, scale=0.001)
    t_phase_current = int32(38812, scale=0.001)
    combined_active_power = int32(38814, scale=0.1)
    r_phase_active_power = int32(38816, scale=0.1)
    s_phase_active_power = int32(38818, scale=0.1)
    t_phase_active_power = int32(38820, scale=0.1)
    combined_reactive_power = int32(38822, scale=0.1)
    r_phase_reactive_power = int32(38824, scale=0.1)
    s_phase_reactive_power = int32(38826, scale=0.1)
    t_phase_reactive_power = int32(38828, scale=0.1)
    combined_apparent_power = int32(38830, scale=0.1)
    r_phase_apparent_power = int32(38832, scale=0.1)
    s_phase_apparent_power = int32(38834, scale=0.1)
    t_phase_apparent_power = int32(38836, scale=0.1)
    combined_power_factor = int32(38838, scale=0.001)
    r_phase_power_factor = int32(38840, scale=0.001)
    s_phase_power_factor = int32(38842, scale=0.001)
    t_phase_power_factor = int32(38844, scale=0.001)
    frequency = int32(38846, scale=0.01)


class Meter2(Component):
    """Second external meter (CT2) readings."""

    register_ranges = ((38901, 38915), (38916, 38921), (38922, 38929), (38930, 38946))

    meter_connection_status = integer(38901, signed=False)
    r_phase_voltage = int32(38902, scale=0.1)
    s_phase_voltage = int32(38904, scale=0.1)
    t_phase_voltage = int32(38906, scale=0.1)
    r_phase_current = int32(38908, scale=0.001)
    s_phase_current = int32(38910, scale=0.001)
    t_phase_current = int32(38912, scale=0.001)
    combined_active_power = int32(38914, scale=0.1)
    r_phase_active_power = int32(38916, scale=0.1)
    s_phase_active_power = int32(38918, scale=0.1)
    t_phase_active_power = int32(38920, scale=0.1)
    combined_reactive_power = int32(38922, scale=0.1)
    r_phase_reactive_power = int32(38924, scale=0.1)
    s_phase_reactive_power = int32(38926, scale=0.1)
    t_phase_reactive_power = int32(38928, scale=0.1)
    combined_apparent_power = int32(38930, scale=0.1)
    r_phase_apparent_power = int32(38932, scale=0.1)
    s_phase_apparent_power = int32(38934, scale=0.1)
    t_phase_apparent_power = int32(38936, scale=0.1)
    combined_power_factor = int32(38938, scale=0.001)
    r_phase_power_factor = int32(38940, scale=0.001)
    s_phase_power_factor = int32(38942, scale=0.001)
    t_phase_power_factor = int32(38944, scale=0.001)
    frequency = int32(38946, scale=0.01)


class Ratings(Component):
    """Static inverter ratings and string/MPPT counts."""

    register_ranges = ((39051, 39062),)

    number_of_strings = integer(39051, signed=False)
    number_of_mppts = integer(39052, signed=False)
    rated_power = int32(39053, scale=0.001)
    max_active_power = int32(39055, scale=0.001)
    max_apparent_power = int32(39057, scale=0.001)
    max_reactive_power_fed = int32(39059, scale=0.001)
    max_reactive_power_absorbed = int32(39061, scale=0.001)


class InverterState(Component):
    """Live inverter status and alarm bitfields."""

    register_ranges = ((39063, 39069),)

    status_1 = integer(39063, signed=False)
    status_3 = uint32(39065)
    alarm_1 = integer(39067, signed=False)
    alarm_2 = integer(39068, signed=False)
    alarm_3 = integer(39069, signed=False)


class PvStrings(Component):
    """PV string voltages/currents (first four) and total input power."""

    register_ranges = ((39070, 39077), (39118, 39118))

    pv1_voltage = gauge(39070, 0.1)
    pv1_current = gauge(39071, 0.01)
    pv2_voltage = gauge(39072, 0.1)
    pv2_current = gauge(39073, 0.01)
    pv3_voltage = gauge(39074, 0.1)
    pv3_current = gauge(39075, 0.01)
    pv4_voltage = gauge(39076, 0.1)
    pv4_current = gauge(39077, 0.01)
    total_pv_power = int32(39118, scale=0.001)


class PvPower(Component):
    """Per-string PV power (first four strings)."""

    register_ranges = ((39279, 39285),)

    pv1_power = int32(39279, scale=0.001)
    pv2_power = int32(39281, scale=0.001)
    pv3_power = int32(39283, scale=0.001)
    pv4_power = int32(39285, scale=0.001)


class GridInverter(Component):
    """Grid voltages, inverter currents, and total active/reactive power."""

    register_ranges = ((39123, 39125), (39126, 39141))

    grid_r_voltage = gauge(39123, 0.1)
    grid_s_voltage = gauge(39124, 0.1)
    grid_t_voltage = gauge(39125, 0.1)
    inv_r_current = int32(39126, scale=0.001)
    inv_s_current = int32(39128, scale=0.001)
    inv_t_current = int32(39130, scale=0.001)
    active_power = int32(39134, scale=0.001)
    reactive_power = int32(39136, scale=0.001)
    power_factor = gauge(39138, 0.001)
    grid_frequency = gauge(39139, 0.01)
    inverter_temp = gauge(39141, 0.1)


class StorageMeterPower(Component):
    """Storage-module and meter-collected active power."""

    register_ranges = ((39162, 39162), (39168, 39168))

    storage_power = int32(39162)
    meter_power = int32(39168)


class EpsOutput(Component):
    """EPS voltages, currents, powers, and frequency."""

    register_ranges = ((39201, 39218),)

    eps_r_voltage = gauge(39201, 0.1, signed=False)
    eps_s_voltage = gauge(39202, 0.1, signed=False)
    eps_t_voltage = gauge(39203, 0.1, signed=False)
    eps_r_current = int32(39204, scale=0.001)
    eps_s_current = int32(39206, scale=0.001)
    eps_t_current = int32(39208, scale=0.001)
    eps_r_power = int32(39210)
    eps_s_power = int32(39212)
    eps_t_power = int32(39214)
    eps_combined_power = int32(39216)
    eps_frequency = gauge(39218, 0.01)


class LoadBatteries(Component):
    """Load powers and per-battery voltage/current/power."""

    register_ranges = ((39219, 39238),)

    load_r_power = int32(39219)
    load_s_power = int32(39221)
    load_t_power = int32(39223)
    load_combined_power = int32(39225)
    battery_1_voltage = gauge(39227, 0.1, signed=False)
    battery_1_current = int32(39228, scale=0.001)
    battery_1_power = int32(39230)
    battery_2_voltage = gauge(39232, 0.1, signed=False)
    battery_2_current = int32(39233, scale=0.001)
    battery_2_power = int32(39235)
    battery_combined_power = int32(39237)


class InverterPowerDetail(Component):
    """Per-phase inverter active/reactive/apparent power and limits."""

    register_ranges = ((39248, 39262), (39264, 39277))

    inv_r_active_power = int32(39248)
    inv_s_active_power = int32(39250)
    inv_t_active_power = int32(39252)
    inv_r_reactive_power = int32(39256)
    inv_s_reactive_power = int32(39258)
    inv_t_reactive_power = int32(39260)
    inv_r_apparent_power = int32(39264)
    inv_s_apparent_power = int32(39266)
    inv_t_apparent_power = int32(39268)
    inv_combined_apparent_power = int32(39270)
    inv_r_frequency = gauge(39272, 0.01)
    inv_s_frequency = gauge(39273, 0.01)
    inv_t_frequency = gauge(39274, 0.01)
    available_import_power = int32(39275)
    available_export_power = int32(39277)


class SystemSoc(Component):
    """System state of charge."""

    register_ranges = ((39423, 39423),)

    system_soc = integer(39423, signed=False)


class Energy(Component):
    """Cumulative energy counters, including BMS charge/discharge totals."""

    register_ranges = ((39601, 39604), (39605, 39623), (39625, 39639))

    pv_total = uint32(39601, scale=0.01)
    pv_today = uint32(39603, scale=0.01)
    battery_charge_total = uint32(39605, scale=0.01)
    battery_charge_today = uint32(39607, scale=0.01)
    battery_discharge_total = uint32(39609, scale=0.01)
    battery_discharge_today = uint32(39611, scale=0.01)
    grid_export_total = uint32(39613, scale=0.01)
    grid_export_today = uint32(39615, scale=0.01)
    grid_import_total = uint32(39617, scale=0.01)
    grid_import_today = uint32(39619, scale=0.01)
    output_energy_total = uint32(39621, scale=0.01)
    output_energy_today = uint32(39623, scale=0.01)
    input_energy_total = uint32(39625, scale=0.01)
    input_energy_today = uint32(39627, scale=0.01)
    load_energy_total = uint32(39629, scale=0.01)
    load_energy_today = uint32(39631, scale=0.01)
    bms_charge_total = uint32(39633, scale=0.01)
    bms_charge_today = uint32(39635, scale=0.01)
    bms_discharge_total = uint32(39637, scale=0.01)
    bms_discharge_today = uint32(39639, scale=0.01)


class Settings(Component):
    """Configuration registers: currents, SoC limits, work mode, and state."""

    register_ranges = (
        (46607, 46611),
        (49203, 49203),
        (49228, 49228),
        (49240, 49240),
    )

    max_charge_current = gauge(46607, 0.1)
    max_discharge_current = gauge(46608, 0.1)
    min_soc = integer(46609, signed=False)
    max_soc = integer(46610, signed=False)
    min_soc_ongrid = integer(46611, signed=False)
    work_mode = integer(49203, signed=False)
    system_power_state = integer(49228, signed=False)
    network_status = integer(49240, signed=False)


class FoxessDevice:
    """A FoxESS inverter or battery system on a Modbus unit.

    Components are independent failure domains: each block polls on its own,
    so one unreadable block costs only its own values. Static identity is
    read once; everything else polls.
    """

    def __init__(self, unit: ModbusUnit) -> None:
        """Initialize the device's components on ``unit``."""
        self._unit = unit
        self.identity = Identity(unit)
        self.versions = FirmwareVersions(unit)
        self.bms_static = BmsPackStatic(unit)
        self.bms_pack2_static = BmsPack2Static(unit)
        self.bms_live = BmsPackLive(unit)
        self.bms_pack2_live = BmsPack2Live(unit)
        self.meter = Meter(unit)
        self.meter2 = Meter2(unit)
        self.ratings = Ratings(unit)
        self.state = InverterState(unit)
        self.pv = PvStrings(unit)
        self.pv_power = PvPower(unit)
        self.grid = GridInverter(unit)
        self.storage_power = StorageMeterPower(unit)
        self.eps = EpsOutput(unit)
        self.load_batteries = LoadBatteries(unit)
        self.power_detail = InverterPowerDetail(unit)
        self.system_soc = SystemSoc(unit)
        self.energy = Energy(unit)
        self.settings = Settings(unit)

    @property
    def components(self) -> dict[str, Component]:
        """Every component of this device, by name."""
        return {
            "identity": self.identity,
            "versions": self.versions,
            "bms_static": self.bms_static,
            "bms_pack2_static": self.bms_pack2_static,
            "bms_live": self.bms_live,
            "bms_pack2_live": self.bms_pack2_live,
            "meter": self.meter,
            "meter2": self.meter2,
            "ratings": self.ratings,
            "state": self.state,
            "pv": self.pv,
            "pv_power": self.pv_power,
            "grid": self.grid,
            "storage_power": self.storage_power,
            "eps": self.eps,
            "load_batteries": self.load_batteries,
            "power_detail": self.power_detail,
            "system_soc": self.system_soc,
            "energy": self.energy,
            "settings": self.settings,
        }

    @classmethod
    async def async_probe(cls, unit: ModbusUnit) -> str:
        """Read the device model name, proving it is reachable."""
        info = Identity(unit)
        await info.async_update()
        return info.model_name or ""
