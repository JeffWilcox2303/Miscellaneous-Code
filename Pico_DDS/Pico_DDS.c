#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/spi.h"
#include "hardware/timer.h"
#include "hardware/irq.h"
#include "math.h"

#define ALARM_NUM 0
#define TS 20 // Sample period in microseconds
# define LED 25 // GPIO LED
# define ISR_DBG 1 // ISR (Interrupt Service Routine) DBG (Debug) GPIO

bool light = true;
uint16_t configs = 0x3000;
uint16_t data = 0xFFFF;
uint16_t DAC_data;
uint16_t *regs;
uint16_t phase;
volatile uint16_t phase_inc = 131;
uint16_t sin_table[1024];
uint16_t Fs = 50000;
// uint16_t threesixzero = 360;
// uint16_t twofivesix = 256;

// Keeping memory of previous buton presses to update button state with debouncing
// The upper half tracks button 1 (gpio 2) and the lower half tracks button 0 (gpio 0)
// The LSB and MSB of each half is the current button gpio input value
// The second bit of each half is the previous button gpio input value
// The third bit of each half is the previous button state
uint8_t debounce = 0;
uint8_t state = 0;
uint16_t amp = 4095;

void freq(uint16_t Fout){
    phase_inc = 65536/Fs*Fout;
}

static void freq_select(void) {
    gpio_put(LED,state);
    if(state == 1){
        freq(200);
        // if(amp < 4095){
        //     amp += 1;
        // }
    }
    else if(state == 2){
        freq(275);
        // if(amp < 4095){
        //     amp += 1;
        // }
    }
    else{
        // if(amp > 0){
        //     amp -= 1;
        // }
        // else{
        //     phase = 0;
        //     phase_inc = 0;
        //     data = 0;
        // }
        phase_inc = 0;
        data = 0;
    }
}

static void alarm_irq(void) {
    // Set ISR GPIO high at beginning of interrupt for debugging
    gpio_put(ISR_DBG, true);
    
    // Clear the alarm IRQ
    hw_clear_bits(&timer_hw -> intr, 1u << ALARM_NUM);

    // Reset alarm register
    timer_hw -> alarm[ALARM_NUM] = timer_hw -> timerawl + TS;
   
    // In Progress, Smoothing out attack and fall off shape
    // if((state == 0) & (amp > 0)){
    //     amp -= 1;
    // }
    // else if(amp < 4095){
    //     amp += 1;
    // }
    // else{
    //     amp = amp;
    // }

    // Increment Phase
    phase += phase_inc;
    
    // Retrieve DAC bit data from phase
    data = sin_table[phase>>6];

    // Update configs and data in main DAC register for SPI transaction
    DAC_data = (configs & 0xF000) | (data & 0x0FFF);
    // (uint16_t)(data*amp)

    // Writing SPI Transaction
    spi_write16_blocking(spi0,regs,1);

    // Set ISR GPIO low at beginning of interrupt
    gpio_put(ISR_DBG, false);
}

// There's a different way of doing this using a state machine
// If this doesn't work, that could be something to investigate
static void update_button_state(void) {
    debounce = (debounce & 0xDD) | ((debounce << 1) & 0x22);
    debounce = (debounce & 0xEE) | !gpio_get(2) << 4 | !gpio_get(0);
    debounce = (debounce & 0x77) | ((debounce << 3) & 0x88);
    uint8_t middle = (debounce & debounce << 1);
    debounce = (debounce & 0xBB) | ((middle << 1 | middle | middle >> 1) & 0x44);
}

// This function handles FSM transitions and relies on post-debouncing button states
static void output_state(void) {
    uint8_t middle = (debounce & 0x44) >> 2;
    middle = ((middle >> 3) & 0x02) | (middle & 0x01);
    if(middle < 3u){
        state = middle;
    }
    else if(middle == 3u){
        state = state;
    }
    else{
        state = 0;
    }
}

int main()
{
    // Linking pointer to DAC data for SPI writes
    regs = &DAC_data;

    // Initialize standard IO
    stdio_init_all();

    // Setup Button Inputs
    gpio_init(0);
    gpio_init(2);
    gpio_pull_up(0);
    gpio_pull_up(2);
    gpio_set_dir(0,false);
    gpio_set_dir(2,false);
    
    // Setup SPI bus
    gpio_set_function(18, GPIO_FUNC_SPI);
    gpio_set_function(19, GPIO_FUNC_SPI);
    gpio_set_function(17, GPIO_FUNC_SPI);

    // Initialize LED GPIO
    gpio_init(LED);
    gpio_set_dir(LED,true);
    gpio_put(LED,light);

    // Setup SPI properties
    spi_init(spi0, 20000000);
    spi_set_format(spi0,16,SPI_CPOL_0,SPI_CPHA_0,SPI_MSB_FIRST);

    // Create a sine table to transform phase to amplitude
    for(int i=0; i<1024; i++){
        sin_table[i] = (uint16_t)(2048*sin(i*0.006136)+2047);
    }

    // Enable alarm interrupt
    hw_set_bits(&timer_hw->inte, 1u << ALARM_NUM);

    // Set IRQ handler to the alarm_irq function
    irq_set_exclusive_handler(TIMER_IRQ_0,alarm_irq);

    // Enable IRQ for alarm 0
    irq_set_enabled(TIMER_IRQ_0,true);
    
    // Set the alarm time and arm it
    timer_hw -> alarm[ALARM_NUM] = timer_hw -> timerawl + TS;    
    
    while (true) {
        update_button_state();
        output_state();
        freq_select();
        // printf("%d\n", (uint16_t)(((double)data)*amp));
        // printf("%d\n", data);
    }
}
