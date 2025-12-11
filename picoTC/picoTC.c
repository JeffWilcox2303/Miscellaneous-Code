#include <stdio.h>
// #include <pthread.h>
#include "pico/stdlib.h"
#include "hardware/spi.h"
#include "hardware/timer.h"
#include "hardware/irq.h"

// Libraries for protothreads
#include <string.h>
#include "pico/multicore.h"
#include "pt_cornell_rp2040_v1_3.h"

#define TC_ALARM 0
#define TS 300000 // Sample period in microseconds

#define CTRL_ALARM 1
#define TCTRL 20 // Sample period in microseconds

#define READ_ALARM 2
#define TREAD 20 // Sample period in microseconds

// SPI Defines
// We are going to use SPI 0, and allocate it to the following GPIO pins
// Pins can be changed, see the GPIO function select table in the datasheet for information on GPIO assignments
#define SPI_PORT spi0
#define PIN_MISO 16
#define PIN_CS   17
#define PIN_SCK  18
#define PIN_MOSI 19
#define GPIO_OUTPUT true
#define GPIO_INPUT false

// Fixed point macros
// Adapted from Hunter Adams Microcontrollers course at Cornell University
typedef signed int fix15;
#define multfix15(a, b) ((fix15)((((signed long long)(a)) * ((signed long long)(b))) >> 15))
#define float2fix15(a) ((fix15)((a) * 32768.0)) // 2^15
#define fix2float15(a) ((float)(a) / 32768.0)
#define absfix15(a) abs(a)
#define int2fix15(a) ((fix15)(a << 15))
#define fix2int15(a) ((int)(a >> 15))
#define char2fix15(a) (fix15)(((fix15)(a)) << 15)
#define divfix(a, b) (fix15)(div_s64s64((((signed long long)(a)) << 15), ((signed long long)(b))))

uint16_t *regs;
uint16_t TC_data;
uint16_t *dummy;
uint16_t dummy_write = 0x0000;
volatile uint16_t temp;
// volatile fix15 setpoint = int2fix15(30);
uint16_t setpoint = 30;
volatile uint8_t state = 0;
uint32_t begin_state;
uint32_t current_time;
// static fix15 plateau0 = int2fix15(30);
// static fix15 plateau1 = int2fix15(150);
// static fix15 plateau2 = int2fix15(250);
static uint16_t plateau0 = 30;
static uint16_t plateau1 = 150;
static uint16_t plateau2 = 250;

static void tc_alarm(void) {
   // Clear the alarm IRQ
    hw_clear_bits(&timer_hw -> intr, 1u << TC_ALARM);

    // Reset alarm register
    timer_hw -> alarm[TC_ALARM] = timer_hw -> timerawl + TS;
   
    // Writing SPI Transaction
    spi_read16_blocking(spi0,dummy_write,regs,1);
    printf("%d,%d\n", ((TC_data&0x7FF8) >> 3), setpoint);
}

static void ctrl_alarm(void) {
   // Clear the alarm IRQ
    hw_clear_bits(&timer_hw -> intr, 1u << CTRL_ALARM);

    // Reset alarm register
    timer_hw -> alarm[CTRL_ALARM] = timer_hw -> timerawl + TCTRL;
   
    // Compare measured temperature to setpoint

    // Converted TC_data to temperature
    temp = (TC_data & 0x7FF8) >> 3;

    // Check state/time and update setpoint/state as needed
    if(state == 0){
        state = 1;
        gpio_put(25,true);
        begin_state = time_us_32();
        gpio_put(25,false);
    }
    else if(state == 1){
        current_time = time_us_32();
        setpoint = plateau0 + 2*(current_time - begin_state)/1000000;
        if(setpoint >= plateau1){
            state = 2;
            setpoint = plateau1;
            begin_state = time_us_32();
        }
    }
    else if(state == 2){
        current_time = time_us_32();
        if(current_time - begin_state >= 100000000){
            state = 3;
            begin_state = time_us_32();
        }
    }
    else if(state == 3){
        current_time = time_us_32();
        setpoint = plateau1 + 2*(current_time - begin_state)/1000000;
        if(setpoint >= plateau2){
            state = 4;
            setpoint = plateau2;
            begin_state = time_us_32();
        }
    }
    else if(state == 4){
        current_time = time_us_32();
        if(current_time - begin_state >= 60000000){
            state = 5;
            begin_state = time_us_32();
        }
    }
    else if(state == 5){
        current_time = time_us_32();
        setpoint = plateau2 - 4*(current_time - begin_state)/1000000;
        if(setpoint <= plateau0){
            state = 0;
            setpoint = plateau0;
        }
    }

    // Set SSR based on setpoint and state
    if(temp < (setpoint << 2)){
        gpio_put(25,true);
    }
    else{
        gpio_put(25,false);
    }
}

