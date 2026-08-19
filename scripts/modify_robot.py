 import bpy
import os
import math

# Paths
input_path = "tesla_bot.glb"
output_dir = "assets"
output_path = os.path.join(output_dir, "robot_k4000.glb")
os.makedirs(output_dir, exist_ok=True)

# Clear default scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Import robot
bpy.ops.import_scene.gltf(filepath=input_path)

# Ensure object mode
bpy.ops.object.mode_set(mode='OBJECT')

# Get all mesh objects
mesh_objs = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']

def set_material_black(material):
    if not material:
        return
    principled = None
    if material.node_tree:
        for node in material.node_tree.nodes:
            if node.type == 'BSDF_PRINCIPLED':
                principled = node
                break
    if principled:
        if "Base Color" in principled.inputs:
            principled.inputs["Base Color"].default_value = (0.01, 0.01, 0.01, 1)
        if "Metallic" in principled.inputs:
            principled.inputs["Metallic"].default_value = 0.0
        if "Roughness" in principled.inputs:
            principled.inputs["Roughness"].default_value = 0.7
    else:
        material.diffuse_color = (0.01, 0.01, 0.01, 1)
        if hasattr(material, 'metallic'):
            material.metallic = 0.0
        if hasattr(material, 'roughness'):
            material.roughness = 0.7

# Apply black body material to all existing materials
for mat in bpy.data.materials:
    set_material_black(mat)

# Compute bounding box of all mesh objects in world space
min_x = min_y = min_z = float('inf')
max_x = max_y = max_z = float('-inf')
for obj in mesh_objs:
    for vert in obj.data.vertices:
        world_co = obj.matrix_world @ vert.co
        min_x = min(min_x, world_co.x)
        min_y = min(min_y, world_co.y)
        min_z = min(min_z, world_co.z)
        max_x = max(max_x, world_co.x)
        max_y = max(max_y, world_co.y)
        max_z = max(max_z, world_co.z)

if math.isinf(min_x):
    raise Exception("No mesh found in imported robot")

center_x = (min_x + max_x) / 2
center_y = (min_y + max_y) / 2
center_z = (min_z + max_z) / 2

# Create LED face screen
face_width = 0.3
face_height = 0.4
face_location = (
    center_x,
    max_y + 0.05,
    center_z + (max_z - center_z) * 0.6
)

bpy.ops.mesh.primitive_plane_add(size=1, location=face_location)
face_plane = bpy.context.active_object
face_plane.name = "K4000_FaceScreen"
face_plane.scale = (face_width, face_height, 1)
face_plane.rotation_euler = (math.radians(90), 0, 0)

face_mat = bpy.data.materials.new(name="K4000_FaceScreen")
face_mat.use_nodes = True
bsdf = face_mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0, 0.4, 1, 1)
    bsdf.inputs["Emission Color"].default_value = (0, 0.4, 1, 1)
    bsdf.inputs["Emission Strength"].default_value = 6.0
    bsdf.inputs["Roughness"].default_value = 0.1
    bsdf.inputs["Metallic"].default_value = 0.0
if face_plane.data.materials:
    face_plane.data.materials[0] = face_mat
else:
    face_plane.data.materials.append(face_mat)

# Add eyes (two small emissive white spheres)
eye_radius = 0.02
eye_x_offset = 0.06
eye_y_offset = 0.0
eye_z_offset = 0.05

bpy.ops.mesh.primitive_uv_sphere_add(radius=eye_radius, location=(center_x - eye_x_offset, max_y + 0.06, face_location[2] + eye_z_offset))
left_eye = bpy.context.active_object
left_eye.name = "K4000_Eye_L"

bpy.ops.mesh.primitive_uv_sphere_add(radius=eye_radius, location=(center_x + eye_x_offset, max_y + 0.06, face_location[2] + eye_z_offset))
right_eye = bpy.context.active_object
right_eye.name = "K4000_Eye_R"

# Add mouth (torus)
bpy.ops.mesh.primitive_torus_add(major_radius=0.03, minor_radius=0.01, location=(center_x, max_y + 0.06, face_location[2] - eye_z_offset))
mouth = bpy.context.active_object
mouth.name = "K4000_Mouth"
mouth.rotation_euler = (math.radians(90), 0, 0)

