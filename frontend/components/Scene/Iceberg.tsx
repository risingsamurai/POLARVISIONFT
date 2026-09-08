"use client";

import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import type { Iceberg } from "@/lib/mockData";
import { latLonToScene } from "@/lib/geo";
import { usePolarisStore } from "@/lib/store";

// Procedural realistic iceberg geometry with individual rounded chunks
function createIcebergGeometry(seed: number, sizeClass: string, scale: number) {
  const rng = (n: number) => {
    const x = Math.sin(seed * 78.233 + n * 12.9898) * 43758.5453;
    return x - Math.floor(x);
  };

  // Create main iceberg body using icosahedron for more organic shape
  const detail = Math.max(1, Math.floor(scale / 2));
  const geo = new THREE.IcosahedronGeometry(scale, detail);
  
  const pos = geo.attributes.position;
  const originalPositions = new Float32Array(pos.count * 3);
  
  // Store original positions
  for (let i = 0; i < pos.count; i++) {
    originalPositions[i * 3] = pos.getX(i);
    originalPositions[i * 3 + 1] = pos.getY(i);
    originalPositions[i * 3 + 2] = pos.getZ(i);
  }

  // Apply noise displacement for realistic ice texture
  for (let i = 0; i < pos.count; i++) {
    const px = originalPositions[i * 3];
    const py = originalPositions[i * 3 + 1];
    const pz = originalPositions[i * 3 + 2];

    // Multi-frequency noise for detailed surface
    const noise1 = (rng(i) - 0.5) * 0.3;
    const noise2 = (rng(i + 100) - 0.5) * 0.15;
    const noise3 = (rng(i + 200) - 0.5) * 0.08;
    
    const totalNoise = noise1 + noise2 + noise3;
    
    // Height variation - taller peaks, flatter base
    const heightFactor = py > 0 ? 1.0 + rng(i + 2) * 0.5 : 0.7 + rng(i + 3) * 0.2;
    
    // Apply displacement
    const displacement = 1 + totalNoise * 0.4;
    
    pos.setXYZ(
      i,
      px * displacement,
      py * heightFactor + totalNoise * scale * 0.2,
      pz * displacement
    );
  }

  geo.computeVertexNormals();
  return geo;
}

export function IcebergMesh({ iceberg }: { iceberg: Iceberg }) {
  const meshRef = useRef<THREE.Mesh>(null);
  const selected = usePolarisStore((s) => s.selectedIcebergId === iceberg.id);
  const select = usePolarisStore((s) => s.selectIceberg);
  const showPred = usePolarisStore((s) => s.layers.predictions);
  const [x, , z] = latLonToScene(iceberg.lat, iceberg.lon);

  // Scaled proportional to real size_nm for realistic appearance
  const baseScale = Math.max(1.5, iceberg.diameterNm * 0.8);
  const seed = Math.abs(iceberg.lat * 100 + iceberg.lon * 10);

  const geo = useMemo(
    () => createIcebergGeometry(seed, iceberg.sizeClass, baseScale),
    [seed, iceberg.sizeClass, baseScale]
  );

  const pathPts = useMemo(() => {
    return iceberg.predictedPath.map((p) => {
      const [px, , pz] = latLonToScene(p.lat, p.lon);
      return new THREE.Vector3(px, 0.4, pz);
    });
  }, [iceberg.predictedPath]);

  useFrame(({ clock }) => {
    if (meshRef.current) {
      // Gentle ocean bobbing for icebergs
      const t = clock.getElapsedTime() + seed;
      meshRef.current.position.y = baseScale * 0.35 + Math.sin(t * 0.8) * 0.08;
      meshRef.current.rotation.z = Math.sin(t * 0.5) * 0.015;
    }
  });

  return (
    <group position={[x, 0, z]}>
      {/* 3D Iceberg Solid */}
      <mesh
        ref={meshRef}
        geometry={geo}
        position={[0, baseScale * 0.35, 0]}
        rotation={[0, (iceberg.headingDeg * Math.PI) / 180, 0]}
        onClick={(e) => {
          e.stopPropagation();
          select(iceberg.id);
        }}
        onPointerOver={(e) => {
          e.stopPropagation();
          document.body.style.cursor = "pointer";
        }}
        onPointerOut={() => {
          document.body.style.cursor = "auto";
        }}
        castShadow
        receiveShadow
      >
        <meshStandardMaterial
          color={selected ? "#bae6fd" : "#e0f7fa"}
          roughness={0.15}
          metalness={0.1}
          flatShading
          emissive={selected ? "#0284c7" : iceberg.highRisk ? "#38bdf8" : "#64748b"}
          emissiveIntensity={selected ? 0.3 : iceberg.highRisk ? 0.12 : 0.04}
          transparent
          opacity={0.95}
        />
      </mesh>

      {/* Underwater Ice Mass Tint / Halo */}
      <mesh position={[0, -0.3, 0]} rotation={[-Math.PI / 2, 0, 0]}>
        <circleGeometry args={[baseScale * 1.35, 16]} />
        <meshBasicMaterial color="#0ea5e9" transparent opacity={0.22} />
      </mesh>

      {/* Selected Target Ring */}
      {selected && (
        <mesh position={[0, 0.25, 0]} rotation={[-Math.PI / 2, 0, 0]}>
          <ringGeometry args={[baseScale * 1.5, baseScale * 1.68, 32]} />
          <meshBasicMaterial color="#38bdf8" />
        </mesh>
      )}

      {/* Predicted Drift Trajectory */}
      {showPred && pathPts.length > 1 && (
        <line>
          <bufferGeometry attach="geometry">
            <bufferAttribute
              attach="attributes-position"
              array={
                new Float32Array(
                  pathPts.flatMap((p) => [p.x - x, p.y, p.z - z])
                )
              }
              count={pathPts.length}
              itemSize={3}
            />
          </bufferGeometry>
          <lineDashedMaterial
            color="#38bdf8"
            dashSize={0.8}
            gapSize={0.4}
            transparent
            opacity={0.85}
          />
        </line>
      )}
    </group>
  );
}

export function IcebergField() {
  const icebergs = usePolarisStore((s) => s.icebergs);
  const visible = usePolarisStore((s) => s.layers.icebergs);
  if (!visible) return null;
  return (
    <group>
      {icebergs.map((ib) => (
        <IcebergMesh key={ib.id} iceberg={ib} />
      ))}
    </group>
  );
}

