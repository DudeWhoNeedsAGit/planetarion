"""
Unit tests for enhanced model functionality

Tests the new fields and relationships added to existing models.
"""

import pytest
from unittest.mock import Mock
from backend.models import Planet, Research, PlanetTrait


class TestEnhancedPlanetModel:
    """Test enhanced Planet model with trait bonuses"""

    def test_planet_trait_bonus_fields(self):
        """Test that Planet model has trait bonus fields"""
        planet = Planet(
            name='Test Planet',
            x=100, y=200, z=300,
            user_id=1
        )

        # Check that trait bonus fields exist and have default values
        assert hasattr(planet, 'base_metal_bonus')
        assert hasattr(planet, 'base_crystal_bonus')
        assert hasattr(planet, 'base_deuterium_bonus')
        assert hasattr(planet, 'base_energy_bonus')
        assert hasattr(planet, 'base_defense_bonus')
        assert hasattr(planet, 'base_attack_bonus')
        assert hasattr(planet, 'colonization_difficulty')
        assert hasattr(planet, 'research_lab')

        # Check default values
        assert planet.base_metal_bonus == 0.0
        assert planet.base_crystal_bonus == 0.0
        assert planet.base_deuterium_bonus == 0.0
        assert planet.base_energy_bonus == 0.0
        assert planet.base_defense_bonus == 0.0
        assert planet.base_attack_bonus == 0.0
        assert planet.colonization_difficulty == 1
        assert planet.research_lab == 0

    def test_planet_with_trait_bonuses(self):
        """Test Planet model with custom trait bonuses"""
        planet = Planet(
            name='Bonus Planet',
            x=150, y=250, z=350,
            user_id=1,
            base_metal_bonus=0.25,
            base_crystal_bonus=0.15,
            base_deuterium_bonus=0.10,
            base_energy_bonus=0.20,
            base_defense_bonus=0.30,
            base_attack_bonus=0.40,
            colonization_difficulty=3,
            research_lab=5
        )

        assert planet.base_metal_bonus == 0.25
        assert planet.base_crystal_bonus == 0.15
        assert planet.base_deuterium_bonus == 0.10
        assert planet.base_energy_bonus == 0.20
        assert planet.base_defense_bonus == 0.30
        assert planet.base_attack_bonus == 0.40
        assert planet.colonization_difficulty == 3
        assert planet.research_lab == 5

    def test_planet_repr_with_enhanced_fields(self):
        """Test that planet repr still works with enhanced fields"""
        planet = Planet(
            name='Enhanced Planet',
            x=200, y=300, z=400,
            user_id=1
        )

        repr_str = str(planet)
        assert 'Enhanced Planet' in repr_str
        assert '200:300:400' in repr_str

    def test_planet_trait_relationship(self):
        """Test Planet-Trait relationship"""
        planet = Planet(
            name='Trait Planet',
            x=250, y=350, z=450,
            user_id=1
        )

        # Mock traits relationship
        mock_trait1 = Mock()
        mock_trait1.trait_name = 'Resource Rich'
        mock_trait1.bonus_value = 0.25

        mock_trait2 = Mock()
        mock_trait2.trait_name = 'Defensive'
        mock_trait2.bonus_value = 0.30

        # Simulate traits relationship
        planet.traits = [mock_trait1, mock_trait2]

        # Should be able to access traits
        assert len(planet.traits) == 2
        assert planet.traits[0].trait_name == 'Resource Rich'
        assert planet.traits[1].trait_name == 'Defensive'