# White emissive material for eyes and mouth
white_emissive = bpy.data.materials.new(name="K4000_WhiteEmissive")
white_emissive.use_nodes = True
white_bsdf = white_emissive.node_tree.nodes.get("Principled BSDF")
if white_bsdf:
    white_bsdf.inputs["Base Color"].default_value = (1, 1, 1, 1)
    white_bsdf.inputs["Emission Color"].default_value = (1, 1, 1, 1)
    white_bsdf.inputs["Emission Strength"].default_value = 8.0
for obj in [left_eye, right_eye, mouth]:
    if obj.data.materials:
        obj.data.materials[0] = white_emissive
    else:
        obj.data.materials.append(white_emissive)

# Create 4 neon rings
ring_material = bpy.data.materials.new(name="K4000_NeonRing")
ring_material.use_nodes = True
ring_bsdf = ring_material.node_tree.nodes.get("Principled BSDF")
if ring_bsdf:
    ring_bsdf.inputs["Base Color"].default_value = (0.0, 0.6, 1.0, 1)
    ring_bsdf.inputs["Emission Color"].default_value = (0.0, 0.6, 1.0, 1)
    ring_bsdf.inputs["Emission Strength"].default_value = 8.0
    ring_bsdf.inputs["Roughness"].default_value = 0.2

ring_radius = max((max_x - min_x), (max_y - min_y)) / 2 + 0.02
num_rings = 4
ring_z_positions = [min_z + (i+1) * ((max_z - min_z) / (num_rings+1)) for i in range(num_rings)]

for idx, z_pos in enumerate(ring_z_positions):
    bpy.ops.mesh.primitive_torus_add(
        major_radius=ring_radius,
        minor_radius=0.015,
        location=(center_x, center_y, z_pos)
    )
    ring_obj = bpy.context.active_object
    ring_obj.name = f"K4000_NeonRing_{idx+1}"
    if ring_obj.data.materials:
        ring_obj.data.materials[0] = ring_material
    else:
        ring_obj.data.materials.append(ring_material)

# Select all and export
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(
    filepath=output_path,
    export_format='GLB',
    use_selection=True,
    export_apply=False
)

print(f"Modified robot exported to {output_path}")import bpy
import os
import math

# Paths
input_path = "tesla_bot.glb"
output_dir = "assets"
output_path = os.path.join(output_dir, "robot_k4000.glb")
os.makedirs(output_dir, exist_ok=True)

# Clear default scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Import robot
bpy.ops.import_scene.gltf(filepath=input_path)

# Ensure object mode
bpy.ops.object.mode_set(mode='OBJECT')

# Get all mesh objects
mesh_objs = [obj for obj in bpy.context.scene.objects if obj.type == 'MESH']

def set_material_black(material):
    if not material:
        return
    principled = None
    if material.node_tree:
        for node in material.node_tree.nodes:
            if node.type == 'BSDF_PRINCIPLED':
                principled = node
                break
    if principled:
        if "Base Color" in principled.inputs:
            principled.inputs["Base Color"].default_value = (0.01, 0.01, 0.01, 1)
        if "Metallic" in principled.inputs:
            principled.inputs["Metallic"].default_value = 0.0
        if "Roughness" in principled.inputs:
            principled.inputs["Roughness"].default_value = 0.7
    else:
        material.diffuse_color = (0.01, 0.01, 0.01, 1)
        if hasattr(material, 'metallic'):
            material.metallic = 0.0
        if hasattr(material, 'roughness'):
            material.roughness = 0.7

# Apply black body material to all existing materials
for mat in bpy.data.materials:
    set_material_black(mat)

# Compute bounding box of all mesh objects in world space
min_x = min_y = min_z = float('inf')
max_x = max_y = max_z = float('-inf')
for obj in mesh_objs:
    for vert in obj.data.vertices:
        world_co = obj.matrix_world @ vert.co
        min_x = min(min_x, world_co.x)
        min_y = min(min_y, world_co.y)
        min_z = min(min_z, world_co.z)
        max_x = max(max_x, world_co.x)
        max_y = max(max_y, world_co.y)
        max_z = max(max_z, world_co.z)

if math.isinf(min_x):
    raise Exception("No mesh found in imported robot")

center_x = (min_x + max_x) / 2
center_y = (min_y + max_y) / 2
center_z = (min_z + max_z) / 2

