import pytest

from gluemap.math.reprojection_error import _representative_focal_length


class _ScalarFocalCamera:
    focal_length = 700.0
    params = [700.0, 320.0, 240.0]


class _TwoFocalCamera:
    params = [800.0, 1000.0, 320.0, 240.0]

    @property
    def focal_length(self):
        raise ValueError("camera model has two focal parameters")


def test_representative_focal_length_uses_scalar_accessor():
    assert _representative_focal_length(_ScalarFocalCamera()) == 700.0


def test_representative_focal_length_averages_fx_fy_for_pinhole_like_camera():
    assert _representative_focal_length(_TwoFocalCamera()) == 900.0


def test_representative_focal_length_rejects_empty_params():
    class EmptyCamera:
        params = []

        @property
        def focal_length(self):
            raise ValueError("no scalar focal")

    with pytest.raises(ValueError, match="no focal"):
        _representative_focal_length(EmptyCamera())
