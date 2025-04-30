class Rover:
    """Class representing a rover/base station in GNSS positioning."""
    
    name: str
    """Name of the rover."""
    
    obs_file: str
    """Path to the observation file associated with the rover."""
    
    _pos_file: str
    """Path to the position file containing the rover's coordinates."""
    
    def __init__(self, name: str = "", obs_file: str = "", pos_file: str = ""):
        """Initialize the Rover with a name, observation file."""
        self.name = name
        self.obs_file = obs_file
        self._pos_file = pos_file
        
    def setPosFile(self, pos_file: str):
        """Set the position file for the rover."""
        self._pos_file = pos_file
        
    def getPosFile(self) -> str:
        """Get the position file of the rover."""
        return self._pos_file