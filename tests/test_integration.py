"""Integration tests for Activities API workflows"""

import pytest


class TestSignupAndVerifyFlow:
    """Tests for signup followed by verification"""

    def test_signup_then_get_activities_shows_new_participant(
        self, client, clean_activities, test_student_email
    ):
        """Verify new participant appears in GET /activities after signup"""
        # Arrange
        activity_name = "Chess Club"

        # Act
        signup_response = client.post(
            f"/activities/{activity_name}/signup?email={test_student_email}"
        )
        get_response = client.get("/activities")

        # Assert
        assert signup_response.status_code == 200
        assert get_response.status_code == 200
        activities_data = get_response.json()
        assert test_student_email in activities_data[activity_name]["participants"]

    def test_signup_increments_visible_count(
        self, client, clean_activities, test_student_email
    ):
        """Verify participant count updates in GET response after signup"""
        # Arrange
        activity_name = "Programming Class"
        get_before = client.get("/activities")
        count_before = len(get_before.json()[activity_name]["participants"])

        # Act
        client.post(f"/activities/{activity_name}/signup?email={test_student_email}")
        get_after = client.get("/activities")

        # Assert
        count_after = len(get_after.json()[activity_name]["participants"])
        assert count_after == count_before + 1
        assert test_student_email in get_after.json()[activity_name]["participants"]


class TestMultipleActivities:
    """Tests for students signing up for multiple activities"""

    def test_same_student_signup_different_activities(self, client, clean_activities):
        """Verify same student can signup for different activities"""
        # Arrange
        student_email = "versatile@mergington.edu"
        activity1 = "Chess Club"
        activity2 = "Programming Class"

        # Act
        response1 = client.post(f"/activities/{activity1}/signup?email={student_email}")
        response2 = client.post(f"/activities/{activity2}/signup?email={student_email}")

        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200

        get_response = client.get("/activities")
        activities_data = get_response.json()
        assert student_email in activities_data[activity1]["participants"]
        assert student_email in activities_data[activity2]["participants"]

    def test_same_student_cannot_signup_twice_same_activity(
        self, client, clean_activities, test_student_email
    ):
        """Verify same student cannot signup twice for the same activity"""
        # Arrange
        activity_name = "Programming Class"

        # Act
        first_signup = client.post(
            f"/activities/{activity_name}/signup?email={test_student_email}"
        )
        duplicate_signup = client.post(
            f"/activities/{activity_name}/signup?email={test_student_email}"
        )

        # Assert
        assert first_signup.status_code == 200
        assert duplicate_signup.status_code == 400
        assert "already signed up" in duplicate_signup.json()["detail"].lower()

        # Verify participant list has only one instance
        get_response = client.get("/activities")
        participants = get_response.json()[activity_name]["participants"]
        assert participants.count(test_student_email) == 1


class TestSignupAndUnregisterFlow:
    """Tests for complete signup and unregister lifecycle"""

    def test_signup_then_unregister_removes_participant(
        self, client, clean_activities, test_student_email
    ):
        """Verify unregister after signup removes participant from activity"""
        # Arrange
        activity_name = "Chess Club"

        # Act
        signup_response = client.post(
            f"/activities/{activity_name}/signup?email={test_student_email}"
        )
        verify_signup = client.get("/activities")
        unregister_response = client.delete(
            f"/activities/{activity_name}/unregister?email={test_student_email}"
        )
        verify_unregister = client.get("/activities")

        # Assert
        assert signup_response.status_code == 200
        assert test_student_email in verify_signup.json()[activity_name]["participants"]

        assert unregister_response.status_code == 200
        assert (
            test_student_email not in verify_unregister.json()[activity_name]["participants"]
        )

    def test_signup_unregister_then_signup_again(
        self, client, clean_activities, test_student_email
    ):
        """Verify student can signup again after unregistering"""
        # Arrange
        activity_name = "Programming Class"

        # Act - First signup
        client.post(f"/activities/{activity_name}/signup?email={test_student_email}")
        first_get = client.get("/activities")

        # Act - Unregister
        client.delete(
            f"/activities/{activity_name}/unregister?email={test_student_email}"
        )
        after_unregister = client.get("/activities")

        # Act - Signup again
        second_signup = client.post(
            f"/activities/{activity_name}/signup?email={test_student_email}"
        )
        second_get = client.get("/activities")

        # Assert
        assert test_student_email in first_get.json()[activity_name]["participants"]
        assert test_student_email not in after_unregister.json()[activity_name]["participants"]
        assert second_signup.status_code == 200
        assert test_student_email in second_get.json()[activity_name]["participants"]


class TestMultipleStudentsInteraction:
    """Tests for multiple students interacting with activities"""

    def test_multiple_students_signup_same_activity(self, client, clean_activities):
        """Verify multiple students can signup and both appear in activity"""
        # Arrange
        activity_name = "Chess Club"
        students = [
            "alice@mergington.edu",
            "bob@mergington.edu",
            "charlie@mergington.edu",
        ]

        # Act
        for student in students:
            response = client.post(
                f"/activities/{activity_name}/signup?email={student}"
            )
            assert response.status_code == 200

        # Assert
        get_response = client.get("/activities")
        participants = get_response.json()[activity_name]["participants"]
        for student in students:
            assert student in participants

    def test_one_student_unregister_doesnt_affect_others(
        self, client, clean_activities
    ):
        """Verify unregistering one student doesn't affect others"""
        # Arrange
        activity_name = "Programming Class"
        student1 = "student1@mergington.edu"
        student2 = "student2@mergington.edu"
        student3 = "student3@mergington.edu"

        # Act - Sign up three students
        client.post(f"/activities/{activity_name}/signup?email={student1}")
        client.post(f"/activities/{activity_name}/signup?email={student2}")
        client.post(f"/activities/{activity_name}/signup?email={student3}")

        # Act - Unregister second student
        client.delete(f"/activities/{activity_name}/unregister?email={student2}")

        # Assert
        get_response = client.get("/activities")
        participants = get_response.json()[activity_name]["participants"]
        assert student1 in participants
        assert student2 not in participants
        assert student3 in participants
        assert len(participants) == 2

    def test_existing_and_new_participants_coexist(
        self, client, clean_activities, existing_student_email, test_student_email
    ):
        """Verify existing and newly added participants appear together"""
        # Arrange
        activity_name = "Chess Club"  # Already has existing_student_email

        # Act
        client.post(f"/activities/{activity_name}/signup?email={test_student_email}")

        # Assert
        get_response = client.get("/activities")
        participants = get_response.json()[activity_name]["participants"]
        assert existing_student_email in participants
        assert test_student_email in participants
        assert len(participants) == 2
