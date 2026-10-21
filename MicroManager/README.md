# MicroManager2 script for time-lapse fluorescence-bioluminescence imaging

## Overview
This is a BeanShell automation script developed for the time-lapse imaging platform running under Micro-Manager 2.0. The script controls CCD camera image acquisition, LED light illumination, filter wheel positioning, and camera settings for long-term fluorescence and luciferase imaging experiments in plant circadian biology and photobiology. It supports automated roGFP2 fluorescence, plant autofluorescence, and luciferase imaging under a variety of lighting regimes.

The script provides:
- Automated Micro-Manager image acquisition.
- Programmable red and blue growth-light control
- Fluorescence imaging at two different excitation points (including autofluorescence imaging)
- Luciferase imaging for long-term circadian experiments (L:D entrainment followed by constant light conditions or LL experiments).
- Short-term light pulse experiments (minute timescale).
- Automated saving as multi-dimensional TIFF datasets

## Getting started

### Dependencies
- Micro-Manager 2.0
  - to download, see https://micro-manager.org/Version_2.0 
  - ImageJ is included within Micro-Manager
  - Expected install time: 1-5 min
- LUMO imaging hardware (or equivalent for the CCD camera used)
- Arduino-controlled LED illumination system
- Motorised filter wheel
  - for roGFP2 imaging, 515 $\pm$ 5 nm and 460 $\pm$ 10 nm filters are used
  - for luciferase imaging, 560 $\pm$ 10 nm filter is used

**DISCLAIMER**
<br> Output datasets are stored in RAM during acquisition before being written to disk, so sufficient system memory should be available for large experiments.

### Demo
Example image stack captured using the *GFP-LL* mode of the script (*WT-LUMOB-141_70-2_MMStack_Default.ome-1.tiff*) can be found in the *roGFP Image Processing Pipeline>>Example data* folder. 

Settings used for image stack capture:
```
gd = new ij.gui.GenericDialog("Constant Conditions Setup");
gd.addNumericField("Red LED intensity : ", 0, 0);
gd.addNumericField("Blue LED intensity : ", 100, 0);
gd.addNumericField("Number of Minutes : ", 10, 0);
gd.addNumericField("Number of Minutes (light) : ", 10, 0);
gd.addNumericField("Images per minute", 2, 0);
gd.addCheckbox("Advanced_Settings",false);
gd.showDialog();
```

## Executing program
Load the BeanShell script through the Micro-Manager scripting interface and execute it.
Upon launch, the user is prompted to enter the experiment ID and experiment mode:
```
ga = new ij.gui.GenericDialog("LUMO Imaging System");
ga.addStringField("LUMOB-", "000", 0);
ga.addChoice("Expt type : ", mode, mode[0]);
ga.showDialog();
```
There are 3 modes to choose from:
- ***GFP***: includes all roGFP2 imaging, including dual fluorescence-bioluminescence imaging
  - Image acquisition sequence is 453/515 nm (blue light excitation), 395/515 nm (UV excitation), and 395/460 (plant autofluorescence)
- ***LUC LD-LL***: luciferase bioluminescence imaging with L:D entrainment followed by imaging under LL conditions
- ***LUC LL***: luciferase bioluminescence imaging under LL conditions only

If you select ***GFP*** mode, a second window appears:
```
gc = new ij.gui.GenericDialog("LUMO Imaging System");
gc.addChoice("Expt type : ", expt, expt[1]);
gc.addCheckbox("Pause after growth lights off? ",false);
gc.addCheckbox("Luciferase imaging?",false);
gc.addNumericField("Exposure time (s) : ", 2, 0);
gc.addNumericField("Postpone imaging by (min) ", 0 ,0);
gc.showDialog();
```
1. **Expt type** : There are 4 experiment types to choose from
   - ***GFP Quick Image***: takes only one image sequence (can be delayed)
   - ***GFP LD-LL***: takes one image sequence every hour for the selected L:D followed by L:L circadian regime
   - ***GFP LL***: takes one image sequence at user-defined frequency on the minute timescale (the highest recommended frequency is one image sequence every 30 seconds). Allows blue/red light to be on for a specified time at the beginning of the imaging regime followed by imaging in the dark
   - ***GFP LL Sub-30 Pulse***: same as *GFP LL* but allows shorter blue/red light treatments (less than the time difference between first and second imaging sequence so minimum 30 s) followed by imaging in the dark