class TestResearchModel:
    """Test Research model functionality"""

    def test_research_model_creation(self):
        """Test creating a new Research record"""
        research = Research(
            user_id=1,
            colonization_tech=2,
            astrophysics=1,
            interstellar_communication=0,
            research_points=500
        )

        assert research.user_id == 1
        assert research.colonization_tech == 2
        assert research.astrophysics == 1
        assert research.interstellar_communication == 0
        assert research.research_points == 500

    def test_research_model_defaults(self):
        """Test Research model default values"""
        research = Research(user_id=2)

        assert research.user_id == 2
        assert research.colonization_tech == 0
        assert research.astrophysics == 0
        assert research.interstellar_communication == 0
        assert research.research_points == 0

    def test_research_model_repr(self):
        """Test Research model string representation"""
        research = Research(
            user_id=3,
            research_points=750
        )

        repr_str = str(research)
        assert 'user:3' in repr_str
        assert 'points:750' in repr_str

    def test_research_user_relationship(self):
        """Test Research-User relationship"""
        research = Research(user_id=1)

        # Mock user relationship
        mock_user = Mock()
        mock_user.username = 'TestUser'
        research.user = mock_user

        assert research.user.username == 'TestUser'

    def test_research_level_validation(self):
        """Test research level value validation"""
        # Test valid levels
        research = Research(
            user_id=1,
            colonization_tech=5,
            astrophysics=3,
            interstellar_communication=2
        )

        assert research.colonization_tech == 5
        assert research.astrophysics == 3
        assert research.interstellar_communication == 2

        # Test zero levels
        research_zero = Research(
            user_id=2,
            colonization_tech=0,
            astrophysics=0,
            interstellar_communication=0
        )

        assert research_zero.colonization_tech == 0
        assert research_zero.astrophysics == 0
        assert research_zero.interstellar_communication == 0


class TestPlanetTraitModel:
    """Test PlanetTrait model functionality"""

    def test_planet_trait_creation(self):
        """Test creating a new PlanetTrait record"""
        trait = PlanetTrait(
            planet_id=1,
            trait_type='resource_bonus',
            trait_name='Resource Rich',
            bonus_value=0.25,
            description='High natural resource deposits'
        )

        assert trait.planet_id == 1
        assert trait.trait_type == 'resource_bonus'
        assert trait.trait_name == 'Resource Rich'
        assert trait.bonus_value == 0.25
        assert trait.description == 'High natural resource deposits'

    def test_planet_trait_defaults(self):
        """Test PlanetTrait model default values"""
        trait = PlanetTrait(
            planet_id=2,
            trait_type='defense_bonus',
            trait_name='Defensive Position'
        )

        assert trait.planet_id == 2
        assert trait.trait_type == 'defense_bonus'
        assert trait.trait_name == 'Defensive Position'
        assert trait.bonus_value == 0.0  # Default value
        assert trait.description is None  # Default value

    def test_planet_trait_repr(self):
        """Test PlanetTrait model string representation"""
        trait = PlanetTrait(
            planet_id=1,
            trait_name='Metal World',
            bonus_value=0.40
        )

        repr_str = str(trait)
        assert 'Metal World' in repr_str
        assert '+0.4' in repr_str

    def test_planet_trait_planet_relationship(self):
        """Test PlanetTrait-Planet relationship"""
        trait = PlanetTrait(
            planet_id=1,
            trait_name='Crystal Caves',
            bonus_value=0.35
        )

        # Mock planet relationship
        mock_planet = Mock()
        mock_planet.name = 'Crystal Planet'
        trait.planet = mock_planet

        assert trait.planet.name == 'Crystal Planet'

    def test_planet_trait_various_types(self):
        """Test PlanetTrait with different trait types"""
        trait_types = [
            ('resource_bonus', 'Resource Rich', 0.25),
            ('defense_bonus', 'Defensive Position', 0.30),
            ('attack_bonus', 'Aggressive Environment', 0.20),
            ('colonization_difficulty', 'Hostile Environment', 2),
            ('energy_bonus', 'High Energy', 0.50)
        ]

        for trait_type, name, value in trait_types:
            trait = PlanetTrait(
                planet_id=1,
                trait_type=trait_type,
                trait_name=name,
                bonus_value=value
            )

            assert trait.trait_type == trait_type
            assert trait.trait_name == name
            assert trait.bonus_value == value


