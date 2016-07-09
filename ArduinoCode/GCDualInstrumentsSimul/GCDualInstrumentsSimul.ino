/*
  GC Analog Input
 This serves as a simple data capture routine from a
 1.0 V serial output of HP 5890 Series II gas chromatograph.

 Current Version: Implements interrupt for stop button.

 The circuit:
 See Frizzing diagram for description of circuit.  

 Uses Adafruit breakout of ADS1115 Texas Instruments 16-Bit ADC

 Two different analog signals from GCs can be accommodated, but not simultaneously 

 Each signal has a separate Start/Stop Button
  Signal 1
    A0 input on ADS1115
    Start button on IO pin 9
    Stop button on IO pin 8
    Greed LED on IO pin 10
   Signal 2
    A1 input on ADS1115
    Start button on IO pin 3
    Stop button on IO pin 2
    Greed LED on IO pin 4 

 Based upon Analog Input Example Created by David Cuartielles
 modified 30 Aug 2011
 By Tom Igoe

 GCDualInstruments code written by T. Andrew Mobey, 7 Jun 2016
 based upon GCTry5 code

 Known Issues:
  1) If one Channel is still collecting data, second channel can be restarted even if mode is not multiple.

 */
#include <Wire.h>
#include <Adafruit_ADS1015.h>

Adafruit_ADS1115 ads1115(0x4B); // construct an ads1115 at address 0x4B (ADDR connected to SCL)

String channel = "1";          // Default to signal 1
int sensorPin1 = A0;       // input pin for the GC (signal 1)
int ledPin1 = 6;           // output pin for the LED (signal 1)
int sensorPin2 = A1;       // input pin for the GC (signal 1)
int ledPin2 = 5;           // output pin for the LED (signal 1)
float sensorValue1 = 0;    // stores the analog signal potential coming from the GC
float sensorValue2 = 0;    // stores the analog signal potential coming from the GC
float timeValue1 = 0;      // stores the current time
float beginTime1 = 0 ;     // indicate time when the experiment started
float timeValue2 = 0;      // stores the current time
float beginTime2 = 0 ;     // indicate time when the experiment started
boolean writeData1=true;   // whether data should be sent to PC
boolean writeData2=true;   // whether data should be sent to PC
boolean firsttime1=true;   // indicate whether this is the first data point taken (used to set beginTime)
boolean firsttime2=true;   // indicate whether this is the first data point taken (used to set beginTime)
boolean started1=false;    // indicates whether experiment is started yet
boolean stopped1=true;    // indicates whether experiment has been stopped by button
boolean started2=false;    // indicates whether experiment is started yet
boolean stopped2=true;    // indicates whether experiment has been stopped by button
int startButton1=9;        // input pin number for start button (default signal 1)
int stopButton1=3;         // interrupt for stop button (default signal 1)
float timeExper1=0;        // time length of experiment
boolean multiple1=false;
int startButton2=8;        // input pin number for start button (default signal 1)
int stopButton2=2;         // interrupt for stop button (default signal 1)
float timeExper2=0;        // time length of experiment
boolean multiple2=false;
boolean multSet=false;
String startString1="stopped";
String startString2="stopped";
float holdTime = 0.;
String adcChoice="";

void setup() {

  pinMode (ledPin1, OUTPUT);       // declare the various pins utilized as input/output
  pinMode (startButton1, INPUT);
  attachInterrupt (digitalPinToInterrupt(stopButton1), listenForStop, RISING);
  pinMode (sensorPin1, INPUT);

  pinMode (ledPin2, OUTPUT);       // declare the various pins utilized as input/output
  pinMode (startButton2, INPUT);
  attachInterrupt (digitalPinToInterrupt(stopButton2), listenForStop, RISING);
  pinMode (sensorPin2, INPUT);

  
  Serial.begin(57600);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB port only
  }

  ads1115.begin(); // Initialize ads1115
  ads1115.setGain(GAIN_FOUR);
  
  analogReference(INTERNAL);    //Sets analog reference to the Internal 1.1V reference
  
  for (int i=0;i<5;i++){        //Read the analog pin several times to allow it to settle down
     analogRead(sensorPin1);     //after changing the analogReference to internal
  }
  for (int i=0;i<5;i++){        //Read the analog pin several times to allow it to settle down
     analogRead(sensorPin2);     //after changing the analogReference to internal
  }
  
  getExperTime();               //Receive details of experiment from the PC, routine will
                                //wait until it hears from PC
  
  listenForStart();             // Wait until start button is pushed on Arduino
    
}