2. **Pause after growth lights off?** : sets a different delay time for luciferase imaging
   - Normally, dark adaptation before luciferase imaging is 30 s. By selecting this option, you can change the time of dark period before luciferase imaging
3. **Luciferase imaging?** : include luciferase imaging as part of the image sequence
   - This option is not available for **GFP LL** and ***GFP LL Sub-30 Pulse*** imaging
4. **Exposure time** : exposure time for each roGFP2 image
   - roGFP2 imaging consists of  three sequential images (excitation/emission): 453/515 nm, 395/515 nm, and 395/460 nm. *Exposure time* refers to exposure per image, not the entire image sequence
   - The minimum recommended for our setup is 2 s, although this varies with camera sensitivity and the intensity of roGFP2 excitation lights
   - Longer exposure time results in better signal and more resolved images. For long-term imaging that does not require very dynamic measurements, the recommended exposure time is 5 s
5. **Postpone imaging by (min)**: delays the start of the imaging sequence (input values are in minutes) for dark adaptation
   - Works for *GFP Quick Image*, *GFP LL*, and *GFP LL Sub-30 Pulse* only
  
The image stack will be saved in the defined folder. Changed the folder location in the *Set parameters* section:
```
String saveLocation = "YOUR FOLDER DIRECTORY";
```
### Image Acquisition Workflow
#### GFP Quick Image
*The logic behind the presented image acquisition sequence is analogous to all experiment types included in the script*

