"use client";

import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import { latLonToScene } from "@/lib/geo";
import { selectLockedRoute, usePolarisStore } from "@/lib/store";

export function RouteLine() {
  const visible = usePolarisStore((s) => s.layers.route);
  const route = usePolarisStore(selectLockedRoute);
  const vessel = usePolarisStore((s) => s.vessel);
  const version = usePolarisStore((s) => s.routeVersion);
  const dest = usePolarisStore((s) => s.destination);
  const pointsRef = useRef<THREE.Points>(null);

  // Generate smooth spline curve from vessel through waypoints to destination
  const { positions, linePositions, destScenePos } = useMemo(() => {
    if (!route?.points || route.points.length < 1) {
      return {
        positions: new Float32Array(0),
        linePositions: new Float32Array(0),
        destScenePos: [0, 0, 0] as [number, number, number],
      };
    }

    const [vx, , vz] = latLonToScene(vessel.lat, vessel.lon);
    const pts: THREE.Vector3[] = [new THREE.Vector3(vx, 0.45, vz)];

    route.points.forEach((p) => {
      const [px, , pz] = latLonToScene(p.lat, p.lon);
      pts.push(new THREE.Vector3(px, 0.45, pz));
    });

    const [dx, , dz] = latLonToScene(dest.lat, dest.lon);
    pts.push(new THREE.Vector3(dx, 0.45, dz));

    // Smooth curve
    const curve = new THREE.CatmullRomCurve3(pts, false, "centripetal", 0.5);
    const sampled = curve.getPoints(120);

    const beads: number[] = [];
    const lines: number[] = [];

    sampled.forEach((p, i) => {
      lines.push(p.x, p.y, p.z);
      if (i % 2 === 0) {
        beads.push(p.x, p.y + 0.08, p.z);
      }
    });

    return {
      positions: new Float32Array(beads),
      linePositions: new Float32Array(lines),
      destScenePos: [dx, 0.45, dz] as [number, number, number],
    };
  }, [route, vessel.lat, vessel.lon, dest, version]);

  useFrame(({ clock }) => {
    if (pointsRef.current) {
      const mat = pointsRef.current.material as THREE.PointsMaterial;
      if (mat) {
        mat.size = 1.1 + Math.sin(clock.getElapsedTime() * 3.0) * 0.2;
      }
    }
  });

  if (!visible || positions.length < 6) return null;

  return (
    <group>
      {/* Underlying subtle glowing route ribbon */}
      <line>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            array={linePositions}
            count={linePositions.length / 3}
            itemSize={3}
          />
        </bufferGeometry>
        <lineBasicMaterial
          color="#10b981"
          transparent
          opacity={0.5}
          linewidth={2}
        />
      </line>

      {/* Glowing Dotted / Bead Green Line */}
      <points ref={pointsRef}>
        <bufferGeometry>
          <bufferAttribute
            attach="attributes-position"
            array={positions}
            count={positions.length / 3}
            itemSize={3}
          />
        </bufferGeometry>
        <pointsMaterial
          color="#34d399"
          size={1.25}
          transparent
          opacity={0.92}
          sizeAttenuation
        />
      </points>

      {/* Destination Target Beacon */}
      <group position={destScenePos}>
        <mesh rotation={[-Math.PI / 2, 0, 0]}>
          <ringGeometry args={[1.8, 2.2, 32]} />
          <meshBasicMaterial color="#10b981" transparent opacity={0.8} />
        </mesh>
        <mesh position={[0, 1.8, 0]}>
          <cylinderGeometry args={[0.15, 0.15, 3.6, 12]} />
          <meshBasicMaterial color="#34d399" transparent opacity={0.7} />
        </mesh>
      </group>
    </group>
  );
}

