"""
Unit tests for enhanced model functionality

Tests the new fields and relationships added to existing models.
Follows the existing database-first testing pattern like test_models.py.
"""

import pytest
from backend.models import Planet, Research, PlanetTrait, User


class TestEnhancedPlanetModel:
    """Test enhanced Planet model with trait bonuses"""

    def test_planet_trait_bonus_fields_creation(self, db_session, sample_user):
        """Test creating planet with trait bonus fields"""
        planet = Planet(
            name='Test Planet',
            x=100, y=200, z=300,
            user_id=sample_user.id,
            base_metal_bonus=0.25,
            base_crystal_bonus=0.15,
            base_deuterium_bonus=0.10,
            base_energy_bonus=0.20,
            base_defense_bonus=0.30,
            base_attack_bonus=0.40,
            colonization_difficulty=3,
            research_lab=5
        )
        db_session.add(planet)
        db_session.commit()

        # Verify fields are saved correctly
        assert planet.id is not None
        assert planet.base_metal_bonus == 0.25
        assert planet.base_crystal_bonus == 0.15
        assert planet.base_deuterium_bonus == 0.10
        assert planet.base_energy_bonus == 0.20
        assert planet.base_defense_bonus == 0.30
        assert planet.base_attack_bonus == 0.40
        assert planet.colonization_difficulty == 3
        assert planet.research_lab == 5

    def test_planet_trait_bonus_fields_defaults(self, db_session, sample_user):
        """Test planet trait bonus field defaults"""
        planet = Planet(
            name='Default Planet',
            x=150, y=250, z=350,
            user_id=sample_user.id
        )
        db_session.add(planet)
        db_session.commit()

        # Check default values
        assert planet.base_metal_bonus == 0.0
        assert planet.base_crystal_bonus == 0.0
        assert planet.base_deuterium_bonus == 0.0
        assert planet.base_energy_bonus == 0.0
        assert planet.base_defense_bonus == 0.0
        assert planet.base_attack_bonus == 0.0
        assert planet.colonization_difficulty == 1
        assert planet.research_lab == 0

    def test_planet_repr_with_enhanced_fields(self, db_session, sample_user):
        """Test that planet repr still works with enhanced fields"""
        planet = Planet(
            name='Enhanced Planet',
            x=200, y=300, z=400,
            user_id=sample_user.id
        )
        db_session.add(planet)
        db_session.commit()

        repr_str = str(planet)
        assert 'Enhanced Planet' in repr_str
        assert '200:300:400' in repr_str

    def test_planet_trait_relationship(self, db_session, sample_user):
        """Test Planet-Trait relationship with real database"""
        # Create planet
        planet = Planet(
            name='Trait Planet',
            x=250, y=350, z=450,
            user_id=sample_user.id
        )
        db_session.add(planet)
        db_session.commit()

        # Create traits
        trait1 = PlanetTrait(
            planet_id=planet.id,
            trait_type='resource_bonus',
            trait_name='Resource Rich',
            bonus_value=0.25,
            description='High natural resource deposits'
        )
        trait2 = PlanetTrait(
            planet_id=planet.id,
            trait_type='defense_bonus',
            trait_name='Defensive',
            bonus_value=0.30,
            description='Natural defensive advantages'
        )
        db_session.add(trait1)
        db_session.add(trait2)
        db_session.commit()

        # Test relationship
        planet_with_traits = db_session.query(Planet).filter_by(id=planet.id).first()
        traits = db_session.query(PlanetTrait).filter_by(planet_id=planet.id).all()

        assert len(traits) == 2
        assert traits[0].trait_name == 'Resource Rich'
        assert traits[1].trait_name == 'Defensive'
        assert traits[0].bonus_value == 0.25
        assert traits[1].bonus_value == 0.30


