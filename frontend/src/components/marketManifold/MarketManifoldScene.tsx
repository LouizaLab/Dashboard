import { useRef, useMemo, useEffect } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Text, Line } from '@react-three/drei';
import * as THREE from 'three';

const MANIFOLD_SIZE = 6;
const SEGMENTS = 100;

// Height function creating fluid-like waves with bumps - MORE DRAMATIC for visibility
function heightFunction(x: number, z: number, time: number = 0): number {
  const scale = MANIFOLD_SIZE / 2;
  const nx = x / scale;
  const nz = z / scale;
  
  let height = 0;
  
  // Fluid wave patterns - INCREASED amplitude for visibility
  const wave1 = 0.4 * Math.sin(nx * 3 + time * 0.5) * Math.cos(nz * 3 + time * 0.5);
  const wave2 = 0.3 * Math.sin(nx * 5 - time * 0.3) * Math.cos(nz * 4 + time * 0.4);
  const wave3 = 0.2 * Math.sin((nx + nz) * 2 + time * 0.6);
  
  height += wave1 + wave2 + wave3;
  
  // Cause and effect bumps - MORE DRAMATIC
  const peak1 = 1.0 * Math.exp(-((nx - 0.0) ** 2 + (nz - 0.0) ** 2) / 0.2);
  height += peak1 * (1 + 0.2 * Math.sin(time * 0.8));
  
  const peak2 = 0.7 * Math.exp(-((nx - 0.6) ** 2 + (nz - 0.3) ** 2) / 0.25);
  height += peak2 * (1 + 0.2 * Math.sin(time * 0.6));
  
  const valley1 = -0.5 * Math.exp(-((nx + 0.5) ** 2 + (nz + 0.4) ** 2) / 0.3);
  height += valley1 * (1 + 0.2 * Math.cos(time * 0.7));
  
  return height;
}

// Get vibrant color based on height - purple to yellow gradient
function getHeatmapColor(height: number): THREE.Color {
  // Normalize height: actual range is approximately -0.3 to 0.9
  const t = Math.max(0, Math.min(1, (height + 0.3) / 1.2));
  
  let r, g, b;
  
  // Purple (low) -> Blue -> Green -> Yellow (high)
  if (t < 0.25) {
    // Deep purple to purple-blue
    const localT = t / 0.25;
    r = 0.5 + (0.3 - 0.5) * localT;
    g = 0.2 + (0.4 - 0.2) * localT;
    b = 0.8 + (0.9 - 0.8) * localT;
  } else if (t < 0.5) {
    // Purple-blue to blue-green
    const localT = (t - 0.25) / 0.25;
    r = 0.3 + (0.0 - 0.3) * localT;
    g = 0.4 + (0.6 - 0.4) * localT;
    b = 0.9 + (0.8 - 0.9) * localT;
  } else if (t < 0.75) {
    // Blue-green to green-yellow
    const localT = (t - 0.5) / 0.25;
    r = 0.0 + (0.5 - 0.0) * localT;
    g = 0.6 + (0.9 - 0.6) * localT;
    b = 0.8 + (0.3 - 0.8) * localT;
  } else {
    // Green-yellow to bright yellow
    const localT = (t - 0.75) / 0.25;
    r = 0.5 + (1.0 - 0.5) * localT;
    g = 0.9 + (1.0 - 0.9) * localT;
    b = 0.3 + (0.2 - 0.3) * localT;
  }
  
  return new THREE.Color(r, g, b);
}

