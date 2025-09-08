import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * Custom hook for managing sector exploration data
 * Following Custom Hooks Pattern from systemPatterns.md
 */
export const useSectorData = (userId) => {
  const [exploredSectors, setExploredSectors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Fetch explored sectors from API
  const fetchExploredSectors = async () => {
    if (!userId) return;

    try {
      setLoading(true);
      setError(null);

      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('No authentication token found');
      }

      const response = await fetch('http://localhost:5000/api/sectors/explored', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch sectors: ${response.status}`);
      }

      const data = await response.json();
      setExploredSectors(data.explored_sectors || []);
    } catch (err) {
      console.error('Error fetching explored sectors:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Explore a sector via API
  const exploreSector = async (systemX, systemY) => {
    try {
      const token = localStorage.getItem('token');
      if (!token) {
        throw new Error('No authentication token found');
      }

      const response = await fetch('http://localhost:5000/api/sectors/explore', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          system_x: systemX,
          system_y: systemY
        })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `Failed to explore sector: ${response.status}`);
      }

      const data = await response.json();

      // Update local state with newly explored sector
      if (data.newly_explored) {
        const newSector = {
          x: data.sector.x,
          y: data.sector.y,
          explored_at: new Date().toISOString()
        };
        setExploredSectors(prev => [...prev, newSector]);
      }

      return data;
    } catch (err) {
      console.error('Error exploring sector:', err);
      throw err;
    }
  };

  // Check if a sector is explored - properly memoized to prevent infinite loops
  const isSectorExplored = useCallback((sectorX, sectorY) => {
    // Create a stable lookup key
    const key = `${sectorX}:${sectorY}`;

    // Use a simple array lookup instead of some() for better performance
    for (const sector of exploredSectors) {
      if (sector.x === sectorX && sector.y === sectorY) {
        return true;
      }
    }
    return false;
  }, [exploredSectors]);

  // Get sector statistics
  const getSectorStats = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:5000/api/sectors/statistics', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch statistics: ${response.status}`);
      }

      return await response.json();
    } catch (err) {
      console.error('Error fetching sector statistics:', err);
      throw err;
    }
  };

  // Reset exploration data
  const resetExploration = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:5000/api/sectors/reset', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to reset exploration: ${response.status}`);
      }

      // Clear local state
      setExploredSectors([]);
      return await response.json();
    } catch (err) {
      console.error('Error resetting exploration:', err);
      throw err;
    }
  };

  // Fetch data on mount and when userId changes
  useEffect(() => {
    fetchExploredSectors();
  }, [userId]);

  return {
    exploredSectors,
    loading,
    error,
    exploreSector,
    isSectorExplored,
    getSectorStats,
    resetExploration,
    refetch: fetchExploredSectors
  };
};
