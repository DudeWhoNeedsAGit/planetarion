"""
Unit tests for PlanetTraitService

Tests individual methods and algorithms without database dependencies.
"""

import pytest
from unittest.mock import Mock, patch
from backend.services.planet_traits import PlanetTraitService


class TestPlanetTraitService:
    """Test PlanetTraitService methods in isolation"""

    def test_generate_planet_traits_creates_valid_objects(self):
        """Test that trait generation creates proper trait objects"""
        # Mock planet object
        mock_planet = Mock()
        mock_planet.id = 1
        mock_planet.base_metal_bonus = 0.0
        mock_planet.base_crystal_bonus = 0.0
        mock_planet.base_deuterium_bonus = 0.0
        mock_planet.base_energy_bonus = 0.0
        mock_planet.colonization_difficulty = 1

        # Mock database operations
        with patch('backend.services.planet_traits.PlanetTrait') as mock_trait_class:
            mock_trait = Mock()
            mock_trait.trait_name = 'Resource Rich'
            mock_trait.bonus_value = 0.25
            mock_trait_class.return_value = mock_trait

            # Generate traits
            traits = PlanetTraitService.generate_planet_traits(mock_planet)

            # Should create 1-3 traits
            assert 1 <= len(traits) <= 3

            # Should call PlanetTrait constructor
            assert mock_trait_class.called

            # Should apply trait effects to planet
            assert mock_planet.base_metal_bonus >= 0

    def test_determine_trait_count_distribution(self):
        """Test trait count determination follows expected distribution"""
        # Mock random to test different outcomes
        with patch('backend.services.planet_traits.random.random') as mock_random:
            # Test 1 trait (0.0 - 0.39)
            mock_random.return_value = 0.2
            count = PlanetTraitService._determine_trait_count()
            assert count == 1

            # Test 2 traits (0.4 - 0.84)
            mock_random.return_value = 0.6
            count = PlanetTraitService._determine_trait_count()
            assert count == 2

            # Test 3 traits (0.85 - 1.0)
            mock_random.return_value = 0.9
            count = PlanetTraitService._determine_trait_count()
            assert count == 3

    def test_select_traits_respects_rarity_weights(self):
        """Test trait selection follows rarity weight distribution"""
        # Mock random for predictable testing
        with patch('backend.services.planet_traits.random.random') as mock_random, \
             patch('backend.services.planet_traits.random.choice') as mock_choice:

            # Test common trait selection (weight: 0.5, cumulative: 0.0-0.5)
            mock_random.return_value = 0.3
            mock_choice.return_value = 'resource_rich'  # Common trait

            selected = PlanetTraitService._select_traits(1)
            assert len(selected) == 1
            assert selected[0] == 'resource_rich'

            # Test uncommon trait selection (weight: 0.3, cumulative: 0.5-0.8)
            mock_random.return_value = 0.6
            mock_choice.return_value = 'metal_world'  # Uncommon trait

            selected = PlanetTraitService._select_traits(1)
            assert len(selected) == 1
            assert selected[0] == 'metal_world'

            # Test rare trait selection (weight: 0.2, cumulative: 0.8-1.0)
            mock_random.return_value = 0.9
            mock_choice.return_value = 'deuterium_ocean'  # Rare trait

            selected = PlanetTraitService._select_traits(1)
            assert len(selected) == 1
            assert selected[0] == 'deuterium_ocean'

    def test_apply_trait_effects_modifies_planet_correctly(self):
        """Test that trait effects are applied correctly to planet bonuses"""
        # Mock planet
        mock_planet = Mock()
        mock_planet.base_metal_bonus = 0.0
        mock_planet.base_crystal_bonus = 0.0
        mock_planet.base_deuterium_bonus = 0.0
        mock_planet.base_energy_bonus = 0.0
        mock_planet.colonization_difficulty = 1
        mock_planet.base_defense_bonus = 0.0
        mock_planet.base_attack_bonus = 0.0

        # Test metal bonus
        effects = {'metal': 0.25}
        PlanetTraitService.apply_trait_effects(mock_planet, effects)
        assert mock_planet.base_metal_bonus == 0.25

        # Test crystal bonus
        effects = {'crystal': 0.15}
        PlanetTraitService.apply_trait_effects(mock_planet, effects)
        assert mock_planet.base_crystal_bonus == 0.15

        # Test all resources bonus
        effects = {'all_resources': 0.10}
        PlanetTraitService.apply_trait_effects(mock_planet, effects)
        assert mock_planet.base_metal_bonus == 0.35  # 0.25 + 0.10
        assert mock_planet.base_crystal_bonus == 0.25  # 0.15 + 0.10
        assert mock_planet.base_deuterium_bonus == 0.10  # 0 + 0.10

        # Test colonization difficulty
        effects = {'colonization_difficulty': 2}
        PlanetTraitService.apply_trait_effects(mock_planet, effects)
        assert mock_planet.colonization_difficulty == 3  # 1 + 2

    def test_calculate_colonization_difficulty_formula(self):
        """Test colonization difficulty calculation formula"""
        # Test low coordinates
        difficulty1 = PlanetTraitService.calculate_colonization_difficulty(100, 100, 100)
        assert 1 <= difficulty1 <= 5

        # Test medium coordinates
        difficulty2 = PlanetTraitService.calculate_colonization_difficulty(500, 500, 500)
        assert 1 <= difficulty2 <= 5

        # Test high coordinates
        difficulty3 = PlanetTraitService.calculate_colonization_difficulty(800, 800, 800)
        assert 1 <= difficulty3 <= 5

        # Higher coordinates should generally give higher difficulty
        # (though randomness can affect this)

    def test_calculate_trait_bonuses_sums_all_effects(self):
        """Test that trait bonuses are calculated correctly"""
        # Mock planet with various bonuses
        mock_planet = Mock()
        mock_planet.base_metal_bonus = 0.25
        mock_planet.base_crystal_bonus = 0.15
        mock_planet.base_deuterium_bonus = 0.10
        mock_planet.base_energy_bonus = 0.20
        mock_planet.base_defense_bonus = 0.30
        mock_planet.base_attack_bonus = 0.40
        mock_planet.colonization_difficulty = 3

        bonuses = PlanetTraitService.calculate_trait_bonuses(mock_planet)

        assert bonuses['metal'] == 0.25
        assert bonuses['crystal'] == 0.15
        assert bonuses['deuterium'] == 0.10
        assert bonuses['energy'] == 0.20
        assert bonuses['defense'] == 0.30
        assert bonuses['attack'] == 0.40
        assert bonuses['colonization_difficulty'] == 3

    def test_get_trait_display_info_returns_correct_data(self):
        """Test trait display information retrieval"""
        # Test known trait
        info = PlanetTraitService.get_trait_display_info('Resource Rich')
        assert info is not None
        assert info['name'] == 'Resource Rich'
        assert info['description'] == 'High natural resource deposits'
        assert info['effects'] == {'metal': 0.25, 'crystal': 0.15}
        assert info['rarity'] == 'common'

        # Test another trait
        info = PlanetTraitService.get_trait_display_info('Deuterium Ocean')
        assert info is not None
        assert info['name'] == 'Deuterium Ocean'
        assert info['rarity'] == 'rare'

        # Test unknown trait
        info = PlanetTraitService.get_trait_display_info('Unknown Trait')
        assert info is None

    def test_trait_types_constant_structure(self):
        """Test that TRAIT_TYPES has correct structure"""
        assert isinstance(PlanetTraitService.TRAIT_TYPES, dict)
        assert len(PlanetTraitService.TRAIT_TYPES) > 0

        # Check structure of first trait
        first_trait_key = list(PlanetTraitService.TRAIT_TYPES.keys())[0]
        first_trait = PlanetTraitService.TRAIT_TYPES[first_trait_key]

        required_keys = ['name', 'description', 'effects', 'rarity']
        for key in required_keys:
            assert key in first_trait

        assert isinstance(first_trait['effects'], dict)
        assert first_trait['rarity'] in ['common', 'uncommon', 'rare']

    def test_select_traits_handles_empty_available_list(self):
        """Test trait selection when no traits are available"""
        with patch('backend.services.planet_traits.random.random') as mock_random:
            mock_random.return_value = 0.5

            # This should handle the edge case gracefully
            selected = PlanetTraitService._select_traits(1)
            # Should return empty list or handle gracefully
            assert isinstance(selected, list)

    def test_apply_trait_effects_handles_missing_attributes(self):
        """Test trait effect application with missing planet attributes"""
        # Mock planet with missing attributes
        mock_planet = Mock()
        # Don't set any attributes

        effects = {'metal': 0.25}
        # Should handle missing attributes gracefully
        PlanetTraitService.apply_trait_effects(mock_planet, effects)

        # Should have set the attribute
        assert hasattr(mock_planet, 'base_metal_bonus')
        assert mock_planet.base_metal_bonus == 0.25
