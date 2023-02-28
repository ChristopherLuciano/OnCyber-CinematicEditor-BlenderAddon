bl_info = {
    # required
    "name": "Oncyber Cinematic",
    "blender": (3, 0, 0),
    "category": "Object",
    "version": (0, 0, 1),
    "author": "@CJLuciano - SmasthTheBat.com",
    "description": "Spline data editor for use in Oncyber Cinematic editor",
    "doc_url": "https://github.com/ChristopherLuciano/Oncyber-CinematicEditor-BlenderAddon",
}

import bpy
import re
import json
from datetime import datetime
from bpy.props import StringProperty, IntProperty, CollectionProperty
from bpy.types import PropertyGroup, UIList, Operator, Panel
from enum import IntEnum

# GLOBALS ---------------------------------------------------------------------------------
PROPS = [
    ( "target_file", bpy.props.StringProperty(
        name="Target File", 
        subtype="FILE_PATH", 
        default="", 
        description="Target file for export"
    )),
    ( "source_file", bpy.props.StringProperty(
        name="Source File", 
        subtype="FILE_PATH", 
        default="", 
        description="Source file to import"
    )),
    ( "status_message", bpy.props.StringProperty(
        name="File export status message", 
        default=""
    )),
    ( "viewerCamera", bpy.props.PointerProperty(
            type=bpy.types.Object,
            name="Camera",
            description="Select a camera object from the scene",
            poll=lambda self, obj: obj.type == "CAMERA"
    )),
    ( "rootCollection", bpy.props.PointerProperty(
            type=bpy.types.Collection,
            name="Root Collection",
            description="The root collection to hold the spline collections"
    )),
    ( "defaultDollyNode", bpy.props.PointerProperty(
            type=bpy.types.Object,
            name="Default Dolly Node",
            description="Default Dolly node, all other generated dolly objects copy from this"
    )),
    ( "defaultLookatNode", bpy.props.PointerProperty(
            type=bpy.types.Object,
            name="Default Lookat Node",
            description="Default Lookat node, all other generated lookat objects copy from this"
    ))
    
]

bpy.props.EnumProperty(items=(("UP", "Up", ""), ("DOWN", "Down", ""),) )

# FUNCTIONS -------------------------------------------------------------------------------
def generate_output(context, operator, params):
    (output_file) = params

    outputData = {
        "export" : []
    }

    if len( context.scene.splineList ) < 1:
            operator.report({"ERROR"}, "Nothing to export")
            return;
        
    for index in range( 0, len( context.scene.splineList ), 1 ):
        splineTree = context.scene.splineList[ index ].splineTree
        if splineTree is None:
            operator.report({"ERROR"}, "Collection error: was it deleted?")
            return;
        splineName = splineTree.name
        dollys = None 
        lookats= None 
        
        dollys  = get_child_of_splinetree( splineTree, "DOLLY"  )
        lookats = get_child_of_splinetree( splineTree, "LOOKAT" )            
            
        if dollys is None or lookats is None:
            operator.report({"ERROR"}, "Missing DOLLY or LOOKAT collection in " + splineName )
            return;
        elif len( dollys.objects ) != len( lookats.objects ):
            operator.report({"ERROR"}, "Count mismatch in " + splineName )
            return;
        elif len( dollys.objects ) < 4:
            operator.report({"ERROR"}, "Spline " + splineName + " must have at least 4 DOLLY and LOOKAT nodes")
            return;
        else:
            outputData[ "export" ].append( {"duration": 10, "position": [], "lookat": [] } )
            
            dollysSorted  = sorted( dollys.objects,  key=lambda obj: obj.name )
            lookatsSorted = sorted( lookats.objects, key=lambda obj: obj.name )        
            
            for i in range( 0, len( dollysSorted ), 1 ):
                dolly = dollysSorted[ i ]
                lookat = lookatsSorted[ i ]
                outputData[ "export" ][ index ][ "position" ].append( [  dolly.location.x,  dolly.location.z,  dolly.location.y * -1  ] )
                outputData[ "export" ][ index ][ "lookat"   ].append( [ lookat.location.x, lookat.location.z, lookat.location.y * -1  ] )

    outputFile = open( output_file, "w" )
    outputFile.write( json.dumps(outputData, indent=4) )
    now = datetime.now()
    setattr( bpy.types.Scene, "status_message", "File generated at: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") )
    operator.report( {"INFO"}, "File generated" )
        