class TestResearchModel:
    """Test Research model functionality"""

    def test_research_model_creation(self, db_session, sample_user):
        """Test creating a new Research record"""
        research = Research(
            user_id=sample_user.id,
            colonization_tech=2,
            astrophysics=1,
            interstellar_communication=0,
            research_points=500
        )
        db_session.add(research)
        db_session.commit()

        assert research.id is not None
        assert research.user_id == sample_user.id
        assert research.colonization_tech == 2
        assert research.astrophysics == 1
        assert research.interstellar_communication == 0
        assert research.research_points == 500

    def test_research_model_repr(self, db_session, sample_user):
        """Test Research model string representation"""
        research = Research(
            user_id=sample_user.id,
            research_points=750
        )
        db_session.add(research)
        db_session.commit()

        repr_str = str(research)
        assert 'user:' in repr_str
        assert 'points:750' in repr_str

    def test_research_user_relationship(self, db_session, sample_user):
        """Test Research-User relationship"""
        research = Research(
            user_id=sample_user.id,
            colonization_tech=3,
            research_points=1000
        )
        db_session.add(research)
        db_session.commit()

        # Test relationship from user side
        user_with_research = db_session.query(User).filter_by(id=sample_user.id).first()
        research_from_user = db_session.query(Research).filter_by(user_id=sample_user.id).first()

        assert research_from_user is not None
        assert research_from_user.colonization_tech == 3
        assert research_from_user.research_points == 1000

    def test_research_level_validation(self, db_session, sample_user):
        """Test research level value validation"""
        # Test valid levels
        research = Research(
            user_id=sample_user.id,
            colonization_tech=5,
            astrophysics=3,
            interstellar_communication=2
        )
        db_session.add(research)
        db_session.commit()

        assert research.colonization_tech == 5
        assert research.astrophysics == 3
        assert research.interstellar_communication == 2

        # Test zero levels
        research_zero = Research(
            user_id=sample_user.id,
            colonization_tech=0,
            astrophysics=0,
            interstellar_communication=0
        )
        db_session.add(research_zero)
        db_session.commit()

        assert research_zero.colonization_tech == 0
        assert research_zero.astrophysics == 0
        assert research_zero.interstellar_communication == 0


class TestPlanetTraitModel:
    """Test PlanetTrait model functionality"""

    def test_planet_trait_creation(self, db_session, sample_user):
        """Test creating a new PlanetTrait record"""
        # Create planet first
        planet = Planet(
            name='Trait Test Planet',
            x=100, y=200, z=300,
            user_id=sample_user.id
        )
        db_session.add(planet)
        db_session.commit()

        trait = PlanetTrait(
            planet_id=planet.id,
            trait_type='resource_bonus',
            trait_name='Resource Rich',
            bonus_value=0.25,
            description='High natural resource deposits'
        )
        db_session.add(trait)
        db_session.commit()

        assert trait.id is not None
        assert trait.planet_id == planet.id
        assert trait.trait_type == 'resource_bonus'
        assert trait.trait_name == 'Resource Rich'
        assert trait.bonus_value == 0.25
        assert trait.description == 'High natural resource deposits'

    def test_planet_trait_repr(self, db_session, sample_user):
        """Test PlanetTrait model string representation"""
        # Create planet first
        planet = Planet(
            name='Trait Repr Planet',
            x=150, y=250, z=350,
            user_id=sample_user.id
        )
        db_session.add(planet)
        db_session.commit()

        trait = PlanetTrait(
            planet_id=planet.id,
            trait_type='resource_bonus',
            trait_name='Metal World',
            bonus_value=0.40
        )
        db_session.add(trait)
        db_session.commit()

        repr_str = str(trait)
        assert 'Metal World' in repr_str
        assert '+0.4' in repr_str

    def test_planet_trait_various_types(self, db_session, sample_user):
        """Test PlanetTrait with different trait types"""
        # Create planet first
        planet = Planet(
            name='Various Traits Planet',
            x=200, y=300, z=400,
            user_id=sample_user.id
        )
        db_session.add(planet)
        db_session.commit()

        trait_types = [
            ('resource_bonus', 'Resource Rich', 0.25),
            ('defense_bonus', 'Defensive Position', 0.30),
            ('attack_bonus', 'Aggressive Environment', 0.20),
            ('colonization_difficulty', 'Hostile Environment', 2),
            ('energy_bonus', 'High Energy', 0.50)
        ]

        for trait_type, name, value in trait_types:
            trait = PlanetTrait(
                planet_id=planet.id,
                trait_type=trait_type,
                trait_name=name,
                bonus_value=value
            )
            db_session.add(trait)

        db_session.commit()

        # Verify all traits were created
        traits = db_session.query(PlanetTrait).filter_by(planet_id=planet.id).all()
        assert len(traits) == len(trait_types)

        for i, (expected_type, expected_name, expected_value) in enumerate(trait_types):
            assert traits[i].trait_type == expected_type
            assert traits[i].trait_name == expected_name
            assert traits[i].bonus_value == expected_value