# Create LED face screen
face_width = 0.3
face_height = 0.4
face_location = (
    center_x,
    max_y + 0.05,
    center_z + (max_z - center_z) * 0.6
)

bpy.ops.mesh.primitive_plane_add(size=1, location=face_location)
face_plane = bpy.context.active_object
face_plane.name = "K4000_FaceScreen"
face_plane.scale = (face_width, face_height, 1)
face_plane.rotation_euler = (math.radians(90), 0, 0)

face_mat = bpy.data.materials.new(name="K4000_FaceScreen")
face_mat.use_nodes = True
bsdf = face_mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0, 0.4, 1, 1)
    bsdf.inputs["Emission Color"].default_value = (0, 0.4, 1, 1)
    bsdf.inputs["Emission Strength"].default_value = 6.0
    bsdf.inputs["Roughness"].default_value = 0.1
    bsdf.inputs["Metallic"].default_value = 0.0
if face_plane.data.materials:
    face_plane.data.materials[0] = face_mat
else:
    face_plane.data.materials.append(face_mat)

# Add eyes (two small emissive white spheres)
eye_radius = 0.02
eye_x_offset = 0.06
eye_y_offset = 0.0
eye_z_offset = 0.05

bpy.ops.mesh.primitive_uv_sphere_add(radius=eye_radius, location=(center_x - eye_x_offset, max_y + 0.06, face_location[2] + eye_z_offset))
left_eye = bpy.context.active_object
left_eye.name = "K4000_Eye_L"

bpy.ops.mesh.primitive_uv_sphere_add(radius=eye_radius, location=(center_x + eye_x_offset, max_y + 0.06, face_location[2] + eye_z_offset))
right_eye = bpy.context.active_object
right_eye.name = "K4000_Eye_R"

# Add mouth (torus)
bpy.ops.mesh.primitive_torus_add(major_radius=0.03, minor_radius=0.01, location=(center_x, max_y + 0.06, face_location[2] - eye_z_offset))
mouth = bpy.context.active_object
mouth.name = "K4000_Mouth"
mouth.rotation_euler = (math.radians(90), 0, 0)

# White emissive material for eyes and mouth
white_emissive = bpy.data.materials.new(name="K4000_WhiteEmissive")
white_emissive.use_nodes = True
white_bsdf = white_emissive.node_tree.nodes.get("Principled BSDF")
if white_bsdf:
    white_bsdf.inputs["Base Color"].default_value = (1, 1, 1, 1)
    white_bsdf.inputs["Emission Color"].default_value = (1, 1, 1, 1)
    white_bsdf.inputs["Emission Strength"].default_value = 8.0
for obj in [left_eye, right_eye, mouth]:
    if obj.data.materials:
        obj.data.materials[0] = white_emissive
    else:
        obj.data.materials.append(white_emissive)

# Create 4 neon rings
ring_material = bpy.data.materials.new(name="K4000_NeonRing")
ring_material.use_nodes = True
ring_bsdf = ring_material.node_tree.nodes.get("Principled BSDF")
if ring_bsdf:
    ring_bsdf.inputs["Base Color"].default_value = (0.0, 0.6, 1.0, 1)
    ring_bsdf.inputs["Emission Color"].default_value = (0.0, 0.6, 1.0, 1)
    ring_bsdf.inputs["Emission Strength"].default_value = 8.0
    ring_bsdf.inputs["Roughness"].default_value = 0.2

ring_radius = max((max_x - min_x), (max_y - min_y)) / 2 + 0.02
num_rings = 4
ring_z_positions = [min_z + (i+1) * ((max_z - min_z) / (num_rings+1)) for i in range(num_rings)]

for idx, z_pos in enumerate(ring_z_positions):
    bpy.ops.mesh.primitive_torus_add(
        major_radius=ring_radius,
        minor_radius=0.015,
        location=(center_x, center_y, z_pos)
    )
    ring_obj = bpy.context.active_object
    ring_obj.name = f"K4000_NeonRing_{idx+1}"
    if ring_obj.data.materials:
        ring_obj.data.materials[0] = ring_material
    else:
        ring_obj.data.materials.append(ring_material)

# Select all and export
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(
    filepath=output_path,
    export_format='GLB',
    use_selection=True,
    export_apply=False
)

print(f"Modified robot exported to {output_path}")