// Manifold surface component
function ManifoldSurface() {
  const meshRef = useRef<THREE.Mesh>(null);
  const gridRef = useRef<THREE.Mesh>(null);
  const timeRef = useRef(0);
  
  // Create geometry with colors - ensure it's rotated to be visible from above
  const geometry = useMemo(() => {
    const geom = new THREE.PlaneGeometry(MANIFOLD_SIZE, MANIFOLD_SIZE, SEGMENTS, SEGMENTS);
    const positions = geom.attributes.position.array as Float32Array;
    const colorArray = new Float32Array(positions.length);
    
    // Initialize positions and colors
    let minY = Infinity;
    let maxY = -Infinity;
    for (let i = 0; i < positions.length; i += 3) {
      const x = positions[i];
      const z = positions[i + 2];
      const y = heightFunction(x, z, 0);
      positions[i + 1] = y; // Set Y position (height)
      
      minY = Math.min(minY, y);
      maxY = Math.max(maxY, y);
      
      const color = getHeatmapColor(y);
      colorArray[i] = color.r;
      colorArray[i + 1] = color.g;
      colorArray[i + 2] = color.b;
    }
    
    // Set color attribute - ensure it's properly configured
    const colorAttr = new THREE.BufferAttribute(colorArray, 3);
    colorAttr.normalized = false;
    geom.setAttribute('color', colorAttr);
    
    // Force update
    geom.attributes.color.needsUpdate = true;
    geom.computeVertexNormals();
    
    // Verify geometry was created with 3D depth
    console.log('ManifoldSurface: Geometry created', {
      vertices: geom.attributes.position.count,
      hasColors: !!geom.getAttribute('color'),
      colorCount: geom.getAttribute('color')?.count,
      minY: minY,
      maxY: maxY,
      depth: maxY - minY
    });
    
    return geom;
  }, []);

  // Surface material with vertex colors - use MeshBasicMaterial for simplicity
  const surfaceMaterial = useMemo(() => {
    const material = new THREE.MeshBasicMaterial({
      vertexColors: true,
      side: THREE.DoubleSide,
      transparent: false,
      opacity: 1.0,
    });
    console.log('ManifoldSurface: Material created', {
      vertexColors: material.vertexColors,
      type: material.type,
      transparent: material.transparent
    });
    return material;
  }, []);

  // Wireframe material
  const gridMaterial = useMemo(() => {
    return new THREE.MeshBasicMaterial({
      color: 0x333333,
      wireframe: true,
      transparent: true,
      opacity: 0.2,
    });
  }, []);

  // Animate surface - ensure it updates every frame
  useFrame((state, delta) => {
    timeRef.current += delta; // Use delta for smooth animation
    
    if (meshRef.current && geometry) {
      const positions = geometry.attributes.position.array as Float32Array;
      const colors = geometry.attributes.color!.array as Float32Array;
      
      for (let i = 0; i < positions.length; i += 3) {
        const x = positions[i];
        const z = positions[i + 2];
        const y = heightFunction(x, z, timeRef.current);
        positions[i + 1] = y;
        
        const color = getHeatmapColor(y);
        colors[i] = color.r;
        colors[i + 1] = color.g;
        colors[i + 2] = color.b;
      }
      
      geometry.attributes.position.needsUpdate = true;
      geometry.attributes.color!.needsUpdate = true;
      geometry.computeVertexNormals();
      geometry.attributes.normal.needsUpdate = true;
    }
  });

  // Verify mesh is in scene after mount
  useEffect(() => {
    if (meshRef.current) {
      console.log('ManifoldSurface: Mesh mounted', {
        visible: meshRef.current.visible,
        geometry: meshRef.current.geometry ? 'exists' : 'missing',
        material: meshRef.current.material ? 'exists' : 'missing',
        inScene: meshRef.current.parent !== null
      });
    }
  }, []);

  if (!geometry) {
    return null;
  }

  return (
    <group>
      {/* Main colored surface - render first */}
      <mesh 
        ref={meshRef} 
        geometry={geometry} 
        material={surfaceMaterial}
        visible={true}
        position={[0, 0, 0]}
        rotation={[-Math.PI / 2, 0, 0]}
        renderOrder={0}
      />
      {/* Wireframe overlay - render on top */}
      <mesh 
        ref={gridRef} 
        geometry={geometry} 
        material={gridMaterial} 
        position={[0, 0.01, 0]}
        rotation={[-Math.PI / 2, 0, 0]}
        visible={true}
        renderOrder={1}
      />
    </group>
  );
}

// Axis component
function Axis({ start, end, label }: { start: [number, number, number], end: [number, number, number], label: string }) {
  const points = useMemo(() => [
    new THREE.Vector3(...start),
    new THREE.Vector3(...end),
  ], [start, end]);

  return (
    <group>
      <Line points={points} color="#333333" lineWidth={3} />
      <Text
        position={[end[0] * 1.15, end[1] * 1.15, end[2] * 1.15]}
        fontSize={0.15}
        color="#333333"
        anchorX="center"
        anchorY="middle"
        outlineWidth={0.01}
        outlineColor="#ffffff"
      >
        {label}
      </Text>
    </group>
  );
}

// Main scene
export default function MarketManifoldScene() {
  return (
    <Canvas
      camera={{ position: [6, 6, 6], fov: 45 }}
      style={{ width: '100%', height: '100%', background: '#ffffff' }}
      gl={{ antialias: true }}
      onCreated={({ gl, camera }) => {
        gl.setClearColor('#ffffff', 1);
        camera.lookAt(0, 0, 0);
      }}
    >
      {/* MeshBasicMaterial doesn't need lights, but keep minimal lighting for wireframe */}
      <ambientLight intensity={0.5} />
      
      <ManifoldSurface />
      
      <Axis 
        start={[0, -0.8, 0]} 
        end={[-2.5, -0.8, -2.5]} 
        label="Price Sensitivity" 
      />
      <Axis 
        start={[0, -0.8, 0]} 
        end={[2.5, -0.8, -2.5]} 
        label="Brand Loyalty" 
      />
      <Axis 
        start={[0, -0.8, 0]} 
        end={[0, 2.0, 0]} 
        label="Trend Fit" 
      />
      
      <OrbitControls
        enablePan={true}
        minDistance={3}
        maxDistance={15}
        target={[0, 0, 0]}
      />
    </Canvas>
  );
}
