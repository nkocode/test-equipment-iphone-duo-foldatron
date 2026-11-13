import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import model from '../../hardware/bench-model.json';

const viewport = document.querySelector('#viewport');
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setClearColor(0xe7ece8);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.25;
viewport.appendChild(renderer.domElement);
const scene = new THREE.Scene();
scene.background = new THREE.Color(0xe7ece8);
let camera = new THREE.PerspectiveCamera(35, 1, 1, 6000);
let orthoHeight = 1000;
camera.up.set(0, 0, 1);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.minDistance = 150;
controls.maxDistance = 2500;
controls.maxPolarAngle = Math.PI * 0.8;
scene.add(new THREE.HemisphereLight(0xffffff, 0x5d7471, 2.7));
const sun = new THREE.DirectionalLight(0xfff9ed, 3.7);
sun.position.set(250, -300, 650);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
Object.assign(sun.shadow.camera, { left: -350, right: 350, top: 350, bottom: -350, near: 1, far: 1200 });
sun.shadow.bias = -0.0004;
scene.add(sun);
const fill = new THREE.DirectionalLight(0xc8e0e0, 1.8);
fill.position.set(-300, 250, 300);
scene.add(fill);
const floor = new THREE.Mesh(new THREE.PlaneGeometry(1800, 1800), new THREE.MeshStandardMaterial({ color: 0xe7ece8, roughness: 1 }));
floor.position.z = -2;
floor.receiveShadow = true;
scene.add(floor);
const moving = new THREE.Group();
const fixed = new THREE.Group();
const door = new THREE.Group();
const axis = new THREE.Vector3(...model.rotation_origin);
const doorAxis = new THREE.Vector3(...model.door_pivot);
moving.position.copy(axis);
door.position.copy(doorAxis);
scene.add(moving, fixed, door);
const meshes = [];
const parts = document.querySelector('#part');
for (const data of model.parts) {
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(data.vertices, 3));
  geometry.setIndex(data.triangles);
  geometry.computeVertexNormals();
  geometry.computeBoundingBox();
  const envelope = geometry.boundingBox.getSize(new THREE.Vector3());
  const phone = data.group.endsWith('phone');
  const glass = data.part.includes('2643');
  const isMoving = data.group.startsWith('moving');
  const isDoor = data.group.startsWith('door');
  if (isMoving) geometry.translate(-axis.x, -axis.y, -axis.z);
  if (isDoor) geometry.translate(-doorAxis.x, -doorAxis.y, -doorAxis.z);
  const material = new THREE.MeshStandardMaterial({
    color: new THREE.Color(...data.color), metalness: phone ? 0.15 : 0.55,
    roughness: phone ? 0.27 : 0.4, transparent: phone || glass, opacity: glass ? 0.13 : phone ? 0.82 : 1,
    depthWrite: !glass,
    side: THREE.DoubleSide,
  });
  const mesh = new THREE.Mesh(geometry, material);
  mesh.castShadow = true;
  mesh.receiveShadow = true;
  mesh.userData = { ...data, originalColor: material.color.clone(), phone, envelope };
  delete mesh.userData.vertices;
  delete mesh.userData.triangles;
  (isMoving ? moving : isDoor ? door : fixed).add(mesh);
  meshes.push(mesh);
  const option = document.createElement('option');
  option.value = data.name;
  option.textContent = data.name;
  parts.append(option);
}

