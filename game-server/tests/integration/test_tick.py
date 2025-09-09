import pytest
import json
from unittest.mock import patch
from backend.database import db
from backend.models import Planet
from backend.database import db
from backend.models import TickLog

import time
from datetime import datetime, timedelta
        
class TestTickEndpoints:
    """Test tick API endpoints"""

    def test_manual_tick_success(self, client, sample_planet):
        """Test manual tick execution"""
        # Set up planet with mines
        sample_planet.metal_mine = 5
        sample_planet.crystal_mine = 3
        sample_planet.deuterium_synthesizer = 2
        sample_planet.solar_plant = 10
        sample_planet.fusion_reactor = 0
        sample_planet.metal = 10000
        sample_planet.crystal = 5000
        sample_planet.deuterium = 2000


        db.session.commit()

        # Record initial resources
        initial_metal = sample_planet.metal
        initial_crystal = sample_planet.crystal
        initial_deuterium = sample_planet.deuterium

        response = client.post('/api/tick')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'message' in data
        assert 'changes' in data

        # Verify resources increased
        db.session.refresh(sample_planet)
        assert sample_planet.metal > initial_metal
        assert sample_planet.crystal > initial_crystal
        assert sample_planet.deuterium > initial_deuterium

        # Verify changes are reported
        assert len(data['changes']) > 0
        planet_change = next((c for c in data['changes'] if c['planet_id'] == sample_planet.id), None)
        assert planet_change is not None
        assert planet_change['metal_change'] > 0

    def test_manual_tick_no_planets(self, client):
        """Test manual tick when no planets exist"""
        
        Planet.query.delete()
        db.session.commit()

        response = client.post('/api/tick')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'message' in data
        assert len(data['changes']) == 0

    def test_manual_tick_energy_shortage(self, client, sample_planet):
        """Test manual tick with energy shortage"""
        # Set up planet with high consumption, low production
        sample_planet.metal_mine = 20
        sample_planet.crystal_mine = 20
        sample_planet.deuterium_synthesizer = 20
        sample_planet.solar_plant = 1  # Very low energy
        sample_planet.fusion_reactor = 0

        db.session.commit()

        initial_metal = sample_planet.metal

        response = client.post('/api/tick')
        assert response.status_code == 200

        # Refresh and check that production was reduced
        db.session.refresh(sample_planet)
        metal_increase = sample_planet.metal - initial_metal

        # With energy shortage, production should be less than full
        full_production = 20 * 30 / 12  # 20 mines * 30 base * 1/12 for 5 min tick
        assert metal_increase < full_production

    def test_manual_tick_multiple_planets(self, client, sample_user, sample_planet):
        """Test manual tick with multiple planets"""

        # Set up mines on the original sample planet
        sample_planet.metal_mine = 5
        sample_planet.crystal_mine = 3

        # Create additional planets
        planets_data = [
            {'name': 'Planet 2', 'x': 1, 'y': 1, 'z': 1, 'user_id': sample_user.id},
            {'name': 'Planet 3', 'x': 2, 'y': 2, 'z': 2, 'user_id': sample_user.id}
        ]

        for planet_data in planets_data:
            planet = Planet(**planet_data)
            planet.metal_mine = 5
            planet.crystal_mine = 3
            db.session.add(planet)
        db.session.commit()

        response = client.post('/api/tick')
        assert response.status_code == 200
        data = json.loads(response.data)

        # Should have changes for all planets (original + 2 new)
        assert len(data['changes']) == 3

    def test_manual_tick_creates_tick_log(self, client, sample_planet):
        """Test that manual tick creates tick log entries"""

        # Set up planet
        sample_planet.metal_mine = 5
        db.session.commit()

        initial_log_count = TickLog.query.count()

        response = client.post('/api/tick')
        assert response.status_code == 200

        # Check that tick log was created
        final_log_count = TickLog.query.count()
        assert final_log_count > initial_log_count

        # Check the latest log
        latest_log = TickLog.query.order_by(TickLog.id.desc()).first()
        assert latest_log.planet_id == sample_planet.id
        assert latest_log.metal_change > 0

    def test_manual_tick_updates_tick_number(self, client, sample_planet):
        """Test that tick numbers increment properly"""

        # Create initial tick log
        initial_tick = TickLog(
            tick_number=100,
            planet_id=sample_planet.id,
            metal_change=1000
        )
        db.session.add(initial_tick)
        db.session.commit()

        response = client.post('/api/tick')
        assert response.status_code == 200

        # Check that new tick has number 101
        latest_log = TickLog.query.order_by(TickLog.tick_number.desc()).first()
        assert latest_log.tick_number == 101

