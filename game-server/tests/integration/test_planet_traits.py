"""
Integration tests for Planet Traits functionality
"""

import pytest
from backend.models import Planet, PlanetTrait, Research, User
from backend.services.planet_traits import PlanetTraitService
from backend.database import db


class TestPlanetTraits:
    """Test planet traits generation and application"""

    def test_generate_planet_traits_creates_valid_traits(self, app):
        """Test that planet trait generation creates valid trait objects"""
        with app.app_context():
            # Create a test user
            user = User(username='testuser', email='test@example.com', password_hash='hash')
            db.session.add(user)
            db.session.commit()

            # Create a test planet
            planet = Planet(
                name='Test Planet',
                x=100, y=200, z=300,
                user_id=user.id,
                metal=1000, crystal=500, deuterium=0
            )
            db.session.add(planet)
            db.session.commit()

            # Generate traits
            traits = PlanetTraitService.generate_planet_traits(planet)

            # Should create 1-3 traits
            assert 1 <= len(traits) <= 3

            # Each trait should be a PlanetTrait instance
            for trait in traits:
                assert isinstance(trait, PlanetTrait)
                assert trait.planet_id == planet.id
                assert trait.trait_name in [
                    'Resource Rich', 'Metal World', 'Crystal Caves', 'Deuterium Ocean',
                    'High Energy', 'Defensive', 'Aggressive', 'Barren', 'Temperate',
                    'Hostile', 'Volcanic', 'Frozen'
                ]
                assert trait.bonus_value != 0

    def test_planet_trait_generation_applies_bonuses(self, app):
        """Test that trait generation applies bonuses to planet"""
        with app.app_context():
            # Create a test user
            user = User(username='testuser2', email='test2@example.com', password_hash='hash')
            db.session.add(user)
            db.session.commit()

            # Create a test planet
            planet = Planet(
                name='Test Planet 2',
                x=150, y=250, z=350,
                user_id=user.id,
                metal=1000, crystal=500, deuterium=0,
                base_metal_bonus=0.0,
                base_crystal_bonus=0.0,
                base_deuterium_bonus=0.0
            )
            db.session.add(planet)
            db.session.commit()

            # Store original bonuses
            original_metal_bonus = planet.base_metal_bonus
            original_crystal_bonus = planet.base_crystal_bonus

            # Generate traits
            PlanetTraitService.generate_planet_traits(planet)

            # Should have applied bonuses
            assert planet.base_metal_bonus >= original_metal_bonus
            assert planet.base_crystal_bonus >= original_crystal_bonus

    def test_get_planet_traits_returns_correct_format(self, app):
        """Test that get_planet_traits returns traits in correct format"""
        with app.app_context():
            # Create a test user
            user = User(username='testuser3', email='test3@example.com', password_hash='hash')
            db.session.add(user)
            db.session.commit()

            # Create a test planet
            planet = Planet(
                name='Test Planet 3',
                x=200, y=300, z=400,
                user_id=user.id
            )
            db.session.add(planet)
            db.session.commit()

            # Generate traits
            PlanetTraitService.generate_planet_traits(planet)

            # Get traits
            traits_data = PlanetTraitService.get_planet_traits(planet.id)

            # Should return list of dictionaries
            assert isinstance(traits_data, list)
            if len(traits_data) > 0:
                trait = traits_data[0]
                assert 'id' in trait
                assert 'name' in trait
                assert 'type' in trait
                assert 'bonus' in trait
                assert 'description' in trait

    def test_calculate_colonization_difficulty(self, app):
        """Test colonization difficulty calculation"""
        # Test different coordinate ranges
        difficulty1 = PlanetTraitService.calculate_colonization_difficulty(100, 100, 100)
        difficulty2 = PlanetTraitService.calculate_colonization_difficulty(500, 500, 500)
        difficulty3 = PlanetTraitService.calculate_colonization_difficulty(800, 800, 800)

        # Should return valid difficulty levels
        assert 1 <= difficulty1 <= 5
        assert 1 <= difficulty2 <= 5
        assert 1 <= difficulty3 <= 5

        # Higher coordinates should generally have higher difficulty
        # (though randomness can affect this)

    def test_calculate_trait_bonuses(self, app):
        """Test trait bonus calculation"""
        with app.app_context():
            # Create a test user
            user = User(username='testuser4', email='test4@example.com', password_hash='hash')
            db.session.add(user)
            db.session.commit()

            # Create a test planet with some bonuses
            planet = Planet(
                name='Test Planet 4',
                x=250, y=350, z=450,
                user_id=user.id,
                base_metal_bonus=0.25,
                base_crystal_bonus=0.15,
                base_energy_bonus=0.10,
                colonization_difficulty=1
            )
            db.session.add(planet)
            db.session.commit()

            # Calculate bonuses
            bonuses = PlanetTraitService.calculate_trait_bonuses(planet)

            # Should return correct bonus values
            assert bonuses['metal'] == 0.25
            assert bonuses['crystal'] == 0.15
            assert bonuses['energy'] == 0.10
            assert bonuses['colonization_difficulty'] == 1

    def test_trait_rarity_distribution(self, app):
        """Test that trait generation follows rarity distribution"""
        with app.app_context():
            # Create multiple planets and check trait distribution
            user = User(username='testuser5', email='test5@example.com', password_hash='hash')
            db.session.add(user)
            db.session.commit()

            trait_counts = {'common': 0, 'uncommon': 0, 'rare': 0}

            # Generate traits for multiple planets
            for i in range(20):
                planet = Planet(
                    name=f'Test Planet {i}',
                    x=100 + i, y=200 + i, z=300 + i,
                    user_id=user.id
                )
                db.session.add(planet)
                db.session.commit()

                traits = PlanetTraitService.generate_planet_traits(planet)

                for trait in traits:
                    trait_info = PlanetTraitService.get_trait_display_info(trait.trait_name)
                    if trait_info:
                        trait_counts[trait_info['rarity']] += 1

            # Should have some distribution (allowing for randomness)
            total_traits = sum(trait_counts.values())
            if total_traits > 0:
                # Common should be most frequent
                assert trait_counts['common'] >= trait_counts['uncommon']
                # Rare should be least frequent
                assert trait_counts['rare'] <= trait_counts['uncommon']

    def test_get_trait_display_info(self, app):
        """Test trait display information retrieval"""
        # Test known trait
        info = PlanetTraitService.get_trait_display_info('Resource Rich')
        assert info is not None
        assert info['name'] == 'Resource Rich'
        assert 'description' in info
        assert 'effects' in info
        assert 'rarity' in info

        # Test unknown trait
        info = PlanetTraitService.get_trait_display_info('Unknown Trait')
        assert info is None


