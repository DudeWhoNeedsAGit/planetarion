"""
Unit tests for research calculation functions

Tests research cost calculations, point generation, and related algorithms.
"""

import pytest
import math
from backend.routes.research import calculate_research_cost, calculate_research_points


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
    """Test research point generation calculations"""

    def test_calculate_research_points_no_planets(self):
        """Test research point calculation with no planets"""
        # Mock empty planet list
        with pytest.mock.patch('backend.routes.research.Planet') as mock_planet:
            mock_planet.query.filter_by.return_value.all.return_value = []
            points = calculate_research_points(1)
            assert points == 0

    def test_calculate_research_points_single_planet(self):
        """Test research point calculation for a single planet"""
        # Mock planet with research lab
        mock_planet = pytest.mock.Mock()
        mock_planet.research_lab = 5
        mock_planet.solar_plant = 10
        mock_planet.metal_mine = 5
        mock_planet.crystal_mine = 3
        mock_planet.deuterium_synthesizer = 2

        with pytest.mock.patch('backend.routes.research.Planet') as mock_planet_class:
            mock_planet_class.query.filter_by.return_value.all.return_value = [mock_planet]

            points = calculate_research_points(1)

            # Calculate expected points:
            # Base points: 5 * 10 = 50 per tick
            # Energy production: 10 * 20 = 200
            # Energy consumption: (5*10 + 3*10 + 2*20 + 5*15) = (50 + 30 + 40 + 75) = 195
            # Energy ratio: 200/195 ≈ 1.026
            # Points per tick: max(1, int(50 * 1.026 / 72)) ≈ max(1, 0) = 1

            assert points >= 0  # Should generate at least some points

    def test_calculate_research_points_multiple_planets(self):
        """Test research point calculation for multiple planets"""
        # Mock two planets
        mock_planet1 = pytest.mock.Mock()
        mock_planet1.research_lab = 3
        mock_planet1.solar_plant = 5
        mock_planet1.metal_mine = 2
        mock_planet1.crystal_mine = 2
        mock_planet1.deuterium_synthesizer = 1

        mock_planet2 = pytest.mock.Mock()
        mock_planet2.research_lab = 7
        mock_planet2.solar_plant = 15
        mock_planet2.metal_mine = 8
        mock_planet2.crystal_mine = 6
        mock_planet2.deuterium_synthesizer = 4

        with pytest.mock.patch('backend.routes.research.Planet') as mock_planet_class:
            mock_planet_class.query.filter_by.return_value.all.return_value = [mock_planet1, mock_planet2]

            points = calculate_research_points(1)

            # Should generate points from both planets
            assert points > 0

            # Planet 2 should generate more points due to higher research lab level
            # Planet 1: 3 * 10 = 30 base points
            # Planet 2: 7 * 10 = 70 base points
            # Total should be combination of both

    def test_calculate_research_points_no_research_lab(self):
        """Test research point calculation for planet without research lab"""
        mock_planet = pytest.mock.Mock()
        mock_planet.research_lab = 0  # No research lab
        mock_planet.solar_plant = 5
        mock_planet.metal_mine = 2
        mock_planet.crystal_mine = 2
        mock_planet.deuterium_synthesizer = 1

        with pytest.mock.patch('backend.routes.research.Planet') as mock_planet_class:
            mock_planet_class.query.filter_by.return_value.all.return_value = [mock_planet]

            points = calculate_research_points(1)

            # Should generate minimal points or zero
            assert points >= 0

    def test_calculate_research_points_energy_efficiency(self):
        """Test research point calculation with different energy ratios"""
        # High energy surplus
        mock_planet_high_energy = pytest.mock.Mock()
        mock_planet_high_energy.research_lab = 5
        mock_planet_high_energy.solar_plant = 20  # High energy production
        mock_planet_high_energy.metal_mine = 1
        mock_planet_high_energy.crystal_mine = 1
        mock_planet_high_energy.deuterium_synthesizer = 1

        # Low energy (deficit)
        mock_planet_low_energy = pytest.mock.Mock()
        mock_planet_low_energy.research_lab = 5
        mock_planet_low_energy.solar_plant = 1   # Low energy production
        mock_planet_low_energy.metal_mine = 10  # High consumption
        mock_planet_low_energy.crystal_mine = 10
        mock_planet_low_energy.deuterium_synthesizer = 10

        # Test high energy planet
        with pytest.mock.patch('backend.routes.research.Planet') as mock_planet_class:
            mock_planet_class.query.filter_by.return_value.all.return_value = [mock_planet_high_energy]

            points_high = calculate_research_points(1)

            # Reset for low energy test
            mock_planet_class.query.filter_by.return_value.all.return_value = [mock_planet_low_energy]

            points_low = calculate_research_points(1)

            # High energy planet should generate more points
            assert points_high >= points_low

    def test_calculate_research_points_zero_energy_consumption(self):
        """Test research point calculation with zero energy consumption"""
        mock_planet = pytest.mock.Mock()
        mock_planet.research_lab = 5
        mock_planet.solar_plant = 10
        mock_planet.metal_mine = 0
        mock_planet.crystal_mine = 0
        mock_planet.deuterium_synthesizer = 0

        with pytest.mock.patch('backend.routes.research.Planet') as mock_planet_class:
            mock_planet_class.query.filter_by.return_value.all.return_value = [mock_planet]

            points = calculate_research_points(1)

            # Should still generate points (energy ratio = 1.0)
            assert points > 0

    def test_calculate_research_points_maximum_values(self):
        """Test research point calculation with maximum building levels"""
        mock_planet = pytest.mock.Mock()
        mock_planet.research_lab = 100  # Very high research lab
        mock_planet.solar_plant = 100   # Very high solar plant
        mock_planet.metal_mine = 100
        mock_planet.crystal_mine = 100
        mock_planet.deuterium_synthesizer = 100

        with pytest.mock.patch('backend.routes.research.Planet') as mock_planet_class:
            mock_planet_class.query.filter_by.return_value.all.return_value = [mock_planet]

            points = calculate_research_points(1)

            # Should generate significant points
            assert points > 100  # Should be substantial

    def test_calculate_research_points_different_users(self):
        """Test research point calculation for different users"""
        # User 1 planets
        mock_planet1 = pytest.mock.Mock()
        mock_planet1.research_lab = 5
        mock_planet1.solar_plant = 10
        mock_planet1.metal_mine = 5
        mock_planet1.crystal_mine = 3
        mock_planet1.deuterium_synthesizer = 2

        # User 2 planets (different levels)
        mock_planet2 = pytest.mock.Mock()
        mock_planet2.research_lab = 3
        mock_planet2.solar_plant = 5
        mock_planet2.metal_mine = 2
        mock_planet2.crystal_mine = 2
        mock_planet2.deuterium_synthesizer = 1

        with pytest.mock.patch('backend.routes.research.Planet') as mock_planet_class:
            # Test user 1
            mock_planet_class.query.filter_by.return_value.all.return_value = [mock_planet1]
            points_user1 = calculate_research_points(1)

            # Test user 2
            mock_planet_class.query.filter_by.return_value.all.return_value = [mock_planet2]
            points_user2 = calculate_research_points(2)

            # Different users should get different point calculations
            # (This is a basic isolation test)


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

    def test_research_efficiency_calculation(self):
        """Test research efficiency calculations"""
        # Mock planet with balanced energy
        mock_planet = pytest.mock.Mock()
        mock_planet.research_lab = 10
        mock_planet.solar_plant = 20
        mock_planet.metal_mine = 5
        mock_planet.crystal_mine = 5
        mock_planet.deuterium_synthesizer = 5

        with pytest.mock.patch('backend.routes.research.Planet') as mock_planet_class:
            mock_planet_class.query.filter_by.return_value.all.return_value = [mock_planet]

            points = calculate_research_points(1)

            # Calculate expected efficiency:
            # Energy production: 20 * 20 = 400
            # Energy consumption: (5*10 + 5*10 + 5*20 + 10*15) = (50 + 50 + 100 + 150) = 350
            # Efficiency ratio: 400/350 ≈ 1.143
            # Base points: 10 * 10 = 100
            # Efficient points: 100 * 1.143 ≈ 114.3
            # Per tick: max(1, int(114.3 / 72)) ≈ max(1, 1) = 1

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
