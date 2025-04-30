from gnsspos.rover import Rover
from gnsspos.service.igs_data_downloader import IGSDataDownloader
from gnsspos.service.rtk_post_runner import RTKPOSTRunner
from gnsspos.ui.user_interface import UserInterface

import logging
import os

class GNSSPos:
    """
    Core class of GNSSPos. It contains all the methods needed to deal with all the other components, from providing basic acquisition information, gathering necessary files from the IGS portal, collecting RINEX .obs files from different rovers, base station data, to post-processing by integrating RTKPOST.
    """
    
    _workdir: str
    """Working directory for processing."""
    
    _rovers: list[Rover]
    """List of rover/base station information in the format 'name,obs_file'."""
    
    _base: Rover | None
    """Base station information in the format 'name,obs_file'."""
    
    _distances: dict[(Rover, Rover), float]
    """Distances between rovers on the vehicle."""
    
    _thresholds: dict[(Rover, Rover), float]
    """Thresholds on the distances between rovers on the vehicle."""
    
    _plot: bool
    """Plot the processed data."""
    
    _rtkpost_runner: RTKPOSTRunner
    """RTKPOST runner instance."""
    
    _igs_downloader: IGSDataDownloader
    """IGS data downloader instance."""
    
    _ui: UserInterface
    """User interface instance."""
    
    def __init__(self, workdir: str, rovers: str, base: str):
        """Initialize the GNSSPos class with the given parameters."""
        
        # Set up the working directory. 
        if workdir is not None:
            self.setWorkdir(workdir)
        
        # Set up rover informations
        if rovers is not None:
            for obsFile in rovers.split(','):
                self.addRover(name=self.getNewRoverName(), obs_file=obsFile)
                
        # Set up base station information
        if base is not None:
            self.setBaseStationOBS(obs_file=base)
            
        # Initialize the distances and thresholds
        self._distances = {}
        self._thresholds = {}
        
        # Check for NASA credentials in the loaded environment variables
        if not os.getenv("NASA_USER") or not os.getenv("NASA_PWD"):
            raise Exception("NASA_USER and NASA_PWD environment variables must be set.")
        
        self._ui = None
        self._rtkpost_runner = RTKPOSTRunner(
            rnx2rtkp_path=os.getenv("RNX2RTKP_PATH"),
        )        
        self._igs_downloader = IGSDataDownloader(
            nasaUsr=os.getenv("NASA_USER"),
            nasaPwd=os.getenv("NASA_PWD")
        )
        
    def getIGSDownloader(self) -> IGSDataDownloader:
        """Get the IGS data downloader instance."""
        return self._igs_downloader
    
    def getRTKPOSTRunner(self) -> RTKPOSTRunner:
        """Get the RTKPOST runner instance."""
        return self._rtkpost_runner
    
    def setWorkdir(self, value):
        """Set the working directory for processing."""
        if not os.path.exists(value):
            os.makedirs(value)
        elif not os.path.isdir(value) or os.listdir(value):
            raise Exception(f"The directory '{value}' is not empty or is not a valid directory.")
        self._workdir = os.path.abspath(value)
        
    def getWorkdir(self) -> str:
        """Get the working directory for processing."""
        return self._workdir
        
    def getRovers(self) -> list[Rover]:
        """Get the list of rover/base station information."""
        return self._rovers
    
    def clearRovers(self):
        """Clear the list of rover/base station information."""
        self._rovers = []
        
    def getNewRoverName(self) -> str:
        """Get a name for a new rover."""
        upperBound = len(self._rovers) + 1
        for i in range(upperBound):
            roverName = f"Rover {i+1}"
            if roverName not in [r.name for r in self._rovers]:
                return roverName
    
    def addRover(self, name: str, obs_file: str):
        """Add a rover."""
        if obs_file is not None and os.path.isfile(obs_file) and not os.path.exists(obs_file):
            raise Exception(f"The file '{obs_file}' does not exist.")
        self._rovers.append(Rover(name=name, obs_file=obs_file))
        
    def deleteRover(self, name: str):
        """Delete a rover."""
        for i, rover in enumerate(self._rovers):
            if rover.name == name:
                del self._rovers[i]
                break
        else:
            raise Exception(f"{name} not found.")
        
    def setBaseStationOBS(self, obs_file: str):
        """Set the base station information."""
        if obs_file is not None and os.path.isfile(obs_file) and not os.path.exists(obs_file):
            raise Exception(f"The file '{obs_file}' does not exist.")
        self._base = Rover(name="Base Station", obs_file=obs_file)
        
    def getThresholds(self) -> dict[(any, any), float]:
        """Get the thresholds on the distances between rovers on the vehicle."""
        return self._thresholds
    
    def setThreshold(self, pair: tuple[any, any], value: float):
        """Set the threshold on the distance between a pair of rovers."""
        if not isinstance(pair, tuple) or len(pair) != 2:
            raise Exception("Pair must be a tuple containing two Rover instances.")
        if not isinstance(value, (int, float)) or value < 0:
            raise Exception("Threshold value must be a non-negative number.")
        if self._thresholds is None:
            self._thresholds = {}
        self._thresholds[pair] = value
        
    def getDistances(self) -> dict[(any, any), float]:
        """Get the distances between rovers on the vehicle."""
        return self._distances
    
    def setDistance(self, pair: tuple[any, any], value: float):
        """Set the distance between a pair of rovers."""
        if not isinstance(pair, tuple) or len(pair) != 2:
            raise Exception("Pair must be a tuple containing two Rover instances.")
        if not isinstance(value, (int, float)) or value < 0:
            raise Exception("Distance value must be a non-negative number.")
        if self._distances is None:
            self._distances = {}
        self._distances[pair] = value
        
    def run(self, additionalArgs: dict = {}, logFunction=None):
        """Run the GNSSPos processing."""
        if self._ui is None:
            raise Exception("User interface is not set.")
        if self._rtkpost_runner is None:
            raise Exception("RTKPOST runner is not set.")
        if self._igs_downloader is None:
            raise Exception("IGS data downloader is not set.")
        if self._workdir is None:
            raise Exception("Working directory is not set.")
        if self._rovers is None or len(self._rovers) == 0:
            raise Exception("No rovers are set.")
        if self._base is None:
            raise Exception("Base station is not set.")
        if self._distances is None:
            raise Exception("Distances between rovers are not set.")
        if self._thresholds is None or len(self._thresholds) == 0:
            raise Exception("Thresholds on the distances between rovers are not set.")
        
        igsFiles = self.getIGSDownloader().getFiles()
        
        # Process the base station data
        try:
            self._base.setPosFile(self.getRTKPOSTRunner().processBase(
                workdir=self._workdir,
                outFile=os.path.join(self.getWorkdir(), "base_station.pos"),
                baseObsFile=self._base.obs_file,
                navFile=igsFiles['broadcast_eph'],
                sp3File=igsFiles['orbits'],
                ionexFile=igsFiles['ionosphere'],
                additionalArgs=additionalArgs,
                logFunction=logFunction
            ))
        except Exception as e:
            raise Exception(f"Error processing base station data: {e}")
        
        # Process the rover data
        try:
            for rover in self._rovers:
                posFile = f"{rover.name}.pos"
                posFile = posFile.replace(" ", "_")
                posFile = posFile.lower()
                posFile = posFile.strip()
                rover.setPosFile(self.getRTKPOSTRunner().processRover(
                    workdir=self._workdir,
                    outFile=os.path.join(self.getWorkdir(), posFile),
                    roverObsFile=rover.obs_file,
                    baseObsFile=self._base.obs_file,
                    basePosFile=self._base.getPosFile(),
                    navFile=igsFiles['broadcast_eph'],
                    sp3File=igsFiles['orbits'],
                    ionexFile=igsFiles['ionosphere'],
                    additionalArgs=additionalArgs,
                    logFunction=logFunction
                ))
        except Exception as e:
            raise Exception(f"Error processing {rover.name} data: {e}")
        
        # Implementation of the algorithm...
        # TODO: place code here
        
        logFunction.info("Processing completed successfully.")
         
        
    def setUi(self, ui: UserInterface):
        """Set the user interface for the GNSSPos instance."""
        self._ui = ui