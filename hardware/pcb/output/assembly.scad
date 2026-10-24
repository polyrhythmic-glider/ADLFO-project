// ADLFO review assembly. Coordinates match design.json. NOT machining release.
// Set explode=0 for nominal assembly. Z=0 is PCB front; panel underside=10 mm.
$fn=64; explode=15; panel_gap=10; panel_thickness=2;
module panel() {
 difference() {
  cube([101.2,128.5,panel_thickness]);
  translate([17.5,80.5,-1]) cylinder(h=4,d=7.2);
  translate([17.5,61.5,-1]) cylinder(h=4,d=4.0);
  translate([17.5,48.5,-1]) cylinder(h=4,d=6.2);
  translate([17.5,33.5,-1]) cylinder(h=4,d=6.2);
  translate([17.5,18.5,-1]) cylinder(h=4,d=6.2);
  translate([39.5,80.5,-1]) cylinder(h=4,d=7.2);
  translate([39.5,61.5,-1]) cylinder(h=4,d=4.0);
  translate([39.5,48.5,-1]) cylinder(h=4,d=6.2);
  translate([39.5,33.5,-1]) cylinder(h=4,d=6.2);
  translate([39.5,18.5,-1]) cylinder(h=4,d=6.2);
  translate([61.5,80.5,-1]) cylinder(h=4,d=7.2);
  translate([61.5,61.5,-1]) cylinder(h=4,d=4.0);
  translate([61.5,48.5,-1]) cylinder(h=4,d=6.2);
  translate([61.5,33.5,-1]) cylinder(h=4,d=6.2);
  translate([61.5,18.5,-1]) cylinder(h=4,d=6.2);
  translate([83.5,80.5,-1]) cylinder(h=4,d=7.2);
  translate([83.5,61.5,-1]) cylinder(h=4,d=4.0);
  translate([83.5,48.5,-1]) cylinder(h=4,d=6.2);
  translate([83.5,33.5,-1]) cylinder(h=4,d=6.2);
  translate([83.5,18.5,-1]) cylinder(h=4,d=6.2);
  translate([6.5,116.5,-1]) cylinder(h=4,d=3.2);
  translate([94.7,116.5,-1]) cylinder(h=4,d=3.2);
  translate([6.5,12.5,-1]) cylinder(h=4,d=3.2);
  translate([94.7,12.5,-1]) cylinder(h=4,d=3.2);
  hull() {translate([6.5,125.5,-1]) cylinder(h=4,d=3.2); translate([8.5,125.5,-1]) cylinder(h=4,d=3.2);}
  hull() {translate([92.86,125.5,-1]) cylinder(h=4,d=3.2); translate([94.86,125.5,-1]) cylinder(h=4,d=3.2);}
  hull() {translate([6.5,3.0,-1]) cylinder(h=4,d=3.2); translate([8.5,3.0,-1]) cylinder(h=4,d=3.2);}
  hull() {translate([92.86,3.0,-1]) cylinder(h=4,d=3.2); translate([94.86,3.0,-1]) cylinder(h=4,d=3.2);}
  translate([10.5,98.5,-1]) cube([27,15,4]);
 }
}
color([0.08,0.1,0.12]) translate([0,0,panel_gap+explode]) panel();
color([0.07,0.32,0.24]) difference() {translate([2.5,9.0,-1.6]) cube([96.2,110.5,1.6]);
translate([6.5,116.5,-2]) cylinder(d=3.2,h=3);
translate([94.7,116.5,-2]) cylinder(d=3.2,h=3);
translate([6.5,12.5,-2]) cylinder(d=3.2,h=3);
translate([94.7,12.5,-2]) cylinder(d=3.2,h=3);
translate([17.5,48.5,-2]) cylinder(d=3,h=3);
translate([17.5,33.5,-2]) cylinder(d=3,h=3);
translate([17.5,18.5,-2]) cylinder(d=3,h=3);
translate([39.5,48.5,-2]) cylinder(d=3,h=3);
translate([39.5,33.5,-2]) cylinder(d=3,h=3);
translate([39.5,18.5,-2]) cylinder(d=3,h=3);
translate([61.5,48.5,-2]) cylinder(d=3,h=3);
translate([61.5,33.5,-2]) cylinder(d=3,h=3);
translate([61.5,18.5,-2]) cylinder(d=3,h=3);
translate([83.5,48.5,-2]) cylinder(d=3,h=3);
translate([83.5,33.5,-2]) cylinder(d=3,h=3);
translate([83.5,18.5,-2]) cylinder(d=3,h=3);
}
color("silver") translate([6.5,116.5,0]) difference(){cylinder(d=5,h=panel_gap);cylinder(d=3.2,h=panel_gap);}
color("silver") translate([94.7,116.5,0]) difference(){cylinder(d=5,h=panel_gap);cylinder(d=3.2,h=panel_gap);}
color("silver") translate([6.5,12.5,0]) difference(){cylinder(d=5,h=panel_gap);cylinder(d=3.2,h=panel_gap);}
color("silver") translate([94.7,12.5,0]) difference(){cylinder(d=5,h=panel_gap);cylinder(d=3.2,h=panel_gap);}
color([0.1,0.2,0.22]) translate([44.5,95.5,-13]) cube([51,18,1.6]);
color([0.05,0.2,0.35]) translate([16.3,95.61,-9]) cube([25.4,17.78,1.6]);
color("silver") translate([17.5,80.5,0]) cylinder(d=6,h=20);
color("gray") translate([17.5,61.5,0]) cylinder(d=3.5,h=13);
color("silver") translate([17.5,48.5,0]) difference(){cylinder(d=6,h=13);cylinder(d=3.5,h=14);}
color("silver") translate([17.5,33.5,0]) difference(){cylinder(d=6,h=13);cylinder(d=3.5,h=14);}
color("silver") translate([17.5,18.5,0]) difference(){cylinder(d=6,h=13);cylinder(d=3.5,h=14);}
color("silver") translate([39.5,80.5,0]) cylinder(d=6,h=20);
color("gray") translate([39.5,61.5,0]) cylinder(d=3.5,h=13);
color("silver") translate([39.5,48.5,0]) difference(){cylinder(d=6,h=13);cylinder(d=3.5,h=14);}
color("silver") translate([39.5,33.5,0]) difference(){cylinder(d=6,h=13);cylinder(d=3.5,h=14);}
color("silver") translate([39.5,18.5,0]) difference(){cylinder(d=6,h=13);cylinder(d=3.5,h=14);}
color("silver") translate([61.5,80.5,0]) cylinder(d=6,h=20);
color("gray") translate([61.5,61.5,0]) cylinder(d=3.5,h=13);
color("silver") translate([61.5,48.5,0]) difference(){cylinder(d=6,h=13);cylinder(d=3.5,h=14);}
color("silver") translate([61.5,33.5,0]) difference(){cylinder(d=6,h=13);cylinder(d=3.5,h=14);}
color("silver") translate([61.5,18.5,0]) difference(){cylinder(d=6,h=13);cylinder(d=3.5,h=14);}
color("silver") translate([83.5,80.5,0]) cylinder(d=6,h=20);
color("gray") translate([83.5,61.5,0]) cylinder(d=3.5,h=13);
color("silver") translate([83.5,48.5,0]) difference(){cylinder(d=6,h=13);cylinder(d=3.5,h=14);}
color("silver") translate([83.5,33.5,0]) difference(){cylinder(d=6,h=13);cylinder(d=3.5,h=14);}
color("silver") translate([83.5,18.5,0]) difference(){cylinder(d=6,h=13);cylinder(d=3.5,h=14);}