<br> Both blue and red LEDs installed are turned off:
```
mmc.setProperty("Arduino32-DAC/Red", "Volts", "0"); 
mmc.setProperty("Arduino32-DAC/Blue", "Volts", "0"); 
```
Setting up the camera:
```
mmc.setProperty("LUMO", "Gain", "2");
mmc.setProperty("LUMO", "PP  1   ENABLED", "No");
```
The structure of .tiff image stack is defined: 3 roGFP2 channels with optional luciferase channel, and one frame:
```
sb = store.getSummaryMetadata().copyBuilder();
axisOrder = new ArrayList();
axisOrder.add(Coords.C);
axisOrder.add(Coords.T);
sb.axisOrder(axisOrder);
channelNames = new ArrayList();
channelNames.add("460nm");
channelNames.add("400nm");
channelNames.add("Autofluo");
if (userLUC == true){channelNames.add("Luciferase");}
sb.channelNames(channelNames);
coordsB = store.getSummaryMetadata().getIntendedDimensions().copyBuilder();
coordsB.c(nrChannels).t(1);
sb.intendedDimensions(coordsB.build());
store.setSummaryMetadata(sb.build());
mm.displays().createDisplay(store);
```
If *Postpone imaging by (min)* was selected:
```
if (delayMin > 0){
	mm.scripter().message("Imaging delayed by "+delayMin+" min");
}
mmc.sleep(delay);
```
453/515 image capture includes moving the filter wheel to 515 $\pm$ 5 nm, turning the blue roGFP2-excitation light to max (100%), and storing the image as channel 1:
```
mmc.setExposure(userExpMs);
mmc.setProperty("FW", "State", "0");//Moves to 515nm
mmc.deviceBusy("FW"); //Safety call to wait for filterwheel to move
mmc.sleep(1000); //Pause before exposure (currently 1 sec)
mm.scripter().message("Exposure in progress");
mmc.setProperty("Arduino32-DAC/460nm", "Volts", "100");
mmc.sleep(1000); //Pause after turning lights on (currently 1 sec)

//Image capture
image = mm.live().snap(false).get(0);
Coords.CoordsBuilder builder = mm.data().getCoordsBuilder();
builder = builder.time(0).channel(0);
image = image.copyAtCoords(builder.build());
store.putImage(image);
mmc.deviceBusy("LUMO"); //Safety call to wait for exposure to finish
mm.scripter().message("460nm image acquired");
```
The next two roGFP2 images, 395/515 nm and 395/460 nm are captured under UV light (blue light off, UV light on). The filter wheel is moved for the 3rd image to 460 $\pm$ 10 nm. The two images are saved as channels 2 and 3 in the image stack respectively:
```
mmc.setProperty("Arduino32-DAC/460nm", "Volts", "0");
mmc.setProperty("Arduino32-DAC/400nm", "Volts", "100");
mmc.sleep(1000); //Pause before exposure (currently 1 sec)
image = mm.live().snap(false).get(0);
builder = builder.channel(1);
image = image.copyAtCoords(builder.build());
store.putImage(image);
mmc.deviceBusy("LUMO"); //Safety call to wait for exposure to finish
mm.scripter().message("400nm image acquired");

mmc.setProperty("Arduino32-DAC/400nm", "Volts", "100");
mmc.setProperty("FW", "State", "3");//Moves to 460nm
mmc.deviceBusy("FW"); //Safety call to wait for filterwheel to move
mmc.sleep(1000); //Pause (currently 1sec)
image = mm.live().snap(false).get(0);
builder = builder.channel(2);
image = image.copyAtCoords(builder.build());
store.putImage(image);
mmc.deviceBusy("LUMO"); //Safety call to wait for exposure to finish
mm.scripter().message("Autofluorescence image (400nm ex/460nm em) acquired");
```
roGFP2 excitation lights are turned off. If selected, **luciferase bioluminescence image** is captured, which includes changing LUMO camera settings to high sensitivity, moving the filter wheel to position 560 $\pm$ 10 nm, delaying imaging for 30 seconds (dark adaptation), followed by image capture with a 7-minute exposure:
```
mmc.setProperty("Arduino32-DAC/400nm", "Volts", "0"); //Turn off imaging LEDs
mmc.setProperty("Arduino32-DAC/460nm", "Volts", "0");

if (userLUC == true){
	mmc.setProperty("LUMO", "Gain", "3");//High sensitivity mode
	mmc.setProperty("LUMO", "PP  1   ENABLED", "Yes");//Turn on high pixel reduction
	mmc.setProperty("FW", "State", "4");
	mmc.deviceBusy("FW"); //Safety call to wait for filterwheel to move
	mmc.setExposure(420000);//Set exposure for luciferase (7 min)
	mm.scripter().message("Dark before luciferase imaging");
	mmc.sleep(30000); //Pause before luciferase exposure (currently 30 s)
	mm.scripter().message("Luciferase imaging in progress");

	image = mm.live().snap(false).get(0);
	builder = builder.channel(3);
	image = image.copyAtCoords(builder.build());
	store.putImage(image);
	}
	mmc.sleep(1000); //Pause after exposures (currently 1 sec)
	mmc.deviceBusy("LUMO"); //Safety call to wait for exposure to finish
 ```
