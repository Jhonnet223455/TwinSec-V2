"""
Plugin Manager - Gestor de plugins de sistemas OT/ICS

Carga dinámicamente plugins de sistemas específicos (tank, HVAC, motor, etc.)
"""

import logging
from typing import Dict, Any, Optional
from pathlib import Path
import importlib.util
import inspect

logger = logging.getLogger(__name__)


class PluginBase:
    """
    Clase base para todos los plugins de sistemas.
    
    Todos los plugins deben heredar de esta clase e implementar:
    - get_initial_state()
    - compute_derivatives()
    - compute_signals()
    """
    
    def get_initial_state(self, model: Dict[str, Any]) -> Dict[str, float]:
        """
        Obtiene el estado inicial del sistema.
        
        Args:
            model: Definición del modelo JSON
            
        Returns:
            Dict con variables de estado y valores iniciales
        """
        raise NotImplementedError("Subclass must implement get_initial_state()")
    
    def compute_derivatives(
        self,
        t: float,
        state: Dict[str, float],
        control: Dict[str, float],
        model: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Calcula las derivadas del sistema (dx/dt).
        
        Args:
            t: Tiempo actual
            state: Estado actual del sistema
            control: Acciones de control
            model: Definición del modelo
            
        Returns:
            Dict con derivadas de cada variable de estado
        """
        raise NotImplementedError("Subclass must implement compute_derivatives()")
    
    def compute_signals(self, state: Dict[str, float]) -> Dict[str, float]:
        """
        Calcula señales observables del sistema.
        
        Args:
            state: Estado actual
            
        Returns:
            Dict con señales medibles (sensores)
        """
        raise NotImplementedError("Subclass must implement compute_signals()")


class PluginManager:
    """
    Gestor de plugins de sistemas.
    
    Carga y registra plugins de sistemas OT/ICS dinámicamente.
    """
    
    def __init__(self):
        self.plugins: Dict[str, PluginBase] = {}
        self._auto_discover_plugins()
    
    def _auto_discover_plugins(self):
        """
        Descubre automáticamente plugins en la carpeta engine/plugins/
        """
        plugins_dir = Path(__file__).parent.parent / "plugins"
        
        if not plugins_dir.exists():
            logger.warning(f"Directorio de plugins no encontrado: {plugins_dir}")
            return
        
        logger.info(f"Buscando plugins en: {plugins_dir}")
        
        for plugin_file in plugins_dir.glob("*_plugin.py"):
            plugin_name = plugin_file.stem.replace("_plugin", "")
            
            try:
                # Cargar módulo dinámicamente
                spec = importlib.util.spec_from_file_location(
                    f"engine.plugins.{plugin_file.stem}",
                    plugin_file
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Buscar clases que hereden de PluginBase
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, PluginBase) and obj != PluginBase:
                        plugin_instance = obj()
                        self.plugins[plugin_name] = plugin_instance
                        logger.info(f"  ✓ Plugin registrado: {plugin_name} ({name})")
                        break
            
            except Exception as e:
                logger.error(f"  ✗ Error cargando plugin {plugin_name}: {str(e)}")
    
    def register_plugin(self, name: str, plugin: PluginBase):
        """
        Registra un plugin manualmente.
        
        Args:
            name: Nombre del plugin (ej: "tank", "hvac")
            plugin: Instancia del plugin
        """
        if not isinstance(plugin, PluginBase):
            raise TypeError(f"Plugin debe heredar de PluginBase")
        
        self.plugins[name] = plugin
        logger.info(f"Plugin registrado manualmente: {name}")
    
    def get_plugin(self, name: str) -> Optional[PluginBase]:
        """
        Obtiene un plugin por nombre.
        
        Args:
            name: Nombre del plugin
            
        Returns:
            Instancia del plugin o None si no existe
        """
        plugin = self.plugins.get(name)
        
        if not plugin:
            logger.error(f"Plugin no encontrado: {name}")
            logger.info(f"Plugins disponibles: {list(self.plugins.keys())}")
        
        return plugin
    
    def list_plugins(self) -> list[str]:
        """Lista todos los plugins registrados."""
        return list(self.plugins.keys())


# Singleton global
_plugin_manager = None


def get_plugin_manager() -> PluginManager:
    """Obtiene la instancia singleton del PluginManager."""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager
