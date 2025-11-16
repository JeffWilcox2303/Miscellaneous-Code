#include <stdio.h>
#include "pico/stdlib.h"
#include "hardware/adc.h"
#include "hardware/uart.h"

const float conversion_factor = 3.3f / (1<<12);

int main()
{
    stdio_init_all();

    adc_init();

    adc_select_input(4);

    adc_set_temp_sensor_enabled(true);

    while (true) {
        uint16_t result = adc_read();
        // volatile float temp = 27.0f - (result*conversion_factor - 0.706f)/0.0011721f;
        printf("%d\n", (int) (27.0f - (result*conversion_factor - 0.706f)/0.0011721f));
        // printf("%d\n", result);
        sleep_ms(50);
    }
}
