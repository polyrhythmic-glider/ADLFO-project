#include "EncoderView.h"
#include "OledUi.h"
#include <array>
#include <cassert>
#include <fstream>
struct Event { int32_t delta=0; bool pressed=false, released=false; };
struct Canvas {
    bool pixels[64][128]{}; int x=0,y=0;
    void Fill(bool on) { for(auto& row:pixels) for(auto& p:row) p=on; }
    void SetCursor(int a,int b) {x=a;y=b;}
    void Pixel(int a,int b,bool on) {assert(a>=0&&a<128&&b>=0&&b<64);pixels[b][a]=on;}
    void DrawLine(int a,int b,int c,int e,bool on) {
        assert(a==c||b==e);
        for(int j=b;j<=e;++j) for(int i=a;i<=c;++i) Pixel(i,j,on);
    }
    void WriteString(const char* s,FontDef f,bool on) {
        assert(x>=0&&y>=0&&x+int(std::strlen(s))*f.FontWidth<=128&&y+f.FontHeight<=64);
        for(;*s;++s,x+=f.FontWidth)
            for(int j=0;j<f.FontHeight;++j)
                for(int i=0;i<f.FontWidth;++i)
                    Pixel(x+i,y+j,(f.data[(*s-32)*f.FontHeight+j] & (0x8000>>i)) ? on : !on);
    }
    void Save(const char* path) {
        std::ofstream o(path);o<<"P1\n128 64\n";
        for(auto& row:pixels) {for(bool p:row) o<<(p?0:1)<<' ';o<<'\n';}
    }
};
int main() {
    for(bool reverse:{false,true}) {
        ui::Chord chord;ui::EncoderView view;std::array<Event,4> e{};
        chord.Scan(!reverse,reverse);assert(!view.Process(e,chord.Consume()));
        chord.Scan(true,true);assert(view.Process(e,chord.Consume())&&view.active);
        for(int i=0;i<10;++i) {chord.Scan(true,true);view.Process(e,chord.Consume());assert(view.active);}
        chord.Scan(reverse,!reverse);view.Process(e,chord.Consume());assert(view.active);
        chord.Scan(false,false);assert(view.Process(e,chord.Consume()));
        for(int i=0;i<4;++i) {
            e={};e[i].delta=-25;view.Process(e,chord.Consume());assert(view.values[i]==-25);
            e={};e[i].pressed=true;view.Process(e,chord.Consume());assert(view.values[i]==-25);
            e={};e[i].released=true;view.Process(e,chord.Consume());assert(view.values[i]==0);
        }
        e={};e[0].delta=INT32_MAX;view.Process(e,{});assert(view.values[0]==9999);
        e[0].delta=INT32_MIN;view.Process(e,{});assert(view.values[0]==-9999);
        // Entire chord during one blocking display transfer; suppress both releases.
        e={};e[0].pressed=e[0].released=e[3].pressed=e[3].released=true;
        chord.Scan(true,true);chord.Scan(false,true);chord.Scan(false,false);
        assert(view.Process(e,chord.Consume())&&!view.active);
        e={};assert(!view.Process(e,chord.Consume()));
    }
    Canvas d;
    for(float time:{.005f,.15f,.9994f,.9995f,1.f,9.94f,9.95f,10.f})
        for(float value:{0.f,.5f,1.f})
            ui::DrawMain(d,time,time,value,value,value,value,true,"EXP");
    ui::DrawMain(d,.15f,1.2f,.65f,.5f,1.f,0.f,true,"LOG");d.Save("/tmp/adlfo-main.pbm");
    int32_t values[]={-9999,9999,0,-1};bool down[]={false,true,false,false};
    bool buttons[4]{};
    ui::DrawEncoders(d,values,down,buttons);
    Canvas released = d;
    // All combinations: pressed quadrants are white with a large black label;
    // unpressed quadrants retain their encoder display.
    for(unsigned mask = 0; mask < 16; ++mask) {
        for(unsigned i = 0; i < 4; ++i) buttons[i] = (mask >> i) & 1;
        ui::DrawEncoders(d,values,down,buttons);
        for(int y = 0; y < 64; ++y) for(int x = 0; x < 128; ++x) {
            unsigned i = (y / 32) * 2 + x / 64;
            if(!buttons[i]) assert(d.pixels[y][x] == released.pixels[y][x]);
            else {
                int local_x=x%64, local_y=y%32;
                bool expected=true;
                if(local_x>=21 && local_x<43 && local_y>=7 && local_y<25) {
                    char ch=local_x<32 ? 'B' : char('1'+i);
                    expected=!(Font_11x18.data[(ch-32)*18+local_y-7]
                               & (0x8000 >> ((local_x-21)%11)));
                }
                assert(d.pixels[y][x]==expected);
            }
        }
    }
    buttons[0]=buttons[2]=buttons[3]=false;buttons[1]=true;
    ui::DrawEncoders(d,values,down,buttons);d.Save("/tmp/adlfo-encoders.pbm");
}