def create_new_spline_structure( parentCollection ):
    collectionSpline = bpy.data.collections.new( "spline" )
    if parentCollection is None:
        bpy.context.scene.collection.children.link( collectionSpline )
    else:
        parentCollection.children.link( collectionSpline )

    dollyCollection = bpy.data.collections.new( "dolly" )
    collectionSpline.children.link( dollyCollection )

    lookatCollection = bpy.data.collections.new( "lookat" )
    collectionSpline.children.link( lookatCollection )
    
    return collectionSpline, dollyCollection, lookatCollection

def add_spline_node( targetLocation, defaultNode, targetCollection, translateLocation=True ):
    if translateLocation:
        location = (targetLocation[0], targetLocation[2]*-1, targetLocation[1] )
    else:
        location = targetLocation
    
    if defaultNode is not None:
        newNode = defaultNode.copy()
        newNode.hide_render = False
        newNode.hide_viewport = False
        newNode.hide_select = False
        newNode.location = location
        #force default suffix of '.000' to avoid non-suffix version and sorting/ordering issues
        if   defaultNode.name == "dolly(reference)" : newNode.name = "dolly.000"
        elif defaultNode.name == "lookat(reference)": newNode.name = "lookat.000"
        
        for collection in newNode.users_collection:
            collection.objects.unlink( newNode )
        targetCollection.objects.link( newNode )


def import_file(context, operator, params):
    (input_file) = params
    jsonFile = None
    jsonData = None
    
    try:
        jsonFile = open(input_file, "r")
        jsonString = jsonFile.read()
        jsonData = json.loads( jsonString )
    except FileNotFoundError:
        operator.report( {"ERROR"}, "Could not find file " + input_file )        
    except IOError:
        operator.report( {"ERROR"}, "Could not read the file " + input_file )        
    except:
        operator.report( {"ERROR"}, "Could not read the file " + input_file )        
    if jsonData is not None:
        clear_spline_list( context )
        now = datetime.now()
        collectionMainImport = bpy.data.collections.new( "import." + datetime.now().strftime("%Y-%m-%d %H:%M:%S") )
        create_default_nodes( context, collectionMainImport )
        bpy.context.scene.collection.children.link( collectionMainImport )
        for splineIndex in range( 0, len( jsonData["export"]), 1 ):
            newSplineTree = create_new_spline_structure( collectionMainImport )
            newItem = context.scene.splineList.add()
            newItem.splineTree = newSplineTree[ SPLINETREE.SPLINE ]
            newItem.name = newSplineTree[ SPLINETREE.SPLINE ].name
            splineItem = jsonData[ "export" ][ splineIndex ]
            for dollyIndex in range( 0, len( jsonData[ "export" ][ splineIndex ][ "position" ] ), 1 ):
                add_spline_node( splineItem["position"][dollyIndex], context.scene.defaultDollyNode, newSplineTree[ SPLINETREE.DOLLY ] )
            for lookatIndex in range( 0, len( jsonData[ "export" ][ splineIndex ][ "lookat" ] ), 1 ):
                add_spline_node( splineItem["lookat"][lookatIndex], context.scene.defaultLookatNode, newSplineTree[ SPLINETREE.LOOKAT ] )
        jsonFile.close()
        
        context.scene.rootCollection = collectionMainImport
        
def add_spline( context, operator, addNodes=False ):
    newSplineTree = create_new_spline_structure( context.scene.rootCollection )
        
    newItem = context.scene.splineList.add()
    newItem.splineTree = newSplineTree[ SPLINETREE.SPLINE ]
    newItem.name = newSplineTree[ SPLINETREE.SPLINE ].name
    
    splineList = context.scene.splineList
    index = len( splineList )

    context.scene.list_index = index-1
    create_default_nodes( context, context.scene.rootCollection )
    if addNodes:
        add_spline_node( bpy.context.scene.cursor.location, context.scene.defaultDollyNode,  newSplineTree[SPLINETREE.DOLLY],  translateLocation=False )
        add_spline_node( bpy.context.scene.cursor.location, context.scene.defaultLookatNode, newSplineTree[SPLINETREE.LOOKAT], translateLocation=False )


