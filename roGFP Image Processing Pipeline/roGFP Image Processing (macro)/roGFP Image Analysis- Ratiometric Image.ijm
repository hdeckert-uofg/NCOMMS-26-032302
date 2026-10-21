// v6.0 adds stack registration
// v7.0 changes dynamic correction to include frame-by-frame C460 correction
// v7.1 adding frame-by-frame only correction
// March 2025- removes one erosion-dilation cycle from mask 
//!IMPORTANT! depending on application, please modify a) median filter value
	//1- for plants grown on plates and seedlings
	//2- for plants with strong trichomes
//b) dilation-erosion cycles when creating mask
// July 2025- switch from ImageJ thresholding to manual mask generation (see 543-550)

img=getTitle();
dir=getDirectory("image");
print("image: " + dir);

Dialog.create("roGFP Image Processing");
	Dialog.addChoice("Autofluorescence correction:", newArray("Dynamic only", "C460 Mean, C400 Dynamic", "Frame-by-Frame Only", "Mean only", "None"));
	Dialog.addCheckbox("Stack registration?", false);
	Dialog.addCheckbox("Measure (requires ROI Set)?", false);
	Dialog.addCheckbox("Calibrated ratio image?", false);
Dialog.show();
autofluo = Dialog.getChoice();
reg = Dialog.getCheckbox();
measure = Dialog.getCheckbox();
calratio = Dialog.getCheckbox();

	if (autofluo == "Dynamic only") {
		Dialog.create("Autofluorescence correction");
			Dialog.addString(".csv file named as XXX-460:", "WT");
			Dialog.addNumber("Gradient 400/515 nm:", 0.4562);
			Dialog.addNumber("y-Intercept 400/515 nm:", 239);
		Dialog.show();
		x = Dialog.getString();
		a = Dialog.getNumber();
		b = Dialog.getNumber();
	}
	
	if (autofluo == "C460 Mean, C400 Dynamic") {
		Dialog.create("Autofluorescence correction");
			Dialog.addNumber("Mean 460/515 nm:", 0);
			Dialog.addNumber("Gradient 400/515 nm:", 0);
			Dialog.addNumber("y-Intercept 400/515 nm:", 0);
		Dialog.show();
		xx = Dialog.getNumber();
		aa = Dialog.getNumber();
		bb = Dialog.getNumber();
	}
	
	if (autofluo == "Frame-by-Frame Only") {
		Dialog.create("Autofluorescence correction");
			Dialog.addString(".csv file named as XXX-460:", "XXX");
			Dialog.addString(".csv file named as XXX-400:", "XXX");
		Dialog.show();
		x = Dialog.getString();
		y = Dialog.getString();
	}
	
	if (autofluo == "Mean only") {
		Dialog.create("Autofluorescence correction");
			Dialog.addNumber("Mean 460/515 nm:", 0);
			Dialog.addNumber("Mean 400/515 nm:", 0);
		Dialog.show();
		m = Dialog.getNumber();
		m2 = Dialog.getNumber();
	}

	if (calratio == true) {
		Dialog.create("Autofluorescence correction");
			Dialog.addNumber("Oxidation ratio (max):", 0);
			Dialog.addNumber("Reduction ratio (min):", 0);
		Dialog.show();
		calMax = Dialog.getNumber();
		calMin = Dialog.getNumber();
	}
	
run("Properties...", "channels=3 slices=1 pixel_width=1.0000 pixel_height=1.0000 voxel_depth=1.0000");

call("ij.ImagePlus.setDefault16bitRange", 0);
run("Median...", "radius=1 stack");
run("32-bit");

getDimensions(width, height, channels, slices, frames);
//for (c=1; c<= channels; c++) {
	//Stack.setChannel(c);
	//Stack.getStatistics(voxelCount, mean, min, max, stdDev);
	//scalar=mean+2*stdDev;
	//setMinAndMax(0, scalar);
//}

run("Split Channels");

selectImage("C3-"+img);
run("Duplicate...", "title=[scaled C3-"+img+"] duplicate");

selectImage("C2-"+img);
if (autofluo == "Dynamic only") {
	selectImage("scaled C3-"+img);
	if (frames==1) {
		run("Multiply...", "value="+a);
		run("Add...", "value="+b);
		selectImage("C2-"+img); 
		imageCalculator("Subtract create", "C2-"+img,"scaled C3-"+img);
		run("Macro...", "code=[if( v < 0) v = 0]");
	} else {
		run("Multiply...", "value="+a+" stack");
		run("Add...", "value="+b+" stack");
		selectImage("C2-"+img); 
		imageCalculator("Subtract create stack", "C2-"+img,"scaled C3-"+img);
		run("Macro...", "code=[if( v < 0) v = 0] stack");
	}
	selectImage("Result of C2-"+img);
}

