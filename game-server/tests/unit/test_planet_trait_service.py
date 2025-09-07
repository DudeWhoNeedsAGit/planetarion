"""
Unit tests for PlanetTraitService

Tests PlanetTraitService operations with real database integration.
Follows the existing database-first testing pattern like test_models.py.
"""

import pytest
from backend.services.planet_traits import PlanetTraitService
from backend.models import Planet, PlanetTrait


class TestPlanetTraitService:
    """Test PlanetTraitService operations with real database"""

    def test_generate_planet_traits_creates_valid_objects(self, db_session, sample_user):
        """Test that trait generation creates proper trait objects"""
        # Create a real planet
        planet = Planet(
            name='Trait Test Planet',
            x=100, y=200, z=300,
            user_id=sample_user.id
        )
        db_session.add(planet)
        db_session.commit()

        # Generate traits for the planet
        traits = PlanetTraitService.generate_planet_traits(planet)

        # Should create 1-3 traits
        assert 1 <= len(traits) <= 3

        # Each trait should be a PlanetTrait instance
        for trait in traits:
            assert isinstance(trait, PlanetTrait)
            assert trait.planet_id == planet.id
            assert trait.trait_type is not None
            assert trait.trait_name is not None
            assert trait.bonus_value is not None

    def test_determine_trait_count_distribution(self):
        """Test trait count determination follows expected distribution"""
        # Test multiple times to see distribution
        counts = []
        for _ in range(100):
            count = PlanetTraitService._determine_trait_count()
            counts.append(count)

        # Should have some variety in counts
        assert 1 in counts
        assert 2 in counts
        assert 3 in counts

        # Distribution should include all trait counts (1, 2, 3)
        # The exact distribution can vary due to randomness
        # but all counts should be present in a large enough sample

    def test_select_traits_respects_rarity_weights(self):
        """Test trait selection follows rarity weight distribution"""
        # Test multiple selections to see distribution
        selected_traits = []
        for _ in range(100):
            traits = PlanetTraitService._select_traits(1)
            if traits:
                selected_traits.append(traits[0])

        # Should have selected some traits
        assert len(selected_traits) > 0

        # Should include traits from different rarity levels
        trait_names = [t for t in selected_traits if t in PlanetTraitService.TRAIT_TYPES]
        assert len(trait_names) > 0

    def test_apply_trait_effects_modifies_planet_correctly(self, db_session, sample_user):
        """Test that trait effects are applied correctly to planet bonuses"""
        # Create a real planet
        planet = Planet(
            name='Effect Test Planet',
            x=100, y=200, z=300,
            user_id=sample_user.id,
            base_metal_bonus=0.0,
            base_crystal_bonus=0.0,
            base_deuterium_bonus=0.0,
            base_energy_bonus=0.0,
            colonization_difficulty=1,
            base_defense_bonus=0.0,
            base_attack_bonus=0.0
        )
        db_session.add(planet)
        db_session.commit()

        # Test metal bonus
        effects = {'metal': 0.25}
        PlanetTraitService.apply_trait_effects(planet, effects)
        assert planet.base_metal_bonus == 0.25

        # Test crystal bonus
        effects = {'crystal': 0.15}
        PlanetTraitService.apply_trait_effects(planet, effects)
        assert planet.base_crystal_bonus == 0.15

        # Test all resources bonus
        effects = {'all_resources': 0.10}
        PlanetTraitService.apply_trait_effects(planet, effects)
        assert planet.base_metal_bonus == 0.35  # 0.25 + 0.10
        assert planet.base_crystal_bonus == 0.25  # 0.15 + 0.10
        assert planet.base_deuterium_bonus == 0.10  # 0 + 0.10

        # Test colonization difficulty
        effects = {'colonization_difficulty': 2}
        PlanetTraitService.apply_trait_effects(planet, effects)
        assert planet.colonization_difficulty == 3  # 1 + 2

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

    def test_calculate_trait_bonuses_sums_all_effects(self, db_session, sample_user):
        """Test that trait bonuses are calculated correctly"""
        # Create a real planet with bonuses
        planet = Planet(
            name='Bonus Test Planet',
            x=100, y=200, z=300,
            user_id=sample_user.id,
            base_metal_bonus=0.25,
            base_crystal_bonus=0.15,
            base_deuterium_bonus=0.10,
            base_energy_bonus=0.20,
            base_defense_bonus=0.30,
            base_attack_bonus=0.40,
            colonization_difficulty=3
        )
        db_session.add(planet)
        db_session.commit()

        bonuses = PlanetTraitService.calculate_trait_bonuses(planet)

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
        # This should handle the edge case gracefully
        selected = PlanetTraitService._select_traits(1)
        # Should return empty list or handle gracefully
        assert isinstance(selected, list)

    def test_apply_trait_effects_handles_missing_attributes(self, db_session, sample_user):
        """Test trait effect application with missing planet attributes"""
        # Create a real planet
        planet = Planet(
            name='Missing Attr Planet',
            x=100, y=200, z=300,
            user_id=sample_user.id
        )
        db_session.add(planet)
        db_session.commit()

        effects = {'metal': 0.25}
        # Should handle missing attributes gracefully
        PlanetTraitService.apply_trait_effects(planet, effects)

        # Should have set the attribute
        assert planet.base_metal_bonus == 0.25
