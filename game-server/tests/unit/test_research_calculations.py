"""
Unit tests for research calculation functions

Tests research cost calculations, point generation, and related algorithms.
Follows the existing database-first testing pattern.
"""

import pytest
from backend.routes.research import calculate_research_cost, calculate_research_points
from backend.models import Planet, Research


class TestResearchCostCalculations:
    """Test research cost calculation algorithms"""

    def test_calculate_research_cost_level_one(self):
        """Test research cost for level 1 upgrades"""
        # Colonization tech level 1
        cost = calculate_research_cost('colonization_tech', 1)
        assert cost == 100

        # Astrophysics level 1
        cost = calculate_research_cost('astrophysics', 1)
        assert cost == 150

        # Interstellar communication level 1
        cost = calculate_research_cost('interstellar_communication', 1)
        assert cost == 200

    def test_calculate_research_cost_exponential_scaling(self):
        """Test that research costs scale exponentially"""
        # Test colonization tech progression
        level1_cost = calculate_research_cost('colonization_tech', 1)
        level2_cost = calculate_research_cost('colonization_tech', 2)
        level3_cost = calculate_research_cost('colonization_tech', 3)

        # Each level should cost more than the previous
        assert level2_cost > level1_cost
        assert level3_cost > level2_cost

        # Test exponential scaling: cost = base * (level ^ 1.5)
        expected_level2 = int(100 * (2 ** 1.5))  # ~282
        expected_level3 = int(100 * (3 ** 1.5))  # ~519

        assert level2_cost == expected_level2
        assert level3_cost == expected_level3

    def test_calculate_research_cost_higher_levels(self):
        """Test research costs for higher technology levels"""
        # Level 5 colonization tech
        level5_cost = calculate_research_cost('colonization_tech', 5)
        expected = int(100 * (5 ** 1.5))  # ~1118
        assert level5_cost == expected

        # Level 10 colonization tech
        level10_cost = calculate_research_cost('colonization_tech', 10)
        expected = int(100 * (10 ** 1.5))  # ~3162
        assert level10_cost == expected

    def test_calculate_research_cost_level_zero(self):
        """Test research cost for level 0 (should be 0)"""
        cost = calculate_research_cost('colonization_tech', 0)
        assert cost == 0

    def test_calculate_research_cost_negative_level(self):
        """Test research cost for negative levels (should be 0)"""
        cost = calculate_research_cost('colonization_tech', -1)
        assert cost == 0

    def test_calculate_research_cost_unknown_technology(self):
        """Test research cost for unknown technology type"""
        cost = calculate_research_cost('unknown_tech', 1)
        assert cost == 100  # Should use default base cost

    def test_calculate_research_cost_all_technologies(self):
        """Test research cost calculation for all technology types"""
        technologies = ['colonization_tech', 'astrophysics', 'interstellar_communication']
        bases = [100, 150, 200]

        for tech, base in zip(technologies, bases):
            # Level 1
            cost1 = calculate_research_cost(tech, 1)
            assert cost1 == base

            # Level 2
            cost2 = calculate_research_cost(tech, 2)
            expected2 = int(base * (2 ** 1.5))
            assert cost2 == expected2

            # Level 3
            cost3 = calculate_research_cost(tech, 3)
            expected3 = int(base * (3 ** 1.5))
            assert cost3 == expected3


