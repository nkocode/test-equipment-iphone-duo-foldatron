// Deterministic kinematic study. No force, motor-current or stopping-time claim.
export class MotionStudy {
  constructor() { this.reset(); }
  reset() {
    this.angle=175; this.velocity=0; this.speed=15; this.dwell=1;
    this.acceleration=60; this.phase='ready'; this.cycles=0;
    this.elapsed=0; this.wait=0; this.running=false;
    this.guardOpen=false; this.estop=false; this.fault=null;
    this.history=[{t:0,angle:175}]; this.sampleAt=0;
  }
  start() {
    if(this.guardOpen||this.estop||this.fault) return false;
    if(this.phase==='ready') this.phase='closing';
    this.running=true; return true;
  }
  pause() { this.running=false; this.velocity=0; }
  scrub(angle) {
    if(!Number.isFinite(angle)) throw new Error('Invalid angle');
    this.pause(); this.angle=Math.max(5,Math.min(175,angle));
    this.phase=this.fault?'fault':'ready'; this.wait=0;
  }
  setInput(input,active) {
    if(!['guardOpen','estop'].includes(input)) throw new Error('Invalid input');
    this[input]=active;
    if(active) {
      this.pause(); this.fault=input==='estop'?'Emergency stop':'Guard removed';
      this.phase='fault';
    }
  }
  resetPermit() {
    if(this.guardOpen||this.estop) return false;
    this.fault=null; this.phase='ready'; this.wait=0; this.pause(); return true;
  }
  get permit() { return !this.guardOpen&&!this.estop&&!this.fault; }
  get openSensor() { return this.angle>=174.5; }
  get closedSensor() { return this.angle<=5.5; }
  advance(seconds) {
    if(!Number.isFinite(seconds)||seconds<0) throw new Error('Invalid time');
    // A bounded integration step makes accelerated playback deterministic.
    for(let remaining=seconds; remaining>1e-9;) {
      const dt=Math.min(remaining,1/120); remaining-=dt;
      if(!this.running||!this.permit) break;
      this.elapsed+=dt;
      if(this.phase.startsWith('dwell')) {
        this.wait-=dt; this.velocity=0;
        if(this.wait<=1e-9) {
          if(this.phase==='dwell-open') this.cycles++;
          this.phase=this.phase==='dwell-open'?'closing':'opening';
        }
      } else {
        const target=this.phase==='closing'?5:175;
        const direction=Math.sign(target-this.angle);
        const distance=Math.abs(target-this.angle);
        const speed=Math.min(this.speed,
          Math.sqrt(2*this.acceleration*distance),
          Math.abs(this.velocity)+this.acceleration*dt);
        const travel=Math.min(distance,speed*dt);
        this.velocity=direction*speed; this.angle+=direction*travel;
        if(distance<=travel+1e-8) {
          this.angle=target;this.velocity=0;this.wait=this.dwell;
          this.phase=target===5?'dwell-closed':'dwell-open';
        }
      }
      if(this.elapsed>=this.sampleAt) {
        this.history.push({t:this.elapsed,angle:this.angle});
        this.sampleAt=this.elapsed+.1;
        while(this.history.length>1200) this.history.shift();
      }
    }
  }
}

export function outputPoint(x,y,z,opening,float=0) {
  const theta=(180-opening)*Math.PI/180;
  return [(x+float)*Math.cos(theta)-(y-140)*Math.sin(theta),
    140+(x+float)*Math.sin(theta)+(y-140)*Math.cos(theta),z];
}
