import pytest


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """Should return all available activities"""
        # ARRANGE
        expected_activities = ["Chess Club", "Programming Class", "Gym Class"]
        
        # ACT
        response = client.get("/activities")
        
        # ASSERT
        assert response.status_code == 200
        data = response.json()
        for activity in expected_activities:
            assert activity in data

    def test_get_activities_structure(self, client):
        """Should return activities with correct structure"""
        # ARRANGE
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        # ACT
        response = client.get("/activities")
        data = response.json()
        activity = data["Chess Club"]
        
        # ASSERT
        for field in required_fields:
            assert field in activity
        assert isinstance(activity["participants"], list)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_participant_success(self, client):
        """Should successfully sign up a new participant"""
        # ARRANGE
        activity_name = "Chess Club"
        email = "student@mergington.edu"
        
        # ACT
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # ASSERT
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        assert email in response.json()["message"]

    def test_signup_updates_participants_list(self, client):
        """Should add the new participant to the activity"""
        # ARRANGE
        activity_name = "Chess Club"
        new_email = "newstudent@mergington.edu"
        
        # ACT
        client.post(f"/activities/{activity_name}/signup?email={new_email}")
        response = client.get("/activities")
        
        # ASSERT
        participants = response.json()[activity_name]["participants"]
        assert new_email in participants

    def test_signup_duplicate_participant_rejected(self, client):
        """Should prevent signing up twice for the same activity"""
        # ARRANGE
        activity_name = "Chess Club"
        email = "duplicate@mergington.edu"
        
        # ACT - First signup
        first_response = client.post(f"/activities/{activity_name}/signup?email={email}")
        # ACT - Second signup (duplicate)
        second_response = client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # ASSERT
        assert first_response.status_code == 200
        assert second_response.status_code == 400
        assert "already signed up" in second_response.json()["detail"]

    def test_signup_existing_participant_rejected(self, client):
        """Should reject signup for participant already in activity"""
        # ARRANGE
        activity_name = "Chess Club"
        existing_email = "michael@mergington.edu"  # Already in Chess Club
        
        # ACT
        response = client.post(f"/activities/{activity_name}/signup?email={existing_email}")
        
        # ASSERT
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_nonexistent_activity_returns_404(self, client):
        """Should return 404 when activity doesn't exist"""
        # ARRANGE
        nonexistent_activity = "Nonexistent Club"
        email = "student@mergington.edu"
        
        # ACT
        response = client.post(f"/activities/{nonexistent_activity}/signup?email={email}")
        
        # ASSERT
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]


class TestRemoveParticipant:
    """Tests for DELETE /activities/{activity_name}/participants/{email} endpoint"""

    def test_remove_participant_success(self, client):
        """Should successfully remove a participant from an activity"""
        # ARRANGE
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already in Chess Club
        
        # ACT
        response = client.delete(f"/activities/{activity_name}/participants/{email}")
        
        # ASSERT
        assert response.status_code == 200
        assert "Removed" in response.json()["message"]

    def test_remove_participant_updates_list(self, client):
        """Should remove participant from the activity's participant list"""
        # ARRANGE
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        
        # ACT
        client.delete(f"/activities/{activity_name}/participants/{email}")
        response = client.get("/activities")
        
        # ASSERT
        participants = response.json()[activity_name]["participants"]
        assert email not in participants

    def test_remove_nonexistent_participant_fails(self, client):
        """Should return 400 when trying to remove participant not signed up"""
        # ARRANGE
        activity_name = "Chess Club"
        unregistered_email = "notregistered@mergington.edu"
        
        # ACT
        response = client.delete(f"/activities/{activity_name}/participants/{unregistered_email}")
        
        # ASSERT
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]

    def test_remove_from_nonexistent_activity_returns_404(self, client):
        """Should return 404 when activity doesn't exist"""
        # ARRANGE
        nonexistent_activity = "Nonexistent Club"
        email = "student@mergington.edu"
        
        # ACT
        response = client.delete(f"/activities/{nonexistent_activity}/participants/{email}")
        
        # ASSERT
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_remove_then_can_signup_again(self, client):
        """Should allow signup after removal"""
        # ARRANGE
        activity_name = "Chess Club"
        email = "testuser@mergington.edu"
        
        # ACT - Sign up
        signup_response = client.post(f"/activities/{activity_name}/signup?email={email}")
        # ACT - Remove
        remove_response = client.delete(f"/activities/{activity_name}/participants/{email}")
        # ACT - Sign up again
        resignup_response = client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # ASSERT
        assert signup_response.status_code == 200
        assert remove_response.status_code == 200
        assert resignup_response.status_code == 200


class TestIntegration:
    """Integration tests combining multiple operations"""

    def test_full_signup_and_removal_flow(self, client):
        """Test complete flow: signup, view, remove, verify absence"""
        # ARRANGE
        activity_name = "Gym Class"
        email = "testflow@mergington.edu"
        
        # ACT - Sign up
        signup_response = client.post(f"/activities/{activity_name}/signup?email={email}")
        list_after_signup = client.get("/activities").json()
        
        # ACT - Remove
        remove_response = client.delete(f"/activities/{activity_name}/participants/{email}")
        list_after_removal = client.get("/activities").json()
        
        # ASSERT signup
        assert signup_response.status_code == 200
        assert email in list_after_signup[activity_name]["participants"]
        
        # ASSERT removal
        assert remove_response.status_code == 200
        assert email not in list_after_removal[activity_name]["participants"]

    def test_single_user_multiple_activities_signup(self, client):
        """Test signing up the same user for multiple different activities"""
        # ARRANGE
        email = "multisignup@mergington.edu"
        activities_to_join = ["Chess Club", "Gym Class", "Programming Class"]
        
        # ACT
        responses = []
        for activity in activities_to_join:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            responses.append(response)
        
        all_activities = client.get("/activities").json()
        
        # ASSERT
        for response in responses:
            assert response.status_code == 200
        
        for activity in activities_to_join:
            assert email in all_activities[activity]["participants"]

    def test_capacity_tracking(self, client):
        """Test that participant count updates correctly"""
        # ARRANGE
        activity_name = "Chess Club"
        email = "capacitytest@mergington.edu"
        
        # ACT - Get initial participant count
        initial_response = client.get("/activities")
        initial_count = len(initial_response.json()[activity_name]["participants"])
        
        # ACT - Add participant
        client.post(f"/activities/{activity_name}/signup?email={email}")
        after_signup = client.get("/activities")
        count_after_signup = len(after_signup.json()[activity_name]["participants"])
        
        # ACT - Remove participant
        client.delete(f"/activities/{activity_name}/participants/{email}")
        after_removal = client.get("/activities")
        final_count = len(after_removal.json()[activity_name]["participants"])
        
        # ASSERT
        assert count_after_signup == initial_count + 1
        assert final_count == initial_count