let fixtureFocus = false;
function projection(kind = 'perspective') {
  const position = camera.position.clone();
  camera = kind === 'perspective'
    ? new THREE.PerspectiveCamera(35, 1, 1, 6000)
    : new THREE.OrthographicCamera(-500, 500, 500, -500, 1, 6000);
  camera.position.copy(position);
  camera.up.set(0, 0, 1);
  controls.object = camera;
  renderer.shadowMap.enabled = kind === 'perspective';
  resize();
}
function resetView() {
  fixtureFocus = false;
  projection();
  camera.position.set(1120, -1450, 990);
  controls.target.set(0, 0, 310);
  controls.update();
  if (meshes.length && document.querySelector('#angle-label')) {
    for (const mesh of meshes) mesh.visible = true;
  }
}
resetView();
function resize() {
  const { width, height } = viewport.getBoundingClientRect();
  renderer.setSize(width, height);
  if (camera.isOrthographicCamera) {
    camera.left = -orthoHeight * width / height / 2;
    camera.right = -camera.left;
    camera.top = orthoHeight / 2;
    camera.bottom = -camera.top;
  } else camera.aspect = width / height;
  camera.updateProjectionMatrix();
}
new ResizeObserver(resize).observe(viewport);
const angle = document.querySelector('#angle');
const explode = document.querySelector('#explode');
const play = document.querySelector('#play');
let playing = false;
let direction = -1;
let opening = 180;
let selected;
function setPlaying(value) {
  playing = value;
  play.textContent = playing ? 'Pause motion' : 'Play motion';
}
function updatePose() {
  moving.rotation.z = THREE.MathUtils.degToRad(180 - opening);
  door.rotation.z = THREE.MathUtils.degToRad(-Number(document.querySelector('#door').value));
  document.querySelector('#angle-label').textContent = `${opening.toFixed(1).replace('.0', '')}°`;
  const amount = Number(explode.value) / 100;
  for (const mesh of meshes) {
    const name = mesh.userData.name;
    let level = name.includes('mast') ? 2 : name.includes('cup') || name.includes('holder') ? 3 : name.startsWith('xy-') ? 1.5 : name.includes('plate') ? 1 : 0;
    if (mesh.userData.phone) level = 4;
    mesh.position.z = amount * level * 25;
    mesh.visible = mesh.userData.phone ? document.querySelector('#phone').checked : true;
    const group = mesh.userData.group;
    if (group.startsWith('moving')) mesh.visible &&= document.querySelector('#moving').checked;
    else if (group.startsWith('fixed') && name !== 'rotary-stage') mesh.visible &&= document.querySelector('#fixed').checked;
    if (group === 'guard' || group.startsWith('door')) mesh.visible &&= document.querySelector('#guard').checked;
    if (group.startsWith('cabinet') || group === 'electrical') mesh.visible &&= document.querySelector('#cabinet').checked;
    if (group === 'cabinet-cover') mesh.visible = false;
    if (fixtureFocus && ['frame', 'plates', 'guard', 'door', 'door-glass', 'cabinet', 'cabinet-cover', 'electrical'].includes(group)) mesh.visible = false;
  }
  document.querySelector('#explode-label').textContent = `${Math.round(amount * 100)}%`;
  document.querySelector('#view-state').textContent = amount ? 'Exploded view · motion paused' : 'Assembled · natural-closure concept';
}
function select(name) {
  if (selected) selected.material.color.copy(selected.userData.originalColor);
  selected = meshes.find(mesh => mesh.userData.name === name);
  parts.value = selected ? name : '';
  if (selected) {
    selected.material.color.set(0x2d9a9e);
    document.querySelector('#part-title').textContent = selected.userData.part;
    document.querySelector('#part-description').textContent = `${selected.userData.evidence}. ${selected.userData.name.replaceAll('-', ' ')}.`;
    const size = selected.userData.envelope;
    document.querySelector('#part-size').textContent = `CAD envelope X / Y / Z: ${size.toArray().map(v => v.toFixed(2)).join(' × ')} mm. Original assembled axes; not a tolerance specification.`;
  }
}
play.addEventListener('click', () => { explode.value = '0'; setPlaying(!playing); updatePose(); });
angle.addEventListener('input', () => { setPlaying(false); opening = Number(angle.value); updatePose(); });
explode.addEventListener('input', () => { setPlaying(false); updatePose(); });
document.querySelector('#reset').addEventListener('click', () => { resetView(); updatePose(); });
for (const id of ['phone', 'fixed', 'moving', 'guard', 'cabinet']) document.querySelector(`#${id}`).addEventListener('change', updatePose);
document.querySelector('#door').addEventListener('input', updatePose);
document.querySelector('#focus').addEventListener('click', () => {
  fixtureFocus = true;
  projection();
  camera.position.set(500, -590, 430); controls.target.set(50, 10, 185); controls.update(); updatePose();
});
for (const button of document.querySelectorAll('[data-view]')) button.addEventListener('click', () => {
  const view = button.dataset.view;
  projection('orthographic');
  orthoHeight = fixtureFocus ? 440 : 980;
  const target = fixtureFocus ? new THREE.Vector3(65, 10, 185) : new THREE.Vector3(0, 0, 310);
  const offset = view === 'front' ? [0, -1600, 0] : view === 'side' ? [1600, 0, 0] : [0, 0, 1600];
  camera.position.copy(target).add(new THREE.Vector3(...offset));
  if (view === 'top') camera.up.set(0, 1, 0);
  controls.target.copy(target);
  controls.update(); resize();
});
document.querySelector('#closure').addEventListener('click', () => {
  document.querySelector('#focus').click();
  explode.value = '0'; opening = 0; angle.value = '0'; setPlaying(false); updatePose();
});
parts.addEventListener('change', () => select(parts.value));
const raycaster = new THREE.Raycaster();
let down;
renderer.domElement.addEventListener('pointerdown', event => { down = [event.clientX, event.clientY]; });
renderer.domElement.addEventListener('pointerup', event => {
  if (!down || Math.hypot(event.clientX - down[0], event.clientY - down[1]) > 5) return;
  const rect = renderer.domElement.getBoundingClientRect();
  raycaster.setFromCamera(new THREE.Vector2((event.clientX - rect.left) / rect.width * 2 - 1, -(event.clientY - rect.top) / rect.height * 2 + 1), camera);
  const hit = raycaster.intersectObjects(meshes).find(item => item.object.visible);
  if (hit) select(hit.object.userData.name);
});
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
let previous = performance.now();
renderer.setAnimationLoop(now => {
  const elapsed = Math.min((now - previous) / 1000, 0.1);
  previous = now;
  if (playing) {
    opening += elapsed * 18 * direction;
    if (opening <= 0 || opening >= 180) { opening = Math.max(0, Math.min(180, opening)); direction *= -1; }
    angle.value = String(opening);
    updatePose();
  }
  controls.enableDamping = !reducedMotion;
  controls.update();
  renderer.render(scene, camera);
});
updatePose();
document.querySelector('#loading').classList.add('hide');
window.foldatronViewer = {
  partCount: meshes.length,
  get openingDegrees() { return opening; },
  setOpening(value) { setPlaying(false); opening = Math.max(0, Math.min(180, value)); angle.value = String(opening); updatePose(); },
};
