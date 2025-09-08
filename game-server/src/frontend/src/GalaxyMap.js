import React, { useState, useEffect, useCallback, useRef } from "react";
import { useSectorData } from "./useSectorData";

// Import debug system with error handling
let galaxyDebugger, debugComponent, debugProps, debugDataFlow, debugElement, debugLog;
try {
  const debugModule = require("./GalaxyDebug");
  galaxyDebugger = debugModule.default;
  debugComponent = debugModule.debugComponent;
  debugProps = debugModule.debugProps;
  debugDataFlow = debugModule.debugDataFlow;
  debugElement = debugModule.debugElement;
  debugLog = debugModule.debugLog;
  console.log("✅ GalaxyDebug module imported successfully");
} catch (error) {
  console.error("❌ Failed to import GalaxyDebug module:", error);
  // Fallback to no-op functions
  galaxyDebugger = { config: { debugEnabled: false } };
  debugComponent = { mount: () => {}, unmount: () => {}, update: () => {} };
  debugProps = () => {};
  debugDataFlow = () => {};
  debugElement = { create: () => {}, render: () => {} };
  debugLog = () => {};
}

// Config
const SECTOR_SIZE = 50; // units
const MAP_WIDTH = 1000;
const MAP_HEIGHT = 1000;
const TOTAL_SECTORS = (MAP_WIDTH / SECTOR_SIZE) * (MAP_HEIGHT / SECTOR_SIZE);