Hardware reset to change to default setting at the end of every imaging:
 ```
mmc.sleep(5000);
mmc.setProperty("Arduino32-DAC/460nm", "Volts", "0"); //Turn all lights off, redundant but safe
mmc.setProperty("Arduino32-DAC/400nm", "Volts", "0");
mmc.setProperty("Arduino32-DAC/Blue", "Volts", "0");
mmc.setProperty("Arduino32-DAC/Red", "Volts", "0");
mm.scripter().message("LEDs off after imaging");
mmc.setProperty("FW", "State", "0");//Move filter into 515nm
mmc.deviceBusy("FW"); //Safety call to wait for filterwheel to move
mmc.setExposure(20); // Resets camera exposure (in ms)
mmc.setProperty("LUMO", "Gain", "2");//Mid sensitivity mode
mmc.setProperty("LUMO", "PP  1   ENABLED", "No");//Turn off high pixel reduction
public void refreshGUI();
 ```
 Saving data as .tiff file in the pre-defined location (see *Executing program* section on how to change it):
 ```
store.save(Datastore.SaveMode.MULTIPAGE_TIFF, saveLocation);
saveLocation += file2;
store.freeze();
mm.scripter().message("Images saved");
return;
 ```
#### GFP LD-LL (Circadian Fluorescence-Bioluminescence Imaging)
 Upon selecting *GFP LD-LL* option, a new dialog window opens:
```
 gg = new ij.gui.GenericDialog("GFP LD-LL");
gg.addNumericField("Daylight Red LED intensity : ", 0, 0);
gg.addNumericField("Daylight Blue LED intensity : ", 0, 0);
gg.addNumericField("Imaging interval during days (h): ", 1, 0);
gg.addNumericField("Number of images (Day) : ", 12, 0);
gg.addNumericField("Night Red LED intensity : ", 0, 0);
gg.addNumericField("Night Blue LED intensity : ", 0, 0);
gg.addNumericField("Imaging interval at night (h): ", 1, 0);
gg.addNumericField("Number of images (Night) : ", 12, 0);
gg.addNumericField("Number of days in LD cycles: ", 1, 0);
gg.addNumericField("Number of hours in constant light: ", 120, 0);
gg.addNumericField("Constant conditions Red LED intensity : ", 0, 0);
gg.addNumericField("Constant conditions Blue LED intensity : ", 0, 0);
gg.addNumericField("Closest previous ZT (h): ", 0, 0);
gg.addNumericField("Pause before first imaging loop (min): ", 0, 0);
gg.showDialog();
 ```
- **LED light intensity** : input values between 0-100. 
  - Two light qualities are available: red and blue 
  - *Daylight* and *Night* LEDs refer to the L:D period at the beginning of the experiment
  -  *Constant conditions* LEDs refers to the L:L period following the L:D. 
- **Imaging interval during days (h)** and **Number of images (Day)** 
  - The values provided must align with *Imaging interval at night (h)* and *Number of images (Night)* such that the day and night together last 24 hours
  - Here both day and night are 12 hours, but other L:D regimes (for example 6:18) can also be programmed
  - If the imaging interval is changed, make sure you account for that in the number of images taken per day/night
    - For example, if you want a 12-hour day and imaging every 2 hours, change *Imaging interval* to 2 and *Number of images (Day)* to 6.
  - *Imaging interval during days (h)* is also an imaging interval for LL free-run
- **Number of days in LD cycles** : a minimum of 1 day is required
  - The first day lasts from the start of the experiment until the next ZT0
    - If you set up your experiment at 12 pm and your ZT0 is 9 am, your first day will be recorded from 1 pm until 9 am the next day
  - You cannot set up your experiment after ZT11 (beginning of night in a 12:12 L:D cycle)
```
logicDiel = dayCal - userZt;//Logic gate for day length
if (logicDiel <= 1){
	mm.scripter().message("Cannot start after ZT11");
	return;}
```
- **Number of hours in constant light** : starts from ZT0 following the last L:D cycle
- **Closest previous ZT (h)** : provide the last integer ZT
  - For example, if ZT0 is at 9 am and it is currently 11.23 am, the closest previous ZT is 2 (ZT2= 11 am)
  - If you image every 2 hours, the closest previous ZT refers to the closest previous **even** ZT
    - For example, if ZT0 is at 9 am and it is currently 12.02 am, the closest previous ZT is 2 (ZT2= 11 am). This is because we want imaging every 2 hours (so at ZT0, ZT2, ZT4, ...)
    - Similarly, if imaged every 3 hours, the closest previous ZT should be a multiple of 3 