def create_default_node( context, parentCollection, objName, matName, matColor ):
    bpy.ops.mesh.primitive_cube_add( size=1, location=(0,0,0) )
    newCube = bpy.context.active_object
    newCube.name = objName
    
    newMaterial = bpy.data.materials.get( matName )
    if newMaterial is None:
        newMaterial = bpy.data.materials.new( name=material_name )
        newMaterial.diffuse_color = matColor
    newCube.data.materials.append( newMaterial )                    
    newCube.show_name = True
    newCube.hide_render = True
    newCube.hide_viewport = True
    newCube.hide_select = True
    if parentCollection is not None:
        for collection in newCube.users_collection:
            collection.objects.unlink( newCube )
        parentCollection.objects.link( newCube )
    return newCube

def create_default_nodes( context, parentCollection ):
    if context.scene.defaultDollyNode is None:
        context.scene.defaultDollyNode  = create_default_node( context, parentCollection, "dolly(reference)",  "spline.dolly",  ( 0, 1, 0, 1 ) )
    if context.scene.defaultLookatNode is None:
        context.scene.defaultLookatNode = create_default_node( context, parentCollection, "lookat(reference)", "spline.lookat", ( 0, 0, 1, 1 ) )
    return

def clear_spline_list(context):
     context.scene.splineList.clear()
     context.scene.list_index = 0

def add_camera( context, operator, params ):
    cinematicCamera = bpy.data.objects.get( "OncyberCinematic" )
    if cinematicCamera is None:
        camera_data = bpy.data.cameras.new( "OncyberCinematic" )
        camera_object = bpy.data.objects.new( "OncyberCinematic", camera_data )
        bpy.context.scene.collection.objects.link( camera_object )
        camera_data.lens = 15
        operator.report( {"INFO"}, "Camera added" )
        bpy.context.scene.viewerCamera = camera_object #camera_data

    else:
        operator.report( {"ERROR"}, "Camera already exists" )

def get_camera( ):
    camera_data =  bpy.context.scene.viewerCamera
    return camera_data

#find a splineTree collection within the view layer
def get_spline_collection_viewlayer( splineTreeName ):
    view_layer = bpy.context.view_layer
    layer_collection = view_layer.layer_collection
    search_queue = layer_collection.children[:]
    while search_queue:
        current_collection = search_queue.pop(0)
        if current_collection.name == splineTreeName:
            return current_collection
            break
        search_queue.extend(current_collection.children)
    else:
        return None

#find the parent splineTree collection given a child dolly or lookat collection
def get_parent_splinetree( nodeCollection ):
    visited_collections = set()
    collections_to_check = list( bpy.data.collections )
    while collections_to_check:
        current_collection = collections_to_check.pop()
        if nodeCollection.name in current_collection.children.keys():
            return current_collection
        visited_collections.add( current_collection )
        for child_collection in current_collection.children.values():
            if child_collection not in visited_collections:
                collections_to_check.append( child_collection )
    return None
    
#find the child dolly or lookat collection given a splineTree
def get_child_of_splinetree( splineTree, childType ):
    for c in splineTree.children:
        if c.name.startswith( childType.lower() ):
            return c
    return None
    
def preview_node( context, operator, params ):
    cancel_preview( context, operator, params )
    
    if bpy.context.active_object is None or bpy.context.active_object.name.startswith( "dolly." ) == False :
        operator.report( {"ERROR"}, "Please select a DOLLY object first" )
        return;
                
    cinematicCamera = get_camera()
    if cinematicCamera is not None:
        dollyObject = bpy.context.active_object;
        if len( dollyObject.users_collection ) != 1:
            operator.report( {"ERROR"}, "Wrong structure: Dolly " + dollyObject.name + " in more than one collection." ) 
            return None
        
        dollyCollection = dollyObject.users_collection[0]
        splineTreeSpline = get_parent_splinetree( dollyCollection )
        lookatCollection = get_child_of_splinetree( splineTreeSpline, "lookat" )
        
        if len(dollyCollection.objects) != len(lookatCollection.objects):
            operator.report({"ERROR"}, "Count mismatch in " + splineTreeSpline.name )
            return None
                
        dollysSorted  = sorted( dollyCollection.objects,  key=lambda obj: obj.name )
        lookatsSorted = sorted( lookatCollection.objects, key=lambda obj: obj.name )        
        
        dollyIndex = None
        for tempIndex in range( 0, len( dollysSorted ), 1 ):
            if dollysSorted[ tempIndex ].name == dollyObject.name:
                dollyIndex = tempIndex
                break
        
        lookatObject = lookatsSorted[ dollyIndex ]
        if dollyObject is not None:
            cinematicCamera.location = dollyObject.location
            cinematicCamera.rotation_euler = dollyObject.rotation_euler

        if lookatObject is not None:
            cinematicCamera.constraints.new( "TRACK_TO" )
            cinematicCamera.constraints[ "Track To" ].target = lookatObject
            cinematicCamera.constraints[ "Track To" ].track_axis = "TRACK_NEGATIVE_Z"

        context.region_data.view_perspective = "CAMERA"
        
        #hide all splines
        for splineIndex in range( 0, 100, 1 ):
            splineName = "spline." + f"{splineIndex:03d}"
            if splineName in bpy.data.collections:
                spline = bpy.data.collections[ splineName ]        
                spline.hide_viewport = True
        operator.report( {"INFO"}, "Preview active" )
    else:
        operator.report( {"ERROR"}, "Camera not found" )

