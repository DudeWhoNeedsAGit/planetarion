import pytest
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from backend.services.tick import (
    run_tick, get_next_tick_number, process_resource_generation,
    calculate_production_rate, process_fleet_movements, log_tick,
    get_tick_statistics
)
from backend.models import TickLog

class TestTickService:
    """Test tick service functions"""

    def test_get_next_tick_number_no_previous(self, db_session):
        """Test getting next tick number when no previous ticks exist"""
        with patch('backend.services.tick.TickLog') as mock_ticklog:
            mock_ticklog.query.order_by.return_value.first.return_value = None
            result = get_next_tick_number()
            assert result == 1

    def test_get_next_tick_number_with_previous(self, db_session):
        """Test getting next tick number with existing ticks"""
        mock_last_tick = MagicMock()
        mock_last_tick.tick_number = 42

        with patch('backend.services.tick.TickLog') as mock_ticklog:
            mock_ticklog.query.order_by.return_value.first.return_value = mock_last_tick
            result = get_next_tick_number()
            assert result == 43

    def test_calculate_production_rate_metal(self):
        """Test metal production rate calculation"""
        rate = calculate_production_rate(5, 'metal')
        expected = 5 * 30 * (1.1 ** 5)
        assert rate == expected

    def test_calculate_production_rate_crystal(self):
        """Test crystal production rate calculation"""
        rate = calculate_production_rate(3, 'crystal')
        expected = 3 * 20 * (1.1 ** 3)
        assert rate == expected

    def test_calculate_production_rate_deuterium(self):
        """Test deuterium production rate calculation"""
        rate = calculate_production_rate(2, 'deuterium')
        expected = 2 * 10 * (1.1 ** 2)
        assert rate == expected

    def test_calculate_production_rate_invalid(self):
        """Test production rate with invalid resource type"""
        rate = calculate_production_rate(1, 'invalid')
        assert rate == 0

    def test_process_resource_generation(self, db_session, sample_planet):
        """Test resource generation processing"""
        # Set up planet with mines
        sample_planet.metal_mine = 5
        sample_planet.crystal_mine = 3
        sample_planet.deuterium_synthesizer = 2
        sample_planet.solar_plant = 10
        sample_planet.fusion_reactor = 0

        db_session.commit()

        changes = process_resource_generation()

        assert len(changes) > 0
        planet_change = next((c for c in changes if c['planet_id'] == sample_planet.id), None)
        assert planet_change is not None
        assert planet_change['metal_change'] > 0
        assert planet_change['crystal_change'] > 0
        assert planet_change['deuterium_change'] > 0

    def test_process_resource_generation_energy_shortage(self, db_session, sample_planet):
        """Test resource generation with energy shortage"""
        # Set up planet with high consumption, low production
        sample_planet.metal_mine = 20
        sample_planet.crystal_mine = 20
        sample_planet.deuterium_synthesizer = 20
        sample_planet.solar_plant = 1  # Very low energy production
        sample_planet.fusion_reactor = 0

        db_session.commit()

        changes = process_resource_generation()

        planet_change = next((c for c in changes if c['planet_id'] == sample_planet.id), None)
        assert planet_change is not None
        # Production should be reduced due to energy shortage
        assert planet_change['metal_change'] < 20 * 30 / 12  # Less than full production

    def test_process_fleet_movements_arrival(self, db_session, sample_fleet):
        """Test fleet arrival processing"""
        # Set fleet to traveling with past arrival time
        sample_fleet.status = 'traveling'
        sample_fleet.arrival_time = datetime.utcnow() - timedelta(hours=1)
        db_session.commit()

        current_time = datetime.utcnow()
        updates = process_fleet_movements(current_time)

        assert len(updates) > 0
        fleet_update = next((u for u in updates if u['fleet_id'] == sample_fleet.id), None)
        assert fleet_update is not None
        assert fleet_update['event_type'] == 'arrival'

        # Refresh fleet from DB
        db_session.refresh(sample_fleet)
        assert sample_fleet.status == 'stationed'

    def test_process_fleet_movements_return(self, db_session, sample_fleet):
        """Test fleet return processing"""
        # Set fleet to returning with past arrival time
        sample_fleet.status = 'returning'
        sample_fleet.arrival_time = datetime.utcnow() - timedelta(hours=1)
        db_session.commit()

        current_time = datetime.utcnow()
        updates = process_fleet_movements(current_time)

        assert len(updates) > 0
        fleet_update = next((u for u in updates if u['fleet_id'] == sample_fleet.id), None)
        assert fleet_update is not None
        assert fleet_update['event_type'] == 'return'

        # Refresh fleet from DB
        db_session.refresh(sample_fleet)
        assert sample_fleet.status == 'stationed'

    def test_process_fleet_movements_no_arrivals(self, db_session, sample_fleet):
        """Test fleet movement processing when no fleets have arrived"""
        # Set fleet to traveling with future arrival time
        sample_fleet.status = 'traveling'
        sample_fleet.arrival_time = datetime.utcnow() + timedelta(hours=1)
        db_session.commit()

        current_time = datetime.utcnow()
        updates = process_fleet_movements(current_time)

        assert len(updates) == 0

    def test_log_tick(self, db_session, sample_planet):
        """Test tick logging"""
        tick_number = 100
        timestamp = datetime.utcnow()
        resource_changes = [{
            'planet_id': sample_planet.id,
            'metal_change': 1000,
            'crystal_change': 500,
            'deuterium_change': 200
        }]
        fleet_updates = [{
            'fleet_id': 1,
            'event_type': 'arrival',
            'description': 'Fleet arrived'
        }]

        log_tick(tick_number, timestamp, resource_changes, fleet_updates)

        # Check resource log was created
        resource_log = db_session.query(TickLog).filter_by(
            tick_number=tick_number,
            planet_id=sample_planet.id
        ).first()
        assert resource_log is not None
        assert resource_log.metal_change == 1000

        # Check fleet log was created
        fleet_log = db_session.query(TickLog).filter_by(
            tick_number=tick_number,
            fleet_id=1
        ).first()
        assert fleet_log is not None
        assert fleet_log.event_type == 'arrival'

    def test_get_tick_statistics_no_ticks(self, db_session):
        """Test tick statistics when no ticks exist"""
        stats = get_tick_statistics()
        assert stats['total_ticks'] == 0
        assert stats['last_tick'] is None
        assert len(stats['recent_activity']) == 0

    def test_get_tick_statistics_with_ticks(self, db_session, sample_planet):
        """Test tick statistics with existing ticks"""
        # Create some tick logs
        for i in range(5):
            tick_log = TickLog(
                tick_number=i+1,
                timestamp=datetime.utcnow() - timedelta(minutes=i*5),
                planet_id=sample_planet.id,
                metal_change=100*(i+1),
                event_type='resource_production'
            )
            db_session.add(tick_log)
        db_session.commit()

        stats = get_tick_statistics()
        assert stats['total_ticks'] == 5
        assert stats['last_tick'] is not None
        assert len(stats['recent_activity']) == 5

    @patch('backend.services.tick.current_app')
    def test_run_tick(self, mock_app, db_session, sample_planet):
        """Test full tick execution"""
        mock_app.app_context.return_value.__enter__ = MagicMock()
        mock_app.app_context.return_value.__exit__ = MagicMock()
        mock_app.logger = MagicMock()

        with patch('backend.services.tick.get_next_tick_number', return_value=1), \
             patch('backend.services.tick.process_resource_generation', return_value=[]), \
             patch('backend.services.tick.process_fleet_movements', return_value=[]), \
             patch('backend.services.tick.log_tick'):

            run_tick()

            # Verify functions were called
            mock_app.logger.info.assert_called()

class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_process_resource_generation_no_planets(self, db_session):
        """Test resource generation with no planets"""
        changes = process_resource_generation()
        assert len(changes) == 0

    def test_process_fleet_movements_no_fleets(self, db_session):
        """Test fleet movement processing with no fleets"""
        current_time = datetime.utcnow()
        updates = process_fleet_movements(current_time)
        assert len(updates) == 0

    def test_calculate_production_rate_zero_level(self):
        """Test production rate calculation with zero level"""
        rate = calculate_production_rate(0, 'metal')
        assert rate == 0

    def test_process_resource_generation_zero_energy(self, db_session, sample_planet):
        """Test resource generation with zero energy production"""
        sample_planet.metal_mine = 5
        sample_planet.solar_plant = 0
        sample_planet.fusion_reactor = 0
        db_session.commit()

        changes = process_resource_generation()

        planet_change = next((c for c in changes if c['planet_id'] == sample_planet.id), None)
        assert planet_change is not None
        # With zero energy, production should be zero
        assert planet_change['metal_change'] == 0
