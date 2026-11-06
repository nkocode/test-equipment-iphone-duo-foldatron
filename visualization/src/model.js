import * as THREE from 'three';
import {cad,groups} from './data.js';

export function createBench() {
  const root=new THREE.Group(), assemblies={}, items=[];
  for(const [id,config] of Object.entries(groups)) {
    const group=new THREE.Group();root.add(group);assemblies[id]=group;
    group.userData.offset=new THREE.Vector3(...config.offset);
  }
  for(const record of cad.instances) {
    const geometry=new THREE.BufferGeometry();
    geometry.setAttribute('position',new THREE.Float32BufferAttribute(record.positions,3));
    geometry.setIndex(record.indices);geometry.computeVertexNormals();
    const pivoted=record.moving||record.rotor;
    if(pivoted) geometry.translate(0,-140,0);
    const info=cad.parts[record.part];
    const polymer=/POM|polycarbonate/.test(info.material)||record.part==='DUT';
    const transparent=record.opacity<1||record.part==='DUT';
    let color=new THREE.Color(...record.color);
    if(info.material.includes('aluminum')) color.set(record.part==='B101'?0xa8bbc3:0x72909f);
    const material=new THREE.MeshStandardMaterial({
      color,metalness:polymer?0:.65,roughness:polymer?.48:.35,
      transparent,opacity:record.part==='DUT'?.32:record.opacity,
      depthWrite:!transparent,side:transparent?THREE.DoubleSide:THREE.FrontSide,
      polygonOffset:true,polygonOffsetFactor:1,polygonOffsetUnits:1,
    });
    const mesh=new THREE.Mesh(geometry,material);
    mesh.castShadow=!transparent;mesh.receiveShadow=!transparent;
    const edges=new THREE.LineSegments(new THREE.EdgesGeometry(geometry,24),
      new THREE.LineBasicMaterial({color:transparent?0x91bfca:0x243641,
        transparent:true,opacity:transparent?.3:.26}));
    mesh.add(edges);
    const holder=new THREE.Group();holder.position.y=pivoted?140:0;
    holder.add(mesh);assemblies[record.group].add(holder);
    mesh.userData.record=record;holder.userData.record=record;
    items.push({record,holder,mesh,edges});
  }
  const datum=new THREE.Group();root.add(datum);
  const line=(points,color=0x74c6cc,dashed=false)=>{
    const geometry=new THREE.BufferGeometry().setFromPoints(points.map(p=>new THREE.Vector3(...p)));
    const material=dashed?new THREE.LineDashedMaterial({color,dashSize:7,gapSize:5}):new THREE.LineBasicMaterial({color});
    const l=new THREE.Line(geometry,material);l.computeLineDistances();datum.add(l);return l;
  };
  line([[0,140,-240],[0,140,265]],0x74c6cc,true);
  const arc=[];for(let a=5;a<=175;a+=2){const t=(180-a)*Math.PI/180;arc.push([170*Math.cos(t),140+170*Math.sin(t),0]);}
  line(arc,0x74c6cc,true);
  function label(text,position,width=95) {
    const canvas=document.createElement('canvas');canvas.width=512;canvas.height=100;
    const ctx=canvas.getContext('2d');ctx.fillStyle='#12262be8';ctx.fillRect(0,0,512,100);
    ctx.font='500 38px Arial';ctx.textAlign='center';ctx.fillStyle='#b0e0df';ctx.fillText(text,256,63);
    const texture=new THREE.CanvasTexture(canvas);texture.colorSpace=THREE.SRGBColorSpace;
    const sprite=new THREE.Sprite(new THREE.SpriteMaterial({map:texture,depthTest:false,transparent:true}));
    sprite.position.set(...position);sprite.scale.set(width,width*100/512,1);datum.add(sprite);
  }
  line([[-175,0,100],[-175,140,100]]);line([[-183,0,100],[-167,0,100]]);line([[-183,140,100],[-167,140,100]]);
  label('140 mm axis',[-205,72,100],90);
  label('5°–175° study',[0,325,0],110);
  line([[-330.2,-33.4,330],[330.2,-33.4,330]]);
  label('660.4 mm frame',[0,-33.4,350],150);
  const bounds=new THREE.Box3Helper(new THREE.Box3(),0x9ae0d9);bounds.visible=false;root.add(bounds);
  let selected=null;
  return {root,items,assemblies,datum,
    select(name){selected=name;for(const item of items){item.mesh.material.emissive.set(item.record.name===name?0x1e7779:0);item.mesh.material.emissiveIntensity=.45;}},
    update(state,dt=1) {
      const ease=state.reduced?1:1-Math.exp(-dt*9);
      for(const group of Object.values(assemblies)) group.position.lerp(group.userData.offset.clone().multiplyScalar(state.explode),ease);
      for(const item of items) {
        const r=item.record;
        const visibleByStep=state.mode!=='build'||state.step<2||r.stage<=state.step+1;
        const mechanism=state.view==='mechanism'||state.view==='endpoints';
        const clipped=mechanism&&(r.group==='frame'&&r.stage===5||r.group==='guard'||r.group==='control');
        item.holder.visible=visibleByStep&&!clipped&&
          (state.panels||r.opacity===1)&&(state.specimen||r.part!=='DUT')&&
          (!state.isolate||r.group===state.isolate);
        if(r.moving||r.rotor) item.holder.rotation.z=(180-state.angle)*Math.PI/180;
        item.mesh.position.x=r.float?state.float:0;
        // Front panel and its key withdraw together; the switch stays fixed.
        const front=r.name==='door'||r.name.startsWith('guard_key');
        item.holder.position.z=front?(state.guardOpen?100:0):0;
      }
      datum.visible=state.dimensions&&state.mode!=='build'&&state.explode===0&&!state.isolate;
      const chosen=items.find(i=>i.record.name===selected);
      bounds.visible=!!chosen?.holder.visible;
      if(bounds.visible) {root.updateMatrixWorld(true);bounds.box.setFromObject(chosen.holder);}
    },
  };
}
