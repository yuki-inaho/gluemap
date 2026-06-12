import numpy as np
import pycolmap

from gluemap.math.reprojection_error import (
    ReprojectionErrorType,
    _compute_errors_batch,
    compute_point_error,
)


def _pinhole_camera() -> pycolmap.Camera:
    camera = pycolmap.Camera.create_from_model_id(
        1, pycolmap.CameraModelId.PINHOLE, 1.0, 800, 600
    )
    camera.focal_length_x = 200.0
    camera.focal_length_y = 400.0
    camera.principal_point_x = 400.0
    camera.principal_point_y = 300.0
    return camera


def test_normalized_point_error_handles_pinhole_camera():
    camera = _pinhole_camera()
    world_point = np.array([0.0, 0.0, 2.0])
    observed = np.array([430.0, 340.0])

    error = compute_point_error(
        world_point,
        np.eye(3),
        np.zeros(3),
        observed,
        camera,
        ReprojectionErrorType.NORMALIZED,
    )

    assert error == np.hypot(30.0, 40.0) / 300.0


def test_normalized_batch_error_handles_pinhole_camera():
    camera = _pinhole_camera()
    x_cam = np.array([[0.0, 0.0, 2.0]])
    observed = np.array([[430.0, 340.0]])

    errors = _compute_errors_batch(
        x_cam,
        observed,
        camera,
        np.array([False]),
        ReprojectionErrorType.NORMALIZED,
    )

    np.testing.assert_allclose(errors, [np.hypot(30.0, 40.0) / 300.0])
