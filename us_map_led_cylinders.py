#
# Description: This script creates emmissive LEDs and places them on a map of
# the United States from the Library of Congress.
# Disclaimer: The map is not shared in the repository.
# Author: Shahan Iqbal
# Clemson University
# Date: 2023-04-05
#

import bpy
import random
import pathlib
import addon_utils
from mathutils import Vector

					
def init_blender_env():
    """
        Select all objects in the view plane and delete them.
        Remove all user-created collections.
    """
	bpy.ops.object.select_all(action='SELECT')
	bpy.ops.object.delete()
	# Get a list of all user-created collections
	user_collections = [coll for coll in bpy.data.collections if not coll.name.startswith('Scene')]

	# Iterate over the user-created collections and delete them
	for coll in user_collections:
		bpy.data.collections.remove(coll)


def load_us_map(max_size_dim, image_path):
	addon_name = 'io_import_images_as_planes'

	laoded_default, loaded_state = addon_utils.check(addon_name)

	if not loaded_state:
		addon_utils.enable(addon_name)

	if image_path.exists():
		bpy.ops.import_image.to_plane(files=[{'name': str(image_path)}])
		
		# Get a reference to the newly created plane object
		plane = bpy.context.selected_objects[0]

		image = bpy.data.images[image_path.name]
		width = image.size[0]
		length = image.size[1]

        # We want to keep the aspect ratio of the map image
		length_ratio = length / width
		
		plane_width = max_size_dim
		plane_length = plane_width * length_ratio
		
		# Set the size of the plane
		plane.dimensions = (plane_width, plane_length, 0.0)  # (width, height, thickness)

		# Set the location of the plane to the origin
		plane.location = (0.0, 0.0, 0.0)
	else:
		print('File not found: {}'.format(image_path))


def new_material(id):

	mat = bpy.data.materials.get(id)

	if mat is None:
		mat = bpy.data.materials.new(name=id)

	mat.use_nodes = True

	if mat.node_tree:
		mat.node_tree.links.clear()
		mat.node_tree.nodes.clear()

	return mat


def new_shader(id, node_type, r, g, b, intensity=None):

	mat = new_material(id)
	
	nodes = mat.node_tree.nodes
	links = mat.node_tree.links
	output = nodes.new(type='ShaderNodeOutputMaterial')

	shader = None

	if node_type == 'emissive':	
		shader = nodes.new(type='ShaderNodeEmission')
		nodes['Emission'].inputs[0].default_value = (r, g, b, 1)
		nodes['Emission'].inputs[1].default_value = intensity
	
	if node_type == 'diffuse':
		shader = nodes.new(type='ShaderNodeBsdfDiffuse')
		nodes["Diffuse BSDF"].inputs[0].default_value = (r, g, b, 1)

	if shader is None:
		raise TypeError
	
	links.new(shader.outputs[0], output.inputs[0])
	
	return mat


def new_text(baseid, text):
	font_curve = bpy.data.curves.new(type="FONT", \
				name='{}_curve'.format(baseid))
	font_curve.body = text
	font_obj = bpy.data.objects.new(name=baseid+'_font', object_data=font_curve)

	bpy.context.scene.collection.objects.link(font_obj)

	return font_obj


def draw_object(x, y, z, mat, label, texmat):
	bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=0.5, align='WORLD', location=(x, y, z))
	led = bpy.context.active_object
	led.data.materials.append(mat)
	led.name = 'LED_{}_{}_{}'.format(x, y, z)
	
	text_str = 'Text_{}_{}_{}'.format(x, y, z)
	text = new_text(text_str, label)
	text.color = (0, 0, 0, 1)
	text.data.materials.append(texmat)
	
	bpy.data.objects[text.name].select_set(True)
	bpy.ops.object.convert(target='MESH')
	mesh_obj = bpy.context.active_object
	mesh_obj.select_set(True)
	bpy.ops.object.mode_set(mode='EDIT')
	bpy.ops.mesh.select_all(action='SELECT')
	bpy.ops.mesh.extrude_region_move(TRANSFORM_OT_translate={"value":(0, 0, 0.3)})
	bpy.ops.object.mode_set(mode='OBJECT')

	bpy.ops.object.select_all(action='DESELECT')

	led_obj = bpy.data.objects[led.name]
	font_obj = bpy.data.objects[text.name]

	led_obj.select_set(True)
	font_obj.select_set(True)

	font_obj.dimensions = (0.5, 0.5, 0.3)
	font_obj.location = (x-0.25, y-0.25, 0.3)

	# Create a new collection
	new_collection = bpy.data.collections.new(name=label + '_led')

	# Link the new collection to the current scene
	bpy.context.scene.collection.children.link(new_collection)

	# Link the objects to the new collection
	new_collection.objects.link(led_obj)
	new_collection.objects.link(font_obj)

    # deselect everything to ensure there is no conflict later
	bpy.ops.object.select_all(action='DESELECT')