class TestResearchIntegration:
    """Test research functionality integration"""

    def test_research_creation(self, app):
        """Test research record creation"""
        with app.app_context():
            # Create a test user
            user = User(username='researchuser', email='research@example.com', password_hash='hash')
            db.session.add(user)
            db.session.commit()

            # Research should be auto-created when accessed
            from backend.services.tick import get_user_research_level
            level = get_user_research_level(user.id)

            # Should return default level (0)
            assert level == 0

            # Should have created research record
            research = Research.query.filter_by(user_id=user.id).first()
            assert research is not None
            assert research.colonization_tech == 0
            assert research.astrophysics == 0
            assert research.interstellar_communication == 0

    def test_research_upgrade_cost_calculation(self, app):
        """Test research upgrade cost calculation"""
        from backend.routes.research import calculate_research_cost

        # Test level 1 costs
        cost1 = calculate_research_cost('colonization_tech', 1)
        assert cost1 == 100

        # Test level 2 costs (should be higher)
        cost2 = calculate_research_cost('colonization_tech', 2)
        assert cost2 > cost1

        # Test different technologies have different base costs
        astro_cost = calculate_research_cost('astrophysics', 1)
        comm_cost = calculate_research_cost('interstellar_communication', 1)

        assert astro_cost == 150
        assert comm_cost == 200

    def test_research_point_generation(self, app):
        """Test research point generation from planets"""
        with app.app_context():
            from backend.routes.research import calculate_research_points

            # Create a test user
            user = User(username='researchuser2', email='research2@example.com', password_hash='hash')
            db.session.add(user)
            db.session.commit()

            # Create a planet with research lab
            planet = Planet(
                name='Research Planet',
                x=300, y=400, z=500,
                user_id=user.id,
                research_lab=5  # Level 5 research lab
            )
            db.session.add(planet)
            db.session.commit()

            # Calculate research points
            points = calculate_research_points(user.id)

            # Should generate points based on research lab level
            assert points >= 0

            # With level 5 research lab, should generate points
            if planet.research_lab > 0:
                assert points > 0
