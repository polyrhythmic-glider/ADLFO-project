// ADLFO review assembly. Coordinates match design.json. NOT machining release.
// Set explode=0 for nominal assembly. Z=0 is PCB front; panel underside=10 mm.
$fn=64; explode=15; panel_gap=10; panel_thickness=2;
module panel() {
 difference() {
  cube([121.6,128.5,panel_thickness]);
  translate([22.0,80.5,-1]) cylinder(h=4,d=7.2);
  translate([22.0,61.5,-1]) cylinder(h=4,d=4.0);
  translate([22.0,48.5,-1]) cylinder(h=4,d=6.2);
  translate([22.0,33.5,-1]) cylinder(h=4,d=6.2);
  translate([22.0,18.5,-1]) cylinder(h=4,d=6.2);
  translate([48.0,80.5,-1]) cylinder(h=4,d=7.2);
  translate([48.0,61.5,-1]) cylinder(h=4,d=4.0);
  translate([48.0,48.5,-1]) cylinder(h=4,d=6.2);
  translate([48.0,33.5,-1]) cylinder(h=4,d=6.2);
  translate([48.0,18.5,-1]) cylinder(h=4,d=6.2);
  translate([74.0,80.5,-1]) cylinder(h=4,d=7.2);
  translate([74.0,61.5,-1]) cylinder(h=4,d=4.0);
  translate([74.0,48.5,-1]) cylinder(h=4,d=6.2);
  translate([74.0,33.5,-1]) cylinder(h=4,d=6.2);
  translate([74.0,18.5,-1]) cylinder(h=4,d=6.2);
  translate([100.0,80.5,-1]) cylinder(h=4,d=7.2);
  translate([100.0,61.5,-1]) cylinder(h=4,d=4.0);
  translate([100.0,48.5,-1]) cylinder(h=4,d=6.2);
  translate([100.0,33.5,-1]) cylinder(h=4,d=6.2);
  translate([100.0,18.5,-1]) cylinder(h=4,d=6.2);
  translate([6.5,115.5,-1]) cylinder(h=4,d=3.2);
  translate([115.1,115.5,-1]) cylinder(h=4,d=3.2);
  translate([6.5,12.5,-1]) cylinder(h=4,d=3.2);
  translate([115.1,12.5,-1]) cylinder(h=4,d=3.2);
  hull() {translate([6.5,125.5,-1]) cylinder(h=4,d=3.2); translate([8.5,125.5,-1]) cylinder(h=4,d=3.2);}
  hull() {translate([113.18,125.5,-1]) cylinder(h=4,d=3.2); translate([115.18,125.5,-1]) cylinder(h=4,d=3.2);}
  hull() {translate([6.5,3.0,-1]) cylinder(h=4,d=3.2); translate([8.5,3.0,-1]) cylinder(h=4,d=3.2);}
  hull() {translate([113.18,3.0,-1]) cylinder(h=4,d=3.2); translate([115.18,3.0,-1]) cylinder(h=4,d=3.2);}
  translate([15.5,98.5,-1]) cube([27,15,4]);
 }
}
color([0.08,0.1,0.12]) translate([0,0,panel_gap+explode]) panel();
color([0.07,0.32,0.24]) difference() {translate([2.5,9.0,-1.6]) cube([116.6,110.5,1.6]);
translate([6.5,115.5,-2]) cylinder(d=3.2,h=3);
translate([115.1,115.5,-2]) cylinder(d=3.2,h=3);
translate([6.5,12.5,-2]) cylinder(d=3.2,h=3);
translate([115.1,12.5,-2]) cylinder(d=3.2,h=3);
translate([22.0,48.5,-2]) cylinder(d=3,h=3);
translate([22.0,33.5,-2]) cylinder(d=3,h=3);
translate([22.0,18.5,-2]) cylinder(d=3,h=3);
translate([48.0,48.5,-2]) cylinder(d=3,h=3);
translate([48.0,33.5,-2]) cylinder(d=3,h=3);
translate([48.0,18.5,-2]) cylinder(d=3,h=3);
translate([74.0,48.5,-2]) cylinder(d=3,h=3);
translate([74.0,33.5,-2]) cylinder(d=3,h=3);
translate([74.0,18.5,-2]) cylinder(d=3,h=3);
translate([100.0,48.5,-2]) cylinder(d=3,h=3);
translate([100.0,33.5,-2]) cylinder(d=3,h=3);
translate([100.0,18.5,-2]) cylinder(d=3,h=3);
}
color("silver") translate([6.5,115.5,0]) difference(){cylinder(d=5,h=panel_gap);cylinder(d=3.2,h=panel_gap);}
color("silver") translate([115.1,115.5,0]) difference(){cylinder(d=5,h=panel_gap);cylinder(d=3.2,h=panel_gap);}
color("silver") translate([6.5,12.5,0]) difference(){cylinder(d=5,h=panel_gap);cylinder(d=3.2,h=panel_gap);}
color("silver") translate([115.1,12.5,0]) difference(){cylinder(d=5,h=panel_gap);cylinder(d=3.2,h=panel_gap);}
color([0.1,0.2,0.22]) translate([56.5,95.5,-13]) cube([51,18,1.6]);
color("silver") translate([22.0,80.5,0]) cylinder(d=6,h=20);
color("gray") translate([22.0,61.5,0]) cylinder(d=3.5,h=13);
color("silver") translate([22.0,48.5,0]) difference(){cylinder(d=6,h=13);cylinder(d=3.5,h=14);}
color("silver") translate([22.0,33.5,0]) difference(){cylinder(d=6,h=13);cylinder(d=3.5,h=14);}
color("silver") translate([22.0,18.5,0]) difference(){cylinder(d=6,h=13);cylinder(d=3.5,h=14);}
color("silver") translate([48.0,80.5,0]) cylinder(d=6,h=20);
color("gray") translate([48.0,61.5,0]) cylinder(d=3.5,h=13);
color("silver") translate([48.0,48.5,0]) difference(){cylinder(d=6,h=13);cylinder(d=3.5,h=14);}
color("silver") translate([48.0,33.5,0]) difference(){cylinder(d=6,h=13);cylinder(d=3.5,h=14);}
color("silver") translate([48.0,18.5,0]) difference(){cylinder(d=6,h=13);cylinder(d=3.5,h=14);}
color("silver") translate([74.0,80.5,0]) cylinder(d=6,h=20);
color("gray") translate([74.0,61.5,0]) cylinder(d=3.5,h=13);
color("silver") translate([74.0,48.5,0]) difference(){cylinder(d=6,h=13);cylinder(d=3.5,h=14);}
color("silver") translate([74.0,33.5,0]) difference(){cylinder(d=6,h=13);cylinder(d=3.5,h=14);}
color("silver") translate([74.0,18.5,0]) difference(){cylinder(d=6,h=13);cylinder(d=3.5,h=14);}
color("silver") translate([100.0,80.5,0]) cylinder(d=6,h=20);
color("gray") translate([100.0,61.5,0]) cylinder(d=3.5,h=13);
color("silver") translate([100.0,48.5,0]) difference(){cylinder(d=6,h=13);cylinder(d=3.5,h=14);}
color("silver") translate([100.0,33.5,0]) difference(){cylinder(d=6,h=13);cylinder(d=3.5,h=14);}
color("silver") translate([100.0,18.5,0]) difference(){cylinder(d=6,h=13);cylinder(d=3.5,h=14);}