void loop() {
  if (Serial.available()>0){
    getExperTime();
  }
  
  checkStart();
  
  readGCDataAnalog(adcChoice);
  
  checkTimeOver();
 
  writeDataOrWriteQuit();
  
  if (stopped1&&stopped2){
    resetAndWaitForRestart();
  }
  
  delay(97);  // wait for 97 milliseconds + 3 msec for other routine for ~100 msec recycle time
}

//Procedures to be called

void readGCDataAnalog(String adcCh){
  // reads in analog sensor from gc

  float intervalue=0.;
  float time1=0;
  float time2=0;

  if (started1){
    if (firsttime1){
      beginTime1=millis()/60000.;
      timeValue1=beginTime1;
      firsttime1=false;
    }
    time1=millis();
    for (int i=0;i<10;i++){
      if (adcCh == "arduino"){
        intervalue=intervalue+analogRead(sensorPin1);
      }
      else if (adcCh =="ads1115"){
        intervalue=intervalue+ads1115.readADC_SingleEnded(0);
      }
    }
    time2=millis();
    sensorValue1 = intervalue/10.;
    if (adcCh == "arduino"){
      sensorValue1 = sensorValue1*1.1/1024;
    }
    else if (adcCh == "ads1115"){
      sensorValue1 = sensorValue1*0.00003125;
    }
    else{
      Serial.println("Bad adcCh");
    }
    timeValue1 = ((time1+time2)/120000)-beginTime1;
  }
  
  if (started2){
    intervalue=0;
 
    if (firsttime2){
      beginTime2=millis()/60000.;
      timeValue2=beginTime2;
      firsttime2=false;
    }
    time1=millis();
    for (int i=0;i<10;i++){
      if (adcCh == "arduino"){
        intervalue=intervalue+analogRead(sensorPin2);
      }
      else if (adcCh =="ads1115"){
        intervalue=intervalue+ads1115.readADC_SingleEnded(1);
      }
    }
    time2=millis();
    sensorValue2 = intervalue/10.;
    if (adcCh == "arduino"){
      sensorValue2 = sensorValue2*1.1/1024;
    }
    else if (adcCh == "ads1115"){
      sensorValue2 = sensorValue2*0.00003125;
    }
    timeValue2 = ((time1+time2)/120000)-beginTime2;
  }
}

void getExperTime(){        // This routine retrieves the experimental time number from PC 
  String multString="";
  String startString="";
  while (multString == ""){
    while (Serial.available()<1){}            // Waiting on PC to deliver string.
    multString = Serial.readStringUntil(' ');   // Collect various information from computer: 
    adcChoice = Serial.readStringUntil(' ');
    startString = Serial.readStringUntil(' ');
    channel = Serial.readStringUntil(' ');
  }  
  if (channel == "1"){
//    if (multString == "multiple"){
//      multiple1 = true;
//    }
//    else{
//      multiple1 = false; 
//    }
    startString1 = startString;
    String inString="";
    int inChar=0;
    while (timeExper1==0){                 //This section of code was adopted from 
      while (Serial.available() > 0){    //StringToFloat example on Arduino site
        inChar = Serial.read();
        if (inChar != '\n') { 
          // As long as the incoming byte
          // is not a newline,
          // convert the incoming byte to a char
          // and add it to the string
          if (inChar==46){
            inString=inString+".";
          }
          else{
            inString =inString + String(inChar-48);
          }
        }
        else {
          timeExper1=inString.toFloat();
        }
      }
    }
  }
  else if (channel == "2"){
//    if (multString == "multiple"){
//      multiple2 = true;
//    }
//    else{
//      multiple2 = false; 
//    }
    startString2 = startString;
    String inString="";
    int inChar=0;
    while (timeExper2==0){                 //This section of code was adopted from 
      while (Serial.available() > 0){    //StringToFloat example on Arduino site
        inChar = Serial.read();
        if (inChar != '\n') { 
          // As long as the incoming byte
          // is not a newline,
          // convert the incoming byte to a char
          // and add it to the string
          if (inChar==46){
            inString=inString+".";
          }
          else{
            inString =inString + String(inChar-48);
          }
        }
        else {
          timeExper2=inString.toFloat();
        }
      }
    }
  }
}

