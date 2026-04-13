"""Unit tests for Activities API endpoints"""

import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client, clean_activities):
        """Verify GET /activities returns all activities"""
        # Arrange
        expected_activity_count = 2

        # Act
        response = client.get("/activities")

        # Assert
        assert response.status_code == 200
        activities_data = response.json()
        assert len(activities_data) == expected_activity_count
        assert "Chess Club" in activities_data
        assert "Programming Class" in activities_data

    def test_get_activities_returns_correct_structure(self, client, clean_activities):
        """Verify GET /activities returns activities with correct structure"""
        # Arrange
        required_keys = {"description", "schedule", "max_participants", "participants"}

        # Act
        response = client.get("/activities")
        activities_data = response.json()

        # Assert
        assert response.status_code == 200
        for activity_name, activity_data in activities_data.items():
            assert isinstance(activity_name, str)
            assert isinstance(activity_data, dict)
            assert required_keys.issubset(set(activity_data.keys()))
            assert isinstance(activity_data["participants"], list)
            assert isinstance(activity_data["max_participants"], int)

    def test_get_activities_includes_participant_count(self, client, clean_activities):
        """Verify activities include participant information"""
        # Arrange
        # Act
        response = client.get("/activities")
        activities_data = response.json()

        # Assert
        assert response.status_code == 200
        chess_club = activities_data["Chess Club"]
        assert len(chess_club["participants"]) == 1
        assert "existing@mergington.edu" in chess_club["participants"]


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self, client, clean_activities, test_student_email):
        """Verify successful signup returns success message"""
        # Arrange
        activity_name = "Programming Class"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={test_student_email}"
        )

        # Assert
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert test_student_email in result["message"]
        assert activity_name in result["message"]

    def test_signup_adds_participant_to_list(self, client, clean_activities, test_student_email):
        """Verify signup actually adds participant to activity"""
        # Arrange
        activity_name = "Programming Class"

        # Act
        client.post(f"/activities/{activity_name}/signup?email={test_student_email}")
        response = client.get("/activities")

        # Assert
        activities_data = response.json()
        assert test_student_email in activities_data[activity_name]["participants"]

    def test_signup_activity_not_found(self, client, clean_activities, test_student_email):
        """Verify signup with nonexistent activity returns 404"""
        # Arrange
        nonexistent_activity = "Nonexistent Activity"

        # Act
        response = client.post(
            f"/activities/{nonexistent_activity}/signup?email={test_student_email}"
        )

        # Assert
        assert response.status_code == 404
        result = response.json()
        assert "Activity not found" in result["detail"]

    def test_signup_already_registered(self, client, clean_activities, existing_student_email):
        """Verify duplicate signup returns 400 error"""
        # Arrange
        activity_name = "Chess Club"  # existing_student_email is already signed up for this

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup?email={existing_student_email}"
        )

        # Assert
        assert response.status_code == 400
        result = response.json()
        assert "already signed up" in result["detail"].lower()

    def test_signup_multiple_students_same_activity(self, client, clean_activities):
        """Verify multiple students can signup for the same activity"""
        # Arrange
        activity_name = "Programming Class"
        student1 = "student1@mergington.edu"
        student2 = "student2@mergington.edu"

        # Act
        response1 = client.post(f"/activities/{activity_name}/signup?email={student1}")
        response2 = client.post(f"/activities/{activity_name}/signup?email={student2}")

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity_name]["participants"]
        assert student1 in participants
        assert student2 in participants

    def test_signup_increments_participant_count(self, client, clean_activities):
        """Verify participant count increases after signup"""
        # Arrange
        activity_name = "Chess Club"
        response_before = client.get("/activities")
        count_before = len(response_before.json()[activity_name]["participants"])

        # Act
        client.post(f"/activities/{activity_name}/signup?email=new@mergington.edu")

        # Assert
        response_after = client.get("/activities")
        count_after = len(response_after.json()[activity_name]["participants"])
        assert count_after == count_before + 1


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self, client, clean_activities, existing_student_email):
        """Verify successful unregister returns success message"""
        # Arrange
        activity_name = "Chess Club"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={existing_student_email}"
        )

        # Assert
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert "Unregistered" in result["message"]

    def test_unregister_removes_participant(self, client, clean_activities, existing_student_email):
        """Verify unregister actually removes participant from activity"""
        # Arrange
        activity_name = "Chess Club"

        # Act
        client.delete(
            f"/activities/{activity_name}/unregister?email={existing_student_email}"
        )
        response = client.get("/activities")

        # Assert
        activities_data = response.json()
        assert existing_student_email not in activities_data[activity_name]["participants"]

    def test_unregister_activity_not_found(self, client, clean_activities):
        """Verify unregister with nonexistent activity returns 404"""
        # Arrange
        nonexistent_activity = "Nonexistent Activity"
        student_email = "student@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{nonexistent_activity}/unregister?email={student_email}"
        )

        # Assert
        assert response.status_code == 404
        result = response.json()
        assert "Activity not found" in result["detail"]

    def test_unregister_student_not_registered(self, client, clean_activities):
        """Verify unregister for non-registered student returns 400"""
        # Arrange
        activity_name = "Programming Class"  # No one is registered for this
        student_email = "unregistered@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister?email={student_email}"
        )

        # Assert
        assert response.status_code == 400
        result = response.json()
        assert "not registered" in result["detail"].lower()

    def test_unregister_decrements_participant_count(self, client, clean_activities, existing_student_email):
        """Verify participant count decreases after unregister"""
        # Arrange
        activity_name = "Chess Club"
        response_before = client.get("/activities")
        count_before = len(response_before.json()[activity_name]["participants"])

        # Act
        client.delete(
            f"/activities/{activity_name}/unregister?email={existing_student_email}"
        )

        # Assert
        response_after = client.get("/activities")
        count_after = len(response_after.json()[activity_name]["participants"])
        assert count_after == count_before - 1
