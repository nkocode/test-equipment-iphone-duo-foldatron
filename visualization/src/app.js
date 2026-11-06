import * as THREE from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';
import {createBench} from './model.js';
import {MotionStudy} from './simulation.js';
import {cad,groups,repo,phases} from './data.js';

const $=s=>document.querySelector(s);
const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
const state={mode:'motion',view:'mechanism',step:0,angle:110,explode:0,
  panels:true,specimen:true,dimensions:true,float:0,isolate:null,
  selected:null,guardOpen:false,reduced};
const simulation=new MotionStudy();simulation.scrub(110);
let renderer;
try {renderer=new THREE.WebGLRenderer({antialias:true,alpha:true});}
catch(error){$('#loading').textContent='WebGL 2 is required. Open this file in a browser with graphics acceleration.';console.error(error);}
if(renderer) initialize();

function initialize() {
  const viewport=$('#viewport');
  renderer.setPixelRatio(Math.min(devicePixelRatio,2));
  renderer.toneMapping=THREE.ACESFilmicToneMapping;renderer.toneMappingExposure=1.0;
  renderer.shadowMap.enabled=true;renderer.shadowMap.type=THREE.PCFShadowMap;
  viewport.appendChild(renderer.domElement);$('#loading').remove();
  const scene=new THREE.Scene();
  const pmrem=new THREE.PMREMGenerator(renderer), room=new RoomEnvironment();
  const environment=pmrem.fromScene(room,.04);scene.environment=environment.texture;scene.environmentIntensity=.65;
  room.dispose();pmrem.dispose();
  const camera=new THREE.PerspectiveCamera(36,1,1,8000);
  const controls=new OrbitControls(camera,renderer.domElement);
  controls.enableDamping=!reduced;controls.dampingFactor=.08;
  controls.minDistance=50;controls.maxDistance=4000;
  controls.maxPolarAngle=Math.PI*.52;
  scene.add(new THREE.HemisphereLight(0xe5f3f5,0x53656b,1.0));
  const key=new THREE.DirectionalLight(0xfff5e6,2.1);key.position.set(-350,850,600);key.castShadow=true;
  key.shadow.mapSize.set(2048,2048);Object.assign(key.shadow.camera,{left:-900,right:1000,top:1000,bottom:-900,near:10,far:2300});
  key.shadow.normalBias=.4;key.shadow.bias=-.0001;scene.add(key);
  const rim=new THREE.DirectionalLight(0x9de0df,1.5);rim.position.set(700,450,-500);scene.add(rim);
  const floor=new THREE.Mesh(new THREE.PlaneGeometry(5000,5000),new THREE.ShadowMaterial({opacity:.28}));
  floor.rotation.x=-Math.PI/2;floor.position.y=-36.5;floor.receiveShadow=true;scene.add(floor);
  const grid=new THREE.GridHelper(1600,32,0x53696e,0x35494e);grid.position.y=-36.4;
  grid.material.transparent=true;grid.material.opacity=.23;scene.add(grid);
  const bench=createBench();scene.add(bench.root);
  const targetPosition=new THREE.Vector3(),targetLook=new THREE.Vector3();let cameraMoving=false;
  const presets={
    overview:{pos:[1020,810,1160],look:[130,195,0],title:'Complete 1010 bench'},
    mechanism:{pos:[-560,490,780],look:[0,125,0],title:'Folding mechanism'},
    endpoints:{pos:[250,240,-440],look:[0,120,-170],title:'Output-side endpoint sensing'},
    guard:{pos:[-570,480,620],look:[-275,300,250],title:'Guard interlock & key mount'},
    top:{pos:[100,1600,1],look:[100,100,0],title:'Bench plan view'},
  };
  let viewportWidth=0;
  function setView(name,immediate=false) {
    state.view=name;const preset=presets[name];
    targetLook.set(...preset.look);targetPosition.set(...preset.pos);
    const aspect=viewport.clientWidth/Math.max(1,viewport.clientHeight);
    if(aspect<1)targetPosition.sub(targetLook).multiplyScalar(Math.min(1.8,1/aspect)).add(targetLook);
    if(state.explode>0)targetPosition.sub(targetLook).multiplyScalar(1.35).add(targetLook);
    cameraMoving=true;
    if(immediate||reduced){camera.position.copy(targetPosition);controls.target.copy(targetLook);cameraMoving=false;controls.update();}
    document.querySelectorAll('[data-view]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===name)));
    $('#scene-title').textContent=state.isolate?groups[state.isolate].name:preset.title;
    $('#scene-subtitle').textContent=state.isolate?'Isolated assembly · drawing-derived geometry':name==='mechanism'||name==='endpoints'?'Cutaway view · frame top and panels hidden':'122 CAD instances · dimensions in millimetres';
    bench.update(state,1);
  }
  function resize(){
    const w=viewport.clientWidth,h=viewport.clientHeight;
    renderer.setSize(w,h);camera.aspect=w/h;camera.updateProjectionMatrix();
    if(w!==viewportWidth){viewportWidth=w;setView(state.view,true);}
  }
  new ResizeObserver(resize).observe(viewport);resize();
  controls.addEventListener('start',()=>{cameraMoving=false;});
  document.querySelectorAll('[data-view]').forEach(b=>b.addEventListener('click',()=>{state.isolate=null;$('#isolate').textContent='Isolate assembly';setView(b.dataset.view);}));

  function focus(objects) {
    bench.update(state,1);scene.updateMatrixWorld(true);
    const bounds=new THREE.Box3();for(const object of objects) bounds.expandByObject(object);
    if(bounds.isEmpty())return;
    bounds.getCenter(targetLook);const size=bounds.getSize(new THREE.Vector3());
    const distance=Math.max(90,size.length()/(2*Math.tan(camera.fov*Math.PI/360)))*1.25/Math.min(1,camera.aspect);
    targetPosition.copy(camera.position).sub(controls.target).normalize().multiplyScalar(distance).add(targetLook);
    cameraMoving=true;
    if(reduced){camera.position.copy(targetPosition);controls.target.copy(targetLook);cameraMoving=false;}
  }
  function select(name) {
    const item=bench.items.find(i=>i.record.name===name);if(!item)return;
    state.selected=name;bench.select(name);const r=item.record,p=cad.parts[r.part];
    $('#part-id').textContent=r.part;$('#part-title').textContent=p.title;
    $('#part-description').textContent=p.description;
    const rows=[['Instance',r.name.replaceAll('_',' ')],['Material',p.material||'Vendor interface envelope'],['Assembly',groups[r.group].name],['Release',p.status],['Evidence',p.source]];
    $('#specs').replaceChildren(...rows.map(([term,value])=>{
      const row=document.createElement('div'),dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=term;dd.textContent=value;row.append(dt,dd);return row;
    }));
    $('#part-note').textContent=p.notes.length?p.notes.join(' '):'Commercial geometry is an interface envelope. The reference specimen is not measured Apple geometry.';
    const custom=r.part.startsWith('B');
    $('#drawing-link').href=custom?`${repo}/blob/main/hardware/rev-b/cad/${r.part}.step`:`${repo}/blob/main/hardware/rev-b/bom.csv`;
    $('#drawing-link').textContent=custom?`Open ${r.part} STEP ↗`:'Open procurement register ↗';
    $('#focus-part').disabled=false;$('#isolate').disabled=false;
    if([...$('#part-list').options].some(o=>o.value===name))$('#part-list').value=name;
    document.querySelectorAll('[data-assembly]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.assembly===r.group)));
  }
  function listParts(filter='') {
    const term=filter.toLowerCase();
    $('#part-list').replaceChildren(...bench.items.filter(({record:r})=>
      `${r.part} ${r.name} ${cad.parts[r.part].title}`.toLowerCase().includes(term)).map(({record:r})=>{
        const option=document.createElement('option');option.value=r.name;option.textContent=`${r.part} · ${r.name.replaceAll('_',' ')}`;return option;
      }));
  }
  listParts();$('#part-search').addEventListener('input',e=>listParts(e.target.value));
  $('#part-list').addEventListener('change',e=>select(e.target.value));
  for(const [id,group] of Object.entries(groups)) {
    const b=document.createElement('button');b.className='assembly-button';b.dataset.assembly=id;b.setAttribute('aria-pressed','false');
    const count=bench.items.filter(i=>i.record.group===id).length;
    b.innerHTML=`<small>${String(count).padStart(2,'0')}</small><div><span>${group.name}</span><em>${group.note}</em></div>`;
    b.addEventListener('click',()=>{
      state.isolate=null;$('#isolate').textContent='Isolate assembly';
      const views={frame:'overview',guard:'guard',control:'overview',endpoints:'endpoints'};
      setView(views[id]||'mechanism');
      const selected=bench.items.find(i=>i.record.group===id);select(selected.record.name);
      if(id!=='frame')focus([bench.assemblies[id]]);
    });$('#assemblies').appendChild(b);
  }
  $('#focus-part').addEventListener('click',()=>{
    const item=bench.items.find(i=>i.record.name===state.selected);
    if(item){
      state.isolate=null;state.panels=true;state.specimen=true;
      $('#panels').checked=true;$('#specimen').checked=true;
      $('#isolate').textContent='Isolate assembly';
      setView('overview');focus([item.holder]);
      $('#scene-title').textContent=cad.parts[item.record.part].title;
      $('#scene-subtitle').textContent=`${item.record.part} · ${item.record.name.replaceAll('_',' ')}`;
    }
  });
  $('#isolate').addEventListener('click',()=>{
    const item=bench.items.find(i=>i.record.name===state.selected);if(!item)return;
    state.isolate=state.isolate?null:item.record.group;
    $('#isolate').textContent=state.isolate?'Show all assemblies':'Isolate assembly';
    if(state.isolate){
      state.panels=true;state.specimen=true;$('#panels').checked=true;$('#specimen').checked=true;
      setView('overview');focus([bench.assemblies[state.isolate]]);
    }else setView('overview');
  });
  const ray=new THREE.Raycaster(),pointer=new THREE.Vector2();let down=null;
  renderer.domElement.addEventListener('pointerdown',e=>{down=[e.clientX,e.clientY];});
  renderer.domElement.addEventListener('pointerup',e=>{
    if(!down||Math.hypot(e.clientX-down[0],e.clientY-down[1])>5)return;
    const rect=renderer.domElement.getBoundingClientRect();pointer.set((e.clientX-rect.left)/rect.width*2-1,-(e.clientY-rect.top)/rect.height*2+1);ray.setFromCamera(pointer,camera);
    const hits=ray.intersectObjects(bench.items.filter(i=>i.holder.visible).map(i=>i.mesh),false);
    const hit=hits.find(h=>!h.object.material.transparent)||hits[0];
    if(hit)select(hit.object.userData.record.name);
  });
  function pause(){simulation.pause();refresh();}
  function refresh(){
    state.angle=simulation.angle;state.guardOpen=simulation.guardOpen;
    $('#angle').value=String(simulation.angle);$('#angle-value').textContent=`${simulation.angle.toFixed(1)}°`;
    $('#cycles').textContent=String(simulation.cycles).padStart(4,'0');
    const seconds=Math.floor(simulation.elapsed);
    $('#elapsed').textContent=`${String(Math.floor(seconds/60)).padStart(2,'0')}:${String(seconds%60).padStart(2,'0')} simulated`;
    $('#phase').textContent=simulation.fault?'Reset required':simulation.running?phases[simulation.phase]:simulation.phase==='ready'?'Ready':'Paused';
    $('#phase-light').className=simulation.fault?'fault':simulation.running?'running':'';
    $('#play').innerHTML=simulation.running?'Pause <span>Ⅱ</span>':'Run study <span>▶</span>';
    $('#play').setAttribute('aria-label',simulation.running?'Pause folding study':'Run folding study');
    $('#play').disabled=!simulation.permit||state.explode>0||state.mode==='build';
    $('#angle').disabled=state.mode==='build'||state.explode>0||!simulation.permit;
    $('#permit-reset').disabled=!simulation.fault||simulation.guardOpen||simulation.estop;
    $('#fault-message').classList.toggle('fault',!!simulation.fault);
    $('#fault-message').textContent=simulation.fault?
      `${simulation.fault}. Restore both inputs, reset the permit, then explicitly run again.`:
      'A full cycle closes, dwells, opens and dwells.';
    for(const [id,on] of [['permit',simulation.permit],['open',simulation.openSensor],['closed',simulation.closedSensor]])$('#signal-'+id).classList.toggle('on',on);
    const end=Math.max(60,simulation.elapsed),start=end-60;
    const points=simulation.history.filter(p=>p.t>=start).map(p=>`${((p.t-start)/60*700).toFixed(2)},${(43-(p.angle-5)/170*40).toFixed(2)}`);
    $('#trace-path').setAttribute('d',points.length?'M'+points.join(' L'):'');
  }
  $('#play').addEventListener('click',()=>{if(simulation.running)simulation.pause();else simulation.start();refresh();});
  $('#angle').addEventListener('input',e=>{simulation.scrub(Number(e.target.value));refresh();});
  for(const [id,property,min,max] of [['speed','speed',1,30],['dwell','dwell',.25,60]])$('#'+id).addEventListener('change',e=>{
    const raw=Number(e.target.value);const value=Number.isFinite(raw)?Math.max(min,Math.min(max,raw)):simulation[property];simulation[property]=value;e.target.value=String(value);
  });
  $('#timescale').addEventListener('change',e=>{$('#clock-scale').textContent=`${e.target.value}× playback`;});
  for(const [id,property]of [['guard-fault','guardOpen'],['estop-fault','estop']])$('#'+id).addEventListener('change',e=>{simulation.setInput(property,e.target.checked);refresh();});
  $('#permit-reset').addEventListener('click',()=>{simulation.resetPermit();refresh();});
  $('#float').addEventListener('input',e=>{pause();state.float=Number(e.target.value);$('#float-value').textContent=`${state.float.toFixed(1)} mm`;});
  $('#explode').addEventListener('input',e=>{
    pause();state.explode=Number(e.target.value)/100;$('#explode-value').textContent=`${e.target.value}%`;
    if(state.explode>0)simulation.scrub(175);setView('overview');refresh();
  });
  for(const id of ['panels','specimen','dimensions'])$('#'+id).addEventListener('change',e=>{state[id]=e.target.checked;});
  for(const [i,operation] of cad.operations.entries()){
    const option=document.createElement('option');option.value=i;option.textContent=`${String(i+1).padStart(2,'0')} / ${operation.title}`;$('#step-select').appendChild(option);
  }
  function showStep(){
    const op=cad.operations[state.step];$('#step-select').value=String(state.step);
    $('#step-count').textContent=`${String(state.step+1).padStart(2,'0')} / ${cad.operations.length}`;
    $('#step-title').textContent=op.title;$('#step-parts').textContent=op.parts;
    $('#step-actions').replaceChildren(...op.actions.map(text=>{const li=document.createElement('li');li.textContent=text;return li;}));
    $('#step-check').textContent=op.check;$('#previous').disabled=state.step===0;$('#next').disabled=state.step===cad.operations.length-1;
    $('#step-link').href=`${repo}/blob/main/docs/rev-b/Foldatron-Rev-B-assembly-traveler.pdf#page=${state.step+2}`;
    $('#scene-title').textContent=`${String(state.step+1).padStart(2,'0')} / Assembly operation`;
    $('#scene-subtitle').textContent=state.step<2?'Inventory / drawing review · complete model shown':'Cumulative CAD assembly · detailed hardware follows the traveler';
    bench.update(state,1);
  }
  function setMode(mode){
    state.mode=mode;pause();state.isolate=null;$('#isolate').textContent='Isolate assembly';
    document.querySelectorAll('[data-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.mode===mode)));
    for(const id of ['motion','parts','build'])$('#'+id+'-panel').hidden=id!==mode;
    $('#explode').disabled=mode==='build';
    if(mode==='build'){state.explode=0;$('#explode').value='0';$('#explode-value').textContent='0%';simulation.scrub(175);setView('overview');showStep();}
    else setView(state.view);
    refresh();
  }
  document.querySelectorAll('[data-mode]').forEach(b=>b.addEventListener('click',()=>setMode(b.dataset.mode)));
  $('#step-select').addEventListener('change',e=>{state.step=Number(e.target.value);showStep();});
  $('#next').addEventListener('click',()=>{state.step=Math.min(cad.operations.length-1,state.step+1);showStep();});
  $('#previous').addEventListener('click',()=>{state.step=Math.max(0,state.step-1);showStep();});
  const initialInspector=$('.inspector').innerHTML;
  $('#reset').addEventListener('click',()=>{
    simulation.reset();simulation.scrub(110);state.float=0;state.explode=0;state.step=0;state.selected=null;state.panels=true;state.specimen=true;state.dimensions=true;
    for(const id of ['panels','specimen','dimensions'])$('#'+id).checked=true;
    for(const id of ['guard-fault','estop-fault'])$('#'+id).checked=false;
    for(const id of ['float','explode'])$('#'+id).value='0';
    $('#float-value').textContent='0.0 mm';$('#explode-value').textContent='0%';$('#speed').value='15';$('#dwell').value='1';$('#timescale').value='1';$('#clock-scale').textContent='1× playback';
    $('.inspector').innerHTML=initialInspector;bench.select(null);$('#focus-part').disabled=true;$('#isolate').disabled=true;
    $('#part-search').value='';listParts();document.querySelectorAll('[data-assembly]').forEach(b=>b.setAttribute('aria-pressed','false'));
    setMode('motion');setView('mechanism');refresh();
  });
  let previous=performance.now(),uiTime=0;
  document.addEventListener('visibilitychange',()=>{previous=performance.now();});
  renderer.setAnimationLoop(time=>{
    const dt=Math.min(.1,Math.max(0,(time-previous)/1000));previous=time;
    if(document.hidden)return;
    simulation.advance(dt*Number($('#timescale').value));state.angle=simulation.angle;
    bench.update(state,dt);
    if(cameraMoving){const ease=reduced?1:1-Math.exp(-dt*6);camera.position.lerp(targetPosition,ease);controls.target.lerp(targetLook,ease);if(camera.position.distanceTo(targetPosition)<.1)cameraMoving=false;}
    if(time-uiTime>80){refresh();uiTime=time;}
    controls.update();renderer.render(scene,camera);
  });
  renderer.domElement.addEventListener('webglcontextlost',event=>{event.preventDefault();pause();const message=document.createElement('p');message.id='loading';message.textContent='Graphics context interrupted. Reload the viewer.';viewport.appendChild(message);});
  refresh();
}
