# Blackbox Custom Firmware Build System
# Usage:
#   make              — build firmware
#   make flash-swd    — flash via SWD debug probe
#   make flash-sd     — copy to SD card for bootloader update
#   make disasm       — disassemble the output
#   make size         — show memory usage
#   make clean        — clean build artifacts

# --- Toolchain ---
PREFIX  = arm-none-eabi-
CC      = $(PREFIX)gcc
CXX     = $(PREFIX)g++
AS      = $(PREFIX)gcc -x assembler-with-cpp
LD      = $(PREFIX)gcc
OBJCOPY = $(PREFIX)objcopy
OBJDUMP = $(PREFIX)objdump
SIZE    = $(PREFIX)size

# --- Target ---
TARGET  = blackbox-custom
BUILD   = build

# --- MCU flags ---
CPU     = -mcpu=cortex-m7
FPU     = -mfpu=fpv5-d16 -mfloat-abi=hard
MCU     = $(CPU) -mthumb $(FPU)

# --- Sources ---
C_SOURCES   = $(wildcard src/*.c)
CXX_SOURCES = $(wildcard src/*.cpp)
ASM_SOURCES = startup/startup_stm32h750.s

# --- Linker script ---
LDSCRIPT = linker/STM32H750_APP.ld

# --- Includes ---
C_INCLUDES = -Iinclude

# --- Compiler flags ---
OPT = -O2
CFLAGS  = $(MCU) $(C_INCLUDES) $(OPT)
CFLAGS += -Wall -Wextra -Wno-unused-parameter
CFLAGS += -fdata-sections -ffunction-sections
CFLAGS += -fno-common
CFLAGS += -DSTM32H750xx

CXXFLAGS  = $(CFLAGS)
CXXFLAGS += -fno-rtti -fno-exceptions

ASFLAGS = $(MCU) -Wall -fdata-sections -ffunction-sections

# --- Linker flags ---
LDFLAGS  = $(MCU)
LDFLAGS += -T$(LDSCRIPT)
LDFLAGS += -Wl,--gc-sections
LDFLAGS += -Wl,-Map=$(BUILD)/$(TARGET).map,--cref
LDFLAGS += --specs=nosys.specs
LDFLAGS += --specs=nano.specs
LDFLAGS += -lc -lm -lnosys

# --- Objects ---
OBJECTS  = $(addprefix $(BUILD)/, $(notdir $(C_SOURCES:.c=.o)))
OBJECTS += $(addprefix $(BUILD)/, $(notdir $(CXX_SOURCES:.cpp=.o)))
OBJECTS += $(addprefix $(BUILD)/, $(notdir $(ASM_SOURCES:.s=.o)))

vpath %.c $(sort $(dir $(C_SOURCES)))
vpath %.cpp $(sort $(dir $(CXX_SOURCES)))
vpath %.s $(sort $(dir $(ASM_SOURCES)))

# --- Rules ---
.PHONY: all clean flash-swd flash-sd disasm size

all: $(BUILD)/$(TARGET).bin $(BUILD)/$(TARGET).hex
	@echo ""
	@echo "=== Build complete ==="
	@echo "  BIN: $(BUILD)/$(TARGET).bin ($(shell wc -c < $(BUILD)/$(TARGET).bin 2>/dev/null || echo '?') bytes)"
	@echo "  HEX: $(BUILD)/$(TARGET).hex"
	@echo ""
	@$(SIZE) $(BUILD)/$(TARGET).elf

$(BUILD)/%.o: %.c | $(BUILD)
	$(CC) -c $(CFLAGS) $< -o $@

$(BUILD)/%.o: %.cpp | $(BUILD)
	$(CXX) -c $(CXXFLAGS) $< -o $@

$(BUILD)/%.o: %.s | $(BUILD)
	$(AS) -c $(ASFLAGS) $< -o $@

$(BUILD)/$(TARGET).elf: $(OBJECTS)
	$(LD) $(OBJECTS) $(LDFLAGS) -o $@

$(BUILD)/$(TARGET).bin: $(BUILD)/$(TARGET).elf
	$(OBJCOPY) -O binary -S $< $@

$(BUILD)/$(TARGET).hex: $(BUILD)/$(TARGET).elf
	$(OBJCOPY) -O ihex $< $@

$(BUILD):
	mkdir -p $@

clean:
	rm -rf $(BUILD)

# --- Flash via SWD (ST-Link or J-Link) ---
flash-swd: $(BUILD)/$(TARGET).bin
	@echo "Flashing via SWD to 0x08040000..."
	STM32_Programmer_CLI -c port=SWD -w $< 0x08040000 -v -rst

# --- Copy to SD card for bootloader update ---
# Adjust the volume name to match your SD card mount point
SD_VOLUME = /Volumes/BLACKBOX
flash-sd: $(BUILD)/$(TARGET).bin
	@if [ ! -d "$(SD_VOLUME)" ]; then \
		echo "Error: SD card not mounted at $(SD_VOLUME)"; \
		echo "Insert SD card or set SD_VOLUME=<mount_point>"; \
		exit 1; \
	fi
	cp $< "$(SD_VOLUME)/BLACKBOX.BIN"
	@echo "Copied to $(SD_VOLUME)/BLACKBOX.BIN"
	@echo "Safely eject the SD card, insert into Blackbox, and power on."

# --- Disassemble ---
disasm: $(BUILD)/$(TARGET).elf
	$(OBJDUMP) -d -S -C $< > $(BUILD)/$(TARGET).disasm
	@echo "Disassembly: $(BUILD)/$(TARGET).disasm"

# --- Memory usage ---
size: $(BUILD)/$(TARGET).elf
	$(SIZE) --format=berkeley $<
	$(SIZE) --format=sysv $<
