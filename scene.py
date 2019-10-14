import os, csv
from math import pi, sin, cos, radians, degrees
from bpy import context, data, ops

# CONFIGURATION PARAMETERS

# TODO set relative path
PATH = '/Users/giovanni/Developer/blender-scene'
# PATH = './'

# CAMERAS SETTINGS
CAMERAS = 8
DISTANCE: float = 5
FOV: float = 65

# RENDERING SETTINGS
OUTPUT_RESOLUTION = 10
START_FRAME = 0
END_FRAME = 250


def main():
    for directory in os.listdir(os.path.join(PATH, 'models')):
        if os.path.isdir(os.path.join(PATH, 'models', directory)):

            for file in os.listdir(os.path.join(PATH, 'models', directory)):
                if file.endswith('.fbx'):
                    name = os.path.splitext(file)[0]
                    print('\n\n\nRendering the following model:', name)

                    clear_scene()
                    add_lights()
                    add_plane()

                    model = add_model(name)

                    setup_cameras(model)
                    save_cameras(model)
                    # render(model)


def clear_scene():
    # Clear data from previous scenes
    if data:
        for item in data.objects:
            data.objects.remove(item)

        for item in data.meshes:
            data.meshes.remove(item)

        for material in data.materials:
            data.materials.remove(material)

        for texture in data.textures:
            data.textures.remove(texture)

    ops.screen.frame_jump(end=False)


def add_lights():
    ops.object.light_add(type='SUN', radius=1, location=(DISTANCE / 4, DISTANCE / 8, DISTANCE / 2))


def add_plane():
    ops.mesh.primitive_circle_add(vertices=128, radius=DISTANCE, fill_type='NGON', location=(0, 0, 0))


def add_model(name):
    path = os.path.join(PATH, 'models', name, name + '.fbx')
    ops.import_scene.fbx(filepath=path)
    model = context.active_object
    model.name = name
    model.show_bounds
    ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME', center='MEDIAN')

    return model


def setup_cameras(model):
    for i in range(CAMERAS):
        angle = i * 2 * pi / CAMERAS
        x = DISTANCE * cos(angle)
        y = DISTANCE * sin(angle)

        # Adding Camera
        ops.object.camera_add(enter_editmode=False, align='VIEW', location=(x, y, model.location[2]),
                              rotation=(0.0, 0.0, 0.0))

        camera = context.active_object
        camera.name = 'camera' + str(i)
        camera.data.angle = radians(FOV)

        # Camera constraint to look at model
        ops.object.constraint_add(type='DAMPED_TRACK')
        tracking = camera.constraints[0]
        tracking.target = data.objects[model.name]
        tracking.track_axis = 'TRACK_NEGATIVE_Z'
        # tracking.up_axis = 'UP_Y'

        ops.transform.transform(mode='ALIGN')


def node_setup():
    # switch on nodes
    context.scene.use_nodes = True
    tree = context.scene.node_tree
    links = tree.links

    # clear default nodes
    for n in tree.nodes:
        tree.nodes.remove(n)

    # Basic Node configuration
    render_node = tree.nodes.new('CompositorNodeRLayers')
    composite_node = tree.nodes.new('CompositorNodeComposite')

    links.new(render_node.outputs['Image'], composite_node.inputs['Image'])
    links.new(render_node.outputs['Depth'], composite_node.inputs['Z'])


def render(model):
    # Rendering options
    context.scene.render.use_overwrite = True
    context.scene.render.use_placeholder = True
    context.scene.render.use_file_extension = True
    context.scene.render.resolution_percentage = OUTPUT_RESOLUTION

    context.scene.frame_start = START_FRAME
    context.scene.frame_end = END_FRAME - 1

    context.scene.render.image_settings.file_format = 'OPEN_EXR'
    context.scene.render.image_settings.use_zbuffer = True
    context.scene.render.image_settings.use_preview = False

    node_setup()

    for i in range(CAMERAS):
        camera = data.objects['camera' + str(i)]
        context.scene.render.filepath = os.path.join(PATH, 'rendering', model.name, camera.name, 'render' + '_')
        context.scene.camera = camera
        ops.render.render(animation=False, write_still=True)

    print('Rendering completed Successfully')


def save_cameras(model):
    file = os.path.join(PATH, 'rendering', model.name, 'cameras.csv')
    writer = csv.writer(open(file, 'w'))

    header = ['Name', 'Position', 'Quaternion', 'Fov']
    writer.writerow(header)

    for i in range(CAMERAS):
        camera = data.objects['camera' + str(i)]
        position = [coordinate for coordinate in camera.location]
        rotation = [degrees(direction) for direction in camera.rotation_quaternion]
        writer.writerow([camera.name, position, rotation, FOV])

    print('File written Successfully')


main()
