#include <stdio.h>
#include <stdlib.h>
#include <signal.h>
#include <time.h>

#include "SDL2/SDL.h"
#include "SDL2/SDL_ttf.h"

#include "falcon_c.h"

#include "app.h"
#include "draw.h"

bool stop = false;
void sigproc(int i)
{
    if(!stop)
    {
        stop = true;
        printf("Quitting\n");
    }
    else exit(0);
}



float signum(float value) {
    if (value > 0.0) {
        return 1.0;
    } else if (value < 0.0) {
        return -1.0;
    } else {
        return 0.0;
    }
}


struct timespec start_time; 
void time_init() {
    timespec_get(&start_time, TIME_UTC);
}

float time_now_ms() {
    struct timespec time_now;
    timespec_get(&time_now, TIME_UTC);

    float elapsed_ms = 1000.0*time_now.tv_sec + 1e-6*time_now.tv_nsec
                     - (1000.0*start_time.tv_sec + 1e-6*start_time.tv_nsec);
    return elapsed_ms;
}

int time_delay_framerate(int target_framerate) {
    const int avg_period_ms = 2000;

    static uint32_t fps = 0;
    static uint32_t fps_frame_count = 0;
    static uint32_t last_time = 0;

    static uint64_t frame_count = 0;
    uint64_t frames = (time_now_ms() * target_framerate) / 1000;
    if(target_framerate > 0)
        while(frame_count > frames) {
            frames = (time_now_ms() * target_framerate) / 1000;
        }
    frame_count++;


    uint32_t time_now = ((int)time_now_ms()) % avg_period_ms;
    if(time_now < last_time) {
        fps = ((float)fps_frame_count * 1000.0) / avg_period_ms;
        fps_frame_count = 0;
    }

    last_time = time_now;
    fps_frame_count++;

    return fps;
}

struct DynObj {
    float mass;
    float pos;
    float vel;
    float accel;

    float force;
    float queued_force;
};


void DynObj_step(struct DynObj * obj, float dt_s) {

    obj->force = obj->queued_force;
    if(obj->mass > 0.0) {
        obj->accel = (obj->force / obj->mass);
    }
    obj->vel += obj->accel * dt_s;
    obj->pos += obj->vel * dt_s;
    obj->queued_force = 0.0;
}


void damping(struct DynObj * target, float b) {
    float force = target->vel * -b;
    target->queued_force += force;
}

void bind_position(struct DynObj * target, struct DynObj * reference,
                   float offset, float proportion) {

    target->pos = (reference->pos * proportion) + offset;
}


void spring_law_solid(struct DynObj * target, struct DynObj * reference,
                      float spring_coeff, float offset) {

    float penetration = (reference->pos + offset) - target->pos;

    if(signum(penetration) == signum(spring_coeff)) {
        float force = signum(spring_coeff) * penetration * spring_coeff;
        target->queued_force += force;
    }
}


int main(int argc, char *argv[]) {

    signal(SIGINT, sigproc);
    time_init();


    void * p1_falcon_ref = falcon_init(0);
    //void * p2_falcon_ref = falcon_init(1);
    printf("init\n");
    int error1 = falcon_load_firmware(p1_falcon_ref, "firmware/novint_T2.bin");
    printf("firmware %d\n", error1);

    //int error2 = falcon_load_firmware(p2_falcon_ref, "firmware/novint_T2.bin");
    //printf("firmware %d\n", error2);

    struct DynObj p1_handle = {.pos = -1.0};
    struct DynObj p2_handle = {.pos = 1.0};
    struct DynObj cursor = {.mass = 0.1};


    const float z_min = 0.075;
    const float z_max = 0.175;
    const float z_range =  z_max - z_min;
    const float p1_offset = (z_min + z_max) / 2.0;
    const float p1_scale = z_range / 2.0;
    const float p2_offset = (z_min + z_max) / 2.0;
    const float p2_scale = z_range / 2.0;


    struct App app = {0};
    App_init(&app, 640, 640, 1000);


    TTF_Init();
    TTF_Font * font = TTF_OpenFont("LiberationMono-Regular.ttf", 25);
    SDL_Color font_color = { 255, 255, 255 };

    const int target_fps = 1600;
    int fps = 0;
    while(!stop) {

        error1 = falcon_run_io_loop(p1_falcon_ref);
        //error2 = falcon_run_io_loop(p2_falcon_ref);

        p1_handle.pos = ((falcon_get_pos_z(p1_falcon_ref) - p1_offset) / p1_scale);
        //p2_handle.pos = -1.0 * ((falcon_get_pos_z(p2_falcon_ref) - p2_offset) / p2_scale);

        printf("%dFPS - %4.2f %4.2f - %4.2f\n", fps, p1_handle.pos, p2_handle.pos, cursor.pos);

        const float k = 5.0;
        const float obj_radius = 0.05;
        const float spring_loss = 0.9;
        const float p1_push = 1.0;
        const float p1_pull = 1.0;
        const float p2_push = 1.0;
        const float p2_pull = 1.0;

        spring_law_solid(&p1_handle, &cursor, -k, -(obj_radius * 2.0));
        spring_law_solid(&cursor, &p1_handle, k * spring_loss * p1_push, (obj_radius * 2.0));
        spring_law_solid(&p1_handle, &cursor, k, (obj_radius * 2.0));
        spring_law_solid(&cursor, &p1_handle, -k * spring_loss * p1_pull, -(obj_radius * 2.0));

        //spring_law_solid(&p2_handle, &cursor, k, (obj_radius * 2.0));
        //spring_law_solid(&cursor, &p2_handle, -k * spring_loss * p2_push, -(obj_radius * 2.0));
        //spring_law_solid(&p2_handle, &cursor, -k, -(obj_radius * 2.0));
        //spring_law_solid(&cursor, &p2_handle, k * spring_loss * p2_pull, (obj_radius * 2.0));

        damping(&cursor, 0.1);

        float dt_s = 1.0 / target_fps;
        DynObj_step(&cursor, dt_s);

        falcon_set_force(p1_falcon_ref, 0.0, 0.0, p1_handle.queued_force);
        p1_handle.force = p1_handle.queued_force;
        p1_handle.queued_force = 0.0;

        //falcon_set_force(p2_falcon_ref, 0.0, 0.0, -p2_handle.queued_force);
        //p2_handle.force = p2_handle.queued_force;
        //p2_handle.queued_force = 0.0;


        fps = time_delay_framerate(target_fps);

        SDL_RenderClear(app.renderer);

        for(int i = 0; i < 50; i++) {
            draw_textf(&app, 0, i * 10, font, font_color, "%dFPS", fps);
        }

        SDL_RenderPresent(app.renderer);
    }

    falcon_exit(p1_falcon_ref);
    //falcon_exit(p2_falcon_ref);

    TTF_CloseFont(font);
    TTF_Quit();


    App_exit(&app);

    return 0;
}
