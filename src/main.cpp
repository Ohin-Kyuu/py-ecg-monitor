#include <Arduino.h>

#define BAUD_RATE 115200 

volatile int adcValue = 0;
volatile bool received = false;

void setupTimer() {
  cli();                  
  TCCR1A = 0; TCCR1B = 0; TCNT1  = 0;
  OCR1A = 3999; // 500Hz           
  TCCR1B |= (1 << WGM12);  
  TCCR1B |= (1 << CS11);  
  TIMSK1 |= (1 << OCIE1A); 
  sei();
}

ISR(TIMER1_COMPA_vect) {
  adcValue = analogRead(A0); 
  received = true;
}

void setup() {
  Serial.begin(BAUD_RATE);
  pinMode(A0, INPUT);
  setupTimer();
}

void loop() {
  if (received) {
    received = false;
    Serial.println(adcValue); 
  }
}