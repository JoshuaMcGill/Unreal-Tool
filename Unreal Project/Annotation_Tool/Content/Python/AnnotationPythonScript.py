import unreal
import sys
from functools import partial
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QMainWindow, QSlider,QVBoxLayout, QLabel, QCheckBox, QComboBox, QGridLayout, QBoxLayout, QGridLayout, QDialog


#TO DO:
#make colour selection menu
#make the tool (good luck)
coloursArray = (
        "black",
        "grey",
        "white",
        "red",
        "orange",
        "yellow",
        "green",
        "blue",
        "cyan",
        "magenta"

)

class ColourWindow(QWidget):
    def __init__(self):
        super().__init__()
        colourLayout = QGridLayout()

        gridX = 0
        gridY = 0

        self.setLayout(colourLayout)
        self.colour_window = QMainWindow()
        #self.colour_window.setParent(self)
        self.colour_window.setFixedSize(QSize(100, 100))
        #ColourWindow.window = ColourWindow()
        #ColourWindow.window.setObjectName("colourWindow")
        #ColourWindow.window.setWindowTitle("Colour Picker")
        self.setLayout(colourLayout)
        for x in (coloursArray):
            self.colourButton = QPushButton()
            self.colourButton.setStyleSheet(f"background-color : {x}")
            self.colourButton.setMaximumWidth(25)
            colourLayout.addWidget(self.colourButton, gridX, gridY)
            gridY = gridY + 1
            if gridY > 4:
                gridX = gridX + 1
                gridY = 0
            self.colourButton.clicked.connect(self.ColourButtonClicked)
        
    def ColourButtonClicked():
        pass
            


class UnrealToolWindow(QWidget):
    def __init__ (self, parent = None):
       
        # Run the Init of Qwidget <--- Parent
        super(UnrealToolWindow, self).__init__(parent)
 
        # Setting up the properties of my UnrealToolWindow
        self.main_window = QMainWindow()
        self.main_window.setParent(self)
        self.main_window.setFixedSize(QSize(400,300))
        # Create a Click Event that when the button is clicked it will call the function
        # ButtonClicked()
        currentColour = ("cyan")

 
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(50)
        self.slider.setSliderPosition(5)
        self.slider.valueChanged.connect(self.sliderChanged)
 
        self.sliderLabel = QLabel()
        self.sliderLabel.setText("5")
        #self.sliderLabel.setAlignment(Qt.AlignJustify)

        self.sliderName = QLabel("Line Width:")

        self.modeLabel = QLabel("Mode:")
 
        self.dropDown = QComboBox()

        self.colourPickerButton = QPushButton()
        self.colourPickerButton.setMaximumWidth(30)
        self.colourPickerButton.setStyleSheet("background-color :" "cyan")

        self.colourPickerLabel = QLabel("Line Colour:")

        self.colourPickerButton.clicked.connect(self.colourPickerButtonClicked)
 
        ##################################
 
        #layout = QBoxLayout(QBoxLayout.Direction.TopToBottom)
        layout = QGridLayout()
        layout.setColumnMinimumWidth(1, 15)
        layout.addWidget(self.modeLabel, 0, 0)
        layout.addWidget(self.dropDown, 0, 2)
        layout.addWidget(self.sliderName, 1, 0)
        layout.addWidget(self.sliderLabel, 1, 1)
        layout.addWidget(self.slider, 1, 2)
        layout.addWidget(self.colourPickerLabel, 2, 0)
        layout.addWidget(self.colourPickerButton, 2, 2)
 
        container = QWidget()
        container.setLayout(layout)
 
        #self.main_window.setCentralWidget(container)
        self.main_window.setMenuWidget(container)
        self.dropDown.addItem("Screen Space")
        self.dropDown.addItem("Surface Snapping")
 
    def sliderChanged(self,value):
        unreal.log("Slider was moved to: " + str(value))
        self.sliderLabel.setText(str(value))
    
    def colourPickerButtonClicked(self, currentColour):
        unreal.log("BUTTON CLICKED")
        self.colourWindow = ColourWindow()
        self.colourWindow.show()
    
 
 
def launchWindow():
    if QApplication.instance():
        for win in (QApplication.allWindows()):
            if 'toolWindow' in win.objectName():
                win.destroy()
    else:
        app = QApplication(sys.argv)
 
    UnrealToolWindow.window = UnrealToolWindow()
    UnrealToolWindow.window.setObjectName("toolWindow")
    UnrealToolWindow.window.setWindowTitle("Annotation Tool")
    UnrealToolWindow.window.show()
    unreal.parent_external_window_to_slate(UnrealToolWindow.window.winId())

launchWindow()
