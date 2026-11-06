import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { createBench } from './model.js';
import { parts, steps } from './data.js';

const $ = (selector) => document.querySelector(selector);
const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const state = {angle:110,explode:0,playing:false,direction:-1,mode:'explore',step:0,selected:null,guard:true};
let renderer;
try { renderer = new THREE.WebGLRenderer({antialias:true,alpha:true}); }
catch (error) {
  $('#loading').textContent='3D requires WebGL 2. Open this file in a current browser with graphics acceleration enabled.';
  console.error(error);
}
if (renderer) initialize();
function initialize() {
  const viewport = $('#viewport');
  renderer.setPixelRatio(Math.min(window.devicePixelRatio,2));
  renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.25;
  renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFShadowMap;
  viewport.appendChild(renderer.domElement);$('#loading').remove();
  const scene = new THREE.Scene();
  const pmrem = new THREE.PMREMGenerator(renderer);
  const room = new RoomEnvironment();
  const env = pmrem.fromScene(room,.04);scene.environment=env.texture;scene.environmentIntensity=.8;
  room.dispose();pmrem.dispose();
  const camera=new THREE.PerspectiveCamera(37,1,1,7000);
  const controls=new OrbitControls(camera,renderer.domElement);
  controls.enableDamping=!reducedMotion;controls.dampingFactor=.075;
  controls.minDistance=220;controls.maxDistance=2800;controls.maxPolarAngle=Math.PI*.49;
  controls.enablePan=true;
  const hemi=new THREE.HemisphereLight(0xd5e7f0,0x1a232d,2);scene.add(hemi);
  const key=new THREE.DirectionalLight(0xfff3e4,3.5);key.position.set(-350,850,500);key.castShadow=true;
  key.shadow.mapSize.set(2048,2048);Object.assign(key.shadow.camera,{left:-1100,right:1100,top:1000,bottom:-1000,near:10,far:2500});key.shadow.bias=-.0005;key.shadow.normalBias=1;
  scene.add(key);
  const rim=new THREE.DirectionalLight(0x8ccbe5,2);rim.position.set(400,500,-500);scene.add(rim);
  const floor=new THREE.Mesh(new THREE.PlaneGeometry(5000,5000),new THREE.ShadowMaterial({opacity:.3}));floor.rotation.x=-Math.PI/2;floor.position.y=-25;floor.receiveShadow=true;scene.add(floor);
  const bench=createBench();scene.add(bench.root);
  const grid=new THREE.GridHelper(1600,32,0x46535d,0x2b363e);grid.position.set(120,-26,0);grid.material.transparent=true;grid.material.opacity=.28;scene.add(grid);
  const selection=new THREE.Box3Helper(new THREE.Box3(),0x8ccbe5);selection.visible=false;selection.material.transparent=true;selection.material.opacity=.45;scene.add(selection);
  const cameraTarget=new THREE.Vector3();const lookTarget=new THREE.Vector3();let cameraMoving=false;
  let currentView="overview", lastViewportWidth=0;

  function view(name,immediate=false) {
    currentView=name;
    if(name==='mechanism'&&state.mode==='explore'){state.guard=false;$('#guard').checked=false;visibility();}
    const mobile=viewport.clientWidth<600;
    const views={
      overview:{pos:mobile?[1250,950,1550]:[950,680,1035],look:[145,140,0]},
      mechanism:{pos:mobile?[-450,490,650]:[-390,380,530],look:[0,135,5]},
      top:{pos:mobile?[150,1900,2]:[150,1450,2],look:[150,70,0]},
    };
    const config=views[name];cameraTarget.set(...config.pos);lookTarget.set(...config.look);
    if(mobile)cameraTarget.sub(lookTarget).multiplyScalar(1.5).add(lookTarget);
    if(state.explode>0&&name==='overview'){cameraTarget.multiplyScalar(1.4);lookTarget.y=280;}
    cameraMoving=true;
    if(immediate||reducedMotion){camera.position.copy(cameraTarget);controls.target.copy(lookTarget);cameraMoving=false;controls.update();}
    document.querySelectorAll('[data-view]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===name)));
  }
  controls.addEventListener('start',()=>{cameraMoving=false;});
  function resize(){const width=viewport.clientWidth,height=viewport.clientHeight;renderer.setSize(width,height);camera.aspect=width/height;camera.updateProjectionMatrix();if(width!==lastViewportWidth){lastViewportWidth=width;view(currentView,true);}}
  new ResizeObserver(resize).observe(viewport);resize();view('overview',true);
  for(const [id,part] of Object.entries(parts)) {
    const button=document.createElement('button');button.className='part';button.dataset.part=id;button.setAttribute('aria-pressed','false');
    const n=Object.keys(parts).indexOf(id)+1;
    button.innerHTML=`<span class="number">0${n}</span><span class="name">${part.name}</span><span class="arrow">↗</span>`;
    button.addEventListener('click',()=>select(id));$('#parts').appendChild(button);
  }
  function select(id) {
    state.selected=id;const p=parts[id];
    $('#part-id').textContent=p.id;$('#part-title').textContent=p.name;$('#part-description').textContent=p.description;
    $('#specs').replaceChildren(...p.specs.map(([name,value])=>{const row=document.createElement('div');const term=document.createElement('dt');const detail=document.createElement('dd');term.textContent=name;detail.textContent=value;row.append(term,detail);return row;}));
    $('#engineering-note').textContent=p.note;$('#evidence').textContent=p.evidence;
    document.querySelectorAll('[data-part]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.part===id)));
    $('#scene-title').textContent=p.name;
  }
  const raycaster=new THREE.Raycaster(),pointer=new THREE.Vector2();let down=null;
  renderer.domElement.addEventListener('pointerdown',e=>{down=[e.clientX,e.clientY];});
  renderer.domElement.addEventListener('pointerup',e=>{
    if(!down||Math.hypot(e.clientX-down[0],e.clientY-down[1])>5)return;
    const rect=renderer.domElement.getBoundingClientRect();pointer.set((e.clientX-rect.left)/rect.width*2-1,-(e.clientY-rect.top)/rect.height*2+1);raycaster.setFromCamera(pointer,camera);
    const hits=raycaster.intersectObjects(Object.values(bench.groups).filter(g=>g.visible),true);
    // Transparent panels should not block picking the mechanism behind them.
    const hit=hits.find(h=>!h.object.material.transparent);
    if(hit){let object=hit.object;while(object&&!object.userData.part)object=object.parent;if(object)select(object.userData.part);}
  });
  function stop(){state.playing=false;$('#play').textContent='▶';$('#play').setAttribute('aria-label','Play folding animation');$('#motion-state').textContent='Paused · manual angle';}
  function updateAngle(){ $('#angle').value=String(Math.round(state.angle));$('#angle-value').textContent=`${Math.round(state.angle)}°`; }
  $('#play').addEventListener('click',()=>{if(state.playing){stop();return;}state.playing=true;$('#play').textContent='Ⅱ';$('#play').setAttribute('aria-label','Pause folding animation');$('#motion-state').textContent='Visual cycle · 3× time scale';});
  $('#angle').addEventListener('input',e=>{stop();state.angle=Number(e.target.value);updateAngle();});
  $('#explode').addEventListener('input',e=>{state.explode=Number(e.target.value)/100;$('#explode-value').textContent=`${e.target.value}%`;stop();view('overview');});
  $('#guard').addEventListener('change',e=>{state.guard=e.target.checked;visibility();});
  document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>view(b.dataset.view)));
  function visibility(){for(const [id,group]of Object.entries(bench.groups)){group.visible=state.mode==='explore'?(id!=='guard'||state.guard):steps[state.step].visible.includes(id);}}
  function mode(name){state.mode=name;stop();state.explode=0;$('#explode').value='0';$('#explode-value').textContent='0%';
    document.querySelectorAll('[data-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.mode===name)));
    $('#explore-panel').hidden=name!=='explore';$('#build-panel').hidden=name!=='build';
    if(name==='build'){showStep();view('overview');}else visibility();
  }
  function showStep(){const step=steps[state.step];$('#step-count').textContent=`0${state.step+1} / 08`;$('#step-title').textContent=step.title;$('#step-description').textContent=step.text;
    $('#previous').disabled=state.step===0;$('#next').disabled=state.step===steps.length-1;
    $('#step-link').textContent=`Manual operations ${step.steps} ↗`;
    $('#step-link').href='https://github.com/nkocode/test-equipment-iphone-duo-foldatron/blob/main/docs/assembly/README.md#'+step.anchor;
    $('#step-progress').innerHTML=steps.map((_,i)=>`<i class="${i<=state.step?'active':''}"></i>`).join('');
    visibility();select(step.part);$('#scene-title').textContent=`0${state.step+1} / ${step.title}`;
  }
  document.querySelectorAll('[data-mode]').forEach(b=>b.addEventListener('click',()=>mode(b.dataset.mode)));
  $('#previous').addEventListener('click',()=>{state.step=Math.max(0,state.step-1);showStep();});
  $('#next').addEventListener('click',()=>{state.step=Math.min(steps.length-1,state.step+1);showStep();});
  const originalInspector=$('.inspector').innerHTML;
  $('#reset').addEventListener('click',()=>{stop();state.angle=110;state.step=0;state.selected=null;state.guard=true;$('#guard').checked=true;mode('explore');updateAngle();$('.inspector').innerHTML=originalInspector;document.querySelectorAll('[data-part]').forEach(b=>b.setAttribute('aria-pressed','false'));$('#scene-title').textContent='Complete bench';view('overview');});
  let previousTime=performance.now(), dwell=0;
  function animate(time){
    const dt=Math.min((time-previousTime)/1000,.05);previousTime=time;
    if(document.hidden)return;
    if(state.playing){
      if(dwell>0)dwell-=dt;
      else{state.angle+=state.direction*45*dt;if(state.angle<=5||state.angle>=175){state.angle=THREE.MathUtils.clamp(state.angle,5,175);state.direction*=-1;dwell=1/3;}updateAngle();}
    }
    bench.moving.rotation.z=THREE.MathUtils.degToRad(180-state.angle);
    const smoothing=reducedMotion?1:1-Math.exp(-dt*7);
    for(const [id,group]of Object.entries(bench.groups)){
      const offset=bench.offsets[id];group.position.lerp(new THREE.Vector3(...offset).multiplyScalar(state.explode),smoothing);
    }
    if(cameraMoving){camera.position.lerp(cameraTarget,smoothing);controls.target.lerp(lookTarget,smoothing);if(camera.position.distanceTo(cameraTarget)<.3)cameraMoving=false;}
    if(state.selected&&bench.groups[state.selected].visible){selection.box.setFromObject(bench.groups[state.selected]);selection.visible=true;}else selection.visible=false;
    controls.update();renderer.render(scene,camera);
  }
  renderer.setAnimationLoop(animate);
  renderer.domElement.addEventListener('webglcontextlost',event=>{event.preventDefault();stop();const message=document.createElement('p');message.id='loading';message.textContent='Graphics context interrupted. Reload the viewer to resume.';viewport.appendChild(message);});
}
