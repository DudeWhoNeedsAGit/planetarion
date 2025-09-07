"""
Planet Traits Service

This module handles planet trait generation, application, and management.
Planet traits provide bonuses and penalties to resource production and colonization.
"""

import random
from backend.models import PlanetTrait, db

class PlanetTraitService:
    """Service for managing planet traits and their effects"""

    # Available planet traits with their effects
    TRAIT_TYPES = {
        'resource_rich': {
            'name': 'Resource Rich',
            'description': 'High natural resource deposits',
            'effects': {'metal': 0.25, 'crystal': 0.15},
            'rarity': 'common'
        },
        'metal_world': {
            'name': 'Metal World',
            'description': 'Exceptionally rich in metal deposits',
            'effects': {'metal': 0.40, 'crystal': -0.10},
            'rarity': 'uncommon'
        },
        'crystal_caves': {
            'name': 'Crystal Caves',
            'description': 'Underground crystal formations',
            'effects': {'crystal': 0.35, 'metal': -0.15},
            'rarity': 'uncommon'
        },
        'deuterium_ocean': {
            'name': 'Deuterium Ocean',
            'description': 'Planet with liquid deuterium oceans',
            'effects': {'deuterium': 0.30, 'energy': -0.20},
            'rarity': 'rare'
        },
        'high_energy': {
            'name': 'High Energy',
            'description': 'Strong natural energy fields',
            'effects': {'energy': 0.50},
            'rarity': 'rare'
        },
        'defensive': {
            'name': 'Defensive Position',
            'description': 'Natural defensive advantages',
            'effects': {'defense': 0.25},
            'rarity': 'uncommon'
        },
        'aggressive': {
            'name': 'Aggressive Environment',
            'description': 'Harsh environment increases combat effectiveness',
            'effects': {'attack': 0.20},
            'rarity': 'uncommon'
        },
        'barren': {
            'name': 'Barren World',
            'description': 'Poor resource availability',
            'effects': {'all_resources': -0.30},
            'rarity': 'common'
        },
        'temperate': {
            'name': 'Temperate Climate',
            'description': 'Balanced climate for efficient production',
            'effects': {'all_resources': 0.10},
            'rarity': 'common'
        },
        'hostile': {
            'name': 'Hostile Environment',
            'description': 'Difficult colonization conditions',
            'effects': {'colonization_difficulty': 2},
            'rarity': 'uncommon'
        },
        'volcanic': {
            'name': 'Volcanic Activity',
            'description': 'Geothermal energy but unstable conditions',
            'effects': {'energy': 0.30, 'colonization_difficulty': 1},
            'rarity': 'rare'
        },
        'frozen': {
            'name': 'Frozen World',
            'description': 'Ice-covered planet with deuterium reserves',
            'effects': {'deuterium': 0.25, 'energy': -0.15},
            'rarity': 'uncommon'
        }
    }

    @staticmethod
    def generate_planet_traits(planet):
        """
        Generate 1-3 random traits for a planet

        Args:
            planet: Planet model instance

        Returns:
            List of PlanetTrait instances
        """
        # Determine number of traits based on rarity weights
        num_traits = PlanetTraitService._determine_trait_count()

        # Select traits based on rarity
        selected_trait_keys = PlanetTraitService._select_traits(num_traits)

        traits = []
        for trait_key in selected_trait_keys:
            trait_data = PlanetTraitService.TRAIT_TYPES[trait_key]

            # Create trait record
            trait = PlanetTrait(
                planet_id=planet.id,
                trait_type=list(trait_data['effects'].keys())[0],
                trait_name=trait_data['name'],
                bonus_value=list(trait_data['effects'].values())[0],
                description=trait_data['description']
            )
            traits.append(trait)

            # Apply trait effects to planet
            PlanetTraitService.apply_trait_effects(planet, trait_data['effects'])

        return traits

    @staticmethod
    def _determine_trait_count():
        """Determine how many traits a planet should have"""
        # 40% chance for 1 trait, 45% for 2 traits, 15% for 3 traits
        rand = random.random()
        if rand < 0.40:
            return 1
        elif rand < 0.85:
            return 2
        else:
            return 3

    @staticmethod
    def _select_traits(num_traits):
        """Select traits based on rarity weights"""
        # Rarity weights
        rarity_weights = {
            'common': 0.5,
            'uncommon': 0.3,
            'rare': 0.2
        }

        # Group traits by rarity
        traits_by_rarity = {}
        for trait_key, trait_data in PlanetTraitService.TRAIT_TYPES.items():
            rarity = trait_data['rarity']
            if rarity not in traits_by_rarity:
                traits_by_rarity[rarity] = []
            traits_by_rarity[rarity].append(trait_key)

        selected_traits = []
        available_traits = list(PlanetTraitService.TRAIT_TYPES.keys())

        for _ in range(num_traits):
            if not available_traits:
                break

            # Select based on rarity weights
            rand = random.random()
            cumulative_weight = 0

            for rarity, weight in rarity_weights.items():
                cumulative_weight += weight
                if rand <= cumulative_weight:
                    rarity_traits = [t for t in available_traits
                                   if PlanetTraitService.TRAIT_TYPES[t]['rarity'] == rarity]
                    if rarity_traits:
                        selected_trait = random.choice(rarity_traits)
                        selected_traits.append(selected_trait)
                        available_traits.remove(selected_trait)
                    break

        return selected_traits

    @staticmethod
    def apply_trait_effects(planet, effects):
        """
        Apply trait effects to planet bonuses

        Args:
            planet: Planet model instance
            effects: Dict of effect types and values
        """
        for effect_type, value in effects.items():
            if effect_type == 'metal':
                planet.base_metal_bonus = (planet.base_metal_bonus or 0) + value
            elif effect_type == 'crystal':
                planet.base_crystal_bonus = (planet.base_crystal_bonus or 0) + value
            elif effect_type == 'deuterium':
                planet.base_deuterium_bonus = (planet.base_deuterium_bonus or 0) + value
            elif effect_type == 'energy':
                planet.base_energy_bonus = (planet.base_energy_bonus or 0) + value
            elif effect_type == 'all_resources':
                planet.base_metal_bonus = (planet.base_metal_bonus or 0) + value
                planet.base_crystal_bonus = (planet.base_crystal_bonus or 0) + value
                planet.base_deuterium_bonus = (planet.base_deuterium_bonus or 0) + value
            elif effect_type == 'colonization_difficulty':
                planet.colonization_difficulty = (planet.colonization_difficulty or 1) + value
            elif effect_type == 'defense':
                planet.base_defense_bonus = (planet.base_defense_bonus or 0) + value
            elif effect_type == 'attack':
                planet.base_attack_bonus = (planet.base_attack_bonus or 0) + value

    @staticmethod
    def get_planet_traits(planet_id):
        """
        Get all traits for a planet

        Args:
            planet_id: Planet ID

        Returns:
            List of trait dictionaries
        """
        traits = PlanetTrait.query.filter_by(planet_id=planet_id).all()

        return [{
            'id': trait.id,
            'name': trait.trait_name,
            'type': trait.trait_type,
            'bonus': trait.bonus_value,
            'description': trait.description
        } for trait in traits]

    @staticmethod
    def calculate_trait_bonuses(planet):
        """
        Calculate total bonuses from all planet traits

        Args:
            planet: Planet model instance

        Returns:
            Dict of total bonuses
        """
        bonuses = {
            'metal': planet.base_metal_bonus or 0,
            'crystal': planet.base_crystal_bonus or 0,
            'deuterium': planet.base_deuterium_bonus or 0,
            'energy': planet.base_energy_bonus or 0,
            'defense': getattr(planet, 'base_defense_bonus', 0),
            'attack': getattr(planet, 'base_attack_bonus', 0),
            'colonization_difficulty': planet.colonization_difficulty or 1
        }

        return bonuses

    @staticmethod
    def get_trait_display_info(trait_name):
        """
        Get display information for a trait

        Args:
            trait_name: Name of the trait

        Returns:
            Dict with display information or None if not found
        """
        for trait_key, trait_data in PlanetTraitService.TRAIT_TYPES.items():
            if trait_data['name'] == trait_name:
                return {
                    'name': trait_data['name'],
                    'description': trait_data['description'],
                    'effects': trait_data['effects'],
                    'rarity': trait_data['rarity']
                }
        return None
