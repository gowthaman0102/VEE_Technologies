"use client";

import dynamic from "next/dynamic";
import { useEffect, useState, useRef } from "react";
import * as THREE from 'three';

const Globe = dynamic(() => import("react-globe.gl"), { ssr: false });

export type CoverageMarker = {
  label: string;
  latitude: number;
  longitude: number;
  color: string;
  size: number;
  locationType: string;
  city?: string;
  country?: string;
  imageUrl?: string;
  isHQ?: boolean;
};

export function CoverageGlobe({
  markers,
  onMarkerClick,
}: {
  markers: CoverageMarker[];
  onMarkerClick?: (marker: CoverageMarker) => void;
}) {
  const [countries, setCountries] = useState<object[]>([]);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const globeRef = useRef<any>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 400, height: 400 });
  const [webglSupported, setWebglSupported] = useState(true);

  // Check WebGL Support
  useEffect(() => {
    try {
      const canvas = document.createElement("canvas");
      const gl = canvas.getContext("webgl") || canvas.getContext("experimental-webgl");
      if (!gl) setWebglSupported(false);
    } catch (e) {
      setWebglSupported(false);
    }
  }, []);

  // ResizeObserver for canvas wrapper
  useEffect(() => {
    if (!containerRef.current) return;
    const observer = new ResizeObserver((entries) => {
      for (const entry of entries) {
        let width = entry.contentRect.width;
        let height = entry.contentRect.height;
        // Cap resolution scaling on smaller screens
        if (width < 480) {
          // You could dynamically adjust devicePixelRatio here if working with raw ThreeJS
        }
        setDimensions({ width, height });
      }
    });
    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  // IntersectionObserver + Visibility API to pause rendering
  useEffect(() => {
    if (!globeRef.current || !containerRef.current) return;
    
    const handleVisibility = (isVisible: boolean) => {
      if (!globeRef.current) return;
      try {
        if (isVisible && document.visibilityState === "visible") {
          if (globeRef.current.resumeAnimation) globeRef.current.resumeAnimation();
        } else {
          if (globeRef.current.pauseAnimation) globeRef.current.pauseAnimation();
        }
      } catch (e) {
        // Ignore if methods don't exist
      }
    };

    const observer = new IntersectionObserver(
      (entries) => handleVisibility(entries[0].isIntersecting),
      { threshold: 0 }
    );
    
    observer.observe(containerRef.current);
    
    const onVisChange = () => {
      // Re-evaluate intersection if needed, but for simplicity rely on visibility API directly here
      if (document.visibilityState !== "visible") handleVisibility(false);
    };
    
    document.addEventListener("visibilitychange", onVisChange);
    return () => {
      observer.disconnect();
      document.removeEventListener("visibilitychange", onVisChange);
    };
  }, []);

  // Fetch topologies for continent outlines
  useEffect(() => {
    let cancelled = false;
    fetch("https://unpkg.com/world-atlas@2/countries-110m.json")
      .then((response) => {
        if (!response.ok) throw new Error(`World map request failed: ${response.status}`);
        return response.json();
      })
      .then((topology) => {
        if (!cancelled) setCountries(topology.objects.countries.geometries);
      })
      .catch((error) => console.error("Unable to load world map boundaries", error));
    return () => {
      cancelled = true;
    };
  }, []);

  const hqMarker = markers.find(m => m.isHQ);
  const [hqPos, setHqPos] = useState<{x: number, y: number, occluded: boolean} | null>(null);

  useEffect(() => {
    if (!globeRef.current || !hqMarker) return;
    
    let animationFrameId: number;
    const updatePosition = () => {
      try {
        const globe = globeRef.current as any;
        if (globe && globe.getCoords && globe.camera && dimensions.width > 0) {
          const coords = globe.getCoords(hqMarker.latitude, hqMarker.longitude, 0);
          const camera = globe.camera();
          if (coords && camera) {
            // Manual projection using THREE
            const vector = new THREE.Vector3(coords.x, coords.y, coords.z);
            vector.project(camera);
            const screenX = (vector.x * 0.5 + 0.5) * dimensions.width;
            const screenY = (vector.y * -0.5 + 0.5) * dimensions.height;
            
            if (!isNaN(screenX) && !isNaN(screenY)) {
              setHqPos({ x: screenX, y: screenY, occluded: false });
            }
          }
        }
      } catch (e) {}
      animationFrameId = requestAnimationFrame(updatePosition);
    };
    
    updatePosition();
    return () => cancelAnimationFrame(animationFrameId);
  }, [hqMarker, dimensions]);

  const onGlobeReady = () => {
    if (globeRef.current) {
      try {
        const controls = globeRef.current.controls();
        const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
        if (controls) {
          controls.autoRotate = !prefersReducedMotion; // Continuous rotation
          controls.autoRotateSpeed = 0.5; // Slow smooth rotation
          controls.enableZoom = false; // Disable zoom to keep static size
          controls.minDistance = controls.getDistance();
          controls.maxDistance = controls.getDistance();
        }

        // Point to North America initially with a much closer altitude (1.2 instead of 2.2) to make the globe large!
        globeRef.current.pointOfView({ lat: 39, lng: -98, altitude: 1.2 }, 0);

        // Adjust lighting for a highly realistic 3D cyber-theme
        const scene = globeRef.current.scene();
        if (scene) {
          // Add a new strong HemisphereLight to ensure the entire globe is evenly lit
          const hemiLight = new THREE.HemisphereLight(0xbfd4ff, 0x1a1030, 0.9);
          scene.add(hemiLight);

          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          scene.children.forEach((child: any) => {
            if (child.type === 'AmbientLight') {
              child.intensity = 0.35; // Match reference
            }
            if (child.type === 'DirectionalLight') {
              child.intensity = 1.6; 
              child.position.set(5, 3, 4); // Match reference sun position
            }
          });

          // Add Custom Atmosphere Shader from Reference
          const earthRadius = 100; // react-globe.gl default
          const atmo = new THREE.Mesh(
            new THREE.SphereGeometry(earthRadius * 1.06, 64, 64),
            new THREE.ShaderMaterial({
              vertexShader: `varying vec3 vN; void main(){ vN=normalize(normalMatrix*normal); gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0); }`,
              fragmentShader: `varying vec3 vN; void main(){ float i=pow(0.62-dot(vN,vec3(0.,0.,1.)),2.5); gl_FragColor=vec4(0.55,0.68,1.0,1.0)*i; }`,
              blending: THREE.AdditiveBlending, side: THREE.BackSide, transparent: true
            })
          );
          // Remove old custom atmo if any (for hot reloading)
          scene.children = scene.children.filter((c: any) => !c.isCustomAtmo);
          (atmo as any).isCustomAtmo = true;
          scene.add(atmo);
        }
        
        const material = globeRef.current.globeMaterial();
        if (material) {
          if (material.color) material.color.set('#ffffff');
          if (material.specular) material.specular.set('#555577'); // Match reference specular
          if (material.shininess !== undefined) material.shininess = 12; // Match reference shininess
          if (material.emissive) material.emissive.set('#000000'); // Remove the fake glow
        }

      } catch (err) {
        console.error("Globe init error:", err);
      }
    }
  };

  if (!webglSupported) {
    return (
      <div className="flex h-full w-full items-center justify-center rounded-2xl border border-white/10 bg-surface/50 p-6 text-center">
        <p className="text-sm font-medium text-muted">3D visualization unavailable.<br/>Your browser does not support WebGL.</p>
      </div>
    );
  }

  // Label coordinates (fixed top-left)
  const labelX = 60;
  const labelY = 60;

  return (
    <div 
      className="globe-root relative flex w-full h-full items-center justify-center mx-auto z-10" 
      ref={containerRef}
      style={{
        aspectRatio: "1 / 1",
        maxWidth: "min(100%, 410px)",
        "--globe-marker": "#00f3ff",
        "--globe-accent": "#b8adff",
      } as React.CSSProperties}
    >
      <div 
        role="img" 
        aria-label="Interactive 3D globe showing global company presence" 
        className="absolute inset-0 flex items-center justify-center"
      >
        <Globe
          ref={globeRef}
          onGlobeReady={onGlobeReady}
          width={dimensions.width}
          height={dimensions.height}
          backgroundColor="rgba(0,0,0,0)"
          globeImageUrl="//unpkg.com/three-globe/example/img/earth-blue-marble.jpg"
          bumpImageUrl="//unpkg.com/three-globe/example/img/earth-topology.png"
          pointsData={markers}
          pointLat="latitude"
          pointLng="longitude"
          pointColor={(d: object) => (d as CoverageMarker).isHQ ? "var(--globe-marker)" : "var(--globe-accent)"}
          pointRadius={(d: object) => (d as CoverageMarker).isHQ ? 0.8 : 0.4}
          pointsMerge={false}
          ringsData={markers}
          ringLat="latitude"
          ringLng="longitude"
          ringColor={(d: object) => (d as CoverageMarker).isHQ ? "var(--globe-marker)" : "var(--globe-accent)"}
          ringMaxRadius={(d: object) => (d as CoverageMarker).isHQ ? 8 : 4}
          ringPropagationSpeed={2}
          ringRepeatPeriod={800}
          enablePointerInteraction
          onPointClick={(d: object) => {
            if (onMarkerClick) onMarkerClick(d as CoverageMarker);
          }}
          showAtmosphere={false}
        />
      </div>

      {/* Dynamic SVG Connector and Label Overlay */}
      
        <div className="absolute inset-0 pointer-events-none z-20">
          <svg className="absolute inset-0 w-full h-full" style={{ opacity: (hqPos && hqPos.occluded) ? 0.2 : 1, transition: 'opacity 0.3s' }}>
            <path 
              d={`M ${labelX + 110} ${labelY + 56} C ${labelX + 110} ${labelY + 110}, ${hqPos ? hqPos.x : dimensions.width / 2} ${(hqPos ? hqPos.y : dimensions.height / 2) - 50}, ${hqPos ? hqPos.x : dimensions.width / 2} ${hqPos ? hqPos.y : dimensions.height / 2}`} 
              fill="none" 
              stroke="#00f3ff" 
              strokeWidth="2" 
              className="drop-shadow-[0_0_5px_rgba(0,243,255,0.8)]"
            />
            {hqPos && <circle cx={hqPos.x} cy={hqPos.y} r="4" fill="#00f3ff" className="drop-shadow-[0_0_8px_rgba(0,243,255,1)]" />}
          </svg>
          
          <div 
            className="absolute rounded-lg border border-[#00f3ff]/60 bg-[#0a0518]/95 backdrop-blur-md px-4 py-2.5 shadow-[0_0_20px_rgba(0,243,255,0.2)] pointer-events-auto cursor-pointer transition-transform hover:scale-105"
            style={{ top: labelY, left: labelX }}
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              if (hqMarker && onMarkerClick) onMarkerClick(hqMarker);
            }}
          >
            <div className="flex flex-col">
              <span className="text-[13px] font-bold text-white tracking-wide leading-tight">OpenAI Headquarters —</span>
              <span className="text-[12px] font-semibold text-[#e2e8f0] leading-tight mt-0.5">San Francisco, United States</span>
            </div>
          </div>
        </div>
    </div>
  );
}
