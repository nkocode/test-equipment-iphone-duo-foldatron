// FoldBench Rev A. Units mm. Envelope model + adjustable plate blanks.
// NOT a collision-validated fabrication release. Vendor patterns transfer-drilled.
// part: "assembly", "base", "backplate", "shoe", "arm", "tower".
part = "assembly";
opening = 110; // phone opening angle: 0 closed; 180 open
hinge_z = 140;
support_y = 95;
radius = 115;
$fn = 48;

module slot(length=20, width=4.5, height=10) {
    hull() for (x=[-(length-width)/2,(length-width)/2])
        translate([x,0,0]) cylinder(h=height,d=width,center=true);
}
module base() {
    difference() {
        translate([0,0,-4]) cube([500,400,8],center=true);
        for(x=[-175:25:175],y=[-125:25:125])
            translate([x,y,-4]) cylinder(h=12,d=6.6,center=true);
        for(x=[-230,230],y=[-180,180])
            translate([x,y,-4]) cylinder(h=12,d=6.6,center=true);
    }
}
module backplate() {
    difference() {
        cube([100,135,4],center=true);
        for(x=[-30,30],y=[-48,48]) translate([x,y,0]) slot();
    }
}
module shoe() {
    // Blank only: contact contour MUST be measured and machined per specimen.
    difference() {
        cube([20,15,8],center=true);
        slot(10,4.5,12);
    }
}
module arm() {
    difference() {
        translate([55,0,0]) cube([125,25,6],center=true);
        translate([0,0,0]) cylinder(d=6.6,h=10,center=true);
        for(y=[-6,6]) translate([115,y,0]) cylinder(d=4.5,h=10,center=true);
    }
}
module tower() {
    difference() {
        translate([0,0,90]) cube([100,8,180],center=true);
        for(x=[-25,25]) translate([x,0,140])
            rotate([90,0,90]) slot(30,6.6,12);
    }
}
module shaft(length) {
    rotate([90,0,0]) cylinder(d=6,h=length,center=true);
}
module assembly() {
    color("lightgray") base();
    // Tower envelopes, bearing patterns intentionally omitted.
    for(y=[-support_y,support_y]) color("gray") translate([0,y,0]) tower();
    // Separate stub shafts -- the space between phone ends remains EMPTY.
    color("silver") translate([0,-110,hinge_z]) shaft(80);
    color("silver") translate([0,105,hinge_z]) shaft(50);
    // Fixed plate and nominal phone half.
    color("slategray") translate([-47,0,hinge_z-9]) backplate();
    color([0.1,0.25,0.35]) translate([-42,0,hinge_z-2.6])
        cube([80,117.8,5.2],center=true);
    // Rotating yoke + nominal floating carrier envelope.
    translate([0,0,hinge_z]) rotate([0,opening-180,0]) {
        for(y=[-support_y,support_y]) color("gray")
            translate([0,y,-10]) arm();
        color("gray") translate([radius,0,-10])
            cube([25,190,6],center=true);
        color("lightsteelblue") translate([47,0,-9]) backplate();
        color([0.25,0.65,0.61]) translate([42,0,-2.6])
            cube([80,117.8,5.2],center=true);
        for(y=[-45,45]) color("silver") translate([50,y,-17])
            cube([100,7,8],center=true);
    }
    // Servo and clutch envelopes; final mounts follow vendor drawings.
    color("orange") translate([0,-151,hinge_z])
        rotate([90,0,0]) cylinder(d=19.05,h=31.75,center=true);
    color("dimgray") translate([0,-185,hinge_z])
        cube([34,46.5,28.5],center=true);
    // Transparent guard envelope.
    color([0.6,0.8,0.9,0.10]) translate([0,0,200])
        difference() {
            cube([600,500,400],center=true);
            cube([592,492,392],center=true);
        }
}

if(part=="assembly") assembly();
else if(part=="base") base();
else if(part=="backplate") backplate();
else if(part=="shoe") shoe();
else if(part=="arm") arm();
else if(part=="tower") tower();