- **Pause before first imaging loop (min)** : the remaining time before the next ZT for which imaging should take place
  - If imaged hourly, this will be minutes till the next ZT. If ZT0 is at 9 am and it is currently 11.23 am, pause before first imaging loop will be 37 minutes.
  - If imaged every 2 hours, this will be minutes till the next **even** ZT. If ZT0 is at 9 am and it is currently 11.23 am, the pause before the first imaging loop will be 97 minutes
    - If 37 minutes is provided instead, the imaging will start at ZT3 so images will be taken for ZT5, ZT7,... instead of ZT6, ZT8,... as intended

Before the imaging starts, the daylight LEDs are switched on for the duration indicated in *Pause before first imaging loop (min)*:
```
mm.scripter().message("Waiting to begin program");
mmc.setProperty("Arduino32-DAC/Red", "Volts", RedVoltsA); 
mmc.setProperty("Arduino32-DAC/Blue", "Volts", BlueVoltsA); 
mmc.sleep(5000); //wait before entering loop (5s)
mm.scripter().message(usedColourA + " LEDs on");
mm.scripter().message("Pausing for " + pauseAi + " mins before entering imaging loop");
mmc.sleep(pauseAims);
```
L conditions for the L:D regime are annotated with *A* throughout the script, D conditions with *B*, and LL freerun with *C*. Example:
```
global.nrFramesAi = nrFramesA;
global.nrFramesBi = nrFramesB;
global.nrFramesCi = (nrFramesC / userTimeA);
```
<br>The script consists of five *for* loops: 
1. the first day 
2. the first night 
3. the remaining days of the LD regime 
4. LL free running conditions
    
