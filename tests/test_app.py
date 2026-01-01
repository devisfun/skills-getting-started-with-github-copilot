"""
Tests for the Mergington High School Activities API
"""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Add the src directory to the path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to their initial state before each test"""
    # Store original state
    original_activities = {
        name: {
            "description": details["description"],
            "schedule": details["schedule"],
            "max_participants": details["max_participants"],
            "participants": details["participants"].copy()
        }
        for name, details in activities.items()
    }
    
    yield
    
    # Restore original state after test
    for name, details in original_activities.items():
        activities[name]["participants"] = details["participants"].copy()


class TestGetActivities:
    """Tests for the GET /activities endpoint"""
    
    def test_get_activities_returns_200(self, client):
        """Test that /activities endpoint returns 200 status code"""
        response = client.get("/activities")
        assert response.status_code == 200
    
    def test_get_activities_returns_dict(self, client):
        """Test that /activities endpoint returns a dictionary"""
        response = client.get("/activities")
        data = response.json()
        assert isinstance(data, dict)
    
    def test_get_activities_contains_all_activities(self, client):
        """Test that all activities are returned"""
        response = client.get("/activities")
        data = response.json()
        assert "Basketball Team" in data
        assert "Swimming Club" in data
        assert "Drama Club" in data
        assert "Art Studio" in data
        assert "Debate Team" in data
        assert "Science Olympiad" in data
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
    
    def test_get_activities_contains_required_fields(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity in data.items():
            assert "description" in activity
            assert "schedule" in activity
            assert "max_participants" in activity
            assert "participants" in activity
            assert isinstance(activity["participants"], list)
    
    def test_get_activities_participants_are_strings(self, client):
        """Test that participant list contains strings (emails)"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity in data.items():
            for participant in activity["participants"]:
                assert isinstance(participant, str)
                assert "@" in participant  # Check it looks like an email


class TestSignupForActivity:
    """Tests for the POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_for_activity_returns_200(self, client, reset_activities):
        """Test that signup returns 200 status code on success"""
        response = client.post(
            "/activities/Basketball Team/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
    
    def test_signup_for_activity_adds_participant(self, client, reset_activities):
        """Test that signup successfully adds a participant"""
        email = "newstudent@mergington.edu"
        response = client.post(
            "/activities/Basketball Team/signup",
            params={"email": email}
        )
        
        assert response.status_code == 200
        
        # Verify participant was added
        activities_response = client.get("/activities")
        data = activities_response.json()
        assert email in data["Basketball Team"]["participants"]
    
    def test_signup_returns_success_message(self, client, reset_activities):
        """Test that signup returns a success message"""
        email = "newstudent@mergington.edu"
        response = client.post(
            "/activities/Basketball Team/signup",
            params={"email": email}
        )
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert "Basketball Team" in data["message"]
    
    def test_signup_for_nonexistent_activity_returns_404(self, client):
        """Test that signup for nonexistent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_duplicate_returns_400(self, client, reset_activities):
        """Test that duplicate signup returns 400 error"""
        email = "alex@mergington.edu"  # Already signed up for Basketball Team
        response = client.post(
            "/activities/Basketball Team/signup",
            params={"email": email}
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_multiple_activities(self, client, reset_activities):
        """Test that a student can sign up for multiple activities"""
        email = "newstudent@mergington.edu"
        
        # Sign up for Basketball Team
        response1 = client.post(
            "/activities/Basketball Team/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Sign up for Swimming Club
        response2 = client.post(
            "/activities/Swimming Club/signup",
            params={"email": email}
        )
        assert response2.status_code == 200
        
        # Verify both signups
        activities_response = client.get("/activities")
        data = activities_response.json()
        assert email in data["Basketball Team"]["participants"]
        assert email in data["Swimming Club"]["participants"]


class TestUnregisterFromActivity:
    """Tests for the DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_returns_200(self, client, reset_activities):
        """Test that unregister returns 200 status code on success"""
        email = "alex@mergington.edu"  # Already signed up for Basketball Team
        response = client.delete(
            "/activities/Basketball Team/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
    
    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregister successfully removes a participant"""
        email = "alex@mergington.edu"
        response = client.delete(
            "/activities/Basketball Team/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        data = activities_response.json()
        assert email not in data["Basketball Team"]["participants"]
    
    def test_unregister_returns_success_message(self, client, reset_activities):
        """Test that unregister returns a success message"""
        email = "alex@mergington.edu"
        response = client.delete(
            "/activities/Basketball Team/unregister",
            params={"email": email}
        )
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert "Basketball Team" in data["message"]
    
    def test_unregister_nonexistent_activity_returns_404(self, client):
        """Test that unregister for nonexistent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent Activity/unregister",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_unregister_not_registered_returns_400(self, client, reset_activities):
        """Test that unregistering a non-registered student returns 400"""
        response = client.delete(
            "/activities/Basketball Team/unregister",
            params={"email": "notregistered@mergington.edu"}
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]
    
    def test_signup_then_unregister(self, client, reset_activities):
        """Test the full flow of signing up and unregistering"""
        email = "newstudent@mergington.edu"
        
        # Sign up
        signup_response = client.post(
            "/activities/Basketball Team/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # Verify signed up
        activities_response = client.get("/activities")
        assert email in activities_response.json()["Basketball Team"]["participants"]
        
        # Unregister
        unregister_response = client.delete(
            "/activities/Basketball Team/unregister",
            params={"email": email}
        )
        assert unregister_response.status_code == 200
        
        # Verify unregistered
        activities_response = client.get("/activities")
        assert email not in activities_response.json()["Basketball Team"]["participants"]


class TestRoot:
    """Tests for the root endpoint"""
    
    def test_root_redirects(self, client):
        """Test that root endpoint redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestActivityConstraints:
    """Tests for activity capacity constraints"""
    
    def test_max_participants_field_exists(self, client):
        """Test that all activities have max_participants field"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity in data.items():
            assert "max_participants" in activity
            assert isinstance(activity["max_participants"], int)
            assert activity["max_participants"] > 0
    
    def test_participants_do_not_exceed_max(self, client):
        """Test that participant count does not exceed max_participants"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity in data.items():
            assert len(activity["participants"]) <= activity["max_participants"]
