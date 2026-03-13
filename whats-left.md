While you finish wiring, send these when ready and I can implement hardware support immediately:

RFID model and interface type (SPI/I2C/UART) plus pin map.
rc522 - SPI is default
sda (cs) gpio8
sck gpio11
mosi gpio10
miso gpio9
irq - unconnected
gnd - gnd
rst - gpio25
3.3 volt



Keypad matrix size and row/column GPIOs.
4x4; 10 digits, a-d, #,*

Relay GPIO and active high vs active low.


Indicator GPIOs (LED and buzzer), plus any display details.


Any level shifters or 5V components in the chain.