import os
from importlib import reload
from math import pi, sin, cos
from random import random

from bpy import context, data, ops

from . import parameters
from . import loader
from .loader import export_view, export_matrix, export_model_parameters, create_directory
from .stdout_utils import suppress_stdout_stderr

reload(parameters)
reload(loader)


def noise(value):
    return value * (random() - 0.5)


class Renderer:

    def __init__(self):
        self.scene = context.scene
        self.settings = context.scene.render

        # Rendering options
        self.settings.use_overwrite = True
        self.settings.use_placeholder = True
        self.settings.use_file_extension = True
        self.settings.resolution_percentage = parameters.OUTPUT_RESOLUTION
        self.scene.render.resolution_x = parameters.RESOLUTION_X
        self.scene.render.resolution_y = parameters.RESOLUTION_Y
        self.scene.render.use_file_extension = True
        self.scene.render.use_placeholder = True

        self.settings.image_settings.file_format = 'OPEN_EXR'
        self.settings.image_settings.color_depth = '16'
        self.settings.image_settings.use_zbuffer = True
        self.settings.image_settings.use_preview = False

        self.scene.frame_start = parameters.START_FRAME
        self.scene.frame_end = parameters.END_FRAME
        self.scene.world.node_tree.nodes["Background"].inputs[0].default_value = (0.5, 0.5, 0.5, 1.0)

        # Switch on nodes
        self.scene.use_nodes = True
        tree = self.scene.node_tree
        links = tree.links

        # Clear default nodes
        for n in tree.nodes:
            tree.nodes.remove(n)

        # Basic Node configuration
        render_node = tree.nodes.new('CompositorNodeRLayers')
        composite_node = tree.nodes.new('CompositorNodeComposite')

        links.new(render_node.outputs['Image'], composite_node.inputs['Image'])
        links.new(render_node.outputs['Depth'], composite_node.inputs['Z'])

    def render(self, camera, model, path, update_views=parameters.UPDATE_VIEWS):

        create_directory(path)

        self.scene.camera = camera.camera

        samples = parameters.CAMERAS_NUMBER
        for i in range(samples):

            camera_name = 'camera_' + str(i + 1)

            create_directory(os.path.join(path, camera_name))

            # Generate semi random positions
            angle = 2 * pi * i / samples  # + noise(radians(parameters.YAW_NOISE))
            distance = parameters.DISTANCE  # + noise(parameters.DISTANCE_NOISE)
            height = parameters.HEIGHT  # + 2 * abs(noise(parameters.HEIGHT_NOISE))

            x = distance * cos(angle)
            y = distance * sin(angle)
            z = height

            camera.move_to((x, y, z), target=model)

            # export camera pose and intrinsic parameters
            pose_matrix = camera.get_pose_matrix()
            export_matrix(pose_matrix, os.path.join(path, camera_name), 'pose')

            intrinsic = camera.get_intrinsics_matrix()
            export_matrix(intrinsic, os.path.join(path, camera_name), 'intrinsic')

            if update_views:
                # export background
                for obj in data.objects:
                    obj.hide_render = True

                export_view(os.path.join(path, camera_name, 'background'))

                for obj in data.objects:
                    if model.name.lower() in obj.name:
                        obj.hide_render = False

                # export camera views
                for frame in range(self.scene.frame_start, self.scene.frame_end + 1):
                    self.scene.frame_set(frame)
                    export_model_parameters(data.objects[model.name].pose.bones["hip"],
                                            os.path.join(path, camera_name), str(frame))
                    export_view(os.path.join(path, camera_name, str(frame)))

                for obj in data.objects:
                    obj.hide_render = False

        print('View extraction completed Successfully\n\n')

    def retarget(self, model, animation):

        model.hide_viewport = False
        animation.hide_viewport = False

        with suppress_stdout_stderr():
            self.scene.rsl_retargeting_armature_source = animation
            self.scene.rsl_retargeting_armature_target = model

            self.scene.rsl_retargeting_auto_scaling = True
            self.scene.rsl_retargeting_use_pose = 'REST'

            ops.rsl.build_bone_list()
            ops.rsl.retarget_animation()

        print('Retargeted ' + animation.name + ' animation')