if (autofluo == "C460 Mean, C400 Dynamic") {
	selectImage("scaled C3-"+img);
	if (frames==1) {
		run("Multiply...", "value="+aa);
		run("Add...", "value="+bb);
		selectImage("C2-"+img); 
		imageCalculator("Subtract create", "C2-"+img,"scaled C3-"+img);
	} else {
		run("Multiply...", "value="+aa+" stack");
		run("Add...", "value="+bb+" stack");
		selectImage("C2-"+img); 
		imageCalculator("Subtract create stack", "C2-"+img,"scaled C3-"+img);
	}
	selectImage("Result of C2-"+img);
}

if (autofluo =="Frame-by-Frame Only") {
	getDimensions(width, height, channels, slices, frames);
	open(dir+y+"-400.csv");
	for (i = 0; i <= frames-1; i++) {
		f=i+1;
		Stack.setFrame(f);
		v = Table.get("C",i);
		print("Value subtracted from frame"+f+": "+v);
		run("Subtract...", "value="+v);
	}
}

if (autofluo =="Mean only") {
	if (frames==1) {
		run("Subtract...", "value="+m2"");
	} else {
		run("Subtract...", "value="+m2+" stack");
	}
}

rename("corrected C2-"+img);
selectImage("scaled C3-"+img);
close;
selectImage("C1-"+img);
run("Duplicate...", "title=[corrected C1-"+img+"] duplicate");

if (autofluo == "Mean only"){
	if (frames==1) {
		run("Subtract...", "value="+m"");
	} else {
		run("Subtract...", "value="+m+" stack");
	}
}

if (autofluo == "C460 Mean, C400 Dynamic"){
	if (frames==1) {
		run("Subtract...", "value="+xx);
	} else {
		run("Subtract...", "value="+xx+" stack");
	}
}

getDimensions(width, height, channels, slices, frames);
if (autofluo == "Dynamic only" || autofluo == "Frame-by-Frame Only"){
	open(dir+x+"-460.csv");
	for (i = 0; i <= frames-1; i++) {
		f=i+1;
		Stack.setFrame(f);
		v = Table.get("C",i);
		print("Value subtracted from frame"+f+": "+v);
		run("Subtract...", "value="+v);
	}
}

if (autofluo == "Dynamic only" || autofluo == "C460 Mean, C400 Dynamic"){
	selectImage("C2-"+img);
	close;
}
selectImage("C3-"+img);
close;

selectImage("C1-"+img);
run("Duplicate...", "title=[mask C1-"+img+"] duplicate");

selectImage("C1-"+img);
close;
selectImage("mask C1-"+img);

run("Duplicate...", "title=std");
getStatistics(voxelCount, mean, min, max, stdDev);
selectImage("std");
setMinAndMax(2*stdDev, mean+2*stdDev);
run("8-bit");
selectImage("mask C1-"+img);
selectImage("mask C1-"+img);
run("Duplicate...", "title=std-1");
selectImage("std-1");
getStatistics(voxelCount, mean, min, max, stdDev);
setMinAndMax(3*stdDev, mean+3*stdDev);
run("8-bit");
run("Images to Stack", "  title=std use keep");
run("Make Montage...", "columns=2 rows=1 scale=0.25 label");
Dialog.create("Mask choice");
	Dialog.addChoice("Which image has a better contrast?", newArray("Left", "Right"));
Dialog.show();
contrast = Dialog.getChoice();
close();
selectImage("Stack");
close();
selectImage("std");
close();
selectImage("std-1");
close();

selectImage("mask C1-"+img);
getDimensions(width, height, channels, slices, frames);
if (contrast=="Left"){
	if (frames==1) {
		getStatistics(voxelCount, mean, min, max, stdDev);
	} else {
		Stack.getStatistics(voxelCount, mean, min, max, stdDev);
	}
	setMinAndMax(2*stdDev, mean+2*stdDev);
	}

if (contrast=="Right"){
	if (frames==1) {
		getStatistics(voxelCount, mean, min, max, stdDev);
	} else {
		Stack.getStatistics(voxelCount, mean, min, max, stdDev);
	}
	setMinAndMax(3*stdDev, mean+3*stdDev);
	}
