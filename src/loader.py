from math import degrees
from bpy import context, ops, data
import os
from pathlib import Path
from .parameters import MODEL_FILE_HEADER
from . import camera_utils
from importlib import reload
from .csv_utils import csv_setup

reload(camera_utils)

# PATH TO REPOSITORY
PATH = Path(data.filepath).parent


def create_directory(name):
    training_directory = os.path.join(PATH, 'training', name)

    if not os.path.exists(training_directory):
        os.makedirs(training_directory)

    test_directory = os.path.join(PATH, 'test', name)

    if not os.path.exists(test_directory):
        os.makedirs(test_directory)


def import_model(name, extension='obj'):
    model_path = os.path.join(PATH, 'models', name, name + '.' + extension)

    if extension == 'fbx':
        ops.import_scene.fbx(filepath=model_path)

    if extension == 'obj':
        ops.import_scene.obj(filepath=model_path, axis_up='Z', axis_forward='Y')


def save_model(model, extension='obj'):
    # Save model parameters
    file = open(os.path.join(PATH, 'test', model.name, 'model.csv'), 'w')
    save_model_parameters(file, model)

    # Generate Mesh
    context.view_layer.objects.active = model
    path = os.path.join(PATH, 'test', model.name, 'groundtruth.' + extension)

    if extension == 'glb':
        ops.export_scene.gltf(filepath=path, export_draco_mesh_compression_enable=True)

    elif extension == 'obj':
        ops.export_scene.obj(filepath=path)


def save_blender_image(camera, file_path):
    context.scene.render.filepath = file_path
    context.scene.camera = camera
    ops.render.render(animation=False, write_still=True)


def save_model_parameters(file, model):
    writer = csv_setup(file, MODEL_FILE_HEADER)

    location = [coordinate for coordinate in model.location]
    rotation = [degrees(angle) for angle in model.rotation_euler]
    scale = [scale for scale in model.scale]
    dimensions = [dimension for dimension in model.dimensions]

    writer.writerow([model.name, location, rotation, scale, dimensions])
    file.flush()


def save_camera_intrinsics(file):
    writer = csv_setup(file, ['Camera Intrinsics'])

    intrinsics = camera_utils.get_calibration_matrix()

    writer.writerow([intrinsics])
    file.flush()


def save_camera_parameters(frame, camera, writer, file):
    location = [coordinate for coordinate in camera.location]
    rotation = [degrees(angle) for angle in camera.rotation_euler]
    fov = degrees(camera.data.angle)

    pose_matrix = camera_utils.get_pose_matrix(camera).flatten().tolist()

    writer.writerow([frame, location, rotation, fov, pose_matrix])
    file.flush()

