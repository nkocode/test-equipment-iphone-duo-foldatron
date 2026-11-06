import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {MotionStudy,outputPoint} from '../src/simulation.js';
const cad=JSON.parse(readFileSync(new URL('../src/rev-b-model.json',import.meta.url)));

test('complete cycle respects travel limits, dwell and speed',()=>{
  const s=new MotionStudy();s.start();let closedDwell=0,openDwell=0;
  for(let n=0;n<3100&&s.cycles===0;n++){
    const last=s.angle;s.advance(.01);
    assert(s.angle>=5&&s.angle<=175);
    assert(Math.abs(s.angle-last)<=.150001);
    if(s.phase==='dwell-closed')closedDwell+=.01;
    if(s.phase==='dwell-open')openDwell+=.01;
  }
  assert.equal(s.cycles,1);assert(s.angle>174.99);
  assert(closedDwell>=.99&&openDwell>=.99);
  assert(s.elapsed>24&&s.elapsed<27);
});
test('pause freezes both virtual time and position',()=>{
  const s=new MotionStudy();s.start();s.advance(3);s.pause();
  const position=s.angle,time=s.elapsed;s.advance(100);
  assert.equal(s.angle,position);assert.equal(s.elapsed,time);
  s.start();s.advance(1);assert(s.angle<position);
});
for(const input of ['guardOpen','estop'])test(`${input} latches until reset and explicit start`,()=>{
  const s=new MotionStudy();s.start();s.advance(2);s.setInput(input,true);
  const position=s.angle;s.advance(5);assert.equal(s.angle,position);
  assert.equal(s.permit,false);assert.equal(s.resetPermit(),false);
  s.setInput(input,false);assert.equal(s.start(),false);
  assert.equal(s.resetPermit(),true);assert.equal(s.running,false);
  s.advance(2);assert.equal(s.angle,position);
  assert.equal(s.start(),true);s.advance(1);assert(s.angle<position);
});
test('both safety inputs must be restored before permit reset',()=>{
  const s=new MotionStudy();s.setInput('guardOpen',true);s.setInput('estop',true);
  s.setInput('guardOpen',false);assert.equal(s.resetPermit(),false);
  s.setInput('estop',false);assert.equal(s.resetPermit(),true);
});
test('presentation changes cannot clear a latched fault',()=>{
  const s=new MotionStudy();s.setInput('guardOpen',true);s.scrub(175);
  assert.equal(s.phase,'fault');assert.equal(s.start(),false);
  s.setInput('guardOpen',false);assert.equal(s.start(),false);
  s.resetPermit();assert.equal(s.running,false);assert.equal(s.start(),true);
});
test('time scaling changes presentation time, not cycle trajectory',()=>{
  const a=new MotionStudy(),b=new MotionStudy();a.start();b.start();
  for(let i=0;i<240;i++)a.advance(1/60);
  for(let i=0;i<60;i++)b.advance(4/60);
  assert(Math.abs(a.angle-b.angle)<1e-8);
});
test('manual limits and nominal sensor polarity',()=>{
  const s=new MotionStudy();s.scrub(-50);assert.equal(s.angle,5);assert(s.closedSensor&&!s.openSensor);
  s.scrub(999);assert.equal(s.angle,175);assert(s.openSensor&&!s.closedSensor);
  assert.throws(()=>s.scrub(NaN));assert.throws(()=>s.advance(Infinity));
});
test('CAD opening convention rotates about the 140 mm output axis',()=>{
  const open=outputPoint(100,140,45,180);
  assert.deepEqual(open,[100,140,45]);
  const halfway=outputPoint(100,140,45,90);
  assert(Math.abs(halfway[0])<1e-9);assert.equal(halfway[1],240);
  const closed=outputPoint(100,140,45,0);
  assert.equal(closed[0],-100);assert(Math.abs(closed[1]-140)<1e-9);
  assert.deepEqual(outputPoint(0,140,45,180,5.7),[5.7,140,45]);
});
test('export contains the current CAD and complete traveler',()=>{
  assert.equal(cad.instances.length,122);assert.equal(cad.operations.length,20);
  for(const [path,hash]of Object.entries(cad.provenance)){
    const bytes=readFileSync(new URL('../../'+path,import.meta.url));
    assert.equal(createHash('sha256').update(bytes).digest('hex'),hash,`Stale CAD export: ${path}`);
  }
  const base=cad.instances.find(i=>i.part==='B101');
  assert(Math.abs(base.bounds[3]-base.bounds[0]-500)<.001);
  assert(Math.abs(base.bounds[5]-base.bounds[2]-460)<.001);
  const cam=cad.instances.find(i=>i.name==='endpoint_cam');assert(cam.moving);
  assert(cad.instances.filter(i=>i.name.startsWith('endpoint_switch_')).every(i=>!i.moving));
  assert(cad.instances.filter(i=>i.rotor).length===2);
  for(const item of cad.instances){
    assert.equal(item.positions.length%3,0);assert.equal(item.indices.length%3,0);
    assert(item.positions.every(Number.isFinite));
    assert(item.indices.every(i=>Number.isInteger(i)&&i>=0&&i<item.positions.length/3));
    assert(item.stage>=3&&item.stage<=16);
  }
});
