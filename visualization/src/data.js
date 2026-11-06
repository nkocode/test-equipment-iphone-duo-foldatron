import cad from './rev-b-model.json' with {type:'json'};
export {cad};
export const repo='https://github.com/nkocode/test-equipment-iphone-duo-foldatron';
export const groups={
  frame:{name:'1010 structure',note:'25.4 mm extrusion · 28 corner brackets',offset:[-160,-100,-150]},
  foundation:{name:'Base & fixed tray',note:'500 × 460 mm base · 140 mm hinge axis',offset:[-70,0,100]},
  bearings:{name:'Bearings & split shafts',note:'NSK 626 · ground 6 mm shafts',offset:[0,65,180]},
  yoke:{name:'Yoke & counterweights',note:'Independent X/Z balance adjustment',offset:[0,220,0]},
  float:{name:'Radial carriage',note:'Two MGN7 guides · manual ±5.7 mm study',offset:[140,340,0]},
  drive:{name:'Actuator & clutch',note:'XM430-W350-T · EAS12 configuration pending',offset:[0,40,350]},
  endpoints:{name:'Endpoint cam & switches',note:'B125–B127 · output-side sensing',offset:[0,75,-260]},
  guard:{name:'Panels & interlock',note:'4 mm polycarbonate · removable front panel',offset:[-200,320,-80]},
  control:{name:'Control enclosure',note:'Hammond 1554YA2GY · external cabinet envelope',offset:[250,0,0]},
  specimen:{name:'Reference specimen',note:'Unverified envelope · shop measures the actual phone',offset:[0,430,0]},
};
export const phases={ready:'Ready',closing:'Closing',opening:'Opening','dwell-closed':'Closed dwell','dwell-open':'Open dwell',fault:'Stopped'};
export const holds={P1:'Phone inserts require shop metrology.',P2:'Clutch engagement and low-torque operation require supplier confirmation.',P3:'Guard and endpoint actuation require physical acceptance.',P4:'Electrical mounting, harness completion and machine acceptance remain open.'};
