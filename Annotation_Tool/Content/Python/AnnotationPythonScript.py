import unreal
# from pynput.keyboard import Key, Listener
# import keyboard
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

#gonna have to make the 'convert mouse position to world space' function myself:
#get the world location and rotation of the camera,
#find the forward vector of the camera,
#add to that vector a multiplied version of the mouse's 2d coordinates (fiddle with it) and add some relative z offset

#FIGURING OUT LOCATION DIFF
#find midpoint of viewport
#find position of mouse RELATIVE to midpoint (mouse pos - midpoint)

#FUNCTIONALITY BREAKDOWN
#   IN MOUSE MOVE EVENT:
#       get current mouse location as a variable
#       check if current mouse location is a certain distance away from previous mouse location
#       if true set current mouse location as old mouse location and create a spline point at the current mouse location

# ADD CALIBRATION!!

#ORDER OF OPERATIONS FOR TODAY:
# [DONE] make drawing and calibration window cover whole screen when opened
# [DONE] add calibration functionality (literally just changes the value of the public screenMidpoint variable and then closes the window)
# [DONE] make Esc or Enter close the drawing window
# [DONE] fix the issue with creating the spline blueprint attempting to overwrite the other one
#Implement spline point creation functionality

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

isDrawing = False

world = unreal.UnrealEditorSubsystem().get_editor_world()
mousePos = unreal.WidgetLayoutLibrary.get_mouse_position_on_viewport(world)
oldMousePos = mousePos

screenMidpoint = mousePos

def printScreenMidpoint():
    print(screenMidpoint)

def CreateSplineBlueprint():
    file_exists = unreal.Paths.directory_exists("/Game/SplineBlueprint")
    if file_exists == True:
        print("FILE DOES NOT EXIST!!!")
        package_path = "/Game"
        factory = unreal.BlueprintFactory()
        factory.set_editor_property("parent_class", unreal.Actor)
        #make the blueprint
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        SplineClass = unreal.Class
        blueprint = asset_tools.create_asset('SplineBlueprint', package_path, unreal.Blueprint, factory)
        #get the root data handle
        subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
        blueprint_handle = subsystem.k2_gather_subobject_data_for_blueprint(blueprint)[0]
        #get blueprint utility
        blueprint_library = unreal.SubobjectDataBlueprintFunctionLibrary()
        #choose component type
        component_type = 'SplineMesh'
        asset_editor_property_name = ''
        asset_path = ''
        #choose component type
        if 'Blueprint' == component_type:
            new_class = unreal.ChildActorComponent
            asset_editor_property_name = 'child_actor_class'
            asset_path = '/Game/Blueprints/BP_Character'
        elif 'StaticMesh' == component_type:
            new_class = unreal.StaticMeshComponent
            asset_editor_property_name = 'static_mesh'              
            asset_path = '/Game/Environments/SM_House'
        elif 'SkeletalMesh' == component_type:
            new_class = unreal.SkeletalMeshComponent
            asset_editor_property_name = 'skeletal_mesh'
            asset_path = '/Game/Characters/SK_Skeleton'
        elif 'SplineMesh' == component_type:
            new_class = unreal.SplineMeshComponent
            asset_editor_property_name = 'spline_mesh'
            asset_path = '/Engine/BasicShapes/Cube.Cube'

        #add sub component
        params = unreal.AddNewSubobjectParams(parent_handle=blueprint_handle, new_class=new_class, blueprint_context=blueprint)
        sub_handle, fail_reason = subsystem.add_new_subobject(params)
        if not fail_reason.is_empty():
            raise Exception("ERROR from sub_object_subsystem.add_new_subobject: {fail_reason}" )

        # attach
        subsystem.attach_subobject( blueprint_handle, sub_handle )

        new_class = unreal.SplineComponent
        asset_editor_property_name = 'spline'

        params = unreal.AddNewSubobjectParams(parent_handle=blueprint_handle, new_class=new_class, blueprint_context=blueprint)
        sub_handle, fail_reason = subsystem.add_new_subobject(params)
        if not fail_reason.is_empty():
            raise Exception("ERROR from sub_object_subsystem.add_new_subobject: {fail_reason}" )

        # attach
        subsystem.attach_subobject( blueprint_handle, sub_handle )
        # get object and component
        sub_data = blueprint_library.get_data(sub_handle)
        sub_component = blueprint_library.get_object(sub_data)

        # # set static mesh asset
        # asset = unreal.EditorAssetLibrary.load_asset(asset_path)
        # if asset is not None:
        #     sub_component.set_editor_property(asset_editor_property_name, asset)

        # set relative location
        # location, is_valid = unreal.StringLibrary.conv_string_to_vector('(X=-208.000000,Y=-1877.000000,Z=662.000000)')
        # sub_component.set_editor_property('RelativeLocation', location)
    else:
        pass

