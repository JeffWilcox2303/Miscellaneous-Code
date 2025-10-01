#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/spi.h"

# define LED 25
bool light = true;
uint16_t configs = 0x3000;
uint16_t data = 0xFFFF;
uint16_t DAC_data;
uint16_t *regs;

int main()
{
    regs = &DAC_data;
    stdio_init_all();
    gpio_init(LED);
    gpio_set_function(18, GPIO_FUNC_SPI);
    gpio_set_function(19, GPIO_FUNC_SPI);
    gpio_set_function(17, GPIO_FUNC_SPI) ;
    gpio_set_dir(LED,true);
    
    gpio_put(LED,light);

    spi_init(spi0, 20000);
    spi_set_format(spi0,16,SPI_CPOL_0,SPI_CPHA_0,SPI_LSB_FIRST);

    while (true) {
        gpio_put(LED,light);
        light = !light;
        // data_0 = data_0 << 1;
        // if (data_0 == 0)
        // {
        //     data_0 = 1;
        // }
        
        DAC_data = configs && 0xF000 || data && 0x0FFF;
        spi_write16_blocking(spi0,regs,16);
    }
}