//run("Brightness/Contrast...");

//for (i = 1; i <= nSlices; i++) {
  //setSlice(i);
   //setMinAndMax(15, 95);
   //call("ij.ImagePlus.setDefault16bitRange", 8);
//}
//run("Apply LUT", "stack");
run("8-bit");
run("Duplicate...", "title=mask");
selectImage("mask C1-"+img);
run("Duplicate...", "title=mask-1");
run("Auto Local Threshold", "method=Phansalkar radius=50 parameter_1=0 parameter_2=0 white");
selectImage("mask");
run("Auto Threshold", "method=Huang2 white");
selectImage("mask C1-"+img);
run("Duplicate...", "title=mask-2");
run("Auto Threshold", "method=Otsu white");
run("Images to Stack", "  title=mask use keep");
run("Make Montage...", "columns=3 rows=1 scale=0.25 label");
Dialog.create("Mask choice");
	Dialog.addChoice("Which mask is better?", newArray("Left (Huang)", "Middle (Local Phan)", "Right (Otsu)"));
Dialog.show();
mask = Dialog.getChoice();
close();
selectImage("Stack");
close();
selectImage("mask");
close();
selectImage("mask-1");
close();
selectImage("mask-2");
close();

selectImage("mask C1-"+img);
getDimensions(width, height, channels, slices, frames);
if (mask=="Left (Huang)"){
	if (frames==1) {
		run("Auto Threshold", "method=Huang2 white");
		setOption("ScaleConversions", true);
		setOption("BlackBackground", true);
		run("Median...", "radius=1");
		run("Dilate");
		run("Erode");
	} else {
		run("Auto Threshold", "method=Huang2 white stack");
		setOption("ScaleConversions", true);
		setOption("BlackBackground", true);
		run("Median...", "radius=1 stack");
		run("Dilate", "stack");
		run("Erode", "stack");
	}
}
if (mask=="Middle (Local Phan)"){
	if (frames==1) {
		run("Auto Local Threshold", "method=Phansalkar radius=50 parameter_1=0 parameter_2=0 white");
		setOption("ScaleConversions", true);
		run("Median...", "radius=1");
		run("Dilate");
		run("Erode");
	} else {
		run("Auto Local Threshold", "method=Phansalkar radius=50 parameter_1=0 parameter_2=0 white stack");
		setOption("ScaleConversions", true);
		run("Median...", "radius=1 stack");
		run("Dilate", "stack");
		run("Erode", "stack");
	}
}
if (mask=="Right (Otsu)"){
	if (frames==1) {
		run("Auto Threshold", "method=Otsu white stack");
		setOption("ScaleConversions", true);
		run("Median...", "radius=1");
		run("Dilate");
		run("Erode");
	} else {
		run("Auto Threshold", "method=Otsu white stack");
		setOption("ScaleConversions", true);
		run("Median...", "radius=1 stack");
		run("Dilate", "stack");
		run("Erode", "stack");
	}
}

saveAs("Tiff",dir+"mask C1-"+img);

selectImage("mask C1-"+img);
run("16-bit");
selectImage("mask C1-"+img);
run("32-bit");
selectImage("mask C1-"+img);
run("16-bit");

if (frames==1) {
	imageCalculator("AND create", "corrected C1-"+img,"mask C1-"+img);
	selectImage("Result of corrected C1-"+img);
	imageCalculator("AND create", "corrected C2-"+img,"mask C1-"+img);
	selectImage("Result of corrected C2-"+img);
} else {
	imageCalculator("AND create stack", "corrected C1-"+img,"mask C1-"+img);
	selectImage("Result of corrected C1-"+img);
	imageCalculator("AND create stack", "corrected C2-"+img,"mask C1-"+img);
	selectImage("Result of corrected C2-"+img);
}

selectImage("Result of corrected C1-"+img);
run("32-bit");
selectImage("Result of corrected C2-"+img);
run("32-bit");

selectImage("corrected C1-"+img);
close;
selectImage("corrected C2-"+img);
close;

