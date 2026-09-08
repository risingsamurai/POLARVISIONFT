"use client";

import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { latLonToScene } from "@/lib/geo";
import { usePolarisStore } from "@/lib/store";

export function DangerZone({
  lat,
  lon,
  radiusNm,
}: {
  lat: number;
  lon: number;
  radiusNm: number;
}) {
  const [x, , z] = latLonToScene(lat, lon);
  const ringRef = useRef<THREE.Mesh>(null);
  const beaconRef = useRef<THREE.Group>(null);

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();
    if (ringRef.current) {
      const scale = 1.0 + Math.sin(t * 2.5) * 0.05;
      ringRef.current.scale.set(scale, scale, 1);
      const mat = ringRef.current.material as THREE.MeshBasicMaterial;
      if (mat) mat.opacity = 0.45 + Math.sin(t * 2.5) * 0.2;
    }
    if (beaconRef.current) {
      beaconRef.current.rotation.y = t * 1.5;
      beaconRef.current.position.y = 3.5 + Math.sin(t * 2.0) * 0.3;
    }
  });

  const r = Math.max(2.5, radiusNm * 0.8);

  return (
    <group position={[x, 0.05, z]}>
      {/* Semi-transparent red danger zone disk on water */}
      <mesh rotation={[-Math.PI / 2, 0, 0]}>
        <circleGeometry args={[r, 48]} />
        <meshBasicMaterial color="#ef4444" transparent opacity={0.15} />
      </mesh>

      {/* Main Solid Outer Warning Ring */}
      <mesh rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[r * 0.94, r, 64]} />
        <meshBasicMaterial color="#ef4444" transparent opacity={0.6} />
      </mesh>

      {/* Inner Pulsing Warning Ring */}
      <mesh ref={ringRef} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[r * 0.80, r * 0.84, 64]} />
        <meshBasicMaterial color="#f87171" transparent opacity={0.5} />
      </mesh>

      {/* Floating 3D Warning Beacon & Exclamation Point */}
      <group ref={beaconRef} position={[0, 3.5, 0]}>
        {/* Warning Diamond / Hexagon */}
        <mesh rotation={[0, 0, Math.PI / 4]}>
          <boxGeometry args={[1.2, 1.2, 0.15]} />
          <meshStandardMaterial
            color="#ef4444"
            emissive="#dc2626"
            emissiveIntensity={0.7}
          />
        </mesh>

        {/* Exclamation Point Stem */}
        <mesh position={[0, 0.2, 0.12]}>
          <boxGeometry args={[0.18, 0.6, 0.12]} />
          <meshBasicMaterial color="#ffffff" />
        </mesh>
        {/* Exclamation Point Dot */}
        <mesh position={[0, -0.35, 0.12]}>
          <boxGeometry args={[0.18, 0.18, 0.12]} />
          <meshBasicMaterial color="#ffffff" />
        </mesh>
      </group>
    </group>
  );
}

export function DangerZones() {
  const icebergs = usePolarisStore((s) => s.icebergs);
  const visible = usePolarisStore((s) => s.layers.riskZones);
  if (!visible) return null;

  return (
    <group>
      {icebergs
        .filter((ib) => ib.highRisk || (ib.dangerRadiusNm && ib.dangerRadiusNm > 0))
        .map((ib) => (
          <DangerZone
            key={ib.id}
            lat={ib.lat}
            lon={ib.lon}
            radiusNm={ib.dangerRadiusNm || ib.diameterNm * 2}
          />
        ))}
    </group>
  );
}

