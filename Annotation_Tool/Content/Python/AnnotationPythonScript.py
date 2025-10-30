import unreal
import sys
from PySide6 import QtCore, QtGui
from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import QApplication, QWidget, QPushButton, QMainWindow, QSlider, QVBoxLayout, QLabel, QCheckBox, QComboBox, QGridLayout, QBoxLayout, QGridLayout, QDialog, QColorDialog
import pyautogui


#Global Variables

selectedColour = "background-color : #ff0000"
currentR, currentG, currentB, currentA = (1.0, 1.0, 1.0, 0.0)
EAS = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world = unreal.UnrealEditorSubsystem().get_editor_world()
mousePos = unreal.WidgetLayoutLibrary.get_mouse_position_on_viewport(world)
screenRes = pyautogui.size()
screenMidpoint = (screenRes[0]/2, screenRes[1]/2)
sliderValue = 0.2
BFL = unreal.SubobjectDataBlueprintFunctionLibrary
SDS = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
MIIndex = 0

class InitialiseTool():
    def __init__(self):
        self.name = "AnnotationTool"

    def CreatePath(): # Creates a folder in the content browser in which all the materials etc. for this tool are stored
        
        # If the folder doesn't exist, make one.
        if not unreal.EditorAssetLibrary.does_asset_exist("/Game/AnnotationTool"):
            print("path created")
            unreal.EditorAssetLibrary.make_directory("AnnotationTool")


    def CreateSplineBlueprint(): # Creates the spline blueprint that's used for the drawing. Basically just an actor with a spline component.

        if not unreal.EditorAssetLibrary.does_asset_exist("/Game//AnnotationTool/SplineBlueprint.SplineBlueprint"): # Checking if blueprint already exists
            package_path = "/Game/AnnotationTool"
            factory = unreal.BlueprintFactory()
            factory.set_editor_property("parent_class", unreal.Actor)
            #make the blueprint
            asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
            SplineClass = unreal.Class
            global blueprint
            blueprint = asset_tools.create_asset('SplineBlueprint', package_path, unreal.Blueprint, factory)
            #get the root data handle
            subsystem = unreal.get_engine_subsystem(unreal.SubobjectDataSubsystem)
            blueprint_handle = subsystem.k2_gather_subobject_data_for_blueprint(blueprint)[0]

            new_class = unreal.SplineComponent
    
            params = unreal.AddNewSubobjectParams(parent_handle=blueprint_handle, new_class=new_class, blueprint_context=blueprint)
            sub_handle, fail_reason = subsystem.add_new_subobject(params)
            if not fail_reason.is_empty():
                raise Exception("ERROR from sub_object_subsystem.add_new_subobject: {fail_reason}" )
    
            # attach
            subsystem.attach_subobject( blueprint_handle, sub_handle )
            # get object and component
    
        else:
            pass
    
    def CreateMaterial(): # Creates the base material, of which instances are made so the colour can be changed for each stroke.
        assetTools = unreal.AssetToolsHelpers.get_asset_tools()
        editorAssetLibrary = unreal.EditorAssetLibrary

        # If the material doesn't exist, make it in the file path defined earlier.
        if not editorAssetLibrary.does_asset_exist("/Game/AnnotationTool/M_Spline.M_Spline"):
            assetTools.create_asset("M_Spline", "/Game/AnnotationTool", unreal.Material, unreal.MaterialFactoryNew())
            mat = unreal.load_asset("/Game/AnnotationTool/M_Spline.M_Spline")
            
            # Create a vector parameter node and attach it to the material output
            parameter = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionVectorParameter, -300, 0)
            unreal.MaterialEditingLibrary.connect_material_property(from_expression=parameter, from_output_name="", property_=unreal.MaterialProperty.MP_BASE_COLOR)
            unreal.MaterialEditingLibrary.recompile_material(mat)
    
        else:
            pass
        mat = unreal.load_asset("/Game/AnnotationTool/M_Spline.M_Spline")
    
    def CreateMaterialInstance(): # Creates a material instance of the material I just defined.
    
        global meshMatInstance
        global MIIndex
        # Load the material
        meshMat = unreal.load_asset("/Game/AnnotationTool/M_Spline.M_Spline")
        assetTools = unreal.AssetToolsHelpers.get_asset_tools()
        MaterialEditingLibrary = unreal.MaterialEditingLibrary
        editorAssetLibrary = unreal.EditorAssetLibrary

        # If a material instance of the current index does not exist, make it.
        if not editorAssetLibrary.does_asset_exist(f"/Game/AnnotationTool/MaterialInstance_{MIIndex}.MaterialInstance_{MIIndex}"):
            meshMatInstance = assetTools.create_asset(f"MaterialInstance_{MIIndex}", "/Game/AnnotationTool", unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
            MaterialEditingLibrary.set_material_instance_parent( meshMatInstance, meshMat)  # set parent material

            # Set the vector parameter value to the currently selected colour
            unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(meshMatInstance, 'Param', unreal.LinearColor(r=currentR, g=currentG, b=currentB, a=1.0))
            unreal.MaterialEditingLibrary.update_material_instance(meshMatInstance)
            unreal.EditorAssetLibrary.save_loaded_asset(meshMatInstance)
            MIIndex = MIIndex + 1
        else:
            MIIndex = MIIndex + 1
        global instance

        # Set the current material instance
        instance = editorAssetLibrary.load_asset(f"/Game/AnnotationTool/MaterialInstance_{MIIndex - 1}.MaterialInstance_{MIIndex - 1}")
    
    # Update the colour of the material instance
    def UpdateInstanceColour():
        unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(instance, 'Param', unreal.LinearColor(r=currentR, g=currentG, b=currentB, a=1.0))
        unreal.MaterialEditingLibrary.update_material_instance(instance)
        unreal.EditorAssetLibrary.save_loaded_asset(instance)

    #Launch the window, and if the window already exists destroy the previous one.
    def launchWindow():
        if QApplication.instance():
            for win in (QApplication.allWindows()):
                if 'toolWindow' in win.objectName():
                    win.destroy()

        #set the name and visibility of the created window
        UnrealToolWindow.window = UnrealToolWindow()
        UnrealToolWindow.window.setObjectName("toolWindow")
        UnrealToolWindow.window.setWindowTitle("Annotation Tool")
        UnrealToolWindow.window.show()
        unreal.parent_external_window_to_slate(UnrealToolWindow.window.winId())
 
class UnrealToolWindow(QWidget): # Class containing all the info about the main tool UI
    def __init__ (self, parent = None):
        # Run the Init of Qwidget <--- Parent
        super(UnrealToolWindow, self).__init__(parent)

        #Set the UI to be in dark mode, and change the font
        self.setStyleSheet("""
            background-color: #303030;
            color: #ffffff;
            font-family: Ariel;
            font-size: 12px;
            selection-background-color: #424242;                  
        """)  
 
        # Setting up the properties of my UnrealToolWindow
        self.main_window = QMainWindow()
        self.main_window.setParent(self)
        self.main_window.setFixedSize(QSize(400,300)) # Set window size

        # Creating all the widgets that populate the UI, and altering their properties
        self.slider = QSlider(Qt.Horizontal) # Drawing size slider
        self.slider.setMinimum(1)
        self.slider.setMaximum(50)
        self.slider.setSliderPosition(2)
        self.slider.valueChanged.connect(self.sliderChanged)

        self.sliderLabel = QLabel() # Label and value for the slider
        self.sliderLabel.setText("2")
        self.sliderName = QLabel("Line Width:")


        self.colourPickerButton = QPushButton() # Button that opens up colour selection window
        self.colourPickerButton.setMaximumWidth(30)
        self.colourPickerButton.setStyleSheet("background-color: #ffffff")

        self.colourPickerLabel = QLabel("Line Colour:") # Name for button

        self.colourPickerButton.clicked.connect(self.colourPickerButtonClicked) # Connects this button to a function defined later
 
        self.drawButton = QPushButton("Start Drawing") # Button that activates drawing
        self.drawButton.setMaximumWidth(200)
        self.drawButton.clicked.connect(self.drawButtonClicked)
 
        self.clearButton = QPushButton("Clear All") # Button that clears all drawings in the level, and deletes all associated material instances
        self.clearButton.setMaximumWidth(200)
        self.clearButton.clicked.connect(self.clearButtonClicked)

        ##################################

        # Add all the widgets to the UI, including their position coordinates on the grid layout (x, y)
        layout = QGridLayout()
        layout.setColumnMinimumWidth(1, 15) # Sets width of column 1
        layout.addWidget(self.sliderName, 1, 0)
        layout.addWidget(self.sliderLabel, 1, 1)
        layout.addWidget(self.slider, 1, 2)
        layout.addWidget(self.colourPickerLabel, 2, 0)
        layout.addWidget(self.colourPickerButton, 2, 2)
        layout.addWidget(self.drawButton, 3, 2)
        layout.addWidget(self.clearButton, 4, 2)
        container = QWidget()
        container.setLayout(layout)
        self.main_window.setMenuWidget(container) # Sets layout of window

    def sliderChanged(self,value): # Function for when the slider value is changed
        unreal.log("Slider was moved to: " + str(value))
        self.sliderLabel.setText(str(value))
        global sliderValue
        sliderValue = value / 10

    def colourPickerButtonClicked(self): # Function for when a new colour is selected from the colour dialog window

        color = QColorDialog.getColor("#ffffff", self, "Select a Color")
 
        if color.isValid():
            # Apply Chosen Colour
            css = f"background-color: {color.name()}; font-weight: bold; font-size: 14px;"
            self.colourPickerButton.setStyleSheet(css)
        global colourHex
        colourHex = color.name()
        global currentR, currentG, currentB, currentA
        currentR, currentG, currentB, currentA = (color.red() / 255, color.green() / 255, color.blue() / 255, color.alpha) # Values used in the material instance
        InitialiseTool.UpdateInstanceColour() # Calls the Update material instance colour function
 
 
    def drawButtonClicked(self): # Creates a transparent window that covers the screen and receives user input
        unreal.log("Started Drawing")
        self.transparentWindow = TransparentWindow()
        self.transparentWindow.show()
        TransparentWindow.window = TransparentWindow()
        TransparentWindow.window.setObjectName("DrawWindow")
        editorAssetLibrary = unreal.EditorAssetLibrary
        # Creates a material instance if one does not exist
        if not editorAssetLibrary.does_asset_exist(f"/Game/AnnotationTool/MaterialInstance_{MIIndex}.MaterialInstance_{MIIndex}"):
            InitialiseTool.CreateMaterialInstance()
 
    def clearButtonClicked(self): # Deletes all spline actors, spline mesh actors, and groups they were contained in
        editorAssetLibrary = unreal.EditorAssetLibrary
        actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.SplineMeshActor) # Gets the spline mesh actors
        for actor in actors:
            actor.destroy_actor()
        actorClass = unreal.EditorAssetLibrary.load_blueprint_class('/Game/AnnotationTool/SplineBlueprint')
        actors = unreal.GameplayStatics.get_all_actors_of_class(world, actorClass) # Gets the spline blueprint actors
        for actor in actors:
            actor.destroy_actor()
        for x in range(MIIndex):
            if editorAssetLibrary.does_asset_exist(f"/Game/AnnotationTool/MaterialInstance_{x}.MaterialInstance_{x}"):
                print("MATERIAL INSTANCE EXISTS!!")
                material = (f"/Game/AnnotationTool/MaterialInstance_{x}.MaterialInstance_{x}")
                unreal.EditorAssetLibrary.delete_asset(material)
        actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.GroupActor)
        for actor in actors:
            label = actor.get_actor_label()
            if label == "SplineGroup": # Checks if the name of the group is SplineGroup, if so deletes it
                actor.destroy_actor()

    def ChangeButtonColour(self, colour):
        self.colourPickerButton.setStyleSheet(f"background-color: {colour}; border: none")
        print(f"NEW BUTTON COLOUR IS: {colour}")

