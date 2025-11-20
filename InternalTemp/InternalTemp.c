#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/adc.h"
#include "hardware/uart.h"

const float conversion_factor = 3.3f / (1<<12);
int out = 16;
int adcread = 17;

int main()
{
    stdio_init_all();

    adc_init();

    adc_select_input(4);

    adc_set_temp_sensor_enabled(true);

    gpio_init(adcread);
    gpio_init(out);
    gpio_set_dir(out, true);
    gpio_set_dir(adcread, true);

    while (true) {
        gpio_put(adcread,true);
        uint16_t result = adc_read();
        gpio_put(adcread,false);
        // volatile float temp = 27.0f - (result*conversion_factor - 0.706f)/0.0011721f;
        sleep_ms(10);
        gpio_put(out,true);
        uint temp = (int) (27.0f - (result*conversion_factor - 0.706f)/0.0011721f);
        printf("%d\n", temp);
        gpio_put(out,false);
        // printf("%d\n", result);
        sleep_ms(10);
    }
}