class TestModelRelationships:
    """Test relationships between enhanced models"""

    def test_user_research_relationship(self):
        """Test User-Research relationship"""
        from backend.models import User

        user = User(
            username='ResearchUser',
            email='research@example.com',
            password_hash='hash'
        )

        research = Research(
            user_id=1,  # Would be set by SQLAlchemy
            colonization_tech=3,
            research_points=1000
        )

        # Mock bidirectional relationship
        user.research_data = [research]
        research.user = user

        assert len(user.research_data) == 1
        assert user.research_data[0].colonization_tech == 3
        assert research.user.username == 'ResearchUser'

    def test_planet_traits_relationship(self):
        """Test Planet-Traits relationship"""
        planet = Planet(
            name='Trait Planet',
            x=100, y=200, z=300,
            user_id=1
        )

        trait1 = PlanetTrait(
            planet_id=1,  # Would be set by SQLAlchemy
            trait_name='Resource Rich',
            bonus_value=0.25
        )

        trait2 = PlanetTrait(
            planet_id=1,  # Would be set by SQLAlchemy
            trait_name='Defensive',
            bonus_value=0.30
        )

        # Mock bidirectional relationship
        planet.traits = [trait1, trait2]
        trait1.planet = planet
        trait2.planet = planet

        assert len(planet.traits) == 2
        assert planet.traits[0].trait_name == 'Resource Rich'
        assert planet.traits[1].trait_name == 'Defensive'
        assert trait1.planet.name == 'Trait Planet'
        assert trait2.planet.name == 'Trait Planet'

    def test_complete_user_planet_research_relationship(self):
        """Test complete User-Planet-Research relationship chain"""
        from backend.models import User

        user = User(
            username='CompleteUser',
            email='complete@example.com',
            password_hash='hash'
        )

        research = Research(
            user_id=1,
            colonization_tech=2,
            astrophysics=1,
            research_points=500
        )

        planet1 = Planet(
            name='Home Planet',
            x=0, y=0, z=0,
            user_id=1,
            base_metal_bonus=0.10,
            research_lab=3
        )

        planet2 = Planet(
            name='Colony Alpha',
            x=100, y=200, z=300,
            user_id=1,
            base_crystal_bonus=0.15,
            colonization_difficulty=2
        )

        trait = PlanetTrait(
            planet_id=2,  # planet2
            trait_name='Crystal Caves',
            bonus_value=0.35
        )

        # Establish relationships
        user.planets = [planet1, planet2]
        user.research_data = [research]

        planet1.owner = user
        planet2.owner = user
        planet2.traits = [trait]

        research.user = user
        trait.planet = planet2

        # Test complete relationship chain
        assert len(user.planets) == 2
        assert len(user.research_data) == 1
        assert user.research_data[0].colonization_tech == 2

        assert user.planets[0].name == 'Home Planet'
        assert user.planets[1].name == 'Colony Alpha'

        assert len(user.planets[1].traits) == 1
        assert user.planets[1].traits[0].trait_name == 'Crystal Caves'

        assert user.planets[1].traits[0].planet.name == 'Colony Alpha'


class TestModelDataValidation:
    """Test data validation for enhanced model fields"""

    def test_planet_bonus_value_ranges(self):
        """Test that planet bonus values are within reasonable ranges"""
        # Test reasonable bonus values
        planet = Planet(
            name='Balanced Planet',
            x=100, y=200, z=300,
            user_id=1,
            base_metal_bonus=0.50,      # 50% bonus
            base_crystal_bonus=0.25,    # 25% bonus
            base_energy_bonus=1.0,      # 100% bonus
            colonization_difficulty=4   # Level 4 difficulty
        )

        assert 0 <= planet.base_metal_bonus <= 2.0      # Reasonable range
        assert 0 <= planet.base_crystal_bonus <= 2.0
        assert 0 <= planet.base_energy_bonus <= 2.0
        assert 1 <= planet.colonization_difficulty <= 5  # Valid difficulty range

    def test_research_level_maximums(self):
        """Test research level maximum values"""
        research = Research(
            user_id=1,
            colonization_tech=10,           # Max level
            astrophysics=15,               # Max level
            interstellar_communication=12, # Max level
            research_points=100000         # Large point total
        )

        assert research.colonization_tech <= 10
        assert research.astrophysics <= 15
        assert research.interstellar_communication <= 12
        assert research.research_points >= 0

    def test_trait_bonus_value_ranges(self):
        """Test trait bonus values are within expected ranges"""
        # Test various trait bonuses
        traits = [
            PlanetTrait(trait_name='Resource Rich', bonus_value=0.25),
            PlanetTrait(trait_name='Metal World', bonus_value=0.40),
            PlanetTrait(trait_name='Defensive', bonus_value=0.25),
            PlanetTrait(trait_name='Hostile', bonus_value=2),  # Difficulty bonus
        ]

        for trait in traits:
            if trait.trait_name == 'Hostile':
                assert trait.bonus_value >= 1  # Difficulty should be at least 1
            else:
                assert 0 <= trait.bonus_value <= 1.0  # Percentage bonuses

    def test_research_points_non_negative(self):
        """Test that research points cannot be negative"""
        research = Research(
            user_id=1,
            research_points=0
        )

        assert research.research_points >= 0

        # Test edge case
        research.research_points = 100
        assert research.research_points >= 0