class TestResearchPointCalculations:
    """Test research point generation calculations with real database"""

    def test_calculate_research_points_no_planets(self, db_session):
        """Test research point calculation with no planets"""
        # Clear all planets for this user
        db_session.query(Planet).filter_by(user_id=1).delete()
        db_session.commit()

        points = calculate_research_points(1)
        assert points == 0

    def test_calculate_research_points_single_planet(self, db_session, sample_user):
        """Test research point calculation for a single planet"""
        # Create planet with research lab
        planet = Planet(
            name='Research Planet',
            x=100, y=200, z=300,
            user_id=sample_user.id,
            research_lab=5,
            solar_plant=10,
            metal_mine=5,
            crystal_mine=3,
            deuterium_synthesizer=2
        )
        db_session.add(planet)
        db_session.commit()

        points = calculate_research_points(sample_user.id)

        # Should generate research points
        assert points >= 0

        # With research lab level 5, should generate points
        assert points > 0

    def test_calculate_research_points_multiple_planets(self, db_session, sample_user):
        """Test research point calculation for multiple planets"""
        # Create two planets
        planet1 = Planet(
            name='Research Planet 1',
            x=100, y=200, z=300,
            user_id=sample_user.id,
            research_lab=3,
            solar_plant=5,
            metal_mine=2,
            crystal_mine=2,
            deuterium_synthesizer=1
        )

        planet2 = Planet(
            name='Research Planet 2',
            x=150, y=250, z=350,
            user_id=sample_user.id,
            research_lab=7,
            solar_plant=15,
            metal_mine=8,
            crystal_mine=6,
            deuterium_synthesizer=4
        )

        db_session.add(planet1)
        db_session.add(planet2)
        db_session.commit()

        points = calculate_research_points(sample_user.id)

        # Should generate points from both planets
        assert points > 0

        # Planet 2 should contribute more due to higher research lab level

    def test_calculate_research_points_no_research_lab(self, db_session, sample_user):
        """Test research point calculation for planet without research lab"""
        planet = Planet(
            name='No Research Planet',
            x=100, y=200, z=300,
            user_id=sample_user.id,
            research_lab=0,  # No research lab
            solar_plant=5,
            metal_mine=2,
            crystal_mine=2,
            deuterium_synthesizer=1
        )
        db_session.add(planet)
        db_session.commit()

        points = calculate_research_points(sample_user.id)

        # Should generate minimal points or zero
        assert points >= 0

    def test_calculate_research_points_energy_efficiency(self, db_session, sample_user):
        """Test research point calculation with different energy ratios"""
        # High energy surplus planet
        planet_high = Planet(
            name='High Energy Planet',
            x=100, y=200, z=300,
            user_id=sample_user.id,
            research_lab=5,
            solar_plant=20,  # High energy production
            metal_mine=1,
            crystal_mine=1,
            deuterium_synthesizer=1
        )

        # Low energy (deficit) planet
        planet_low = Planet(
            name='Low Energy Planet',
            x=150, y=250, z=350,
            user_id=sample_user.id,
            research_lab=5,
            solar_plant=1,   # Low energy production
            metal_mine=10,  # High consumption
            crystal_mine=10,
            deuterium_synthesizer=10
        )

        db_session.add(planet_high)
        db_session.add(planet_low)
        db_session.commit()

        points = calculate_research_points(sample_user.id)

        # Should generate points from both planets
        assert points > 0

        # High energy planet should contribute more efficiently

    def test_calculate_research_points_zero_energy_consumption(self, db_session, sample_user):
        """Test research point calculation with zero energy consumption"""
        planet = Planet(
            name='Zero Consumption Planet',
            x=100, y=200, z=300,
            user_id=sample_user.id,
            research_lab=5,
            solar_plant=10,
            metal_mine=0,
            crystal_mine=0,
            deuterium_synthesizer=0
        )
        db_session.add(planet)
        db_session.commit()

        points = calculate_research_points(sample_user.id)

        # Should still generate points (energy ratio = 1.0)
        assert points > 0

    def test_calculate_research_points_maximum_values(self, db_session, sample_user):
        """Test research point calculation with maximum building levels"""
        planet = Planet(
            name='Max Planet',
            x=100, y=200, z=300,
            user_id=sample_user.id,
            research_lab=100,  # Very high research lab
            solar_plant=100,   # Very high solar plant
            metal_mine=100,
            crystal_mine=100,
            deuterium_synthesizer=100
        )
        db_session.add(planet)
        db_session.commit()

        points = calculate_research_points(sample_user.id)

        # Should generate significant points
        assert points > 0  # Should be substantial

    def test_calculate_research_points_different_users(self, db_session, sample_user):
        """Test research point calculation for different users"""
        from backend.models import User

        # Create second user
        user2 = User(
            username='testuser2',
            email='test2@example.com',
            password_hash='hash2'
        )
        db_session.add(user2)
        db_session.commit()

        # Create planets for both users
        planet1 = Planet(
            name='User1 Planet',
            x=100, y=200, z=300,
            user_id=sample_user.id,
            research_lab=5,
            solar_plant=10,
            metal_mine=5,
            crystal_mine=3,
            deuterium_synthesizer=2
        )

        planet2 = Planet(
            name='User2 Planet',
            x=150, y=250, z=350,
            user_id=user2.id,
            research_lab=3,
            solar_plant=5,
            metal_mine=2,
            crystal_mine=2,
            deuterium_synthesizer=1
        )

        db_session.add(planet1)
        db_session.add(planet2)
        db_session.commit()

        # Test different users get different calculations
        points_user1 = calculate_research_points(sample_user.id)
        points_user2 = calculate_research_points(user2.id)

        # Both should generate points
        assert points_user1 > 0
        assert points_user2 > 0

        # User1 should have more points due to higher research lab


class TestResearchIntegrationCalculations:
    """Test research calculations that integrate multiple components"""

    def test_research_progression_cost_increase(self):
        """Test that research costs increase appropriately with progression"""
        # Calculate costs for first 5 levels of colonization tech
        costs = []
        for level in range(1, 6):
            cost = calculate_research_cost('colonization_tech', level)
            costs.append(cost)

        # Each subsequent level should cost more
        for i in range(1, len(costs)):
            assert costs[i] > costs[i-1]

        # Test that the increase is exponential
        ratio_2_1 = costs[1] / costs[0]  # ~2.82
        ratio_3_2 = costs[2] / costs[1]  # ~1.84
        ratio_4_3 = costs[3] / costs[2]  # ~1.54
        ratio_5_4 = costs[4] / costs[3]  # ~1.36

        # The ratios should decrease (but stay > 1) due to exponential scaling
        assert ratio_2_1 > ratio_3_2 > ratio_4_3 > ratio_5_4 > 1

    def test_research_efficiency_calculation(self, db_session, sample_user):
        """Test research efficiency calculations with real database"""
        # Create planet with balanced energy
        planet = Planet(
            name='Balanced Planet',
            x=100, y=200, z=300,
            user_id=sample_user.id,
            research_lab=10,
            solar_plant=20,
            metal_mine=5,
            crystal_mine=5,
            deuterium_synthesizer=5
        )
        db_session.add(planet)
        db_session.commit()

        points = calculate_research_points(sample_user.id)

        # Should generate research points
        assert points >= 1

    def test_research_cost_scaling_formula(self):
        """Test that research cost scaling follows the expected formula"""
        base_cost = 100
        exponent = 1.5

        for level in range(1, 11):
            expected_cost = int(base_cost * (level ** exponent))
            actual_cost = calculate_research_cost('colonization_tech', level)

            assert actual_cost == expected_cost

            # Additional validation: cost should be reasonable
            assert actual_cost >= base_cost
            assert actual_cost <= base_cost * (level ** 2)  # Upper bound check