<br>*Loops 1. and 2. are separate from 3. as the first day does not have to be a full one (if imaging starts after ZT0).*
```
global.firstDiel = nrFramesAi - (userZt / userTimeA);
if (pauseCal == 0){
	global.firstDiel = (int) firstDiel;}
else {global.firstDiel = firstDiel - 1;}
	global.firstNight = nrFramesBi;
	global.firstDay = firstDiel + firstNight;
```
<br>The duration of each loop is provided as *Imaging interval during days (h)* and *Imaging interval at night (h)*. Imaging exposure (three roGFP2 images and an optional luciferase image) times and script pauses are accounted for here:
```
global.TimeA = userTimeA * 3600000;
global.TimeB= userTimeB * 3600000;
if (userPause == true){
	if (userLUC == true){
global.TimeAm = TimeA  - 454000 - 7000 - 3 * userExpMs;
global.TimeBm = TimeB  - 454000 - 7000 - 3 * userExpMs;
}
if (userLUC == false){
global.TimeAm = TimeA - 3000 - 3 * userExpMs - userDelayMs;
global.TimeBm = TimeB - 3000 - 3 * userExpMs - userDelayMs;
}
}
```
Example of an imaging loop (lights on- pause based on imaging interval- lights off- image acquisition):
```
	for (k=0; k < firstDiel; k++) {
		print(startText);
		print(diffText);
		Calendar cal = Calendar.getInstance();
		loopTime = cal.getTime();
		x = k+1;
		mm.scripter().message("Loop " + x + " of " + nrFrames + " at:" + "\n" + loopTime);
      mmc.setProperty("LUMO", "Gain", "2");//High sensitivity mode
      mmc.setProperty("LUMO", "PP  1   ENABLED", "No");//Turn off reduce high pixels
      mmc.setProperty("FW", "State", "0");//Move FW to 515nm
		mmc.deviceBusy("FW"); //Safety call to wait for filterwheel to move
      mmc.setExposure(userExpMs);
      mmc.setProperty("Arduino32-DAC/Red", "Volts", RedVoltsA); 
	  mmc.setProperty("Arduino32-DAC/Blue", "Volts", BlueVoltsA); 
		mm.scripter().message(usedColourA + " LEDs on for " + userTimeA + " hrs");
		mmc.sleep(TimeAm);
		//Acquisition loop
		mmc.setProperty("Arduino32-DAC/Red", "Volts", "0"); //Set LEDs to off
		mmc.setProperty("Arduino32-DAC/Blue", "Volts", "0"); //Set LEDs to off
		mm.scripter().message("Growth LEDs off");
		//mmc.setProperty("MaestroServo", "Position", 1895);//Moves flipper down
		if(userPause == true){
			mm.scripter().message("Pausing before imaging");
			mmc.sleep(userDelayMs);
			}
		mm.scripter().message("Exposure in progress");
		mmc.setProperty("Arduino32-DAC/460nm", "Volts", "100");
		//mmc.setExposure(10);
		mmc.sleep(1000); //Pause before exposure (currently 1 sec)

		image = mm.live().snap(false).get(0);
		Coords.CoordsBuilder builder = mm.data().getCoordsBuilder();
		builder = builder.time(k).channel(0);
		image = image.copyAtCoords(builder.build());
		store.putImage(image);
		mmc.deviceBusy("LUMO"); //Safety call to wait for exposure to finish
		mm.scripter().message("460nm image acquired");

		mmc.setProperty("Arduino32-DAC/460nm", "Volts", "0");
		mmc.setProperty("Arduino32-DAC/400nm", "Volts", "100");
		mmc.sleep(1000); //Pause before exposure (currently 1 sec)
		image = mm.live().snap(false).get(0);
		Coords.CoordsBuilder builder = mm.data().getCoordsBuilder();
		builder = builder.time(k).channel(1);
		image = image.copyAtCoords(builder.build());
		store.putImage(image);
        mmc.deviceBusy("LUMO");
		mm.scripter().message("400nm image acquired");

      mmc.setProperty("FW", "State", "3");//Move FW to 460nm
		mmc.deviceBusy("FW"); //Safety call to wait for filterwheel to move
      mmc.sleep(1000); //Pause before exposure (currently 1 sec)
      image = mm.live().snap(false).get(0);
		Coords.CoordsBuilder builder = mm.data().getCoordsBuilder();
		builder = builder.time(k).channel(2);
		image = image.copyAtCoords(builder.build());
		store.putImage(image);
        mmc.deviceBusy("LUMO");
		mm.scripter().message("Autofluorescence image acquired");
    
		mmc.setProperty("Arduino32-DAC/460nm", "Volts", "0");
		mmc.setProperty("Arduino32-DAC/400nm", "Volts", "0");

if (userLUC == true){
	mmc.setProperty("FW", "State", "4");//Moves to 560nm
	mmc.deviceBusy("FW"); //Safety call to wait for filterwheel to move
	mmc.setExposure(420000);//Set exposure for luciferase (7 min)
	mmc.setProperty("LUMO", "Gain", "3");//High sensitivity mode
	mmc.setProperty("LUMO", "PP  1   ENABLED", "Yes");//Turn on reduce hgh pixels
			if(userPause == false){
			mm.scripter().message("Pausing before LUC imaging");
			mmc.sleep(30000);
			}
			if(userPause == true){
			mm.scripter().message("Pausing before LUC imaging");
			mmc.sleep(flexDelay);
			}
	mm.scripter().message("Dark before luciferase imaging");
	mmc.sleep(2000); //Pause before luciferase exposure (currently 2 sec)
	mm.scripter().message("Luciferase imaging in progress");

	image = mm.live().snap(false).get(0);
	Coords.CoordsBuilder builder = mm.data().getCoordsBuilder();
	builder = builder.time(k).channel(3);
	image = image.copyAtCoords(builder.build());
	store.putImage(image);
	}
	mm.scripter().message("Image " + x + " complete");
	mmc.sleep(2000); //Pause after exposures (currently 2 sec)
	mmc.deviceBusy("LUMO"); //Safety call to wait for exposure to finish
		//Acquisition loop ends

		global.l = k + 1;
   		}
```
#### GFP LL 
Upon selecting *GFP LL* option, a new dialog window opens:
```
gd = new ij.gui.GenericDialog("Constant Conditions Setup");
gd.addNumericField("Red LED intensity : ", 0, 0);
gd.addNumericField("Blue LED intensity : ", 0, 0);
gd.addNumericField("Number of Minutes : ", 10, 0);
gd.addNumericField("Number of Minutes (light) : ", 10, 0);
gd.addNumericField("Images per minute", 2, 0);
gd.addCheckbox("Advanced_Settings",false);
gd.showDialog();
```
- **Red/Blue LED intensity**: input value between 0 and 100
  - The selected lights will be switched on after the first image acquisition sequence
