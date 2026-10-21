list = getList("image.titles");

for(i = 0;i<list.length;i++){
	if(matches(list[i],".*new_ratio.*")){
		selectImage(list[i]);
	}
}

img=getTitle();
dir=getDirectory("image");
print("image: " + dir);

for(i = 0;i<list.length;i++){
	if(matches(list[i],".*improved_corrected-.*")){
		selectImage(list[i]);
	}
}

img2=getTitle();
dir2=getDirectory("image");
print("image: " + dir2);

selectImage(img2);
run("Split Channels");

list = getList("image.titles");

for(i = 0;i<list.length;i++){
	if(matches(list[i],".*C1.*")){
		selectImage(list[i]);
	}
}

C1=getTitle();
dirC1=getDirectory("image");
print("image: " + dirC1);

for(i = 0;i<list.length;i++){
	if(matches(list[i],".*C2.*")){
		selectImage(list[i]);
	}
}

C2=getTitle();
dirC2=getDirectory("image");
print("image: " + dirC2);

selectImage(img);

waitForUser("Find threshold ratios (needs to be provided in the next step)");
Dialog.create("Remove nonsense ratio (cannot be reversed)");
			Dialog.addNumber("Ratio threshold (max):", 0);
			Dialog.addNumber("Ratio threshold (min):", 0);
		Dialog.show();
		thrmax = Dialog.getNumber();
		thrmin= Dialog.getNumber();
		
selectImage(img);
getDimensions(width, height, channels, slices, frames);
		
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

saveAs("Tiff",dir+"cyto-"+img);

selectImage("cyto-"+img);
run("Duplicate...", "title=[mask-"+img+"] duplicate");
selectImage("mask-"+img);
getDimensions(width, height, channels, slices, frames);

if (frames==1) {
	run("Macro...", "code=[if( v > " + 0 + ") v = 65535]");
} else {
	run("Macro...", "code=[if( v > " + 0 + ") v = 65535] stack");
}


selectImage("mask-"+img);
run("16-bit");
selectImage("mask-"+img);
run("32-bit");
selectImage("mask-"+img);
run("16-bit");

if (frames==1) {
	imageCalculator("AND create", C1,"mask-"+img);
	selectImage("Result of "+C1);
	imageCalculator("AND create", C2,"mask-"+img);
	selectImage("Result of "+C2);
} else {
	imageCalculator("AND create stack", C1,"mask-"+img);
	selectImage("Result of "+C1);
	imageCalculator("AND create stack", C2,"mask-"+img);
	selectImage("Result of "+C2);
}
selectImage(C1);
close;
selectImage(C2);
close;

run("Merge Channels...", "c1=[Result of "+C1+"] c2=[Result of "+C2+"] create keep");
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
saveAs("Tiff",dir+"cyto-"+img2);

selectImage("Result of "+C1);
close;
selectImage("Result of "+C2);
close;

print("All done!");
