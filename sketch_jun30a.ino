unsigned long randNumber;
unsigned long t;
//bool sendNum = true;
//int incomingByte = 0;

void setup() {
  Serial.begin(9600);
  // if analog input pin 0 is unconnected, random analog
  // noise will cause the call to randomSeed() to generate
  // different seed numbers each time the sketch runs.
  // randomSeed() will then shuffle the random function.
  randomSeed(analogRead(0));
}

void loop() {

  randNumber = random(255);
  Serial.print(millis());
  Serial.print('\t');
  Serial.println(randNumber);
//      }
//      if (Serial.available() > 0) {
//        incomingByte = Serial.read();
//        sendNum = incomingByte;
//      }
  delay(10);
}
