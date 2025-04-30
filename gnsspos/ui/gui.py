from gnsspos.gnsspos import GNSSPos
from gnsspos.rover import Rover
from gnsspos.ui.user_interface import UserInterface
from time import sleep

import sys
import os
from PyQt6 import QtWidgets, QtCore, QtGui


class GUI(UserInterface):
    """
    Graphic User Interface (GUI) for GNSSPos.
    This class implements the UserInterface abstract base class for the graphical user interface.
    It uses PyQt to create and manage the GUI components.
    """
    
    def __init__(self, gnsspos, logger, mainWindow):
        """Initialize the GUI interface."""
        super().setController(gnsspos)
        self.logger = logger
        self.mainWindow = mainWindow
        self._checks = {}
        
    def start(self):
        """Start the GUI interface."""
        self.setupUi(self.mainWindow)
        self.mainWindow.setWindowFlags(QtCore.Qt.WindowType.WindowCloseButtonHint | QtCore.Qt.WindowType.WindowMinimizeButtonHint)
        self.mainWindow.show()
        
        # Add status bar
        self.statusBar = QtWidgets.QStatusBar(self.mainWindow)
        self.mainWindow.setStatusBar(self.statusBar)
        
        # Disable fields
        self.txtStartingTime.setEnabled(False)
        self.txtEndTime.setEnabled(False)
        self.cmbTimeInterval.setEnabled(False)
        self.btnDownloadIGSData.setEnabled(False)
        self.btnRUN.setEnabled(False)
        self.btnPlotPositions.setEnabled(False)
        self.btnSetupDistances.setEnabled(False)
        self.btnSetupThresholds.setEnabled(False)
        self.btnDeleteRover.setEnabled(False)
        self.txtBaseStationOBS.setReadOnly(True)
        self.txtWorkingDirectory.setReadOnly(True)
        
        # TODO: disable the "Add Rover" button until the working directory is set
        # self.btnAddRover.setEnabled(False)
        self.setCheck('workingDirectory', False)
        self.setCheck('igsData', False)
        self.setCheck('rovers', False)
        self.setCheck('distances', False)
        self.setCheck('thresholds', False)
        self.setCheck('baseStation', False)
        
        # Set the default date in the calendar
        self.calDateTime.setSelectedDate(QtCore.QDate.currentDate())
        self.calDateTime.setGridVisible(True)
        self.chooseObservationDate()
        
        # Fill the time interval combo box and select the default value
        for i in [1, 2, 5, 10, 15, 30, 60]:
            self.cmbTimeInterval.addItem(str(i))
        self.cmbTimeInterval.setCurrentText("1")
        
        # Add the IGS data providers to the combo box
        self.cmbIGSDataProvider.addItem(super().getController().getIGSDownloader().PROVIDER_URL)
        self.cmbIGSDataProvider.setCurrentText(super().getController().getIGSDownloader().PROVIDER_URL)
        self.cmbIGSDataProvider.setEnabled(True)
        
        # Remove all the rovers from the list
        self.tabsRover.clear()
        super().getController().clearRovers()
        
        # Log the initial message
        self.log("Select a working directory to start using GNSSPos.", level="info")
        
        # Connect signals to slots (add event handlers)
        self.chkStartingTime.clicked.connect(self.toggleStartingTime)
        self.chkEndTime.clicked.connect(self.toggleEndTime)
        self.chkTimeInterval.clicked.connect(self.toggleTimeInterval)
        
        self.btnChooseDirectory.clicked.connect(self.chooseWorkingDirectory)
        self.calDateTime.clicked.connect(self.chooseObservationDate)
        self.btnDownloadIGSData.clicked.connect(self.downloadIGSData)
        self.btnAddRover.clicked.connect(self.addRover)
        self.btnDeleteRover.clicked.connect(self.deleteSelectedRover)
        self.btnChooseBaseStationOBS.clicked.connect(self.chooseBaseStationOBSFile)
        self.btnSetupThresholds.clicked.connect(self.setupThresholds)
        self.btnSetupDistances.clicked.connect(self.setupDistances)
        self.btnRUN.clicked.connect(self.run)
        self.btnPlotPositions.clicked.connect(self.plotPositions)
        
    def toggleStartingTime(self):
        """Toggle the starting time field."""
        self.txtStartingTime.setEnabled(self.chkStartingTime.isChecked())
        
    def toggleEndTime(self):
        """Toggle the end time field."""
        self.txtEndTime.setEnabled(self.chkEndTime.isChecked())
        
    def toggleTimeInterval(self):
        """Toggle the time interval field."""
        self.cmbTimeInterval.setEnabled(self.chkTimeInterval.isChecked())
        
    def chooseWorkingDirectory(self):
        """Open a dialog to choose the working directory."""
        try:
            directory = QtWidgets.QFileDialog.getExistingDirectory(self.mainWindow, "Select Working Directory")
            if directory:
                self.txtWorkingDirectory.setText(f"{directory}/")
                super().getController().setWorkdir(directory)
                self.log(f"Working directory correctly set to: {directory}. Pick the date on the calendar, then download the IGS data.")
                # enable the download button
                self.btnDownloadIGSData.setEnabled(True)
                self.setCheck('workingDirectory', True)
                self.setCheck('igsData', False)
        except Exception as e:
            self.log(f"Error selecting working directory: {e}", level="error")
            
    def chooseObservationDate(self):
        """Take the selected date from the calendar, convert and set the date in the labels."""
        try:
            date = self.calDateTime.selectedDate()
            
            if self.lblSelectedDate.text() != date.toString("yyyy-MM-dd") and self.lblSelectedDate.text() != "dd/MM/yyyy": # and self.btnDownloadIGSData.isEnabled():
                # the user has changed the date after having already selected it once
                self.setCheck('igsData', False)
                
            date_dict = super().getController().getIGSDownloader().setDate(date.year(), date.month(), date.day())
            self.lblSelectedDate.setText(date_dict['date_str'])
            self.lblYYYY.setText(str(date_dict['YYYY']))
            self.lblYY.setText(str(date_dict['YY']))
            self.lblDDD.setText(str(date_dict['DDD']))
            self.lblD.setText(str(date_dict['D']))
            self.lblWWWW.setText(str(date_dict['WWWW']))
        except Exception as e:
            self.log(f"Error selecting observation date: {e}", level="error")
            
    def downloadIGSData(self):
        """Download the IGS data from the selected provider."""
        try:
            # download the data
            super().getController().getIGSDownloader().downloadBroadcastEphemeris(super().getController().getWorkdir())
            self.log("Broadcast ephemeris downloaded successfully.")
            super().getController().getIGSDownloader().downloadPreciseFinalOrbit(super().getController().getWorkdir())
            self.log("Precise final orbit downloaded successfully.")
            super().getController().getIGSDownloader().downloadPreciseFinalClock(super().getController().getWorkdir())
            self.log("Precise final clock downloaded successfully.")
            super().getController().getIGSDownloader().downloadIonosphere(super().getController().getWorkdir())
            self.log("Ionosphere data downloaded successfully.")
            super().getController().getIGSDownloader().downloadTroposhpere(super().getController().getWorkdir())
            self.log("Troposhpere data downloaded successfully.")
            # remove the yellow background color
            self.log("IGS data downloaded successfully.")
            self.setCheck('igsData', True)
            
            # TODO: enable "Add Rover" button
            # self.btnAddRover.setEnabled(True)
        except Exception as e:
            self.log(f"Error while getting IGS data: {e}", level="error")
            
    def addRover(self):
        """Add a rover tab."""
        try:
            # open a dialog to choose the rover observation file
            obsFile, _ = QtWidgets.QFileDialog.getOpenFileName(self.mainWindow, "Select Rover OBS File")
            newRoverName = super().getController().getNewRoverName()
            super().getController().addRover(newRoverName, obsFile)
            # add the rover tab to the GUI
            self.tabsRover.addTab(Ui_RoverTab(obsFile=obsFile), newRoverName)
            self.tabsRover.setCurrentIndex(self.tabsRover.count() - 1)
            self.setCheck('rovers', True)
            
            # enable the delete button
            self.btnDeleteRover.setEnabled(True)
            # enable the thresholds and distances buttons only if there are at least 2 rovers
            if self.tabsRover.count() > 1:
                self.btnSetupDistances.setEnabled(True)    
                self.btnSetupThresholds.setEnabled(True)
            else:
                # disable the thresholds and distances buttons
                self.btnSetupDistances.setEnabled(False)    
                self.btnSetupThresholds.setEnabled(False)
            
            # change the background color of thresholds and distances button to yellow
            self.setCheck('distances', False)
            self.setCheck('thresholds', False)
            
            self.log(f"{newRoverName} added successfully.")
            # remove the yellow background color
            self.btnAddRover.setStyleSheet("")
        except Exception as e:
            self.log(f"Error adding rover: {e}", level="error")
            
    def deleteSelectedRover(self):
        """Delete the selected rover tab."""
        try:
            currentIndex = self.tabsRover.currentIndex()
            roverName = self.tabsRover.tabText(currentIndex)
            reply = QtWidgets.QMessageBox.question(
                self.mainWindow,
                "Confirm Deletion",
                f"Are you sure you want to delete '{roverName}'?",
                QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
            )
            if reply != QtWidgets.QMessageBox.StandardButton.Yes:
                return
            if currentIndex != -1:
                super().getController().deleteRover(roverName)
                self.tabsRover.removeTab(currentIndex)
                # disable the delete button if there are no more rovers
                if self.tabsRover.count() == 0:
                    # disable the delete button
                    self.btnDeleteRover.setEnabled(False)
                    # disable thresholds and distances buttons
                    self.btnSetupDistances.setEnabled(False)    
                    self.btnSetupThresholds.setEnabled(False)
                    # restore checks for rover
                    self.setCheck('rovers', False)
                
                self.setCheck('distances', False)
                self.setCheck('thresholds', False)
                
                self.log(f"{roverName} deleted successfully.")
        except Exception as e:
            self.log(f"Error deleting rover: {e}", level="error")
            
    def chooseBaseStationOBSFile(self):
        """Open a dialog to choose the base station observation file."""
        try:
            # open a dialog to choose the base station observation file
            obsFile, _ = QtWidgets.QFileDialog.getOpenFileName(self.mainWindow, "Select Base Station OBS File")
            if obsFile is not None and obsFile != "":
                super().getController().setBaseStationOBS(obsFile)
                # update the base station .obs text field with the selected file
                self.txtBaseStationOBS.setText(obsFile)
                self.setCheck('baseStation', True)
                self.log(f"Base Station observation file selected successfully.")
        except Exception as e:
            self.log(f"Error selecting base station observation file: {e}", level="error")
            
    def setupThresholds(self):
        """
        Open a dialog to set the thresholds on the distances between rovers.
        """
        self.thresholdWidget = Ui_ThresholdsPopup(super().getController(), self)
        self.thresholdWidget.show()
        self.setCheck('thresholds', True)
        
    def setThreshold(self, rover1, rover2, value):
        """
        Set the threshold on the distance between rovers.
        """
        try:
            # set the threshold on the distance between two rovers
            super().getController().setThreshold((rover1, rover2), value)
            nomeRover1 = str(rover1.name) if rover1 is not None else rover1
            nomeRover2 = str('-' + rover2.name) if rover2 is not None else ""
            self.log(f"Threshold for {nomeRover1}{nomeRover2} set to {value}.")
        except Exception as e:
            self.log(f"Error setting threshold: {e}", level="error")
        
    def setupDistances(self):
        """
        Open a dialog to set the distances between rovers.
        """
        self.distancesWidget = Ui_DistancesPopup(super().getController(), self)
        self.distancesWidget.show()
        self.setCheck('distances', True)
        
    def setDistance(self, rover1, rover2, value):
        """
        Set the distance between rovers.
        """
        try:
            # set the distance between two rovers
            super().getController().setDistance((rover1, rover2), value)
            self.log(f"Distance between {rover1.name} and {rover2.name} set to {value}.")
        except Exception as e:
            self.log(f"Error setting distance: {e}", level="error")
    
    def run(self):
        try:
            # understand if there are any additional arguments to pass to the controller. In our case:
            additionalArgs = {}
            
            #   -ts   ds ts start day/time (ds=y/m/d ts=h:m:s) [obs start time]
            if self.chkStartingTime.isChecked():
                startingDate = super().getController().getIGSDownloader().getDate()
                startingTime = f"{self.txtStartingTime.text()}:00"
                additionalArgs['-ts'] = f'{startingDate.year()}/{startingDate.month()}/{startingDate.day()} {startingTime}'
            
            #   -te   de te end day/time (de=y/m/d te=h:m:s) [obs end time]
            if self.chkEndTime.isChecked():
                if not self.chkStartingTime.isChecked():
                    raise Exception("Ending time requires a starting time to be set.")
                startingDate = super().getController().getIGSDownloader().getDate()
                startingTime = f"{self.txtStartingTime.text()}:00"
                endingDate = super().getController().getIGSDownloader().getDate()
                endingTime = f"{self.txtEndTime.text()}:00"
                # Ensure ending time is greater than starting time
                start_time_obj = QtCore.QTime.fromString(self.txtStartingTime.text(), "HH:mm")
                end_time_obj = QtCore.QTime.fromString(self.txtEndTime.text(), "HH:mm")
                if end_time_obj <= start_time_obj:
                    raise Exception("Ending time must be greater than starting time.")
                additionalArgs['-te'] = f'{endingDate.year()}/{endingDate.month()}/{endingDate.day()} {endingTime}'
            
            #   -ti   tint time interval (sec) [all]
            if self.chkTimeInterval.isChecked():
                time_interval = float(self.cmbTimeInterval.currentText())
                if time_interval > 0:
                    additionalArgs['-ti'] = str(time_interval)
                else:
                    raise Exception("Time interval must be greater than 0.")
            
            # run the processing
            self.log("Processing started...")
            super().getController().run(additionalArgs, self.log)
            self.log("Processing completed successfully.")
            # enable the plot button
            self.btnPlotPositions.setEnabled(True)
        except Exception as e:
            self.log(f"Error during processing: {e}", level="error")
    
    def plotPositions(self):
        # TODO:
        pass
    
    def setCheck(self, checkType, value):
        """
        Set the check status for a specific element.
        If value is True, the background color is removed; otherwise its background color is set.
        """
        self._checks[checkType] = value
        
        widgets_map = {
            'workingDirectory': [self.txtWorkingDirectory, self.btnChooseDirectory],
            'igsData': [self.btnDownloadIGSData],
            'rovers': [self.btnAddRover],
            'distances': [self.btnSetupDistances],
            'thresholds': [self.btnSetupThresholds],
            'baseStation': [self.txtBaseStationOBS, self.btnChooseBaseStationOBS],
        }

        if checkType in widgets_map:
            widgets = widgets_map[checkType]
            for widget in widgets:
                widget.setStyleSheet("" if value else "background-color: lightyellow;")
        
        # Enable the RUN button if all checks are True
        self.btnRUN.setEnabled(all(self._checks.values()))
        # Disable the plot button
        self.btnPlotPositions.setEnabled(False)
    
    def log(self, message, level="info"):
        """Log messages to the status bar and the logger."""
        if level == "info":
            self.statusBar.setStyleSheet("QStatusBar { background-color: lightgray; }")
            self.logger.info(message)
        elif level == "warning":
            self.statusBar.setStyleSheet("QStatusBar { background-color: yellow; }")
            self.logger.warning(message)
        elif level == "error":
            self.statusBar.setStyleSheet("QStatusBar { background-color: red; }")
            self.logger.error(message)
        self.statusBar.showMessage(message)
        sleep(2)
        
    # Form implementation generated from reading ui file 'GUI.ui'
    #
    # Created by: PyQt6 UI code generator 6.4.2
    #
    # WARNING: Any manual changes made to this file will be lost when pyuic6 is
    # run again.  Do not edit this file unless you know what you are doing.
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(595, 679)
        self.centralwidget = QtWidgets.QWidget(parent=MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.lblGeneralSettings = QtWidgets.QLabel(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        font.setStrikeOut(False)
        self.lblGeneralSettings.setFont(font)
        self.lblGeneralSettings.setObjectName("lblGeneralSettings")
        self.gridLayout.addWidget(self.lblGeneralSettings, 0, 0, 1, 1)
        self.hlyworkingDirectory = QtWidgets.QHBoxLayout()
        self.hlyworkingDirectory.setObjectName("hlyworkingDirectory")
        self.lblWorkingDirectory = QtWidgets.QLabel(parent=self.centralwidget)
        self.lblWorkingDirectory.setObjectName("lblWorkingDirectory")
        self.hlyworkingDirectory.addWidget(self.lblWorkingDirectory)
        self.txtWorkingDirectory = QtWidgets.QLineEdit(parent=self.centralwidget)
        self.txtWorkingDirectory.setObjectName("txtWorkingDirectory")
        self.hlyworkingDirectory.addWidget(self.txtWorkingDirectory)
        self.btnChooseDirectory = QtWidgets.QToolButton(parent=self.centralwidget)
        self.btnChooseDirectory.setObjectName("btnChooseDirectory")
        self.hlyworkingDirectory.addWidget(self.btnChooseDirectory)
        self.gridLayout.addLayout(self.hlyworkingDirectory, 1, 0, 1, 1)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.calDateTime = QtWidgets.QCalendarWidget(parent=self.centralwidget)
        self.calDateTime.setObjectName("calDateTime")
        self.horizontalLayout_2.addWidget(self.calDateTime)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.formLayout = QtWidgets.QFormLayout()
        self.formLayout.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignTrailing|QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.formLayout.setFormAlignment(QtCore.Qt.AlignmentFlag.AlignLeading|QtCore.Qt.AlignmentFlag.AlignLeft|QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.formLayout.setObjectName("formLayout")
        self.lblDate = QtWidgets.QLabel(parent=self.centralwidget)
        self.lblDate.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignTrailing|QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.lblDate.setObjectName("lblDate")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.ItemRole.LabelRole, self.lblDate)
        self.lblSelectedDate = QtWidgets.QLabel(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.lblSelectedDate.setFont(font)
        self.lblSelectedDate.setObjectName("lblSelectedDate")
        self.formLayout.setWidget(0, QtWidgets.QFormLayout.ItemRole.FieldRole, self.lblSelectedDate)
        self.lbl4DigitYYYY = QtWidgets.QLabel(parent=self.centralwidget)
        self.lbl4DigitYYYY.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignTrailing|QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.lbl4DigitYYYY.setObjectName("lbl4DigitYYYY")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.ItemRole.LabelRole, self.lbl4DigitYYYY)
        self.lblYYYY = QtWidgets.QLabel(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.lblYYYY.setFont(font)
        self.lblYYYY.setObjectName("lblYYYY")
        self.formLayout.setWidget(1, QtWidgets.QFormLayout.ItemRole.FieldRole, self.lblYYYY)
        self.lbl2DigitYY = QtWidgets.QLabel(parent=self.centralwidget)
        self.lbl2DigitYY.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignTrailing|QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.lbl2DigitYY.setObjectName("lbl2DigitYY")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.ItemRole.LabelRole, self.lbl2DigitYY)
        self.lblYY = QtWidgets.QLabel(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.lblYY.setFont(font)
        self.lblYY.setObjectName("lblYY")
        self.formLayout.setWidget(2, QtWidgets.QFormLayout.ItemRole.FieldRole, self.lblYY)
        self.lbl4DigitWWWW = QtWidgets.QLabel(parent=self.centralwidget)
        self.lbl4DigitWWWW.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignTrailing|QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.lbl4DigitWWWW.setObjectName("lbl4DigitWWWW")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.ItemRole.LabelRole, self.lbl4DigitWWWW)
        self.lblWWWW = QtWidgets.QLabel(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.lblWWWW.setFont(font)
        self.lblWWWW.setObjectName("lblWWWW")
        self.formLayout.setWidget(3, QtWidgets.QFormLayout.ItemRole.FieldRole, self.lblWWWW)
        self.lbl3DigitDDD = QtWidgets.QLabel(parent=self.centralwidget)
        self.lbl3DigitDDD.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignTrailing|QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.lbl3DigitDDD.setObjectName("lbl3DigitDDD")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.ItemRole.LabelRole, self.lbl3DigitDDD)
        self.lblDDD = QtWidgets.QLabel(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.lblDDD.setFont(font)
        self.lblDDD.setObjectName("lblDDD")
        self.formLayout.setWidget(4, QtWidgets.QFormLayout.ItemRole.FieldRole, self.lblDDD)
        self.lbl1DigitD = QtWidgets.QLabel(parent=self.centralwidget)
        self.lbl1DigitD.setAlignment(QtCore.Qt.AlignmentFlag.AlignRight|QtCore.Qt.AlignmentFlag.AlignTrailing|QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.lbl1DigitD.setObjectName("lbl1DigitD")
        self.formLayout.setWidget(5, QtWidgets.QFormLayout.ItemRole.LabelRole, self.lbl1DigitD)
        self.lblD = QtWidgets.QLabel(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.lblD.setFont(font)
        self.lblD.setObjectName("lblD")
        self.formLayout.setWidget(5, QtWidgets.QFormLayout.ItemRole.FieldRole, self.lblD)
        self.verticalLayout.addLayout(self.formLayout)
        self.hlyStartTime = QtWidgets.QHBoxLayout()
        self.hlyStartTime.setObjectName("hlyStartTime")
        self.chkStartingTime = QtWidgets.QCheckBox(parent=self.centralwidget)
        self.chkStartingTime.setObjectName("chkStartingTime")
        self.hlyStartTime.addWidget(self.chkStartingTime)
        self.txtStartingTime = QtWidgets.QTimeEdit(parent=self.centralwidget)
        self.txtStartingTime.setObjectName("txtStartingTime")
        self.hlyStartTime.addWidget(self.txtStartingTime)
        self.verticalLayout.addLayout(self.hlyStartTime)
        self.hlyEndTime = QtWidgets.QHBoxLayout()
        self.hlyEndTime.setObjectName("hlyEndTime")
        self.chkEndTime = QtWidgets.QCheckBox(parent=self.centralwidget)
        self.chkEndTime.setObjectName("chkEndTime")
        self.hlyEndTime.addWidget(self.chkEndTime)
        self.txtEndTime = QtWidgets.QTimeEdit(parent=self.centralwidget)
        self.txtEndTime.setObjectName("txtEndTime")
        self.hlyEndTime.addWidget(self.txtEndTime)
        self.verticalLayout.addLayout(self.hlyEndTime)
        self.hlyTimeInterval = QtWidgets.QHBoxLayout()
        self.hlyTimeInterval.setObjectName("hlyTimeInterval")
        self.chkTimeInterval = QtWidgets.QCheckBox(parent=self.centralwidget)
        self.chkTimeInterval.setObjectName("chkTimeInterval")
        self.hlyTimeInterval.addWidget(self.chkTimeInterval)
        self.cmbTimeInterval = QtWidgets.QComboBox(parent=self.centralwidget)
        self.cmbTimeInterval.setObjectName("cmbTimeInterval")
        self.hlyTimeInterval.addWidget(self.cmbTimeInterval)
        self.verticalLayout.addLayout(self.hlyTimeInterval)
        self.horizontalLayout_2.addLayout(self.verticalLayout)
        self.gridLayout.addLayout(self.horizontalLayout_2, 2, 0, 1, 1)
        self.hlyIGSProvider = QtWidgets.QHBoxLayout()
        self.hlyIGSProvider.setObjectName("hlyIGSProvider")
        self.lblIGSDataProvider = QtWidgets.QLabel(parent=self.centralwidget)
        self.lblIGSDataProvider.setObjectName("lblIGSDataProvider")
        self.hlyIGSProvider.addWidget(self.lblIGSDataProvider)
        self.cmbIGSDataProvider = QtWidgets.QComboBox(parent=self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Policy.Expanding, QtWidgets.QSizePolicy.Policy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.cmbIGSDataProvider.sizePolicy().hasHeightForWidth())
        self.cmbIGSDataProvider.setSizePolicy(sizePolicy)
        self.cmbIGSDataProvider.setObjectName("cmbIGSDataProvider")
        self.hlyIGSProvider.addWidget(self.cmbIGSDataProvider)
        self.btnDownloadIGSData = QtWidgets.QPushButton(parent=self.centralwidget)
        self.btnDownloadIGSData.setObjectName("btnDownloadIGSData")
        self.hlyIGSProvider.addWidget(self.btnDownloadIGSData)
        self.gridLayout.addLayout(self.hlyIGSProvider, 3, 0, 1, 1)
        self.line = QtWidgets.QFrame(parent=self.centralwidget)
        self.line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self.line.setObjectName("line")
        self.gridLayout.addWidget(self.line, 4, 0, 1, 1)
        self.vlyRoversBase = QtWidgets.QVBoxLayout()
        self.vlyRoversBase.setObjectName("vlyRoversBase")
        self.vlyRovers = QtWidgets.QVBoxLayout()
        self.vlyRovers.setObjectName("vlyRovers")
        self.lblRovers = QtWidgets.QLabel(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.lblRovers.setFont(font)
        self.lblRovers.setObjectName("lblRovers")
        self.vlyRovers.addWidget(self.lblRovers)
        self.hlyRoverButtons = QtWidgets.QHBoxLayout()
        self.hlyRoverButtons.setObjectName("hlyRoverButtons")
        self.btnSetupThresholds = QtWidgets.QPushButton(parent=self.centralwidget)
        self.btnSetupThresholds.setObjectName("btnSetupThresholds")
        self.hlyRoverButtons.addWidget(self.btnSetupThresholds)
        self.btnSetupDistances = QtWidgets.QPushButton(parent=self.centralwidget)
        self.btnSetupDistances.setObjectName("btnSetupDistances")
        self.hlyRoverButtons.addWidget(self.btnSetupDistances)
        self.btnAddRover = QtWidgets.QPushButton(parent=self.centralwidget)
        self.btnAddRover.setObjectName("btnAddRover")
        self.hlyRoverButtons.addWidget(self.btnAddRover)
        self.btnDeleteRover = QtWidgets.QPushButton(parent=self.centralwidget)
        self.btnDeleteRover.setEnabled(False)
        self.btnDeleteRover.setObjectName("btnDeleteRover")
        self.hlyRoverButtons.addWidget(self.btnDeleteRover)
        self.vlyRovers.addLayout(self.hlyRoverButtons)
        self.tabsRover = QtWidgets.QTabWidget(parent=self.centralwidget)
        self.tabsRover.setObjectName("tabsRover")
        self.tab = QtWidgets.QWidget()
        self.tab.setObjectName("tab")
        self.tabsRover.addTab(self.tab, "")
        self.tab_2 = QtWidgets.QWidget()
        self.tab_2.setObjectName("tab_2")
        self.tabsRover.addTab(self.tab_2, "")
        self.vlyRovers.addWidget(self.tabsRover)
        self.vlyRoversBase.addLayout(self.vlyRovers)
        self.vlyBaseStation = QtWidgets.QVBoxLayout()
        self.vlyBaseStation.setObjectName("vlyBaseStation")
        self.lblBaseStation = QtWidgets.QLabel(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(12)
        font.setBold(True)
        font.setWeight(75)
        self.lblBaseStation.setFont(font)
        self.lblBaseStation.setObjectName("lblBaseStation")
        self.vlyBaseStation.addWidget(self.lblBaseStation)
        self.hlyOBSFileName = QtWidgets.QHBoxLayout()
        self.hlyOBSFileName.setObjectName("hlyOBSFileName")
        self.lblBaseStationOBS = QtWidgets.QLabel(parent=self.centralwidget)
        self.lblBaseStationOBS.setObjectName("lblBaseStationOBS")
        self.hlyOBSFileName.addWidget(self.lblBaseStationOBS)
        self.txtBaseStationOBS = QtWidgets.QLineEdit(parent=self.centralwidget)
        self.txtBaseStationOBS.setObjectName("txtBaseStationOBS")
        self.hlyOBSFileName.addWidget(self.txtBaseStationOBS)
        self.btnChooseBaseStationOBS = QtWidgets.QToolButton(parent=self.centralwidget)
        self.btnChooseBaseStationOBS.setObjectName("btnChooseBaseStationOBS")
        self.hlyOBSFileName.addWidget(self.btnChooseBaseStationOBS)
        self.vlyBaseStation.addLayout(self.hlyOBSFileName)
        self.vlyRoversBase.addLayout(self.vlyBaseStation)
        self.gridLayout.addLayout(self.vlyRoversBase, 5, 0, 1, 1)
        self.line_3 = QtWidgets.QFrame(parent=self.centralwidget)
        self.line_3.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        self.line_3.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        self.line_3.setObjectName("line_3")
        self.gridLayout.addWidget(self.line_3, 6, 0, 1, 1)
        self.hlyButtons = QtWidgets.QHBoxLayout()
        self.hlyButtons.setObjectName("hlyButtons")
        self.btnRUN = QtWidgets.QPushButton(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(14)
        font.setBold(False)
        font.setWeight(50)
        font.setKerning(False)
        self.btnRUN.setFont(font)
        self.btnRUN.setObjectName("btnRUN")
        self.hlyButtons.addWidget(self.btnRUN)
        self.btnPlotPositions = QtWidgets.QPushButton(parent=self.centralwidget)
        font = QtGui.QFont()
        font.setPointSize(14)
        self.btnPlotPositions.setFont(font)
        self.btnPlotPositions.setObjectName("btnPlotPositions")
        self.hlyButtons.addWidget(self.btnPlotPositions)
        self.gridLayout.addLayout(self.hlyButtons, 7, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(parent=MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 595, 22))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(parent=MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        MainWindow.setWindowIcon(QtGui.QIcon(os.path.join(os.path.dirname(__file__), '..', '..', "logo.png")))

        self.retranslateUi(MainWindow)
        self.tabsRover.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "GNSSPos"))
        self.lblGeneralSettings.setText(_translate("MainWindow", "General Settings"))
        self.lblWorkingDirectory.setText(_translate("MainWindow", "Working Directory:"))
        self.txtWorkingDirectory.setPlaceholderText(_translate("MainWindow", "press the button aside to choose the working directory..."))
        self.btnChooseDirectory.setText(_translate("MainWindow", "..."))
        self.lblDate.setText(_translate("MainWindow", "Selected Date:"))
        self.lblSelectedDate.setText(_translate("MainWindow", "dd/mm/yyyy"))
        self.lbl4DigitYYYY.setText(_translate("MainWindow", "4-digit year (YYYY):"))
        self.lblYYYY.setText(_translate("MainWindow", "YYYY"))
        self.lbl2DigitYY.setText(_translate("MainWindow", "2-digit year (YY):"))
        self.lblYY.setText(_translate("MainWindow", "YY"))
        self.lbl4DigitWWWW.setText(_translate("MainWindow", "4-digit GPS week (WWWW):"))
        self.lblWWWW.setText(_translate("MainWindow", "WWWW"))
        self.lbl3DigitDDD.setText(_translate("MainWindow", "3-digit day of year (DDD):"))
        self.lblDDD.setText(_translate("MainWindow", "DDD"))
        self.lbl1DigitD.setText(_translate("MainWindow", "1-digit day of week (D):"))
        self.lblD.setText(_translate("MainWindow", "D"))
        self.chkStartingTime.setText(_translate("MainWindow", "Starting Time:"))
        self.chkEndTime.setText(_translate("MainWindow", "End Time:"))
        self.chkTimeInterval.setText(_translate("MainWindow", "Time Interval:"))
        self.lblIGSDataProvider.setText(_translate("MainWindow", "IGS Data Provider:"))
        self.btnDownloadIGSData.setText(_translate("MainWindow", "Download Data"))
        self.lblRovers.setText(_translate("MainWindow", "Rovers"))
        self.btnSetupThresholds.setText(_translate("MainWindow", "Setup Thresholds"))
        self.btnSetupDistances.setText(_translate("MainWindow", "Setup Distances"))
        self.btnAddRover.setText(_translate("MainWindow", "Add Rover"))
        self.btnDeleteRover.setText(_translate("MainWindow", "Delete Selected Rover"))
        self.tabsRover.setTabText(self.tabsRover.indexOf(self.tab), _translate("MainWindow", "Tab 1"))
        self.tabsRover.setTabText(self.tabsRover.indexOf(self.tab_2), _translate("MainWindow", "Tab 2"))
        self.lblBaseStation.setText(_translate("MainWindow", "Base Station"))
        self.lblBaseStationOBS.setText(_translate("MainWindow", "OBS File:"))
        self.txtBaseStationOBS.setPlaceholderText(_translate("MainWindow", "press the button aside to choose an .OBS file..."))
        self.btnChooseBaseStationOBS.setText(_translate("MainWindow", "..."))
        self.btnRUN.setText(_translate("MainWindow", "RUN"))
        self.btnPlotPositions.setText(_translate("MainWindow", "PLOT SOLUTIONS"))
    ### --- END OF GENERATED CODE ---
    
# Form implementation generated from reading ui file 'RoverTab.ui'
#
# Created by: PyQt6 UI code generator 6.4.2
#
# WARNING: Any manual changes made to this file will be lost when pyuic6 is
# run again.  Do not edit this file unless you know what you are doing.
class Ui_RoverTab(QtWidgets.QWidget):
    # TODO: everytime you modify this .ui, remember to replace the inherited class (object -> QWidget).
    
    def setupUi(self, RoverTab):
        RoverTab.setObjectName("RoverTab")
        RoverTab.resize(404, 43)
        self.gridLayout = QtWidgets.QGridLayout(RoverTab)
        self.gridLayout.setObjectName("gridLayout")
        self.lblChooseRoverOBS = QtWidgets.QLabel(parent=RoverTab)
        self.lblChooseRoverOBS.setObjectName("lblChooseRoverOBS")
        self.gridLayout.addWidget(self.lblChooseRoverOBS, 0, 0, 1, 1)
        self.txtRoverOBSFile = QtWidgets.QLineEdit(parent=RoverTab)
        self.txtRoverOBSFile.setObjectName("txtRoverOBSFile")
        self.gridLayout.addWidget(self.txtRoverOBSFile, 0, 1, 1, 1)
        self.btnChooseRoverOBS = QtWidgets.QToolButton(parent=RoverTab)
        self.btnChooseRoverOBS.setObjectName("btnChooseRoverOBS")
        self.gridLayout.addWidget(self.btnChooseRoverOBS, 0, 2, 1, 1)

        self.retranslateUi(RoverTab)
        QtCore.QMetaObject.connectSlotsByName(RoverTab)

    def retranslateUi(self, RoverTab):
        _translate = QtCore.QCoreApplication.translate
        RoverTab.setWindowTitle(_translate("RoverTab", "Form"))
        self.lblChooseRoverOBS.setText(_translate("RoverTab", "OBS File:"))
        self.txtRoverOBSFile.setPlaceholderText(_translate("RoverTab", "press the button aside to choose an .OBS file..."))
        self.btnChooseRoverOBS.setText(_translate("RoverTab", "..."))
    # --- END OF GENERATED CODE ---
    
    def __init__(self, obsFile: str = None):
        """Initialize the RoverTab UI."""
        super().__init__()
        self.setupUi(self)
        
        # Set the default OBS file path if provided
        if obsFile is not None:
            self.txtRoverOBSFile.setText(obsFile)
        self.txtRoverOBSFile.setReadOnly(True)
        
        # Connect signals to slots (add event handlers)
        self.btnChooseRoverOBS.clicked.connect(self.chooseRoverOBSFile)
        
    def chooseRoverOBSFile(self):
        """Open a dialog to choose the rover observation file."""
        try:
            obsFile, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Select Rover OBS File")
            if obsFile:
                self.txtRoverOBSFile.setText(obsFile)
        except Exception as e:
            raise Exception(f"Error selecting rover .obs file: {e}")
        
class Ui_ThresholdsPopup(QtWidgets.QWidget):
    """
    This class is used to create a popup window for setting thresholds.
    It inherits from QWidget and sets up the UI elements in the constructor.
    """
    
    def __init__(self, controller, parentWidget):
        """Initialize the ThresholdPopup UI."""
        super().__init__()
        
        # dynamical creation of popup
        thresholds = controller.getThresholds()
        rovers = controller.getRovers()
        
        verticalLayout = QtWidgets.QVBoxLayout()
        
        for kRow, vRow in enumerate(rovers):
            for kCol, vCol in enumerate(rovers):
                if kRow < kCol:
                    # Creo layout orizzontale
                    horizontalLayout = QtWidgets.QHBoxLayout()
                    # Creo etichetta e casella di testo
                    label = QtWidgets.QLabel(f"{vRow.name} - {vCol.name}: ")
                    horizontalLayout.addWidget(label)
                    # Creo casella di testo per input numerico
                    textBox = QtWidgets.QDoubleSpinBox()
                    textBox.setObjectName(f"threshold_{vRow.name}_{vCol.name}")
                    textBox.setValue(float(thresholds.get((vRow, vCol), 0.00)))
                    textBox.valueChanged.connect(lambda value: parentWidget.setThreshold(vRow, vCol, value))
                    horizontalLayout.addWidget(textBox)
                    verticalLayout.addLayout(horizontalLayout)
        # ho anche le threshold su sdx, sdy, sdz
        for vSd in ['sdx', 'sdy', 'sdz']:
            # Creo layout orizzontale
            horizontalLayout = QtWidgets.QHBoxLayout()
            # Creo etichetta e casella di testo
            label = QtWidgets.QLabel(f"{vSd}: ")
            horizontalLayout.addWidget(label)
            # Creo casella di testo per input numerico
            textBox = QtWidgets.QDoubleSpinBox()
            textBox.setObjectName(f"threshold_{vSd}")
            textBox.setValue(float(thresholds.get((vSd, None), 0.00)))
            textBox.valueChanged.connect(lambda value: parentWidget.setThreshold(vSd, None, value))
            horizontalLayout.addWidget(textBox)
            verticalLayout.addLayout(horizontalLayout)
        # aggiungo un pulsante per chiudere il form
        # button = QtWidgets.QPushButton("Close")
        # button.clicked.connect(popupWidget.close)
        # verticalLayout.addWidget(button)
        # imposto il layout principale della finestra
        self.setLayout(verticalLayout)
        self.setWindowTitle("Thresholds (in meters)")
        
class Ui_DistancesPopup(QtWidgets.QWidget):
    """
    This class is used to create a popup window for setting distances between roversss.
    It inherits from QWidget and sets up the UI elements in the constructor.
    """
    def __init__(self, controller, parentWidget):
        """Initialize the ThresholdPopup UI."""
        super().__init__()
        
        # dynamical creation of popup
        distances = controller.getDistances()
        rovers = controller.getRovers()
        
        verticalLayout = QtWidgets.QVBoxLayout()
        
        for kRow, vRow in enumerate(rovers):
            for kCol, vCol in enumerate(rovers):
                if kRow < kCol:
                    # Creo layout orizzontale
                    horizontalLayout = QtWidgets.QHBoxLayout()
                    # Creo etichetta e casella di testo
                    label = QtWidgets.QLabel(f"{vRow.name} - {vCol.name}: ")
                    horizontalLayout.addWidget(label)
                    # Creo casella di testo per input numerico
                    textBox = QtWidgets.QDoubleSpinBox()
                    textBox.setObjectName(f"distance_{vRow.name}_{vCol.name}")
                    textBox.setValue(float(distances.get((vRow, vCol), 0.00)))
                    textBox.valueChanged.connect(lambda value: parentWidget.setDistance(vRow, vCol, value))
                    horizontalLayout.addWidget(textBox)
                    verticalLayout.addLayout(horizontalLayout)
        # aggiungo un pulsante per chiudere il form
        # button = QtWidgets.QPushButton("Close")
        # button.clicked.connect(popupWidget.close)
        # verticalLayout.addWidget(button)
        # imposto il layout principale della finestra
        self.setLayout(verticalLayout)
        self.setWindowTitle("Distances (in meters)")