//Stack registration
if (reg== true){
	getDateAndTime(year, month, dayOfWeek, dayOfMonth,
		hour, minute, second, msec);
	tmpfile  = getDirectory("temp");
	tmpfile += "MSR-" + year + "-" + month + "-" + dayOfMonth +
		"_" + hour + "-" + minute + "-" + second + ".txt";
	run("MultiStackReg", "stack_1=[Result of corrected C1-"+ img
		+ "] action_1=Align"
		+ " file_1=[" + tmpfile + "]"
		+ " stack_2=None"
		+ " action_2=Ignore"
		+ " file_2=[]"
		+ " transformation=[Rigid Body] save");
	
	run("MultiStackReg", "stack_1=[Result of corrected C2-"+ img +
		"] action_1=[Load Transformation File]" +
		" file_1=[" + tmpfile + "]" +
		" stack_2=None" +
		" action_2=Ignore" +
		" file_2=[]" +
		" transformation=[Rigid Body]");
	
	run("MultiStackReg", "stack_1=[mask C1-"+ img +
		"] action_1=[Load Transformation File]" +
		" file_1=[" + tmpfile + "]" +
		" stack_2=None" +
		" action_2=Ignore" +
		" file_2=[]" +
		" transformation=[Rigid Body]");
	
	selectImage("mask C1-"+img);
	run("Auto Threshold", "method=Otsu white stack");
	setOption("ScaleConversions", true);
	selectImage("mask C1-"+img);
	run("32-bit");
	run("16-bit");
	
	selectImage("Result of corrected C1-"+img);
	rename("corrected C1-"+img);
	selectImage("Result of corrected C2-"+img);
	rename("corrected C2-"+img);
	
	if (frames==1) {
	imageCalculator("AND create", "corrected C1-"+img,"mask C1-"+img);
	rename("Result of corrected C1-"+img);
	imageCalculator("AND create", "corrected C2-"+img,"mask C1-"+img);
	rename("Result of corrected C2-"+img);
	} else {
	imageCalculator("AND create stack", "corrected C1-"+img,"mask C1-"+img);
	rename("Result of corrected C1-"+img);
	imageCalculator("AND create stack", "corrected C2-"+img,"mask C1-"+img);
	rename("Result of corrected C2-"+img);
	}
	
	selectImage("Result of corrected C1-"+img);
	getDimensions(width, height, channels, slices, frames);
	if (frames==1) {
	changeValues(60000, 65536, 0);		
	} else {
		for (f=1; f<= frames; f++) {
		Stack.setFrame(f);
		changeValues(60000, 65536, 0);
		}
	}
	
	selectImage("Result of corrected C2-"+img);
	getDimensions(width, height, channels, slices, frames);
	if (frames==1) {
	changeValues(60000, 65536, 0);		
	} else {
		for (f=1; f<= frames; f++) {
		Stack.setFrame(f);
		changeValues(60000, 65536, 0);
		}
	}
}

run("Merge Channels...", "c1=[Result of corrected C1-"+img+"] c2=[Result of corrected C2-"+img+"] create");
rename("corrected-"+img);

selectImage("corrected-"+img);

getDimensions(width, height, channels, slices, frames);
for (c=1; c<= channels; c++) {
	Stack.setChannel(c);
	if (frames==1) {
	changeValues(0, 0, NaN);	
	changeValues(60000, 65536, 0);
	} else {
		for (f=1; f<= frames; f++) {
		Stack.setFrame(f);
		changeValues(0, 0, NaN);
		changeValues(60000, 65536, 0);
		}
	}	
}

run("Split Channels");
selectImage("C1-corrected-"+img);
selectImage("C2-corrected-"+img);

getDimensions(width, height, channels, slices, frames);
if (frames==1) {
	imageCalculator("Divide create 32-bit", "C2-corrected-"+img,"C1-corrected-"+img);
	run("Macro...", "code=[if( v > 4 ) v = NaN]");
} else {
	imageCalculator("Divide create 32-bit stack", "C2-corrected-"+img,"C1-corrected-"+img);
	run("Macro...", "code=[if( v > 4 ) v = NaN] stack");
}

selectImage("Result of C2-corrected-"+img);
rename("ratio-"+img);

run("Fire");
//Change v value once you've got the calibration right

getDimensions(width, height, channels, slices, frames);
if (frames==1) {
	getStatistics(voxelCount, mean, min, max, stdDev);
} else {
	Stack.getStatistics(voxelCount, mean, min, max, stdDev);
}

scalar=mean+2*stdDev;
setMinAndMax(0, scalar);
if (calratio == true) {
	setMinAndMax(calMin,calMax);
}

waitForUser("Find threshold ratios (needs to be provided in the next step)");
Dialog.create("Remove nonsense ratio (cannot be reversed)");
			Dialog.addNumber("Ratio threshold (max):", 0);
			Dialog.addNumber("Ratio threshold (min):", 0);
		Dialog.show();
		thrmax = Dialog.getNumber();
		thrmin= Dialog.getNumber();

