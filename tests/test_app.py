"""Tests for the Mergington High School Activities API"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_dict(self, client):
        """Test that GET /activities returns a dictionary of activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        assert isinstance(response.json(), dict)
    
    def test_get_activities_contains_expected_activities(self, client):
        """Test that GET /activities contains expected activity names"""
        response = client.get("/activities")
        data = response.json()
        expected_activities = [
            "Chess Club", 
            "Programming Class", 
            "Gym Class", 
            "Basketball Team",
            "Tennis Club",
            "Art Studio",
            "Music Band",
            "Debate Team",
            "Science Club"
        ]
        for activity in expected_activities:
            assert activity in data
    
    def test_activity_structure(self, client):
        """Test that each activity has the correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_valid_email(self, client):
        """Test signing up with a valid email"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "test@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]
    
    def test_signup_nonexistent_activity(self, client):
        """Test signing up for a nonexistent activity"""
        response = client.post(
            "/activities/NonExistent%20Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_signup_duplicate_email(self, client):
        """Test signing up with an email already registered for that activity"""
        # First signup
        response1 = client.post(
            "/activities/Chess%20Club/signup?email=duplicate@mergington.edu"
        )
        assert response1.status_code == 200
        
        # Second signup with same email
        response2 = client.post(
            "/activities/Chess%20Club/signup?email=duplicate@mergington.edu"
        )
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_adds_participant_to_activity(self, client):
        """Test that signup actually adds the participant to the activity"""
        email = "newstudent@mergington.edu"
        activity_name = "Programming Class"
        
        # Get activities before signup
        response_before = client.get("/activities")
        participants_before = response_before.json()[activity_name]["participants"].copy()
        
        # Signup
        response = client.post(
            f"/activities/{activity_name.replace(' ', '%20')}/signup?email={email}"
        )
        assert response.status_code == 200
        
        # Get activities after signup
        response_after = client.get("/activities")
        participants_after = response_after.json()[activity_name]["participants"]
        
        assert email in participants_after
        assert len(participants_after) == len(participants_before) + 1


class TestUnregister:
    """Tests for POST /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_existing_participant(self, client):
        """Test unregistering an existing participant"""
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        
        # Verify participant exists
        response_before = client.get("/activities")
        assert email in response_before.json()[activity_name]["participants"]
        
        # Unregister
        response = client.post(
            f"/activities/{activity_name.replace(' ', '%20')}/unregister?email={email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        
        # Verify participant is removed
        response_after = client.get("/activities")
        assert email not in response_after.json()[activity_name]["participants"]
    
    def test_unregister_nonexistent_activity(self, client):
        """Test unregistering from a nonexistent activity"""
        response = client.post(
            "/activities/NonExistent%20Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_unregister_non_registered_participant(self, client):
        """Test unregistering a participant not in that activity"""
        response = client.post(
            "/activities/Chess%20Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]


class TestIntegration:
    """Integration tests combining multiple operations"""
    
    def test_signup_and_unregister_flow(self, client):
        """Test the full flow of signing up and unregistering"""
        email = "integration@mergington.edu"
        activity = "Gym Class"
        
        # Signup
        response_signup = client.post(
            f"/activities/{activity.replace(' ', '%20')}/signup?email={email}"
        )
        assert response_signup.status_code == 200
        
        # Verify signup
        response_check = client.get("/activities")
        assert email in response_check.json()[activity]["participants"]
        
        # Unregister
        response_unregister = client.post(
            f"/activities/{activity.replace(' ', '%20')}/unregister?email={email}"
        )
        assert response_unregister.status_code == 200
        
        # Verify unregister
        response_final = client.get("/activities")
        assert email not in response_final.json()[activity]["participants"]