const GalaxyMap = ({
  systems,
  initialCenter = { x: 500, y: 500 },
  zoom = 1,
  userId
}) => {
  console.log('🚀 GalaxyMap component function called with props:', { systems, initialCenter, zoom, userId });

  const [viewOffset, setViewOffset] = useState({ x: 0, y: 0 });
  const [center, setCenter] = useState(initialCenter);
  const [sectors, setSectors] = useState([]);
  const [hoveredSector, setHoveredSector] = useState(null);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });

  // Debug: Component mount
  useEffect(() => {
    console.log('🔍 GalaxyMap: Component mounting with debug...');
    try {
      debugComponent.mount('GalaxyMap', { systems, initialCenter, zoom, userId });
      console.log('✅ GalaxyMap: Debug mount called successfully');

      // Validate props
      const expectedProps = [
        { name: 'systems', type: 'object' },
        { name: 'initialCenter', type: 'object' },
        { name: 'zoom', type: 'number' },
        { name: 'userId', type: 'number' }
      ];
      debugProps('GalaxyMap', { systems, initialCenter, zoom, userId }, expectedProps);
      console.log('✅ GalaxyMap: Debug props validation called successfully');
    } catch (error) {
      console.error('❌ GalaxyMap: Debug system failed:', error);
    }

    return () => {
      try {
        debugComponent.unmount('GalaxyMap');
        console.log('✅ GalaxyMap: Debug unmount called successfully');
      } catch (error) {
        console.error('❌ GalaxyMap: Debug unmount failed:', error);
      }
    };
  }, []);

  // Debug: Props changes
  const prevPropsRef = useRef();
  useEffect(() => {
    if (prevPropsRef.current) {
      debugComponent.update('GalaxyMap', prevPropsRef.current, { systems, initialCenter, zoom, userId });
    }
    prevPropsRef.current = { systems, initialCenter, zoom, userId };
  });

  // Use sector data hook
  const {
    exploredSectors,
    loading: sectorsLoading,
    error: sectorsError,
    exploreSector,
    isSectorExplored
  } = useSectorData(userId);

  // Generate grid sectors - optimized to avoid calling isSectorExplored for every sector
  useEffect(() => {
    debugLog('INFO', 'GalaxyMap', 'Generating sector grid', {
      exploredSectorsCount: exploredSectors.length,
      mapDimensions: { width: MAP_WIDTH, height: MAP_HEIGHT },
      sectorSize: SECTOR_SIZE
    });

    // Create a lookup map for explored sectors for O(1) lookup
    const exploredLookup = new Map();
    exploredSectors.forEach(sector => {
      exploredLookup.set(`${sector.x}:${sector.y}`, true);
    });

    const generated = [];
    for (let x = 0; x < MAP_WIDTH; x += SECTOR_SIZE) {
      for (let y = 0; y < MAP_HEIGHT; y += SECTOR_SIZE) {
        const sectorX = Math.floor(x / SECTOR_SIZE);
        const sectorY = Math.floor(y / SECTOR_SIZE);
        const explored = exploredLookup.has(`${sectorX}:${sectorY}`);

        generated.push({
          x: sectorX,
          y: sectorY,
          explored: explored
        });
      }
    }

    debugDataFlow('GalaxyMap', 'sector-generation', { exploredSectors }, { sectors: generated }, true);
    setSectors(generated);
  }, [exploredSectors]); // Only depend on exploredSectors, not isSectorExplored

  // Convert sector coordinates to screen position
  const getSectorPosition = (sector) => ({
    x: (sector.x - center.x) * zoom + window.innerWidth / 2 + viewOffset.x,
    y: (sector.y - center.y) * zoom + window.innerHeight / 2 + viewOffset.y,
  });

  // Convert system coordinates to screen position
  const getSystemPosition = (system) => ({
    x: (system.x - center.x) * zoom + window.innerWidth / 2 + viewOffset.x,
    y: (system.y - center.y) * zoom + window.innerHeight / 2 + viewOffset.y,
  });

  // Handle system exploration via API
  const handleExploreSystem = async (system) => {
    debugLog('INFO', 'GalaxyMap', 'System exploration initiated', {
      system: { x: system.x, y: system.y, z: system.z },
      userId
    });

    try {
      // Call API to explore sector
      const startTime = Date.now();
      const result = await exploreSector(system.x, system.y);
      const duration = Date.now() - startTime;

      debugDataFlow('GalaxyMap', 'explore-sector-api', { system, userId }, { result, duration }, result.success);

      if (result.success) {
        debugLog('INFO', 'GalaxyMap', 'Sector exploration successful', {
          sector: result.sector,
          newly_explored: result.newly_explored,
          duration
        });

        // Update local sector state
        setSectors(prev =>
          prev.map(sector =>
            sector.x === result.sector.x && sector.y === result.sector.y
              ? { ...sector, explored: true }
              : sector
          )
        );

        // Optional: Show success feedback
        if (result.newly_explored) {
          debugLog('INFO', 'GalaxyMap', 'New sector discovered', {
            coordinates: `${result.sector.x}:${result.sector.y}`,
            totalExplored: exploredSectors.length + 1
          });
        } else {
          debugLog('INFO', 'GalaxyMap', 'Sector was already explored', {
            coordinates: `${result.sector.x}:${result.sector.y}`
          });
        }
      } else {
        debugLog('WARN', 'GalaxyMap', 'Sector exploration returned unsuccessful', { result });
      }
    } catch (error) {
      debugLog('ERROR', 'GalaxyMap', 'Sector exploration failed', {
        system,
        error: error.message,
        stack: error.stack
      });
      // Optional: Show error feedback to user
    }
  };

  // Show loading state
  if (sectorsLoading) {
    return (
      <div className="relative w-full h-full overflow-hidden bg-black flex items-center justify-center">
        <div className="text-white text-lg">Loading galaxy sectors...</div>
      </div>
    );
  }

  // Show error state
  if (sectorsError) {
    return (
      <div className="relative w-full h-full overflow-hidden bg-black flex items-center justify-center">
        <div className="text-red-400 text-center">
          <div className="text-lg mb-2">Failed to load galaxy sectors</div>
          <div className="text-sm">{sectorsError}</div>
        </div>
      </div>
    );
  }

  // Calculate progress
  const exploredCount = exploredSectors.length;
  const progressPercentage = TOTAL_SECTORS > 0 ? (exploredCount / TOTAL_SECTORS) * 100 : 0;

  debugLog('INFO', 'GalaxyMap', 'Rendering galaxy map', {
    sectorsCount: sectors.length,
    systemsCount: systems?.length || 0,
    exploredCount: exploredSectors.length,
    progressPercentage: progressPercentage.toFixed(1) + '%'
  });

  return (
    <div className="relative w-full h-full overflow-hidden bg-black">
      {/* Debug Panel */}
      {galaxyDebugger.config?.visual?.debugPanel && (
        <div className="debug-panel">
          <h4>🔍 Debug Info</h4>
          <div>Sectors: {sectors.length}</div>
          <div>Systems: {systems?.length || 0}</div>
          <div>Explored: {exploredCount}</div>
          <div>Progress: {progressPercentage.toFixed(1)}%</div>
          <div>Center: ({center.x}, {center.y})</div>
          <div>Zoom: {zoom}</div>
        </div>
      )}

      {/* Sector Grid Overlay */}
      <div className="sector-grid">
        {debugElement.create('GalaxyMap', 'sector-grid', { count: sectors.length })}
        {sectors && sectors.map((sector, idx) => {
          const pos = getSectorPosition(sector);
          // Removed debug log for sector-boundary creation to reduce noise
          // debugElement.create('GalaxyMap', 'sector-boundary', {
          //   sector: `${sector.x}:${sector.y}`,
          //   explored: sector.explored,
          //   position: pos
          // });

          return (
            <div
              key={`boundary-${idx}`}
              className={`sector-boundary ${sector.explored ? 'explored' : 'unexplored'}`}
              style={{
                left: `${pos.x}px`,
                top: `${pos.y}px`,
                width: `${SECTOR_SIZE * zoom}px`,
                height: `${SECTOR_SIZE * zoom}px`,
                transform: "translate(-50%, -50%)",
              }}
              onMouseEnter={(e) => {
                setHoveredSector(sector);
                setTooltipPosition({ x: e.clientX, y: e.clientY });
              }}
              onMouseLeave={() => setHoveredSector(null)}
            />
          );
        })}
        {debugElement.render('GalaxyMap', 'sector-grid', sectors && sectors.length > 0)}
      </div>

      {/* Space background - always visible */}
      {sectors && sectors.map((s, idx) => {
        const pos = getSectorPosition(s);
        return (
          <div
            key={`bg-${idx}`}
            className="absolute bg-gradient-to-br from-blue-900 via-black to-purple-900"
            style={{
              left: `${pos.x}px`,
              top: `${pos.y}px`,
              width: `${SECTOR_SIZE * zoom}px`,
              height: `${SECTOR_SIZE * zoom}px`,
              transform: "translate(-50%, -50%)",
              pointerEvents: "none",
              zIndex: 0,
            }}
          />
        );
      })}

      {/* Systems */}
      {systems && systems.map((sys, idx) => {
        const pos = getSystemPosition(sys);
        return (
          <div
            key={`sys-${idx}`}
            onClick={() => handleExploreSystem(sys)}
            className="sector-system-marker absolute bg-yellow-400 rounded-full cursor-pointer"
            style={{
              left: `${pos.x}px`,
              top: `${pos.y}px`,
              width: `${10 * zoom}px`,
              height: `${10 * zoom}px`,
              transform: "translate(-50%, -50%)",
              zIndex: 5,
            }}
          />
        );
      })}



      {/* Sector Progress Indicator */}
      <div className="sector-progress">
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: `${progressPercentage}%` }}
          />
        </div>
        <div className="progress-text">
          {exploredCount} / {TOTAL_SECTORS} sectors explored
        </div>
      </div>

      {/* Sector Statistics Panel */}
      <div className="sector-stats-panel">
        <h3>🌌 Galaxy Statistics</h3>
        <div className="stat-item">
          <span>Explored Sectors:</span>
          <span className="stat-value">{exploredCount}</span>
        </div>
        <div className="stat-item">
          <span>Total Sectors:</span>
          <span className="stat-value">{TOTAL_SECTORS}</span>
        </div>
        <div className="stat-item">
          <span>Exploration Progress:</span>
          <span className="stat-value">{progressPercentage.toFixed(1)}%</span>
        </div>
        <div className="stat-item">
          <span>Systems Visible:</span>
          <span className="stat-value">{systems ? systems.length : 0}</span>
        </div>
      </div>

      {/* Sector Tooltip */}
      {hoveredSector && (
        <div
          className="sector-tooltip"
          style={{
            left: `${tooltipPosition.x + 10}px`,
            top: `${tooltipPosition.y - 10}px`,
          }}
        >
          <h4>Sector {hoveredSector.x}:{hoveredSector.y}</h4>
          <p>Status: {hoveredSector.explored ? 'Explored' : 'Unexplored'}</p>
          <p>Coordinates: ({hoveredSector.x * SECTOR_SIZE}, {hoveredSector.y * SECTOR_SIZE})</p>
          <p>Size: {SECTOR_SIZE}x{SECTOR_SIZE} units</p>
          {hoveredSector.explored && (
            <p>Click systems to explore further!</p>
          )}
        </div>
      )}
    </div>
  );
};

export default GalaxyMap;