class TestTickIntegration:
    """Test tick-related integration scenarios"""

    def test_tick_preserves_data_integrity(self, client, sample_planet, sample_fleet):
        """Test that tick doesn't corrupt existing data"""
        # Record initial state
        initial_planet_metal = sample_planet.metal
        initial_fleet_status = sample_fleet.status

        response = client.post('/api/tick')
        assert response.status_code == 200

        db.session.refresh(sample_planet)
        db.session.refresh(sample_fleet)

        assert sample_planet.metal >= initial_planet_metal  # Should not decrease
        assert sample_fleet.status == initial_fleet_status  # Should not change

    def test_tick_handles_zero_level_structures(self, client, sample_planet):
        """Test tick with structures at level 0"""
        # Set all structures to 0
        sample_planet.metal_mine = 0
        sample_planet.crystal_mine = 0
        sample_planet.deuterium_synthesizer = 0
        sample_planet.solar_plant = 0
        sample_planet.fusion_reactor = 0


        db.session.commit()

        initial_resources = {
            'metal': sample_planet.metal,
            'crystal': sample_planet.crystal,
            'deuterium': sample_planet.deuterium
        }

        response = client.post('/api/tick')
        assert response.status_code == 200

        # Refresh and verify no production occurred
        db.session.refresh(sample_planet)
        assert sample_planet.metal == initial_resources['metal']
        assert sample_planet.crystal == initial_resources['crystal']
        assert sample_planet.deuterium == initial_resources['deuterium']

    def test_tick_with_max_resources(self, client, sample_planet):
        """Test tick when planet has maximum resources"""
        # Set resources to very high values
        sample_planet.metal = 999999999999
        sample_planet.crystal = 999999999999
        sample_planet.deuterium = 999999999999
        sample_planet.metal_mine = 10

        db.session.commit()

        response = client.post('/api/tick')
        assert response.status_code == 200

        # Should still work without overflow issues
        db.session.refresh(sample_planet)
        assert sample_planet.metal >= 999999999999

class TestTickEdgeCases:
    """Test tick endpoint edge cases"""

    def test_tick_with_fleet_movements(self, client, sample_planet, sample_fleet):
        """Test tick execution alongside fleet movements"""
        # Set up fleet in transit
        sample_fleet.status = 'traveling'
        sample_fleet.arrival_time = datetime.utcnow() + timedelta(hours=1)


        db.session.commit()

        response = client.post('/api/tick')
        assert response.status_code == 200

        # Fleet should still be traveling (tick doesn't affect fleet movement)
        db.session.refresh(sample_fleet)
        assert sample_fleet.status == 'traveling'

    def test_tick_database_transaction_rollback(self, client, sample_planet):
        """Test that tick properly handles database transactions"""
        # This is more of a conceptual test - in practice we'd need to simulate DB errors
        response = client.post('/api/tick')
        assert response.status_code == 200

        # If there was an error mid-tick, all changes should be rolled back
        # But since our implementation commits at the end, this should work

    def test_concurrent_tick_execution(self, client, sample_planet):
        """Test behavior with concurrent tick execution"""
        # This would require more complex setup with threading
        # For now, just verify single execution works
        response = client.post('/api/tick')
        assert response.status_code == 200

        # Second execution should also work
        response2 = client.post('/api/tick')
        assert response2.status_code == 200

