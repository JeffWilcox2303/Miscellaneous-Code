#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/spi.h"
#include "math.h"

# define LED 25
bool light = true;
uint16_t configs = 0x3000;
uint16_t data = 0xFFFF;
uint16_t DAC_data;
uint16_t *regs;
uint16_t phase;
uint16_t phase_inc = 1365;
uint16_t sin_table[1024];
uint16_t Fs = 48000;
uint16_t threesixzero = 360;
uint16_t twofivesix = 256;

void freq(uint16_t Fout){
    // phase_inc = Fout/Fs*65536;
    phase_inc = 16*Fout*1.365333;
}

int main()
{
    regs = &DAC_data;
    stdio_init_all();
    
    gpio_set_function(18, GPIO_FUNC_SPI);
    gpio_set_function(19, GPIO_FUNC_SPI);
    gpio_set_function(17, GPIO_FUNC_SPI);

    gpio_init(LED);
    gpio_set_dir(LED,true);
    
    gpio_put(LED,light);

    spi_init(spi0, 48000);
    spi_set_format(spi0,16,SPI_CPOL_0,SPI_CPHA_0,SPI_MSB_FIRST);
    for(int i=0; i<1024; i++){
        sin_table[i] = (uint16_t)(2048*sin(i*0.006136)+2047);
    }
    
    int j = 1;

    freq(100);

    while (true) {
        gpio_put(LED,light);
        light = !light;
        // data = data << 1;
        // if (data == 0)
        // {
        //     data = 1;
        // }
        phase += phase_inc;
        // printf("%d\n", phase);
        data = sin_table[phase>>6];
        // printf("%f\n", sin_table[64]);
        DAC_data = (configs & 0xF000) | (data & 0x0FFF);
        spi_write16_blocking(spi0,regs,1);
        // j = j + 1;
        // printf("%lf %lf\n",sin(j*0.024543),sin_table[j]);
        // if(j > 256){
        //     j = 0;
        // }
        // sleep_ms(100);
    }
}
