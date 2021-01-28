#include "draw.h"

#include <stdint.h>
#include <stdarg.h>
#include <stdio.h>

#include "SDL2/SDL.h"
#include "SDL2/SDL_ttf.h"

#include "app.h"


void draw_text(struct App * app, int x, int y,
               TTF_Font * font, SDL_Color color,
               char * string)
{
    SDL_Surface * surface = TTF_RenderText_Solid(font, string, color);
    SDL_Texture * texture = SDL_CreateTextureFromSurface(app->renderer, surface);

    SDL_Rect dest = {x, y, 0, 0};
    SDL_QueryTexture(texture, NULL, NULL, &(dest.w), &(dest.h));

    SDL_RenderCopy(app->renderer, texture, NULL, &dest);

    SDL_DestroyTexture(texture);
    SDL_FreeSurface(surface);
}

#define TEXT_LINE_MAX 256
char text_buffer[TEXT_LINE_MAX];

void draw_textf(struct App * app, int x, int y,
                TTF_Font * font, SDL_Color color,
                char * format, ...)
{
    memset(text_buffer, '\0', sizeof(text_buffer));

    va_list args;

    va_start(args, format);
    vsprintf(text_buffer, format, args);

    va_end(args);

    draw_text(app, x, y, font, color, text_buffer);
}



void draw_point(struct App * app, int x, int y, SDL_Color color) {
  SDL_SetRenderDrawColor(app->renderer, color.r, color.g, color.b, color.a);
  SDL_RenderDrawPoint(app->renderer, x, y);
}

void draw_line(struct App * app, int x1, int y1, int x2, int y2, SDL_Color color) {
  SDL_SetRenderDrawColor(app->renderer, color.r, color.g, color.b, color.a);
  SDL_RenderDrawLine(app->renderer, x1, y1, x2, y2);
}

void draw_polygon(struct App * app, float center_x, float center_y, float radius, int sides, float angle, SDL_Color color) {
    SDL_SetRenderDrawColor(app->renderer, color.r, color.g, color.b, color.a);

    int num_points = sides+1;
    SDL_FPoint * points = (SDL_FPoint *)malloc(sizeof(SDL_FPoint) * num_points);

    float segment_rad = (2*M_PI)/sides;
    for(int p = 0; p < num_points; p++) {
        points[p].x = center_x + (radius*cos((p*segment_rad) + angle));
        points[p].y = center_y + (radius*sin((p*segment_rad) + angle));
    }

    SDL_RenderDrawLinesF(app->renderer, points, num_points);
    free(points);
}

void draw_circle(struct App * app, float center_x, float center_y, float radius, SDL_Color color) {
    draw_polygon(app, center_x, center_y, radius, (int)(radius), 0.0, color);
}

void draw_triangle_center(struct App * app, float center_x, float center_y, float radius, float angle, SDL_Color color) {
    draw_polygon(app, center_x, center_y, radius, 3, angle, color);
}

void draw_rect(struct App * app, int x, int y, int w, int h, SDL_Color color) {
    SDL_SetRenderDrawColor(app->renderer, color.r, color.g, color.b, color.a);
    SDL_Rect drawrect = {x, y, w, h};
    SDL_RenderDrawRect(app->renderer, &drawrect);
}

void fill_rect(struct App * app, int x, int y, int w, int h, SDL_Color color) {
    SDL_SetRenderDrawColor(app->renderer, color.r, color.g, color.b, color.a);
    SDL_Rect drawrect = {x, y, w, h};
    SDL_RenderFillRect(app->renderer, &drawrect);
}

void draw_cursor(struct App * app, int x, int y, SDL_Color color) {
    SDL_SetRenderDrawColor(app->renderer, color.r, color.g, color.b, color.a);
    SDL_RenderDrawLine(app->renderer, x-10, y, x+10, y);
    SDL_RenderDrawLine(app->renderer, x, y-10, x, y+10);
}