void listenForStart(){
   while(!started1&&!started2){
      delay(50);
      if(digitalRead(startButton1)==HIGH&&startString1!="stopped"){
        started1=true;
        stopped1=false;
        digitalWrite(ledPin1,HIGH);
        Serial.print(startString1);
        Serial.print(" ");
        Serial.println("stopped");
      }
      if(digitalRead(startButton2)==HIGH&&startString2!="stopped"){
        started2=true;
        stopped2=false;
        digitalWrite(ledPin2,HIGH);
        Serial.print("stopped");
        Serial.print(" ");
        Serial.println(startString2);
      }
      if (started1||started2){
        break;
      }
   } 
}

void checkStart(){
    if(digitalRead(startButton1)==HIGH&&!started1){
      started1=true;
      stopped1=false;
      writeData1=true;
      digitalWrite(ledPin1,HIGH);
    }
    if(digitalRead(startButton2)==HIGH&&!started2){
      started2=true;
      stopped2=false;
      writeData2=true;
      digitalWrite(ledPin2,HIGH);
    }
}

void listenForStop(){
    if(digitalRead(stopButton1)==HIGH){
      stopped1=true;
      timeExper1=0;
      timeValue1=0;
      writeData1=false;
//      sensorValue1=0;
      firsttime1=true;
      digitalWrite(ledPin1,LOW);
    }
    if(digitalRead(stopButton2)==HIGH){
      stopped2=true;
      timeExper2=0;
      timeValue2=0;
      writeData2=false;
//      sensorValue2=0;
      firsttime2=true;
      digitalWrite(ledPin2,LOW);
    }
}

void checkTimeOver(){
  if (timeValue1>timeExper1){
    writeData1=false;
    stopped1=true;
//    timeValue1=0;
//    sensorValue1=0;
    firsttime1=true;
    digitalWrite(ledPin1,LOW);
  }
  if (timeValue2>timeExper2){
    writeData2=false;
    stopped2=true;
//    timeValue2=0;
//    sensorValue2=0;
    firsttime2=true;
    digitalWrite(ledPin2,LOW);
  }
}

void writeDataOrWriteQuit(){
  if ((writeData1&&started1)&&(writeData2&&started2)) {
    Serial.print(startString1);
    Serial.print(" ");
    Serial.print(startString2);
    Serial.print(" ");
    Serial.print(timeValue1,5);
    Serial.print(" ");
    Serial.print(sensorValue1,8);
    Serial.print(" ");
    Serial.print(timeValue2,5);
    Serial.print(" ");
    Serial.println(sensorValue2,8);
  }
  else if (writeData1&&started1) {
    Serial.print(startString1);
    Serial.print(" ");
    Serial.print("stopped");
    Serial.print(" ");
    Serial.print(timeValue1,5);
    Serial.print(" ");
    Serial.print(sensorValue1,8);
    Serial.print(" ");
    Serial.print("q");
    Serial.print(" ");
    Serial.println("q");
  }
  else if (writeData2&&started2) {
    Serial.print("stopped");
    Serial.print(" ");
    Serial.print(startString2);
    Serial.print(" ");
    Serial.print("q");
    Serial.print(" ");
    Serial.print("q");
    Serial.print(" ");
    Serial.print(timeValue2,5);
    Serial.print(" ");
    Serial.println(sensorValue2,8);
  }
  else if (stopped1&&stopped2) {
    Serial.print("stopped stopped ");
    Serial.println("q q q q");
  }
  if (stopped1){
    started1=false;
  }
  if (stopped2){
    started2=false;
  }
}

void resetAndWaitForRestart(){
//    Serial.print("stopped stopped ");
//    Serial.println("q q q q");
//  if (!multiple1&&!multiple2){
//    timeExper1=0;
//    timeExper2=0;
//    getExperTime();
//  }
  firsttime1=true;
  timeValue1=0;
  writeData1=true;
  firsttime2=true;
  timeValue2=0;
  writeData2=true;
  getExperTime();
  listenForStart();
//  while (stopped1&&stopped2){
//    if(digitalRead(startButton1)==HIGH){
//      started1=true;
//      stopped1=false;
//      digitalWrite(ledPin1,HIGH);
//      Serial.print(startString1);
//      Serial.print(" ");
//      Serial.println("stopped");
//      break;  
//    }
//    else if(digitalRead(startButton2)==HIGH){
//      started2=true;
//      stopped2=false;
//      digitalWrite(ledPin2,HIGH);
//      Serial.print("stopped");
//      Serial.print(" ");
//      Serial.println(startString2);
//      break; 
//    }
//  }
}