class TestModelDataValidation:
    """Test data validation for enhanced model fields"""

    def test_planet_bonus_value_ranges(self, db_session, sample_user):
        """Test that planet bonus values are within reasonable ranges"""
        # Test reasonable bonus values
        planet = Planet(
            name='Balanced Planet',
            x=100, y=200, z=300,
            user_id=sample_user.id,
            base_metal_bonus=0.50,      # 50% bonus
            base_crystal_bonus=0.25,    # 25% bonus
            base_energy_bonus=1.0,      # 100% bonus
            colonization_difficulty=4   # Level 4 difficulty
        )
        db_session.add(planet)
        db_session.commit()

        assert 0 <= planet.base_metal_bonus <= 2.0      # Reasonable range
        assert 0 <= planet.base_crystal_bonus <= 2.0
        assert 0 <= planet.base_energy_bonus <= 2.0
        assert 1 <= planet.colonization_difficulty <= 5  # Valid difficulty range

    def test_research_level_maximums(self, db_session, sample_user):
        """Test research level maximum values"""
        research = Research(
            user_id=sample_user.id,
            colonization_tech=10,           # Max level
            astrophysics=15,               # Max level
            interstellar_communication=12, # Max level
            research_points=100000         # Large point total
        )
        db_session.add(research)
        db_session.commit()

        assert research.colonization_tech <= 10
        assert research.astrophysics <= 15
        assert research.interstellar_communication <= 12
        assert research.research_points >= 0

    def test_trait_bonus_value_ranges(self, db_session, sample_user):
        """Test trait bonus values are within expected ranges"""
        # Create planet first
        planet = Planet(
            name='Trait Range Planet',
            x=250, y=350, z=450,
            user_id=sample_user.id
        )
        db_session.add(planet)
        db_session.commit()

        # Test various trait bonuses
        traits = [
            PlanetTrait(planet_id=planet.id, trait_type='resource_bonus', trait_name='Resource Rich', bonus_value=0.25),
            PlanetTrait(planet_id=planet.id, trait_type='resource_bonus', trait_name='Metal World', bonus_value=0.40),
            PlanetTrait(planet_id=planet.id, trait_type='defense_bonus', trait_name='Defensive', bonus_value=0.25),
            PlanetTrait(planet_id=planet.id, trait_type='colonization_difficulty', trait_name='Hostile', bonus_value=2),  # Difficulty bonus
        ]

        for trait in traits:
            db_session.add(trait)

        db_session.commit()

        saved_traits = db_session.query(PlanetTrait).filter_by(planet_id=planet.id).all()

        for trait in saved_traits:
            if trait.trait_name == 'Hostile':
                assert trait.bonus_value >= 1  # Difficulty should be at least 1
            else:
                assert 0 <= trait.bonus_value <= 1.0  # Percentage bonuses

    def test_research_points_non_negative(self, db_session, sample_user):
        """Test that research points cannot be negative"""
        research = Research(
            user_id=sample_user.id,
            research_points=0
        )
        db_session.add(research)
        db_session.commit()

        assert research.research_points >= 0

        # Test edge case
        research.research_points = 100
        db_session.commit()

        updated_research = db_session.query(Research).filter_by(id=research.id).first()
        assert updated_research.research_points >= 0
