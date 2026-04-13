"""Pytest configuration and shared fixtures for API tests"""

import copy
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Provide a FastAPI TestClient for making requests"""
    return TestClient(app)


def create_activity(
    name: str = "Test Activity",
    description: str = "A test activity",
    schedule: str = "Monday, 3:00 PM - 4:00 PM",
    max_participants: int = 10,
    participants: list = None,
) -> dict:
    """Factory function to create activity data with sensible defaults
    
    Args:
        name: Activity name
        description: Activity description
        schedule: Meeting schedule
        max_participants: Maximum participant capacity
        participants: List of participant email addresses
    
    Returns:
        A dictionary representing an activity
    """
    if participants is None:
        participants = []
    
    return {
        "description": description,
        "schedule": schedule,
        "max_participants": max_participants,
        "participants": participants.copy(),
    }


@pytest.fixture
def clean_activities():
    """Fixture that provides isolated, clean activities state for each test
    
    This fixture returns a fresh copy of the activities dict so tests
    don't interfere with each other. It resets the global activities
    dict to a clean state before yielding to the test.
    
    Yields:
        The global activities dict (fresh copy)
    """
    # Store original activities
    original = copy.deepcopy(activities)
    
    # Clear and set up clean test state
    activities.clear()
    activities.update({
        "Chess Club": create_activity(
            name="Chess Club",
            description="Learn strategies and compete in chess tournaments",
            schedule="Fridays, 3:30 PM - 5:00 PM",
            max_participants=12,
            participants=["existing@mergington.edu"],
        ),
        "Programming Class": create_activity(
            name="Programming Class",
            description="Learn programming fundamentals and build software projects",
            schedule="Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            max_participants=20,
            participants=[],
        ),
    })
    
    yield activities
    
    # Restore original activities after test
    activities.clear()
    activities.update(original)


@pytest.fixture
def sample_activity_data():
    """Provide sample activity data for tests"""
    return {
        "Chess Club": create_activity(
            name="Chess Club",
            description="Learn strategies and compete in chess tournaments",
            schedule="Fridays, 3:30 PM - 5:00 PM",
            max_participants=12,
            participants=["existing@mergington.edu"],
        ),
        "Programming Class": create_activity(
            name="Programming Class",
            description="Learn programming fundamentals and build software projects",
            schedule="Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            max_participants=20,
            participants=[],
        ),
    }


@pytest.fixture
def test_student_email():
    """Provide a test student email that won't collide with defaults"""
    return "newstudent@mergington.edu"


@pytest.fixture
def existing_student_email():
    """Provide an email for a student already registered in test data"""
    return "existing@mergington.edu"