states = ['AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'HI', \
	'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD', 'MA', 'MI', 'MN', \
	'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', \
	'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', \
	'WV', 'WI', 'WY']

# The following dictionary correspond to the specific rendering the US map at
# full resolution as the source. Each coordinate correspond to the capital city
# of the respective state on the map.
states_dict = {
	'AL': (14.0, -1.0, 0.0), 'AK': (-3.0, -25.0, 0.0), 'AZ': (-25.5, 1.0, 0.0),
	'AR': (5.5, 1.0, 0.0), 'CA': (-37.5, 13.0, 0.0), 'CO': (-13.0, 11.0, 0.0),
	'CT': (32.0, 18.5, 0.0), 'DE': (29.5, 13.0, 0.0), 'FL': (19.0, -6.0, 0.0),
	'GA': (18.0, 0.0, 0.0), 'HI': (-35.0, -25.0, 0.0), 'ID': (-28.0, 21.0, 0.0),
	'IL': (9.0, 11.0, 0.0), 'IN': (14.0, 11.5, 0.0), 'IA': (3.0, 14.0, 0.0),
	'KS': (0.0, 9.0, 0.0), 'KY': (16.0, 9.0, 0.0), 'LA': (8.0, -7.0, 0.0),
	'ME': (35.0, 24.0, 0.0), 'MD': (28.0, 13.0, 0.0), 'MA': (34.0, 20.5, 0.0),
	'MI': (16.0, 17.0, 0.0), 'MN': (4.0, 21.0, 0.0), 'MS': (9.0, -3.0, 0.0),
	'MO': (5.5, 8.5, 0.0), 'MT': (-21.0, 25.5, 0.0), 'NE': (-1.0, 16.0, 0.0),
	'NV': (-35.0, 14.0, 0.0), 'NH': (33.0, 22.0, 0.0), 'NJ': (30.0, 15.0, 0.0),
	'NM': (-15.5, 3.5, 0.0), 'NY': (30.0, 20.0, 0.0), 'NC': (26.0, 5.5, 0.0),
	'ND': (-6.5, 24.0, 0.0), 'OH': (18.5, 12.0, 0.0), 'OK': (-2.5, 2.5, 0.0),
	'OR': (-36.0, 25.5, 0.0), 'PA': (23.0, 14.0, 0.0), 'RI': (34.0, 19.0, 0.0),
	'SC': (23.0, 2.0, 0.0), 'SD': (-10.0, 19.0, 0.0), 'TN': (14.0, 4.5, 0.0),
	'TX': (-3.0, -7.5, 0.0), 'UT': (-23.0, 14.0, 0.0), 'VT': (31.0, 23.0, 0.0),
	'VA': (27.0, 9.0, 0.0), 'WA': (-34.0, 30.0, 0.0), 'WV': (21.0, 9.5, 0.0),
	'WI': (9.0, 17.0, 0.0), 'WY': (-13.0, 14.0, 0.0)
}

if __name__ == "__main__":
	# This is the filename of the US map
    filename = ''
	
	image_path = pathlib.Path('res/png/' + filename)

	load_us_map(90, image_path)

	for state, pos in states_dict.items():


		whitebalance = 255
		r = whitebalance
		g = whitebalance
		b = whitebalance

		x, y, z = pos

		# TODO this can be driven by data
		intensity = 1

		mat = new_shader('LEDShader_{}_{}_{}'.format(r, g, b), \
			'emissive', r, g, b, intensity)
		texmat = new_shader('TextShader_{}_{}_{}'.format(0, 0, 0), \
			'diffuse', 0, 0, 0)
		draw_object(x, y, z, mat, \
			label=state, texmat=texmat)
			