class ColourWindow(QWidget):
    def __init__(self, parent = UnrealToolWindow):
        super().__init__()
        colourLayout = QVBoxLayout()
 
        self.setLayout(colourLayout)
        self.colourWidget = QColorDialog()
        colourLayout.addWidget(self.colourWidget)
        self.colourWidget.colorSelected.connect(self.ColourSelected)
 
    def ColourSelected(self):
        selectedColour = self.sender().currentColor()
        global colourHex
        colourHex = selectedColour.name()
        global currentR, currentG, currentB, currentA
        currentR, currentG, currentB, currentA = (selectedColour.red() / 255, selectedColour.green() / 255, selectedColour.blue() / 255, selectedColour.alpha)
        InitialiseTool.UpdateInstanceColour()
        self.destroy()

class TransparentWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.transparent_window = QMainWindow()
        self.setMinimumSize(QSize(3000, 3000))
        palette = QtGui.QPalette()
        palette.setColorGroup
        palette.setColor(QtGui.QPalette.ColorRole.Window, "#000000")
        self.setPalette(palette)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setWindowOpacity(0.1)
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)

 
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            global mousePos
            mousePos = unreal.WidgetLayoutLibrary.get_mouse_position_on_viewport(world)
            relativeMouseCoords = mousePos - screenMidpoint
            UES = unreal.UnrealEditorSubsystem()
            camLocation = unreal.UnrealEditorSubsystem.get_level_viewport_camera_info(UES)
 
            self.spawnMousePos = mousePos
 
            global cameraValues
            cameraValues = []
            for x in camLocation:
                cameraValues.append(x)
 
            self.meshArray = []
 
            global vForward
            vForward = unreal.MathLibrary.get_forward_vector(cameraValues[1])
            global spawnLocation
            spawnLocation = cameraValues[0] + (vForward *  (screenRes[1]*0.9))
 
            actorClass = unreal.EditorAssetLibrary.load_blueprint_class('/Game/AnnotationTool/SplineBlueprint')
            componentClass = unreal.SplineMeshComponent
            global Drawing
            Drawing = EAS.spawn_actor_from_class(actorClass, spawnLocation)
            Drawing.set_actor_rotation(cameraValues[1], False)
            Drawing.add_actor_local_offset((0, relativeMouseCoords.x, -relativeMouseCoords.y), False, False)
            unreal.SubobjectDataSubsystem(Drawing).create_new_bp_component(componentClass, '/All/Game/AnnotationTool', 'SplineMesh')
 
            coordSpace = unreal.SplineCoordinateSpace
            Drawing.get_component_by_class(unreal.SplineComponent).clear_spline_points(update_spline = True)
            Drawing.get_component_by_class(unreal.SplineComponent).add_spline_point((0, 0, 0), coordSpace.LOCAL, update_spline = True)
            global splinePoint
            global splineIndex
            global MIIndex
            splineIndex = 0
            splinePoint = Drawing.get_component_by_class(unreal.SplineComponent).get_spline_point_at(splineIndex, coordSpace.LOCAL)
            self.meshArray.append(Drawing)
            Drawing.get_component_by_class(unreal.SplineComponent).set_editor_property("visible", True)
            self.meshMat = unreal.load_asset("/Game/AnnotationTool/M_Spline.M_Spline")

        elif event.button() == QtCore.Qt.MiddleButton:
            self.destroy()
 
 
    def get_sub_handle_object(sub_handle):
        obj = BFL.get_object(BFL.get_data(sub_handle))
        return obj
    def add_component(self, root_data_handle, subsystem, blueprint, new_class, name):
        sub_handle, fail_reason = subsystem.add_new_subobject(
            params = unreal.AddNewSubobjectParams(
                parent_handle=root_data_handle,
                new_class=new_class,
                blueprint_context=blueprint
            )
        )
        if not fail_reason.is_empty():
            raise Exception(f"ERROR from sub_object_subsystem.add_new_subobject: {fail_reason}")
        subsystem.rename_subobject(handle=sub_handle, new_name=unreal.Text(name))
        subsystem.attach_subobject(owner_handle=root_data_handle, child_to_add_handle=sub_handle)
        obj = BFL.get_object(BFL.get_data(sub_handle))
        return sub_handle, obj
 
    def mouseReleaseEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            AGU = unreal.ActorGroupingUtils()
            group = AGU.group_actors(self.meshArray)
            group.set_actor_label("SplineGroup")
            InitialiseTool.CreateMaterialInstance()
            self.showNormal()
    def mouseMoveEvent(self, event):
        global world
        global mousePos
        currentMousePos = unreal.WidgetLayoutLibrary.get_mouse_position_on_viewport(world)
        relativeMouseCoords = currentMousePos - self.spawnMousePos
        correctedLocation = (0, relativeMouseCoords.x, -relativeMouseCoords.y)
        posDiff = currentMousePos - mousePos

        if abs(posDiff.x) >=20 or abs(posDiff.y) >= 20:
            global splineIndex
            coordSpace = unreal.SplineCoordinateSpace
            staticMesh = unreal.EditorAssetLibrary.load_asset('/Engine/BasicShapes/Cylinder.Cylinder')
            splineComp = Drawing.get_component_by_class(unreal.SplineComponent)
            Drawing.get_component_by_class(unreal.SplineComponent).add_spline_point(correctedLocation, unreal.SplineCoordinateSpace.LOCAL, update_spline = True)
            points = []
            points.append(splineComp.get_spline_point_at(splineIndex, coordSpace.WORLD))
            for point in points:
                oldPointData = unreal.SplineComponent.get_location_and_tangent_at_spline_point(splineComp, splineIndex-1, coordSpace.WORLD)
                newPointData = unreal.SplineComponent.get_location_and_tangent_at_spline_point(splineComp, splineIndex, coordSpace.WORLD)
 
                MeshactorClass = unreal.SplineMeshActor
                MeshActor = EAS.spawn_actor_from_class(MeshactorClass, (0, 0, 0))
                MeshActor.get_component_by_class(unreal.SplineMeshComponent).set_static_mesh(staticMesh)
                MeshActor.get_component_by_class(unreal.SplineMeshComponent).set_end_scale(end_scale = [sliderValue, sliderValue], update_mesh = True)
                MeshActor.get_component_by_class(unreal.SplineMeshComponent).set_start_scale(start_scale = [sliderValue, sliderValue], update_mesh = True)
                MeshActor.get_component_by_class(unreal.SplineMeshComponent).set_start_and_end(oldPointData[0], oldPointData[1], newPointData[0], newPointData[1], update_mesh=True)
                MeshActor.get_component_by_class(unreal.SplineMeshComponent).set_forward_axis(unreal.SplineMeshAxis.Z)
                MeshActor.get_component_by_class(unreal.SplineMeshComponent).set_editor_property("cast_shadow", False)
                MeshActor.get_component_by_class(unreal.SplineMeshComponent).set_material(0, instance)
                MeshActor.set_actor_hidden_in_game(True)
                MeshActor.set_actor_enable_collision(False)
 
                self.meshArray.append(MeshActor)

            mousePos = currentMousePos
            splineIndex = splineIndex + 1

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.destroy()

class CalibrateWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.calibrate_window = QMainWindow()
        self.setMinimumSize(QSize(2000, 2000))
        palette = QtGui.QPalette()
        palette.setColorGroup
        palette.setColor(QtGui.QPalette.ColorRole.Window, "#000000")
        self.setPalette(palette)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setWindowOpacity(0.1)
 
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            world = unreal.UnrealEditorSubsystem().get_editor_world()
            global screenMidpoint
            screenMidpoint = unreal.WidgetLayoutLibrary.get_mouse_position_on_viewport(world)
            self.destroy()
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.destroy()

#find all the tool menus names - we'll use this to register out our own tool menu

tool_menus = unreal.ToolMenus.get()


class AnnotationToolMenu():
    def __init__(self):
        self.tool_menus = unreal.ToolMenus.get()
        self.menuOwner = "AnnotationTool"
        self.tool_menu_name = "LevelEditor.MainMenu.AnnotationTool"
        self.newMenu = None

    def CreateMenu(self):

        mainMenu = self.tool_menus.find_menu("LevelEditor.MainMenu")
        self.newMenu = mainMenu.add_sub_menu("AnnotationTool", self.menuOwner, self.menuOwner, "Annotation Tool")
        self.newMenu = self.tool_menus.register_menu(self.tool_menu_name, "", unreal.MultiBoxType.MENU, True)
        self.tool_menus.refresh_all_widgets()

    def CreateMenuEntry(self):
        command = (
            "from AnnotationPythonScript import InitialiseTool, UnrealToolWindow, ColourWindow, TransparentWindow, CalibrateWindow\n"
            "InitialiseTool.CreatePath\n"
            "InitialiseTool.CreateSplineBlueprint()\n"
            "InitialiseTool.CreateMaterial()\n"
            "InitialiseTool.CreateMaterialInstance()\n"
            "InitialiseTool.launchWindow()"
        )

        menuEntry = unreal.ToolMenuEntryExtensions.init_menu_entry(
            owner=self.menuOwner,
            name=self.menuOwner,
            label="Annotation Tool Utility",
            tool_tip="Annotation Tool",
            command_type= unreal.ToolMenuStringCommandType.PYTHON,
            custom_command_type="",
            command_string= command
        )

        icon = "ClassIcon.SplineComponent"
        menuEntry.set_icon("EditorStyle", icon)

        self.newMenu.add_menu_entry("Utils", menuEntry)

        self.tool_menus.refresh_all_widgets()

if __name__ == "__main__":
    menu = AnnotationToolMenu()
    menu.CreateMenu()
    menu.CreateMenuEntry()