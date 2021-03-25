#ifndef _MULTIAGENTEXP_DRAW_H_
#define _MULTIAGENTEXP_DRAW_H_

#include "SDL2/SDL.h"
#include "SDL2/SDL_ttf.h"

struct App;

void draw_text(struct App * app, int x, int y,
               TTF_Font * font, SDL_Color color,
               char * string);

void draw_textf(struct App * app, int x, int y,
                TTF_Font * font, SDL_Color color,
                char * format, ...);

void draw_point(struct App * app, int x, int y, SDL_Color color);
void draw_line(struct App * app, int x1, int y1, int x2, int y2, SDL_Color color);
void draw_polygon(struct App * app, float center_x, float center_y,
                  float radius, int sides, float angle,
                  SDL_Color color);

void draw_circle(struct App * app,
                 float center_x, float center_y, float radius,
                 SDL_Color color);

void draw_triangle_center(struct App * app, float center_x, float center_y, float radius, float angle, SDL_Color color);
void draw_rect(struct App * app, int x, int y, int w, int h, SDL_Color color);
void fill_rect(struct App * app, int x, int y, int w, int h, SDL_Color color);
void draw_cursor(struct App * app, int x, int y, SDL_Color color);

#endif // _HOVERRUN_DRAW_H_