CreateSplineBlueprint()

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

        self.calibrateButton = QPushButton("Calibrate")
        self.calibrateButton.setMaximumWidth(200)
        self.calibrateButton.clicked.connect(self.calibrateButtonClicked)
 
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
        layout.addWidget(self.calibrateButton, 3, 2)
        layout.addWidget(self.drawButton, 4, 2)
 
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

    def calibrateButtonClicked(self):
        unreal.log("Started Calibrating")
        self.calibrateWindow = CalibrateWindow()
        self.calibrateWindow.show()

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
        global buttonColour
        buttonColour = colour
        selectedColour = self.sender().styleSheet()
        mainWindow = UnrealToolWindow()
        mainWindow.updateButtonColour(selectedColour)
   
class TransparentWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.transparent_window = QMainWindow()
        # self.transparent_window.setFixedSize(QSize(3000, 3000))
        # self.transparent_window.setMaximumSize(QSize(100, 100))
        self.setMinimumSize(QSize(2000, 2000))
        palette = QtGui.QPalette()
        palette.setColorGroup
        # palette.setColor(QtGui.QPalette.color, QColor("#01000000"))
        palette.setColor(QtGui.QPalette.ColorRole.Window, "#000000")
        self.setPalette(palette)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setWindowOpacity(0.1)
        # self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        
    
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            print("Hello you fool")
            isDrawing = True
            # player = unreal.PlayerController()
            global mousePos
            mousePos = unreal.WidgetLayoutLibrary.get_mouse_position_on_viewport(world)
            oldMousePos = mousePos
            relativeMouseCoords = mousePos - screenMidpoint
            print (f"MOUSE POS: {mousePos}")
            UES = unreal.UnrealEditorSubsystem()
            camLocation = unreal.UnrealEditorSubsystem.get_level_viewport_camera_info(UES)
            # print (camLocation)
            global cameraValues
            cameraValues = []
        
            for x in camLocation:
                # print(type(x))
                cameraValues.append(x)
        
            print(cameraValues[0])
            global vForward
            vForward = unreal.MathLibrary.get_forward_vector(cameraValues[1])
            vUp = unreal.MathLibrary.get_up_vector(cameraValues[1])
            vRight = unreal.MathLibrary.get_right_vector(cameraValues[1])
            global spawnLocation
            spawnLocation = cameraValues[0] + (vForward * 750)
            correctedLocation = (spawnLocation.x + (relativeMouseCoords.x * 0.5), spawnLocation.y + (relativeMouseCoords.y * 0.5), spawnLocation.z)
            # correctedLocation = (cameraValues[0].x + (vForward.x * 1000), cameraValues[0].y + (vUp.y * relativeMouseCoords.y), cameraValues[0].z + (vRight.z * relativeMouseCoords.x))
            print(f"SPAWN LOCATION: {spawnLocation}")
            # mouseInfo = unreal.PlayerController.deproject_screen_position_to_world(player, mousePos.x, mousePos.y)
            # print (mouseInfo)
            # hud = unreal.HUD()
            # mouseInfo = unreal.HUD.deproject(hud, mousePos.x, mousePos.y)
            # print (mouseInfo)
            # world = unreal.Viewport.get_viewport_world(self)
            forward = unreal.Vector.FORWARD
            print(forward)
            # actorClass = unreal.StaticMeshActor
            # componentClass = unreal.StaticMeshComponent
            # location = unreal.Vector(0, 0, 200)
            # staticMeshActor = EAS.spawn_actor_from_class(actorClass, spawnLocation)
            # staticMesh = unreal.EditorAssetLibrary.load_asset('/Engine/BasicShapes/Cube.Cube')
            # staticMeshActor.set_actor_rotation(cameraValues[1], False)
            # staticMeshActor.add_actor_local_offset((0, relativeMouseCoords.x, -relativeMouseCoords.y), False, False)
        
            # staticMeshActor.get_component_by_class(componentClass).set_static_mesh(staticMesh)

            # actorClass = unreal.SplineMeshActor
            # Drawing = EAS.spawn_actor_from_class(actorClass, spawnLocation)
            # Drawing.set_actor_rotation(cameraValues[1], False)
            # Drawing.add_actor_local_offset((0, relativeMouseCoords.x, -relativeMouseCoords.y), False, False)
            # staticMesh = unreal.EditorAssetLibrary.load_asset('/Engine/BasicShapes/Cube.Cube')
            # Drawing.get_component_by_class(componentClass).set_static_mesh(staticMesh)

            actorClass = unreal.EditorAssetLibrary.load_blueprint_class('/Game/SplineBlueprint')
            componentClass = unreal.SplineMeshComponent
            staticMesh = unreal.EditorAssetLibrary.load_asset('/Engine/BasicShapes/Cube.Cube')
            global Drawing
            Drawing = EAS.spawn_actor_from_class(actorClass, spawnLocation)
            Drawing.set_actor_rotation(cameraValues[1], False)
            Drawing.add_actor_local_offset((0, relativeMouseCoords.x, -relativeMouseCoords.y), False, False)
            unreal.SubobjectDataSubsystem(Drawing).create_new_bp_component(componentClass, '/All/Game', 'SplineMesh')

            coordSpace = unreal.SplineCoordinateSpace
            Drawing.get_component_by_class(componentClass).set_static_mesh(staticMesh)
            Drawing.get_component_by_class(unreal.SplineComponent).clear_spline_points(update_spline = True)
            Drawing.get_component_by_class(unreal.SplineComponent).add_spline_point((0, 0, 0), coordSpace.LOCAL, update_spline = True)
            global splinePoint
            global splineIndex
            splineIndex = 0
            splinePoint = Drawing.get_component_by_class(unreal.SplineComponent).get_spline_point_at(splineIndex, coordSpace.LOCAL)

    def mouseReleaseEvent(self, event):
        isDrawing = False
        
    def mouseMoveEvent(self, event):
        global world
        global mousePos
        currentMousePos = unreal.WidgetLayoutLibrary.get_mouse_position_on_viewport(world)
        relativeMouseCoords = currentMousePos - screenMidpoint
        # correctedLocation = (spawnLocation.x, spawnLocation.y + relativeMouseCoords.x, spawnLocation.z - relativeMouseCoords.y)
        correctedLocation = (0, relativeMouseCoords.x, -relativeMouseCoords.y)
        posDiff = currentMousePos - mousePos
        if abs(posDiff.x) >=20 or abs(posDiff.y) >= 20:
            print("PLACE SPLINE POINT NOW!")
            global splineIndex
            coordSpace = unreal.SplineCoordinateSpace
            splineComp = Drawing.get_component_by_class(unreal.SplineComponent)
            oldPointData = unreal.SplineComponent.get_local_location_and_tangent_at_spline_point(splineComp, splineIndex-1)
            global splinePoint
            global previousSplinePoint
            print (splineIndex)
            # splinePoint = Drawing.get_component_by_class(unreal.SplineComponent).get_spline_point_at(splineIndex, coordSpace.LOCAL)
            newPointData = unreal.SplineComponent.get_local_location_and_tangent_at_spline_point(splineComp, splineIndex)
            Drawing.get_component_by_class(unreal.SplineComponent).add_spline_point(correctedLocation, unreal.SplineCoordinateSpace.LOCAL, update_spline = True)
            mousePos = currentMousePos
            staticMesh = unreal.EditorAssetLibrary.load_asset('/Engine/BasicShapes/Cube.Cube')
            Drawing.get_component_by_class(unreal.SplineMeshComponent).set_static_mesh(staticMesh)
            MeshComponents = Drawing.get_components_by_class(unreal.SplineMeshComponent)
            meshCompLength = MeshComponents.__len__()
            CurrentMesh = MeshComponents[meshCompLength - 1]
            CurrentMesh.set_start_and_end(oldPointData[0], oldPointData[1], newPointData[0], newPointData[1], update_mesh=True)
            CurrentMesh.set_static_mesh(staticMesh)
            unreal.SubobjectDataSubsystem(Drawing).create_new_bp_component(unreal.SplineMeshComponent, '/All/Game', 'SplineMesh')
            splineIndex = splineIndex + 1
            # previousSplinePoint = splinePoint
            print(meshCompLength)


    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.destroy()
 
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

class CalibrateWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.calibrate_window = QMainWindow()
        self.setMinimumSize(QSize(2000, 2000))
        palette = QtGui.QPalette()
        palette.setColorGroup
        # palette.setColor(QtGui.QPalette.color, QColor("#01000000"))
        palette.setColor(QtGui.QPalette.ColorRole.Window, "#000000")
        self.setPalette(palette)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setWindowOpacity(0.1)
        # self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            world = unreal.UnrealEditorSubsystem().get_editor_world()
            global screenMidpoint
            screenMidpoint = unreal.WidgetLayoutLibrary.get_mouse_position_on_viewport(world)
            printScreenMidpoint()
            self.destroy()
    
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.destroy()
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
    vForward = unreal.MathLibrary.get_forward_vector(cameraValues[1])
    spawnLocation = cameraValues[0] + (vForward * 1000)
    print(f"SPAWN LOCATION: {spawnLocation}")
    # unreal.log(camLocation)
 
    mouse = unreal.MouseInputDeviceState()
    RMB = mouse.right.__getattribute__("down")
    print(RMB)
 
    actorClass = unreal.StaticMeshActor
    componentClass = unreal.StaticMeshComponent
    location = unreal.Vector(0, 0, 200)
    staticMeshActor = EAS.spawn_actor_from_class(actorClass, spawnLocation)
    staticMesh = unreal.EditorAssetLibrary.load_asset('/Engine/BasicShapes/Cube.Cube')
 
    staticMeshActor.get_component_by_class(componentClass).set_static_mesh(staticMesh)
    # SystemLibrary.line_trace_single(start=camLocation, end=)

    DelBase = unreal.KeyEvent
    print (DelBase)