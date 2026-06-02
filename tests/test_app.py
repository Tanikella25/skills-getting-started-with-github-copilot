"""
Comprehensive test suite for the Mergington High School Activities API.

Tests use the AAA (Arrange-Act-Assert) pattern:
- Arrange: Set up test data and preconditions
- Act: Call the endpoint/function being tested
- Assert: Verify the response and state changes
"""
import pytest


class TestRootEndpoint:
    """Tests for the root endpoint."""

    def test_root_redirects_to_static(self, client):
        """
        Arrange: Prepare a request to the root endpoint.
        Act: Make the request.
        Assert: Verify redirect to static/index.html.
        """
        # Arrange & Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


class TestGetActivities:
    """Tests for retrieving all activities."""

    def test_get_activities_returns_all_activities(self, client):
        """
        Arrange: Prepare to fetch all activities.
        Act: Make GET request to /activities.
        Assert: Verify response contains all activities with correct structure.
        """
        # Arrange & Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert response.status_code == 200
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
        assert "Soccer Team" in data
        assert "Swim Club" in data
        assert "Drama Club" in data
        assert "Art Studio" in data
        assert "Debate Team" in data
        assert "Math Club" in data

    def test_get_activities_structure(self, client):
        """
        Arrange: Prepare to fetch activities.
        Act: Get activities and inspect structure.
        Assert: Verify each activity has required fields.
        """
        # Arrange & Act
        response = client.get("/activities")
        activities = response.json()
        
        # Assert
        for activity_name, activity_data in activities.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignup:
    """Tests for student signup functionality."""

    def test_successful_signup(self, client):
        """
        Arrange: Identify an available activity (Soccer Team) with open spots.
        Act: Sign up a new student.
        Assert: Verify success response and student added to participants.
        """
        # Arrange
        activity_name = "Soccer Team"
        email = "newstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity_name}"
        
        # Verify student was added to participants
        activities = client.get("/activities").json()
        assert email in activities[activity_name]["participants"]

    def test_duplicate_signup_returns_400(self, client):
        """
        Arrange: Identify a student already registered (michael@mergington.edu in Chess Club).
        Act: Attempt to sign up the same student again.
        Assert: Verify 400 error is returned with appropriate message.
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_signup_nonexistent_activity_returns_404(self, client):
        """
        Arrange: Prepare to sign up for an activity that doesn't exist.
        Act: Attempt signup for invalid activity.
        Assert: Verify 404 error is returned.
        """
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_full_activity_returns_400(self, client):
        """
        Arrange: Create a scenario where an activity is at full capacity.
               (Gym Class has max_participants=30, currently has 2 participants)
               We'll fill it by signing up 28 more students.
        Act: Try to sign up beyond capacity.
        Assert: Verify 400 error when activity is full.
        """
        # Arrange
        activity_name = "Gym Class"
        
        # Fill the activity to capacity (max 30, currently 2, need 28 more)
        for i in range(28):
            email = f"student{i}@mergington.edu"
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Act: Try to sign up one more student when activity is full
        overfull_email = "overfull@mergington.edu"
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": overfull_email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "Activity is full" in response.json()["detail"]

    def test_email_normalization_during_signup(self, client):
        """
        Arrange: Prepare to sign up with an email that has leading/trailing whitespace
                 and mixed case.
        Act: Sign up with "  NewStudent@MERGINGTON.EDU  ".
        Assert: Verify email is normalized to lowercase and stored correctly.
        """
        # Arrange
        activity_name = "Drama Club"
        email_with_whitespace = "  newactor@MERGINGTON.EDU  "
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email_with_whitespace}
        )
        
        # Assert
        assert response.status_code == 200
        activities = client.get("/activities").json()
        assert "newactor@mergington.edu" in activities[activity_name]["participants"]
        # Verify the non-normalized version is NOT in participants
        assert email_with_whitespace not in activities[activity_name]["participants"]

    def test_signup_case_insensitive_duplicate(self, client):
        """
        Arrange: A student is registered with lowercase email.
        Act: Try to sign up the same student with uppercase email.
        Assert: Verify duplicate check is case-insensitive and returns 400.
        """
        # Arrange
        activity_name = "Art Studio"
        # First signup with lowercase
        email_lower = "artist@mergington.edu"
        response1 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email_lower}
        )
        assert response1.status_code == 200
        
        # Act: Try to sign up with uppercase version of same email
        email_upper = "ARTIST@MERGINGTON.EDU"
        response2 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email_upper}
        )
        
        # Assert
        assert response2.status_code == 400
        assert "already registered" in response2.json()["detail"]


class TestUnregister:
    """Tests for student unregistration functionality."""

    def test_successful_unregister(self, client):
        """
        Arrange: Identify a student registered in an activity (michael@mergington.edu in Chess Club).
        Act: Unregister the student.
        Assert: Verify success response and student removed from participants.
        """
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        
        # Verify student is initially registered
        activities_before = client.get("/activities").json()
        assert email in activities_before[activity_name]["participants"]
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Unregistered {email} from {activity_name}"
        
        # Verify student was removed from participants
        activities_after = client.get("/activities").json()
        assert email not in activities_after[activity_name]["participants"]

    def test_unregister_nonexistent_activity_returns_404(self, client):
        """
        Arrange: Prepare to unregister from an activity that doesn't exist.
        Act: Attempt unregister from invalid activity.
        Assert: Verify 404 error is returned.
        """
        # Arrange
        activity_name = "Nonexistent Activity"
        email = "student@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_student_not_in_activity_returns_404(self, client):
        """
        Arrange: Try to unregister a student who is not registered in the activity.
        Act: Attempt to unregister non-registered student.
        Assert: Verify 404 error is returned.
        """
        # Arrange
        activity_name = "Swim Club"
        email = "notregistered@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "Student not found" in response.json()["detail"]

    def test_email_normalization_during_unregister(self, client):
        """
        Arrange: Sign up a student, then try to unregister using different email casing/whitespace.
        Act: Sign up, then unregister with different case/whitespace.
        Assert: Verify email normalization works during unregister.
        """
        # Arrange: Sign up a student
        activity_name = "Debate Team"
        email_original = "speaker@mergington.edu"
        response1 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email_original}
        )
        assert response1.status_code == 200
        
        # Act: Unregister with different casing and whitespace
        email_variant = "  SPEAKER@MERGINGTON.EDU  "
        response2 = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email_variant}
        )
        
        # Assert
        assert response2.status_code == 200
        activities = client.get("/activities").json()
        assert email_original not in activities[activity_name]["participants"]

    def test_unregister_frees_capacity(self, client):
        """
        Arrange: Sign up multiple students to fill an activity.
        Act: Unregister one student, then try to sign up a new one.
        Assert: Verify the freed capacity allows new signup.
        """
        # Arrange: Fill Math Club (max 18 participants, currently likely has room)
        activity_name = "Math Club"
        emails_to_add = [f"mathstudent{i}@mergington.edu" for i in range(18)]
        
        for email in emails_to_add:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            if response.status_code != 200:
                break  # Activity is full
        
        # Verify activity is full
        response_full = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": "overflow@mergington.edu"}
        )
        assert response_full.status_code == 400
        
        # Act: Unregister a student
        email_to_remove = emails_to_add[0]
        response_unregister = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email_to_remove}
        )
        assert response_unregister.status_code == 200
        
        # Assert: Verify we can now sign up a new student
        response_new_signup = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": "newmathstudent@mergington.edu"}
        )
        assert response_new_signup.status_code == 200


class TestIntegrationScenarios:
    """Tests for complex multi-step scenarios."""

    def test_signup_unregister_signup_workflow(self, client):
        """
        Arrange: Prepare a workflow of signup -> unregister -> signup again.
        Act: Execute the workflow.
        Assert: Verify all steps succeed and state is correct.
        """
        # Arrange
        activity_name = "Swim Club"
        email = "swimmer@mergington.edu"
        
        # Act: First signup
        response1 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Act: Unregister
        response2 = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        assert response2.status_code == 200
        
        # Act: Sign up again
        response3 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response3.status_code == 200
        activities = client.get("/activities").json()
        assert email in activities[activity_name]["participants"]

    def test_multiple_students_same_activity(self, client):
        """
        Arrange: Sign up multiple different students to the same activity.
        Act: Add several students, then unregister one.
        Assert: Verify all operations affect the correct participants list.
        """
        # Arrange
        activity_name = "Programming Class"
        emails = [
            "programmer1@mergington.edu",
            "programmer2@mergington.edu",
            "programmer3@mergington.edu",
        ]
        
        # Act: Sign up all students
        for email in emails:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Act: Verify all are registered
        activities = client.get("/activities").json()
        for email in emails:
            assert email in activities[activity_name]["participants"]
        
        # Act: Unregister one
        response_unregister = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": emails[1]}
        )
        
        # Assert
        assert response_unregister.status_code == 200
        activities = client.get("/activities").json()
        assert emails[0] in activities[activity_name]["participants"]
        assert emails[1] not in activities[activity_name]["participants"]
        assert emails[2] in activities[activity_name]["participants"]
