import { useEffect, useRef } from "react";
import * as THREE from "three";

/**
 * NOVA hologram — rotating wireframe core + particle field.
 * Pure three.js, no extra deps. Respects prefers-reduced-motion.
 * `fill` makes the canvas stretch to its parent; otherwise `size`x`size`.
 */
export default function HoloAvatar({ size = 280, active = false, fill = false }) {
  const mountRef = useRef(null);
  const activeRef = useRef(active);

  useEffect(() => {
    activeRef.current = active;
  }, [active]);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return;
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100);
    camera.position.z = 4.6;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    mount.appendChild(renderer.domElement);

    const group = new THREE.Group();
    scene.add(group);

    // Core: wireframe icosahedron
    const coreGeo = new THREE.IcosahedronGeometry(1.15, 1);
    const coreMat = new THREE.MeshBasicMaterial({
      color: 0x8b5cf6,
      wireframe: true,
      transparent: true,
      opacity: 0.55,
    });
    const core = new THREE.Mesh(coreGeo, coreMat);
    group.add(core);

    // Inner solid glow sphere
    const innerGeo = new THREE.IcosahedronGeometry(0.55, 2);
    const innerMat = new THREE.MeshBasicMaterial({
      color: 0xc084fc,
      transparent: true,
      opacity: 0.18,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
    group.add(new THREE.Mesh(innerGeo, innerMat));

    // Outer ring
    const ringGeo = new THREE.TorusGeometry(1.7, 0.012, 8, 90);
    const ringMat = new THREE.MeshBasicMaterial({
      color: 0xa78bfa, transparent: true, opacity: 0.5,
      blending: THREE.AdditiveBlending, depthWrite: false,
    });
    const ring = new THREE.Mesh(ringGeo, ringMat);
    ring.rotation.x = Math.PI / 2.4;
    group.add(ring);

    // Particle field
    const pCount = 350;
    const pos = new Float32Array(pCount * 3);
    for (let i = 0; i < pCount; i++) {
      const r = 1.8 + Math.random() * 1.6;
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      pos[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      pos[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      pos[i * 3 + 2] = r * Math.cos(phi);
    }
    const pGeo = new THREE.BufferGeometry();
    pGeo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    const pMat = new THREE.PointsMaterial({
      color: 0x8b5cf6, size: 0.02, transparent: true, opacity: 0.7,
      blending: THREE.AdditiveBlending, depthWrite: false,
    });
    const particles = new THREE.Points(pGeo, pMat);
    group.add(particles);

    // Scan ring (hologram sweep)
    const scanGeo = new THREE.TorusGeometry(1.35, 0.006, 8, 80);
    const scanMat = new THREE.MeshBasicMaterial({
      color: 0x22d3ee, transparent: true, opacity: 0.35,
      blending: THREE.AdditiveBlending, depthWrite: false,
    });
    const scan = new THREE.Mesh(scanGeo, scanMat);
    scan.rotation.x = Math.PI / 2;
    group.add(scan);

    // Responsive fit: renderer fills mount, camera aspect + group scale track size
    const fit = () => {
      const w = mount.clientWidth || size;
      const h = mount.clientHeight || size;
      renderer.setSize(w, h);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      const s = Math.min(w, h) / 340;
      group.scale.setScalar(Math.max(0.4, Math.min(s, 1.6)));
    };
    fit();
    const ro = new ResizeObserver(fit);
    ro.observe(mount);

    const onColor = new THREE.Color(0x22d3ee);
    const offColor = new THREE.Color(0x8b5cf6);
    const tmp = new THREE.Color();

    let raf;
    const clock = new THREE.Clock();
    const animate = () => {
      raf = requestAnimationFrame(animate);
      const t = clock.getElapsedTime();
      const on = activeRef.current;
      if (!reduced) {
        core.rotation.y = t * 0.4;
        core.rotation.x = Math.sin(t * 0.3) * 0.25;
        innerMat.opacity = 0.12 + Math.sin(t * 2) * 0.07;
        ring.rotation.z = t * 0.2;
        particles.rotation.y = -t * 0.08;
        scan.position.y = Math.sin(t * 0.8) * 0.9;
        scan.rotation.z = t * 0.5;
        group.position.y = Math.sin(t * 0.7) * 0.08;
      }
      // smooth color shift when listening/speaking
      tmp.copy(on ? onColor : offColor);
      coreMat.color.lerp(tmp, 0.08);
      innerMat.color.lerp(tmp, 0.08);
      pMat.color.lerp(tmp, 0.08);
      ringMat.color.lerp(tmp, 0.05);
      renderer.render(scene, camera);
    };
    animate();

    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
      mount.removeChild(renderer.domElement);
      renderer.dispose();
      coreGeo.dispose(); coreMat.dispose();
      innerGeo.dispose(); innerMat.dispose();
      ringGeo.dispose(); ringMat.dispose();
      pGeo.dispose(); pMat.dispose();
      scanGeo.dispose(); scanMat.dispose();
    };
  }, [size]);

  return (
    <div
      ref={mountRef}
      style={fill ? { width: "100%", height: "100%" } : { width: size, height: size, margin: "0 auto" }}
      aria-label="NOVA hologram"
    />
  );
}
