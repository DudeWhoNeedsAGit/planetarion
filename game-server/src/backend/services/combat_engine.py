"""
Combat Engine Service

This service handles all combat calculations including:
- Fleet vs Fleet battles
- Ship combat statistics
- Rapid fire mechanics
- Shield absorption
- Hull damage calculation
- Debris field generation
- Battle report generation
"""

import json
import math
from datetime import datetime
from backend.database import db
from backend.models import Fleet, Planet, CombatReport, DebrisField, User, TickLog


class CombatEngine:
    """Core combat calculation engine"""

    # Ship combat statistics
    SHIP_STATS = {
        'small_cargo': {
            'hull': 4000, 'shield': 10, 'weapon': 5, 'speed': 5000,
            'cargo': 5000, 'fuel': 10
        },
        'large_cargo': {
            'hull': 12000, 'shield': 25, 'weapon': 5, 'speed': 7500,
            'cargo': 25000, 'fuel': 50
        },
        'light_fighter': {
            'hull': 4000, 'shield': 10, 'weapon': 50, 'speed': 12500,
            'cargo': 50, 'fuel': 20
        },
        'heavy_fighter': {
            'hull': 10000, 'shield': 25, 'weapon': 150, 'speed': 10000,
            'cargo': 100, 'fuel': 75
        },
        'cruiser': {
            'hull': 27000, 'shield': 50, 'weapon': 400, 'speed': 15000,
            'cargo': 800, 'fuel': 300
        },
        'battleship': {
            'hull': 60000, 'shield': 200, 'weapon': 1000, 'speed': 10000,
            'cargo': 1500, 'fuel': 500
        },
        'colony_ship': {
            'hull': 30000, 'shield': 100, 'weapon': 50, 'speed': 2500,
            'cargo': 7500, 'fuel': 1000
        }
    }

    # Rapid fire bonuses (attacker:defender ratio)
    RAPID_FIRE = {
        'light_fighter': {'heavy_fighter': 2, 'cruiser': 6, 'battleship': 3},
        'heavy_fighter': {'small_cargo': 3, 'large_cargo': 4, 'cruiser': 4, 'battleship': 7},
        'cruiser': {'light_fighter': 6, 'heavy_fighter': 4, 'battleship': 7},
        'battleship': {'small_cargo': 3, 'large_cargo': 4}
    }

    @staticmethod
    def calculate_battle(attacker_fleet, defender_fleet, defender_planet=None):
        """Main battle calculation engine"""
        print("DEBUG: Starting battle calculation")
        print(f"DEBUG: Attacker fleet: {attacker_fleet.id}, Defender fleet: {defender_fleet.id}")

        rounds = []
        attacker_ships = CombatEngine._fleet_to_combat_ships(attacker_fleet)
        defender_ships = CombatEngine._fleet_to_combat_ships(defender_fleet)

        # Add planetary defenses if defending planet
        if defender_planet:
            defender_ships.update(CombatEngine._planet_defenses_to_ships(defender_planet))

        round_num = 1
        while CombatEngine._has_ships(attacker_ships) and CombatEngine._has_ships(defender_ships) and round_num <= 6:
            print(f"DEBUG: Calculating round {round_num}")
            round_result = CombatEngine._calculate_round(attacker_ships, defender_ships)
            rounds.append(round_result)
            round_num += 1

        # Determine winner and calculate losses
        winner = 'attacker' if CombatEngine._has_ships(attacker_ships) else 'defender'
        print(f"DEBUG: Battle winner: {winner}")

        # Calculate final losses
        attacker_losses = CombatEngine._calculate_losses(attacker_fleet, attacker_ships)
        defender_losses = CombatEngine._calculate_losses(defender_fleet, defender_ships)
        debris = CombatEngine._calculate_debris(attacker_fleet, defender_fleet)

        result = {
            'winner': winner,
            'rounds': rounds,
            'attacker_losses': attacker_losses,
            'defender_losses': defender_losses,
            'debris': debris
        }

        print(f"DEBUG: Battle calculation complete. Winner: {winner}")
        return result

    @staticmethod
    def _fleet_to_combat_ships(fleet):
        """Convert fleet to combat-ready ship dictionary"""
        ships = {}
        for ship_type in ['small_cargo', 'large_cargo', 'light_fighter', 'heavy_fighter', 'cruiser', 'battleship', 'colony_ship']:
            count = getattr(fleet, ship_type, 0)
            if count > 0:
                ships[ship_type] = {
                    'count': count,
                    'hull': CombatEngine.SHIP_STATS[ship_type]['hull'],
                    'shield': CombatEngine.SHIP_STATS[ship_type]['shield'],
                    'weapon': CombatEngine.SHIP_STATS[ship_type]['weapon']
                }
        return ships

    @staticmethod
    def _planet_defenses_to_ships(planet):
        """Convert planetary defenses to ship-like combat units"""
        # For now, planetary defenses are represented as ships
        # This could be expanded to include actual defense structures
        defenses = {}
        for ship_type in ['small_cargo', 'large_cargo', 'light_fighter', 'heavy_fighter', 'cruiser', 'battleship', 'colony_ship']:
            count = getattr(planet, ship_type, 0)
            if count > 0:
                defenses[ship_type] = {
                    'count': count,
                    'hull': CombatEngine.SHIP_STATS[ship_type]['hull'],
                    'shield': CombatEngine.SHIP_STATS[ship_type]['shield'],
                    'weapon': CombatEngine.SHIP_STATS[ship_type]['weapon']
                }
        return defenses

    @staticmethod
    def _calculate_round(attacker_ships, defender_ships):
        """Calculate a single round of combat"""
        # Calculate firepower with rapid fire
        attacker_fire = CombatEngine._calculate_firepower(attacker_ships, defender_ships, 'attacker')
        defender_fire = CombatEngine._calculate_firepower(defender_ships, attacker_ships, 'defender')

        # Apply shield absorption
        attacker_damage = CombatEngine._apply_shields(attacker_fire, defender_ships)
        defender_damage = CombatEngine._apply_shields(defender_fire, attacker_ships)

        # Apply hull damage
        CombatEngine._apply_hull_damage(attacker_damage, defender_ships)
        CombatEngine._apply_hull_damage(defender_damage, attacker_ships)

        return {
            'attacker_fire': attacker_fire,
            'defender_fire': defender_fire,
            'attacker_damage': attacker_damage,
            'defender_damage': defender_damage
        }

    @staticmethod
    def _calculate_firepower(attacker_ships, defender_ships, side):
        """Calculate total firepower including rapid fire bonuses"""
        total_fire = 0

        for ship_type, ship_data in attacker_ships.items():
            if ship_data['count'] <= 0:
                continue

            base_fire = ship_data['count'] * ship_data['weapon']
            rapid_fire_bonus = 1.0

            # Apply rapid fire bonuses
            if ship_type in CombatEngine.RAPID_FIRE:
                for target_type, ratio in CombatEngine.RAPID_FIRE[ship_type].items():
                    if target_type in defender_ships and defender_ships[target_type]['count'] > 0:
                        # Calculate how many extra shots this ship gets
                        target_count = defender_ships[target_type]['count']
                        extra_shots = min(target_count * (ratio - 1), ship_data['count'])
                        rapid_fire_bonus += extra_shots / ship_data['count']

            total_fire += base_fire * rapid_fire_bonus

        return int(total_fire)

    @staticmethod
    def _apply_shields(damage, target_ships):
        """Apply shield absorption to damage"""
        remaining_damage = damage

        for ship_type, ship_data in target_ships.items():
            if ship_data['count'] <= 0 or remaining_damage <= 0:
                continue

            total_shield = ship_data['count'] * ship_data['shield']
            absorbed = min(remaining_damage, total_shield)
            remaining_damage -= absorbed

            if remaining_damage <= 0:
                break

        return max(0, damage - (damage - remaining_damage))

    @staticmethod
    def _apply_hull_damage(damage, target_ships):
        """Apply damage to ship hulls"""
        remaining_damage = damage

        for ship_type, ship_data in target_ships.items():
            if ship_data['count'] <= 0 or remaining_damage <= 0:
                continue

            total_hull = ship_data['count'] * ship_data['hull']
            damage_taken = min(remaining_damage, total_hull)

            # Calculate ships destroyed
            ships_destroyed = damage_taken // ship_data['hull']
            ship_data['count'] = max(0, ship_data['count'] - ships_destroyed)

            remaining_damage -= damage_taken

            if remaining_damage <= 0:
                break

    @staticmethod
    def _has_ships(ships):
        """Check if fleet still has ships"""
        return any(ship_data['count'] > 0 for ship_data in ships.values())

    @staticmethod
    def _calculate_losses(original_fleet, remaining_ships):
        """Calculate ship losses from original fleet"""
        losses = {}

        for ship_type in ['small_cargo', 'large_cargo', 'light_fighter', 'heavy_fighter', 'cruiser', 'battleship', 'colony_ship']:
            original_count = getattr(original_fleet, ship_type, 0)
            remaining_count = remaining_ships.get(ship_type, {}).get('count', 0)
            losses[ship_type] = max(0, original_count - remaining_count)

        return losses

    @staticmethod
    def _calculate_debris(attacker_fleet, defender_fleet):
        """Calculate debris from destroyed ships"""
        total_metal = 0
        total_crystal = 0

        # 30% of ship costs become debris
        # Simplified cost calculation (would be more complex in real implementation)
        ship_costs = {
            'small_cargo': {'metal': 2000, 'crystal': 2000},
            'large_cargo': {'metal': 6000, 'crystal': 6000},
            'light_fighter': {'metal': 3000, 'crystal': 1000},
            'heavy_fighter': {'metal': 6000, 'crystal': 4000},
            'cruiser': {'metal': 20000, 'crystal': 7000},
            'battleship': {'metal': 45000, 'crystal': 15000},
            'colony_ship': {'metal': 10000, 'crystal': 20000}
        }

        for ship_type, count in CombatEngine._calculate_losses(attacker_fleet, CombatEngine._fleet_to_combat_ships(attacker_fleet)).items():
            if count > 0 and ship_type in ship_costs:
                cost = ship_costs[ship_type]
                total_metal += int(count * cost['metal'] * 0.3)
                total_crystal += int(count * cost['crystal'] * 0.3)

        for ship_type, count in CombatEngine._calculate_losses(defender_fleet, CombatEngine._fleet_to_combat_ships(defender_fleet)).items():
            if count > 0 and ship_type in ship_costs:
                cost = ship_costs[ship_type]
                total_metal += int(count * cost['metal'] * 0.3)
                total_crystal += int(count * cost['crystal'] * 0.3)

        return {'metal': total_metal, 'crystal': total_crystal}

    @staticmethod
    def process_combat_result(combat_result, attacker_fleet, defender_fleet, planet):
        """Process the results of a combat engagement"""
        print("DEBUG: Processing combat result")

        # Update fleet combat statistics
        if combat_result['winner'] == 'attacker':
            attacker_fleet.combat_victories += 1
            defender_fleet.combat_defeats += 1
        else:
            attacker_fleet.combat_defeats += 1
            defender_fleet.combat_victories += 1

        attacker_fleet.last_combat_time = datetime.utcnow()
        defender_fleet.last_combat_time = datetime.utcnow()

        # Apply ship losses
        for ship_type, losses in combat_result['attacker_losses'].items():
            if losses > 0:
                current_count = getattr(attacker_fleet, ship_type, 0)
                setattr(attacker_fleet, ship_type, max(0, current_count - losses))

        for ship_type, losses in combat_result['defender_losses'].items():
            if losses > 0:
                current_count = getattr(defender_fleet, ship_type, 0)
                setattr(defender_fleet, ship_type, max(0, current_count - losses))

        # Create debris field
        if combat_result['debris']['metal'] > 0 or combat_result['debris']['crystal'] > 0:
            debris_field = DebrisField(
                planet_id=planet.id,
                metal=combat_result['debris']['metal'],
                crystal=combat_result['debris']['crystal'],
                deuterium=0  # Could be expanded to include deuterium debris
            )
            db.session.add(debris_field)

        # Generate battle report
        winner_id = attacker_fleet.user_id if combat_result['winner'] == 'attacker' else defender_fleet.user_id

        battle_report = CombatReport(
            attacker_id=attacker_fleet.user_id,
            defender_id=defender_fleet.user_id,
            planet_id=planet.id,
            winner_id=winner_id,
            rounds=json.dumps(combat_result['rounds']),
            attacker_losses=json.dumps(combat_result['attacker_losses']),
            defender_losses=json.dumps(combat_result['defender_losses']),
            debris_metal=combat_result['debris']['metal'],
            debris_crystal=combat_result['debris']['crystal']
        )
        db.session.add(battle_report)

        # Create tick log entry
        tick_log = TickLog(
            planet_id=planet.id,
            event_type='combat',
            event_description=f'Combat between {attacker_fleet.user.username} and {defender_fleet.user.username}. Winner: {battle_report.winner.username}'
        )
        db.session.add(tick_log)

        db.session.commit()
        print("DEBUG: Combat result processing complete")

        return battle_report

    @staticmethod
    def calculate_planet_attack(fleet, planet):
        """Calculate attack on undefended planet (capture mechanics)"""
        # Simplified planet capture logic
        # In a full implementation, this would consider planetary defenses

        # For now, assume undefended planets are captured
        return {
            'winner': 'attacker',
            'rounds': [],
            'attacker_losses': {ship: 0 for ship in ['small_cargo', 'large_cargo', 'light_fighter', 'heavy_fighter', 'cruiser', 'battleship', 'colony_ship']},
            'defender_losses': {ship: 0 for ship in ['small_cargo', 'large_cargo', 'light_fighter', 'heavy_fighter', 'cruiser', 'battleship', 'colony_ship']},
            'debris': {'metal': 0, 'crystal': 0},
            'planet_captured': True
        }

    @staticmethod
    def process_planet_attack_result(combat_result, fleet, planet):
        """Process the results of a planet attack"""
        print("DEBUG: Processing planet attack result")

        # Update fleet combat statistics
        if combat_result.get('planet_captured', False):
            fleet.combat_victories += 1
            planet.user_id = fleet.user_id  # Transfer ownership

            # Create tick log entry
            tick_log = TickLog(
                planet_id=planet.id,
                event_type='planet_capture',
                event_description=f'Planet {planet.name} captured by {fleet.user.username}'
            )
            db.session.add(tick_log)

        fleet.last_combat_time = datetime.utcnow()
        db.session.commit()

        print("DEBUG: Planet attack result processing complete")
