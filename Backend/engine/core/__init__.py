"""
Engine Core Package - Componentes principales del motor de simulación

Exports:
    - Simulator: Motor de simulación principal
    - PluginManager: Gestor de plugins de sistemas
    - PluginBase: Clase base para plugins
"""

from .simulator import Simulator, SimulationState
from .plugin_manager import PluginManager, PluginBase, get_plugin_manager

__all__ = [
    "Simulator",
    "SimulationState",
    "PluginManager",
    "PluginBase",
    "get_plugin_manager"
]