selectImage("ratio-"+img);
		
if (frames==1) {
	run("Macro...", "code=[if( v >= " + thrmax + ") v = NaN]");
} else {
	run("Macro...", "code=[if( v >= " + thrmax + ") v = NaN] stack");
}

if (frames==1) {
	run("Macro...", "code=[if( v <= " + thrmin + ") v = NaN]");
} else {
	run("Macro...", "code=[if( v <= " + thrmin + ") v = NaN] stack");
}

saveAs("Tiff",dir+"new_ratio-"+img);
print("Ratiometric image created");

selectImage("new_ratio-"+img);

if (measure == true) {
	selectImage("new_ratio"+img);
	run("Duplicate...", "title=[measure-ratio-"+img+"] duplicate");
	
	run("ROI Manager...");
	
	selectImage("measure-ratio-"+img);
	
	roiManager("Open", dir+"RoiSet.zip");
	roiManager("Show All with labels");
	roiManager("Select All");
	
	run("Set Measurements...", "mean redirect=None decimal=5");
	roiManager("Multi Measure");
	selectWindow("Results");
	saveAs("Results", dir+"Ratio-"+img+".csv");
	print("Ratio results saved");
	
	selectImage("new_ratio-"+img);
}

///Binary mask
run("Duplicate...", "title=[mask_improved-"+img+"] duplicate");
selectImage("mask_improved-"+img);
if (frames==1) {
	run("Macro...", "code=[if( v > " + 0 + ") v = 255]");
} else {
	run("Macro...", "code=[if( v > " + 0 + ") v = 255] stack");
}
run("8-bit");

//run("Convert to Mask", "method=Percentile background=Dark calculate black create");

selectImage("mask C1-"+img);
close;

selectImage("mask_improved-"+img);
	
run("16-bit");
selectImage("mask_improved-"+img);
run("32-bit");
selectImage("mask_improved-"+img);
run("16-bit");

if (frames==1) {
	imageCalculator("AND create", "C1-corrected-"+img,"mask_improved-"+img);
	selectImage("Result of C1-corrected-"+img);
	imageCalculator("AND create", "C2-corrected-"+img,"mask_improved-"+img);
	selectImage("Result of C2-corrected-"+img);
} else {
	imageCalculator("AND create stack", "C1-corrected-"+img,"mask_improved-"+img);
	selectImage("Result of C1-corrected-"+img);
	imageCalculator("AND create stack", "C2-corrected-"+img,"mask_improved-"+img);
	selectImage("Result of C2-corrected-"+img);
}
selectImage("C1-corrected-"+img);
close;
selectImage("C2-corrected-"+img);
close;

if (measure == true) {
	selectImage("Result of C2-corrected-"+img);
	run("Duplicate...", "title=[measure-C2-"+img+"] duplicate");
	
	selectImage("Result of C1-corrected-"+img);
	run("Duplicate...", "title=[measure-C1-"+img+"] duplicate");
	
	run("ROI Manager...");
	
	selectImage("measure-C1-"+img);
	
	roiManager("Open", dir+"RoiSet.zip");
	roiManager("Show All with labels");
	roiManager("Select All");
	
	run("Set Measurements...", "mean redirect=None decimal=5");
	roiManager("Multi Measure");
	selectWindow("Results");
	saveAs("Results", dir+"460Results-"+img+".csv");
	print("460/515nm results saved");
	
	selectImage("measure-C2-"+img);
	roiManager("Show All with labels");
	roiManager("Multi Measure");
	selectWindow("Results");
	saveAs("Results", dir+"400Results-"+img+".csv");
	print("400/515nm results saved");
	
	selectImage("measure-C1-"+img);
	close;
	selectImage("measure-C2-"+img);
	close;
}

run("Merge Channels...", "c1=[Result of C1-corrected-"+img+"] c2=[Result of C2-corrected-"+img+"] create keep");
rename("improved_corrected-"+img);
getDimensions(width, height, channels, slices, frames);
for (c=1; c<= channels; c++) {
	Stack.setChannel(c);
	if (frames==1) {
	changeValues(0, 0, NaN);		
	} else {
		for (f=1; f<= frames; f++) {
		Stack.setFrame(f);
		changeValues(0, 0, NaN);
		}
	}	
}
saveAs("Tiff",dir+"improved_corrected-"+img);
print("Corrected image saved");

selectImage("Result of C1-corrected-"+img);
close;
selectImage("Result of C2-corrected-"+img);
close;

print("All done!");


