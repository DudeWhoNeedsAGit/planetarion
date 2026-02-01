"""
Phase 5: Colonization Performance Testing Framework

This module implements comprehensive performance testing for colonization mechanics,
including load testing, concurrent operations, and performance benchmarking.
"""

import pytest
import time
import threading
import concurrent.futures
import statistics
from datetime import datetime, timedelta
import os

psutil = pytest.importorskip("psutil")

from tests.conftest import (
    create_test_user_with_hashed_password,
    create_test_colony_fleet_with_validation,
    create_test_planet_with_traits,
    setup_test_research_levels,
    login_as_test_user,
    create_colonization_fleet_api,
    send_colonization_mission_api,
    get_fleets_api,
    get_planets_api
)


class TestColonizationPerformance:
    """Performance testing for colonization mechanics"""

    def test_single_user_colonization_throughput(self, db_session):
        """Test colonization throughput for a single user performing multiple operations"""
        # Create user with high resources
        user, password = create_test_user_with_hashed_password(
            db_session, 'perf_single', 'perf@test.com', 'password'
        )

        # Create home planet with ample resources
        home_planet = create_test_planet_with_traits(
            db_session,
            user_id=user.id,
            metal=1000000, crystal=500000, deuterium=300000,
            colony_ship=50, light_fighter=5000, cruiser=1000
        )

        # Setup research
        research = setup_test_research_levels(
            db_session,
            user.id,
            colonization_tech=5
        )

        # Create multiple target planets
        target_planets = []
        for i in range(10):
            planet = create_test_planet_with_traits(
                db_session,
                x=i*100, y=i*100, z=i*100,
                planet_type='terrestrial',
                user_id=None
            )
            target_planets.append(planet)

        db_session.commit()

        # Measure performance of creating and sending multiple colonization fleets
        start_time = time.time()
        fleets_created = 0
        missions_sent = 0

        for i, target_planet in enumerate(target_planets):
            try:
                # Create fleet
                fleet = create_test_colony_fleet_with_validation(
                    db_session,
                    user.id,
                    home_planet.id,
                    target_planet.id,
                    colony_ship=1,
                    light_fighter=10 + i,  # Vary fleet composition
                    cruiser=5 + i//2,
                    mission='colonize',
                    status='stationed'
                )
                fleets_created += 1

                # Send mission
                # In a real scenario, this would be sent via API
                fleet.status = 'traveling'
                fleet.departure_time = datetime.utcnow()
                fleet.arrival_time = datetime.utcnow() + timedelta(seconds=30)  # Fast for testing
                missions_sent += 1

            except Exception as e:
                print(f"Failed to create/send fleet {i}: {e}")

        db_session.commit()
        end_time = time.time()

        total_time = end_time - start_time
        throughput = fleets_created / total_time if total_time > 0 else 0

        print(f"✅ Single user throughput: {throughput:.2f} fleets/second")
        print(f"   Total time: {total_time:.2f}s")
        print(f"   Fleets created: {fleets_created}")
        print(f"   Missions sent: {missions_sent}")

        # Performance assertions
        assert total_time < 5.0, f"Too slow: {total_time:.2f}s for {fleets_created} fleets"
        assert fleets_created == len(target_planets), "Not all fleets created successfully"
        assert throughput > 1.0, f"Low throughput: {throughput:.2f} fleets/second"

    def test_concurrent_users_colonization_load(self, db_session):
        """Test colonization performance under concurrent user load"""
        num_users = 5
        fleets_per_user = 3

        # Create multiple users
        users = []
        for i in range(num_users):
            user, password = create_test_user_with_hashed_password(
                db_session, f'concurrent_perf_{i}', f'perf{i}@test.com', 'password'
            )

            # Create home planet
            home_planet = create_test_planet_with_traits(
                db_session,
                user_id=user.id,
                metal=500000, crystal=250000, deuterium=150000,
                colony_ship=20, light_fighter=2000, cruiser=500
            )

            # Setup research
            research = setup_test_research_levels(
                db_session,
                user.id,
                colonization_tech=3
            )

            users.append({
                'user': user,
                'password': password,
                'home_planet': home_planet,
                'research': research
            })

        # Create target planets for all users
        target_planets = []
        for i in range(num_users * fleets_per_user):
            planet = create_test_planet_with_traits(
                db_session,
                x=i*50, y=i*50, z=i*50,
                planet_type='terrestrial',
                user_id=None
            )
            target_planets.append(planet)

        db_session.commit()

        # Measure concurrent performance
        start_time = time.time()
        results = []
        lock = threading.Lock()

        def user_colonization_workflow(user_data, user_targets):
            """Simulate user colonization workflow"""
            user_results = {
                'user_id': user_data['user'].id,
                'fleets_created': 0,
                'missions_sent': 0,
                'errors': 0,
                'start_time': time.time()
            }

            for target_planet in user_targets:
                try:
                    # Create fleet
                    fleet = create_test_colony_fleet_with_validation(
                        db_session,
                        user_data['user'].id,
                        user_data['home_planet'].id,
                        target_planet.id,
                        colony_ship=1,
                        light_fighter=15,
                        cruiser=8,
                        mission='colonize',
                        status='traveling',
                        departure_time=datetime.utcnow(),
                        arrival_time=datetime.utcnow() + timedelta(seconds=30)
                    )
                    user_results['fleets_created'] += 1
                    user_results['missions_sent'] += 1

                except Exception as e:
                    user_results['errors'] += 1
                    print(f"User {user_data['user'].id} error: {e}")

            user_results['end_time'] = time.time()
            user_results['duration'] = user_results['end_time'] - user_results['start_time']

            with lock:
                results.append(user_results)

        # Execute concurrent workflows
        threads = []
        planets_per_user = len(target_planets) // num_users

        for i, user_data in enumerate(users):
            start_idx = i * planets_per_user
            end_idx = start_idx + fleets_per_user
            user_targets = target_planets[start_idx:end_idx]

            thread = threading.Thread(
                target=user_colonization_workflow,
                args=(user_data, user_targets)
            )
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        end_time = time.time()
        total_time = end_time - start_time

        # Analyze results
        total_fleets = sum(r['fleets_created'] for r in results)
        total_missions = sum(r['missions_sent'] for r in results)
        total_errors = sum(r['errors'] for r in results)
        user_durations = [r['duration'] for r in results]

        throughput = total_fleets / total_time if total_time > 0 else 0
        avg_user_time = statistics.mean(user_durations) if user_durations else 0
        max_user_time = max(user_durations) if user_durations else 0

        print("✅ Concurrent users performance test results:")
        print(f"   Total users: {num_users}")
        print(f"   Total fleets created: {total_fleets}")
        print(f"   Total missions sent: {total_missions}")
        print(f"   Total errors: {total_errors}")
        print(f"   Total time: {total_time:.2f}s")
        print(f"   Throughput: {throughput:.2f} fleets/second")
        print(f"   Average user time: {avg_user_time:.2f}s")
        print(f"   Max user time: {max_user_time:.2f}s")

        # Performance assertions
        assert total_errors == 0, f"Too many errors: {total_errors}"
        assert total_fleets == num_users * fleets_per_user, "Not all fleets created"
        assert total_time < 10.0, f"Too slow: {total_time:.2f}s for concurrent operations"
        assert throughput > 2.0, f"Low throughput: {throughput:.2f} fleets/second"

    def test_memory_usage_during_colonization_operations(self, db_session):
        """Test memory usage during intensive colonization operations"""
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Create large-scale scenario
        num_users = 10
        fleets_per_user = 5

        users = []
        for i in range(num_users):
            user, password = create_test_user_with_hashed_password(
                db_session, f'memory_test_{i}', f'memory{i}@test.com', 'password'
            )

            home_planet = create_test_planet_with_traits(
                db_session,
                user_id=user.id,
                metal=100000, crystal=50000, deuterium=30000,
                colony_ship=10, light_fighter=1000, cruiser=200
            )

            users.append({'user': user, 'home_planet': home_planet})

        # Create target planets
        target_planets = []
        for i in range(num_users * fleets_per_user):
            planet = create_test_planet_with_traits(
                db_session,
                x=i*20, y=i*20, z=i*20,
                planet_type='terrestrial',
                user_id=None
            )
            target_planets.append(planet)

        db_session.commit()

        # Perform operations and monitor memory
        memory_readings = []
        start_time = time.time()

        for i, user_data in enumerate(users):
            user_targets = target_planets[i*fleets_per_user:(i+1)*fleets_per_user]

            for target_planet in user_targets:
                # Create and send fleet
                fleet = create_test_colony_fleet_with_validation(
                    db_session,
                    user_data['user'].id,
                    user_data['home_planet'].id,
                    target_planet.id,
                    colony_ship=1,
                    light_fighter=10,
                    cruiser=5,
                    mission='colonize',
                    status='traveling'
                )

            # Record memory usage
            current_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_readings.append(current_memory)

            if (i + 1) % 2 == 0:  # Every 2 users
                db_session.commit()  # Force commit to test memory management

        end_time = time.time()
        final_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Analyze memory usage
        memory_increase = final_memory - initial_memory
        avg_memory = statistics.mean(memory_readings)
        max_memory = max(memory_readings)
        memory_growth_rate = memory_increase / (end_time - start_time) if (end_time - start_time) > 0 else 0

        print("✅ Memory usage test results:")
        print(f"   Initial memory: {initial_memory:.2f} MB")
        print(f"   Final memory: {final_memory:.2f} MB")
        print(f"   Memory increase: {memory_increase:.2f} MB")
        print(f"   Average memory: {avg_memory:.2f} MB")
        print(f"   Max memory: {max_memory:.2f} MB")
        print(f"   Memory growth rate: {memory_growth_rate:.2f} MB/second")

        # Memory assertions
        assert memory_increase < 50, f"Excessive memory increase: {memory_increase:.2f} MB"
        assert max_memory < initial_memory + 100, f"Memory usage too high: {max_memory:.2f} MB"

    def test_database_performance_under_load(self, db_session):
        """Test database performance during colonization operations"""
        # Create test scenario
        user, password = create_test_user_with_hashed_password(
            db_session, 'db_perf', 'db@test.com', 'password'
        )

        home_planet = create_test_planet_with_traits(
            db_session,
            user_id=user.id,
            metal=1000000, crystal=500000, deuterium=300000,
            colony_ship=100, light_fighter=10000, cruiser=2000
        )

        # Create many target planets
        target_planets = []
        for i in range(50):
            planet = create_test_planet_with_traits(
                db_session,
                x=i*10, y=i*10, z=i*10,
                planet_type='terrestrial',
                user_id=None
            )
            target_planets.append(planet)

        db_session.commit()

        # Measure database operation times
        create_times = []
        query_times = []
        update_times = []

        for i, target_planet in enumerate(target_planets):
            # Measure fleet creation time
            start_time = time.time()
            fleet = create_test_colony_fleet_with_validation(
                db_session,
                user.id,
                home_planet.id,
                target_planet.id,
                colony_ship=1,
                light_fighter=10,
                cruiser=5,
                mission='colonize',
                status='stationed'
            )
            create_time = time.time() - start_time
            create_times.append(create_time)

            # Measure query time
            start_time = time.time()
            fleets = db_session.query(db_session.query().entity).filter_by(user_id=user.id).all()
            query_time = time.time() - start_time
            query_times.append(query_time)

            # Measure update time
            start_time = time.time()
            fleet.status = 'traveling'
            fleet.departure_time = datetime.utcnow()
            db_session.commit()
            update_time = time.time() - start_time
            update_times.append(update_time)

        # Analyze performance metrics
        avg_create_time = statistics.mean(create_times)
        avg_query_time = statistics.mean(query_times)
        avg_update_time = statistics.mean(update_times)

        max_create_time = max(create_times)
        max_query_time = max(query_times)
        max_update_time = max(update_times)

        print("✅ Database performance test results:")
        print(f"   Average create time: {avg_create_time*1000:.2f}ms")
        print(f"   Average query time: {avg_query_time*1000:.2f}ms")
        print(f"   Average update time: {avg_update_time*1000:.2f}ms")
        print(f"   Max create time: {max_create_time*1000:.2f}ms")
        print(f"   Max query time: {max_query_time*1000:.2f}ms")
        print(f"   Max update time: {max_update_time*1000:.2f}ms")

        # Performance assertions
        assert avg_create_time < 0.1, f"Slow creates: {avg_create_time*1000:.2f}ms avg"
        assert avg_query_time < 0.05, f"Slow queries: {avg_query_time*1000:.2f}ms avg"
        assert avg_update_time < 0.1, f"Slow updates: {avg_update_time*1000:.2f}ms avg"
        assert max_create_time < 0.5, f"Very slow create: {max_create_time*1000:.2f}ms max"
        assert max_query_time < 0.2, f"Very slow query: {max_query_time*1000:.2f}ms max"
        assert max_update_time < 0.5, f"Very slow update: {max_update_time*1000:.2f}ms max"

    def test_api_endpoint_performance(self):
        """Test API endpoint performance under load"""
        # This test requires running backend server
        auth_data = login_as_test_user()

        # Test fleet creation API performance
        create_times = []
        for i in range(10):
            start_time = time.time()
            try:
                fleet = create_colonization_fleet_api(
                    auth_headers=auth_data['headers'],
                    fleet_data={
                        'start_planet_id': 1,
                        'colony_ship': 1,
                        'light_fighter': 10 + i,
                        'cruiser': 5
                    }
                )
                create_time = time.time() - start_time
                create_times.append(create_time)
            except Exception as e:
                print(f"API create failed: {e}")
                create_times.append(1.0)  # Penalize failures

        # Test fleet retrieval API performance
        query_times = []
        for i in range(20):
            start_time = time.time()
            try:
                fleets = get_fleets_api(auth_headers=auth_data['headers'])
                query_time = time.time() - start_time
                query_times.append(query_time)
            except Exception as e:
                print(f"API query failed: {e}")
                query_times.append(1.0)  # Penalize failures

        # Analyze API performance
        if create_times:
            avg_create_time = statistics.mean(create_times)
            max_create_time = max(create_times)
            print(f"✅ API Create Performance: {avg_create_time:.3f}s avg, {max_create_time:.3f}s max")

            assert avg_create_time < 0.5, f"Slow API creates: {avg_create_time:.3f}s avg"
            assert max_create_time < 2.0, f"Very slow API create: {max_create_time:.3f}s max"

        if query_times:
            avg_query_time = statistics.mean(query_times)
            max_query_time = max(query_times)
            print(f"✅ API Query Performance: {avg_query_time:.3f}s avg, {max_query_time:.3f}s max")

            assert avg_query_time < 0.2, f"Slow API queries: {avg_query_time:.3f}s avg"
            assert max_query_time < 1.0, f"Very slow API query: {max_query_time:.3f}s max"

    def test_scalability_with_increasing_load(self, db_session):
        """Test how performance scales with increasing load"""
        # Test with different load levels
        load_levels = [5, 10, 20, 50]

        scalability_results = []

        for num_operations in load_levels:
            print(f"\n🧪 Testing scalability with {num_operations} operations...")

            # Create test user
            user, password = create_test_user_with_hashed_password(
                db_session, f'scalability_{num_operations}', f'scale{num_operations}@test.com', 'password'
            )

            home_planet = create_test_planet_with_traits(
                db_session,
                user_id=user.id,
                metal=1000000, crystal=500000, deuterium=300000,
                colony_ship=num_operations, light_fighter=num_operations*10
            )

            # Create target planets
            target_planets = []
            for i in range(num_operations):
                planet = create_test_planet_with_traits(
                    db_session,
                    x=i*5, y=i*5, z=i*5,
                    planet_type='terrestrial',
                    user_id=None
                )
                target_planets.append(planet)

            db_session.commit()

            # Measure performance
            start_time = time.time()
            successful_operations = 0

            for target_planet in target_planets:
                try:
                    fleet = create_test_colony_fleet_with_validation(
                        db_session,
                        user.id,
                        home_planet.id,
                        target_planet.id,
                        colony_ship=1,
                        light_fighter=10,
                        cruiser=5,
                        mission='colonize',
                        status='traveling'
                    )
                    successful_operations += 1
                except Exception as e:
                    print(f"Failed operation: {e}")

            end_time = time.time()
            total_time = end_time - start_time
            throughput = successful_operations / total_time if total_time > 0 else 0

            scalability_results.append({
                'load_level': num_operations,
                'total_time': total_time,
                'successful_operations': successful_operations,
                'throughput': throughput,
                'success_rate': successful_operations / num_operations
            })

            print(f"   Load {num_operations}: {throughput:.2f} ops/sec, {total_time:.2f}s total")

        # Analyze scalability
        throughputs = [r['throughput'] for r in scalability_results]
        throughput_decline = throughputs[0] / throughputs[-1] if throughputs[-1] > 0 else float('inf')

        print("\n✅ Scalability analysis:")
        print(f"   Throughput decline: {throughput_decline:.2f}x")
        print(f"   Best throughput: {max(throughputs):.2f} ops/sec")
        print(f"   Worst throughput: {min(throughputs):.2f} ops/sec")

        # Scalability should not degrade too much
        assert throughput_decline < 5.0, f"Poor scalability: {throughput_decline:.2f}x decline"


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
