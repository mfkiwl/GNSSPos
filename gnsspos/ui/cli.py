from gnsspos.ui.user_interface import UserInterface
from gnsspos.rover import Rover

import os

class CLI(UserInterface):
    """
    Command Line Interface (CLI) for GNSSPos.
    This class implements the UserInterface abstract base class for command line interaction.
    It provides methods for displaying messages, errors, and progress updates in the console.
    """
    
    def __init__(self, gnsspos, logger):
        """Initialize the CLI interface."""
        super().setController(gnsspos)
        self.logger = logger
        
    def start(self):
        """Start the CLI interface."""
        controller = super().get_controller()
        print()
        print("The CLI version of GNSSPos has not been implemented yet. Please use the GUI version.")