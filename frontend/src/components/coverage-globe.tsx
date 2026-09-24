"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";

const Globe = dynamic(() => import("react-globe.gl"), { ssr: false });

type CoverageMarker = {
  label: string;
  latitude: number;
  longitude: number;
  color: string;
  size: number;
  locationType: string;
};

export function CoverageGlobe({
  markers,
}: {
  markers: CoverageMarker[];
}) {
  const [countries, setCountries] = useState<object[]>([]);

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

  return (
    <div className="flex h-[min(520px,58vh)] min-h-[420px] items-center justify-center overflow-hidden rounded-2xl border border-[#a99cf0]/35 bg-[radial-gradient(circle_at_50%_35%,#7565c2_0%,#493b91_42%,#302665_100%)] shadow-[inset_0_0_80px_rgba(183,171,255,.16),0_14px_40px_rgba(48,38,101,.22)]">
      <Globe
        width={520}
        height={420}
        backgroundColor="#4c3f9a"
        globeImageUrl="//unpkg.com/three-globe/example/img/earth-blue-marble.jpg"
        bumpImageUrl="//unpkg.com/three-globe/example/img/earth-topology.png"
        polygonsData={countries}
        polygonCapColor={() => "rgba(129, 112, 218, 0.28)"}
        polygonSideColor={() => "rgba(62, 49, 128, 0.35)"}
        polygonStrokeColor={() => "rgba(224, 219, 255, 0.55)"}
        polygonAltitude={0.006}
        pointsData={markers}
        pointLat="latitude"
        pointLng="longitude"
        pointColor="color"
        pointLabel="label"
        pointRadius="size"
        pointsMerge={false}
        ringsData={markers}
        ringLat="latitude"
        ringLng="longitude"
        ringColor="color"
        ringMaxRadius={3}
        ringPropagationSpeed={1.5}
        ringRepeatPeriod={1200}
        htmlElementsData={markers}
        htmlLat="latitude"
        htmlLng="longitude"
        htmlElement={(data: object) => {
          const marker = data as CoverageMarker;
          const element = document.createElement("div");
          element.className = "pointer-events-none -translate-y-full whitespace-nowrap rounded-lg border border-cyan-100/40 bg-[#241d5d]/90 px-2.5 py-1.5 text-[10px] font-semibold text-cyan-50 shadow-[0_0_18px_rgba(165,243,252,.28)]";
          element.textContent = marker.label;
          return element;
        }}
        enablePointerInteraction
        showAtmosphere
        atmosphereColor="#b8adff"
        atmosphereAltitude={0.18}
      />
    </div>
  );
}
