#include "app.h"

#include <assert.h>

#include "SDL2/SDL.h"

void App_init(struct App * app, int window_w, int window_h, int target_fps) {

    assert(SDL_Init(SDL_INIT_VIDEO) == 0);

    app->window = SDL_CreateWindow("EXPERIMENT",
                                   SDL_WINDOWPOS_UNDEFINED, SDL_WINDOWPOS_UNDEFINED,
                                   window_w, window_h, 0);
    app->renderer = SDL_CreateRenderer(app->window, -1, 0);
}


void App_exit(struct App * app) {
    SDL_DestroyRenderer(app->renderer);
    SDL_DestroyWindow(app->window);
    SDL_Quit();
}