def cancel_preview( context, operator, params ):
    context.region_data.view_perspective = "PERSP"
    for splineIndex in range( 0, 100, 1 ):
        splineName = "spline." + f"{splineIndex:03d}"
        if splineName in bpy.data.collections:
            spline = bpy.data.collections[ splineName ]        
            spline.hide_viewport = False
    cinematicCamera = get_camera()
    if cinematicCamera is not None:
        for cns in cinematicCamera.constraints:
            cinematicCamera.constraints.remove( cns )

# OPERATORS -------------------------------------------------------------------------------
class GenerateOperator( bpy.types.Operator ):
    bl_idname = "opr.object_generate"
    bl_label = "Generate Output"
    bl_description = "Export to file"
    
    def execute( self, context ):
        params = (
            context.scene.target_file
        )
        generate_output( context, self, params )
        return { "FINISHED" }
    
class ImportOperator( bpy.types.Operator ):
    bl_idname = "opr.object_import"
    bl_label = "Import File"
    bl_description = "Import the file"
    
    def execute( self, context ):
        params = (
            context.scene.source_file
        )
        import_file( context, self, params )
        #create_default_nodes()
        return { "FINISHED" }
    
class AddSplineOperator( bpy.types.Operator ):
    bl_idname = "opr.object_addspline"
    bl_label = "Add New Spline"
    bl_description = "Create and add a new spline collection"    
    
    def execute( self, context ):
        add_spline( context, self, addNodes=False )
        return { "FINISHED" }

class AddSplineAndNodesOperator(bpy.types.Operator):
    bl_idname = "opr.object_addsplineandnodes"
    bl_label = "Add New Spline and Nodes"
    bl_description = "Create and add a new spline collection with DOLLY and LOOKAT nodes"    
    
    def execute( self, context ):
        add_spline( context, self, addNodes=True )
        return { "FINISHED" }

class RemoveSplineOperator( bpy.types.Operator ):
    bl_idname = "opr.object_removespline"
    bl_label = "Remove Spline"
    bl_description = "Remove the new spline collection from the list.  Does not delete the actual collection."    
    
    @classmethod
    def poll( cls, context ):
        return context.scene.splineList

    def execute( self, context ):
        splineList = context.scene.splineList
        index = context.scene.list_index

        splineList.remove( index )
        context.scene.list_index = min( max(0, index - 1), len(splineList) - 1 )

        return{"FINISHED"}   
 
class ClearListOperator( bpy.types.Operator ):
    bl_idname = "opr.object_clearlist"
    bl_label = "Clear list"
    bl_description = "Clears all spline collections from the list.  Does not delete the actual collections."    
    
    @classmethod
    def poll( cls, context ):
        return context.scene.splineList

    def execute( self, context ):
        clear_spline_list(context)
        return{ "FINISHED" }   


class HideSplineOperator( bpy.types.Operator ):
    bl_idname = "opr.object_hidespline"
    bl_label = "Hide the Spline from view"
    bl_description = "Hides the spline collection from the current view"    
    
    index: bpy.props.IntProperty()
    
    def execute( self, context ):
        splineList = context.scene.splineList
        splineIndex = self.index #context.scene.list_index
        
        collectionInView = get_spline_collection_viewlayer( splineList[ splineIndex ].splineTree.name )
        
        if collectionInView is not None:
            collectionInView.hide_viewport = not collectionInView.hide_viewport

        return{ "FINISHED" }