// static void read_alarm(void) {
//    // Clear the alarm IRQ
//     hw_clear_bits(&timer_hw -> intr, 1u << READ_ALARM);

//     // Reset alarm register
//     timer_hw -> alarm[READ_ALARM] = timer_hw -> timerawl + TREAD;
// }

int main()
{
    stdio_init_all();

    regs = &TC_data;
    dummy = &dummy_write;

    // SSR Level Shift Test
    gpio_init(15);
    gpio_set_dir(15, GPIO_OUTPUT);
    gpio_set_drive_strength(15,GPIO_DRIVE_STRENGTH_12MA);
    // gpio_pull_down(15); // Dumb hardware design - if you reflash the board, the SSR will be default ON
    gpio_put(15,false);

    // LED for debug
    gpio_init(25);
    gpio_set_dir(25, GPIO_OUTPUT);
    gpio_put(25,false);

    // SPI initialisation. This example will use SPI at 1MHz.
    gpio_set_function(PIN_MISO, GPIO_FUNC_SPI);
    gpio_set_function(PIN_CS,   GPIO_FUNC_SPI);
    gpio_set_function(PIN_SCK,  GPIO_FUNC_SPI);
    gpio_set_function(PIN_MOSI, GPIO_FUNC_SPI);

    spi_init(SPI_PORT, 1000*1000);
    spi_set_format(spi0,16,SPI_CPOL_0,SPI_CPHA_1,SPI_MSB_FIRST);
    
    // // Chip select is active-low, so we'll initialise it to a driven-high state
    // gpio_set_dir(PIN_CS, GPIO_OUT);
    // gpio_put(PIN_CS, 1);
    // For more examples of SPI use see https://github.com/raspberrypi/pico-examples/tree/master/spi

    // Enable alarm interrupt for TC read
    hw_set_bits(&timer_hw->inte, 1u << TC_ALARM);
    // Set IRQ handler to the alarm_irq function
    irq_set_exclusive_handler(TIMER_IRQ_0, tc_alarm);
    // Enable IRQ for alarm 0
    irq_set_enabled(TIMER_IRQ_0,true);
    // Set the alarm time and arm it
    timer_hw -> alarm[TC_ALARM] = timer_hw -> timerawl + TS;

    // Enable alarm interrupt for setpoint comparison
    hw_set_bits(&timer_hw->inte, 1u << CTRL_ALARM);
    // Set IRQ handler to the alarm_irq function
    irq_set_exclusive_handler(TIMER_IRQ_1, ctrl_alarm);
    // Enable IRQ for alarm 0
    irq_set_enabled(TIMER_IRQ_1,true);
    // Set the alarm time and arm it
    timer_hw -> alarm[CTRL_ALARM] = timer_hw -> timerawl + TCTRL;

    // // Enable alarm interrupt to read from computer
    // hw_set_bits(&timer_hw->inte, 1u << READ_ALARM);
    // // Set IRQ handler to the alarm_irq function
    // irq_set_exclusive_handler(TIMER_IRQ_2, read_alarm);
    // // Enable IRQ for alarm 0
    // irq_set_enabled(TIMER_IRQ_2,true);
    // // Set the alarm time and arm it
    // timer_hw -> alarm[READ_ALARM] = timer_hw -> timerawl + TREAD;

    while (true) {
        // printf("%d\n", temp);
    }
}
