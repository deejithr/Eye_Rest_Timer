import sys, os
import json
from PyQt5 import uic
from PyQt5.QtGui import *
from PyQt5.QtCore import QPoint, QTimer, Qt, QObject, QThread, pyqtSignal
from PyQt5.QtWidgets import *
from playsound import playsound

# Macros
TIMERSTATE_STOPPED = 0
TIMERSTATE_RUNNING = 1

DEFAULT_ON = "ON"

DEFAULT_DURATION = 20
DEFAULT_RESTPERIOD = 1
BLUE = "rgb(85, 170, 255)"
GREY = "rgb(191, 191, 191)"
LIGHT_ORANGE = "rgba(255, 242, 222,0)"
DARKER_ORANGE = "rgba(209, 160, 52,0)"
# Path where UI files are kept 
UI_Path = "ui//"
IMAGES_PATH = "ui//resources//images//"
SOUNDS_PATH = "C://Windows//Media//"

class worker(QObject):
    audiofile =""
    finished = pyqtSignal()

    def run(self):
        playsound(SOUNDS_PATH + self.audiofile)
        self.finished.emit()


class Ui_MainWindow_TimerApp(QDialog):

    def __init__(self):
        # Initializing the variables
        
        # Timer duration
        self.Timer_Duration = 0
        # Timer Rest Period
        self.Timer_RestPeriod = 0
        # Seconds Counter
        self.SecondsCounter = 0
        # Timer State
        self.TimerState = TIMERSTATE_STOPPED
        # Timer Settings 
        self.Settings ={}
        # SecondsTimer 
        self.SecondsTimer = QTimer()
        # Minimized Flag
        self.minimized = False


        super(Ui_MainWindow_TimerApp, self).__init__()

        # Connect the Timeout event of Seconds Timer to showProgressBar
        self.SecondsTimer.timeout.connect(self.showProgressBar)
        #Load the TimerApp Mainwindow UI
        uic.loadUi(UI_Path + "Timer_MainWindow.ui", self)
        # Remove the title bar from the window
        self.setWindowFlag(Qt.FramelessWindowHint)
        # Add function to close the application on pressing the X button
        self.pushButton_TimerMW_Close.clicked.connect(self.MainWindowClose)
        # Add function to minimize the application on pressing the - button
        self.pushButton_TimerMW_Minimize.clicked.connect(self.MainWindowMinimize)
        # Add function to update the timer values when 'Update' button is pressed
        self.pushButton_Update.clicked.connect(self.UpdateTimer)
        # Display start in the 'StartStop' pushbutton
        self.pushButton_StartStop_Timer.setText("START")
        self.label_RunningStatus.setText("STOPPED")
        # Add function to start or stop the timer values when 'Start/Stop' button is pressed
        self.pushButton_StartStop_Timer.clicked.connect(self.StartStopTimer)
        # Read the duration and rest period currently saved
        self.ReadSavedTimerValues()
        # Initialize the progress bar to 0
        self.progressBarUpdate(0)

        #Icon 
        self.icon = QIcon(IMAGES_PATH + "timer-icon2.png")

        # Tray
        self.tray = QSystemTrayIcon()
        self.tray.setIcon(self.icon)
        self.tray.setVisible(True)

        #Menu for Tray
        self.menu = QMenu()
        self.option1 = QAction("Show Timer")
        self.quit = QAction("Exit")
        self.quit.triggered.connect(self.MainWindowClose)
        self.option1.triggered.connect(self.showApp)
        self.menu.addAction(self.option1)
        self.menu.addAction(self.quit)
        self.tray.setContextMenu(self.menu)

        # For AutoRun Checkbox
        self.checkBox_AutostartTimer.stateChanged.connect(self.ASCheckboxPressed)
        if("ON" == self.AutoRunTimerStatus):
            self.checkBox_AutostartTimer.setChecked(True)
        else:
            self.checkBox_AutostartTimer.setChecked(False)



    # Function to update the timer values on clicking the 'Update' button
    def UpdateTimer(self):
        # Get the value of duration and Rest period
        Duration = int(self.spinBox_Duration.value())
        RestPeriod = int(self.spinBox_RestPeriod.value())

        # Update the timer duration and Rest Period
        self.Timer_Duration = Duration
        self.Timer_RestPeriod = RestPeriod

        if(TIMERSTATE_RUNNING == self.TimerState):
            self.stopTimer()
            self.startTimer((Duration * 60 * 1000))
        
        # Save the timer values in the TimerConfig file
        self.TimerConfigfile = open("TimerConfig.ini", "w+") 
        self.saveTimerData(Duration, RestPeriod, self.AutoRunTimerStatus)

    def ASCheckboxPressed(self):
        if(self.checkBox_AutostartTimer.isChecked()):
            self.AutoRunTimerStatus = "ON"
            self.StartStopTimer()
        else:
            self.AutoRunTimerStatus = "OFF"
        # Save the timer values in the TimerConfig file
        self.TimerConfigfile = open("TimerConfig.ini", "w+")
        self.saveTimerData(self.Timer_Duration, self.Timer_RestPeriod, self.AutoRunTimerStatus)

    

    # Function to read the Timer settings on startup
    def ReadSavedTimerValues(self):
        # If a configuration file already exsists
        if(os.path.exists("TimerConfig.ini")):
            self.TimerConfigfile = open("TimerConfig.ini", "r+")
            # String List to hold the Settings read
            Settings_string = []
            Settings_string = self.TimerConfigfile.readlines()
            if (0 != Settings_string.__len__()):
                self.Settings = json.loads(Settings_string[0])
    
                # Get the saved Timer Duaraion and Rest period
                self.Timer_Duration = self.Settings["Duration"]
                self.Timer_RestPeriod = self.Settings["Rest_Period"]
                self.AutoRunTimerStatus = self.Settings["AutoRun"]

                # Update the SpinBoxes to the read values
                self.spinBox_Duration.setValue(self.Timer_Duration) 
                self.spinBox_RestPeriod.setValue(self.Timer_RestPeriod)

        # If configuration file not present, create one
        else:
            self.TimerConfigfile = open("TimerConfig.ini", "w+")
            # Running for the first time, set with Default values
            self.spinBox_Duration.setValue(DEFAULT_DURATION) 
            self.spinBox_RestPeriod.setValue(DEFAULT_RESTPERIOD)

            # Update the timer duration and Rest Period
            self.Timer_Duration = DEFAULT_DURATION
            self.Timer_RestPeriod = DEFAULT_RESTPERIOD
            self.AutoRunTimerStatus = DEFAULT_ON
            # Save the timer values 
            self.saveTimerData(DEFAULT_DURATION, DEFAULT_RESTPERIOD, DEFAULT_ON)

            

    def saveTimerData(self, Duration, RestPeriod, OnOff):
         
        self.Settings["Duration"] = Duration
        self.Settings["Rest_Period"] = RestPeriod
        self.Settings["AutoRun"] = OnOff

        settings_JSON = json.dumps(self.Settings)
        # Bring the file pointer to the beginning of the file
        self.TimerConfigfile.seek(0)
        self.TimerConfigfile.write(settings_JSON)
        self.TimerConfigfile.close()

    
    
    def StartStopTimer(self):

        #Check the Timer State
        if (TIMERSTATE_STOPPED == self.TimerState):
            Timer_duration_in_msecs = self.Timer_Duration * 60 * 1000
            self.startTimer(Timer_duration_in_msecs)
            # Display STOP in the 'Start/Stop' push button
            self.pushButton_StartStop_Timer.setText("STOP")

        # Timer Running
        else:
            self.stopTimer()
            # Display START in the 'Start/Stop' push button
            self.pushButton_StartStop_Timer.setText("START")
            

    
    
    def stopTimer(self):
        # Stop the timer
        self.SecondsTimer.stop()
        self.SecondsCounter = 0
        self.TimerState = TIMERSTATE_STOPPED
        self.OuterCircleUpdate(GREY)
        self.label_RunningStatus.setText("STOPPED")

    
    
    def startTimer(self, Duration):
        # Start the Timer with the current value of Timer_Duration
        self.progressBarUpdate(0)
        self.SecondsTimer.start(1000)
        self.TimerState = TIMERSTATE_RUNNING
        self.OuterCircleUpdate(BLUE)
        self.label_RunningStatus.setText("RUNNING")


    def showPopUp(self):
        self.SecondsCounter = 0
        # Stop the SecondsTimer
        self.stopTimer()
        # Create PopUpUI object
        self.PopUp = PopUpUI()

    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        delta = QPoint (event.globalPos() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPos()


    def progressBarUpdate(self, value):
        stylesheet = """
        QFrame#frame_Circle1
        {
            background-color: qconicalgradient(cx:0.5, cy:0.5, angle:90, stop:{STOP_1} rgba(141, 65, 255, 0), stop:{STOP_2} rgba(170,         170, 255, 255));
           border-radius: 170px;
             
        }
        """
        progress = (100- value)/100.0

        STOP_1 = str(progress - 0.001)
        STOP_2 =str(progress)
        newStyleSheet = stylesheet.replace("{STOP_1}", STOP_1).replace("{STOP_2}", STOP_2)
        self.frame_Circle1.setStyleSheet(newStyleSheet)

    def OuterCircleUpdate(self,color):
        stylesheet = """
        QFrame#frame_Circle2
        {
            background-color:{COLOR};
            border-radius: 155px;
        }
        """
        newStyleSheet = stylesheet.replace("{COLOR}", color)
        self.frame_Circle2.setStyleSheet(newStyleSheet)

    def showProgressBar(self):
        self.SecondsCounter = self.SecondsCounter + 1
        if(False == self.minimized):
           CountDownTimerText = """
           <html><head/><body><p><span style=" font-size:26pt; color:#ffffff;">{Minutes}:</span><span style=" font-size:36pt;    color:#ffffff;">{Seconds}</span></p></body></html>
           """
           Seconds = ((self.Timer_Duration * 60) - self.SecondsCounter ) % 60
           Seconds = f"{Seconds:02}"
           Minutes = int(((self.Timer_Duration * 60) - self.SecondsCounter )/60)
           Minutes = f"{Minutes:02}"
           CountDownTimerText = CountDownTimerText.replace("{Minutes}", Minutes).replace("{Seconds}", Seconds)
           PercentageComp = ((self.SecondsCounter)/ (self.Timer_Duration * 60)) * 100
           self.label_CountDownTimer.setText(CountDownTimerText)
           self.progressBarUpdate(PercentageComp)

        if((self.Timer_Duration * 60) == self.SecondsCounter):
            # Timer expired
            self.showPopUp()


    # Function to close the application on clicking the X button
    def MainWindowClose(self):
        sys.exit()

    def MainWindowMinimize(self):
        self.hide()
        self.tray.showMessage("Timer", "Timer app minimized to tray", QSystemTrayIcon.Information, 1500)
        self.minimized = True

    def progressBarColorUpdate(self, color):
        stylesheet = """
        QFrame#frame_Circle1
        {
            background-color: qconicalgradient(cx:0.5, cy:0.5, angle:90, stop:{STOP_1} rgba(141, 65, 255, 0), stop:{STOP_2} {COLOR});
           border-radius: 170px;
             
        }
        """
        value = 99.99
        progress = (100- value)/100.0

        STOP_1 = str(progress - 0.001)
        STOP_2 =str(progress)
        newStyleSheet = stylesheet.replace("{STOP_1}", STOP_1).replace("{STOP_2}", STOP_2)
        newStyleSheet.replace("{COLOR}",color)

        TimerApp.frame_Circle1.setStyleSheet(newStyleSheet)

    def showApp(self):
        self.minimized = False
        self.show()

        
class PopUpUI(QDialog):
    def __init__(self):
        super(PopUpUI, self).__init__()
        #Load the PopUp Dialog UI
        uic.loadUi(UI_Path + "Timer_popupdialog.ui", self)
        #Get the current position of the window
        self.oldpos = self.pos()
        # The Restperiod seconds Timer
        self.RestPeriodSecondsTimer = QTimer()
        self.RestPeriodSecondsTimer.timeout.connect(self.RestPeriodSecondsTimerExpiry)


        # RestPeriod Seconds Counter
        self.RestPeriodSecondsCounter = 0

        # Flags
        self.snooze_1MinPressed = False
        self.snooze_5MinPressed = False
        self.RestPeriodCompleted = False

        # Set the Text for labelRest
        self.labelRest.setText("REST for " + str(TimerApp.Timer_RestPeriod) + " minute(s)")
        self.progressBar_Time.setValue(0)

        # Connect the functions to the pushbuttons
        self.pushButton_skip.clicked.connect(self.Skip)
        self.pushButton_1MinSnooze.clicked.connect(self.snooze_1Min)
        self.pushButton_5MinSnooze.clicked.connect(self.snooze_5Min)
        self.pushButton_TimerPopup_Close.clicked.connect(self.PopClose)
        self.RestPeriodSecondsTimer.start(1000)

        # Remove the title bar from the window
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.show()
        self.Playwav("Windows Unlock.wav")

    def Playwav(self, audio):
        self.worker = worker()
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        self.worker.audiofile = audio
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()
        

    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        delta = QPoint (event.globalPos() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPos()

    def snooze_1Min(self):
        # Reset the Seconds Period Counter
        self.RestPeriodSecondsCounter = 0
        # Set the flag for 1 minute snooze
        self.snooze_1MinPressed = True
        TimerApp.label_RunningStatus.setText("SNOOZED")
        TimerApp.progressBarColorUpdate(LIGHT_ORANGE)
        TimerApp.label_CountDownTimer.setText("1 min")
        # Hide the PopUp dialog box
        self.hide()

    def snooze_5Min(self):
        # Reset the Seconds Period Counter
        self.RestPeriodSecondsCounter = 0
        # Set the flag for 1 minute snooze
        self.snooze_5MinPressed = True
        TimerApp.label_RunningStatus.setText("SNOOZED")
        TimerApp.progressBarColorUpdate(DARKER_ORANGE)
        TimerApp.label_CountDownTimer.setText("5 min")
        # Hide the PopUp dialog box
        self.hide()

    def Skip(self):
        if (False == self.RestPeriodCompleted):
            # Reset the Seconds Period Counter
            self.RestPeriodSecondsCounter = 0
            self.progressBar_Time.setValue(0)
            TimerApp.startTimer(TimerApp.Timer_Duration)
        self.setParent(None)
        self.deleteLater()

    def RestPeriodSecondsTimerExpiry(self):
        self.RestPeriodSecondsCounter = self.RestPeriodSecondsCounter + 1 
        if (
             (True == self.snooze_1MinPressed) and
             (self.RestPeriodSecondsCounter == 60)
           ):
           # Reset the 1min Snooze button pressed flag and the seconds Counter
           self.snooze_1MinPressed = False
           self.RestPeriodSecondsCounter = 0
           self.progressBar_Time.setValue(0)
           self.Playwav("Windows Unlock.wav")
           self.show()
        elif (
             (True == self.snooze_5MinPressed) and
             (self.RestPeriodSecondsCounter == 300)
           ):
           # Reset the 1min Snooze button pressed flag and the seconds Counter
           self.snooze_5MinPressed = False
           self.RestPeriodSecondsCounter = 0
           self.progressBar_Time.setValue(0)
           self.Playwav("Windows Unlock.wav")
           self.show()
        else:
            if ( (False == self.snooze_1MinPressed) and
                 (False == self.snooze_5MinPressed)
            ):
               PercentValue = 0
               PercentValue = int((self.RestPeriodSecondsCounter/(TimerApp.Timer_RestPeriod * 60))*100)
               self.progressBar_Time.setValue(PercentValue)
               if (self.RestPeriodSecondsCounter == (TimerApp.Timer_RestPeriod * 60)):
                   self.labelRest.setText("Completed !!")
                   self.Playwav("Windows Proximity Connection.wav")
                   self.RestPeriodCompleted = True
                   self.RestPeriodSecondsTimer.stop()
                   self.RestPeriodSecondsCounter = 0
                   self.pushButton_skip.setEnabled(False)
                   self.pushButton_1MinSnooze.setEnabled(False)
                   self.pushButton_5MinSnooze.setEnabled(False)
                   TimerApp.startTimer(TimerApp.Timer_Duration)

    def PopClose(self):
        self.Skip()




if __name__ == "__main__":
    app = QApplication(sys.argv)
    TimerApp = Ui_MainWindow_TimerApp()
    TimerApp.oldPos = TimerApp.pos()
    TimerApp.showApp()
    sys.exit(app.exec())