- **Number of Minutes**: total duration of the experiment
- **Number of Minutes (light)**: light treatment duration at the beginning of the experiment
  - For example, if the *Number of Minutes* is 10 and *Number of Minutes (light)* is 6, the imaging will be performed for 6 minutes under light conditions provided in *Red/BLue LED intensity* and the remaining 4 minutes in the dark
- **Images per minute**
  - Based on the duration of the current image acquisition sequence, the maximum number of images per minute is *2*
  - The number can be a fraction- inputting *0.5* will result in one image sequence being captured every 2 minutes
  ```
  global.ExptTime = userTl * userF; 
  global.nrFrames = ExptTime;
  global.BlFrames = userBl * userF;
  ```

The script first captures the first image sequence before switching on pre-defined LED lights. The script consists of two imaging loops:
1. Light loop
```
for (m=1; m < BlFrames+1; m++) {
		m = (int) m;
		print(startText);
		Calendar cal = Calendar.getInstance();
		loopTime = cal.getTime();
		y = m+1;
    ...
```
1. Dark loop
```
for (n = BlDone; n < nrFrames+1; n++) {
		n = (int) n;
		print(startText);
		Calendar cal = Calendar.getInstance();
		loopTime = cal.getTime();
		y = n+1;
    ...
```
#### GFP LL Sub-30 Pulse
Upon selecting *GFP LL Sub-30 Pulse* option, a new dialog window opens:
```
if (userExpt == "GFP LL sub 30 pulse"){
gd = new ij.gui.GenericDialog("Constant Conditions Setup");
gd.addNumericField("Red LED intensity : ", 0, 0);
gd.addNumericField("Blue LED intensity : ", 0, 0);
gd.addNumericField("Light pulse time (< imaging interval) : ", 0, 0);
gd.addNumericField("Number of Minutes : ", 15, 0);
gd.addNumericField("Images per minute", 1, 0);
gd.showDialog();
```
The options are analogous to the *GFP LL* experiment type, except:
- **Time  pulse (< imaging interval)** : select the light treatment duration between the first and second image acquisition sequence. It should not be higher than the interval between image acquisition sequences
  - For example, if you image samples every 30 s, the light pulse duration should be between *0* and *30 s - image acqusisition sequence* 
```
global.TPs= TP * 1000
mmc.sleep(TPs); 
global.TPr= TimeAm - TPs
...
for (m=1; m < nrFrames+1; m++) {
		m = (int) m;
		print(startText);
...
    if (m > 1){
        mmc.sleep(TimeAm);}
        else {mmc.sleep(TPr);}
...
}
```

## Authors

Matt Jones, University *of* Glasgow (contact: Matt.Jones@glasgow.ac.uk)
<br>Hanna Deckert (Hanna.Deckert@glasgow.ac.uk)

## Acknowledgements
 The readme file was generated with assistance of Microsoft Copilot (version: 2.20260928.61.0). 
