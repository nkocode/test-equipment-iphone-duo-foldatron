import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';

// Display units are mm. World axes: x = design X, y = design Z,
// z = -design Y (operator/front is +z). Envelopes, not fabrication CAD.
export function createBench() {
  const root = new THREE.Group();
  const groups = {};
  const materials = {
    aluminum: new THREE.MeshStandardMaterial({ color: 0xb5c1c8, metalness: .82, roughness: .32 }),
    dark: new THREE.MeshStandardMaterial({ color: 0x273238, metalness: .65, roughness: .34 }),
    steel: new THREE.MeshStandardMaterial({ color: 0xe1e8ea, metalness: .95, roughness: .22 }),
    rubber: new THREE.MeshStandardMaterial({ color: 0x10171c, roughness: .9 }),
    blue: new THREE.MeshStandardMaterial({ color: 0x3488b2, metalness: .55, roughness: .32 }),
    screen: new THREE.MeshStandardMaterial({ color: 0x224c64, metalness: .4, roughness: .15 }),
    pcb: new THREE.MeshStandardMaterial({ color: 0x245e4d, roughness: .5 }),
    gold: new THREE.MeshStandardMaterial({ color: 0xb8a265, metalness: .7, roughness: .4 }),
    glass: new THREE.MeshPhysicalMaterial({ color: 0xa4cee0, transparent: true, opacity: .055, roughness: .2, metalness: .15, depthWrite: false, side: THREE.DoubleSide }),
    red: new THREE.MeshStandardMaterial({ color: 0xb93932, roughness: .4 }),
    yellow: new THREE.MeshStandardMaterial({ color: 0xe2c568, roughness: .55 }),
  };
  const offsets = { base: [0,-25,0], supports:[0,35,90], drive:[0,80,220], cradle:[0,180,0], guard:[-80,320,-50], control:[240,30,0] };
  for (const id of Object.keys(offsets)) {
    const group = new THREE.Group(); group.userData.part = id;
    groups[id] = group; root.add(group);
  }
  function mesh(parent, geometry, material, position) {
    const m = new THREE.Mesh(geometry, materials[material] || material);
    m.position.set(...position); m.castShadow = material !== 'glass'; m.receiveShadow = true;
    parent.add(m); return m;
  }
  function box(parent, size, pos, material='aluminum', radius=1) {
    return mesh(parent, radius ? new RoundedBoxGeometry(...size, 2, Math.min(radius, ...size.map(v=>v/3))) : new THREE.BoxGeometry(...size), material, pos);
  }
  function cylinder(parent, radius, length, pos, material='steel', axis='y') {
    const m=mesh(parent,new THREE.CylinderGeometry(radius,radius,length,32),material,pos);
    if(axis==='z') m.rotation.x=Math.PI/2;
    if(axis==='x') m.rotation.z=Math.PI/2;
    return m;
  }
  function screw(parent, pos, axis='y', size=3) {
    cylinder(parent,size,2.5,pos,'steel',axis);
    const socket=cylinder(parent,size*.45,2.6,pos,'dark',axis);
    return socket;
  }
  function cable(parent, points, material='rubber', radius=1.8) {
    const path = new THREE.CatmullRomCurve3(points.map(p=>new THREE.Vector3(...p)));
    return mesh(parent,new THREE.TubeGeometry(path,40,radius,8,false),material,[0,0,0]);
  }
  function decal(parent, text, width, pos, color='#c0d6df', background='#263239') {
    const canvas=document.createElement('canvas'); canvas.width=512;canvas.height=128;
    const ctx=canvas.getContext('2d');ctx.fillStyle=background;ctx.fillRect(0,0,512,128);
    ctx.fillStyle=color;ctx.font='bold 48px Arial';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(text,256,64);
    const texture=new THREE.CanvasTexture(canvas);texture.colorSpace=THREE.SRGBColorSpace;
    const m=mesh(parent,new THREE.PlaneGeometry(width,width/4),new THREE.MeshStandardMaterial({map:texture,roughness:.7}),pos);
    return m;
  }
  const base=groups.base;
  box(base,[500,8,400],[0,-4,0]);
  for(let x=-175;x<=175;x+=25) for(let z=-125;z<=125;z+=25){
    cylinder(base,3.3,.3,[x,.2,z],'dark');
  }
  for(const x of [-230,230]) for(const z of [-180,180]) {
    cylinder(base,14,15,[x,-16,z],'rubber');screw(base,[x,1,z]);
  }
  decal(base,'foldatron  /  REV A',105,[-150,-3,200.4]);
  // Tower plate envelopes with separate 6 mm stub shafts. Central phone
  // volume z=-70..70 deliberately has no shaft passing through it.
  const supports=groups.supports;
  for(const z of [-95,95]) {
    box(supports,[100,180,8],[0,90,z],'aluminum');
    box(supports,[110,8,48],[0,4,z],'dark');
    for(const x of [-38,38]) {screw(supports,[x,9,z+12]);screw(supports,[x,9,z-12]);}
    box(supports,[42,32,18],[0,140,z+Math.sign(z)*12],'dark',3);
    cylinder(supports,12,20,[0,140,z+Math.sign(z)*12],'steel','z');
    cylinder(supports,3,z>0?64:50,[0,140,z>0?116:-105],'steel','z');
    for(const x of [-16,16]) screw(supports,[x,140,z+Math.sign(z)*23],'z',2.5);
    for(const y of [38,70,102]) box(supports,[42,5,1],[0,y,z+4.6],'dark');
  }
  // Fixed backing plate, shoes and specimen half.
  const cradle=groups.cradle;
  for(const z of [-50,50])box(cradle,[12,124,16],[-70,62,z],'dark');
  box(cradle,[100,4,135],[-47,131,0],'aluminum');
  const moving=new THREE.Group();moving.position.y=140;cradle.add(moving);
  box(moving,[100,4,135],[47,-9,0],'aluminum');
  for(const z of [-45,45]) {
    box(moving,[100,8,7],[50,-17,z],'steel');
    box(moving,[25,10,17],[52,-15,z],'blue');
    for(const x of [8,92]) screw(moving,[x,-12,z], 'y',2);
  }
  for(const z of [-95,95]) {
    box(moving,[125,6,25],[55,-10,z],'aluminum');
    cylinder(moving,12,9,[0,0,z],'blue','z');
    for(const x of [20,110])screw(moving,[x,-6,z]);
  }
  box(moving,[25,6,190],[115,-10,0],'aluminum');
  function phone(parent,x,y) {
    box(parent,[80,5.2,117.8],[x,y,0],'dark',2.3);
    box(parent,[77,0.5,114.8],[x,y+2.8,0],'screen',.2);
    // Subtle screen bands indicate a specimen, not fabricated sensor readings.
    for(let k=0;k<4;k++)box(parent,[58-k*7,.2,1],[x,y+3.1,-32+k*8],'blue',0);
    for(const z of [-57,57]) for(const px of [x-27,x+27]) {
      box(parent,[20,8,15],[px,y-3,z],'rubber');
      screw(parent,[px,y+1.5,z],'y',2);
    }
  }
  phone(cradle,-42,137.4);phone(moving,42,-2.6);
  // Actuator and coaxial clutch; exterior geometry is illustrative.
  const drive=groups.drive;
  box(drive,[74,7,64],[0,3.5,174],'dark');
  box(drive,[8,124,40],[-23,65,181],'aluminum');
  box(drive,[34,28.5,46.5],[0,140,185],'dark',3);
  for(const x of [-13,13])for(const y of [130,150])screw(drive,[x,y,209],'z',1.8);
  box(drive,[32,18,1],[0,140,209.3],'rubber');
  decal(drive,'XM430',25,[0,140,210]);
  cylinder(drive,10,4,[0,140,160],'steel','z');
  cylinder(drive,9.525,31.75,[0,140,142],'aluminum','z');
  for(const z of [129,142,155])cylinder(drive,10.3,2,[0,140,z],'dark','z');
  cable(drive,[[15,132,207],[28,100,210],[40,35,200],[140,14,170],[220,15,150]],'rubber',2.3);
  for(const z of [-85,85]){
    box(drive,[18,10,9],[33,120,z],'rubber');
    box(drive,[24,2,3],[25,127,z],'steel');
    cable(drive,[[33,118,z],[50,80,z],[60,12,z],[225,12,70]],'blue',1);
  }
  // Guard frame is nominal: panel interfaces/outriggers remain design hold H3.
  const guard=groups.guard;
  function extrusion(size,pos) {
    box(guard,size,pos,'aluminum',.4);
    const axis=size.indexOf(Math.max(...size));
    const slot=[...size];slot[axis]-=8;
    if(axis===1){slot[0]=3;slot[2]=.5;box(guard,slot,[pos[0],pos[1],pos[2]+10.1],'dark',0);}
    else{slot[1]=3;slot[axis===0?2:0]=20.2;box(guard,slot,pos,'dark',0);}
  }
  for(const x of [-290,290])for(const z of [-240,240])extrusion([20,400,20],[x,200,z]);
  for(const y of [10,390]){
    for(const z of [-240,240])extrusion([560,20,20],[0,y,z]);
    for(const x of [-290,290])extrusion([20,20,460],[x,y,0]);
  }
  for(const x of [-289,289])box(guard,[4,360,460],[x,200,0],'glass',0);
  for(const z of [-239,239])box(guard,[560,360,4],[0,200,z],'glass',0);
  box(guard,[560,4,460],[0,389,0],'glass',0);
  for(const y of [100,300])box(guard,[22,30,15],[-278,y,252],'dark');
  box(guard,[12,66,12],[268,200,255],'dark');
  for(const y of [173,227])box(guard,[12,10,20],[268,y,249],'dark');
  box(guard,[25,44,25],[278,280,250],'dark');
  // Service cabinet to the right, exterior panels removed to expose controls.
  const control=groups.control;
  box(control,[300,8,250],[475,5,0],'aluminum');
  box(control,[300,150,5],[475,75,-122.5],'dark');
  for(const x of [327.5,622.5])box(control,[5,150,250],[x,75,0],'dark');
  box(control,[300,42,5],[475,21,122.5],'dark');
  for(const z of [-56,55])box(control,[260,4,12],[475,15,z],'steel');
  box(control,[85,2,56],[393,25,40],'pcb');
  box(control,[24,13,24],[385,33,39],'steel');
  for(let n=0;n<7;n++)box(control,[22,8,1],[385,39,29+n*3],'aluminum',0);
  for(const x of [415,430])box(control,[14,16,15],[x,34,55],'steel');
  box(control,[45,6,5],[385,29,16],'rubber');
  for(let n=0;n<20;n++)cylinder(control,.6,7,[365+n*2,31,16],'gold');
  box(control,[45,30,95],[477,31,-34],'yellow');
  box(control,[39,12,75],[477,50,-34],'dark');
  for(const z of [-72,3])box(control,[40,8,12],[477,54,z],'blue');
  for(let n=0;n<6;n++){
    box(control,[8,25,28],[526+n*13,28,-45],'aluminum');
    screw(control,[526+n*13,42,-45],'y',2);
  }
  box(control,[38,8,20],[456,25,60],'dark');
  box(control,[46,3,30],[525,22,55],'pcb');
  for(const x of [340,610])for(const z of [-107,106])screw(control,[x,10,z]);
  cylinder(control,21,5,[560,52,125],'yellow','z');
  cylinder(control,16,15,[560,52,137],'red','z');
  cylinder(control,9,8,[600,45,130],'blue','z');
  decal(control,'CONTROL / 24 V',110,[421,23,126]);
  cable(control,[[456,26,60],[442,45,70],[410,45,70],[410,33,60]],'rubber',2);
  cable(control,[[475,50,3],[500,65,15],[543,50,-40]],'blue',1.8);
  cable(control,[[330,20,40],[300,12,90],[260,12,150],[220,15,150]],'rubber',3);
  // Cabinet wiring is a routing illustration, never a terminal schematic.
  return { root, groups, moving, offsets };
}
