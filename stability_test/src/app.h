#ifndef _MULTIAGENTEXP_APP_H_
#define _MULTIAGENTEXP_APP_H_

#include "SDL2/SDL.h"

struct App {
  SDL_Window * window;
  SDL_Renderer * renderer;

  int target_fps;

};


void App_init(struct App * app, int window_w, int window_h, int target_fps);
void App_exit(struct App * app);

#endif // _MULTIAGENTEXP_APP_H_
