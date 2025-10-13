import unreal
from pynput.keyboard import Key, Listener
import keyboard
from collections import deque
from collections.abc import Iterable
import sys
from PySide6 import QtCore, QtGui
from unreal import SystemLibrary
from functools import partial
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QMainWindow, QSlider, QVBoxLayout, QLabel, QCheckBox, QComboBox, QGridLayout, QBoxLayout, QGridLayout, QDialog
import time
 
 
#TO DO:
#make colour selection menu (returning to this later)
#make a "start drawing" button on the UI that opens a transparent window that covers the whole screen. this way it can detect key inputs AND stop me moving about the camera using the mouse. Esc to close it
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
 
selectedColour = "background-color : green"

toolRunning = True
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
 
 
 
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
        currentColour = selectedColour
 
 
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
        self.colourPickerButton.setStyleSheet("background-color : cyan")
 
        self.colourPickerLabel = QLabel("Line Colour:")
 
        self.colourPickerButton.clicked.connect(self.colourPickerButtonClicked)

        self.drawButton = QPushButton("Start Drawing")
        self.drawButton.setMaximumWidth(200)
        self.drawButton.clicked.connect(self.drawButtonClicked)
 
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
        layout.addWidget(self.drawButton, 3, 2)
 
        container = QWidget()
        container.setLayout(layout)
 
        #self.main_window.setCentralWidget(container)
        self.main_window.setMenuWidget(container)
        self.dropDown.addItem("Screen Space")
        self.dropDown.addItem("Surface Snapping")
 
    def updateButtonColour(self, selectedColour):
        self.colourPickerButton.setStyleSheet("background-color : red")
        unreal.log(selectedColour)
       
 
    def sliderChanged(self,value):
        unreal.log("Slider was moved to: " + str(value))
        self.sliderLabel.setText(str(value))
   
    def colourPickerButtonClicked(self):
        unreal.log("BUTTON CLICKED")
        self.colourWindow = ColourWindow()
        self.colourWindow.show()
        # selectedColour = ("background-color : green")
        self.colourPickerButton.setStyleSheet(f"{selectedColour}")
        fish = self.colourPickerButton.styleSheet()
        print (fish)

    def drawButtonClicked(self):
        unreal.log("Started Drawing")
        self.transparentWindow = TransparentWindow()
        self.transparentWindow.show()

    # def keyPressEvent(self, event):
    #     print(event.key())
    #     # if event.key() == Qt.Key_Space:
    #     #     print("Hello")
   
class ColourWindow(QWidget):
    def __init__(self, parent = UnrealToolWindow):
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
       
    def ColourButtonClicked(self):
        colour = self.sender().styleSheet()
        buttonColour = colour
        selectedColour = self.sender().styleSheet()
        mainWindow = UnrealToolWindow()
        mainWindow.updateButtonColour(selectedColour)
   
class TransparentWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.transparent_window = QMainWindow()
        self.transparent_window.setFixedSize(QSize(3000, 3000))
        self.transparent_window.setMinimumSize(QSize(3000, 3000))
        palette = QtGui.QPalette()
        palette.setColorGroup
        # palette.setColor(QtGui.QPalette.color, QColor("#01000000"))
        palette.setColor(QtGui.QPalette.ColorRole.Window, "#000000")
        self.setPalette(palette)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setWindowOpacity(0.01)
        # self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        
    
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            print("Hello you fool")
 
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
 
class SplineActor():
    EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    # viewport = unreal.Viewport()
    # camLocation = unreal.Viewport.get_view_rotation(viewport)
    # camLocation = unreal.EditorLevelLibrary.get_level_viewport_camera_info()
    UES = unreal.UnrealEditorSubsystem()
    camLocation = unreal.UnrealEditorSubsystem.get_level_viewport_camera_info(UES)
    # print (camLocation)
    cameraValues = []
   
    for x in camLocation:
        # print(type(x))
        cameraValues.append(x)
 
    print(cameraValues[0])
    # unreal.log(camLocation)
 
    mouse = unreal.MouseInputDeviceState()
    RMB = mouse.right.__getattribute__("down")
    print(RMB)
 
    actorClass = unreal.StaticMeshActor
    componentClass = unreal.StaticMeshComponent
    location = unreal.Vector(0, 0, 200)
    staticMeshActor = EAS.spawn_actor_from_class(actorClass, cameraValues[0])
    staticMesh = unreal.EditorAssetLibrary.load_asset('/Engine/BasicShapes/Cube.Cube')
 
    staticMeshActor.get_component_by_class(componentClass).set_static_mesh(staticMesh)
    # SystemLibrary.line_trace_single(start=camLocation, end=)

    DelBase = unreal.KeyEvent
    print (DelBase)



# class PyTick():

#     _delegate_handle = None
#     _current = None
#     schedule = None

#     def __init__(self):
#         self.schedule = deque()
#         self._delegate_handle = unreal.register_slate_post_tick_callback(self._callback)

#     def _callback(self, _):
#         if self._current is None:
#             if self.schedule:
#                 self._current = self.schedule.popleft()

#             else:
#                 print ('Done Jobs')
#                 unreal.unregister_slate_post_tick_callback(self._delegate_handle)
#                 return
            
#         try:
#             task = next(self._current)

#             if task is not None and isinstance(task, Iterable):

#                 self.schedule.appendleft(self._current)
#                 self._current = task

#         except StopIteration:
#             self._current = None

#         except:
#             self._current = None
#             raise
    
# def my_loop():
#     for i in range(10):
#         print('Tick A %s'% i)
#         yield my_inner_loop()

# def my_inner_loop():
#     for i in range(2):
#         print ('Tick B %s'% i)
#         yield

# def checkInput():
#     # if SplineActor.RMB == True:
#     #     print("HELLO")
#     #     yield checkInput()
#     if keyboard.is_pressed('q'):
#         print("HELLO")
#         actorClass = unreal.StaticMeshActor
#         componentClass = unreal.StaticMeshComponent
#         location = unreal.Vector(0, 0, 0)
#         staticMeshActor = EAS.spawn_actor_from_class(actorClass, location)
#         staticMesh = unreal.EditorAssetLibrary.load_asset('/Engine/BasicShapes/Cube.Cube')

#         staticMeshActor.get_component_by_class(componentClass).set_static_mesh(staticMesh)
#         py_tick.schedule.append(checkInput())
#     else:
#         return

# py_tick = PyTick()
# py_tick.schedule.append(checkInput())


###############################################

# keyInfo = unreal.KeyboardInputDeviceState()
# print (keyInfo)

# def on_press(key):
#     print('{0} pressed'.format(key))

# def on_release(key):
#     print('{0} released'.format(key))
#     if key == Key.esc:
#         return False
    
# with Listener(
#     on_press=on_press,
#     on_release=on_release) as listener: listener.join()
# while True:
#     print ("hello")
#     break
#     try:
#         if keyboard.is_pressed('q'):
#             print("HELLO")
#             # actorClass = unreal.StaticMeshActor
#             # componentClass = unreal.StaticMeshComponent
#             # location = unreal.Vector(0, 0, 0)
#             # staticMeshActor = EAS.spawn_actor_from_class(actorClass, location)
#             # staticMesh = unreal.EditorAssetLibrary.load_asset('/Engine/BasicShapes/Cube.Cube')
        
#             # staticMeshActor.get_component_by_class(componentClass).set_static_mesh(staticMesh)
#     except:
#         break



