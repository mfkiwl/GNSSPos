from abc import ABC, abstractmethod

class UserInterface(ABC):
    """
    Abstract base class for user interfaces.
    This class defines the interface for user interfaces in the GNSSPos application.
    It provides methods for displaying messages, errors, and progress updates.
    Subclasses should implement these methods to provide specific user interface functionality.
    """
    
    _gnsspos: any
    """The GNSSPos instance associated with this user interface."""
    
    def setController(self, gnsspos):
        """Set the GNSSPos controller for this user interface."""
        self._gnsspos = gnsspos
        
    def getController(self):
        """Get the GNSSPos controller for this user interface."""
        return self._gnsspos
        
    @abstractmethod
    def start(self):
        """Start the user interface."""
        pass