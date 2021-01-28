PROJECT = experiment

all: $(PROJECT)

SRC_DIR = ./src
BIN_DIR = ./bin

SRC = $(wildcard $(SRC_DIR)/*.c)
OBJECTS = $(patsubst %, $(BIN_DIR)/%, $(notdir $(SRC:.c=.o)))
DEPFILES = $(OBJECTS:.o=.d)

-include $(DEPFILES)

CC = g++
INCLUDE_DIRS = $(SRC_DIR) ./falcon_c
INCLUDE = $(patsubst %,-I%,$(INCLUDE_DIRS))

SDL2FLAGS = `sdl2-config --cflags`
CFLAGS = $(SDL2FLAGS) -Og -pg -Werror=implicit-function-declaration

SDL2LIBS = `sdl2-config --libs` -lSDL2_image -lSDL2_ttf -lSDL2_gfx
LFLAGS = -lm -lnifalcon

#generate dependency files
$(BIN_DIR)/%.d: $(SRC_DIR)/%.c
	@$(CC) $(CFLAGS) $(INCLUDE) $< -MM -MT $(@:.d=.o) >$@

#compile objects
$(BIN_DIR)/%.o :
	$(CC) -c $(INCLUDE) $< -o $@ $(CFLAGS)

#link project
$(PROJECT): $(OBJECTS)
	$(CC) -o $(BIN_DIR)/$(PROJECT) $(OBJECTS) $(LFLAGS) $(SDL2LIBS)

clean:
	rm -f $(BIN_DIR)/$(PROJECT) $(OBJECTS) $(DEPFILES)
