"""Derived scientific parameters computation and registry service.

Provides an extensible registry for calculating derived oceanographic variables
such as kinetic energy, temperature conversions, and anomalies.
"""

from typing import Callable
import numpy as np
import xarray as xr


class DerivedAnalyzer:
    """Registry and executor for oceanographic derived parameters."""

    _registry: dict[str, Callable[[xr.Dataset], tuple[np.ndarray, str, str]]] = {}

    @classmethod
    def register(cls, name: str, func: Callable[[xr.Dataset], tuple[np.ndarray, str, str]]) -> None:
        """Register a new derived parameter transformation function."""
        cls._registry[name.upper()] = func

    @classmethod
    def compute(cls, operation: str, ds: xr.Dataset) -> tuple[np.ndarray, str, str]:
        """Compute a registered derived parameter.

        Returns:
            Tuple of (numpy.ndarray result, physical units string, standard name string).
        """
        op_key = operation.upper()
        if op_key not in cls._registry:
            raise ValueError(
                f"Derived operation '{operation}' not registered. Available: {list(cls._registry.keys())}"
            )
        return cls._registry[op_key](ds)

    @classmethod
    def available_operations(cls) -> list[str]:
        """List registered derived operations."""
        return list(cls._registry.keys())


# Built-in derived operations


def _compute_kinetic_energy(ds: xr.Dataset) -> tuple[np.ndarray, str, str]:
    """Compute specific kinetic energy: 0.5 * (u^2 + v^2)."""
    var_names_lower = {name.lower(): name for name in ds.data_vars.keys()}
    u_name = var_names_lower.get("u") or var_names_lower.get("uo") or var_names_lower.get("water_u")
    v_name = var_names_lower.get("v") or var_names_lower.get("vo") or var_names_lower.get("water_v")

    if not u_name or not v_name:
        raise ValueError("Kinetic energy requires 'u' and 'v' velocity components.")

    u = np.asarray(ds[u_name].values, dtype=np.float64)
    v = np.asarray(ds[v_name].values, dtype=np.float64)
    ke = 0.5 * (u**2 + v**2)
    return ke, "m2 s-2", "specific_kinetic_energy_of_sea_water"


def _compute_celsius_from_kelvin(ds: xr.Dataset) -> tuple[np.ndarray, str, str]:
    """Convert sea surface temperature from Kelvin to Celsius: T - 273.15."""
    t_name = None
    for name in ds.data_vars:
        da = ds[name]
        units = str(da.attrs.get("units", "")).lower()
        if units in ["k", "kelvin"]:
            t_name = name
            break

    if not t_name:
        var_names_lower = {name.lower(): name for name in ds.data_vars.keys()}
        t_name = (
            var_names_lower.get("temperature")
            or var_names_lower.get("temp_k")
            or var_names_lower.get("sst")
            or var_names_lower.get("sea_surface_temperature")
            or var_names_lower.get("thetao")
        )

    if not t_name or t_name not in ds:
        raise ValueError("Temperature variable (in Kelvin or sst/temperature/thetao) not found.")

    t_kelvin = np.asarray(ds[t_name].values, dtype=np.float64)
    celsius = t_kelvin - 273.15
    return celsius, "degC", "sea_surface_temperature"


DerivedAnalyzer.register("KINETIC_ENERGY", _compute_kinetic_energy)
DerivedAnalyzer.register("CELSIUS_FROM_KELVIN", _compute_celsius_from_kelvin)