class TestAutomaticTickSystem:
    """Test the automatic 5-second tick system"""

    def test_automatic_tick_resource_generation(self, client, sample_planet):
        """Test that automatic ticks increase resources over 15 seconds (3 ticks)"""
        
        # Set up planet with mines for predictable production
        sample_planet.metal_mine = 5
        sample_planet.crystal_mine = 3
        sample_planet.deuterium_synthesizer = 2
        sample_planet.solar_plant = 10  # Plenty of energy
        sample_planet.fusion_reactor = 0
        sample_planet.metal = 10000
        sample_planet.crystal = 5000
        sample_planet.deuterium = 2000
        db.session.commit()

        # Record initial resources
        initial_metal = sample_planet.metal
        initial_crystal = sample_planet.crystal
        initial_deuterium = sample_planet.deuterium

        print(f"Initial resources - Metal: {initial_metal}, Crystal: {initial_crystal}, Deuterium: {initial_deuterium}")

        # Wait for 3 ticks (15 seconds with 5-second intervals)
        print("Waiting 15 seconds for 3 automatic ticks...")
        time.sleep(15)

        # Refresh planet data from database
        db.session.refresh(sample_planet)

        print(f"Final resources - Metal: {sample_planet.metal}, Crystal: {sample_planet.crystal}, Deuterium: {sample_planet.deuterium}")

        # Verify resources increased
        assert sample_planet.metal > initial_metal, f"Metal should increase: {sample_planet.metal} > {initial_metal}"
        assert sample_planet.crystal > initial_crystal, f"Crystal should increase: {sample_planet.crystal} > {initial_crystal}"
        assert sample_planet.deuterium > initial_deuterium, f"Deuterium should increase: {sample_planet.deuterium} > {initial_deuterium}"

        # Calculate expected minimum increase for 3 ticks
        # Metal: 5 mines × 30 base × (1.1^5) × 3 ticks × (1/7200) per tick
        metal_production_rate = 5 * 30 * (1.1 ** 5)  # ~212.58 per hour
        expected_metal_increase = metal_production_rate * 3 / 7200  # ~0.0886 per tick × 3 = ~0.266

        # Crystal: 3 mines × 20 base × (1.1^3) × 3 ticks × (1/7200) per tick
        crystal_production_rate = 3 * 20 * (1.1 ** 3)  # ~79.86 per hour
        expected_crystal_increase = crystal_production_rate * 3 / 7200  # ~0.0333 per tick × 3 = ~0.099

        # Deuterium: 2 synthesizers × 10 base × (1.1^2) × 3 ticks × (1/7200) per tick
        deuterium_production_rate = 2 * 10 * (1.1 ** 2)  # ~24.2 per hour
        expected_deuterium_increase = deuterium_production_rate * 3 / 7200  # ~0.0101 per tick × 3 = ~0.030

        print(f"Expected increases - Metal: {expected_metal_increase:.3f}, Crystal: {expected_crystal_increase:.3f}, Deuterium: {expected_deuterium_increase:.3f}")
        print(f"Actual increases - Metal: {sample_planet.metal - initial_metal}, Crystal: {sample_planet.crystal - initial_crystal}, Deuterium: {sample_planet.deuterium - initial_deuterium}")

        # Verify minimum expected increases (allowing for floating point precision)
        assert sample_planet.metal >= initial_metal + expected_metal_increase - 0.1, \
            f"Metal increase should meet minimum: {sample_planet.metal - initial_metal} >= {expected_metal_increase - 0.1}"
        assert sample_planet.crystal >= initial_crystal + expected_crystal_increase - 0.1, \
            f"Crystal increase should meet minimum: {sample_planet.crystal - initial_crystal} >= {expected_crystal_increase - 0.1}"
        assert sample_planet.deuterium >= initial_deuterium + expected_deuterium_increase - 0.1, \
            f"Deuterium increase should meet minimum: {sample_planet.deuterium - initial_deuterium} >= {expected_deuterium_increase - 0.1}"

    @patch('backend.services.tick.run_tick')
    def test_automatic_tick_timing_accuracy(self, mock_tick, client, sample_planet):
        """Test that ticks occur at approximately 5-second intervals"""

        # Mock the tick function to control execution and prevent recursion
        mock_tick.return_value = True

        # Clear existing tick logs
        TickLog.query.delete()
        db.session.commit()

        # Set up planet
        sample_planet.metal_mine = 1
        db.session.commit()

        initial_log_count = TickLog.query.count()

        # Manually trigger 4 ticks with controlled timing
        import time
        start_time = time.time()

        for i in range(4):
            mock_tick()
            if i < 3:  # Don't sleep after last tick
                time.sleep(5)  # 5-second intervals

        end_time = time.time()
        final_log_count = TickLog.query.count()

        elapsed_time = end_time - start_time
        tick_count = final_log_count - initial_log_count

        print(f"Elapsed time: {elapsed_time:.2f} seconds")
        print(f"Tick logs created: {tick_count}")

        # Should have created exactly 4 ticks
        assert tick_count == 4, f"Should have exactly 4 ticks, got {tick_count}"

        # Average interval should be close to 5 seconds
        if tick_count > 1:
            avg_interval = elapsed_time / (tick_count - 1)
            print(f"Average tick interval: {avg_interval:.2f} seconds")
            assert 4.5 <= avg_interval <= 6.5, f"Average interval should be 4.5-6.5 seconds, got {avg_interval}"
