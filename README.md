![GitHub](https://img.shields.io/github/license/ChristopherLuciano/OnCyber-CinematicEditor-BlenderAddon?label=License)


![screenshot01.png](https://github.com/ChristopherLuciano/Oncyber-CinematicEditor-BlenderAddon/raw/main/images/screenshot01.png)

# OnCyber-CinematicEditor-BlenderAddon
Blender-based Cinematic spline editor for use with the Oncyber cinematic video creator.

## Description
Oncyber's platform is simply phenomenal! Plus they are continually building and releasing new features to the community.  One such feature, the Cinematic Editor for creating videos of spaces, allows you to create stunning videos of your space.  However, the current version of this editor lacks a few usability features, making it a bit cumbersome to work with.  Navigating around the space to adjust nodes is difficult since parts of the model often obstruct the view. There's also currently no way to duplicate nodes, adjust multiple nodes at once, reorder sequences, nor the ability to accurately align nodes.  This hinders one's ability to quickly and easily create video sequences, especially when one is coming from a full fledged editing program like Blender.

Surely Oncyber is already working on updates to their Cinematic Editor and it will be interesting to see what they have in store for us.  In the meantime, this OnCyber-CinematicEditor-BlenderAddon attempts to ease the creation of video sequences for builders by enabling full editing of splines and nodes directly within Blender itself.

## Audience
This tool is for architects and builders who are creating video presentations of their spaces.  End users likely won't have the tools nor access to source files to run this on their owned spaces.

**Note:** It is not required that your space was originally built in Blender to use this tool.  If your space was built in another 3D modeling program, you can still import your .glb file into Blender and create your splines and nodes.

## DISCLAIMER
I cobbled this together to meet an immediate need. While this code has been fully tested and used by myself on my own project, I make no warranties on its functionality.  **I STRONGLY recommend that you do not run this on your main .blend file but instead run it on a separate copy.**  All functions are intended to be non-destructive to any existing elements within your .blend file with the exception of the Preview Node function which will change some properties of the chosen camera (see [Viewer](#viewer) below for more details)

## Getting Started
* Developed and tested on:
	 * Blender 3.3.0
	 * Python 3.10.2
	 * Windows 11

### Installing
* Download the python script file from github
	* oncyber-cinematic-addon.py
* From within Blender, choose Edit > Preferences > Add-ons
* Click 'Install', select the downloaded oncyber-cinematic-addon.py file, click 'Install Add-on'
* Find the 'Oncyber Cinematic' add-on from the Community collection
* Click the checkbox to enable the add-on
* A new panel will now be available within the 3D Viewport editor sidebar
	* If not visible, hit 'N' to toggle the sidebar on/off

## Background
The Oncyber Cinematic Editor uses spline curves with key points along those curves to control the camera.  You can have multiple spline items with each spline containing two curves: one for the camera location and one for where the camera should be looking.  The key points on these curves correspond 1:1 in that the first camera position will point the camera at the first lookat position, and similarly for all subsequent positions.  Oncyber requires at least four (4) key points within each spline.

This add-on adopts a similar methodology:
* Define the SPLINE collections where each one represents a separate camera path through the scene
* Within each SPLINE, two child collections are created to hold the key points along the paths: DOLLY and LOOKAT
* The matching of DOLLY and LOOKAT positions are done alphabetically at export time.  All objects under DOLLY are alphabetically sorted, then all objects under LOOKAT are also alphabetically sorted, then the positions are matched up 1:1.  See [Output](#output) below for more details.

 SPLINE, DOLLY, and LOOKAT collections are organized as follows:
```markdown
├── SPLINE.000
│   ├── DOLLY.000
│   │   ├── dolly object.000
│   │   ├── dolly object.001
│   │   ├── dolly object.002
│   │   ├── dolly object.003
│   ├── LOOKAT.000
│   │   ├── lookat object.000
│   │   ├── lookat object.001
│   │   ├── lookat object.002
│   │   ├── lookat object.003
├── SPLINE.001
│   ├── DOLLY.001
│   │   ├── dolly object.004
│   │   ├── dolly object.005
│   │   ├── dolly object.006
│   │   ├── dolly object.007
│   ├── LOOKAT.001
│   │   ├── lookat object.004
│   │   ├── lookat object.005
│   │   ├── lookat object.006
│   │   ├── lookat object.007
...etc...
```
The SPLINE, DOLLY, and LOOKAT items above are Collections.  The objects can be any Blender object which you like.  When you choose 'Add New Spline and Nodes', the add-on creates Cube meshes and assigns materials according to the same color scheme as used in Oncyber: green for DOLLY, blue for LOOKAT.

## Usage
The add-on is separated into individual sections as described below.  Refer to the screenshot shown above to see each of these within the add-on interface.

### Import
You can import a JSON file which was created either from this add-on or from the Oncyber Cinematic Editor directly (e.g., cinematic.json)

* Choose the 'Source File' and click 'Import File'

Each time you import a file, a new top level collection will be created to hold the generated SPLINE configuration.  This top level collection will be named according to the following naming convention:
* import.[YYY-MM-DD] [HH:MM:SS]

This allows you to separate the SPLINE configurations from your other scene objects and manage multiple configurations within the same .blend file.

### Splines
This is the main section of the add-on and where you will manage your SPLINE nodes.
* Root Collection
	* This is the root collection of your SPLINE nodes.  You can choose from a list of existing collections or drag & drop a collection from the Blender outliner.
	* The main purpose of the root collection is to indicate which collection should be used when a new SPLINE is created from within the add-on using one of the Add Spline functions (the '+' buttons to the right of the spline list)
	* When you Import a file, a new root collection will automatically be created for you and set as the root collection
* Spline list
	* Here you can manage the individual SPLINES which control the cinematic animation.
	* The list shows three columns:
		* Name
			* A logical name which you can use to label your SPLINE for easy identification (e.g., 'Exterior Flyover')
		* Target
			*  The SPLINE collection within the .blend file which contains the DOLLY and LOOKAT nodes for that spline 
		* Show / Hide
			* Allows you to quickly toggle a SPLINE's visibility within the viewport
	* To change the Name and Target of a SPLINE, select the SPLINE from the list.  Two editor fields will then appear below the SPLINE list where you can change these values.
* Action Buttons
	* Add New Spline 
		* This will create a new SPLINE collection structure under the chosen Root Collection
	* Add New Spline and Nodes
		*  Like Add New Spline, this will create a new SPLINE collection structure under the chosen Root Collection, but additionally add starter DOLLY and LOOKAT nodes
		* It will create new materials 'spline.dolly' and 'spline.lookat' to color code the DOLLY and LOOKAT nodes
	* Remove Spline
		* This will remove the SPLINE from the animation.  Note that this does not delete the SPLINE collection from your blend file, it simply removes it from the list so that it will not be included in the exported file.
	* Move Spline : Up / Down
		* Easily reorder your SPLINES.  Select a SPLINE from the list then choose up or down to move it's position.
	* Clear List
		* This will remove all SPLINES from the animation.  Note that this does not delete the SPLINE collections from your blend file, it simply removes them from the list so that they will not be included in the exported file.

### Viewer
 From here you can quickly preview an individual DOLLY and LOOKAT pair to see what the camera view will look like at the chosen spline position.
 * Camera
	 * Choose the camera which you want to use for the preview.  You can choose from a list of existing cameras or drag & drop one from the Blender outliner.
 * Add Default Camera
	 * If you don't already have a camera in your scene, this will add a new camera named 'OncyberCinematic' for you.  This camera will be created with the necessary configuration to closely match that used within the Oncyber Cinematic Editor.
 * Preview Node
	 * This allows for quickly jumping into camera view to preview the camera angle
	 * It does the following:
		 * Switch the 3D Viewport into camera view (equivalent to the Blender hotkey Numpad 0)
		 * Position the camera to the same position as the chosen DOLLY object
		 * Add a 'Track To' constraint to the camera so that it looks at the corresponding LOOKAT object
		 * Modify the camera's configuration (e.g., focal length) to give a more accurate view
		 * Hide all other cinematic objects from the scene so as to give a clear camera view
	 * **Note:** This will change the configuration of the chosen camera.  If you already have a camera in your scene for other purposes, it's recommended that you choose or add a different camera for this Preview function so as to not change your other camera's configuration.
 * Cancel Preview
	 * This will revert back to your normal viewport view, turning off Camera View and showing all other cinematic objects in the scene which were hidden during Preview mode

### Output
This will take your SPLINE configuration and export the JSON file for importing into Oncyber Cinematic Editor.
* Target File
	* The full path to the file where the file will be generated
* Export to File
	* This will export your spline configuration and write the target file

SPLINES are exported according to the order as shown in the Spline List, top to bottom.  Within each SPLINE, the DOLLY and LOOKAT nodes are exported according to **alphabetical** order.  By default, Blender usually uses alphabetical sorting within the outline, therefore what you see there should correspond to the output order.  Note though that you may need to rename objects to achieve your desired ordering.

You can now import the generated JSON file into Oncyber Cinematic Editor.  The splines may require some adjusting to get the desired end result.

## Help
Contact me on Twitter if you have any questions or ideas for new features.
![Twitter URL](https://img.shields.io/twitter/url?label=%40CJLuciano&style=social&url=https%3A%2F%2Ftwitter.com%2FCJLuciano)

## Version History

* 0.0.1
    * Initial release

## License

This project is licensed under the GPL-3  GNU General Public License - see the LICENSE file for details
