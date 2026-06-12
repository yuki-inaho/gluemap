import numpy as np
import pycolmap

from gluemap.utils import colmap as colmap_utils


def test_prepare_feature_database_uses_aliked_lightglue_sequential(
    tmp_path, monkeypatch
):
    calls = {}

    def fake_extract_features(
        database_path,
        images_path,
        image_names,
        camera_mode,
        reader_options,
        extraction_options,
    ):
        calls["extract"] = {
            "database_path": database_path,
            "images_path": images_path,
            "image_names": image_names,
            "camera_model": reader_options.camera_model,
            "extractor_type": extraction_options.type,
        }

    def fake_match_sequential(
        database_path, matching_options, pairing_options
    ):
        calls["match"] = {
            "database_path": database_path,
            "matcher_type": matching_options.type,
            "overlap": pairing_options.overlap,
            "quadratic_overlap": pairing_options.quadratic_overlap,
        }

    monkeypatch.setattr(pycolmap, "extract_features", fake_extract_features)
    monkeypatch.setattr(pycolmap, "match_sequential", fake_match_sequential)
    monkeypatch.setattr(pycolmap.Database, "open", lambda _path: object())
    monkeypatch.setattr(
        colmap_utils, "remap_cameras_to_intrinsics", lambda *_args: None
    )

    colmap_utils.prepare_sift_database(
        str(tmp_path),
        "/images",
        ["frame_00001.jpg", "frame_00002.jpg"],
        {0: 0, 1: 0},
        np.array([[0, 1]], dtype=int),
        device="cpu",
        camera_model="PINHOLE",
        feature_extractor="ALIKED_N16ROT",
        feature_matcher="ALIKED_LIGHTGLUE",
        feature_pairing="sequential",
        feature_backend="pycolmap",
        sequential_overlap=4,
        sequential_quadratic_overlap=False,
    )

    assert calls["extract"]["database_path"] == str(
        tmp_path / "database_sift.db"
    )
    assert calls["extract"]["image_names"] == [
        "frame_00001.jpg",
        "frame_00002.jpg",
    ]
    assert calls["extract"]["camera_model"] == "PINHOLE"
    assert (
        calls["extract"]["extractor_type"]
        == pycolmap.FeatureExtractorType.ALIKED_N16ROT
    )
    assert (
        calls["match"]["matcher_type"]
        == pycolmap.FeatureMatcherType.ALIKED_LIGHTGLUE
    )
    assert calls["match"]["overlap"] == 4
    assert calls["match"]["quadratic_overlap"] is False


def test_prepare_feature_database_keeps_imported_pairs_path(
    tmp_path, monkeypatch
):
    calls = {}

    def fake_extract_features(*_args, **_kwargs):
        return None

    def fake_match_image_pairs(
        database_path, matching_options, pairing_options
    ):
        calls["database_path"] = database_path
        calls["matcher_type"] = matching_options.type
        calls["match_list_path"] = pairing_options.match_list_path

    monkeypatch.setattr(pycolmap, "extract_features", fake_extract_features)
    monkeypatch.setattr(pycolmap, "match_image_pairs", fake_match_image_pairs)
    monkeypatch.setattr(pycolmap.Database, "open", lambda _path: object())
    monkeypatch.setattr(
        colmap_utils, "remap_cameras_to_intrinsics", lambda *_args: None
    )

    colmap_utils.prepare_sift_database(
        str(tmp_path),
        "/images",
        ["a.jpg", "b.jpg", "c.jpg"],
        {0: 0, 1: 0, 2: 0},
        np.array([[0, 1], [1, 2]], dtype=int),
        device="cpu",
        feature_extractor="SIFT",
        feature_pairing="imported",
        feature_backend="pycolmap",
    )

    pairs_path = tmp_path / "pairs.txt"
    assert calls["database_path"] == str(tmp_path / "database_sift.db")
    assert calls["matcher_type"] == pycolmap.FeatureMatcherType.SIFT_BRUTEFORCE
    assert calls["match_list_path"] == pairs_path
    assert set(pairs_path.read_text().splitlines()) == {
        "a.jpg b.jpg",
        "b.jpg c.jpg",
    }


def test_aliked_auto_backend_uses_colmap_cli(tmp_path, monkeypatch):
    calls = {}

    def fake_prepare_with_cli(
        dir_write,
        images_path,
        images_list,
        intrinsics_mapping,
        database_dir,
        camera_model,
        extractor_type,
        matcher_type,
        pairing_mode,
        use_gpu,
        gpu_index,
        sequential_overlap,
        sequential_quadratic_overlap,
    ):
        calls["cli"] = {
            "dir_write": dir_write,
            "images_path": images_path,
            "images_list": images_list,
            "intrinsics_mapping": intrinsics_mapping,
            "database_dir": database_dir,
            "camera_model": camera_model,
            "extractor_type": extractor_type,
            "matcher_type": matcher_type,
            "pairing_mode": pairing_mode,
            "use_gpu": use_gpu,
            "gpu_index": gpu_index,
            "sequential_overlap": sequential_overlap,
            "sequential_quadratic_overlap": sequential_quadratic_overlap,
        }

    monkeypatch.setattr(
        colmap_utils,
        "_prepare_feature_database_with_colmap_cli",
        fake_prepare_with_cli,
    )
    monkeypatch.setattr(pycolmap.Database, "open", lambda _path: object())
    monkeypatch.setattr(
        colmap_utils, "remap_cameras_to_intrinsics", lambda *_args: None
    )

    colmap_utils.prepare_sift_database(
        str(tmp_path),
        "/images",
        ["a.jpg", "b.jpg"],
        {0: 0, 1: 0},
        np.array([[0, 1]], dtype=int),
        device="cuda:2",
        feature_extractor="aliked",
        feature_pairing="sequential",
        sequential_overlap=3,
    )

    assert calls["cli"]["database_dir"] == str(tmp_path / "database_sift.db")
    assert (
        calls["cli"]["extractor_type"]
        == pycolmap.FeatureExtractorType.ALIKED_N16ROT
    )
    assert (
        calls["cli"]["matcher_type"]
        == pycolmap.FeatureMatcherType.ALIKED_LIGHTGLUE
    )
    assert calls["cli"]["pairing_mode"] == "SEQUENTIAL"
    assert calls["cli"]["use_gpu"] is True
    assert calls["cli"]["gpu_index"] == "2"
    assert calls["cli"]["sequential_overlap"] == 3
