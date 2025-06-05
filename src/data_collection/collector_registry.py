"""
Collector registry module for CityPulse data collection framework.

This module provides a centralized registry for data collectors, allowing
for dynamic discovery and instantiation of collectors.
"""

import importlib
import inspect
from typing import Dict, Any, Type, Optional, List, Callable
from pathlib import Path

from src.data_collection.base_collector import BaseCollector
from src.utils.logging import get_module_logger

logger = get_module_logger(__name__)


class CollectorRegistry:
    """
    Registry for data collectors in the CityPulse system.
    
    This class provides a centralized way to register, discover, and
    instantiate data collectors.
    
    Attributes:
        collectors (Dict[str, Type[BaseCollector]]): Registered collector classes
        factories (Dict[str, Callable]): Factory functions for creating collector instances
        metadata (Dict[str, Dict[str, Any]]): Metadata for registered collectors
    """
    
    def __init__(self):
        """Initialize the collector registry."""
        self.collectors: Dict[str, Type[BaseCollector]] = {}
        self.factories: Dict[str, Callable] = {}
        self.metadata: Dict[str, Dict[str, Any]] = {}
        
        logger.info("Initialized collector registry")
    
    def register_collector(
        self, 
        collector_class: Type[BaseCollector], 
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Register a collector class.
        
        Args:
            collector_class: The collector class to register
            name: Optional name to register the collector under (defaults to class name)
            metadata: Optional metadata for the collector
        """
        if not issubclass(collector_class, BaseCollector):
            raise TypeError(f"Collector class must inherit from BaseCollector: {collector_class}")
        
        collector_name = name or collector_class.__name__
        
        if collector_name in self.collectors:
            logger.warning(f"Overwriting existing collector: {collector_name}")
        
        self.collectors[collector_name] = collector_class
        self.metadata[collector_name] = metadata or {}
        
        # Add class attributes to metadata
        if hasattr(collector_class, '__doc__') and collector_class.__doc__:
            self.metadata[collector_name]['description'] = collector_class.__doc__.strip()
        
        logger.info(f"Registered collector: {collector_name}")
    
    def register_factory(
        self, 
        factory_func: Callable, 
        name: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Register a factory function for creating collector instances.
        
        Args:
            factory_func: Factory function that returns a BaseCollector instance
            name: Optional name to register the factory under (defaults to function name)
            metadata: Optional metadata for the factory
        """
        factory_name = name or factory_func.__name__
        
        if factory_name in self.factories:
            logger.warning(f"Overwriting existing factory: {factory_name}")
        
        self.factories[factory_name] = factory_func
        self.metadata[factory_name] = metadata or {}
        
        # Add function docstring to metadata
        if factory_func.__doc__:
            self.metadata[factory_name]['description'] = factory_func.__doc__.strip()
        
        logger.info(f"Registered collector factory: {factory_name}")
    
    def get_collector_class(self, name: str) -> Type[BaseCollector]:
        """
        Get a registered collector class by name.
        
        Args:
            name: Name of the collector class
            
        Returns:
            The collector class
            
        Raises:
            KeyError: If the collector is not registered
        """
        if name not in self.collectors:
            raise KeyError(f"Collector not registered: {name}")
        
        return self.collectors[name]
    
    def get_factory(self, name: str) -> Callable:
        """
        Get a registered factory function by name.
        
        Args:
            name: Name of the factory function
            
        Returns:
            The factory function
            
        Raises:
            KeyError: If the factory is not registered
        """
        if name not in self.factories:
            raise KeyError(f"Factory not registered: {name}")
        
        return self.factories[name]
    
    def create_collector(self, name: str, **kwargs) -> BaseCollector:
        """
        Create a collector instance by name.
        
        This method will first try to use a registered factory function.
        If no factory is found, it will try to instantiate the collector class directly.
        
        Args:
            name: Name of the collector or factory
            **kwargs: Arguments to pass to the factory or constructor
            
        Returns:
            A collector instance
            
        Raises:
            KeyError: If the collector or factory is not registered
        """
        # Try factory first
        if name in self.factories:
            logger.info(f"Creating collector using factory: {name}")
            return self.factories[name](**kwargs)
        
        # Then try collector class
        if name in self.collectors:
            logger.info(f"Creating collector using class: {name}")
            return self.collectors[name](**kwargs)
        
        raise KeyError(f"No collector or factory registered with name: {name}")
    
    def list_collectors(self) -> List[Dict[str, Any]]:
        """
        List all registered collectors with their metadata.
        
        Returns:
            List of dictionaries containing collector information
        """
        result = []
        
        # Add collectors
        for name, collector_class in self.collectors.items():
            info = {
                'name': name,
                'type': 'class',
                'module': collector_class.__module__,
                'class': collector_class.__name__
            }
            
            # Add metadata
            if name in self.metadata:
                info.update(self.metadata[name])
            
            result.append(info)
        
        # Add factories
        for name, factory_func in self.factories.items():
            # Skip if already added as a collector
            if name in self.collectors:
                continue
                
            info = {
                'name': name,
                'type': 'factory',
                'module': factory_func.__module__,
                'function': factory_func.__name__
            }
            
            # Add metadata
            if name in self.metadata:
                info.update(self.metadata[name])
            
            result.append(info)
        
        return result
    
    def discover_collectors(self, package: str = 'src.data_collection') -> int:
        """
        Discover and register collectors from a package.
        
        This method will search the package for classes that inherit from BaseCollector
        and factory functions that return BaseCollector instances.
        
        Args:
            package: Package to search for collectors
            
        Returns:
            Number of collectors discovered
        """
        logger.info(f"Discovering collectors in package: {package}")
        
        try:
            package_obj = importlib.import_module(package)
        except ImportError as e:
            logger.error(f"Error importing package {package}: {str(e)}")
            return 0
        
        # Get the package directory
        if hasattr(package_obj, '__path__'):
            package_dir = Path(package_obj.__path__[0])
        else:
            logger.error(f"Package {package} has no __path__ attribute")
            return 0
        
        count = 0
        
        # Iterate over Python files in the package
        for py_file in package_dir.glob('**/*.py'):
            if py_file.name.startswith('__'):
                continue
                
            # Construct the module name
            rel_path = py_file.relative_to(package_dir)
            module_name = f"{package}.{rel_path.with_suffix('').as_posix().replace('/', '.')}"
            
            try:
                module = importlib.import_module(module_name)
                
                # Find collector classes
                for name, obj in inspect.getmembers(module):
                    # Skip if not a class or function
                    if not (inspect.isclass(obj) or inspect.isfunction(obj)):
                        continue
                    
                    # Register collector classes
                    if inspect.isclass(obj) and issubclass(obj, BaseCollector) and obj != BaseCollector:
                        self.register_collector(obj)
                        count += 1
                    
                    # Register factory functions
                    elif inspect.isfunction(obj) and name.startswith('get_') and name.endswith('_collector'):
                        # Check if the function returns a BaseCollector
                        try:
                            return_type = inspect.signature(obj).return_annotation
                            if isinstance(return_type, type) and issubclass(return_type, BaseCollector):
                                self.register_factory(obj)
                                count += 1
                        except (ValueError, TypeError):
                            # Skip if we can't determine the return type
                            pass
            
            except (ImportError, AttributeError) as e:
                logger.warning(f"Error importing module {module_name}: {str(e)}")
        
        logger.info(f"Discovered {count} collectors")
        return count


# Singleton instance
_registry = None


def get_collector_registry() -> CollectorRegistry:
    """
    Get the singleton instance of the collector registry.
    
    Returns:
        The collector registry instance
    """
    global _registry
    if _registry is None:
        _registry = CollectorRegistry()
    return _registry


def register_collector(
    collector_class: Type[BaseCollector], 
    name: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Register a collector class with the global registry.
    
    Args:
        collector_class: The collector class to register
        name: Optional name to register the collector under
        metadata: Optional metadata for the collector
    """
    registry = get_collector_registry()
    registry.register_collector(collector_class, name, metadata)


def register_factory(
    factory_func: Callable, 
    name: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Register a factory function with the global registry.
    
    Args:
        factory_func: Factory function that returns a BaseCollector instance
        name: Optional name to register the factory under
        metadata: Optional metadata for the factory
    """
    registry = get_collector_registry()
    registry.register_factory(factory_func, name, metadata)


def create_collector(name: str, **kwargs) -> BaseCollector:
    """
    Create a collector instance by name using the global registry.
    
    Args:
        name: Name of the collector or factory
        **kwargs: Arguments to pass to the factory or constructor
        
    Returns:
        A collector instance
    """
    registry = get_collector_registry()
    return registry.create_collector(name, **kwargs)


def list_collectors() -> List[Dict[str, Any]]:
    """
    List all registered collectors with their metadata.
    
    Returns:
        List of dictionaries containing collector information
    """
    registry = get_collector_registry()
    return registry.list_collectors()


def discover_collectors(package: str = 'src.data_collection') -> int:
    """
    Discover and register collectors from a package.
    
    Args:
        package: Package to search for collectors
        
    Returns:
        Number of collectors discovered
    """
    registry = get_collector_registry()
    return registry.discover_collectors(package) 