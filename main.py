import argparse
import logging
import sys

from dotenv import load_dotenv

from gnsspos.gnsspos import GNSSPos
from gnsspos.ui.cli import CLI
from gnsspos.ui.gui import GUI
from PyQt6.QtWidgets import QApplication, QMainWindow

def main():
    PROGRAM_NAME = "GNSSPos"
    PROGRAM_VERSION = "1.5.0"
    welcome_message = f"""Welcome to {PROGRAM_NAME}! This program processes GNSS data, enabling kinematic precise point positioning (PPP) by post-processing .obs RINEX files from multiple receivers simultaneously, integrating them with a base station."""
    
    load_dotenv()

    # argparse is needed to understand if the program should run in CLI or GUI mode
    parser = argparse.ArgumentParser(
        prog=PROGRAM_NAME,
        description=welcome_message
    )

    parser.add_argument('-gui', '--gui', default=True, action='store_true', help="Launch the program in GUI mode, otherwise it will run in CLI mode.")
    
    # The user can specify some parameters, that are mandatory in CLI mode
    # If the user decides to run the program in GUI mode, these parameters will also be passed to the GUI.
    parser.add_argument('-w', '--workdir', default=None, type=str, help="Working directory for processing. It can also be a non-existing directory, in that case it will be created. Please, provide an absolute path.")
    parser.add_argument('-r', '--rovers', default=None, type=str, help="Space-separated list of rovers. Each rover should be in the format 'name,obs_file'. Please, note that the obs_file can be provided using both the relative and the absolute path.")
    parser.add_argument('-b', '--base', default=None, type=str, help="Base station information in the format 'name,obs_file'. Please, note that the obs_file can be provided using both the relative and the absolute path.")
    parser.add_argument('-p', '--plot', action='store_true', default=False, help="Plot the processed data. If enabled, the program will generate plots of the processed GNSS data. In GUI mode, a window will also be opened for visualization.")
    parser.add_argument('-l', '--loglevel', type=str, choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'], default='INFO', help="Set the logging level")
    parser.add_argument('-V', '--version', action='version', version=f'{PROGRAM_NAME} {PROGRAM_VERSION}', help="Show program's version number and exit")

    print(welcome_message)
    print()
    
    # Parse command line arguments checking for required arguments if not in GUI mode
    args = parser.parse_args()
    
    # Set up logging configuration
    logging.basicConfig(level=args.loglevel, format='%(asctime)s [%(levelname)s]: %(message)s')
    
    # if not args.gui:
    #     required_args = ['workdir', 'rovers', 'base']
    #     missing_args = [arg for arg in required_args if not getattr(args, arg)]
    #     if missing_args:
    #         logging.error(f"The following arguments are required in CLI mode: {', '.join('--' + arg for arg in missing_args)}")
    #         sys.exit(1)
    
    try:
        # Set up GNSSPos instance
        gnsspos = GNSSPos(
            workdir=args.workdir,
            rovers=args.rovers,
            base=args.base
        )
        
        if args.gui:
            logging.info(f"{PROGRAM_NAME} starting in GUI mode...")
            app = QApplication([])
            mainWindow = QMainWindow()
            ui = GUI(gnsspos, logging, mainWindow)
        else:
            logging.info(f"{PROGRAM_NAME} starting in CLI mode...")
            ui = CLI(gnsspos, logging)
            
        # link the UI to the GNSSPos instance
        gnsspos.setUi(ui)
        
        # start the UI
        ui.start()
        
        if args.gui:
            sys.exit(app.exec())
    except Exception as e:
        e.with_traceback()
        logging.error(f"An error occurred: {e}")
        sys.exit(1)
    

if __name__ == "__main__":
    main()