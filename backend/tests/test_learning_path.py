"""Unit tests for taxonomy-based learning path recommendations."""

import json
import sys
from pathlib import Path

import pytest

backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

import backend.app.services.learning_path_engine as learning_path_module


class DummyEmbeddingService:
    def generate_embedding(self, _: str):
        return [0.1, 0.2, 0.3]


@pytest.fixture
def service(monkeypatch):
    monkeypatch.setattr(
        learning_path_module,
        "get_embedding_service",
        lambda: DummyEmbeddingService(),
    )
    return learning_path_module.LearningPathService()


def _machine_learning_candidates():
    return [
        {"skill_name": "Deep Learning", "skill_category": "Machine Learning", "similarity": 0.69},
        {"skill_name": "Neural Networks", "skill_category": "Machine Learning", "similarity": 0.68},
        {"skill_name": "Reinforcement Learning", "skill_category": "Machine Learning", "similarity": 0.64},
        {"skill_name": "Natural Language Processing", "skill_category": "Natural Language Processing", "similarity": 0.62},
        {"skill_name": "Computer Vision", "skill_category": "Computer Vision", "similarity": 0.61},
        {"skill_name": "Data Science", "skill_category": "Data Science", "similarity": 0.56},
        {"skill_name": "Data Analysis", "skill_category": "Data Science", "similarity": 0.52},
        {"skill_name": "Data Mining", "skill_category": "Data Science", "similarity": 0.59},
        {"skill_name": "Big Data", "skill_category": "Data Science", "similarity": 0.58},
        {"skill_name": "Data Warehousing", "skill_category": "Data Science", "similarity": 0.55},
    ]


def test_prerequisites_are_ancestors(service, monkeypatch):
    monkeypatch.setattr(service, "_fetch_related", lambda *_: _machine_learning_candidates())

    result = service.get_learning_path("Machine Learning", "intermediate")
    pre_names = [item["skill_name"].lower() for item in result["prerequisites"]]

    assert "data science" in pre_names
    assert any(name in pre_names for name in ["data analysis", "statistics"])


def test_complementary_comes_from_siblings_or_cousins(service, monkeypatch):
    monkeypatch.setattr(service, "_fetch_related", lambda *_: _machine_learning_candidates())

    result = service.get_learning_path("Machine Learning", "intermediate")
    comp_names = [item["skill_name"].lower() for item in result["complementary"]]

    assert any(name in comp_names for name in ["big data", "data mining", "data warehousing", "data engineering"])


def test_next_level_prefers_children(service, monkeypatch):
    monkeypatch.setattr(service, "_fetch_related", lambda *_: _machine_learning_candidates())

    result = service.get_learning_path("Machine Learning", "intermediate")
    next_names = [item["skill_name"].lower() for item in result["next_level"]]

    assert any(name in next_names for name in ["deep learning", "natural language processing", "computer vision"])


def test_user_level_controls_ancestor_depth(service, monkeypatch):
    monkeypatch.setattr(service, "_fetch_related", lambda *_: _machine_learning_candidates())

    beginner = service.get_learning_path("Machine Learning", "beginner")
    expert = service.get_learning_path("Machine Learning", "expert")

    assert len(beginner["prerequisites"]) >= len(expert["prerequisites"])


def test_smoke_print_taxonomy_learning_paths(service, monkeypatch):
    monkeypatch.setattr(service, "_fetch_related", lambda *_: _machine_learning_candidates())

    machine_learning_path = service.get_learning_path("Machine Learning", "intermediate")
    data_science_path = service.get_learning_path("Data Science", "intermediate")

    print("\nMachine Learning taxonomy path:")
    print(json.dumps(machine_learning_path, indent=2))
    print("\nData Science taxonomy path:")
    print(json.dumps(data_science_path, indent=2))

    assert machine_learning_path["skill"] == "Machine Learning"
    assert data_science_path["skill"] == "Data Science"


def test_data_science_prerequisites_exclude_software_engineering_noise(service, monkeypatch):
    candidates = [
        {"skill_name": "Data Analysis", "skill_category": None, "similarity": 0.669},
        {"skill_name": "Data Structures", "skill_category": "Software Engineering", "similarity": 0.561},
        {"skill_name": "Big Data", "skill_category": "Data Science", "similarity": 0.625},
        {"skill_name": "Data Mining", "skill_category": "Data Science", "similarity": 0.599},
        {"skill_name": "Machine Learning", "skill_category": "Data Science", "similarity": 0.532},
        {"skill_name": "Data Visualization", "skill_category": "Data Science", "similarity": 0.491},
        {"skill_name": "Feature Engineering", "skill_category": "Machine Learning", "similarity": 0.447},
    ]
    monkeypatch.setattr(service, "_fetch_related", lambda *_: candidates)

    result = service.get_learning_path("Data Science", "intermediate")
    pre_names = [item["skill_name"].lower() for item in result["prerequisites"]]

    assert "data structures" not in pre_names