class AddCameraOperator( bpy.types.Operator ):
    bl_idname = "opr.object_addcamera"
    bl_label = "Add Camera"
    bl_description = "Add the default Cinematic camera to the scene"        
    
    def execute( self, context ):
        params = (
        )
        add_camera( context, self, params )
        return { "FINISHED" }

class PreviewNodeOperator( bpy.types.Operator ):
    bl_idname = "opr.object_previewnode"
    bl_label = "Preview Node"
    bl_description = "Enter Camera View using the chosen camera and the selected DOLLY object"        
    
    def execute( self, context ):
        params = (
        )
        preview_node( context, self, params )
        return { "FINISHED" }

class CancelPreviewOperator( bpy.types.Operator ):
    bl_idname = "opr.object_cancelpreview"
    bl_label = "Cancel Preview"
    bl_description = "Cancel preview"
    
    def execute( self, context ):
        params = ()
        cancel_preview( context, self, params )
        return { "FINISHED" }

class MoveListItemOperator( bpy.types.Operator ):
    bl_idname = "opr.object_moveitem"
    bl_label = "Move an item in the list"
    bl_description = "Move selected spline"    

    direction: bpy.props.EnumProperty( items=(("UP", "Up", ""), ("DOWN", "Down", ""),) )
    
    @classmethod
    def poll( cls, context ):
        return context.scene.splineList

    def move_index(self):
        index = bpy.context.scene.list_index
        list_length = len( bpy.context.scene.splineList ) - 1 
        new_index = index + (-1 if self.direction == "UP" else 1)

        bpy.context.scene.list_index = max( 0, min(new_index, list_length) )

    def execute(self, context):
        splineList = context.scene.splineList
        index = context.scene.list_index

        neighbor = index + (-1 if self.direction == "UP" else 1)
        splineList.move(neighbor, index)
        self.move_index()

        return{ "FINISHED" }
    
# CLASSES --------------------------------------------------------------------------------- 
class SPLINETREE(IntEnum):
    SPLINE  = 0
    DOLLY   = 1
    LOOKAT  = 2
    
class SPLINE_UL_List( UIList ):
    def draw_filter( self, context, layout ):
        return; 
    
    def draw_item( self, context, layout, data, item, icon, active_data, active_propname, index ):
        self.use_filter_show = False
        if self.layout_type in { "DEFAULT", "COMPACT" }:
            displayName = ""
            if item.splineTree is None:
                displayName = "~deleted~"
            elif item.splineTree.name == "" or item.splineTree.name is None:
                displayName = "~deleted~"
            else:
                displayName = item.name #splineCollection.name

            layout.label(text=displayName, icon = "OUTLINER_COLLECTION")
            if item.splineTree is not None:
                layout.label( text="( " + item.splineTree.name + " )" )
                iconName = "TRIA_UP"
                collectionInView = get_spline_collection_viewlayer( item.splineTree.name )
                if collectionInView is not None:
                    if collectionInView.hide_viewport == False: iconName = "HIDE_OFF"
                    else: iconName = "HIDE_ON"
                hideBtnOp = layout.operator( "opr.object_hidespline", text="", icon=iconName )
                hideBtnOp.index = index
        elif self.layout_type in { "GRID" }:
            layout.alignment = "CENTER"
            layout.label( text="", icon="OBJECT_DATAMODE" )

class SplineListItem( PropertyGroup ):
    name: StringProperty(
           name="Name",
           description="Logical name for this spline collection",
           default="Untitled")

    splineTree:  bpy.props.PointerProperty(
        type=bpy.types.Collection,
        name="Target spline collection",
        description="Target spline collection containing DOLLY and LOOKAT nodes"
    )
    
# PANELS ----------------------------------------------------------------------------------
class CinematicMainPanel( bpy.types.Panel ):
    bl_idname = "VIEW3D_PT_object_mainpanel"
    bl_label = "Oncyber Cinematic"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Oncyber"
    
    def draw( self, context ):
        layout = self.layout
        scene = context.scene
    
class ImportPanel( bpy.types.Panel ):
    bl_idname = "VIEW3D_PT_object_importpanel"
    bl_parent_id = "VIEW3D_PT_object_mainpanel"
    bl_label = "Import"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Oncyber"
   
    def draw( self, context ):
        layout = self.layout
        scene = context.scene
        row = layout.row()
        row.prop( context.scene, "source_file" )
        row = layout.row()    
        row.operator( "opr.object_import", text="Import File", icon="IMPORT" )

class SplinesPanel( bpy.types.Panel ):
    bl_idname = "VIEW3D_PT_object_splinespanel"
    bl_parent_id = "VIEW3D_PT_object_mainpanel"
    bl_label = "Splines"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Oncyber"
    
    def draw( self, context ):
        layout = self.layout
        scene = context.scene
        
        row = layout.row()
        col = row.column()
        col.prop( context.scene, "rootCollection" )
        
        row = layout.row()
        col = row.column()
        col.template_list( "SPLINE_UL_List", "SplineList", scene, "splineList", scene, "list_index", item_dyntip_propname="name", rows=1 )
        
        col = row.column(align=True)
        col.operator( "opr.object_addspline", icon="ADD", text="" )
        col.operator( "opr.object_addsplineandnodes", icon="PLUS", text="" )        
        col.operator( "opr.object_removespline", icon="REMOVE", text="" )
        col.separator()
        col.operator( "opr.object_moveitem", icon="TRIA_UP", text="" ).direction = "UP"
        col.operator( "opr.object_moveitem", icon="TRIA_DOWN", text="" ).direction = "DOWN"
        col.separator()
        col.operator( "opr.object_clearlist", icon="X", text="" )

        index = bpy.context.scene.list_index
        splineList = bpy.context.scene.splineList
        if splineList is not None and len( splineList ) > 0 and bpy.context.scene.splineList[ index ] is not None:
            flow = layout.grid_flow( row_major=False, columns=0, even_columns=False, even_rows=False, align=True )
            col = flow.column( align=True )
            col.alignment = "RIGHT"
            col.prop( splineList[ index ], "name", text="Name" )
            col.prop( splineList[ index ], "splineTree", text="Target" )
            col.separator()
             
class ViewerPanel( bpy.types.Panel ):
    bl_idname = "VIEW3D_PT_object_viewerpanel"
    bl_parent_id = "VIEW3D_PT_object_mainpanel"
    bl_label = "Viewer"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Oncyber"
    
    def draw( self, context ):
        layout = self.layout
        scene = context.scene
        row = layout.row()

        row = layout.row()
        row.prop( context.scene, "viewerCamera" )
        row = layout.row()
        row.operator( "opr.object_addcamera", text="Add Default Camera", icon="VIEW_CAMERA" )
        row = layout.row()
        row.operator( "opr.object_previewnode", text="Preview Node", icon="VIEW_ZOOM" )
        row.operator( "opr.object_cancelpreview", text="Cancel Preview", icon="CANCEL" )

        layout.row().separator()

class GeneratorPanel( bpy.types.Panel ):
    bl_idname = "VIEW3D_PT_object_generatorpanel"
    bl_parent_id = "VIEW3D_PT_object_mainpanel"
    bl_label = "Output"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Oncyber"
    
    def draw( self, context ):
        layout = self.layout
        scene = context.scene
        row = layout.row()
        row.prop( context.scene, "target_file" )
        row = layout.row()    
        row.operator( "opr.object_generate", text="Export to File", icon="EXPORT" )
        row = layout.row()
        row.alignment = "CENTER"        
        row.label( text=context.scene.status_message )
   
CLASSES = [
    CinematicMainPanel,
    ImportPanel,
    SplinesPanel,
    ViewerPanel,
    GeneratorPanel,
    GenerateOperator,
    AddSplineOperator,
    AddSplineAndNodesOperator,
    RemoveSplineOperator,
    AddCameraOperator,
    PreviewNodeOperator,
    CancelPreviewOperator,
    SplineListItem,
    SPLINE_UL_List,
    HideSplineOperator,
    MoveListItemOperator,
    ClearListOperator,
    ImportOperator
    
]

def register():
    for ( prop_name, prop_value ) in PROPS:
        setattr( bpy.types.Scene, prop_name, prop_value )
    
    for cls in CLASSES:
        bpy.utils.register_class( cls )
        
    bpy.types.Scene.splineList = CollectionProperty( type = SplineListItem )
    bpy.types.Scene.list_index = IntProperty(name="", description="", default = 0)
        

def unregister():
    del bpy.types.Scene.splineList
    del bpy.types.Scene.list_index
    
    for ( prop_name, _) in PROPS:
        delattr( bpy.types.Scene, prop_name )

    for cls in CLASSES:
        bpy.utils.unregister_class( cls )
        

if __name__ == "__main__":
    register()
    
    

